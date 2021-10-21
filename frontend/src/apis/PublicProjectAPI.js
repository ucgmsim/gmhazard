import * as CONSTANTS from "constants/Constants";

/* Project - Site Selection Form */
export const getPublicProjectID = async (signal) => {
  return await fetch(
    CONSTANTS.INTERMEDIATE_API_URL + CONSTANTS.PUBLIC_API_PROJECT_IDS_ENDPOINT,
    {
      signal: signal,
    }
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

export const getPublicProjectGMSID = async (signal, queryString) => {
  return await fetch(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_GMS_RUNS_ENDPOINT +
      queryString,
    {
      signal: signal,
    }
  );
};

/* Project - Site Selection Viewer */
export const getPublicProjectMaps = async (signal, queryString) => {
  return await fetch(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_MAPS_ENDPOINT +
      queryString,
    {
      signal: signal,
    }
  );
};

/* Project - Hazard Curve Viewer */
export const getPublicProjectHazardCurve = async (signal, queryString) => {
  return await fetch(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_HAZARD_ENDPOINT +
      queryString,
    {
      signal: signal,
    }
  );
};

/* Project - Disaggregation Viewer */
export const getPublicProjectDisaggregation = async (signal, queryString) => {
  return await fetch(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PUBLIC_API_HAZARD_DISAGG_ENDPOINT +
      queryString,
    {
      signal: signal,
    }
  );
};
