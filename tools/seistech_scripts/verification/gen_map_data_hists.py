"""Generates histogram plots for the specified .xyz map data files"""
import os
import json
import glob
import argparse
import multiprocessing as mp

import pandas as pd
import matplotlib.pyplot as plt

import seistech_utils as su


def plot_hist(data_ffp: str, n_bins: int = 15, no_clobber: bool = False):
    """Plots a histogram for the given dataframe csv file, which is expected
    to have the columns station_name, lon, lat, value.
    Adds x-label and title if a metadata file exists for the specified data file"""
    out_ffp = su.utils.change_file_ext(data_ffp, "_hist.png", excl_dot=True)
    if no_clobber and os.path.exists(out_ffp):
        print(f"Output file {os.path.basename(out_ffp)} already exists, skipping")
        return

    df = pd.read_csv(data_ffp, index_col="station_name")
    plt.hist(df.value.values, bins=n_bins)

    # Check if there is a metadata file
    meta_ffp = su.utils.change_file_ext(data_ffp, "json")
    if os.path.exists(meta_ffp):
        try:
            with open(meta_ffp, "r") as f:
                meta_dict = json.load(f)
        except json.decoder.JSONDecodeError as e:
            print(
                f"Failed to decode metadata file {os.path.basename(meta_ffp)}, "
                f"no meta data added to plot."
            )
            plt.title("Failed to read metadata")
            return

        # Set the title and x-label
        plt.title(meta_dict.get("plot_title"))
        plt.xlabel(meta_dict.get("im"))

    print(f"Saving figure {os.path.basename(out_ffp)}")
    plt.savefig(out_ffp)
    plt.close()


def main(
    data_dir: str,
    file_filter: str,
    n_bins: int = 15,
    recursive: bool = False,
    n_procs: int = 4,
    no_clobber: bool = False,
):
    # Get the files
    file_filter = (
        os.path.join(data_dir, "**", file_filter)
        if recursive
        else os.path.join(data_dir, file_filter)
    )
    files = glob.glob(file_filter, recursive=recursive)

    if n_procs == 1:
        for cur_file in files:
            plot_hist(cur_file, n_bins=n_bins, no_clobber=no_clobber)
    else:
        with mp.Pool(processes=n_procs) as p:
            p.starmap(plot_hist, [(cur_file, n_bins, no_clobber) for cur_file in files])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "data_dir", type=str, help="Data dir that contains the map files"
    )
    parser.add_argument(
        "file_filter", type=str, help="Glob filter for selection of files of interest"
    )
    parser.add_argument("--recursive", action="store_true", default=False)
    parser.add_argument(
        "--n_bins", type=int, help="Number of bins to use for the histogram", default=15
    )
    parser.add_argument("--n_procs", type=int)
    parser.add_argument(
        "--no_clobber",
        action="store_true",
        default=False,
        help="If specified then existing histograms are not overwritten",
    )

    args = parser.parse_args()

    main(
        args.data_dir,
        args.file_filter,
        n_bins=args.n_bins,
        recursive=args.recursive,
        n_procs=args.n_procs,
        no_clobber=args.no_clobber,
    )
