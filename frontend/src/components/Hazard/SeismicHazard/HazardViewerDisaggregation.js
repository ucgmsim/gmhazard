import React, { Fragment, useState, useEffect, useContext } from "react";

import $ from "jquery";
import { Tabs, Tab } from "react-bootstrap";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import {
  LoadingSpinner,
  DownloadButton,
  GuideMessage,
  ErrorMessage,
  ContributionTable,
} from "components/common";
import {
  handleErrors,
  APIQueryBuilder,
  combineIMwithPeriod,
} from "utils/Utils";

const HazardViewerDisaggregation = () => {
  const { getTokenSilently } = useAuth0();

  const {
    disaggComputeClick,
    setDisaggComputeClick,
    vs30,
    defaultVS30,
    station,
    selectedIM,
    selectedIMPeriod,
    selectedIMComponent,
    selectedEnsemble,
    disaggAnnualProb,
  } = useContext(GlobalContext);

  // For disagg data fetcher
  const [showSpinnerDisaggFault, setShowSpinnerDisaggFault] = useState(false);
  const [showSpinnerDisaggEpsilon, setShowSpinnerDisaggEpsilon] =
    useState(false);
  const [showSpinnerContribTable, setShowSpinnerContribTable] = useState(false);
  const [showErrorMessage, setShowErrorMessage] = useState({
    isError: false,
    errorCode: null,
  });
  const [showPlotDisaggEpsilon, setShowPlotDisaggEpsilon] = useState(false);
  const [showPlotDisaggFault, setShowPlotDisaggFault] = useState(false);
  const [showContribTable, setShowContribTable] = useState(false);

  // For Source contributions table
  const [disaggMeanData, setDisaggMeanData] = useState(null);
  const [disaggContributionData, setDisaggContributionData] = useState(null);
  const [rowsToggled, setRowsToggled] = useState(true);
  const [toggleText, setToggleText] = useState(CONSTANTS.SHOW_MORE);

  // For download data button
  const [downloadToken, setDownloadToken] = useState("");
  const [filteredSelectedIM, setFilteredSelectedIM] = useState("");

  // For Epsilon and Fault/distributed seismicity images
  const [disaggPlotData, setDisaggPlotData] = useState({
    eps: null,
    src: null,
  });

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
    setShowSpinnerDisaggFault(false);
    setShowSpinnerDisaggEpsilon(false);
    setShowSpinnerContribTable(false);
    setShowPlotDisaggEpsilon(false);
    setShowPlotDisaggFault(false);
    setShowContribTable(false);
    setDownloadToken("");
    setDisaggComputeClick(null);
  }, [station]);

  // Get Hazard Disagg data
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getHazardData = async () => {
      if (disaggComputeClick !== null) {
        try {
          const token = await getTokenSilently();
          setShowErrorMessage({ isError: false, errorCode: null });

          setShowSpinnerDisaggEpsilon(true);

          setShowSpinnerDisaggFault(true);

          setShowPlotDisaggEpsilon(false);
          setShowPlotDisaggFault(false);

          setShowContribTable(false);
          setShowSpinnerContribTable(true);

          let queryString = APIQueryBuilder({
            ensemble_id: selectedEnsemble,
            station: station,
            im: combineIMwithPeriod(selectedIM, selectedIMPeriod),
            im_component: selectedIMComponent,
            exceedance: disaggAnnualProb,
            gmt_plot: true,
          });
          if (vs30 !== defaultVS30) {
            queryString += `&vs30=${vs30}`;
          }

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_HAZARD_DISAGG_ENDPOINT +
              queryString,
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

              setDownloadToken(responseData["download_token"]);

              setShowSpinnerDisaggEpsilon(false);

              const srcDisaggPlot = responseData["gmt_plot_src"];
              const epsDisaggPlot = responseData["gmt_plot_eps"];

              setDisaggPlotData({
                src: srcDisaggPlot,
                eps: epsDisaggPlot,
              });

              setShowSpinnerDisaggEpsilon(false);

              setShowSpinnerDisaggFault(false);

              setShowSpinnerContribTable(false);

              setShowPlotDisaggEpsilon(true);

              setShowPlotDisaggFault(true);

              setShowContribTable(true);

              const disaggTotalData =
                responseData["disagg_data"]["total_contribution"];

              const extraInfo = responseData["extra_info"];
              try {
                extraInfo.rupture_name["distributed_seismicity"] =
                  CONSTANTS.DISTRIBUTED_SEISMICITY;
              } catch (err) {
                console.log(err.message);
              }

              const data = Array.from(Object.keys(disaggTotalData), (key) => {
                return [
                  key,
                  extraInfo.rupture_name[key],
                  disaggTotalData[key],
                  extraInfo.annual_rec_prob[key],
                  extraInfo.magnitude[key],
                  extraInfo.rrup[key],
                ];
              });

              data.sort((entry1, entry2) => {
                return entry1[2] > entry2[2] ? -1 : 1;
              });

              setDisaggMeanData(responseData["disagg_data"]);
              setDisaggContributionData(data);
            })
            .catch((error) => {
              if (error.name !== "AbortError") {
                setShowSpinnerContribTable(false);
                setShowSpinnerDisaggEpsilon(false);
                setShowSpinnerDisaggFault(false);

                setShowErrorMessage({ isError: true, errorCode: error });
              }

              console.log(error);
            });
        } catch (error) {
          setShowSpinnerContribTable(false);
          setShowSpinnerDisaggEpsilon(false);
          setShowSpinnerDisaggFault(false);

          setShowErrorMessage({ isError: true, errorCode: error });
          console.log(error);
        }
      }
    };
    getHazardData();

    return () => {
      abortController.abort();
    };
  }, [disaggComputeClick]);

  const rowToggle = () => {
    setRowsToggled(!rowsToggled);

    if (rowsToggled) {
      $("tr.contrib-toggle-row.contrib-row-hidden").removeClass(
        "contrib-row-hidden"
      );
    } else {
      $("tr.contrib-toggle-row").addClass("contrib-row-hidden");
    }

    setToggleText(rowsToggled ? CONSTANTS.SHOW_LESS : CONSTANTS.SHOW_MORE);
  };

  return (
    <div className="disaggregation-viewer">
      <Tabs defaultActiveKey="epsilon" className="pivot-tabs">
        <Tab eventKey="epsilon" title={CONSTANTS.EPSILON}>
          {disaggComputeClick === null && (
            <GuideMessage
              header={CONSTANTS.DISAGGREGATION}
              body={CONSTANTS.DISAGGREGATION_GUIDE_MSG_PLOT}
              instruction={CONSTANTS.DISAGGREGATION_INSTRUCTION_PLOT}
            />
          )}

          {showSpinnerDisaggEpsilon === true &&
            disaggComputeClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {disaggComputeClick !== null &&
            showSpinnerDisaggEpsilon === false &&
            showErrorMessage.isError === true && (
              <ErrorMessage errorCode={showErrorMessage.errorCode} />
            )}

          {showSpinnerDisaggEpsilon === false &&
            showPlotDisaggEpsilon === true &&
            showErrorMessage.isError === false && (
              <Fragment>
                <img
                  className="img-fluid rounded mx-auto d-block"
                  src={`data:image/png;base64,${disaggPlotData.eps}`}
                  alt={CONSTANTS.EPSILON_DISAGG_PLOT_ALT}
                />
              </Fragment>
            )}
        </Tab>

        <Tab eventKey="fault" title={CONSTANTS.FAULT_DISTRIBUTED_SEISMICITY}>
          {disaggComputeClick === null && (
            <GuideMessage
              header={CONSTANTS.DISAGGREGATION}
              body={CONSTANTS.DISAGGREGATION_GUIDE_MSG_PLOT}
              instruction={CONSTANTS.DISAGGREGATION_INSTRUCTION_PLOT}
            />
          )}

          {showSpinnerDisaggFault === true &&
            disaggComputeClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {disaggComputeClick !== null &&
            showSpinnerDisaggFault === false &&
            showErrorMessage.isError === true && (
              <ErrorMessage errorCode={showErrorMessage.errorCode} />
            )}

          {showSpinnerDisaggFault === false &&
            showPlotDisaggFault === true &&
            showErrorMessage.isError === false && (
              <Fragment>
                <img
                  className="img-fluid rounded mx-auto d-block"
                  src={`data:image/png;base64,${disaggPlotData.src}`}
                  alt={CONSTANTS.SOURCE_DISAGG_PLOT_ALT}
                />
              </Fragment>
            )}
        </Tab>

        <Tab eventKey="contributions" title={CONSTANTS.SOURCE_CONTRIBUTIONS}>
          {disaggComputeClick === null && (
            <GuideMessage
              header={CONSTANTS.DISAGGREGATION}
              body={CONSTANTS.DISAGGREGATION_GUIDE_MSG_TABLE}
              instruction={CONSTANTS.DISAGGREGATION_INSTRUCTION_TABLE}
            />
          )}

          {showSpinnerContribTable === true &&
            disaggComputeClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {disaggComputeClick !== null &&
            showSpinnerContribTable === false &&
            showErrorMessage.isError === true && (
              <ErrorMessage errorCode={showErrorMessage.errorCode} />
            )}

          {showSpinnerContribTable === false &&
            showContribTable === true &&
            showErrorMessage.isError === false && (
              <Fragment>
                <ContributionTable
                  meanData={disaggMeanData}
                  contributionData={disaggContributionData}
                />
                <button
                  className="btn btn-info hazard-disagg-contrib-button"
                  onClick={() => rowToggle()}
                >
                  {toggleText}
                </button>
              </Fragment>
            )}
        </Tab>
      </Tabs>
      <DownloadButton
        disabled={!showContribTable}
        downloadURL={CONSTANTS.CORE_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT}
        downloadToken={{
          disagg_token: downloadToken,
        }}
        fileName={`Disaggregation_${filteredSelectedIM}_RP_${(
          1 / disaggAnnualProb
        ).toFixed(0)}.zip`}
      />
    </div>
  );
};

export default HazardViewerDisaggregation;
