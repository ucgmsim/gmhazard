"""
Plots the mean and standard deviation between the different hypocentre locations used to compute fd
can be produced in either a contour or mesh grid
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt

import common
from gmhazard_calc.directivity import utils


def std_mean_plots(
    baseline_dir,
    input_dir,
    faults,
    nhyps,
    nhm_dict,
    grid_space,
    colour_mode,
    output_dir,
):
    for fault_name in faults:
        fault, _, planes, lon_lat_depth, x, y = utils.load_fault_info(
            fault_name, nhm_dict, grid_space
        )

        modes = ["std", "mean bias"]

        baseline_array = np.load(f"{baseline_dir}/{fault_name}_20000_fd.npy").reshape(
            (10000, 1)
        )

        for mode in modes:
            fig = plt.figure(figsize=(16, 10))

            for i, nhyp in enumerate(nhyps):
                fd_array = np.load(f"{input_dir}/{fault_name}_{nhyp}_fd_mc.npy")
                ratio = np.log(fd_array / baseline_array)

                if mode == "std":
                    values = np.std(ratio, axis=0).reshape((grid_space, grid_space))
                else:
                    values = np.mean(ratio, axis=0).reshape((grid_space, grid_space))

                ax1 = fig.add_subplot(2, 2, i + 1)
                if mode == "std":
                    bounds = list(np.round(np.linspace(0, 0.05, 13), 3))
                    if colour_mode == "contour":
                        c = plt.contourf(
                            x,
                            y,
                            values,
                            levels=bounds,
                            cmap=plt.cm.get_cmap("Reds", 12),
                            extend="max",
                        )
                    elif colour_mode == "mesh":
                        c = ax1.pcolormesh(
                            x, y, values, cmap="Reds", vmax=0.05, vmin=0, shading="flat"
                        )
                else:
                    bounds = list(np.round(np.linspace(-0.01, 0.01, 21), 3))
                    colour_map = [
                        "#0000ff",
                        "#1b1bff",
                        "#3636ff",
                        "#5151ff",
                        "#6b6bff",
                        "#8686ff",
                        "#a1a1ff",
                        "#bcbcff",
                        "#d7d7ff",
                        "#ffffff",
                        "#ffffff",
                        "#ffd7d7",
                        "#ffbcbc",
                        "#ffa1a1",
                        "#ff8686",
                        "#ff6b6b",
                        "#ff5151",
                        "#ff3636",
                        "#ff1b1b",
                        "#ff0000",
                    ]
                    if colour_mode == "contour":
                        c = plt.contourf(
                            x,
                            y,
                            values,
                            levels=bounds,
                            colors=colour_map,
                            extend="both",
                        )
                    elif colour_mode == "mesh":
                        c = ax1.pcolormesh(
                            x,
                            y,
                            values,
                            cmap="bwr",
                            vmax=0.3,
                            vmin=-0.3,
                            shading="flat",
                        )
                ax1.scatter(
                    lon_lat_depth[:, 0][::2],
                    lon_lat_depth[:, 1][::2],
                    c=lon_lat_depth[:, 2][::2],
                    label="srf points",
                    s=1.0,
                )
                cb = plt.colorbar(c, pad=0)
                if mode == "mean bias":
                    cb.set_label("mean of (ln(estimate) - ln(exact))")
                else:
                    cb.set_label("std of (ln(estimate) - ln(exact))")
                ax1.set_title(f"{nhyp} Hypocentres")
                plt.xlabel("Longitude")
                plt.ylabel("Latitude")

            plt.subplots_adjust(
                left=0.1, bottom=0.1, right=0.95, top=0.90, wspace=0.40, hspace=0.35
            )
            fig.suptitle(f"{fault_name} {mode} across all sites", fontsize=16)
            if mode == "mean bias":
                fig.savefig(f"{output_dir}/{fault_name}_mean_bias.png")
            else:
                fig.savefig(f"{output_dir}/{fault_name}_{mode}.png")
            plt.close()


def parse_args():
    nhm_dict, faults, im, grid_space, _ = common.default_variables()

    parser = argparse.ArgumentParser()
    parser.add_argument("baseline_dir")
    parser.add_argument("input_dir")
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
    parser.add_argument(
        "--colour_mode",
        default="contour",
        help="'contour' for Contours and 'mesh' for a mesh square grid",
    )
    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()

    std_mean_plots(
        args.baseline_dir,
        args.input_dir,
        args.faults,
        args.nhyps,
        nhm_dict,
        args.grid_space,
        args.colour_mode,
        args.output_dir,
    )
