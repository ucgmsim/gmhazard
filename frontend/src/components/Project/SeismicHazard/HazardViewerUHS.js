import React, { Fragment, useEffect, useState, useContext } from "react";

import { Tabs, Tab } from "react-bootstrap";
import Select from "react-select";

import * as CONSTANTS from "constants/Constants";
import { GlobalContext } from "context";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import {
  UHSPlot,
  UHSBranchPlot,
  LoadingSpinner,
  DownloadButton,
  GuideMessage,
  ErrorMessage,
} from "components/common";
import { getProjectUHS } from "apis/ProjectAPI";
import { handleErrors, APIQueryBuilder, createStationID } from "utils/Utils";

const HazardViewerUHS = () => {
  const { isAuthenticated, getTokenSilently } = useAuth0();

  const {
    projectId,
    projectLocation,
    projectVS30,
    projectZ1p0,
    projectZ2p5,
    projectLocationCode,
    projectSelectedUHSRP,
    setProjectSelectedUHSRP,
    projectSelectedIMComponent,
    projectUHSGetClick,
    setProjectUHSGetClick,
    projectSiteSelectionGetClick,
  } = useContext(GlobalContext);

  // For UHS data fetcher
  const [showSpinnerUHS, setShowSpinnerUHS] = useState(false);
  const [showPlotUHS, setShowPlotUHS] = useState(false);
  const [showErrorMessage, setShowErrorMessage] = useState({
    isError: false,
    errorCode: null,
  });

  // For UHS Plots
  const [uhsData, setUHSData] = useState(null);
  const [uhsBranchData, setUHSBranchData] = useState(null);
  const [uhsNZS1170p5Data, setUHSNZS1170p5Data] = useState(null);
  const [extraInfo, setExtraInfo] = useState({});

  // For Download Data button
  const [downloadToken, setDownloadToken] = useState("");

  // For Select, dropdown
  const [localSelectedRP, setLocalSelectedRP] = useState(null);
  const [uhsRPOptions, setUHSRPOptions] = useState([]);

  // Reset tabs if users click Get button from Site Selection
  useEffect(() => {
    if (projectSiteSelectionGetClick !== null) {
      setShowPlotUHS(false);
      setShowSpinnerUHS(false);
      setProjectSelectedUHSRP([]);
      setProjectUHSGetClick(null);
    }
  }, [projectSiteSelectionGetClick]);

  // Setting variables for the selected RP and RP options
  useEffect(() => {
    if (uhsData !== null) {
      const sortedSelectedRP = getSelectedRP()
        .sort((a, b) => a - b)
        .map((option) => ({
          value: 1 / Number(option),
          label: option,
        }));

      setLocalSelectedRP(sortedSelectedRP[0]);
      setUHSRPOptions(sortedSelectedRP);
    }
  }, [uhsData]);

  // Get UHS data to plot
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    if (projectUHSGetClick !== null) {
      setShowPlotUHS(false);
      setShowSpinnerUHS(true);
      setShowErrorMessage({ isError: false, errorCode: null });

      let token = null;
      const queryString = APIQueryBuilder({
        project_id: projectId["value"],
        station_id: createStationID(
          projectLocationCode[projectLocation],
          projectVS30,
          projectZ1p0,
          projectZ2p5
        ),
        rp: `${getSelectedRP().join(",")}`,
        im_component:
          projectSelectedIMComponent === null
            ? "RotD50"
            : projectSelectedIMComponent,
      });

      (async () => {
        if (isAuthenticated) token = await getTokenSilently();

        getProjectUHS(queryString, signal, token)
          .then(handleErrors)
          .then(async (response) => {
            const responseData = await response.json();

            updateUHSData(responseData);
          })
          .catch((error) => catchError(error));
      })();
    }

    return () => {
      abortController.abort();
    };
  }, [projectUHSGetClick]);

  // Create an array of selected RPs
  const getSelectedRP = () => projectSelectedUHSRP.map((RP) => RP.value);

  /* 
    Filter the UHSData with selected RPs to display
    only the selected RPs in plots
  */
  const filterUHSData = (UHSData, selectedRP) => {
    const filtered = Object.keys(UHSData)
      .filter((key) => selectedRP.includes(1 / Number(key)))
      .reduce((obj, key) => {
        obj[key] = UHSData[key];
        return obj;
      }, {});

    return filtered;
  };

  const updateUHSData = (uhsData) => {
    setUHSData(filterUHSData(uhsData["uhs_results"], getSelectedRP()));
    setUHSNZS1170p5Data(
      filterUHSData(uhsData["nzs1170p5_uhs_df"], getSelectedRP())
    );
    setUHSBranchData(uhsData["branch_uhs_results"]);
    setDownloadToken(uhsData["download_token"]);
    setExtraInfo({
      from: "project",
      id: projectId,
      location: projectLocation,
      vs30: projectVS30,
      selectedRPs: getSelectedRP(),
    });

    setShowSpinnerUHS(false);
    setShowPlotUHS(true);
  };

  const catchError = (error) => {
    if (error.name !== "AbortError") {
      setShowSpinnerUHS(false);
      setShowErrorMessage({ isError: true, errorCode: error });
    }
    console.log(error);
  };

  return (
    <div className="uhs-viewer">
      <Tabs defaultActiveKey="allRP" className="pivot-tabs">
        <Tab eventKey="allRP" title="Selected Return Periods">
          <div className="tab-content">
            {projectUHSGetClick === null && (
              <GuideMessage
                header={CONSTANTS.UNIFORM_HAZARD_SPECTRUM}
                body={CONSTANTS.UNIFORM_HAZARD_SPECTRUM_MSG}
                instruction={
                  CONSTANTS.PROJECT_UNIFORM_HAZARD_SPECTRUM_INSTRUCTION
                }
              />
            )}

            {showSpinnerUHS === true &&
              projectUHSGetClick !== null &&
              showErrorMessage.isError === false && <LoadingSpinner />}

            {projectUHSGetClick !== null &&
              showSpinnerUHS === false &&
              showErrorMessage.isError === true && (
                <ErrorMessage errorCode={showErrorMessage.errorCode} />
              )}

            {showSpinnerUHS === false &&
              showPlotUHS === true &&
              showErrorMessage.isError === false && (
                <Fragment>
                  <UHSPlot
                    from={"projects"}
                    uhsData={uhsData}
                    nzs1170p5Data={uhsNZS1170p5Data}
                    extra={extraInfo}
                  />
                </Fragment>
              )}
          </div>
        </Tab>
        <Tab eventKey="specificRP" title="Return Period branches">
          <div className="tab-content">
            {projectUHSGetClick === null && (
              <GuideMessage
                header={CONSTANTS.UNIFORM_HAZARD_SPECTRUM}
                body={CONSTANTS.UNIFORM_HAZARD_SPECTRUM_MSG}
                instruction={
                  CONSTANTS.PROJECT_UNIFORM_HAZARD_SPECTRUM_INSTRUCTION
                }
              />
            )}

            {showSpinnerUHS === true &&
              projectUHSGetClick !== null &&
              showErrorMessage.isError === false && <LoadingSpinner />}

            {projectUHSGetClick !== null &&
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
                      id={"project-rp"}
                      value={localSelectedRP}
                      onChange={(rpOption) => setLocalSelectedRP(rpOption)}
                      options={uhsRPOptions}
                      isDisabled={uhsRPOptions.length === 0}
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
                    from={"projects"}
                    uhsData={uhsData[localSelectedRP["value"]]}
                    uhsBranchData={
                      uhsBranchData === undefined || uhsBranchData === null
                        ? null
                        : uhsBranchData[localSelectedRP["value"]]
                    }
                    nzs1170p5Data={uhsNZS1170p5Data[localSelectedRP["value"]]}
                    rp={localSelectedRP["label"]}
                    extra={extraInfo}
                  />
                </Fragment>
              )}
          </div>
        </Tab>
      </Tabs>

      <DownloadButton
        disabled={!showPlotUHS}
        downloadURL={CONSTANTS.PROJECT_API_HAZARD_UHS_DOWNLOAD_ENDPOINT}
        downloadToken={{
          uhs_token: downloadToken,
        }}
        fileName="Uniform_Hazard_Spectrum.zip"
      />
    </div>
  );
};

export default HazardViewerUHS;
