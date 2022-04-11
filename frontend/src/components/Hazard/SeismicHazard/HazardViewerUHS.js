import React, { Fragment, useEffect, useState, useContext } from "react";

import { Tabs, Tab } from "react-bootstrap";
import Select from "react-select";

import { useAuth0 } from "components/common/ReactAuth0SPA";
import * as CONSTANTS from "constants/Constants";
import { GlobalContext } from "context";

import {
  UHSPlot,
  UHSBranchPlot,
  LoadingSpinner,
  DownloadButton,
  GuideMessage,
  ErrorMessage,
} from "components/common";
import { APIQueryBuilder, handleErrors, renderSigfigs } from "utils/Utils";

const HazardViewerUHS = () => {
  const { getTokenSilently } = useAuth0();

  const {
    uhsComputeClick,
    setUHSComputeClick,
    selectedNZS1170p5SoilClass,
    nzs1170p5DefaultParams,
    selectedNZS1170p5ZFactor,
    vs30,
    defaultVS30,
    selectedEnsemble,
    selectedIMComponent,
    station,
    uhsRateTable,
    siteSelectionLat,
    siteSelectionLng,
    uhsNZS1170p5Data,
    setUHSNZS1170p5Data,
    uhsNZS1170p5Token,
    setUHSNZS1170p5Token,
    showUHSNZS1170p5,
    setComputedNZS1170p5ZFactor,
    setComputedNZS1170p5SoilClass,
  } = useContext(GlobalContext);

  // For UHS data fetcher
  const [showSpinnerUHS, setShowSpinnerUHS] = useState(false);
  const [showPlotUHS, setShowPlotUHS] = useState(false);
  const [showErrorMessage, setShowErrorMessage] = useState({
    isError: false,
    errorCode: null,
  });

  // For UHS plots
  const [uhsData, setUHSData] = useState(null);
  const [uhsBranchData, setUHSBranchData] = useState(null);
  const [extraInfo, setExtraInfo] = useState({});

  // For Download data button
  const [downloadUHSToken, setDownloadUHSToken] = useState("");

  // For Select, dropdown
  const [localSelectedRP, setLocalSelectedRP] = useState(null);
  const [uhsRPOptions, setUHSRPOptions] = useState([]);

  // Reset variables when user chooses a different location
  useEffect(() => {
    setShowSpinnerUHS(false);
    setShowPlotUHS(false);
    setUHSData(null);
    setDownloadUHSToken("");
    setUHSComputeClick(null);
  }, [station]);

  // Setting variables for the selected RP and RP options
  useEffect(() => {
    if (uhsData !== null) {
      const sortedSelectedRP = getExceedances()
        .sort((a, b) => {
          return parseFloat(1 / Number(a)) - parseFloat(1 / Number(b));
        })
        .map((option) => ({
          value: option,
          label: renderSigfigs(1 / Number(option), CONSTANTS.APP_UI_SIGFIGS),
        }));

      setLocalSelectedRP(sortedSelectedRP[0]);
      setUHSRPOptions(sortedSelectedRP);
    }
  }, [uhsData]);

  // Get UHS data
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const loadUHSData = async () => {
      if (uhsComputeClick !== null) {
        try {
          setShowPlotUHS(false);
          setShowSpinnerUHS(true);
          setShowErrorMessage({ isError: false, errorCode: null });
          setComputedNZS1170p5ZFactor(selectedNZS1170p5ZFactor);
          setComputedNZS1170p5SoilClass(selectedNZS1170p5SoilClass);

          const token = await getTokenSilently();

          let queryString = APIQueryBuilder({
            ensemble_id: selectedEnsemble,
            station: station,
            exceedances: `${getExceedances().join(",")}`,
            calc_percentiles: 1,
            im_component:
              selectedIMComponent === null ? "RotD50" : selectedIMComponent,
          });
          if (vs30 !== defaultVS30) {
            queryString += `&vs30=${vs30}`;
          }

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_HAZARD_UHS_ENDPOINT +
              queryString,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          )
            .then(handleErrors)
            .then(async (uhsResponse) => {
              const responseData = await uhsResponse.json();

              setUHSData(responseData["uhs_results"]);
              setUHSBranchData(responseData["branch_uhs_results"]);
              setDownloadUHSToken(responseData["download_token"]);

              return fetch(
                CONSTANTS.INTERMEDIATE_API_URL +
                  CONSTANTS.CORE_API_HAZARD_UHS_NZS1170P5_ENDPOINT +
                  APIQueryBuilder({
                    ensemble_id: selectedEnsemble,
                    station: station,
                    exceedances: `${getExceedances().join(",")}`,
                    soil_class: selectedNZS1170p5SoilClass["value"],
                    distance: Number(nzs1170p5DefaultParams["distance"]),
                    z_factor: selectedNZS1170p5ZFactor,
                    im_component:
                      selectedIMComponent === null
                        ? "RotD50"
                        : selectedIMComponent,
                  }),
                {
                  headers: {
                    Authorization: `Bearer ${token}`,
                  },
                  signal: signal,
                }
              );
            })
            .then(handleErrors)
            .then(async (nzs1170p5CodeResponse) => {
              const nzs1170p5CodeDataResponse =
                await nzs1170p5CodeResponse.json();
              setUHSNZS1170p5Data(
                nzs1170p5CodeDataResponse["nzs1170p5_uhs_df"]
              );
              setUHSNZS1170p5Token(nzs1170p5CodeDataResponse["download_token"]);

              setExtraInfo({
                from: "hazard",
                lat: siteSelectionLat,
                lng: siteSelectionLng,
                selectedRPs: getSelectedRP(),
              });

              setShowSpinnerUHS(false);
              setShowPlotUHS(true);
            })
            .catch((error) => {
              if (error.name !== "AbortError") {
                setShowSpinnerUHS(false);
                setShowErrorMessage({ isError: true, errorCode: error });
              }
              console.log(error);
            });
        } catch (error) {
          setShowSpinnerUHS(false);
          setShowErrorMessage({ isError: false, errorCode: error });
        }
      }
    };

    loadUHSData();

    return () => {
      abortController.abort();
    };
  }, [uhsComputeClick]);

  // Create an array of RPs from selected annual exceedance rates
  const getSelectedRP = () => {
    const selectedRPs = uhsRateTable.map((rate) => {
      return renderSigfigs(1 / parseFloat(rate), CONSTANTS.APP_UI_SIGFIGS);
    });

    return selectedRPs;
  };

  // Create an array of annual exeedance rates
  const getExceedances = () => {
    const exceedances = uhsRateTable.map((rate) => {
      return parseFloat(rate);
    });

    return exceedances;
  };

  return (
    <div className="uhs-viewer">
      <Tabs defaultActiveKey="allRP" className="pivot-tabs">
        <Tab eventKey="allRP" title="Selected Return Periods">
          <div className="tab-content">
            {uhsComputeClick === null && (
              <GuideMessage
                header={CONSTANTS.UNIFORM_HAZARD_SPECTRUM}
                body={CONSTANTS.UNIFORM_HAZARD_SPECTRUM_MSG}
                instruction={CONSTANTS.UNIFORM_HAZARD_SPECTRUM_INSTRUCTION}
              />
            )}

            {showSpinnerUHS === true &&
              uhsComputeClick !== null &&
              showErrorMessage.isError === false && <LoadingSpinner />}

            {uhsComputeClick !== null &&
              showSpinnerUHS === false &&
              showErrorMessage.isError === true && (
                <ErrorMessage errorCode={showErrorMessage.errorCode} />
              )}

            {showSpinnerUHS === false &&
              showPlotUHS === true &&
              showErrorMessage.isError === false && (
                <Fragment>
                  <UHSPlot
                    from={"non-projects"}
                    uhsData={uhsData}
                    nzs1170p5Data={uhsNZS1170p5Data}
                    extra={extraInfo}
                    showNZS1170p5={showUHSNZS1170p5}
                  />
                </Fragment>
              )}
          </div>
        </Tab>
        <Tab eventKey="specificRP" title="Return Period branches">
          <div className="tab-content">
            {uhsComputeClick === null && (
              <GuideMessage
                header={CONSTANTS.UNIFORM_HAZARD_SPECTRUM}
                body={CONSTANTS.UNIFORM_HAZARD_SPECTRUM_MSG}
                instruction={CONSTANTS.UNIFORM_HAZARD_SPECTRUM_INSTRUCTION}
              />
            )}

            {showSpinnerUHS === true &&
              uhsComputeClick !== null &&
              showErrorMessage.isError === false && <LoadingSpinner />}

            {uhsComputeClick !== null &&
              showSpinnerUHS === false &&
              showErrorMessage.isError === true && (
                <ErrorMessage errorCode={showErrorMessage.errorCode} />
              )}

            {showSpinnerUHS === false &&
              showPlotUHS === true &&
              showErrorMessage.isError === false && (
                <div className="form-group">
                  <Fragment>
                    <Select
                      id={"hazard-rp"}
                      value={localSelectedRP}
                      onChange={(rpOption) => setLocalSelectedRP(rpOption)}
                      options={uhsRPOptions}
                      menuPlacement="auto"
                    />
                  </Fragment>
                </div>
              )}

            {showSpinnerUHS === false &&
              showPlotUHS === true &&
              showErrorMessage.isError === false && (
                <Fragment>
                  <UHSBranchPlot
                    from={"non-projects"}
                    uhsData={uhsData[localSelectedRP["value"]]}
                    uhsBranchData={
                      uhsBranchData === undefined || uhsBranchData === null
                        ? null
                        : uhsBranchData[localSelectedRP["value"]]
                    }
                    nzs1170p5Data={uhsNZS1170p5Data[localSelectedRP["value"]]}
                    rp={renderSigfigs(
                      1 / Number(localSelectedRP["value"]),
                      CONSTANTS.APP_UI_SIGFIGS
                    )}
                    extra={extraInfo}
                    showNZS1170p5={showUHSNZS1170p5}
                  />
                </Fragment>
              )}
          </div>
        </Tab>
      </Tabs>

      <DownloadButton
        disabled={!showPlotUHS}
        downloadURL={CONSTANTS.CORE_API_HAZARD_UHS_DOWNLOAD_ENDPOINT}
        downloadToken={{
          uhs_token: downloadUHSToken,
          nzs1170p5_hazard_token: uhsNZS1170p5Token,
        }}
        fileName="Uniform_Hazard_Spectrum.zip"
      />
    </div>
  );
};

export default HazardViewerUHS;
