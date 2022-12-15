"""
Compute directivity values multiple times specified by a repeating value
To understand the standard deviation in results for the different number of hypocentres
"""
import time
import argparse
import multiprocessing as mp
from pathlib import Path

import numpy as np

from qcore import nhm
import gmhazard_calc
from gmhazard_calc.im import IM, IMType
from gmhazard_calc import directivity
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
    repeat_n_procs: int,
    hypo_n_procs: int,
):
    assert repeat_n_procs == 1 or hypo_n_procs == 1

    if nhypo is None:
        nhypo = hypo_along_strike * hypo_down_dip
    print(f"Computing for {fault_name} {nhypo}")

    fault, site_coords, planes, lon_lat_depth, x, y = directivity.utils.load_fault_info(
        fault_name, nhm_dict, grid_space
    )
    n_hypo_data = directivity.NHypoData(
        gmhazard_calc.HypoMethod(method), nhypo, hypo_along_strike, hypo_down_dip
    )

    if n_hypo_data.method in [
        gmhazard_calc.HypoMethod.monte_carlo,
        gmhazard_calc.HypoMethod.latin_hypercube,
    ]:
        total_fd = np.zeros((repeats, len(site_coords), 1))
        total_fd_array = np.zeros((repeats, nhypo, len(site_coords), 1))

        if repeat_n_procs == 1:
            for i in range(repeats):
                fdi, fdi_array, _ = directivity.compute_fault_directivity(
                    lon_lat_depth,
                    planes,
                    site_coords,
                    n_hypo_data,
                    fault.mw,
                    fault.rake,
                    periods=[period],
                    n_procs=hypo_n_procs,
                )

                total_fd[i] = fdi
                total_fd_array[i] = fdi_array
        else:
            with mp.Pool(repeat_n_procs) as pool:
                results = pool.starmap(
                    directivity.compute_fault_directivity,
                    [
                        (
                            lon_lat_depth,
                            planes,
                            site_coords,
                            n_hypo_data,
                            fault.mw,
                            fault.rake,
                            [period],
                            1,
                        )
                        for ix in range(repeats)
                    ],
                )

                for ix, cur_result in enumerate(results):
                    total_fd[ix] = cur_result[0]
                    total_fd_array[ix] = cur_result[1]

        fdi_average = np.mean(total_fd, axis=0)
        fdi_average = fdi_average.reshape((grid_space, grid_space))
    else:
        fdi, fdi_array, _ = directivity.compute_fault_directivity(
            lon_lat_depth,
            planes,
            site_coords,
            n_hypo_data,
            fault.mw,
            fault.rake,
            periods=[period],
            n_procs=hypo_n_procs,
        )
        total_fd = fdi
        fdi_average = fdi.reshape((100, 100))
        total_fd_array = fdi_array

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
        type=int,
        help="List of hypocentres along strike",
    )
    parser.add_argument(
        "--ndips",
        default=None,
        nargs="+",
        type=int,
        help="List of hypocentres down dip",
    )
    parser.add_argument(
        "--nhypos",
        default=None,
        nargs="+",
        type=int,
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
        type=int,
        help="Times to repeat directivity calculation",
    )
    parser.add_argument(
        "--period",
        default=im.period,
        type=float,
        help="Period to calculate directivity for",
    )
    parser.add_argument(
        "--grid_space",
        default=grid_space,
        type=int,
        help="Number of sites to do along each axis",
    )
    parser.add_argument(
        "--repeat_n_procs",
        default=1,
        type=int,
        help="Number of processes to use to process the number of repeats."
        "Note: Only one of repeat_n_procs and hypo_n_procs can be greater than one",
    )
    parser.add_argument(
        "--hypo_n_procs",
        default=1,
        type=int,
        help="Number of processes to use for hypocentre computation. "
        "Note: Only one of repeat_n_procs and hypo_n_procs can be greater than one",
    )

    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()

    n_hypo_comb = len(args.nhypos) if args.nhypos is not None else len(args.nstrikes)

    start_time = time.time()
    for fault in args.faults:
        for ix in range(n_hypo_comb):
            perform_mp_directivity(
                fault,
                None if args.nstrikes is None else args.nstrikes[ix],
                None if args.ndips is None else args.ndips[ix],
                None if args.nhypos is None else args.nhypos[ix],
                args.method,
                args.repeats,
                args.period,
                args.grid_space,
                nhm_dict,
                args.output_dir,
                args.repeat_n_procs,
                args.hypo_n_procs,
            )

    print(f"FINISHED and took {time.time() - start_time}")
