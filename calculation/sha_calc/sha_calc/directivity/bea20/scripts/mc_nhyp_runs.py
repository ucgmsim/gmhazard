import pandas as pd
import multiprocessing as mp

from sha_calc.directivity.bea20.validation.plots import plot_fdi
from pathlib import Path

import gmhazard_calc
from gmhazard_calc.im import IM, IMType
import time
import gmhazard_calc.rupture as rupture
import sha_calc
from qcore import nhm
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from sha_calc.directivity.bea20.utils import EventType
from sha_calc.directivity.bea20 import bea20, utils
import os
import subprocess
import sys


im = IM(IMType.pSA, period=3.0)
ens = gmhazard_calc.gm_data.Ensemble("v20p5emp")
branch = ens.get_im_ensemble(im.im_type).branches[0]

# nhyp = 20000
# hypo_along_strike = 200
# hypo_down_dip = 100
nhm_dict = nhm.load_nhm(branch.flt_erf_ffp)
grid_space = 100
# faults = list(nhm_dict.keys())
faults = ["Ashley", "AlpineK2T", "AlfMakuri", "ArielNorth", "Swedge1", "Wairau"]
nhyps = [5, 15, 30, 50, 100]
combo = [(fault, strike, 1) for strike in nhyps for fault in faults]
n_procs = 2


def perform_mp_directivity(combo):
    fault_name, hypo_along_strike, hypo_down_dip = combo
    nhyp = hypo_along_strike * hypo_down_dip
    print(f"Computing for {fault_name} {nhyp}")

    # PREP
    fault = nhm_dict[fault_name]
    planes, lon_lat_depth = rupture.get_fault_header_points(fault)

    lon_values = np.linspace(
        lon_lat_depth[:, 0].min() - 0.5, lon_lat_depth[:, 0].max() + 0.5, grid_space
    )
    lat_values = np.linspace(
        lon_lat_depth[:, 1].min() - 0.5, lon_lat_depth[:, 1].max() + 0.5, grid_space
    )

    x, y = np.meshgrid(lon_values, lat_values)
    site_coords = np.stack((x, y), axis=2).reshape(-1, 2)

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
        Path(f"/mnt/mantle_data/joel_scratch/directivity/latin_mc/plots/{fault_name}_{nhyp}.png"),
        title,
    )
    np.save(f"/mnt/mantle_data/joel_scratch/directivity/latin_mc/{fault_name}_{nhyp}_fd_mc_hypo_array.npy", np.exp(total_fd_array))
    np.save(f"/mnt/mantle_data/joel_scratch/directivity/latin_mc/{fault_name}_{nhyp}_fd_mc.npy", np.exp(total_fd))
    np.save(f"/mnt/mantle_data/joel_scratch/directivity/latin_mc/{fault_name}_{nhyp}_fd_average.npy", np.exp(fdi_average))


if __name__ == '__main__':
    start_time = time.time()

    pool = mp.Pool(n_procs)
    pool.map(perform_mp_directivity, combo)
    pool.close()

    print(f"FINISHED and took {time.time() - start_time}")