"""Script to generate IM csv files from a set of Karim empirical files

Used to include subduction faults in the CS non-parametric IMDB
(as subduction fault are currently not simulated)
"""
import os
import glob
import argparse
import multiprocessing as mp
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import norm

import gmhazard_calc.utils as utils
import gmhazard_calc.modules.gm_data as gm_data
import gmhazard_calc.modules.location as site
from qcore.simulation_structure import get_realisation_name

EMP_FILE_COLUMN_NAMES = [
    "SrcName",
    "Mag",
    "Rrup",
    "Rjb",
    "Rx",
    "MeanIm",
    "Stdv",
    "RupProb",
    "TectType",
]


IM_TO_FILE_IM_MAPPING = {
    "PGA": "PGA",
    "pSA_0.1": "SA(0p1)",
    "pSA_0.2": "SA(0p2)",
    "pSA_0.5": "SA(0p5)",
    "pSA_1.0": "SA(1p0)",
    "pSA_2.0": "SA(2p0)",
    "pSA_3.0": "SA(3p0)",
    "pSA_5.0": "SA(5p0)",
}

IM_MEAN_FORMAT_STR = "{}_mean"
IM_STD_FORMAT_STR = "{}_std"


def process_station(
    emp_ffp: str, ens: gm_data.Ensemble, ims_dict: Dict, faults_start_with: str = None
):
    emp_fname = os.path.basename(emp_ffp)

    # Get the location specific part of the filename
    emp_stat_loc = emp_fname.split("_")[:3]
    lat = float(emp_stat_loc[1][3:].replace("p", "."))
    lon = float(emp_stat_loc[2][3:].replace("p", "."))

    site_info, dist = site.Site.get_site_from_coords(ens, lat, lon)

    if dist > 0.5:
        raise Exception("This distance seems a bit large?")

    dfs = []
    for im, im_path in ims_dict.items():

        # This is probably rather in-efficient
        cur_emp_ffp = emp_fname.split("_")
        cur_emp_ffp[4] = IM_TO_FILE_IM_MAPPING[im]
        cur_emp_ffp = os.path.join(im_path, "_".join(cur_emp_ffp))

        cur_df = pd.read_csv(
            cur_emp_ffp,
            sep="\t",
            names=EMP_FILE_COLUMN_NAMES,
            header=0,
            index_col="SrcName",
        )

        # Only interested in columns mean and std
        # Also drop all rows with a rup probability of zero
        cur_df = cur_df.loc[cur_df.RupProb != 0.0, ("MeanIm", "Stdv")]
        cur_df = cur_df.rename(
            columns={
                "MeanIm": IM_MEAN_FORMAT_STR.format(im),
                "Stdv": IM_STD_FORMAT_STR.format(im),
            }
        )

        if faults_start_with is not None:
            cur_df = cur_df.loc[
                np.char.startswith(cur_df.index.values.astype(str), faults_start_with)
            ]

        # If one is empty, then all others for that station are also empty
        if cur_df.shape[0] == 0:
            return site_info, None

        dfs.append(cur_df)

    station_df = pd.concat(dfs, axis=1)
    return site_info, station_df


def generate_realisations(
    fault: str, station_df: pd.DataFrame, ims: List[str], n_rel: int = 50
):
    """Generates realisation data in the format [n_rel, n_ims]"""
    im_values = []
    for im in ims:
        # Yes, this actually makes sense! Think about it! (Or just debug it)
        ppf_y = np.arange(0.5 / n_rel, 1, 1 / n_rel)

        im_values.append(
            np.exp(
                norm.ppf(
                    ppf_y,
                    loc=station_df.loc[fault, IM_MEAN_FORMAT_STR.format(im)],
                    scale=station_df.loc[fault, IM_STD_FORMAT_STR.format(im)],
                )
            )
        )

    return np.vstack(im_values).T


def main(
    input_dir: str,
    output_dir: str,
    ensemble_id: str,
    faults_start_with: str,
    n_procs: int,
):
    im_dirs = next(os.walk(input_dir))[1]
    ims_dict = {
        utils.convert_im_type(im_dir): os.path.join(input_dir, im_dir)
        for im_dir in im_dirs
    }
    ims = list(ims_dict.keys())

    # Get all the fault/station combinations for which we have data,
    # can be done using any of the IMs
    # cur_im = list(ims_dict.keys())[0]
    cur_im = "pSA_5.0"
    cur_emp_files = glob.glob(os.path.join(ims_dict[cur_im], "EmpiricalPsha_Lat*.txt"))

    # Get the station data
    print("Collecting station data")
    ens = gm_data.Ensemble(ensemble_id)
    station_data = []
    if n_procs == 1:
        for cur_file in cur_emp_files:
            station_data = process_station(
                cur_file, ens, ims_dict, faults_start_with=faults_start_with
            )
    else:
        with mp.Pool(n_procs) as pool:
            station_data = pool.starmap(
                process_station,
                [
                    (cur_file, ens, ims_dict, faults_start_with)
                    for cur_file in cur_emp_files
                ],
            )

    station_dict = {
        cur_site_info.station_name: cur_df for cur_site_info, cur_df in station_data
    }

    # Get the fault -> stations mapping
    print("Creating fault -> station mapping")
    fault_dict = {}
    for cur_station, cur_df in station_dict.items():
        if cur_df is None:
            continue

        for cur_fault in cur_df.index.values:
            if cur_fault in fault_dict.keys():
                fault_dict[cur_fault].append(cur_station)
            else:
                fault_dict[cur_fault] = [cur_station]

    # Wri
    n_rel = 50
    for cur_fault in fault_dict.keys():
        fault_dir = os.path.join(output_dir, cur_fault)
        os.mkdir(fault_dir)

        # Initialize 3d array of format [n_rel, n_ims, n_stations]
        fault_data = np.zeros((n_rel, len(ims), len(fault_dict[cur_fault])))
        for ix, cur_station in enumerate(fault_dict[cur_fault]):
            cur_im_values = generate_realisations(
                cur_fault, station_dict[cur_station], ims, n_rel=n_rel
            )
            fault_data[:, :, ix] = cur_im_values

        # Write the realisation data
        for rel_ix in range(n_rel):
            df = pd.DataFrame(
                index=fault_dict[cur_fault],
                columns=ims,
                data=fault_data[rel_ix, :, :].T,
            )
            df["component"] = "geom"

            rel_name = get_realisation_name(cur_fault, rel_ix)
            cur_ouput_dir = os.path.join(fault_dir, rel_name, "IM_calc")
            os.makedirs(cur_ouput_dir)

            df.to_csv(
                os.path.join(cur_ouput_dir, f"{rel_name}.csv"),
                index_label="station",
                columns=["component"] + ims,
            )

            continue

    exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input_dir",
        type=str,
        help="Directory that contains a directory for each IM, "
        "and each IM data_dir contains a set of EmpiricalPsha_* files",
    )
    parser.add_argument("output_dir", type=str, help="Output data_dir")
    parser.add_argument(
        "--faults_start_with",
        type=str,
        help="If specified, then only faults starting "
        "with the specified string will be used.",
        default=None,
    )
    parser.add_argument(
        "--n_procs", type=int, help="Number of processes to use", default=4
    )
    args = parser.parse_args()

    ensemble_id = "v18p6sim"
    main(
        args.input_dir,
        args.output_dir,
        ensemble_id,
        args.faults_start_with,
        args.n_procs,
    )
