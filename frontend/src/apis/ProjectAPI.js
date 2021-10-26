import * as CONSTANTS from "constants/Constants";

const projectAPIRequest = async (url, token, signal) => {
  return await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal: signal,
  });
};

/* Project - Site Selection Form */
export const getProjectID = (token, signal) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL + CONSTANTS.PROJECT_API_PROJECT_IDS_ENDPOINT,
    token,
    signal
  );
};

export const getProjectLocation = async (queryString, token, signal) => {
  return await Promise.all([
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PROJECT_API_SITES_ENDPOINT +
        queryString,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal: signal,
      }
    ),
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PROJECT_API_IMS_ENDPOINT +
        queryString,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal: signal,
      }
    ),
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PROJECT_API_HAZARD_DISAGG_RPS_ENDPOINT +
        queryString,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal: signal,
      }
    ),
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PROJECT_API_HAZARD_UHS_RPS_ENDPOINT +
        queryString,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal: signal,
      }
    ),
  ]);
};

export const getProjectGMSID = (queryString, token, signal) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_GMS_RUNS_ENDPOINT +
      queryString,
    token,
    signal
  );
};

/* Project - Site Selection Viewer */
export const getProjectMaps = (queryString, token, signal) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_MAPS_ENDPOINT +
      queryString,
    token,
    signal
  );
};

/* Project - Hazard Curve Viewer */
export const getProjectHazardCurve = (queryString, token, signal) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_HAZARD_ENDPOINT +
      queryString,
    token,
    signal
  );
};

/* Project - Disaggregation Viewer */
export const getProjectDisaggregation = (queryString, token, signal) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_HAZARD_DISAGG_ENDPOINT +
      queryString,
    token,
    signal
  );
};

/* Project - UHS Viewer */
export const getProjectUHS = (queryString, token, signal) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_HAZARD_UHS_ENDPOINT +
      queryString,
    token,
    signal
  );
};

/* Project - GMS Viewer */
export const getProjectGMS = async (queryString, token, signal) => {
  return await Promise.all([
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PROJECT_API_GMS_ENDPOINT +
        queryString,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal: signal,
      }
    ),
    fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.PROJECT_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT +
        queryString,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal: signal,
      }
    ),
  ]);
};

/* Project - Scenario Viewer */
export const getProjectScenario = (queryString, token, signal) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_SCENARIOS_ENDPOINT +
      queryString,
    token,
    signal
  );
};
