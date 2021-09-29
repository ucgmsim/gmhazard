"""Compute a the hazard curve for a site of interest

Data for this example can be found here:
https://www.dropbox.com/s/2il2hhbzrlueujl/seistech_example_data.zip?dl=0
"""
import gmhazard_calc as sc

# Create the ensemble
ens = sc.gm_data.Ensemble("gnzl", config_ffp="/path-to/seistech_example_data/v20p5emp_gnzl.yaml")

# Print out name of available stations
# print(f"Available stations Ids:\n{ens.stations.index.values}")

# Create site
site = sc.site.get_site_from_name(ens, "Christchurch_300_0p535_2p375")

# Create IM
im = sc.im.IM.from_str("PGA")

# Compute the hazard curve
hazard_data = sc.hazard.run_ensemble_hazard(ens, site, im)

# Generate a hazard curve plot
sc.plots.plt_hazard(hazard_data.as_dataframe(), f"Hazard - {site.station_name} - {im}", im, save_file="./hazard.png")



