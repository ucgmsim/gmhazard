import time
import multiprocessing as mp
from pathlib import Path
import argparse

import numpy as np

import sha_calc
from sha_calc.directivity.bea20.validation.plots import plot_fdi
from sha_calc.directivity.bea20.HypoMethod import HypoMethod
import common


def perform_mp_directivity(
    fault_name,
    hypo_along_strike,
    hypo_down_dip,
    method,
    period,
    grid_space,
    nhm_dict,
    output_dir,
):
    print(f"Computing for {fault_name}")

    fault, site_coords, planes, lon_lat_depth, x, y = common.load_fault_info(
        fault_name, nhm_dict, grid_space
    )

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

    fdi = fdi.reshape(grid_space, grid_space)

    nhyp = hypo_along_strike * hypo_down_dip
    title = f"{fault_name} Length={fault.length} Dip={fault.dip} Rake={fault.rake}"
    plot_fdi(
        x,
        y,
        fdi,
        lon_lat_depth,
        Path(f"{output_dir}/{fault_name}_{nhyp}_mu.png"),
        title,
    )
    np.save(
        f"{output_dir}/{fault_name}_{nhyp}_fd_array.npy",
        np.exp(fdi_array),
    )
    np.save(
        f"{output_dir}/{fault_name}_{nhyp}_fd.npy",
        np.exp(fdi),
    )
    np.save(
        f"{output_dir}/{fault_name}_{nhyp}_phi_red.npy",
        np.exp(phi_red),
    )


def parse_args():
    nhm_dict, faults, im, grid_space, _ = common.default_variables()

    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir")
    parser.add_argument(
        "--faults",
        default=faults,
        nargs="+",
        help="Which faults to calculate for",
    )
    parser.add_argument(
        "--nstrike",
        default=200,
        help="How many hypocentres along strike",
    )
    parser.add_argument(
        "--ndip",
        default=100,
        help="How many hypocentres down dip",
    )
    parser.add_argument(
        "--method",
        default="MONTE_CARLO",
        help="Method to place hypocentres",
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
        default=6,
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
                    args.nstrike,
                    args.ndip,
                    HypoMethod[args.method],
                    args.period,
                    args.grid_space,
                    nhm_dict,
                    args.output_dir,
                )
                for fault in args.faults
            ],
        )

    print(f"FINISHED and took {time.time() - start_time}")
