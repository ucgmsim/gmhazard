from random import sample
import numpy as np
import pandas as pd

import common
import sha_calc
from qcore.formats import load_station_file

# Load common variables
nhm_dict, _, im, grid_space, _ = common.default_variables()
fault_name = "Wairau"
nhyps = [5, 15, 30, 50, 100, 1000]

site_names = sample(list(np.load("/home/joel/local/directivity/wairau_stations.npy")), 1000)

stat_file = "/mnt/mantle_data/seistech/sites/18p6/non_uniform_whole_nz_with_real_stations-hh400_v18p6_land.ll"
stat_df = load_station_file(stat_file)

site_coords = np.asarray(stat_df.loc[site_names].values)

column_values = []
for x in nhyps:
    column_values.append(f"FD_{x}")
    column_values.append(f"PHI_RED_{x}")
df = pd.DataFrame(index=site_names, columns=column_values)

# PREP
fault, _, planes, lon_lat_depth, _, _ = common.load_fault_info(fault_name, nhm_dict, grid_space)

df = df.sort_index(ascending=False)

for nhpy in nhyps:
    hypo_along_strike = nhpy
    hypo_down_dip = 1

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
        return_fdi_array=False,
    )

    df[f"FD_{nhpy}"] = np.exp(fdi)
    df[f"PHI_RED_{nhpy}"] = phi_red

df.to_csv("/home/joel/local/directivity/Wairau_sites.csv")
