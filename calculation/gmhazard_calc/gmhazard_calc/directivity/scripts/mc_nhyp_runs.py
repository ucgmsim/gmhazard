import time
import multiprocessing as mp
import argparse
from pathlib import Path

import numpy as np

from gmhazard_calc import directivity
import sha_calc
import common


def perform_mp_directivity(
    fault_name,
    hypo_along_strike,
    hypo_down_dip,
    nhypo,
    method,
    repeats,
    period,
    grid_space,
    nhm_dict,
    output_dir,
):
    if nhypo is None:
        nhypo = hypo_along_strike * hypo_down_dip
    print(f"Computing for {fault_name} {nhypo}")

    fault, site_coords, planes, lon_lat_depth, x, y = directivity.utils.load_fault_info(
        fault_name, nhm_dict, grid_space
    )
    n_hypo_data = directivity.NHypoData(method, nhypo, hypo_along_strike, hypo_down_dip)

    total_fd = np.zeros((repeats, len(site_coords), 1))
    total_fd_array = np.zeros((repeats, nhypo, len(site_coords), 1))

    for i in range(repeats):
        fdi, fdi_array, phi_red = directivity.compute_fault_directivity(
            lon_lat_depth,
            planes,
            site_coords,
            n_hypo_data,
            fault.mw,
            fault.rake,
            periods=[period],
        )

        total_fd[i] = fdi
        total_fd_array[i] = fdi_array

    fdi_average = np.mean(total_fd, axis=0)
    fdi_average = fdi_average.reshape((grid_space, grid_space))

    title = f"{fault_name} Length={fault.length} Dip={fault.dip} Rake={fault.rake}"
    directivity.validation.plots.plot_fdi(
        x,
        y,
        fdi_average,
        lon_lat_depth,
        Path(f"{output_dir}/{fault_name}_{nhypo}.png"),
        title,
    )
    np.save(
        f"{output_dir}/{fault_name}_{nhypo}_fd_mc_hypo_array.npy",
        np.exp(total_fd_array),
    )
    np.save(
        f"{output_dir}/{fault_name}_{nhypo}_fd_mc.npy",
        np.exp(total_fd),
    )
    np.save(
        f"{output_dir}/{fault_name}_{nhypo}_fd_average.npy",
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
        help="List of faults to calculate",
    )
    parser.add_argument(
        "--nstrikes",
        default=None,
        nargs="+",
        help="List of hypocentres along strike",
    )
    parser.add_argument(
        "--ndips",
        default=None,
        nargs="+",
        help="List of hypocentres down dip",
    )
    parser.add_argument(
        "--nhypos",
        default=None,
        nargs="+",
        help="List of hypocentre totals",
    )
    parser.add_argument(
        "--method",
        default="LATIN_HYPERCUBE",
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
        help="Number of sites to do along each axis",
    )
    parser.add_argument(
        "--n_procs",
        default=30,
        help="Number of processes to use",
    )

    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()

    start_time = time.time()

    with mp.Pool(processes=args.n_procs) as pool:
        pool.starmap(
            perform_mp_directivity,
            [
                (
                    fault,
                    strike,
                    None if args.ndips is None else args.ndips[i],
                    None if args.nhypos is None else args.nhypos[i],
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
