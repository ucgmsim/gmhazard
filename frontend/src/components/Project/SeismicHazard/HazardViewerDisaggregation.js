import React, { Fragment, useState, useEffect, useContext } from "react";

import $ from "jquery";
import Select from "react-select";
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
import { getProjectDisaggregation } from "apis/ProjectAPI";
import {
  APIQueryBuilder,
  handleErrors,
  combineIMwithPeriod,
  createStationID,
} from "utils/Utils";

const HazardViewerDisaggregation = () => {
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
    projectSiteSelectionGetClick,
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
  const [toggleText, setToggleText] = useState(CONSTANTS.SHOW_MORE);

  // For download data button
  const [downloadToken, setDownloadToken] = useState("");
  const [filteredSelectedIM, setFilteredSelectedIM] = useState("");

  // For Epsilon and Fault/distributed seismicity images
  const [disaggPlotData, setDisaggPlotData] = useState({
    eps: null,
    src: null,
  });

  // For Select, dropdown
  const [localSelectedRP, setLocalSelectedRP] = useState(null);
  const [disaggRPOptions, setDisaggRPOptions] = useState([]);

  // Reset tabs if users click Get button from Site Selection
  useEffect(() => {
    if (projectSiteSelectionGetClick !== null) {
      setShowSpinnerDisaggEpsilon(false);
      setShowPlotDisaggEpsilon(false);

      setShowSpinnerDisaggFault(false);
      setShowPlotDisaggFault(false);

      setShowContribTable(false);
      setShowSpinnerContribTable(false);

      setProjectDisaggGetClick(null);

      setProjectSelectedDisagRP(null);

      setRowsToggled(true);
      setToggleText(CONSTANTS.SHOW_MORE);
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

  // Get hazard disagg data
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    if (projectDisaggGetClick !== null) {
      setShowErrorMessage({ isError: false, errorCode: null });

      setShowSpinnerDisaggEpsilon(true);

      setShowSpinnerDisaggFault(true);

      setShowPlotDisaggEpsilon(false);
      setShowPlotDisaggFault(false);

      setShowContribTable(false);
      setShowSpinnerContribTable(true);

      setRowsToggled(true);
      setToggleText(CONSTANTS.SHOW_MORE);

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

        getProjectDisaggregation(queryString, signal, token)
          .then(handleErrors)
          .then(async (response) => {
            const responseData = await response.json();
            updateDisaggData(responseData);
          })
          .catch((error) => catchError(error));
      })();
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
    } else {
      $("tr.contrib-toggle-row").addClass("contrib-row-hidden");
    }

    setToggleText(rowsToggled ? CONSTANTS.SHOW_LESS : CONSTANTS.SHOW_MORE);
  };

  /* 
    Filter the disaggData with selected RPs to display
    only the selected RPs in plots
  */
  const filterDisaggData = (disaggData, selectedRP) => {
    const filtered = Object.keys(disaggData)
      .filter((key) => selectedRP.includes(Number(key)))
      .reduce((obj, key) => {
        obj[key] = disaggData[key];
        return obj;
      }, {});

    return filtered;
  };

  const updateDisaggData = (disaggData) => {
    const selectedRPs = projectSelectedDisagRP.map((RP) => RP.value);

    const sortedSelectedRPs = selectedRPs
      .sort((a, b) => a - b)
      .map((rp) => ({
        value: rp,
        label: Number((1 / Number(rp)).toFixed(4)),
      }));
    setDisaggRPOptions(sortedSelectedRPs);
    setLocalSelectedRP(sortedSelectedRPs[0]);
    setDownloadToken(disaggData["download_token"]);

    const srcDisaggPlot = filterDisaggData(
      disaggData["gmt_plot_src"],
      selectedRPs
    );
    const epsDisaggPlot = filterDisaggData(
      disaggData["gmt_plot_eps"],
      selectedRPs
    );

    setDisaggPlotData({
      src: srcDisaggPlot,
      eps: epsDisaggPlot,
    });

    const disaggTotalData = filterDisaggData(
      disaggData["disagg_data"],
      selectedRPs
    );

    let filteredTotalContribution = {};
    for (const item in disaggTotalData) {
      filteredTotalContribution[item] =
        disaggTotalData[item]["total_contribution"];
    }
    const extraInfo = filterDisaggData(disaggData["extra_info"], selectedRPs);

    // Polish total contribution data
    let data = {};
    for (const RP in filteredTotalContribution) {
      extraInfo[RP].rupture_name["distributed_seismicity"] =
        CONSTANTS.DISTRIBUTED_SEISMICITY;

      const unsortedData = Array.from(
        Object.keys(filteredTotalContribution[RP]),
        (key) => {
          return [
            key,
            extraInfo[RP].rupture_name[key],
            filteredTotalContribution[RP][key],
            extraInfo[RP].annual_rec_prob[key],
            extraInfo[RP].magnitude[key],
            extraInfo[RP].rrup[key],
          ];
        }
      );

      data[RP] = unsortedData.sort((a, b) => b[2] - a[2]);
    }

    setDisaggMeanData(disaggTotalData);
    setDisaggContributionData(data);

    setShowSpinnerDisaggEpsilon(false);
    setShowSpinnerDisaggFault(false);
    setShowSpinnerContribTable(false);

    setShowPlotDisaggEpsilon(true);
    setShowPlotDisaggFault(true);

    setShowContribTable(true);
  };

  const catchError = (error) => {
    if (error.name !== "AbortError") {
      setShowSpinnerContribTable(false);
      setShowSpinnerDisaggEpsilon(false);
      setShowSpinnerDisaggFault(false);

      setShowErrorMessage({ isError: true, errorCode: error });
    }
    console.log(error);
  };

  return (
    <div className="disaggregation-viewer">
      <Tabs defaultActiveKey="epsilon" className="pivot-tabs">
        <Tab eventKey="epsilon" title={CONSTANTS.EPSILON}>
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
                <Select
                  value={localSelectedRP}
                  onChange={(rpOption) => setLocalSelectedRP(rpOption)}
                  options={disaggRPOptions}
                  isDisabled={disaggRPOptions.length === 0}
                  menuPlacement="auto"
                />
                <img
                  className="img-fluid rounded mx-auto d-block"
                  src={`data:image/png;base64,${
                    disaggPlotData.eps[localSelectedRP["value"]]
                  }`}
                  alt={CONSTANTS.EPSILON_DISAGG_PLOT_ALT}
                />
              </Fragment>
            )}
        </Tab>

        <Tab eventKey="fault" title={CONSTANTS.FAULT_DISTRIBUTED_SEISMICITY}>
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
                <Select
                  value={localSelectedRP}
                  onChange={(rpOption) => setLocalSelectedRP(rpOption)}
                  options={disaggRPOptions}
                  isDisabled={disaggRPOptions.length === 0}
                  menuPlacement="auto"
                />
                <img
                  className="img-fluid rounded mx-auto d-block"
                  src={`data:image/png;base64,${
                    disaggPlotData.src[localSelectedRP["value"]]
                  }`}
                  alt={CONSTANTS.SOURCE_DISAGG_PLOT_ALT}
                />
              </Fragment>
            )}
        </Tab>

        <Tab eventKey="contributions" title={CONSTANTS.SOURCE_CONTRIBUTIONS}>
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
                <Select
                  value={localSelectedRP}
                  onChange={(rpOption) => setLocalSelectedRP(rpOption)}
                  options={disaggRPOptions}
                  isDisabled={disaggRPOptions.length === 0}
                  menuPlacement="auto"
                />
                <ContributionTable
                  meanData={disaggMeanData[localSelectedRP["value"]]}
                  contributionData={
                    disaggContributionData[localSelectedRP["value"]]
                  }
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
        fileName={`Projects_Disaggregation_${filteredSelectedIM}.zip`}
      />
    </div>
  );
};

export default HazardViewerDisaggregation;
