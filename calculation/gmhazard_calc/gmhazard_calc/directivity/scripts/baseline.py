"""
Computes the baseline values default of 20,000 hypocenters using Monte Carlo placement and distributions
which can be used to compare against other methods to determine
how close can you get to the 'expected' results
"""
import time
import multiprocessing as mp
import argparse
from pathlib import Path

import numpy as np

import common
from gmhazard_calc import directivity
from gmhazard_calc.constants import HypoMethod


def perform_mp_directivity(
    fault_name,
    n_hypo_data,
    period,
    grid_space,
    nhm_dict,
    output_dir,
):
    print(f"Computing for {fault_name}")

    fault, site_coords, planes, lon_lat_depth, x, y = directivity.utils.load_fault_info(
        fault_name, nhm_dict, grid_space
    )

    fdi, fdi_array, phi_red = directivity.compute_fault_directivity(
        lon_lat_depth,
        planes,
        site_coords,
        n_hypo_data,
        fault.mw,
        fault.rake,
        periods=[period],
    )

    fdi = fdi.reshape(grid_space, grid_space)

    nhyp = n_hypo_data.nhypo
    title = f"{fault_name} Length={fault.length} Dip={fault.dip} Rake={fault.rake}"
    directivity.validation.plots.plot_fdi(
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
        help="List of faults to calculate for",
    )
    parser.add_argument(
        "--nstrike",
        default=200,
        help="Number of hypocentres along strike",
    )
    parser.add_argument(
        "--ndip",
        default=100,
        help="Number of hypocentres down dip",
    )
    parser.add_argument(
        "--nhypo",
        default=20000,
        help="How many hypocentres total",
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
        help="Number of sites to do along each axis",
    )
    parser.add_argument(
        "--n_procs",
        default=6,
        help="Number of processes to use",
    )

    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()

    n_hypo_data = directivity.NHypoData(
        HypoMethod[args.method], args.nhypo, args.nstrike, args.ndip
    )

    start_time = time.time()

    with mp.Pool(processes=args.n_procs) as pool:
        pool.starmap(
            perform_mp_directivity,
            [
                (
                    fault,
                    n_hypo_data,
                    args.period,
                    args.grid_space,
                    nhm_dict,
                    args.output_dir,
                )
                for fault in args.faults
            ],
        )

    print(f"FINISHED and took {time.time() - start_time}")
