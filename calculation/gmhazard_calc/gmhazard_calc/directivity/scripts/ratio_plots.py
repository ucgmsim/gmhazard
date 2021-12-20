import argparse

import numpy as np
import matplotlib.pyplot as plt

import common
from gmhazard_calc import directivity

"""
Plots the ratio difference between two fd results from using different methods
or hypocentre locations or to compare against the baseline
"""


def plot_ratio(
    old_data_dir,
    new_data_dir,
    faults,
    nhyps,
    nhm_dict,
    grid_space,
    output_dir,
):
    for fault_name in faults:
        for nhyp in nhyps:
            fault, _, planes, lon_lat_depth, x, y = directivity.load_fault_info(
                fault_name, nhm_dict, grid_space
            )

            try:
                fdi_average = np.load(
                    f"{old_data_dir}/{fault_name}_{nhyp}_total_fd.npy"
                )
                fdi_average = np.mean(fdi_average, axis=0)
                fdi_average = fdi_average.reshape((grid_space, grid_space))

                new_fd = np.load(f"{new_data_dir}/{fault_name}_{nhyp}_fd_average.npy")
                new_fd = new_fd.reshape((grid_space, grid_space))

                ratio = new_fd / fdi_average

                title = f"{fault_name} Length={fault.length} Dip={fault.dip} Rake={fault.rake}"
                fig, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)

                c = ax1.pcolormesh(x, y, ratio, cmap="bwr", vmax=1.2, vmin=0.8)
                ax1.scatter(
                    lon_lat_depth[:, 0][::2],
                    lon_lat_depth[:, 1][::2],
                    c=lon_lat_depth[:, 2][::2],
                    label="srf points",
                    s=1.0,
                )
                plt.colorbar(c)
                ax1.set_title(title)

                fig.savefig(f"{output_dir}/{fault_name}_{nhyp}.png")
            except FileNotFoundError:
                print(f"Could not find file - Skipping {fault_name} {nhyp}")


def parse_args():
    nhm_dict, faults, im, grid_space, _ = common.default_variables()

    parser = argparse.ArgumentParser()
    parser.add_argument("old_data_dir")
    parser.add_argument("new_data_dir")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--faults",
        default=faults,
        nargs="+",
        help="List of faults to produce results for",
    )
    parser.add_argument(
        "--nhyps",
        default=[5, 15, 30, 50],
        nargs="+",
        help="List of Hypocentre comparisons",
    )
    parser.add_argument(
        "--grid_space",
        default=grid_space,
        help="Number of sites to do along each axis",
    )
    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()

    plot_ratio(
        args.old_data_dir,
        args.new_data_dir,
        args.faults,
        args.nhyps,
        nhm_dict,
        args.grid_space,
        args.output_dir,
    )
