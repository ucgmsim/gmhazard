import * as CONSTANTS from "constants/Constants";

const publicProjectAPIRequest = async (url, signal) => {
  return await fetch(url, {
    signal: signal,
  });
};

/* Project - Site Selection Form */
export const getPublicProjectID = (signal) => {
  return publicProjectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL + CONSTANTS.PUBLIC_API_PROJECT_IDS_ENDPOINT,
    signal
  );
};

export const getPublicProjectLocation = async (signal, queryString) => {
  return await Promise.all([
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PUBLIC_API_SITES_ENDPOINT +
        queryString,
      {
        signal: signal,
      }
    ),
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PUBLIC_API_IMS_ENDPOINT +
        queryString,
      {
        signal: signal,
      }
    ),
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PUBLIC_API_HAZARD_DISAGG_RPS_ENDPOINT +
        queryString,
      {
        signal: signal,
      }
    ),
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PUBLIC_API_HAZARD_UHS_RPS_ENDPOINT +
        queryString,
      {
        signal: signal,
      }
    ),
  ]);
};

export const getPublicProjectGMSID = (signal, queryString) => {
  return publicProjectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_GMS_RUNS_ENDPOINT +
      queryString,
    signal
  );
};

/* Project - Site Selection Viewer */
export const getPublicProjectMaps = (signal, queryString) => {
  return publicProjectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_MAPS_ENDPOINT +
      queryString,
    signal
  );
};

/* Project - Hazard Curve Viewer */
export const getPublicProjectHazardCurve = (signal, queryString) => {
  return publicProjectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_HAZARD_ENDPOINT +
      queryString,
    signal
  );
};

/* Project - Disaggregation Viewer */
export const getPublicProjectDisaggregation = (signal, queryString) => {
  return publicProjectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_HAZARD_DISAGG_ENDPOINT +
      queryString,
    signal
  );
};

/* Project - UHS Viewer */
export const getPublicProjectUHS = (signal, queryString) => {
  return publicProjectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_HAZARD_UHS_ENDPOINT +
      queryString,
    signal
  );
};

/* Project - GMS to be added */

/* Project - Scenario */
export const getPublicProjectScenario = (signal, queryString) => {
  return publicProjectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_SCENARIOS_ENDPOINT +
      queryString,
    signal
  );
};
