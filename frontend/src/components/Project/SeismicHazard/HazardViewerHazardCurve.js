import React, { useState, useEffect, useContext, Fragment } from "react";

import { Tabs, Tab } from "react-bootstrap";

import { GlobalContext } from "context";
import { useAuth0 } from "components/common/ReactAuth0SPA";
import * as CONSTANTS from "constants/Constants";

import {
  LoadingSpinner,
  DownloadButton,
  GuideMessage,
  ErrorMessage,
  HazardEnsemblePlot,
  HazardBranchPlot,
  HazardCurveMetadata,
} from "components/common";
import {
  handleErrors,
  APIQueryBuilder,
  combineIMwithPeriod,
  createStationID,
} from "utils/Utils";

const HazardViewerHazardCurve = () => {
  const { getTokenSilently } = useAuth0();

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

  // Reset tabs if users change Project ID, Vs30 or Location
  useEffect(() => {
    setShowSpinnerHazard(false);
    setShowPlotHazard(false);
    setProjectHazardCurveGetClick(null);
    setProjectSelectedIM(null);
    setProjectSelectedIMPeriod(null);
  }, [projectId, projectVS30, projectLocation]);

  // Get hazard curve data
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getHazardCurve = async () => {
      if (projectHazardCurveGetClick !== null) {
        try {
          setShowPlotHazard(false);
          setShowSpinnerHazard(true);
          setShowErrorMessage({ isError: false, errorCode: null });

          const token = await getTokenSilently();

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.PROJECT_API_HAZARD_ENDPOINT +
              APIQueryBuilder({
                project_id: projectId["value"],
                station_id: createStationID(
                  projectLocationCode[projectLocation],
                  projectVS30,
                  projectZ1p0,
                  projectZ2p5
                ),
                im: combineIMwithPeriod(
                  projectSelectedIM,
                  projectSelectedIMPeriod
                ),
                im_component: projectSelectedIMComponent,
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

              setHazardData(responseData);
              setHazardNZS1170p5Data(
                responseData["nzs1170p5_hazard"]["im_values"]
              );
              setMetadataParam({
                "Project Name": projectId["label"],
                "Project ID": projectId["value"],
                Location: projectLocation,
                Latitude: projectLat,
                Longitude: projectLng,
                Vs30: `${projectVS30} m/s`,
                "Intensity Measure": responseData["im"],
              });
              setExtraInfo({
                from: "project",
                id: projectId,
                location: projectLocation,
                vs30: projectVS30,
                im: combineIMwithPeriod(
                  projectSelectedIM,
                  projectSelectedIMPeriod
                ),
              });

              if (projectSelectedIM === "PGA") {
                if (
                  !Object.values(
                    responseData["nzta_hazard"]["pga_values"]
                  ).includes("nan")
                ) {
                  /*
                    NZS1170p5 is available(Both Z Factor and Soil Class)
                    NZTA is also valid (Only Soil Class)
                  */
                  setHazardNZTAData(responseData["nzta_hazard"]["pga_values"]);
                  setMetadataParam((prevState) => ({
                    ...prevState,
                    "NZS1170.5 Z Factor": responseData["nzs1170p5_hazard"]["Z"],
                    "NZS1170.5 Soil Class":
                      responseData["nzs1170p5_hazard"]["soil_class"],
                    "NZTA Soil Class":
                      responseData["nzta_hazard"]["soil_class"],
                  }));
                } else {
                  /*
                    NZS1170p5 is available(Both Z Factor and Soil Class)
                    NZTA is there but its NaN
                  */
                  setHazardNZTAData(null);
                  setMetadataParam((prevState) => ({
                    ...prevState,
                    "NZS1170.5 Z Factor": responseData["nzs1170p5_hazard"]["Z"],
                    "NZS1170.5 Soil Class":
                      responseData["nzs1170p5_hazard"]["soil_class"],
                  }));
                }
              } else {
                /*
                  NZS1170p5 is available(Both Z Factor and Soil Class)
                  NZTA does not exist as IM is not PGA
                */
                setHazardNZTAData(null);
                setMetadataParam((prevState) => ({
                  ...prevState,
                  "NZS1170.5 Z Factor": responseData["nzs1170p5_hazard"]["Z"],
                  "NZS1170.5 Soil Class":
                    responseData["nzs1170p5_hazard"]["soil_class"],
                }));
                if (projectSelectedIMComponent !== "Larger") {
                  setMetadataParam((prevState) => ({
                    ...prevState,
                    "Disclaimer": "NZ Code values have been converted from original Larger IM Component",
                  }));
                }
              }
              setPercentileData(responseData["percentiles"]);
              setDownloadToken(responseData["download_token"]);
              setShowSpinnerHazard(false);
              setShowPlotHazard(true);
            })
            .catch((error) => {
              if (error.name !== "AbortError") {
                setShowSpinnerHazard(false);
                setShowErrorMessage({ isError: true, errorCode: error });
              }

              console.log(error);
            });
        } catch (error) {
          setShowSpinnerHazard(false);
          setShowErrorMessage({ isError: true, errorCode: error });
          console.log(error);
        }
      }
    };
    getHazardCurve();

    return () => {
      abortController.abort();
    };
  }, [projectHazardCurveGetClick]);

  return (
    <div className="hazard-curve-viewer">
      <Tabs defaultActiveKey="ensemble" className="pivot-tabs">
        <Tab eventKey="ensemble" title="Ensemble branches">
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
                <HazardCurveMetadata metadata={metadataParam} />
              </Fragment>
            )}
        </Tab>

        <Tab eventKey="fault" title="Fault/distributed seismicity contribution">
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
                <HazardCurveMetadata metadata={metadataParam} />
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
