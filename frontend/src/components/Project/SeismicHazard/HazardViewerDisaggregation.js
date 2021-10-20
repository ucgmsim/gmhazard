import React, { Fragment, useState, useEffect, useContext } from "react";

import $ from "jquery";
import { Tabs, Tab } from "react-bootstrap";

import { useAuth0 } from "components/common/ReactAuth0SPA";
import * as CONSTANTS from "constants/Constants";
import { GlobalContext } from "context";

import {
  LoadingSpinner,
  DownloadButton,
  GuideMessage,
  ErrorMessage,
  ContributionTable,
} from "components/common";
import {
  APIQueryBuilder,
  handleErrors,
  combineIMwithPeriod,
  createStationID,
} from "utils/Utils";

const HazadViewerDisaggregation = () => {
  const { isAuthenticated, getTokenSilently } = useAuth0();

  const {
    projectDisaggGetClick,
    setProjectDisaggGetClick,
    projectId,
    projectVS30,
    projectZ1p0,
    projectZ2p5,
    projectLocation,
    projectLocationCode,
    projectSelectedIM,
    projectSelectedIMPeriod,
    projectSelectedIMComponent,
    projectSelectedDisagRP,
    setProjectSelectedDisagRP,
  } = useContext(GlobalContext);

  // For data fetcher
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
  const [toggleText, setToggleText] = useState("Show More...");

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

  // Reset tabs if users change project id, project vs30, project location or project im
  useEffect(() => {
    setShowSpinnerDisaggEpsilon(false);
    setShowPlotDisaggEpsilon(false);

    setShowSpinnerDisaggFault(false);
    setShowPlotDisaggFault(false);

    setShowContribTable(false);
    setShowSpinnerContribTable(false);

    setProjectDisaggGetClick(null);

    setProjectSelectedDisagRP(null);
  }, [projectId, projectVS30, projectLocation]);

  // Get hazard disagg data
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getDisaggData = async () => {
      if (projectDisaggGetClick !== null) {
        try {
          const token = await getTokenSilently();
          setShowErrorMessage({ isError: false, errorCode: null });

          setShowSpinnerDisaggEpsilon(true);

          setShowSpinnerDisaggFault(true);

          setShowPlotDisaggEpsilon(false);
          setShowPlotDisaggFault(false);

          setShowContribTable(false);
          setShowSpinnerContribTable(true);

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.PROJECT_API_HAZARD_DISAGG_ENDPOINT +
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
                rp: projectSelectedDisagRP,
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
                  "Distributed Seismicity";
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

    const getPublicDisaggData = async () => {
      if (projectDisaggGetClick !== null) {
        try {
          const token = await getTokenSilently();
          setShowErrorMessage({ isError: false, errorCode: null });

          setShowSpinnerDisaggEpsilon(true);

          setShowSpinnerDisaggFault(true);

          setShowPlotDisaggEpsilon(false);
          setShowPlotDisaggFault(false);

          setShowContribTable(false);
          setShowSpinnerContribTable(true);

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.PUBLIC_API_HAZARD_DISAGG_ENDPOINT +
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
                rp: projectSelectedDisagRP,
                im_component: projectSelectedIMComponent,
              }),
            {
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
                  "Distributed Seismicity";
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

    if (isAuthenticated) {
      getDisaggData();
    } else {
      getPublicDisaggData();
    }

    return () => {
      abortController.abort();
    };
  }, [projectDisaggGetClick]);

  const rowToggle = () => {
    setRowsToggled(!rowsToggled);

    if (rowsToggled) {
      $("tr.contrib-toggle-row.contrib-row-hidden").removeClass(
        "contrib-row-hidden"
      );
      $("tr.contrib-ellipsis td").addClass("hidden");
    } else {
      $("tr.contrib-toggle-row").addClass("contrib-row-hidden");
      $("tr.contrib-ellipsis td.hidden").removeClass("hidden");
    }

    setToggleText(rowsToggled ? "Show Less..." : "Show More...");
  };

  return (
    <div className="disaggregation-viewer">
      <Tabs defaultActiveKey="epsilon" className="pivot-tabs">
        <Tab eventKey="epsilon" title="Epsilon">
          {projectDisaggGetClick === null && (
            <GuideMessage
              header={CONSTANTS.DISAGGREGATION}
              body={CONSTANTS.DISAGGREGATION_GUIDE_MSG_PLOT}
              instruction={CONSTANTS.PROJECT_DISAGG_INSTRUCTION_PLOT}
            />
          )}

          {showSpinnerDisaggEpsilon === true &&
            projectDisaggGetClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {projectDisaggGetClick !== null &&
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
                  alt="Epsilon disagg plot"
                />
              </Fragment>
            )}
        </Tab>

        <Tab eventKey="fault" title="Fault/distributed seismicity">
          {projectDisaggGetClick === null && (
            <GuideMessage
              header={CONSTANTS.DISAGGREGATION}
              body={CONSTANTS.DISAGGREGATION_GUIDE_MSG_PLOT}
              instruction={CONSTANTS.PROJECT_DISAGG_INSTRUCTION_PLOT}
            />
          )}

          {showSpinnerDisaggFault === true &&
            projectDisaggGetClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {projectDisaggGetClick !== null &&
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
                  alt="Source disagg plot"
                />
              </Fragment>
            )}
        </Tab>

        <Tab eventKey="contributions" title="Source contributions">
          {projectDisaggGetClick === null && (
            <GuideMessage
              header={CONSTANTS.DISAGGREGATION}
              body={CONSTANTS.DISAGGREGATION_GUIDE_MSG_TABLE}
              instruction={CONSTANTS.PROJECT_DISAGG_INSTRUCTION_TABLE}
            />
          )}

          {showSpinnerContribTable === true &&
            projectDisaggGetClick !== null &&
            showErrorMessage.isError === false && <LoadingSpinner />}

          {projectDisaggGetClick !== null &&
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
        downloadURL={CONSTANTS.PROJECT_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT}
        downloadToken={{
          disagg_token: downloadToken,
        }}
        fileName={`Projects_Disaggregation_${filteredSelectedIM}_RP_${projectSelectedDisagRP}.zip`}
      />
    </div>
  );
};

export default HazadViewerDisaggregation;
