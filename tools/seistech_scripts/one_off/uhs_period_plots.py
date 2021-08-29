"""Generates UHS plots with different number of data points.
The plots are used to determine the number of periods of SA we need/want for
future UHS (seistech) plots.
"""
import os

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import sha_calc.src.ground_motion as gm
import sha_calc.src.hazard as haz
import seistech_calc as sc


exceedance = 0.00010025083647088573

ens = sc.gm_data.Ensemble("v19p5sim")

output_folder = "/home/cbs51/code/data/200218_uhs_115"

with sc.dbs.IMDBNonParametric("/home/cbs51/code/data/200108_v18p6_full_imdb/imdb_full.h5") as db:
    im_df = db.im_data("CCCC")

# Get SA periods that are in all the datasets
sa_ims, sa_periods = sc.shared.get_SA_periods(im_df.columns.values)
sa_ims, sa_periods = np.asarray(sa_ims), np.asarray(sa_periods)

# Sort
sort_ind = np.argsort(sa_periods)
sa_ims = sa_ims[sort_ind]
sa_periods = sa_periods[sort_ind]

sa_values = []
for im, period in zip(sa_ims, sa_periods):
    im_levels = sc.utils.get_im_values(im, n_values=50)

    # Loop over the IM values
    im_series = []
    for im_level in im_levels:
        im_series.append(gm.non_parametric_gm_prob(im_level, im_df[im]))

    cur_df = pd.concat(im_series, axis=1, join="inner")
    cur_df.columns = im_levels

    cur_df.index = sc.rupture.rupture_name_to_id(cur_df.index.values, ens._config["datasets"]["sim"]["flt_erf"])

    cur_hazard = haz.hazard_curve(cur_df, ens.rupture_df_id["annual_rec_prob"])

    sa_values.append(sc.hazard.exceedance_to_im(exceedance, cur_hazard.index.values, cur_hazard.values))

m_size = 3.0

n_periods = np.arange(10, 113, 10)
min_period, max_period = sa_periods.min(), sa_periods.max()
for cur_n_periods in n_periods:
    cur_sa_periods = np.linspace(min_period, max_period, cur_n_periods)
    cur_sa_values = np.interp(cur_sa_periods, sa_periods, sa_values)

    fig = plt.figure(figsize=(12, 9))
    plt.plot(cur_sa_periods, cur_sa_values, marker='o', ms=m_size)
    plt.title(cur_n_periods)

    plt.xlabel("Period (s)")
    plt.ylabel("SA (g)")

    fig.savefig(os.path.join(output_folder, f"UHS_{cur_n_periods}.png"))
    plt.close()

for cur_n_periods in n_periods:
    cur_sa_periods = np.exp(np.linspace(np.log(min_period + 1e-8), np.log(max_period), cur_n_periods))
    cur_sa_values = np.interp(cur_sa_periods, sa_periods, sa_values)

    fig = plt.figure(figsize=(12, 9))
    plt.plot(cur_sa_periods, cur_sa_values, marker='o', ms=m_size)
    plt.title(cur_n_periods)

    plt.xlabel("Period (s)")
    plt.ylabel("SA (g)")

    fig.savefig(os.path.join(output_folder, f"UHS_{cur_n_periods}_log.png"))
    plt.close()

fig = plt.figure(figsize=(12, 9))
plt.plot(sa_periods, sa_values, marker='o', ms=m_size)
plt.title(len(sa_periods))

plt.xlabel("Period (s)")
plt.ylabel("SA (g)")

fig.savefig(os.path.join(output_folder, f"UHS_orig_{len(sa_periods)}.png"))
plt.close()

for ix in range(2, 11):
    fig = plt.figure(figsize=(12, 9))
    plt.plot(sa_periods[::ix], sa_values[::ix], marker='o', ms=m_size)
    plt.title(len(sa_periods[::ix]))

    plt.xlabel("Period (s)")
    plt.ylabel("SA (g)")

    fig.savefig(os.path.join(output_folder, f"UHS_orig_{len(sa_periods[::ix])}_{ix}th.png"))
    plt.close()

exit()



