// TODO - split constants individually
// BASE_URL (URL for Intermediate API) and MAP_BOX_TOKEN details from the .env file
export const INTERMEDIATE_API_URL = process.env.REACT_APP_INTERMEDIATE_API_URL;

export const CORE_API_ENSEMBLE_IDS_ENDPOINT = "/coreAPI/ensembleids/get";
export const CORE_API_IMS_ENDPOINT = "/coreAPI/ims/get";
export const CORE_API_CONTEXT_MAP_ENDPOINT = "/coreAPI/contextmap/get";
export const CORE_API_VS30_MAP_ENDPOINT = "/coreAPI/vs30map/get";
export const CORE_API_STATION_ENDPOINT = "/coreAPI/station/get";
export const CORE_API_VS30_SOIL_CLASS_ENDPOINT = "/coreAPI/vs30/soil_class/get";

export const CORE_API_HAZARD_ENDPOINT = "/coreAPI/hazard/get";
export const CORE_API_HAZARD_NZS1170P5_ENDPOINT =
  "/coreAPI/hazard/nzs1170p5/get";
export const CORE_API_HAZARD_NZTA_ENDPOINT = "/coreAPI/hazard/nzta/get";
export const CORE_API_HAZARD_DISAGG_ENDPOINT = "/coreAPI/disagg/get";
export const CORE_API_HAZARD_UHS_ENDPOINT = "/coreAPI/uhs/get";
export const CORE_API_HAZARD_UHS_NZS1170P5_ENDPOINT =
  "/coreAPI/uhs/nzs1170p5/get";
export const CORE_API_HAZARD_NZS1170P5_SOIL_CLASS_ENDPOINT =
  "/coreAPI/hazard/nzs1170p5/soil_class/get";
export const CORE_API_HAZARD_NZS1170P5_DEFAULT_PARAMS_ENDPOINT =
  "/coreAPI/hazard/nzs1170p5/default/get";
export const CORE_API_HAZARD_NZTA_SOIL_CLASS_ENDPOINT =
  "/coreAPI/hazard/nzta/soil_class/get";
export const CORE_API_HAZARD_NZTA_DEFAULT_PARAMS_ENDPOINT =
  "/coreAPI/hazard/nzta/default/get";

export const CORE_API_GMS_ENDPOINT = "/coreAPI/gms/ensemble_gms/get";
export const CORE_API_GMS_DEFAULT_IM_WEIGHTS_ENDPOINT =
  "/coreAPI/gms/default_im_weights/get";
export const CORE_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT =
  "/coreAPI/gms/default_causal_params/get";
export const CORE_API_GMS_IMS_ENDPOINT_ENDPOINT =
  "/coreAPI/gms/ensemble_gms/ims/get";
export const CORE_API_GMS_DATASETS_ENDPOINT =
  "/coreAPI/gms/ensemble_gms/datasets/get";

export const CORE_API_SCENARIOS_ENDPOINT =
  "/coreAPI/scenario/ensemble_scenario/get";
export const CORE_API_SCENARIOS_DOWNLOAD_ENDPOINT =
  "/coreAPI/scenario/ensemble_scenario/download";

/* 
This endpoint will eventually replace when we implement DB properly
As this function reads from Available_Project table (A bridge table between User and Project)
*/
export const PROJECT_API_PROJECT_IDS_ENDPOINT = "/projectAPI/ids/get";
export const PROJECT_API_SITES_ENDPOINT = "/projectAPI/sites/get";
export const PROJECT_API_IMS_ENDPOINT = "/projectAPI/ims/get";
export const PROJECT_API_MAPS_ENDPOINT = "/projectAPI/maps/get";

export const PROJECT_API_HAZARD_ENDPOINT = "/projectAPI/hazard/get";
export const PROJECT_API_HAZARD_DISAGG_ENDPOINT = "/projectAPI/disagg/get";
export const PROJECT_API_HAZARD_DISAGG_RPS_ENDPOINT =
  "/projectAPI/disagg/rps/get";
export const PROJECT_API_HAZARD_UHS_ENDPOINT = "/projectAPI/uhs/get";
export const PROJECT_API_HAZARD_UHS_RPS_ENDPOINT = "/projectAPI/uhs/rps/get";

export const PROJECT_API_GMS_RUNS_ENDPOINT = "/projectAPI/gms/runs/get";
export const PROJECT_API_GMS_ENDPOINT = "/projectAPI/gms/get";
export const PROJECT_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT =
  "/projectAPI/gms/default_causal_params/get";

export const PROJECT_API_SCENARIOS_ENDPOINT =
  "/projectAPI/scenario/ensemble_scenario/get";

// Download path
export const CORE_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT =
  "/coreAPI/hazard/download";
export const CORE_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT =
  "/coreAPI/disagg/download";
export const CORE_API_HAZARD_UHS_DOWNLOAD_ENDPOINT = "/coreAPI/uhs/download";
export const CORE_API_GMS_DOWNLOAD_ENDPOINT = "/coreAPI/gms/download";

export const PROJECT_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT =
  "/projectAPI/hazard/download";
export const PROJECT_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT =
  "/projectAPI/disagg/download";
export const PROJECT_API_HAZARD_UHS_DOWNLOAD_ENDPOINT =
  "/projectAPI/uhs/download";
export const PROJECT_API_GMS_DOWNLOAD_ENDPOINT = "/projectAPI/gms/download";
export const PROJECT_API_SCENARIOS_DOWNLOAD_ENDPOINT =
  "/projectAPI/scenario/ensemble_scenario/download";

// Intermediate API path
export const INTERMEDIATE_API_AUTH0_USER_INFO_ENDPOINT =
  "/intermediateAPI/auth0/user/permissions/get";
export const INTERMEDIATE_API_AUTH0_USERS_ENDPOINT =
  "/intermediateAPI/auth0/users/get";

export const INTERMEDIATE_API_CREATE_PROJECT_ENDPOINT =
  "/intermediateAPI/project/create";

export const INTERMEDIATE_API_USER_PROJECTS_ENDPOINT =
  "/intermediateAPI/user/projects/get";
export const INTERMEDIATE_API_USER_ALLOCATE_PROJECTS_ENDPOINT =
  "/intermediateAPI/user/allocate_projects";
export const INTERMEDIATE_API_USER_REMOVE_PROJECTS_ENDPOINT =
  "/intermediateAPI/user/remove_projects";

export const INTERMEDIATE_API_ALL_PERMISSIONS_ENDPOINT =
  "/intermediateAPI/permission/get/all";

export const INTERMEDIATE_API_ALL_USERS_PERMISSIONS_ENDPOINT =
  "/intermediateAPI/users_permissions/get/all";

export const INTERMEDIATE_API_ALL_USERS_PROJECTS_ENDPOINT =
  "/intermediateAPI/users_projects/get/all";
export const INTERMEDIATE_API_ALL_PRIVATE_PROJECTS_ENDPOINT =
  "/intermediateAPI/project/private/get/all";
export const INTERMEDIATE_API_ALL_PUBLIC_PROJECTS_ENDPOINT =
  "/intermediateAPI/project/public/get/all";

// Labels
export const HAZARD_ANALYSIS = "Hazard Analysis";
export const SITE_SELECTION = "Site Selection";
export const SEISMIC_HAZARD = "Seismic Hazard";
export const GMS = "Ground Motion Selection";
export const SCENARIOS = "Scenarios";
export const HAZARD_CURVE = "Hazard Curve";
export const DISAGGREGATION = "Disaggregation";
export const UNIFORM_HAZARD_SPECTRUM = "Uniform Hazard Spectrum";
export const ENSEMBLE_BRANCHES = "Ensemble branches";
export const FAULT_DISTRIBUTED_SEISMICITY_CONTRIBUTION =
  "Fault/distributed seismicity contribution";
export const DOWNLOAD_DATA = "Download data";
export const RETURN_PERIOD_WITH_UNIT = "Return Period (years)"
export const GET_BUTTON = "Get"
export const GMS_IM_DISTRIBUTIONS_PLOT = "IM Distributions"
export const GMS_CONDITIONING_IM_NAME = "Conditioning IM Name"
export const VIBRATION_PERIOD = "Vibration Period"
export const EXCEEDANCE_RATE_LEVEL = "Exceedance rate level"
export const IM_VECTOR = "IM Vector"
export const CAUSAL_PARAMETERS = "Causal Parameters"

// Units in labels
export const SECONDS = "(s)"
export const KILOMETRE = "(km)"
export const METRE_PER_SECOND = "(m/s)"
export const YEARS = "(years)"

export const APP_LOCATION_DEFAULT_ENSEMBLE = "v20p5emp";

export const APP_UI_CONTRIB_TABLE_ROWS = 10;
export const APP_UI_VS30_DP = 1;
export const APP_UI_SIGFIGS = 4;
export const APP_UI_UHS_RATETABLE_RATE_SIGFIGS = 3;

export const UHS_TABLE_MESSAGE = "No rates added";

// For Site Selection
export const DEFAULT_LAT = process.env.REACT_APP_DEFAULT_LAT || "";
export const DEFAULT_LNG = process.env.REACT_APP_DEFAULT_LNG || "";
export const ENV = process.env.REACT_APP_ENV;

export const SITE_SELECTION_VS30_TITLE = "VS30";

/* 
Guide Messages
Site Selection - Regional & Vs30
*/
export const SITE_SELECTION_VS30_MSG =
  "Please do the following steps to see an image.";
export const SITE_SELECTION_VS30_INSTRUCTION = [
  "Put appropriate Latitude and Longitude values.",
  "Click the Set button in the 'Location' section to see an image.",
];

export const SITE_SELECTION_REGIONAL_TITLE = "Regional";
export const SITE_SELECTION_REGIONAL_MSG =
  "Please do the following steps to see an image.";
export const SITE_SELECTION_REGIONAL_INSTRUCTION = [
  "Put appropriate Latitude and Longitude values.",
  "Click the Set button in the 'Location' section to see an image.",
];

/*
Map Box
Default coordinates needed, so I put our coordinates (UC Engineering Core Building)
*/
export const DEFAULT_MAPBOX_LAT = -43.521463221980085;
export const DEFAULT_MAPBOX_LNG = 172.58361319646755;
export const MAP_BOX_WIDTH = "66vw";
export const MAP_BOX_HEIGHT = "70vh";
// Needs to be changed once we have a GMHazard account with MapBox
export const MAP_BOX_TOKEN = process.env.REACT_APP_MAP_BOX_TOKEN;

// For HazardForm
export const PROBABILITY = "probability";
export const PROBABILITY_YEARS = "Probability/years";
export const RETURN_PERIOD = "Return Period";
export const ANNUAL_PROBABILITY = "Annual Probability";

/* 
Guide messages
Seismic Hazard - Hazard Viewer
*/
export const HAZARD_CURVE_GUIDE_MSG =
  "Please do the following steps to see plots.";
export const HAZARD_CURVE_INSTRUCTION = [
  "Choose the Intensity Measure first.",
  "Click the compute button in the 'Hazard Curve' section to see plots.",
];
export const DISAGGREGATION_GUIDE_MSG_PLOT =
  "Please do the following steps to see plots.";
export const DISAGGREGATION_GUIDE_MSG_TABLE =
  "Please do the following steps to see the contribution table.";
export const DISAGGREGATION_INSTRUCTION_PLOT = [
  "Choose the Intensity Measure first.",
  "Update input fields in the 'Disaggregation' section to get a probability.",
  "Click the compute button in the 'Disaggregation' section to see plots.",
];
export const DISAGGREGATION_INSTRUCTION_TABLE = [
  "Choose the Intensity Measure first.",
  "Update input fields in the 'Disaggregation' section to get a probability.",
  "Click the compute button in the 'Disaggregation' section to see the contribution table.",
];

export const UNIFORM_HAZARD_SPECTRUM_MSG =
  "Please do the following steps to see plots.";
export const UNIFORM_HAZARD_SPECTRUM_INSTRUCTION = [
  "Using input fields to find the RP.",
  "Click Add button to add for calculation.",
  "Click Compute button to see plots.",
];
export const PROJECT_UNIFORM_HAZARD_SPECTRUM_INSTRUCTION = [
  "Select the RP(s).",
  "Click Get button to see plots.",
];

/* 
Guide messages
GMS
*/
export const GMS_VIEWER_GUIDE_MSG =
  "Please do the following steps to see plots.";
export const GMS_VIEWER_GUIDE_INSTRUCTION = [
  "Select IM from Conditioning IM Name.",
  "Choose one option from IM / Exceedance rate level then put a value.",
  "Click Get causal parameters bounds",
  "Select IM Vector(s).",
  "Click Get IM vector weights",
  "Put Number of Ground Motions.",
  "Click the Compute button.",
];
export const PROJECT_GMS_VIEWER_GUIDE_INSTRUCTION = [
  "Select IM from Conditioning IM Name.",
  "Select Exceedance rate level.",
  "Click the Get button.",
];

/*
Guide messages
Scenarios
*/
export const SCENARIO_VIEWER_GUIDE_MSG =
  "Please do the following steps to see plots.";
export const SCENARIO_VIEWER_GUIDE_INSTRUCTION = [
  "Select an IM Component",
  "Click the Compute button",
  "Select scenarios to plot when available",
];

// Project Tabs
export const PROJECT_SITE_SELECTION_GUIDE_MSG =
  "Please do the following steps to see images.";
export const PROJECT_SITE_SELECTION_INSTRUCTION = [
  "Choose the Project.",
  "Choose the Location.",
  "Choose the Vs30.",
  "Choose the Z1.0 | Z2.5.",
  "Click the Get button to see an image",
];

export const PROJECT_HAZARD_CURVE_INSTRUCTION = [
  "Choose the Intensity Measure.",
  "Click the Get button in the 'Hazard Curve' section to see plots.",
];

export const PROJECT_DISAGG_INSTRUCTION_PLOT = [
  "Choose the Intensity Measure.",
  "Choose the Return Period",
  "Click the Get button in the 'Disaggregation' section to see plots.",
];

export const PROJECT_DISAGG_INSTRUCTION_TABLE = [
  "Choose the Intensity Measure.",
  "Choose the Return Period",
  "Click the Get button in the 'Disaggregation' section to see contribution table.",
];

export const PROJECT_SCENARIO_VIEWER_GUIDE_INSTRUCTION = [
  "Select an IM Component",
  "Click the Get button",
  "Select scenarios to plot when available",
];

// Error Messages
export const ERROR_SET_DIFF_CODE = {
  DEFAULT: {
    ERROR_MSG_HEADER: "Error",
    ERROR_MSG_TITLE: "Something went wrong.",
    ERROR_MSG_BODY: "Please try again or contact us.",
  },
  400: {
    ERROR_MSG_HEADER: "400 Error",
    ERROR_MSG_TITLE: "One of the request inputs is not valid.",
    ERROR_MSG_BODY: "Please check inputs and try again.",
  },
  500: {
    ERROR_MSG_HEADER: "500 Error",
    ERROR_MSG_TITLE: "Our server is currently having issues.",
    ERROR_MSG_BODY: "Please try again later.",
  },

  // GMS Validation error
  gms_im: {
    ERROR_MSG_HEADER: "Ground Motion Selection - IMs",
    ERROR_MSG_TITLE:
      "Issue found in the returned data that properties do not match with selected IM Vector",
    ERROR_MSG_BODY:
      "Please try to compute the Ground Motion Selection again or contact us.",
  },
  gms_gcim_cdf_x: {
    ERROR_MSG_HEADER: "Ground Motion Selection - gcim_cdf_x",
    ERROR_MSG_TITLE:
      "Issue found in the returned data that properties do not match with selected IM Vector",
    ERROR_MSG_BODY:
      "Please try to compute the Ground Motion Selection again or contact us.",
  },
  gms_gcim_cdf_y: {
    ERROR_MSG_HEADER: "Ground Motion Selection - gcim_cdf_y",
    ERROR_MSG_TITLE:
      "Issue found in the returned data that properties do not match with selected IM Vector",
    ERROR_MSG_BODY:
      "Please try to compute the Ground Motion Selection again or contact us.",
  },
  gms_realisations: {
    ERROR_MSG_HEADER: "Ground Motion Selection - realisations",
    ERROR_MSG_TITLE:
      "Issue found in the returned data that properties do not match with selected IM Vector",
    ERROR_MSG_BODY:
      "Please try to compute the Ground Motion Selection again or contact us.",
  },
  gms_IM_j: {
    ERROR_MSG_HEADER: "Ground Motion Selection - IM_j",
    ERROR_MSG_TITLE:
      "Issue found in the returned data that properties do not match with selected Conditioning IM Name",
    ERROR_MSG_BODY:
      "Please try to compute the Ground Motion Selection again or contact us.",
  },
  gms_metadata: {
    ERROR_MSG_HEADER: "Ground Motion Selection - metadata",
    ERROR_MSG_TITLE:
      "Issue found in the returned data that properties do not match with GMS_LABELS",
    ERROR_MSG_BODY:
      "Please try to compute the Ground Motion Selection again or contact us.",
  },
};

// react-plotly.js configuration
export const PLOT_MARGIN = {
  l: 60,
  r: 50,
  b: 50,
  t: 30,
  pad: 4,
};

// Minimize the options in the modebar (plotly's menu)
export const PLOT_CONFIG = {
  displayModeBar: true,
  modeBarButtonsToRemove: [
    "select2d",
    "lasso2d",
    "zoomIn2d",
    "zoomOut2d",
    "toggleSpikelines",
    "hoverCompareCartesian",
    "hoverClosestCartesian",
    "autoScale2d",
  ],
  doubleClick: "autosize",
};

// Constant Tooltips Message
export const TOOLTIP_MESSAGES = {
  SITE_SELECTION_LOCATION:
    "Enter the location (Lat, Lon) of the site of interest",
  SITE_SELECTION_SITE_CONDITION:
    "Enter the site parameters, such as the 30m-averaged shear-wave velocity. Default values of these parameters are estimated based on the selected location. You can either use this or manually override it with a specified value.",
  HAZARD_HAZARD:
    "Select the intensity measure of interest to compute the seismic hazard curve.",
  HAZARD_DISAGG:
    "Specify the annual exceedance rate (inverse of return period) to compute the disaggregation distribution. The adopted intensity measure is that specified in the Intensity Measure tab.",
  HAZARD_UHS:
    "Specify one or more annual exceedance rates (inverse of return period) to compute the Uniform Hazard Spectrum (UHS) for. Specified rates are displayed, which can be subsequently removed.",
  HAZARD_NZ_CODE:
    "Select one of the relevant code/guideline prescriptions in order to compare with the site-specific hazard results. Based on the location and Vs30 values assigned, these parameters have been estimated, but can be manually over-ridden.",
  HAZARD_NZS1170P5_CODE:
    "Select the Soil Class and Z Factor as defined in NZS1170.5",
  HAZARD_NZTA_CODE: "Select the Soil Class as defined in NZTA",
  PROJECT_SITE_SELECTION_PROJECT_NAME:
    "Select the Project title from the list of available alternatives.",
  PROJECT_SITE_SELECTION_LOCATION:
    "Select the site/location of interest for this Project.",
  PROJECT_SITE_SELECTION_VS30:
    "Select the site parameters of interest for this site of interest, such as the 30m-averaged shear-wave velocity.",
  PROJECT_SITE_SELECTION_Z1p0_Z2p5:
    "Select the site parameters of interest for this Vs30, such as the depth of 1,000 Vs30 and 2,500 Vs30.",
  PROJECT_HAZARD:
    "Select the intensity measure of interest to compute the seismic hazard curve.",
  PROJECT_DISAGG:
    "Select the annual exceedance rate (inverse of return period) to compute the disaggregation distribution. The adopted intensity measure is that specified in the Intensity Measure tab.",
  PROJECT_UHS:
    "Select one or more annual exceedance rates (inverse of return period) to compute the Uniform Hazard Spectrum (UHS) for. Selected rates are displayed, which can be subsequently removed.",
  PROJECT_GMS_ID: "NEED TO BE UPDATED",
  // GMS Section
  HAZARD_GMS_CONDITIONING_IM_NAME: "Select the conditioning intensity measure.",
  GMS_VIBRATION_PERIOD: "Select the vibration period.",
  PROJECTS_GMS_EXCEEDANCE_RATE_LEVEL:
    "Select the exceedance rate of the conditioning IM at which to perform Ground Motion Selection.",
  HAZARD_GMS_IM_LEVEL_EXCEEDANCE_RATE:
    "Set the value of the Conditioning IM. This can be done by either specifying this directly as the 'IM level', or indirectly by specifying the Exceedance Rate from which the hazard curve is used to obtain the IM level.",
  HAZARD_GMS_IM_VECTOR:
    "Select the intensity measures to include in the IM vector. Default weights for each intensity measure are assigned, which can be edited in the 'Advanced' fields.",
  PROJECTS_GMS_IM_VECTOR:
    "Select the intensity measures to include in the IM vector.",
  HAZARD_GMS_NUM_GMS: "Set the number of ground motions for selection.",
  HAZARD_GMS_ADVANCED:
    "These are additional parameters for which default values are likely to be suitable for many users.  The advanced user may wish to manually deviate from these defaults. See the documentation page for additional details on the models used to compute these defaults.",
  HAZARD_GMS_CAUSAL_PARAMS_BOUNDS:
    "Specify the minimum and maximum allowable values of Magnitude, Rupture Distance, and 30m-averaged shear-wave velocity.",
  HAZARD_GMS_WEIGHTS:
    "Weights for each intensity measure in the 'IM Vector' used in the misfit calculation for ground-motion selection. Select the 'renormalise' button to normalise the weights to 1.0.",
  HAZARD_GMS_DB:
    "Select one or more databases from which prospective ground motions can be selected.",
  HAZARD_GMS_REPLICATES:
    "The number of replicates performed. This attempts to overcome statistical artifacts due to the use of Monte Carlo simulation within the ground-motion selection method. A larger number will give more stable results, but compute time will increase proportionately.",
  // Scenario tab
  SCENARIOS:
    "Select the component of interest to view response spectra for the selected scenario ruptures.",
  // Inside tab
  INNER_TAB_SITE_SELECTION:
    "This tab allows the specification of basic information about the site, including the location (Lat, Lon), and site conditions.",
  INNER_TAB_SEISMIC_HAZARD:
    "This tab provides access to site-specific seismic hazard results, including hazard curves and disaggregation for multiple intensity measures and exceedance rates (or return periods); and uniform hazard spectra.",
  INNER_TAB_GMS:
    "This tab provides access to site-specific ground-motion selection that is consistent with the site-specific seismic hazard.",
};

// Hyperlinks for Tooltips
export const TOOLTIP_URL = {
  HAZARD_NZ_CODE: "https://google.com",
};

// GMS Labels
export const GMS_LABELS = {
  mag: "Magnitude (Mw)",
  rrup: `Rupture distance (R${"rup".sub()})`,
  sf: "Scale factor (SF)",
  vs30: `30m-averaged shear-wave velocity (V${"s30".sub()})`,
};

// Projects' Metadata
export const NZTA_SOIL_CLASS = {
  A: "A - rock",
  D: "D - soft or deep soil",
};
export const NZS_SOIL_CLASS = {
  A: "A - rock",
  B: "B - weak rock",
  C: "C - intermediate soil",
  D: "D - soft or deep soil",
  E: "E - very soft",
};

// GMS IM Distribution plots x label
export const GMS_IM_DISTRIBUTIONS_LABEL = {
  PGA: "Peak ground acceleration, PGA (g)",
  PGV: "Peak ground velocity, PGV (cm/s)",
  CAV: "Cumulative absolute velocity, CAV (g.s)",
  Ds595: "5-95% Significant duration, Ds595 (s)",
  Ds575: "5-75% Significatn duration, Ds575 (s)",
  AI: "Arias intensity, AI (cms/s)",
};
