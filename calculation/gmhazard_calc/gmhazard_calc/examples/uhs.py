"""Compute a the hazard curve for a site of interest

Data for this example can be found here:
https://www.dropbox.com/s/2il2hhbzrlueujl/gmhazard_example_data.zip?dl=0
"""
import numpy as np
import gmhazard_calc as sc

# Create the ensemble
ens = sc.gm_data.Ensemble(
    "gnzl", config_ffp="/path-to/gmhazard_example_data/v20p5emp_gnzl.yaml"
)

# Print out name of available stations
# print(f"Available stations Ids:\n{ens.stations.index.values}")

# Create site
site = sc.site.get_site_from_name(ens, "Christchurch_300_0p535_2p375")

# Compute UHS for return period of 250, 500 & 1000 years
uhs_results = sc.uhs.run_ensemble_uhs(
    ens, site, np.asarray([1 / 250, 1 / 500, 1 / 1000]), n_procs=4
)

# Create a UHS dataframe from the results
uhs_df = sc.uhs.EnsembleUHSResult.combine_results(uhs_results)

# Generate the UH plot
sc.plots.plt_uhs(uhs_df, save_file="./uhs.png")
