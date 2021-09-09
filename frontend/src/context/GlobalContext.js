import React, { createContext, useState, useEffect } from "react";

import PropTypes from "prop-types";

import { useAuth0 } from "components/common/ReactAuth0SPA";
import * as CONSTANTS from "constants/Constants";

import { handleErrors } from "utils/Utils";

export const Context = createContext({});

export const Provider = (props) => {
  const { children } = props;

  // Site Selection
  const [station, setStation] = useState("");
  const [vs30, setVS30] = useState("");
  const [defaultVS30, setDefaultVS30] = useState("");
  const [Z1p0, setZ1p0] = useState("");
  const [defaultZ1p0, setDefaultZ1p0] = useState("");
  const [Z2p5, setZ2p5] = useState("");
  const [defaultZ2p5, setDefaultZ2p5] = useState("");
  const [locationSetClick, setLocationSetClick] = useState(null);

  const [selectedEnsemble, setSelectedEnsemble] = useState(
    CONSTANTS.APP_LOCATION_DEFAULT_ENSEMBLE
  );
  const [siteSelectionLat, setSiteSelectionLat] = useState("");
  const [siteSelectionLng, setSiteSelectionLng] = useState("");
  // For MapBox as using above two will send request everytime users change its value
  const [mapBoxCoordinate, setMapBoxCoordinate] = useState({
    lat: CONSTANTS.DEFAULT_MAPBOX_LAT,
    lng: CONSTANTS.DEFAULT_MAPBOX_LNG,
    input: "input",
  });

  // For IMs
  // The only exception regards naming conventions as 'ims' seems very odd
  const [IMs, setIMs] = useState([]);
  const [IMPeriods, setIMPeriods] = useState([]);
  const [IMDict, setIMDict] = useState([]);

  //  Seismic Hazard
  const [selectedIM, setSelectedIM] = useState(null);
  const [selectedIMPeriod, setSelectedIMPeriod] = useState(null);
  const [selectedIMComponent, setSelectedIMComponent] = useState(null);
  const [disaggAnnualProb, setDisaggAnnualProb] = useState("");

  const [hazardCurveComputeClick, setHazardCurveComputeClick] = useState(null);

  const [disaggComputeClick, setDisaggComputeClick] = useState(null);

  const [uhsComputeClick, setUHSComputeClick] = useState(null);

  const [nzs1170p5DefaultParams, setNZS1170p5DefaultParams] = useState([]);
  const [nztaDefaultParams, setNZTADefaultParams] = useState([]);

  const [nzs1170p5SoilClass, setNZS1170p5SoilClass] = useState([]);
  const [nztaSoilClass, setNZTASoilClass] = useState([]);

  const [nzs1170p5DefaultSoilClass, setNZS1170p5DefaultSoilClass] = useState(
    {}
  );
  const [nztaDefaultSoilClass, setNZTADefaultSoilClass] = useState({});

  // Check box stats for Hazard Curve and UHS for NZS1170p5 Code, default is true
  const [showHazardNZCode, setShowHazardNZCode] = useState(true);
  const [showUHSNZS1170p5, setShowUHSNZS1170p5] = useState(true);

  // NZS1170p5 Code is now split
  const [hazardNZS1170p5Data, setHazardNZS1170p5Data] = useState(null);
  const [uhsNZS1170p5Data, setUHSNZS1170p5Data] = useState(null);

  const [hazardNZTAData, setHazardNZTAData] = useState(null);

  // For a selected soil class
  const [selectedNZS1170p5SoilClass, setSelectedNZS1170p5SoilClass] = useState(
    {}
  );
  const [selectedNZTASoilClass, setSelectedNZTASoilClass] = useState({});
  // For a computed soil class, to validate compute button
  const [computedNZS1170p5SoilClass, setComputedNZS1170p5SoilClass] = useState(
    {}
  );
  const [computedNZTASoilClass, setComputedNZTASoilClass] = useState({});
  // For a selected Z Factor
  const [selectedNZS1170p5ZFactor, setSelectedNZS1170p5ZFactor] = useState(-1);
  // For a computed Z Factor, to validate compute button
  const [computedNZS1170p5ZFactor, setComputedNZS1170p5ZFactor] = useState(0);

  // To update Metadata after we compute Hazard Curve and/or NZ Codes
  const [isNZS1170p5Computed, setIsNZS1170p5Computed] = useState(false);
  const [isNZTAComputed, setIsNZTAComputed] = useState(false);
  const [isHazardCurveComputed, setIsHazardCurveComputed] = useState(false);

  // Download Token which is needed for Hazard Curve
  const [hazardNZS1170p5Token, setHazardNZS1170p5Token] = useState("");
  const [hazardNZTAToken, setHazardNZTAToken] = useState("");
  // and UHS
  const [uhsNZS1170p5Token, setUHSNZS1170p5Token] = useState("");

  const [uhsRateTable, setUHSRateTable] = useState([]);

  // GMS
  const [GMSComputeClick, setGMSComputeClick] = useState(null);
  const [GMSIMLevel, setGMSIMLevel] = useState("");
  const [GMSExcdRate, setGMSExcdRate] = useState("");
  const [GMSIMVector, setGMSIMVector] = useState([]);
  const [GMSRadio, setGMSRadio] = useState("im-level");
  const [GMSIMType, setGMSIMType] = useState(null);
  const [GMSIMPeriod, setGMSIMPeriod] = useState(null);
  const [GMSNum, setGMSNum] = useState("");
  const [GMSReplicates, setGMSReplicates] = useState(1);
  const [GMSWeights, setGMSWeights] = useState("");
  const [GMSMwMin, setGMSMwMin] = useState("");
  const [GMSMwMax, setGMSMwMax] = useState("");
  const [GMSRrupMin, setGMSRrupMin] = useState("");
  const [GMSRrupMax, setGMSRrupMax] = useState("");
  const [GMSVS30Min, setGMSVS30Min] = useState("");
  const [GMSVS30Max, setGMSVS30Max] = useState("");
  const [GMSSFMin, setGMSSFMin] = useState("");
  const [GMSSFMax, setGMSSFMax] = useState("");
  const [GMSDatabase, setGMSDatabase] = useState("");

  // Scenarios
  const [ScenarioComputeClick, setScenarioComputeClick] = useState(null);
  const [scenarioData, setScenarioData] = useState(null);
  const [scenarioSelectedRuptures, setScenarioSelectedRuptures] = useState([]);
  const [selectedScenarioIMComponent, setSelectedScenarioIMComponent] =
    useState(null);
  const [scenarioIMComponentOptions, setScenarioIMComponentOptions] = useState(
    []
  );

  // Project Tab

  // Site Selection
  const [projectId, setProjectId] = useState(null);
  const [projectLocationCode, setProjectLocationCode] = useState({});
  const [projectVS30, setProjectVS30] = useState(null);
  const [projectZ1p0, setProjectZ1p0] = useState("");
  const [projectZ2p5, setProjectZ2p5] = useState("");
  const [projectLocation, setProjectLocation] = useState(null);
  const [projectLat, setProjectLat] = useState(null);
  const [projectLng, setProjectLng] = useState(null);
  const [projectSiteSelectionGetClick, setProjectSiteSelectionGetClick] =
    useState(null);

  // Seismic Hazard
  const [projectSelectedIM, setProjectSelectedIM] = useState(null);
  const [projectSelectedIMPeriod, setProjectSelectedIMPeriod] = useState(null);
  const [projectSelectedIMComponent, setProjectSelectedIMComponent] =
    useState(null);
  const [projectIMs, setProjectIMs] = useState([]);
  const [projectIMDict, setProjectIMDict] = useState([]);
  const [projectIMPeriods, setProjectIMPeriods] = useState([]);
  const [projectHazardCurveGetClick, setProjectHazardCurveGetClick] =
    useState(null);

  const [projectDisagRPs, setProjectDisagRPs] = useState([]);
  const [projectUHSRPs, setProjectUHSRPs] = useState([]);
  const [projectSelectedDisagRP, setProjectSelectedDisagRP] = useState(null);
  const [projectDisaggGetClick, setProjectDisaggGetClick] = useState(null);
  const [projectUHSGetClick, setProjectUHSGetClick] = useState(null);
  const [projectSelectedUHSRP, setProjectSelectedUHSRP] = useState([]);

  // GMS
  const [projectGMSIDs, setProjectGMSIDs] = useState([]);
  const [projectGMSIMTypes, setProjectGMSIMTypes] = useState([]);
  const [projectGMSIMPeriods, setProjectGMSIMPeriods] = useState([]);
  const [projectGMSExceedances, setProjectGMSExceedances] = useState([]);
  const [projectGMSIMVectors, setProjectGMSIMVectors] = useState([]);
  const [projectGMSGetClick, setProjectGMSGetClick] = useState(null);
  const [projectGMSConditionIM, setProjectGMSConditionIM] = useState(null);
  const [projectGMSSelectedIMPeriod, setProjectGMSSelectedIMPeriod] =
    useState(null);
  const [projectGMSExceedance, setProjectGMSExceedance] = useState(null);
  const [projectGMSIMVector, setProjectGMSIMVector] = useState(null);
  const [projectGMSNumGMs, setProjectGMSNumGMs] = useState({});

  // Scenarios
  const [projectScenarioGetClick, setProjectScenarioGetClick] = useState(null);
  const [projectScenarioData, setProjectScenarioData] = useState(null);
  const [projectScenarioSelectedRuptures, setProjectScenarioSelectedRuptures] =
    useState([]);
  const [
    projectSelectedScenarioIMComponent,
    setProjectSelectedScenarioIMComponent,
  ] = useState(null);
  const [
    projectScenarioIMComponentOptions,
    setProjectScenarioIMComponentOptions,
  ] = useState([]);

  // User Permissions
  const { isAuthenticated, getTokenSilently } = useAuth0();

  const [permissions, setPermissions] = useState([]);

  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;
    // To get user data, we need to check that it is authenticated first
    if (isAuthenticated && permissions.length === 0) {
      const callGetUserData = async () => {
        const token = await getTokenSilently();

        await fetch(
          CONSTANTS.INTERMEDIATE_API_URL +
            CONSTANTS.INTERMEDIATE_API_AUTH0_USER_INFO_ENDPOINT,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: signal,
          }
        )
          .then(handleErrors)
          .then(async (response) => {
            const decodedToken = await response.json();
            setPermissions(decodedToken.permissions);
          })
          .catch((error) => {
            console.log(error);
          });
      };
      callGetUserData();
    }
  }, [isAuthenticated]);

  const hasPermission = (permission) => {
    return permissions.includes(permission);
  };

  const uhsTableAddRow = (row) => {
    if (
      uhsRateTable.length === 0 &&
      uhsRateTable[0] === CONSTANTS.UHS_TABLE_MESSAGE
    ) {
      uhsRateTable.length = 0;
    }
    uhsRateTable.push(row);
    setUHSRateTable(Array.from(uhsRateTable));
  };

  const uhsTableDeleteRow = (idx) => {
    uhsRateTable.splice(idx, 1);
    setUHSRateTable(Array.from(uhsRateTable));
  };

  // Make the context object:
  const globalContext = {
    // User Auth
    hasPermission,

    // Hazard Analysis Tab

    //Site Selection
    station,
    setStation,
    vs30,
    setVS30,
    defaultVS30,
    setDefaultVS30,
    Z1p0,
    setZ1p0,
    defaultZ1p0,
    setDefaultZ1p0,
    Z2p5,
    setZ2p5,
    defaultZ2p5,
    setDefaultZ2p5,
    locationSetClick,
    setLocationSetClick,

    selectedEnsemble,
    setSelectedEnsemble,
    siteSelectionLat,
    setSiteSelectionLat,
    siteSelectionLng,
    setSiteSelectionLng,

    // Seismic Hazard tab's Hazard Curve & GMS tab's IM Type
    IMs,
    setIMs,
    IMPeriods,
    setIMPeriods,
    IMDict,
    setIMDict,

    // MapBox
    mapBoxCoordinate,
    setMapBoxCoordinate,

    // Seismic Hazard
    selectedIM,
    setSelectedIM,
    selectedIMPeriod,
    setSelectedIMComponent,
    selectedIMComponent,
    setSelectedIMPeriod,
    disaggAnnualProb,
    setDisaggAnnualProb,
    hazardCurveComputeClick,
    setHazardCurveComputeClick,
    disaggComputeClick,
    setDisaggComputeClick,
    uhsComputeClick,
    setUHSComputeClick,
    nzs1170p5DefaultParams,
    setNZS1170p5DefaultParams,
    nztaDefaultParams,
    setNZTADefaultParams,
    nzs1170p5SoilClass,
    setNZS1170p5SoilClass,
    nztaSoilClass,
    setNZTASoilClass,
    nzs1170p5DefaultSoilClass,
    setNZS1170p5DefaultSoilClass,
    nztaDefaultSoilClass,
    setNZTADefaultSoilClass,
    selectedNZS1170p5SoilClass,
    setSelectedNZS1170p5SoilClass,
    selectedNZTASoilClass,
    setSelectedNZTASoilClass,
    computedNZS1170p5SoilClass,
    setComputedNZS1170p5SoilClass,
    computedNZTASoilClass,
    setComputedNZTASoilClass,
    selectedNZS1170p5ZFactor,
    setSelectedNZS1170p5ZFactor,
    computedNZS1170p5ZFactor,
    setComputedNZS1170p5ZFactor,
    showHazardNZCode,
    setShowHazardNZCode,
    showUHSNZS1170p5,
    setShowUHSNZS1170p5,
    hazardNZS1170p5Data,
    setHazardNZS1170p5Data,
    hazardNZTAData,
    setHazardNZTAData,
    uhsNZS1170p5Data,
    setUHSNZS1170p5Data,
    isNZS1170p5Computed,
    setIsNZS1170p5Computed,
    isNZTAComputed,
    setIsNZTAComputed,
    isHazardCurveComputed,
    setIsHazardCurveComputed,
    hazardNZS1170p5Token,
    setHazardNZS1170p5Token,
    hazardNZTAToken,
    setHazardNZTAToken,
    uhsNZS1170p5Token,
    setUHSNZS1170p5Token,

    uhsRateTable,
    setUHSRateTable,
    uhsTableAddRow,
    uhsTableDeleteRow,

    // GMS
    GMSComputeClick,
    setGMSComputeClick,
    GMSIMLevel,
    setGMSIMLevel,
    GMSExcdRate,
    setGMSExcdRate,
    GMSIMVector,
    setGMSIMVector,
    GMSRadio,
    setGMSRadio,
    GMSIMType,
    setGMSIMType,
    GMSIMPeriod,
    setGMSIMPeriod,
    GMSNum,
    setGMSNum,
    GMSReplicates,
    setGMSReplicates,
    GMSWeights,
    setGMSWeights,
    GMSMwMin,
    setGMSMwMin,
    GMSMwMax,
    setGMSMwMax,
    GMSRrupMin,
    setGMSRrupMin,
    GMSRrupMax,
    setGMSRrupMax,
    GMSVS30Min,
    setGMSVS30Min,
    GMSVS30Max,
    setGMSVS30Max,
    GMSSFMin,
    setGMSSFMin,
    GMSSFMax,
    setGMSSFMax,
    GMSDatabase,
    setGMSDatabase,

    // Scenarios
    ScenarioComputeClick,
    setScenarioComputeClick,
    scenarioData,
    setScenarioData,
    selectedScenarioIMComponent,
    setSelectedScenarioIMComponent,
    scenarioIMComponentOptions,
    setScenarioIMComponentOptions,
    scenarioSelectedRuptures,
    setScenarioSelectedRuptures,

    // Project Tab

    // Site Selection
    projectId,
    setProjectId,
    projectLocationCode,
    setProjectLocationCode,
    projectVS30,
    setProjectVS30,
    projectZ1p0,
    setProjectZ1p0,
    projectZ2p5,
    setProjectZ2p5,
    projectLocation,
    setProjectLocation,
    projectLat,
    setProjectLat,
    projectLng,
    setProjectLng,
    projectSiteSelectionGetClick,
    setProjectSiteSelectionGetClick,

    // Seismic Hazard
    projectSelectedIM,
    setProjectSelectedIM,
    projectSelectedIMPeriod,
    setProjectSelectedIMPeriod,
    projectSelectedIMComponent,
    setProjectSelectedIMComponent,
    projectIMs,
    setProjectIMs,
    projectIMDict,
    setProjectIMDict,
    projectIMPeriods,
    setProjectIMPeriods,
    projectHazardCurveGetClick,
    setProjectHazardCurveGetClick,
    projectDisagRPs,
    setProjectDisagRPs,
    projectUHSRPs,
    setProjectUHSRPs,
    projectSelectedDisagRP,
    setProjectSelectedDisagRP,
    projectDisaggGetClick,
    setProjectDisaggGetClick,
    projectUHSGetClick,
    setProjectUHSGetClick,
    projectSelectedUHSRP,
    setProjectSelectedUHSRP,

    // GMS
    projectGMSIDs,
    setProjectGMSIDs,
    projectGMSIMTypes,
    setProjectGMSIMTypes,
    projectGMSIMPeriods,
    setProjectGMSIMPeriods,
    projectGMSExceedances,
    setProjectGMSExceedances,
    projectGMSIMVectors,
    setProjectGMSIMVectors,
    projectGMSGetClick,
    setProjectGMSGetClick,
    projectGMSConditionIM,
    setProjectGMSConditionIM,
    projectGMSSelectedIMPeriod,
    setProjectGMSSelectedIMPeriod,
    projectGMSExceedance,
    setProjectGMSExceedance,
    projectGMSIMVector,
    setProjectGMSIMVector,
    projectGMSNumGMs,
    setProjectGMSNumGMs,

    // Scenarios
    projectScenarioGetClick,
    setProjectScenarioGetClick,
    projectScenarioData,
    setProjectScenarioData,
    projectSelectedScenarioIMComponent,
    setProjectSelectedScenarioIMComponent,
    projectScenarioIMComponentOptions,
    setProjectScenarioIMComponentOptions,
    projectScenarioSelectedRuptures,
    setProjectScenarioSelectedRuptures,
  };

  // pass the value in provider and return
  return <Context.Provider value={globalContext}>{children}</Context.Provider>;
};

export const { Consumer } = Context;

Provider.propTypes = {
  uhsRateTable: PropTypes.array,
};
