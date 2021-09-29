"""Compute disaggreation for a site of interest

Data for this example can be found here:
https://www.dropbox.com/s/2il2hhbzrlueujl/gmhazard_example_data.zip?dl=0
"""
import gmhazard_calc as sc

# Create the ensemble
ens = sc.gm_data.Ensemble(
    "gnzl", config_ffp="/path-to/gmhazard_example_data/v20p5emp_gnzl.yaml"
)

# Print out name of available stations
# print(f"Available stations Ids:\n{ens.stations.index.values}")

# Create site
site = sc.site.get_site_from_name(ens, "Christchurch_300_0p535_2p375")

# Create IM
im = sc.im.IM.from_str("PGA")

# Compute disaggregation for return period of 250 years
disagg_data = sc.disagg.run_ensemble_disagg(ens, site, im, exceedance=(1 / 250))

# Print the top-10 contributing ruptures
print(disagg_data.total_contributions.iloc[:10])

# Grid the data (only required for plotting)
disagg_grid_data = sc.disagg.run_disagg_gridding(disagg_data)

# Generate disagg plot (this requires gmt to be installed, see http://gmt.soest.hawaii.edu/projects/gmt/wiki/Installing)
sc.plots.gmt_disagg("./disagg_src", disagg_grid_data.to_dict(), bin_type="src")
sc.plots.gmt_disagg("./disagg_eps", disagg_grid_data.to_dict(), bin_type="eps")
