import time
import multiprocessing as mp
from pathlib import Path

import numpy as np

import sha_calc
from sha_calc.directivity.bea20.validation.plots import plot_fdi
import common

# Constant / Adjustable variables
nhm_dict, faults, im, grid_space, nhyps = common.default_variables()
combo = [(fault, strike, 1) for strike in nhyps for fault in faults]
n_procs = 30


def perform_mp_directivity(combo):
    fault_name, hypo_along_strike, hypo_down_dip = combo
    nhyp = hypo_along_strike * hypo_down_dip
    print(f"Computing for {fault_name} {nhyp}")

    fault, site_coords, planes, lon_lat_depth, x, y = common.load_fault_info(
        fault_name, nhm_dict, grid_space
    )

    repeats = 100

    total_fd = np.zeros((repeats, 10000, 1))
    total_fd_array = np.zeros((repeats, nhyp, 10000, 1))

    for i in range(repeats):
        fdi, fdi_array, phi_red = sha_calc.bea20.compute_fault_directivity(
            lon_lat_depth,
            planes,
            site_coords,
            hypo_along_strike,
            hypo_down_dip,
            fault.mw,
            fault.rake,
            periods=[im.period],
            fault_name=fault_name,
            return_fdi_array=True,
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
        Path(
            f"/mnt/mantle_data/joel_scratch/directivity/latin_mc/plots/{fault_name}_{nhyp}.png"
        ),
        title,
    )
    np.save(
        f"/mnt/mantle_data/joel_scratch/directivity/latin_mc/{fault_name}_{nhyp}_fd_mc_hypo_array.npy",
        np.exp(total_fd_array),
    )
    np.save(
        f"/mnt/mantle_data/joel_scratch/directivity/latin_mc/{fault_name}_{nhyp}_fd_mc.npy",
        np.exp(total_fd),
    )
    np.save(
        f"/mnt/mantle_data/joel_scratch/directivity/latin_mc/{fault_name}_{nhyp}_fd_average.npy",
        np.exp(fdi_average),
    )


if __name__ == "__main__":
    start_time = time.time()

    pool = mp.Pool(n_procs)
    pool.map(perform_mp_directivity, combo)
    pool.close()

    print(f"FINISHED and took {time.time() - start_time}")
