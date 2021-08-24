import seistech_calc as si

# GM data endpoints
ENSEMBLE_IDS_ENDPOINT = "/api/gm_data/ensemble/ids/get"
ENSEMBLE_IMS_ENDPOINT = "/api/gm_data/ensemble/ims/get"

# Hazard endpoints
ENSEMBLE_HAZARD_ENDPOINT = "/api/hazard/ensemble_hazard/get"
ENSEMBLE_HAZARD_DOWNLOAD_ENDPOINT = "/api/hazard/ensemble_hazard/download"

# NZS1170p5 endpoints
NZS1170p5_HAZARD_ENDPOINT = "/api/hazard/nzs1170p5/get"
NZS1170p5_UHS_ENDPOINT = "/api/uhs/nzs1170p5/get"
NZS1170p5_DEFAULT_PARAMS_ENDPOINT = "/api/hazard/nzs1170p5/default_params/get"
NZS1170p5_SOIL_CLASS_ENDPOINT = "/api/hazard/nzs1170p5/soil_class/get"

# NZTA endpoints
NZTA_HAZARD_ENDPOINT = "/api/hazard/nzta/get"
NZTA_DEFAULT_PARAMS_ENDPOINT = "/api/hazard/nzta/default_params/get"
NZTA_SOIL_CLASS_ENDPOINT = "/api/hazard/nzta/soil_class/get"

# Disagg endpoints
ENSEMBLE_DISAGG_ENDPOINT = "/api/disagg/ensemble_disagg/get"
ENSEMBLE_DISAGG_DOWNLOAD_ENDPOINT = "/api/disagg/ensemble_disagg/download"
ENSEMBLE_FULL_DISAGG_ENDPOINT = "/api/disagg/full_disagg/get"

# UHS endpoints
ENSEMBLE_UHS_ENDPOINT = "/api/uhs/ensemble_uhs/get"
ENSEMBLE_UHS_DOWNLOAD_ENDPOINT = "/api/uhs/ensemble_uhs/download"

# GMS endpoints
ENSEMBLE_GMS_COMPUTE_ENDPOINT = "/api/gms/ensemble_gms/compute"
ENSEMBLE_GMS_DOWNLOAD_ENDPOINT = "/api/gms/ensemble_gms/download"
GMS_DEFAULT_IM_WEIGHTS_ENDPOINT = "/api/gms/ensemble_gms/get_default_IM_weights"
GMS_IMS_ENDPOINT = "/api/gms/ensemble_gms/ims"
GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT = "/api/gms/ensemble_gms/get_default_causal_params"
GMS_GM_DATASETS_ENDPOINT = "/api/gms/ensemble_gms/datasets"

# Rupture endpoints
RUPTURES_ENDPOINT = "/api/rupture/ruptures/get"

# Site endpoints
SITE_LOCATION_ENDPOINT = "/api/site/station/location/get"
SITE_NAME_ENDPOINT = "/api/site/station/name/get"
SITE_CONTEXT_MAP_ENDPOINT = "/api/site/context/map/download"
SITE_VS30_MAP_ENDPOINT = "/api/site/vs30/map/download"
SITE_VS30_SOIL_CLASS_ENDPOINT = "/api/site/vs30/soil_class/get"

# Site-source endpoints
SITE_SOURCE_DISTANCES_ENDPOINT = "/api/site_source/distances/get"


NZ_CODE_OPT_ARGS = [
    ("soil_class", si.NZSSoilClass),
    ("distance", float),
    ("z_factor", float),
    ("z_factor_radius", float),
]
