import time
import multiprocessing as mp
from pathlib import Path
import argparse

import numpy as np

import sha_calc
from sha_calc.directivity.bea20.validation.plots import plot_fdi
import common


def perform_mp_directivity(
    fault_name,
    hypo_along_strike,
    hypo_down_dip,
    method,
    repeats,
    period,
    grid_space,
    nhm_dict,
    output_dir,
):
    nhyp = hypo_along_strike * hypo_down_dip
    print(f"Computing for {fault_name} {nhyp}")

    fault, site_coords, planes, lon_lat_depth, x, y = common.load_fault_info(
        fault_name, nhm_dict, grid_space
    )

    total_fd = np.zeros((repeats, len(site_coords), 1))
    total_fd_array = np.zeros((repeats, nhyp, len(site_coords), 1))

    for i in range(repeats):
        fdi, fdi_array, phi_red = sha_calc.bea20.compute_fault_directivity(
            lon_lat_depth,
            planes,
            site_coords,
            hypo_along_strike,
            hypo_down_dip,
            fault.mw,
            fault.rake,
            periods=[period],
            method=method,
        )

        total_fd[i] = fdi
        total_fd_array[i] = fdi_array

    fdi_average = np.mean(total_fd, axis=0)
    fdi_average = fdi_average.reshape((grid_space, grid_space))

    title = f"{fault_name} Length={fault.length} Dip={fault.dip} Rake={fault.rake}"
    plot_fdi(
        x,
        y,
        fdi_average,
        lon_lat_depth,
        Path(f"{output_dir}/{fault_name}_{nhyp}.png"),
        title,
    )
    np.save(
        f"{output_dir}/{fault_name}_{nhyp}_fd_mc_hypo_array.npy",
        np.exp(total_fd_array),
    )
    np.save(
        f"{output_dir}/{fault_name}_{nhyp}_fd_mc.npy",
        np.exp(total_fd),
    )
    np.save(
        f"{output_dir}/{fault_name}_{nhyp}_fd_average.npy",
        np.exp(fdi_average),
    )


def parse_args():
    nhm_dict, faults, im, grid_space, nhyps = common.default_variables()

    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir")
    parser.add_argument(
        "--faults",
        default=faults,
        nargs="+",
        help="Which faults to calculate for",
    )
    parser.add_argument(
        "--nstrikes",
        default=[5],
        nargs="+",
        help="How many hypocentres along strike",
    )
    parser.add_argument(
        "--ndips",
        default=[1],
        nargs="+",
        help="How many hypocentres down dip",
    )
    parser.add_argument(
        "--method",
        default="Hypercube",
        help="Method to place hypocentres",
    )
    parser.add_argument(
        "--repeats",
        default=100,
        help="Times to repeat directivity calculation",
    )
    parser.add_argument(
        "--period",
        default=im.period,
        help="Period to calculate directivity for",
    )
    parser.add_argument(
        "--grid_space",
        default=grid_space,
        help="How many sites to do along each axis",
    )
    parser.add_argument(
        "--n_procs",
        default=30,
        help="Number of processes to use",
    )

    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()
    n_procs = 30

    start_time = time.time()

    with mp.Pool(processes=args.n_procs) as pool:
        pool.starmap(
            perform_mp_directivity,
            [
                (
                    fault,
                    strike,
                    args.ndips[i],
                    args.method,
                    args.repeats,
                    args.period,
                    args.grid_space,
                    nhm_dict,
                    args.output_dir,
                )
                for i, strike in enumerate(args.nstrikes)
                for fault in args.faults
            ],
        )

    print(f"FINISHED and took {time.time() - start_time}")
