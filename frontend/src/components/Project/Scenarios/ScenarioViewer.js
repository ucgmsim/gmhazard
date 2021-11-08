import React, { Fragment, useContext, useState, useEffect } from "react";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import {
  LoadingSpinner,
  DownloadButton,
  GuideMessage,
  ErrorMessage,
  ScenarioPlot,
} from "components/common";
import { getProjectScenario } from "apis/ProjectAPI";
import { getPublicProjectScenario } from "apis/PublicProjectAPI";
import { handleErrors, APIQueryBuilder, createStationID } from "utils/Utils";

import "assets/style/ScenarioViewer.css";

const ScenarioViewer = () => {
  const { isAuthenticated, getTokenSilently } = useAuth0();

  const {
    projectId,
    projectLocation,
    projectLocationCode,
    projectVS30,
    projectZ1p0,
    projectZ2p5,
    projectScenarioGetClick,
    setProjectScenarioGetClick,
    projectScenarioData,
    setProjectScenarioData,
    projectScenarioSelectedRuptures,
    projectSelectedScenarioIMComponent,
  } = useContext(GlobalContext);

  // For fetching Scenario data
  const [isLoading, setIsLoading] = useState(false);
  const [showErrorMessage, setShowErrorMessage] = useState({
    isError: false,
    errorCode: null,
  });

  // For Scenario Plots
  const [extraInfo, setExtraInfo] = useState({});

  // For Download data button
  const [downloadToken, setDownloadToken] = useState("");

  // Get Scenario data
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    if (
      projectScenarioGetClick !== null &&
      projectSelectedScenarioIMComponent !== null
    ) {
      setIsLoading(true);
      setProjectScenarioData(null);
      setShowErrorMessage({ isError: false, errorCode: null });

      let queryString = APIQueryBuilder({
        project_id: projectId["value"],
        station_id: createStationID(
          projectLocationCode[projectLocation],
          projectVS30,
          projectZ1p0,
          projectZ2p5
        ),
        im_component: projectSelectedScenarioIMComponent,
      });

      if (isAuthenticated) {
        (async () => {
          const token = await getTokenSilently();

          getProjectScenario(queryString, token, signal)
            .then(handleErrors)
            .then(async (response) => {
              const responseData = await response.json();
              updateScenarioData(responseData);
            })
            .catch((error) => catchError(error));
        })();
      } else {
        getPublicProjectScenario(queryString, signal)
          .then(handleErrors)
          .then(async (response) => {
            const responseData = await response.json();
            updateScenarioData(responseData);
          })
          .catch((error) => catchError(error));
      }
    }

    return () => {
      abortController.abort();
    };
  }, [projectScenarioGetClick]);

  // Reset tabs if users change Project ID, Vs30, Z values or Location
  useEffect(() => {
    setProjectScenarioGetClick(null);
    setShowErrorMessage({ isError: false, errorCode: null });
  }, [projectId, projectVS30, projectLocation, projectZ1p0, projectZ2p5]);

  const updateScenarioData = (data) => {
    setProjectScenarioData(data);
    setDownloadToken(data["download_token"]);

    setExtraInfo({
      from: "project",
      id: projectId["value"],
      location: projectLocation,
      vs30: projectVS30,
    });

    setIsLoading(false);
  };

  const catchError = (error) => {
    if (error.name !== "AbortError") {
      setIsLoading(false);
      setShowErrorMessage({ isError: true, errorCode: error });
    }
    console.log(error);
  };

  return (
    <div className="scenario-viewer">
      {projectScenarioGetClick === null && (
        <GuideMessage
          header={CONSTANTS.SCENARIOS}
          body={CONSTANTS.SCENARIO_VIEWER_GUIDE_MSG}
          instruction={CONSTANTS.PROJECT_SCENARIO_VIEWER_GUIDE_INSTRUCTION}
        />
      )}
      {projectScenarioGetClick !== null &&
        isLoading === true &&
        showErrorMessage.isError === false && <LoadingSpinner />}
      {isLoading === false && showErrorMessage.isError === true && (
        <ErrorMessage errorCode={showErrorMessage.errorCode} />
      )}
      {isLoading === false &&
        projectScenarioData !== null &&
        showErrorMessage.isError === false && (
          <Fragment>
            <ScenarioPlot
              scenarioData={projectScenarioData}
              scenarioSelectedRuptures={projectScenarioSelectedRuptures}
              extra={extraInfo}
            />
            <DownloadButton
              downloadURL={CONSTANTS.PROJECT_API_SCENARIOS_DOWNLOAD_ENDPOINT}
              downloadToken={{
                scenario_token: downloadToken,
              }}
              fileName="Scenarios.zip"
            />
          </Fragment>
        )}
    </div>
  );
};

export default ScenarioViewer;
