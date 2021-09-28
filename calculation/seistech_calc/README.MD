# Seistech Calculation

This package is used for PSHA calculation using logic trees (referred to as ensembles in the code and documentation)

As calculations are performed using a set of pre-computed databases:
    - IMDBs: contains the ground motion (GM) intensity measure (IM) parameters for the sites of interest.
    - site-source DB: contains the source-site distances

Additionally files describing the sites of interest are also required:
    - Site locations (.ll file)
    - Site conditions (.vs30 and .z)

A complete example dataset along with its ensemble config can be found [here](https://www.dropbox.com/s/2il2hhbzrlueujl/seistech_example_data.zip?dl=0)

## Run PSHA calculations

To run any calculation:
1) The ensemble has to be loaded
2) Site of interest has to be specified

```python
import gmhazard_calc as sc

# Create the ensemble
ens = sc.gm_data.Ensemble("gnzl", config_ffp="/path-to/seistech_example_data/v20p5emp_gnzl.yaml")

# Create site
site = sc.site.get_site_from_name(ens, "Christchurch_300_0p535_2p375")
```

Note - Available sites can be printed out with:
```python
print(f"Available stations Ids:\n{ens.stations.index.values}")
```

Hazard can then be computed & plotted as follows:
```python
# Create IM
im = sc.im.IM.from_str("PGA")

# Compute the hazard curve
hazard_data = sc.hazard.run_ensemble_hazard(ens, site, im)

# Generate a hazard curve plot
sc.plots.plt_hazard(hazard_data.as_dataframe(), f"Hazard - {site.station_name} - {im}", im, save_file="./hazard.png")
```

For examples of computing UHS and disaggregation see the examples folder

