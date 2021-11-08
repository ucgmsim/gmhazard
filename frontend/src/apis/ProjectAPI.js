import * as CONSTANTS from "constants/Constants";

const projectAPIRequest = async (url, signal, token) => {
  let options = {
    signal: signal,
  };

  if (token) {
    options["headers"] = {
      Authorization: `Bearer ${token}`,
    };
  }

  return await fetch(url, options);
};

/* Project - Site Selection Form */
export const getProjectID = (signal, token = null) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL + CONSTANTS.PROJECT_API_PROJECT_IDS_ENDPOINT,
    signal,
    token
  );
};

export const getProjectLocation = async (queryString, signal, token = null) => {
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

export const getProjectGMSID = (queryString, signal, token = null) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_GMS_RUNS_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - Site Selection Viewer */
export const getProjectMaps = (queryString, signal, token = null) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_MAPS_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - Hazard Curve Viewer */
export const getProjectHazardCurve = (queryString, signal, token = null) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_HAZARD_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - Disaggregation Viewer */
export const getProjectDisaggregation = (queryString, signal, token = null) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_HAZARD_DISAGG_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - UHS Viewer */
export const getProjectUHS = (queryString, signal, token = null) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_HAZARD_UHS_ENDPOINT +
      queryString,
    signal,
    token
  );
};

/* Project - GMS Viewer */
export const getProjectGMS = async (queryString, signal, token = null) => {
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
export const getProjectScenario = (queryString, signal, token = null) => {
  return projectAPIRequest(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_SCENARIOS_ENDPOINT +
      queryString,
    signal,
    token
  );
};
