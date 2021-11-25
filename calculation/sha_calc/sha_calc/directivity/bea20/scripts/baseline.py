import time
import multiprocessing as mp
from pathlib import Path

import numpy as np

import sha_calc
from sha_calc.directivity.bea20.validation.plots import plot_fdi
import gmhazard_calc.rupture as rupture
import common

# Constant / Adjustable variables
nhm_dict, faults, im, grid_space, _ = common.default_variables()
nhyp = 20000
hypo_along_strike = 200
hypo_down_dip = 100
n_procs = 30


def perform_mp_directivity(fault_name):
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
        periods=[im.period],
        fault_name=fault_name,
    )

    fdi = fdi.reshape(grid_space, grid_space)

    title = f"{fault_name} Length={fault.length} Dip={fault.dip} Rake={fault.rake}"
    plot_fdi(
        x,
        y,
        fdi,
        lon_lat_depth,
        Path(
            f"/mnt/mantle_data/joel_scratch/directivity/new_baseline/plots/{fault_name}_{nhyp}_mu.png"
        ),
        title,
    )
    np.save(
        f"/mnt/mantle_data/joel_scratch/directivity/new_baseline/{fault_name}_{nhyp}_fd_array.npy",
        np.exp(fdi_array),
    )
    np.save(
        f"/mnt/mantle_data/joel_scratch/directivity/new_baseline/{fault_name}_{nhyp}_fd.npy",
        np.exp(fdi),
    )
    np.save(
        f"/mnt/mantle_data/joel_scratch/directivity/new_baseline/{fault_name}_{nhyp}_phi_red.npy",
        np.exp(phi_red),
    )


if __name__ == "__main__":
    start_time = time.time()

    pool = mp.Pool(n_procs)
    pool.map(perform_mp_directivity, faults)
    pool.close()

    print(f"FINISHED and took {time.time() - start_time}")
