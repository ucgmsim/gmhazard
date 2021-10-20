# Core API Endpoints - Hazard Analysis tab
# Site Selection
CORE_API_ENSEMBLE_IDS_ENDPOINT = "/coreAPI/ensembleids/get"
CORE_API_IMS_ENDPOINT = "/coreAPI/ims/get"
CORE_API_CONTEXT_MAP_ENDPOINT = "/coreAPI/contextmap/get"
CORE_API_VS30_MAP_ENDPOINT = "/coreAPI/vs30map/get"
CORE_API_STATION_ENDPOINT = "/coreAPI/station/get"
CORE_API_VS30_SOIL_CLASS_ENDPOINT = "/coreAPI/vs30/soil_class/get"

# Seismic Hazard
CORE_API_HAZARD_ENDPOINT = "/coreAPI/hazard/get"
CORE_API_HAZARD_NZS1170P5_ENDPOINT = "/coreAPI/hazard/nzs1170p5/get"
CORE_API_HAZARD_NZTA_ENDPOINT = "/coreAPI/hazard/nzta/get"
CORE_API_HAZARD_NZS1170P5_SOIL_CLASS_ENDPOINT = (
    "/coreAPI/hazard/nzs1170p5/soil_class/get"
)
CORE_API_HAZARD_NZS1170P5_DEFAULT_PARAMS_ENDPOINT = (
    "/coreAPI/hazard/nzs1170p5/default/get"
)
CORE_API_HAZARD_NZTA_SOIL_CLASS_ENDPOINT = "/coreAPI/hazard/nzta/soil_class/get"
CORE_API_HAZARD_NZTA_DEFAULT_PARAMS_ENDPOINT = "/coreAPI/hazard/nzta/default/get"
CORE_API_HAZARD_DISAGG_ENDPOINT = "/coreAPI/disagg/get"
CORE_API_HAZARD_UHS_ENDPOINT = "/coreAPI/uhs/get"
CORE_API_HAZARD_UHS_NZS1170P5_ENDPOINT = "/coreAPI/uhs/nzs1170p5/get"

# Ground Motion Selection
CORE_API_GMS_ENDPOINT = "/coreAPI/gms/ensemble_gms/get"
CORE_API_GMS_DEFAULT_IM_WEIGHTS_ENDPOINT = "/coreAPI/gms/default_im_weights/get"
CORE_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT = "/coreAPI/gms/default_causal_params/get"
CORE_API_GMS_DATASETS_ENDPOINT = "/coreAPI/gms/ensemble_gms/datasets/get"
CORE_API_GMS_IMS_ENDPOINT_ENDPOINT = "/coreAPI/gms/ensemble_gms/ims/get"

# Scenarios
CORE_API_SCENARIOS_ENDPOINT = "/coreAPI/scenario/ensemble_scenario/get"

# Download Endpoints
CORE_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT = "/coreAPI/hazard/download"
CORE_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT = "/coreAPI/disagg/download"
CORE_API_HAZARD_UHS_DOWNLOAD_ENDPOINT = "/coreAPI/uhs/download"
CORE_API_SCENARIOS_DOWNLOAD_ENDPOINT = "/coreAPI/scenario/ensemble_scenario/download"
CORE_API_GMS_DOWNLOAD_ENDPOINT = "/coreAPI/gms/download"

# Project API Endpoints - Project tab
# Site Selection
PROJECT_API_PROJECT_IDS_ENDPOINT = "/projectAPI/ids/get"
PROJECT_API_SITES_ENDPOINT = "/projectAPI/sites/get"
PROJECT_API_IMS_ENDPOINT = "/projectAPI/ims/get"
PROJECT_API_MAPS_ENDPOINT = "/projectAPI/maps/get"

# Seismic Hazard
PROJECT_API_HAZARD_ENDPOINT = "/projectAPI/hazard/get"
PROJECT_API_HAZARD_DISAGG_ENDPOINT = "/projectAPI/disagg/get"
PROJECT_API_HAZARD_DISAGG_RPS_ENDPOINT = "/projectAPI/disagg/rps/get"
PROJECT_API_HAZARD_UHS_ENDPOINT = "/projectAPI/uhs/get"
PROJECT_API_HAZARD_UHS_RPS_ENDPOINT = "/projectAPI/uhs/rps/get"

# GMS
PROJECT_API_GMS_RUNS_ENDPOINT = "/projectAPI/gms/runs/get"
PROJECT_API_GMS_ENDPOINT = "/projectAPI/gms/get"
PROJECT_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT = (
    "/projectAPI/gms/default_causal_params/get"
)

# Scenarios
PROJECT_API_SCENARIOS_ENDPOINT = "/projectAPI/scenario/ensemble_scenario/get"

# Download Endpoints
PROJECT_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT = "/projectAPI/hazard/download"
PROJECT_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT = "/projectAPI/disagg/download"
PROJECT_API_HAZARD_UHS_DOWNLOAD_ENDPOINT = "/projectAPI/uhs/download"
PROJECT_API_GMS_DOWNLOAD_ENDPOINT = "/projectAPI/gms/download"
PROJECT_API_SCENARIOS_DOWNLOAD_ENDPOINT = "/projectAPI/scenario/ensemble_scenario/download"

# Create new projects
PROJECT_API_CREATE_NEW_PROJECT_ENDPOINT = "/projectAPI/project/create"

# Intermediate API Endpoints
INTERMEDIATE_API_AUTH0_USER_INFO_ENDPOINT = (
    "/intermediateAPI/auth0/user/permissions/get"
)
INTERMEDIATE_API_AUTH0_USERS_ENDPOINT = "/intermediateAPI/auth0/users/get"

INTERMEDIATE_API_ALL_USERS_PROJECTS_ENDPOINT = "/intermediateAPI/users_projects/get/all"
INTERMEDIATE_API_CREATE_PROJECT_ENDPOINT = "/intermediateAPI/project/create"

INTERMEDIATE_API_USER_PROJECTS_ENDPOINT = "/intermediateAPI/user/projects/get"
INTERMEDIATE_API_USER_ALLOCATE_PROJECTS_ENDPOINT = (
    "/intermediateAPI/user/allocate_projects"
)
INTERMEDIATE_API_USER_REMOVE_PROJECTS_ENDPOINT = "/intermediateAPI/user/remove_projects"

INTERMEDIATE_API_ALL_PERMISSIONS_ENDPOINT = "/intermediateAPI/permission/get/all"

INTERMEDIATE_API_ALL_USERS_PERMISSIONS_ENDPOINT = (
    "/intermediateAPI/users_permissions/get/all"
)

INTERMEDIATE_API_ALL_PRIVATE_PROJECTS_ENDPOINT = (
    "/intermediateAPI/project/private/get/all"
)
INTERMEDIATE_API_ALL_PUBLIC_PROJECTS_ENDPOINT = (
    "/intermediateAPI/project/public/get/all"
)

# Public Project API Endpoints - Project tab
# Site Selection
PUBLIC_API_PROJECT_IDS_ENDPOINT = "/projectAPI/ids/get"
PUBLIC_API_SITES_ENDPOINT = "/projectAPI/sites/get"
PUBLIC_API_IMS_ENDPOINT = "/projectAPI/ims/get"
PUBLIC_API_MAPS_ENDPOINT = "/projectAPI/maps/get"

# Seismic Hazard
PUBLIC_API_HAZARD_ENDPOINT = "/projectAPI/hazard/get"
PUBLIC_API_HAZARD_DISAGG_ENDPOINT = "/projectAPI/disagg/get"
PUBLIC_API_HAZARD_DISAGG_RPS_ENDPOINT = "/projectAPI/disagg/rps/get"
PUBLIC_API_HAZARD_UHS_ENDPOINT = "/projectAPI/uhs/get"
PUBLIC_API_HAZARD_UHS_RPS_ENDPOINT = "/projectAPI/uhs/rps/get"

# GMS
PUBLIC_API_GMS_RUNS_ENDPOINT = "/projectAPI/gms/runs/get"
PUBLIC_API_GMS_ENDPOINT = "/projectAPI/gms/get"
PUBLIC_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT = (
    "/projectAPI/gms/default_causal_params/get"
)

# Scenarios
PUBLIC_API_SCENARIOS_ENDPOINT = "/projectAPI/scenario/ensemble_scenario/get"

# Download Endpoints
PUBLIC_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT = "/projectAPI/hazard/download"
PUBLIC_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT = "/projectAPI/disagg/download"
PUBLIC_API_HAZARD_UHS_DOWNLOAD_ENDPOINT = "/projectAPI/uhs/download"
PUBLIC_API_GMS_DOWNLOAD_ENDPOINT = "/projectAPI/gms/download"
PUBLIC_API_SCENARIOS_DOWNLOAD_ENDPOINT = "/projectAPI/scenario/ensemble_scenario/download"

# Forwarding path to Core API
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
NZS1170p5_SOIL_CLASS = "/api/hazard/nzs1170p5/soil_class/get"

# NZTA endpoints
NZTA_HAZARD_ENDPOINT = "/api/hazard/nzta/get"
NZTA_DEFAULT_PARAMS_ENDPOINT = "/api/hazard/nzta/default_params/get"
NZTA_SOIL_CLASS = "/api/hazard/nzta/soil_class/get"

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

# Scenarios
ENSEMBLE_SCENARIO_ENDPOINT = "/api/scenario/ensemble_scenario/get"
ENSEMBLE_SCENARIO_DOWNLOAD_ENDPOINT = "/api/scenario/ensemble_scenario/download"

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

# Forwarding path to Project API
# Project
PROJECT_IDS_ENDPOINT = "/api/project/ids/get"
PROJECT_SITES_ENDPOINT = "/api/project/sites/get"
PROJECT_IMS_ENDPOINT = "/api/project/ims/get"
PROJECT_CONTEXT_MAPS_ENDPOINT = "/api/project/maps/get"

PROJECT_CREATE_NEW_ENDPOINT = "/api/project/create"

PROJECT_DOWNLOAD_TOKEN_ENDPOINT = "/api/project/download_token/get"
PROJECT_DOWNLOAD_ENDPOINT = "/api/project/download"

# Hazard endpoints
PROJECT_HAZARD_ENDPOINT = "/api/project/hazard/get"
PROJECT_HAZARD_DOWNLOAD_ENDPOINT = "/api/project/hazard/download"

# Disagg endpoints
PROJECT_DISAGG_RPS_ENDPOINT = "/api/project/disagg/rps/get"
PROJECT_DISAGG_ENDPOINT = "/api/project/disagg/get"
PROJECT_DISAGG_DOWNLOAD_ENDPOINT = "/api/project/disagg/download"

# UHS endpoints
PROJECT_UHS_RPS_ENDPOINT = "/api/project/uhs/rps/get"
PROJECT_UHS_ENDPOINT = "/api/project/uhs/get"
PROJECT_UHS_DOWNLOAD_ENDPOINT = "/api/project/uhs/download"

# GMS endpoints
PROJECT_GMS_RUNS_ENDPOINT = "/api/project/gms/runs/get"
PROJECT_GMS_ENDPOINT = "/api/project/gms/get"
PROJECT_GMS_DOWNLOAD_ENDPOINT = "/api/project/gms/download"
PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT = (
    "/api/project/gms/default_causal_params/get"
)

# Scenarios
PROJECT_SCENARIO_ENDPOINT = "/api/project/scenario/get"
PROJECT_SCENARIO_DOWNLOAD_ENDPOINT = "/api/project/scenario/download"

# HTTP Response codes
OK_CODE = 200
BAD_REQUEST_CODE = 400
UNAUTHORIZED_CODE = 401
NO_ACCESS_RIGHT_CODE = 403
CONFLICT_CODE = 409
INTERNAL_SERVER_ERROR_CODE = 500
SERVICE_UNAVAILABLE_CODE = 503
