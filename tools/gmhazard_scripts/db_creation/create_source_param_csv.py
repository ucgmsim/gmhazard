"""Creates a source attribute csv file for a given Cybershake sources directory
"""
import os
import glob
import argparse
import multiprocessing as mp

import h5py
import pandas as pd
import numpy as np


def get_fault_data(sources_dir: str, fault_name: str):
    # Get the first info file
    info_files = glob.glob(os.path.join(sources_dir, fault_name, "Srf", "*.info"))

    data_dirs, rel_names = [], []
    for info_file in info_files:
        rel_names.append(os.path.basename(info_file).split(".")[0])

        with h5py.File(info_file, "r") as f:
            tect_type = (
                f.attrs["tect_type"] if "tect_type" in f.attrs.keys() else "ACTIVE_SHALLOW"
            )
            data_dirs.append({
                    "fault": fault_name,
                    "mag": f.attrs["mag"],
                    "tect_type": tect_type,
                    "hdepth": f.attrs["hdepth"],
                    "hlon": f.attrs["hlon"],
                    "hlat": f.attrs["hlat"]
            })

    return pd.DataFrame.from_records(data_dirs, index=rel_names)


def main(sources_dir: str, output_ffp: str, n_procs: int = 4):
    if os.path.isfile(output_ffp):
        print("The output file already exist, quitting!")
        exit()

    # Get all faults
    faults = np.asarray(next(os.walk(sources_dir))[1])

    # Collect data for each fault
    if n_procs == 1:
        rel_dfs = [
            get_fault_data(sources_dir, cur_fault) for cur_fault in faults
        ]
    else:
        with mp.Pool(processes=n_procs) as p:
            rel_dfs = p.starmap(
                get_fault_data, [(sources_dir, cur_fault) for cur_fault in faults]
            )

    src_df = pd.concat(rel_dfs)

    # Write dataframe
    src_df.to_csv(output_ffp, index=True, index_label="realisation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "sources_dir", type=str, help="The cybershake sources directory"
    )
    parser.add_argument(
        "output_ffp", type=str, help="The output file path for the source params csv"
    )
    parser.add_argument(
        "--n_procs", type=int, help="Number of processes to use", default=4
    )

    args = parser.parse_args()

    main(args.sources_dir, args.output_ffp, n_procs=args.n_procs)
