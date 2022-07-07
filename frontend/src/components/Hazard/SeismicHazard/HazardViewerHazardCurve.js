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
  HazardEnsemblePlot,
  HazardBranchPlot,
} from "components/common";
import {
  handleErrors,
  APIQueryBuilder,
  combineIMwithPeriod,
} from "utils/Utils";

const HazardViewerHazardCurve = () => {
  const { getTokenSilently } = useAuth0();

  const {
    hazardCurveComputeClick,
    setHazardCurveComputeClick,
    vs30,
    defaultVS30,
    selectedIM,
    selectedIMPeriod,
    selectedIMComponent,
    selectedEnsemble,
    station,
    hazardNZS1170p5Data,
    setHazardNZS1170p5Data,
    setHazardNZTAData,
    nzs1170p5DefaultParams,
    selectedNZS1170p5SoilClass,
    selectedNZTASoilClass,
    selectedNZS1170p5ZFactor,
    showHazardNZCode,
    setIsHazardCurveComputed,
    setIsNZS1170p5Computed,
    siteSelectionLat,
    siteSelectionLng,
    hazardNZS1170p5Token,
    setHazardNZS1170p5Token,
    hazardNZTAToken,
    setHazardNZTAToken,
    hazardNZTAData,
    setSelectedNZTASoilClass,
    nztaDefaultSoilClass,
    setIsNZTAComputed,
    computedNZS1170p5SoilClass,
    setComputedNZS1170p5SoilClass,
    computedNZS1170p5ZFactor,
    setComputedNZS1170p5ZFactor,
    computedNZTASoilClass,
    setComputedNZTASoilClass,
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
  const [percentileData, setPercentileData] = useState(null);
  const [extraInfo, setExtraInfo] = useState({});

  // For Metadata
  const [metadataParam, setMetadataParam] = useState({});

  // For Download button
  const [downloadHazardToken, setDownloadHazardToken] = useState("");
  const [filteredSelectedIM, setFilteredSelectedIM] = useState("");

  // Replace the .(dot) to p for filename
  useEffect(() => {
    if (selectedIM !== null && selectedIM !== "pSA") {
      setFilteredSelectedIM(selectedIM);
    } else if (selectedIM === "pSA" && selectedIMPeriod !== null) {
      setFilteredSelectedIM(
        `${selectedIM}_${selectedIMPeriod.replace(".", "p")}`
      );
    }
  }, [selectedIM, selectedIMPeriod]);

  // Reset variables when user chooses a different location
  useEffect(() => {
    setShowSpinnerHazard(false);
    setShowPlotHazard(false);
    setHazardData(null);
    setDownloadHazardToken("");
    setHazardCurveComputeClick(null);
  }, [station]);

  // Update metadataParam when NZS1170.5 Soil Class gets updated
  useEffect(() => {
    if (
      computedNZS1170p5SoilClass["value"] !== undefined &&
      computedNZS1170p5SoilClass["value"] !==
        metadataParam["NZS1170.5 Soil Class"]
    ) {
      setMetadataParam((prevState) => ({
        ...prevState,
        "NZS1170.5 Soil Class": computedNZS1170p5SoilClass["value"],
      }));
    }
  }, [computedNZS1170p5SoilClass]);

  // Update metadataParam when NZS1170.5 Z Factor gets updated
  useEffect(() => {
    if (
      computedNZS1170p5ZFactor !== 0 &&
      computedNZS1170p5ZFactor !== metadataParam["NZS1170.5 Z Factor"]
    ) {
      setMetadataParam((prevState) => ({
        ...prevState,
        "NZS1170.5 Z Factor": computedNZS1170p5ZFactor,
      }));
    }
  }, [computedNZS1170p5ZFactor]);

  // Update metadataParam when NZTA Soil Class gets updated
  useEffect(() => {
    if (
      computedNZTASoilClass["value"] !== undefined &&
      computedNZTASoilClass["value"] !== metadataParam["NZTA Soil Class"]
    ) {
      setMetadataParam((prevState) => ({
        ...prevState,
        "NZTA Soil Class": computedNZTASoilClass["value"],
      }));
    }
  }, [computedNZTASoilClass]);

  // Get Hazard Curve data with NZ Codes
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getHazardCurve = async () => {
      if (hazardCurveComputeClick !== null) {
        try {
          setShowPlotHazard(false);
          setShowSpinnerHazard(true);
          setShowErrorMessage({ isError: false, errorCode: null });
          setIsNZS1170p5Computed(false);
          setIsNZTAComputed(false);
          setIsHazardCurveComputed(false);
          setComputedNZS1170p5ZFactor(selectedNZS1170p5ZFactor);
          setComputedNZS1170p5SoilClass(selectedNZS1170p5SoilClass);

          // Reset NZCodes data
          setHazardNZS1170p5Data(null);
          setHazardNZS1170p5Token("");
          setHazardNZTAData(null);
          setHazardNZTAToken("");

          const token = await getTokenSilently();

          let hazardDataQueryString = APIQueryBuilder({
            ensemble_id: selectedEnsemble,
            station: station,
            im: combineIMwithPeriod(selectedIM, selectedIMPeriod),
            im_component: selectedIMComponent,
            calc_percentiles: 1,
          });
          if (vs30 !== defaultVS30) {
            hazardDataQueryString += `&vs30=${vs30}`;
          }

          fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_HAZARD_ENDPOINT +
              hazardDataQueryString,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          )
            .then(handleErrors)
            .then(async (hazardResponse) => {
              const hazardData = await hazardResponse.json();

              setIsHazardCurveComputed(true);
              setHazardData(hazardData);
              setDownloadHazardToken(hazardData["download_token"]);
              setPercentileData(hazardData["percentiles"]);

              setExtraInfo({
                from: "hazard",
                lat: siteSelectionLat,
                lng: siteSelectionLng,
              });
              setMetadataParam({
                Ensemble: hazardData["ensemble_id"],
                "Intensity Measure": hazardData["im"],
                Vs30: vs30,
              });

              const promises = [];

              if (selectedIM === "PGA" || selectedIM.startsWith("pSA")) {
                const nzs1170p5Code = fetch(
                  CONSTANTS.INTERMEDIATE_API_URL +
                    CONSTANTS.CORE_API_HAZARD_NZS1170P5_ENDPOINT +
                    APIQueryBuilder({
                      ensemble_id: selectedEnsemble,
                      station: station,
                      im: combineIMwithPeriod(selectedIM, selectedIMPeriod),
                      soil_class: selectedNZS1170p5SoilClass["value"],
                      distance: Number(nzs1170p5DefaultParams["distance"]),
                      z_factor: selectedNZS1170p5ZFactor,
                      im_component: selectedIMComponent,
                    }),
                  {
                    headers: {
                      Authorization: `Bearer ${token}`,
                    },
                    signal: signal,
                  }
                ).then((response) => response);

                promises.push(nzs1170p5Code);
              }
              if (selectedIM === "PGA") {
                /*
                  User hasn't clicked the NZTA tab yet
                  so no such property for selectedNZTASoilClass object
                  Use the default one for computedNZTASoilClass & selectedNZTASoilClass
                  Use the default soil class to compute NZTA code
                  if user did not choose the NZTA yet
                */
                const nztaCode = fetch(
                  CONSTANTS.INTERMEDIATE_API_URL +
                    CONSTANTS.CORE_API_HAZARD_NZTA_ENDPOINT +
                    APIQueryBuilder({
                      ensemble_id: selectedEnsemble,
                      station: station,
                      im: combineIMwithPeriod(selectedIM, selectedIMPeriod),
                      soil_class:
                        selectedNZTASoilClass["value"] ||
                        nztaDefaultSoilClass["value"],
                      im_component: selectedIMComponent,
                    }),
                  {
                    headers: {
                      Authorization: `Bearer ${token}`,
                    },
                    signal: signal,
                  }
                ).then((response) => response);

                promises.push(nztaCode);
              }

              return Promise.all(promises);
            })
            .then(handleErrors)
            .then(async (response) => {
              if (response.length >= 1) {
                const nzs1170p5Data = await response[0].json();
                setHazardNZS1170p5Data(
                  nzs1170p5Data["nzs1170p5_hazard"]["im_values"]
                );
                setHazardNZS1170p5Token(nzs1170p5Data["download_token"]);

                setMetadataParam((prevState) => ({
                  ...prevState,
                  "NZS1170.5 Z Factor": nzs1170p5Data["nzs1170p5_hazard"]["Z"],
                  "NZS1170.5 Soil Class":
                    nzs1170p5Data["nzs1170p5_hazard"]["soil_class"],
                }));
                if (selectedIMComponent !== "Larger") {
                  setMetadataParam((prevState) => ({
                    ...prevState,
                    Disclaimer: CONSTANTS.NZ_CODE_DISCLAIMER,
                  }));
                }
                setIsNZS1170p5Computed(true);
              }

              if (response.length === 2) {
                const nztaData = await response[1].json();

                /* 
                  Set NZTA related states only if NZTA does not include nan
                  as we currently don't have any NZTA values and they return NaN
                */
                if (
                  !Object.values(
                    nztaData["nzta_hazard"]["pga_values"]
                  ).includes("nan")
                ) {
                  // Update only if NZTA does have values
                  if (selectedNZTASoilClass["value"] === undefined) {
                    setComputedNZTASoilClass(nztaDefaultSoilClass);
                    setSelectedNZTASoilClass(nztaDefaultSoilClass);
                  } else {
                    setComputedNZTASoilClass(selectedNZTASoilClass);
                  }

                  setHazardNZTAData(nztaData["nzta_hazard"]["pga_values"]);
                  setHazardNZTAToken(nztaData["download_token"]);

                  setMetadataParam((prevState) => ({
                    ...prevState,
                    "NZTA Soil Class": nztaData["nzta_hazard"]["soil_class"],
                  }));

                  setIsNZTAComputed(true);
                } else {
                  setHazardNZTAData(null);
                }
              } else {
                setHazardNZTAData(null);
              }

              setShowSpinnerHazard(false);
              setShowPlotHazard(true);
              setIsHazardCurveComputed(false);
            })
            .catch((error) => {
              if (error.name !== "AbortError") {
                setShowSpinnerHazard(false);
                setIsHazardCurveComputed(false);
                setShowErrorMessage({ isError: true, errorCode: error });
              }
              console.log(error);
            });
        } catch (error) {
          setShowSpinnerHazard(false);
          setIsHazardCurveComputed(false);
          setShowErrorMessage({ isError: true, errorCode: error });
          console.log(error);
        }
      }
    };
    getHazardCurve();

    return () => {
      abortController.abort();
    };
  }, [hazardCurveComputeClick]);

  return (
    <div className="hazard-curve-viewer">
      <Tabs defaultActiveKey="ensemble" className="pivot-tabs">
        <Tab eventKey="ensemble" title={CONSTANTS.ENSEMBLE_BRANCHES}>
          {hazardCurveComputeClick === null && (
            <GuideMessage
              header={CONSTANTS.HAZARD_CURVE}
              body={CONSTANTS.HAZARD_CURVE_GUIDE_MSG}
              instruction={CONSTANTS.HAZARD_CURVE_INSTRUCTION}
            />
          )}

          {showSpinnerHazard === true &&
            hazardCurveComputeClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {hazardCurveComputeClick !== null &&
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
                  percentileData={percentileData}
                  showNZCode={showHazardNZCode}
                  nztaData={hazardNZTAData}
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
          {hazardCurveComputeClick === null && (
            <GuideMessage
              header={CONSTANTS.HAZARD_CURVE}
              body={CONSTANTS.HAZARD_CURVE_GUIDE_MSG}
              instruction={CONSTANTS.HAZARD_CURVE_INSTRUCTION}
            />
          )}

          {showSpinnerHazard === true &&
            hazardCurveComputeClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {hazardCurveComputeClick !== null &&
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
                  percentileData={percentileData}
                  showNZCode={showHazardNZCode}
                  nztaData={hazardNZTAData}
                  extra={extraInfo}
                />
                <MetadataBox metadata={metadataParam} />
              </Fragment>
            )}
        </Tab>
      </Tabs>

      <DownloadButton
        disabled={!showPlotHazard}
        downloadURL={CONSTANTS.CORE_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT}
        downloadToken={{
          hazard_token: downloadHazardToken,
          nzs1170p5_hazard_token: hazardNZS1170p5Token,
          nzta_hazard_token: hazardNZTAToken,
        }}
        fileName={`Hazard_${filteredSelectedIM}.zip`}
      />
    </div>
  );
};

export default HazardViewerHazardCurve;
