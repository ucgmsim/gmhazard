import argparse

import numpy as np
import matplotlib.pyplot as plt

import common

"""
Plots a histogram for each of the 9 sites to show difference in fd averaged values
over the monte carlo repeats of the directivity calculation
"""


def site_mc_hist(input_dir, faults, nhyps, repeats, grid_space, sample, output_dir):
    for fault_name in faults:
        sites = [[x, y] for x in sample for y in sample]
        for x, site in enumerate(sites):
            fig = plt.figure(figsize=(16, 10))
            for i, nhyp in enumerate(nhyps):
                total = np.load(
                    f"{input_dir}/{fault_name}_{nhyp}_total_fd.npy"
                ).reshape((repeats, grid_space, grid_space, 1))
                site_100 = total[:, site[0], site[1]]
                ax1 = fig.add_subplot(2, 2, i + 1)
                ax1.set_xlabel("fD")
                ax1.set_ylabel("Count")
                plt.title(f"{fault_name} {nhyp} Site {x+1}")
                plt.hist(site_100)
            plt.subplots_adjust(
                left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4, hspace=0.4
            )
            fig.savefig(f"{output_dir}/convergance_{fault_name}_site_{x}.png")


def parse_args():
    nhm_dict, faults, im, grid_space, _ = common.default_variables()

    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
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
        "--repeats",
        default=100,
        help="Times directivity calculation was repeated",
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

    site_mc_hist(
        args.input_dir,
        args.faults,
        args.fault_types,
        args.nhyps,
        args.repeats,
        args.grid_space,
        args.sample,
    )
