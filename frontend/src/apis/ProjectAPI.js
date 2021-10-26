import * as CONSTANTS from "constants/Constants";

const projectAPIRequest = async (url, signal, token) => {
  return await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal: signal,
  });
};

/* Project - Site Selection Form */
export const getProjectID = (signal, token) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL + CONSTANTS.PROJECT_API_PROJECT_IDS_ENDPOINT,
    signal,
    token
  );
};

export const getProjectLocation = async (signal, token, queryString) => {
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

export const getProjectGMSID = (signal, token, queryString) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_GMS_RUNS_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - Site Selection Viewer */
export const getProjectMaps = (signal, token, queryString) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_MAPS_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - Hazard Curve Viewer */
export const getProjectHazardCurve = (signal, token, queryString) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_HAZARD_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - Disaggregation Viewer */
export const getProjectDisaggregation = (signal, token, queryString) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_HAZARD_DISAGG_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - UHS Viewer */
export const getProjectUHS = (signal, token, queryString) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_HAZARD_UHS_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - GMS to be added */

/* Project - Scenario */
export const getProjectScenario = (signal, token, queryString) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_SCENARIOS_ENDPOINT +
      queryString,
    signal,
    token
  );
};
