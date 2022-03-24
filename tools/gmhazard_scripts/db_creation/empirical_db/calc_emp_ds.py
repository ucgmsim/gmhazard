#!/usr/bin/env python3
"""Script to calculate IMs for empirical distributed seismicity

Writes to multiple empirical DB depending on the config
"""
import argparse
import math
import time
import threading

from mpi4py import MPI
import pandas as pd

import gmhazard_calc as sc
import common
from empirical.util import empirical_factory

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
hostname = MPI.Get_processor_name()
master = 0
is_master = not rank

if size < 2:
    print("This script is required to run with MPI and have n_procs >= 2")
    exit()


def calculate_ds(
    background_sources_ffp,
    site_source_db_ffp,
    vs30_ffp,
    z_ffp,
    ims,
    psa_periods,
    output_dir,
    model_dict_ffp,
    suffix=None,
):
    """
    Calculate Empirical values for every site-fault pairing in the provided site_source_db.

    Pairs the station name with the vs30 value in the provided vs30 file. Only sites that have vs30 values will be calculated.

    Saves all IM values (median and sigma) for all ims specified to the imdb_path in pandas h5 format

    :return: None
    """
    imdb_dict = {}
    wait_time = 0.0
    nhm_data, rupture_df = None, None
    if is_master:
        nhm_data = sc.utils.ds_nhm_to_rup_df(background_sources_ffp)
        rupture_df = pd.DataFrame(nhm_data["rupture_name"])
        imdb_dict, stations_calculated = common.open_imdbs(
            model_dict_ffp,
            output_dir,
            sc.constants.SourceType.distributed,
            suffix=suffix,
        )
    nhm_data = comm.bcast(nhm_data, root=master)
    rupture_df = comm.bcast(rupture_df, root=master)
    imdb_dict_copy = comm.bcast({key: None for key in imdb_dict.keys()}, root=master)
    model_dict = empirical_factory.read_model_dict(model_dict_ffp)

    with sc.dbs.SiteSourceDB(site_source_db_ffp) as distance_store:
        fault_df = None
        if is_master:
            # For DS, master is getting all of the work and then distributing it to slaves. Hence why size is 1.
            fault_df, n_stations, site_df, work = common.get_work(
                distance_store, vs30_ffp, z_ffp, rank, 1, stations_calculated
            )
        fault_df = comm.bcast(fault_df, root=master)

        status = MPI.Status()
        if is_master:
            nslaves = size - 1
            n_rows = len(work)
            print(f"{n_rows} stations to compute")

            # Determine number of MP processes to use per site
            n_mp_proc = math.ceil(size / n_rows) if size > n_rows else 1
            print(f"Using {n_mp_proc} MP processes per station")

            i = 0
            results = []
            writer = threading.Thread(
                None, print, "writer", ("Writer thread started")
            )  # create the thread object to check if it is running below
            while nslaves:
                value, station_name = comm.recv(source=MPI.ANY_SOURCE, status=status)
                slave_id = status.Get_source()

                # next job - gives work before storing data
                if i < n_rows:
                    msg = (i, n_rows, work.iloc[i], n_mp_proc)
                    comm.send(obj=msg, dest=slave_id)
                    i += 1
                else:
                    comm.send(obj=StopIteration, dest=slave_id)
                    nslaves -= 1

                if station_name is None:
                    print(f"Rank {slave_id} asking for work")
                else:
                    print(f"Received site {station_name} from {slave_id}")
                    results.append((value, imdb_dict, station_name))
                    if not writer.is_alive():
                        writer = threading.Thread(
                            None, write_results_to_db, "writer", (results,)
                        )
                        writer.start()
                        results = []
            if len(results) > 0:
                write_results_to_db(results)
            writer.join()
            print("all done")
        else:
            value = (None, None)
            s_time = time.perf_counter()
            for i, n_rows, site, n_mp_proc in iter(
                lambda: comm.sendrecv(value, dest=master), StopIteration
            ):
                print("IN CALC_EMP_DS")
                print(site)
                comm_time = time.perf_counter() - s_time
                wait_time += comm_time
                if distance_store.has_station_data(site.name):
                    print(
                        f"Processing site {i + 1} / {n_rows} - Rank: {rank} - {hostname} - waited for {comm_time:.2f}s"
                    )
                    max_dist = common.get_max_dist_zfac_scaled(site)
                    value = (
                        common.calculate_emp_site(
                            ims,
                            psa_periods,
                            imdb_dict_copy,
                            fault_df,
                            rupture_df,
                            distance_store,
                            nhm_data,
                            site.vs30,
                            site.z1p0 if hasattr(site, "z1p0") else None,
                            site.z2p5 if hasattr(site, "z2p5") else None,
                            site.name,
                            model_dict,
                            max_dist,
                            dist_filter_by_mag=True,
                            return_vals=True,
                            n_procs=n_mp_proc,
                            use_directivity=False,
                        ),
                        site.name,
                    )
                else:
                    print(f"Skipping site {i} - Rank: {rank}")
                print(f"total time for station: {time.perf_counter() - s_time:.2f}s")
                s_time = time.perf_counter()
            print(
                f"rank: {rank} - {hostname} complete. Total time waited {wait_time:.2f}s"
            )

    if is_master:
        common.write_metadata_and_close(
            imdb_dict,
            background_sources_ffp,
            rupture_df,
            site_df,
            vs30_ffp,
            psa_periods,
            ims,
            model_dict_ffp,
        )


def write_results_to_db(results):
    for result in results:
        print(f"Writing {result[2]}")
        common.write_result_to_db(*result)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("background_txt", help="background txt file")
    parser.add_argument("site_source_db")
    parser.add_argument("vs30_file")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--z-file",
        help="File name of the Z data",
    )
    parser.add_argument(
        "--periods",
        default=common.PERIOD,
        nargs="+",
        help="Which pSA periods to calculate for",
    )
    parser.add_argument(
        "--im", default=common.IM_TYPE_LIST, nargs="+", help="Which IMs to calculate", type=sc.im.IMType,
    )
    parser.add_argument(
        "--model-dict",
        help="model dictionary to specify which model to use for each tect-type",
    )
    parser.add_argument(
        "--suffix",
        "-s",
        help="suffix for the end of the imdb files",
        default=None,
    )

    return parser.parse_args()


def calculate_emp_ds():
    args = None
    if is_master:
        args = parse_args()
    args = comm.bcast(args, root=master)
    calculate_ds(
        args.background_txt,
        args.site_source_db,
        args.vs30_file,
        args.z_file,
        args.im,
        args.periods,
        args.output_dir,
        args.model_dict,
        suffix=args.suffix,
    )


if __name__ == "__main__":
    calculate_emp_ds()
