import React, { Fragment, useContext, useEffect, useState } from "react";

import { v4 as uuidv4 } from "uuid";

import { GlobalContext } from "context";
import { useAuth0 } from "components/common/ReactAuth0SPA";
import * as CONSTANTS from "constants/Constants";

import { CustomSelect, GuideTooltip } from "components/common";
import {
  handleErrors,
  sortIMs,
  renderSigfigs,
  APIQueryBuilder,
  splitIMPeriods,
} from "utils/Utils";

import "assets/style/HazardForms.css";

const SiteSelectionForm = () => {
  const {
    setProjectIMs,
    setProjectIMDict,
    setProjectDisagRPs,
    setProjectUHSRPs,
    setProjectId,
    setProjectVS30,
    setProjectZ1p0,
    setProjectZ2p5,
    setProjectLocation,
    setProjectLocationCode,
    setProjectLat,
    setProjectLng,
    projectSiteSelectionGetClick,
    setProjectSiteSelectionGetClick,
    setProjectGMSIDs,
    setProjectGMSIMTypes,
    setProjectGMSIMPeriods,
    setProjectGMSExceedances,
    setProjectGMSIMVectors,
    setProjectGMSNumGMs,
    setProjectScenarioIMComponentOptions,
  } = useContext(GlobalContext);

  const { isAuthenticated, getTokenSilently } = useAuth0();

  // For react-select (Dropdowns)
  const [projectIdOptions, setProjectIdOptions] = useState([]);
  const [localProjectLocations, setLocalProjectLocations] = useState({});
  const [locationOptions, setLocationOptions] = useState([]);
  const [vs30Options, setVs30Options] = useState([]);
  const [zOptions, setZOptions] = useState([]);

  // selected value from the dropdowns
  const [localProjectId, setLocalProjectId] = useState(null);
  const [localLocation, setLocalLocation] = useState(null);
  const [localVS30, setLocalVS30] = useState(null);
  const [localZs, setLocalZs] = useState(null);

  // Coordinates information after getting site information
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");

  // Getting Project IDs
  useEffect(() => {
    // Reset those to default to disable tabs
    setProjectId(null);
    setProjectLocation(null);
    setProjectVS30(null);

    const abortController = new AbortController();
    const signal = abortController.signal;

    const getProjectID = async () => {
      try {
        const token = await getTokenSilently();

        await fetch(
          CONSTANTS.INTERMEDIATE_API_URL +
            CONSTANTS.PROJECT_API_PROJECT_IDS_ENDPOINT,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: signal,
          }
        )
          .then(handleErrors)
          .then(async (response) => {
            const responseData = await response.json();
            setProjectIdOptions(responseData);
          })
          .catch((error) => {
            console.log(error);
          });
      } catch (error) {
        console.log(error);
      }
    };

    const getPublicProjectID = async () => {
      try {
        await fetch(
          CONSTANTS.INTERMEDIATE_API_URL +
            CONSTANTS.PUBLIC_API_PROJECT_IDS_ENDPOINT,
          {
            signal: signal,
          }
        )
          .then(handleErrors)
          .then(async (response) => {
            const responseData = await response.json();
            setProjectIdOptions(responseData);
          })
          .catch((error) => {
            console.log(error);
          });
      } catch (error) {
        console.log(error);
      }
    };

    if (isAuthenticated) {
      getProjectID();
    } else {
      getPublicProjectID();
    }

    return () => {
      abortController.abort();
    };
  }, []);

  // Getting location, IMs (for Hazard Curve) and RPs (for Disaggregation and UHS)
  // when the Project ID is selected
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getLocation = async () => {
      if (localProjectId !== null) {
        try {
          const token = await getTokenSilently();

          let queryString = APIQueryBuilder({
            project_id: localProjectId["value"],
          });

          await Promise.all([
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
          ])
            .then(handleErrors)
            .then(async ([location, im, disaggRPs, uhsRPs]) => {
              const responseLocationData = await location.json();
              const responseIMData = await im.json();
              const responseDisaggRPData = await disaggRPs.json();
              const responseUHSRPData = await uhsRPs.json();

              // Setting Locations
              setLocalProjectLocations(responseLocationData);
              // Setting IMs
              setProjectIMs(sortIMs(Object.keys(responseIMData["ims"])));
              setProjectIMDict(responseIMData["ims"]);
              setProjectScenarioIMComponentOptions(
                responseIMData["ims"]["pSA"]["components"]
              );

              // Setting RPs
              setProjectDisagRPs(responseDisaggRPData["rps"]);
              setProjectUHSRPs(responseUHSRPData["rps"]);
              // Reset dropdowns
              setLocalLocation(null);
              setLocalVS30(null);
              setLocalZs(null);
            })
            .catch((error) => {
              console.log(error);
            });
        } catch (error) {
          console.log(error);
        }
      }
    };

    const getPublicLocation = async () => {
      if (localProjectId !== null) {
        try {
          let queryString = APIQueryBuilder({
            project_id: localProjectId["value"],
          });

          await Promise.all([
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
          ])
            .then(handleErrors)
            .then(async ([location, im, disaggRPs, uhsRPs]) => {
              const responseLocationData = await location.json();
              const responseIMData = await im.json();
              const responseDisaggRPData = await disaggRPs.json();
              const responseUHSRPData = await uhsRPs.json();

              // Setting Locations
              setLocalProjectLocations(responseLocationData);
              // Setting IMs
              setProjectIMs(sortIMs(Object.keys(responseIMData["ims"])));
              setProjectIMDict(responseIMData["ims"]);
              setProjectScenarioIMComponentOptions(
                responseIMData["ims"]["pSA"]["components"]
              );

              // Setting RPs
              setProjectDisagRPs(responseDisaggRPData["rps"]);
              setProjectUHSRPs(responseUHSRPData["rps"]);
              // Reset dropdowns
              setLocalLocation(null);
              setLocalVS30(null);
              setLocalZs(null);
            })
            .catch((error) => {
              console.log(error);
            });
        } catch (error) {
          console.log(error);
        }
      }
    };

    if (isAuthenticated) {
      getLocation();
    } else {
      getPublicLocation();
    }

    return () => {
      abortController.abort();
    };
  }, [localProjectId]);

  // Create an array of objects for Location dropdown
  useEffect(() => {
    if (Object.values(localProjectLocations).length > 0) {
      let tempOptionArray = [];
      let tempLocationCodeObj = {};
      for (const key of Object.keys(localProjectLocations)) {
        // Only pushing names into an array, ex: Christchurch and Dunedin
        tempOptionArray.push(localProjectLocations[key]["name"]);
        // Looks like { Christchurch: chch, Dunedin: dud}, to get station code easy
        tempLocationCodeObj[localProjectLocations[key]["name"]] = key;
      }
      setLocationOptions(tempOptionArray);
      setProjectLocationCode(tempLocationCodeObj);
    }
  }, [localProjectLocations]);

  // Find an array of objects for Vs30 dropdown based on the chosen location
  useEffect(() => {
    if (localLocation !== null) {
      setVs30Options([]);
      for (const key of Object.keys(localProjectLocations)) {
        if (localLocation["value"] === localProjectLocations[key]["name"]) {
          setVs30Options([...new Set(localProjectLocations[key]["vs30"])]);
          setLat(localProjectLocations[key]["lat"]);
          setLng(localProjectLocations[key]["lon"]);
          // Reset the Vs30 value
          setLocalVS30(null);
        }
      }
    }
  }, [localLocation]);

  // Find an array of objects for Z1.0/Z2.5 dropdown based on the chosen Vs30
  useEffect(() => {
    if (localVS30 !== null) {
      setZOptions([]);
      for (const key of Object.keys(localProjectLocations)) {
        if (localLocation["value"] === localProjectLocations[key]["name"]) {
          let zOptionsList = [];
          for (
            let index = 0;
            index < localProjectLocations[key]["vs30"].length;
            index++
          ) {
            const vs30 = localProjectLocations[key]["vs30"][index];
            if (vs30 === localVS30["value"]) {
              zOptionsList.push({
                "Z1.0": localProjectLocations[key]["Z1.0"][index],
                "Z2.5": localProjectLocations[key]["Z2.5"][index],
              });
            }
          }
          setZOptions(zOptionsList);
          // Reset the Z values
          setLocalZs(null);
        }
      }
    }
  }, [localVS30]);

  // Reset dropdowns when Project ID gets changed
  useEffect(() => {
    if (localProjectId !== null) {
      setLocalLocation(null);
      setLocalVS30(null);
      setLocationOptions([]);
      setVs30Options([]);
      setZOptions([]);
    }
  }, [localProjectId]);

  // Get GMS IDs
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getGMSIDs = async () => {
      if (projectSiteSelectionGetClick !== null) {
        try {
          const token = await getTokenSilently();

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.PROJECT_API_GMS_RUNS_ENDPOINT +
              APIQueryBuilder({
                project_id: localProjectId["value"],
              }),
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          )
            .then(handleErrors)
            .then(async (response) => {
              const responseData = await response.json();
              const targetArr = Object.values(responseData);

              setProjectGMSIDs(Object.keys(responseData));

              const numGMs = {};
              for (const [key, value] of Object.entries(responseData)) {
                numGMs[key] = value["n_gms"];
              }
              setProjectGMSNumGMs(numGMs);

              const splitIMs = splitIMPeriods(
                getValuesFromArr(targetArr, "IM_j")
              );
              const periods = [...splitIMs["Periods"]];

              setProjectGMSIMTypes(sortIMs([...new Set(splitIMs["IMs"])]));
              setProjectGMSIMPeriods(periods.sort((a, b) => a - b));
              setProjectGMSExceedances(
                getValuesFromArr(targetArr, "exceedance")
              );
              setProjectGMSIMVectors(getValuesFromArr(targetArr, "IMs"));
            });
        } catch (error) {
          console.log(error);
        }
      }
    };

    const getPublicGMSIDs = async () => {
      if (projectSiteSelectionGetClick !== null) {
        try {
          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.PUBLIC_API_GMS_RUNS_ENDPOINT +
              APIQueryBuilder({
                project_id: localProjectId["value"],
              }),
            {
              signal: signal,
            }
          )
            .then(handleErrors)
            .then(async (response) => {
              const responseData = await response.json();
              const targetArr = Object.values(responseData);

              setProjectGMSIDs(Object.keys(responseData));

              const numGMs = {};
              for (const [key, value] of Object.entries(responseData)) {
                numGMs[key] = value["n_gms"];
              }
              setProjectGMSNumGMs(numGMs);

              const splitIMs = splitIMPeriods(
                getValuesFromArr(targetArr, "IM_j")
              );
              const periods = [...splitIMs["Periods"]];

              setProjectGMSIMTypes(sortIMs([...new Set(splitIMs["IMs"])]));
              setProjectGMSIMPeriods(periods.sort((a, b) => a - b));
              setProjectGMSExceedances(
                getValuesFromArr(targetArr, "exceedance")
              );
              setProjectGMSIMVectors(getValuesFromArr(targetArr, "IMs"));
            });
        } catch (error) {
          console.log(error);
        }
      }
    };

    if (isAuthenticated) {
      getGMSIDs();
    } else {
      getPublicGMSIDs();
    }

    return () => {
      abortController.abort();
    };
  }, [projectSiteSelectionGetClick]);

  const setGlobalVariables = () => {
    setProjectId(localProjectId);
    setProjectLocation(localLocation["value"]);
    setProjectVS30(localVS30["value"]);
    setProjectZ1p0(localZs["value"]["Z1.0"]);
    setProjectZ2p5(localZs["value"]["Z2.5"]);
    setProjectSiteSelectionGetClick(uuidv4());
    setProjectLat(renderSigfigs(lat, CONSTANTS.APP_UI_SIGFIGS));
    setProjectLng(renderSigfigs(lng, CONSTANTS.APP_UI_SIGFIGS));
  };

  /*
    Create a new array with an array of objects and each object's
    certain property's value then remove duplicates.
  */
  const getValuesFromArr = (givenArr, propertyName) => {
    if (propertyName === "IMs") {
      return [
        ...new Set(givenArr.map((gmsObj) => gmsObj[propertyName].join(", "))),
      ];
    } else {
      return [...new Set(givenArr.map((gmsObj) => gmsObj[propertyName]))];
    }
  };

  const invalidInputs = () => {
    return (
      localProjectId === null ||
      localLocation === null ||
      localVS30 === null ||
      localZs === null
    );
  };

  return (
    <Fragment>
      <div className="form-group form-section-title">
        Project Name
        <GuideTooltip
          explanation={
            CONSTANTS.TOOLTIP_MESSAGES["PROJECT_SITE_SELECTION_PROJECT_NAME"]
          }
        />
      </div>
      <div className="form-group">
        <CustomSelect
          setSelect={setLocalProjectId}
          options={projectIdOptions}
          isProjectID={true}
          resettable={false}
        />
      </div>

      <div className="form-group form-section-title">
        Location
        <GuideTooltip
          explanation={
            CONSTANTS.TOOLTIP_MESSAGES["PROJECT_SITE_SELECTION_LOCATION"]
          }
        />
      </div>
      <div className="form-group">
        <CustomSelect
          setSelect={setLocalLocation}
          options={locationOptions}
          placeholder={
            localProjectId === null
              ? "Please select the Project ID first..."
              : "Loading..."
          }
          resettable={false}
          resetOnChange={localProjectId}
        />
      </div>

      <div className="form-group form-section-title">
        <span>
          V<sub>S30</sub>
        </span>
        <GuideTooltip
          explanation={
            CONSTANTS.TOOLTIP_MESSAGES["PROJECT_SITE_SELECTION_VS30"]
          }
        />
      </div>
      <div className="form-group">
        <CustomSelect
          setSelect={setLocalVS30}
          options={vs30Options}
          placeholder={
            localLocation === null
              ? "Please select the Location first..."
              : "Loading..."
          }
          isVs30={true}
          resettable={false}
          resetOnChange={localLocation}
        />
      </div>

      <div className="form-group form-section-title">
        <span>
          Z<sub>1.0</sub> | Z<sub>2.5</sub>
        </span>
        <GuideTooltip
          explanation={
            CONSTANTS.TOOLTIP_MESSAGES["PROJECT_SITE_SELECTION_Z1p0_Z2p5"]
          }
        />
      </div>
      <div className="form-group">
        <CustomSelect
          setSelect={setLocalZs}
          options={zOptions}
          placeholder={
            localVS30 === null
              ? "Please select the Vs30 first..."
              : "Loading..."
          }
          isZ={true}
          resettable={false}
          resetOnChange={localVS30}
        />
      </div>

      <div className="form-group">
        <button
          id="project-site-selection-get"
          type="button"
          className="btn btn-primary mt-2"
          disabled={invalidInputs()}
          onClick={() => setGlobalVariables()}
        >
          Get
        </button>
      </div>
    </Fragment>
  );
};

export default SiteSelectionForm;
