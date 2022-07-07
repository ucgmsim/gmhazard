import React, { useState, useEffect, useContext, Fragment } from "react";

import { Tabs, Tab } from "react-bootstrap";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import {
  MetadataBox,
  GuideMessage,
  ErrorMessage,
  LoadingSpinner,
  DownloadButton,
  HazardBranchPlot,
  HazardEnsemblePlot,
} from "components/common";
import { getProjectHazardCurve } from "apis/ProjectAPI";
import {
  handleErrors,
  APIQueryBuilder,
  createStationID,
  combineIMwithPeriod,
} from "utils/Utils";

const HazardViewerHazardCurve = () => {
  const { isAuthenticated, getTokenSilently } = useAuth0();

  const {
    projectHazardCurveGetClick,
    setProjectHazardCurveGetClick,
    projectId,
    projectLocation,
    projectVS30,
    projectZ1p0,
    projectZ2p5,
    projectLocationCode,
    projectLat,
    projectLng,
    projectSelectedIM,
    setProjectSelectedIM,
    projectSelectedIMPeriod,
    projectSelectedIMComponent,
    setProjectSelectedIMPeriod,
    projectSiteSelectionGetClick,
  } = useContext(GlobalContext);

  // For Fetching Hazard data
  const [showSpinnerHazard, setShowSpinnerHazard] = useState(false);
  const [showPlotHazard, setShowPlotHazard] = useState(false);
  const [showErrorMessage, setShowErrorMessage] = useState({
    isError: false,
    errorCode: null,
  });

  // For Plots (Branch/Ensemble)
  const [hazardData, setHazardData] = useState(null);
  const [hazardNZS1170p5Data, setHazardNZS1170p5Data] = useState(null);
  const [hazardNZTAData, setHazardNZTAData] = useState(null);
  const [percentileData, setPercentileData] = useState(null);
  const [extraInfo, setExtraInfo] = useState({});

  // For Metadata
  const [metadataParam, setMetadataParam] = useState({});

  // For Download button
  const [downloadToken, setDownloadToken] = useState("");
  const [filteredSelectedIM, setFilteredSelectedIM] = useState("");

  // Reset tabs if users click Get button from Site Selection
  useEffect(() => {
    if (projectSiteSelectionGetClick !== null) {
      setShowSpinnerHazard(false);
      setShowPlotHazard(false);
      setProjectHazardCurveGetClick(null);
      setProjectSelectedIM(null);
      setProjectSelectedIMPeriod(null);
    }
  }, [projectSiteSelectionGetClick]);

  // Replace the .(dot) to p for filename
  useEffect(() => {
    if (projectSelectedIM !== null && projectSelectedIM !== "pSA") {
      setFilteredSelectedIM(projectSelectedIM);
    } else if (
      projectSelectedIM === "pSA" &&
      projectSelectedIMPeriod !== null
    ) {
      setFilteredSelectedIM(
        `${projectSelectedIM}_${projectSelectedIMPeriod.replace(".", "p")}`
      );
    }
  }, [projectSelectedIM, projectSelectedIMPeriod]);

  // Get hazard curve data
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    if (projectHazardCurveGetClick !== null) {
      setShowPlotHazard(false);
      setShowSpinnerHazard(true);
      setShowErrorMessage({ isError: false, errorCode: null });
      resetHazardData();

      let token = null;
      const queryString = APIQueryBuilder({
        project_id: projectId["value"],
        station_id: createStationID(
          projectLocationCode[projectLocation],
          projectVS30,
          projectZ1p0,
          projectZ2p5
        ),
        im: combineIMwithPeriod(projectSelectedIM, projectSelectedIMPeriod),
        im_component: projectSelectedIMComponent,
      });

      (async () => {
        if (isAuthenticated) token = await getTokenSilently();

        getProjectHazardCurve(queryString, signal, token)
          .then(handleErrors)
          .then(async (response) => {
            const responseData = await response.json();
            updateHazardData(responseData);
          })
          .catch((error) => catchError(error));
      })();
    }

    return () => {
      abortController.abort();
    };
  }, [projectHazardCurveGetClick]);

  const resetHazardData = () => {
    setHazardData(null);
    setHazardNZS1170p5Data(null);
    setHazardNZTAData(null);
    setMetadataParam({});
    setExtraInfo({});
    setPercentileData(null);
    setDownloadToken("");
  };
  const updateHazardData = (hazardData) => {
    setHazardData(hazardData);
    // NZS1170p5 only available for PGA and pSA IM
    if (projectSelectedIM === "PGA" || projectSelectedIM === "pSA") {
      setHazardNZS1170p5Data(hazardData["nzs1170p5_hazard"]["im_values"]);
    }

    setMetadataParam({
      "Project Name": projectId["label"],
      "Project ID": projectId["value"],
      Location: projectLocation,
      Latitude: projectLat,
      Longitude: projectLng,
      Vs30: `${projectVS30} m/s`,
      z1p0: `${projectZ1p0} km`,
      z2p5: `${projectZ2p5} km`,
      "Intensity Measure": hazardData["im"],
    });
    setExtraInfo({
      from: "project",
      id: projectId,
      location: projectLocation,
      vs30: projectVS30,
      im: combineIMwithPeriod(projectSelectedIM, projectSelectedIMPeriod),
    });

    if (projectSelectedIM === "PGA") {
      if (
        !Object.values(hazardData["nzta_hazard"]["pga_values"]).includes("nan")
      ) {
        /*
        NZS1170p5 is available(Both Z Factor and Soil Class)
        NZTA is also valid (Only Soil Class)
        */
        setHazardNZTAData(hazardData["nzta_hazard"]["pga_values"]);
        setMetadataParam((prevState) => ({
          ...prevState,
          "NZS 1170.5 Z Factor": hazardData["nzs1170p5_hazard"]["Z"],
          "NZS 1170.5 Soil Class": hazardData["nzs1170p5_hazard"]["soil_class"],
          "NZTA Soil Class": hazardData["nzta_hazard"]["soil_class"],
        }));
      } else {
        /*
        NZS1170p5 is available(Both Z Factor and Soil Class)
        NZTA is there but its NaN
        */
        setHazardNZTAData(null);
        setMetadataParam((prevState) => ({
          ...prevState,
          "NZS 1170.5 Z Factor": hazardData["nzs1170p5_hazard"]["Z"],
          "NZS 1170.5 Soil Class": hazardData["nzs1170p5_hazard"]["soil_class"],
        }));
      }
    } else if (projectSelectedIM === "pSA") {
      /*
      NZS1170p5 is available(Both Z Factor and Soil Class)
      NZTA does not exist as IM is not PGA
      */
      setHazardNZTAData(null);
      setMetadataParam((prevState) => ({
        ...prevState,
        "NZS 1170.5 Z Factor": hazardData["nzs1170p5_hazard"]["Z"],
        "NZS 1170.5 Soil Class": hazardData["nzs1170p5_hazard"]["soil_class"],
      }));
      if (projectSelectedIMComponent !== "Larger") {
        setMetadataParam((prevState) => ({
          ...prevState,
          Disclaimer: CONSTANTS.NZ_CODE_DISCLAIMER,
        }));
      }
    }
    setPercentileData(hazardData["percentiles"]);
    setDownloadToken(hazardData["download_token"]);
    setShowSpinnerHazard(false);
    setShowPlotHazard(true);
  };

  const catchError = (error) => {
    if (error.name !== "AbortError") {
      setShowSpinnerHazard(false);
      setShowErrorMessage({ isError: true, errorCode: error });
    }
    console.log(error);
  };

  return (
    <div className="hazard-curve-viewer">
      <Tabs defaultActiveKey="ensemble" className="pivot-tabs">
        <Tab eventKey="ensemble" title={CONSTANTS.ENSEMBLE_BRANCHES}>
          {projectHazardCurveGetClick === null && (
            <GuideMessage
              header={CONSTANTS.HAZARD_CURVE}
              body={CONSTANTS.HAZARD_CURVE_GUIDE_MSG}
              instruction={CONSTANTS.PROJECT_HAZARD_CURVE_INSTRUCTION}
            />
          )}

          {showSpinnerHazard === true &&
            projectHazardCurveGetClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {projectHazardCurveGetClick !== null &&
            showSpinnerHazard === false &&
            showErrorMessage.isError === true && (
              <ErrorMessage errorCode={showErrorMessage.errorCode} />
            )}

          {showSpinnerHazard === false &&
            showPlotHazard === true &&
            hazardData !== null &&
            showErrorMessage.isError === false && (
              <Fragment>
                <HazardBranchPlot
                  hazardData={hazardData}
                  nzs1170p5Data={hazardNZS1170p5Data}
                  nztaData={hazardNZTAData}
                  percentileData={percentileData}
                  extra={extraInfo}
                />
                <MetadataBox metadata={metadataParam} />
              </Fragment>
            )}
        </Tab>

        <Tab
          eventKey="fault"
          title={CONSTANTS.FAULT_DISTRIBUTED_SEISMICITY_CONTRIBUTION}
        >
          {projectHazardCurveGetClick === null && (
            <GuideMessage
              header={CONSTANTS.HAZARD_CURVE}
              body={CONSTANTS.HAZARD_CURVE_GUIDE_MSG}
              instruction={CONSTANTS.PROJECT_HAZARD_CURVE_INSTRUCTION}
            />
          )}

          {showSpinnerHazard === true &&
            projectHazardCurveGetClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {projectHazardCurveGetClick !== null &&
            showSpinnerHazard === false &&
            showErrorMessage.isError === true && (
              <ErrorMessage errorCode={showErrorMessage.errorCode} />
            )}

          {showSpinnerHazard === false &&
            showPlotHazard === true &&
            hazardData !== null &&
            showErrorMessage.isError === false && (
              <Fragment>
                <HazardEnsemblePlot
                  hazardData={hazardData}
                  nzs1170p5Data={hazardNZS1170p5Data}
                  nztaData={hazardNZTAData}
                  percentileData={percentileData}
                  extra={extraInfo}
                />
                <MetadataBox metadata={metadataParam} />
              </Fragment>
            )}
        </Tab>
      </Tabs>

      <DownloadButton
        disabled={!showPlotHazard}
        downloadURL={CONSTANTS.PROJECT_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT}
        downloadToken={{
          hazard_token: downloadToken,
        }}
        fileName={`Projects_Hazard_${filteredSelectedIM}.zip`}
      />
    </div>
  );
};

export default HazardViewerHazardCurve;
