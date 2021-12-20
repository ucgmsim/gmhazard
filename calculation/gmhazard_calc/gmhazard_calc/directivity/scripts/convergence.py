import argparse

import numpy as np
import matplotlib.pyplot as plt

import common
from gmhazard_calc.directivity import utils

"""
Plots convergence over 9 site locations around the faults to compare different
number of hypocentres with how accurate they are to the baseline 'exact' values
"""


def convergence(input_dir, baseline_dir, faults, nhyps, grid_space, sample, output_dir):

    for fault_name in faults:
        fig = plt.figure(figsize=(16, 10))
        mean_values = dict()
        std_values = dict()
        try:
            baseline_array = np.load(f"{baseline_dir}/{fault_name}_20000_fd.npy")
            baseline_sites = [baseline_array[x, y] for x in sample for y in sample]

            for nhyp in nhyps:
                total = np.load(f"{input_dir}/{fault_name}_{nhyp}_fd_mc.npy")
                fdi_average = np.mean(total, axis=0).reshape((grid_space, grid_space))
                std_mc_average = np.std(total, axis=0).reshape((grid_space, grid_space))
                mean_values[nhyp] = [fdi_average[x, y] for x in sample for y in sample]
                std_values[nhyp] = [
                    std_mc_average[x, y] for x in sample for y in sample
                ]

            for site in range(9):
                ax1 = fig.add_subplot(3, 3, site + 1)
                ax1.set_xlabel("Number of Hypocentres")
                ax1.set_ylabel("Mean Directivity Amplification")
                plt.title(f"Site {site + 1}")

                ax1.errorbar(
                    x=[str(x) for x in list(mean_values.keys())],
                    y=[x[site] for x in list(mean_values.values())],
                    yerr=[x[site] for x in list(std_values.values())],
                    marker=".",
                    label="Estimate Across 100 Iterations",
                    color="blue",
                )
                plt.axhline(
                    y=baseline_sites[site], color="r", linestyle="-", label="Exact"
                )
                plt.legend()

            plt.subplots_adjust(
                left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4, hspace=0.4
            )
            fig.suptitle(f"{fault_name} Convergence")
            plt.savefig(f"{output_dir}/convergance_{fault_name}.png")

            fault, _, planes, lon_lat_depth, x, y = utils.load_fault_info(
                fault_name, nhm_dict, grid_space
            )

            lon_values = np.linspace(
                lon_lat_depth[:, 0].min() - 0.5,
                lon_lat_depth[:, 0].max() + 0.5,
                grid_space,
            )
            lat_values = np.linspace(
                lon_lat_depth[:, 1].min() - 0.5,
                lon_lat_depth[:, 1].max() + 0.5,
                grid_space,
            )

            site_x = [lon_values[a] for a in sample]
            site_y = [lat_values[a] for a in sample]
            site_x, site_y = np.meshgrid(site_x, site_y)

            title = f"{fault_name} Site Locations On Baseline Values"
            fig2, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)

            vmax = max(
                max(baseline_array.reshape(10000)) - 1,
                1 - min(baseline_array.reshape(10000)),
            )
            c = ax1.pcolormesh(
                x, y, baseline_array, cmap="bwr", vmax=1 + vmax, vmin=1 - vmax
            )
            ax1.scatter(
                lon_lat_depth[:, 0][::2],
                lon_lat_depth[:, 1][::2],
                c=lon_lat_depth[:, 2][::2],
                label="srf points",
                s=1.0,
            )
            plt.plot(site_x, site_y, "bo", color="black")
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            site_x = site_x.reshape(9)
            site_y = site_y.reshape(9)
            for site in range(9):
                plt.annotate(
                    f"Site {site + 1}",
                    (site_x[site], site_y[site]),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    fontsize=20,
                )
            cb = plt.colorbar(c)
            cb.set_label("fD Baseline")
            ax1.set_title(title)

            fig2.savefig(f"{output_dir}/{fault_name}_sites.png")
        except FileNotFoundError:
            print(f"Could not find file - Skipping {fault_name}")


def parse_args():
    nhm_dict, faults, im, grid_space, _ = common.default_variables()

    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("baseline_dir")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--faults",
        default=faults,
        nargs="+",
        help="List of faults to calculate for",
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
    parser.add_argument(
        "--sample",
        default=[24, 49, 74],
        nargs="+",
        help="Index of site locations of interest",
    )
    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()

    convergence(
        args.input_dir,
        args.baseline_dir,
        args.faults,
        args.fault_types,
        args.nhyps,
        args.grid_space,
        args.sample,
    )
