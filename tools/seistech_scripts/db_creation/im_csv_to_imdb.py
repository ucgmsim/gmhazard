#!/usr/bin/env python3
"""Script for creating the non-parametric IMDB from the
IM csv files produced by Cybershake.

Uses the ray multiprocessing library, as it allows easy usage of shared memory.
https://ray.readthedocs.io/en/latest/installation.html
https://github.com/ray-project/ray

Reads all csv files initially and loads these into shared memory, from
there multiple workers, construct the station dataframes and feed these to
the single writer process, which writes it the database.

The data is stored in shared memory using a dictionary of simulations,
where the values are the corresponding IM data values as numpy arrays.
The numpy arrays are of format [n_stations_for_simulation/fault, n_ims],
where the assumption is made that IM csv files have the same number of IMs
in the same order.
The association between the rows of the arrays and stations is made at a
fault level, by storing the indices of the stations (in the station list) per fault,
and ensuring that stations are in order.

Note: This script requires python3.7+, otherwise a pickle error will occur
"""
import gc
import os
import time
import glob
import logging
import argparse
from typing import Dict, List, Tuple, Union, Optional, Iterable

import ray
import numpy as np
import pandas as pd

import seistech_calc as sc
from qcore.formats import load_station_file


def get_im_files(fault_dir: str) -> List[str]:
    """Retrieves the IM files for a given fault directory"""
    return glob.glob(os.path.join(fault_dir, "*/*/*.csv"))


def get_sim_name(im_file: str) -> str:
    """Gets the simulation name from an IM file path"""
    return str(os.path.basename(im_file).split(".")[0])


@ray.remote(num_cpus=1)
class DataCollector:
    """Worker process for the reading of IM csv files"""

    def __init__(
        self,
        fault_dirs: Iterable[str],
        stations: np.ndarray,
        csv_ffps: np.ndarray,
        im_names: np.ndarray,
        component: str,
    ):
        """Constructor, called using DataCollector.remote(args)

        Parameters
        ----------
        fault_dirs: Iterable of strings
            The fault directories this Actor will process
        stations: numpy array of strings
            Array of station names
        csv_ffps: numpy array of strings
            Full path for all csv files
        im_names: numpy array of strings
            The name of the IMs to retrieve from the IM csv files
        component: str
            The IM Component to extract from the IM csv files
        """
        self._faults = fault_dirs
        self._stations = stations
        self._csv_ffps = csv_ffps
        self._im_names = im_names
        self.component = component

    def run(self) -> List[Tuple[np.ndarray, List[str], Dict[str, np.ndarray]]]:
        """Runs the data collection

        Returns
        -------
        List of tuples of np.ndarray, list of strings, dictionary of str:np.ndarray
            Returns an tuple for each of the processed faults,
            a tuple contains
                - indices of the stations, for which there is data, into
                the station list
                - list of all the simulation names
                - dictionary of the actual IM data, where the simulation name is key,
                and the value is a numpy array of the im values for that simulation,
                format [n_stations_for_simulation/fault, n_ims]
        """
        results = []
        fault_for_csv = np.asarray([os.path.basename(file).split("_")[0] for file in self._csv_ffps])

        for fault in self._faults:
            # Get the csv files
            im_files = self._csv_ffps[fault_for_csv == fault]

            sim_names = [get_sim_name(file) for file in im_files]

            df = pd.read_csv(im_files[0], index_col=0, usecols=[0, 1], engine="c")

            # Requires the csv files to be sorted by the station name
            # Sort if required
            if not df.index.is_monotonic_increasing:
                df.sort_index(inplace=True)
            assert df.index.is_monotonic_increasing

            # Get the stations indices into the station list
            # Same as np.flatnonzero(np.isin(stations, df.index.values)) but much faster
            station_ind = np.flatnonzero(
                sc.utils.pandas_isin(self._stations, df.index.values)
            )

            # Read the csv files
            sim_dict = {}
            for im_file, sim_name in zip(im_files, sim_names):
                cur_df = pd.read_csv(im_file, index_col=0, engine="c", sep=",")

                # Filtering by Component before potential sorting
                cur_df = cur_df.loc[cur_df["component"] == self.component]

                # Sort if required
                if not cur_df.index.is_monotonic_increasing:
                    cur_df.sort_index(inplace=True)
                assert cur_df.index.is_monotonic_increasing

                data = cur_df.loc[self._stations[station_ind], self._im_names].values
                sim_dict[sim_name] = data

            results.append((station_ind, sim_names, sim_dict))
        return results

    def terminate(self):
        print("Exiting DataCollector")
        ray.actor.exit_actor()


@ray.remote(num_cpus=1)
class StationProcessor:
    """Worker process that constructs the IM dataframes
    for the given stations, using the data stored in shared memory
    """

    def __init__(
        self,
        fault_dict: Dict[str, Tuple[np.ndarray, List[str]]],
        im_names: np.ndarray,
        simulations: pd.Series,
        im_data_dict: Dict[str, np.ndarray],
        writer: ray.ActorClassID,
    ):
        """Constructor, called using StationProcessor.remote(args)

        Parameters
        ----------
        fault_dict: dictionary
            Contains fault level information
            Keys are fault names, values are tuples of
            station indices and simulation names
        im_names: numpy array of strings
            The IM names (in the same order as the columns in the IM data)
        simulations: pandas series
            All simulations
        im_data_dict: dictionary
            The IM data, keys are the simulations,
            values are the corresponding IM data as numpy arrays,
            where the columns correspond to im_names
        writer: actor id
            The ray id corresponding to the writer process
        """
        self._fault_dict = fault_dict
        self._faults = np.asarray(list(self._fault_dict.keys()))
        self._im_names = im_names
        self._simulations = simulations
        self._im_data_dict = im_data_dict
        self._writer = writer

    def run(self, station_names: np, station_ind) -> None:
        """For each of the specified stations,
        creates the IM dataframe and calls the
        writer process to write to the db.

        Parameters
        ----------
        station_names: numpy array of strings
            The names of the stations to process
        station_ind: numpy array of ints
            The indices of the stations to process
            into the station list
        """
        # Sanity check
        assert len(station_ind) == len(station_names)

        # Iterate over the stations
        for ix, (station_ix, station_name) in enumerate(
            zip(station_ind, station_names)
        ):
            print(f"Processing station {station_name}")
            start_time = time.time()

            # Retrieve the IM dataframe
            im_df = self._process_station(station_ix)

            # Write
            if im_df is not None:
                write_id = self._writer.write.remote(station_name, im_df)

                # Wait for the write
                wait_s_time = time.time()
                print(f"Waiting for writer, station {station_name}")
                ray.get(write_id)
                print(f"Waited {time.time() - wait_s_time} for write")
            print(
                f"Completed station {station_name}, {ix + 1}/{len(station_names)}, took {time.time() - start_time:.5}"
            )
        print("Completed all assigned stations")

    def _process_station(self, station_ix: int) -> Union[None, pd.DataFrame]:
        """Creates the IM dataframe for the specified station

        Parameters
        ----------
        station_ix: int
            Index of the station to process (into the station list)

        Returns
        -------
        pd.DataFrame
            The IM dataframe, where the rows are the simulations,
            and the columns the different IM values
        """
        # Get the faults which have data for the specified station
        fault_mask = np.asarray(
            [station_ix in self._fault_dict[fault][0] for fault in self._faults]
        )

        # Iterate over the relevant faults and their
        # simulations to collect the relevant data
        station_data = {}
        for fault in self._faults[fault_mask]:
            row_ix = np.flatnonzero(self._fault_dict[fault][0] == station_ix)
            # print(f"Row ix - {row_ix}")

            for sim in self._fault_dict[fault][1]:
                s_time = time.time()
                # print(f"{self.name} - ", sim_data_dict[sim])
                cur_data = self._im_data_dict[sim][row_ix].reshape(-1)
                # print(sim, self._im_names, cur_data)
                # print(f"{self.name} - {sim} - data:\n{cur_data}")
                station_data[sim] = cur_data

        if len(station_data) == 0:
            return None
        else:
            # Create the dataframe, sort by simulation names
            # and replace simulation with the simulation indices
            # into the full list of simulations
            df = pd.DataFrame.from_dict(
                data=station_data, orient="index", columns=self._im_names
            )
            df.sort_index(inplace=True)
            sim_indices = np.flatnonzero(
                sc.utils.pandas_isin(self._simulations.values, df.index.values)
            )
            df.index = sim_indices
            return df


@ray.remote(num_cpus=1)
class WriterProcess:
    """Process/Actor for writing the IM data to the IMDB"""

    def __init__(
        self,
        imdb_file: str,
        site_df: pd.DataFrame,
        simulations: pd.Series,
        im_names: np.ndarray,
        append: bool = False,
    ):
        """Constructor, called using WriterProcess.remote(args)

        Also writes the initial data, sites and simulations

        Parameters
        ----------
        imdb_file: str
            IMDB file path
        site_df: pandas dataframe
            Index are the stations names, columns are [lat, lon]
        simulations: pandas series
            All simulations, have to be sorted
        """
        self._append = append

        self._imdb_file = imdb_file
        self._simulations = simulations

        # Create and open db
        self._imdb = sc.dbs.IMDBNonParametric(
            self._imdb_file, writeable=True, source_type=sc.SourceType.fault
        )
        self._imdb.open()

        if not self._append:
            # Write initial data
            self._imdb.write_sites(site_df)

            assert np.all(simulations.sort_values() == simulations)
            self._imdb.write_simulations(simulations)

            # Not sure if we want to save the IM types as an attribute
            # (can figure that out later, once we have a consistent DB base..)
            self._imdb.write_attributes(ims=im_names.astype(str))
        else:
            exiting_ims = self._imdb.get_attributes()["ims"]
            self._imdb.write_attributes(
                ims=np.concatenate((exiting_ims, im_names.astype(str)))
            )

    def write(self, station_name: str, df: pd.DataFrame) -> None:
        """Writes the IM data to the IMDB"""
        print(f"Starting write for {station_name}")
        if self._append:
            self._imdb.add_im_data(station_name, df)
        else:
            self._imdb.write_im_data(station_name, df)
        print(f"Writer - Wrote station {station_name}")

    def close_db(self) -> None:
        print("Closing imdb")
        self._imdb.close()


def run(
    csv_ffps: np.ndarray,
    station_file: str,
    output_file: str,
    pre_n_procs: int,
    n_procs: int,
    component: str,
    im_names: np.ndarray = None,
    rupture_lookup: bool = False,
    iteration: int = 0,
):
    """
    Parameters
    ----------
    csv_ffps: numpy array of strings
        Full path for all csv files
    station_file: str
        Station list file
    output_file: str
    pre_n_procs: int
        Number of processes to use for the reading of the IM csv files
    n_procs: int
        Number of worker processes to use for creating IM dataframes
        Note: the total number of processes at that stage will be
        n_procs + 2 (main process and writer process)
    im_names: string numpy array, optional
        If provided then only those IMs will be added to the IMDB,
        otherwise all found in the IM csv files will be added
    rupture_lookup: bool, optional
        If true, then data will be added to the IMDB to allow
        rupture based lookup of IM data
    iteration: int, optional
        The current iteration, only used when adding all the IMs
        to the IMDB can not be done in a single run-through
    """
    total_start_time = time.time()

    # Sets the number of proceses the ray can use,
    # the amount of memory each worker can use (memory)
    # the amount of memory of the shared object store (object_store_memory)
    # These should be fine, might have to be adjusted
    # if the number of IMs increases.
    # The worker memory can probably be significantly lower.
    ray.init(
        num_cpus=max(n_procs, pre_n_procs),
        object_store_memory=30 * 1e9,
        logging_level=logging.DEBUG,
    )

    if iteration == 0 and os.path.exists(output_file):
        print("The specified output file already exists. Quitting!")
        exit()

    # Get all faults
    faults = list({os.path.basename(csv).split("_")[0] for csv in csv_ffps})

    # Get the IM names in the csv files
    # Assumes that all csv files have the same IMs
    im_file = csv_ffps[0]
    df = pd.read_csv(im_file, engine="c", nrows=2, index_col=0)
    df.drop("component", inplace=True, axis=1)
    if im_names is None:
        im_names = df.columns.values

    # All stations
    site_df = load_station_file(station_file)
    stations = np.sort(site_df.index.values)

    # Read the IM csv files
    print("Reading/processing csv files")
    n_faults_per = len(faults) // pre_n_procs
    data_collectors, split_faults, result_ids = [], [], []
    for ix in range(pre_n_procs):
        cur_faults = (
            faults[ix * n_faults_per : (ix + 1) * n_faults_per]
            if ix + 1 < pre_n_procs
            else faults[ix * n_faults_per :]
        )
        cur_collector = DataCollector.remote(cur_faults, stations, np.asarray(csv_ffps), im_names, component)
        data_collectors.append(cur_collector)
        split_faults.append(cur_faults)
        result_ids.append(cur_collector.run.remote())

    results = [ray.get(id) for id in result_ids]

    print("Combining results")
    fault_dict, simulations = {}, []
    im_data_dict = {}
    for cur_faults, result in zip(split_faults, results):
        for fault, data in zip(cur_faults, result):
            fault_dict[fault] = (data[0], data[1])
            simulations.extend(data[1])
            im_data_dict.update(data[2])

    simulations = np.asarray(simulations)
    simulations.sort()

    # Load the combined result to shared memory (object store)
    im_data_dict_id = ray.put(im_data_dict)

    # Delete the no longer needed things
    del im_data_dict
    for col in data_collectors:
        col.terminate.remote()
    gc.collect()

    # Create the writer process
    writer = WriterProcess.remote(
        output_file,
        site_df,
        pd.Series(simulations),
        im_names,
        True if iteration > 0 else False,
    )

    # Create the worker processes
    worker_procs = [
        StationProcessor.remote(
            fault_dict, im_names, pd.Series(simulations), im_data_dict_id, writer
        )
        for ix in range(n_procs)
    ]

    # Split the work and start the worker processes
    n_stations_per = stations.size // n_procs
    worker_run_ids = []
    for ix in range(n_procs):
        cur_stations = (
            stations[ix * n_stations_per : (ix + 1) * n_stations_per]
            if ix + 1 < n_procs
            else stations[ix * n_stations_per :]
        )
        cur_station_ind = np.arange(
            ix * n_stations_per, (ix * n_stations_per) + cur_stations.size, dtype=np.int
        )
        worker_run_ids.append(
            worker_procs[ix].run.remote(cur_stations, cur_station_ind)
        )

    # Wait for the worker processes to finish
    print("Collecting and writing station data")
    ray.wait(worker_run_ids, num_returns=len(worker_run_ids))

    close_id = writer.close_db.remote()
    ray.wait([close_id], num_returns=1)
    print(f"Total time {time.time() - total_start_time}")

    if rupture_lookup:
        print("Adding data for rupture based lookup")
        sc.dbs.IMDB.add_rupture_lookup(output_file, n_procs=n_procs)

    ray.shutdown()


def main(args):
    """Handles incremental IMDB creation if required, due to memory limitations"""
    items_per_iter = args.ims_per_iter

    # No need to split into iterations
    if args.ims is not None and len(args.ims) < items_per_iter:
        run(
            args.csv_ffps,
            args.station_file,
            args.output_file,
            args.pre_n_procs,
            args.n_procs,
            im_names=np.asarray(args.ims) if args.ims is not None else None,
        )
    else:
        im_names = args.ims
        # Get the IMs from one of the csv files if not specified by the user
        if im_names is None:
            im_file = args.csv_ffps[0]
            df = pd.read_csv(im_file, engine="c", nrows=2, index_col=0)
            df.drop("component", inplace=True, axis=1)
            im_names = df.columns.values
        im_names = np.asarray(im_names)

        # No iterations required
        if im_names.shape[0] < items_per_iter:
            run(
                args.csv_ffps,
                args.station_file,
                args.output_file,
                args.pre_n_procs,
                args.n_procs,
                args.component,
                im_names=im_names,
            )
        # Have to create the IMDB incrementally
        else:
            n_iter = int(np.ceil(im_names.shape[0] // items_per_iter))
            for ix in range(n_iter):
                cur_im_names = (
                    im_names[ix * items_per_iter : (ix + 1) * items_per_iter]
                    if ix + 1 < n_iter
                    else im_names[ix * items_per_iter :]
                )
                print(f"Running iteration {ix + 1}/{n_iter}")
                run(
                    args.csv_ffps,
                    args.station_file,
                    args.output_file,
                    args.pre_n_procs,
                    args.n_procs,
                    args.component,
                    im_names=cur_im_names,
                    iteration=ix,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script for creating a non-parametric IMDB from IM csv files"
    )
    parser.add_argument(
        "-csv_ffps",
        type=str,
        nargs="+",
        help="List of CSV full paths to turn into IMDB's",
        required=True,
    )
    parser.add_argument(
        "-station_file", type=str, help="Station list file", required=True
    )
    parser.add_argument(
        "-output_file", type=str, help="Location of the new IMDB", required=True
    )
    parser.add_argument(
        "--pre_n_procs",
        type=int,
        help="Number of processes to use for the reading of the IM csv files",
        default=8,
    )
    parser.add_argument(
        "--n_procs",
        type=int,
        help="Number of worker processes to use for creating IM dataframes\n"
        "Note: the total number of processes at that stage will be "
        "n_procs + 2 (main process and writer process)",
        default=3,
    )
    parser.add_argument(
        "--ims_per_iter",
        type=int,
        default=20,
        help="Number of IMs to add per iteration, "
        "making this too large will result memory issues. "
        "To run with the default value 32GB is required.",
    )
    parser.add_argument(
        "--ims",
        type=str,
        nargs="+",
        help="If set, then only the specified IMs "
        "are processed from the IM csv files",
        default=None,
    )
    parser.add_argument(
        "--component",
        type=str,
        help="IM Component to extract from the IM csv files."
             "Default value is rotd50",
        default="rotd50",
    )

    args = parser.parse_args()
    main(args)
