"""Script for comparison of non-paramatric and parametric IM
distrbution at a specific station for a specific IM
"""
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

import gmhazard_calc as sc

rupture = "AlpineF2K"
station = "CCCC"
im = "pSA_5.0"
n_bins = 15

# Need to provide a proper path. Refer to the WiKi
non_para_imdb_ffp = ""
para_imdb_ffp = ""


with sc.dbs.IMDBNonParametric(non_para_imdb_ffp) as db:
    im_values_df = db.im_data(station, im)
im_values = im_values_df[rupture].values

with sc.dbs.IMDBParametric(para_imdb_ffp) as db:
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
