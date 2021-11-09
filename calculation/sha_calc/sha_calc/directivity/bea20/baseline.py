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

nhyp = 20000
hypo_along_strike = 200
hypo_down_dip = 100
nhm_dict = nhm.load_nhm(branch.flt_erf_ffp)
grid_space = 100
faults = list(nhm_dict.keys())

n_procs = 20

def perform_mp_directivity(fault_name):
    print(f"Computing for {fault_name}")

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

    # MODEL
    fdi, _ = None, None
    del fdi
    del _
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

    fdi = fdi.reshape(grid_space, grid_space)

    title = f"{fault_name} Length={fault.length} Dip={fault.dip} Rake={fault.rake}"
    plot_fdi(
        x,
        y,
        fdi,
        lon_lat_depth,
        Path(f"/mnt/mantle_data/joel_scratch/directivity/baseline/plots/{fault_name}_{nhyp}_mu.png"),
        title,
    )
    np.save(f"/mnt/mantle_data/joel_scratch/directivity/baseline/{fault_name}_{nhyp}_fd_array.npy", np.exp(fdi_array))
    np.save(f"/mnt/mantle_data/joel_scratch/directivity/baseline/{fault_name}_{nhyp}_fd.npy", np.exp(fdi))
    np.save(f"/mnt/mantle_data/joel_scratch/directivity/baseline/{fault_name}_{nhyp}_phi_red.npy", np.exp(phi_red))


if __name__ == '__main__':
    start_time = time.time()

    pool = mp.Pool(n_procs)
    pool.map(perform_mp_directivity, faults)
    pool.close()

    print(f"FINISHED and took {time.time() - start_time}")