"""Script for comparison of non-paramatric and parametric IM
distrbution at a specific station for a specific IM
"""
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

import seistech_calc as si

rupture = "AlpineF2K"
station = "CCCC"
im = "pSA_5.0"
n_bins = 15

non_para_imdb_ffp = "/nesi/nobackup/nesi00213/seistech/simulations/18p6/cs18p6_flt_new.h5"
para_imdb_ffp = "/nesi/nobackup/nesi00213/seistech/empiricals/18p6_new/B10_flt.db"


with si.dbs.IMDBNonParametric(non_para_imdb_ffp) as db:
    im_values_df = db.im_data(station, im)
im_values = im_values_df[rupture].values

with si.dbs.IMDBParametric(para_imdb_ffp) as db:
    im_params_df = db.im_data(station, im)
im_mu, im_sigma = im_params_df.loc[rupture]

# Plot histogram of non-parametric IM values
plt.hist(im_values_df.loc[rupture], bins=n_bins)
plt.xlabel(im)
plt.title(f"{rupture} - {station} - Median - {np.median(im_values):.5f}")

# Plot pdf of log-normal parametric distribution
im_min, im_max = im_values_df.loc[rupture].min(), im_values_df.loc[rupture].max()
x = np.linspace(im_min, im_max, 1000)
emp_pdf = stats.norm.pdf(np.log(x), im_mu, im_sigma)

plt.figure()
plt.plot(x, emp_pdf)
plt.xlabel(im)
plt.title(f"{rupture} - {station} - Median - {np.exp(im_mu):.5f}")

plt.show()
exit()



