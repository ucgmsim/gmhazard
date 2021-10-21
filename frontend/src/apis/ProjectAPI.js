import * as CONSTANTS from "constants/Constants";

export const getProjectID = async (signal, token) => {
  return await fetch(
    CONSTANTS.INTERMEDIATE_API_URL + CONSTANTS.PROJECT_API_PROJECT_IDS_ENDPOINT,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal: signal,
    }
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

export const getProjectGMSID = async (signal, token, queryString) => {
  return await fetch(
    CONSTANTS.INTERMEDIATE_API_URL +
      CONSTANTS.PROJECT_API_GMS_RUNS_ENDPOINT +
      queryString,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal: signal,
    }
  );
};
