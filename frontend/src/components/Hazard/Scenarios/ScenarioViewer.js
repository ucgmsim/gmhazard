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
import { handleErrors, APIQueryBuilder } from "utils/Utils";

import "assets/style/ScenarioViewer.css";

const ScenarioViewer = () => {
  const { getTokenSilently } = useAuth0();

  const {
    selectedEnsemble,
    station,
    vs30,
    defaultVS30,
    siteSelectionLat,
    siteSelectionLng,
    ScenarioComputeClick,
    setScenarioComputeClick,
    scenarioData,
    setScenarioData,
    scenarioSelectedRuptures,
    selectedScenarioIMComponent,
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

    const computeEnsembleScenario = async () => {
      if (
        ScenarioComputeClick !== null &&
        selectedScenarioIMComponent !== null
      ) {
        try {
          const token = await getTokenSilently();

          setIsLoading(true);
          setScenarioData(null);
          setShowErrorMessage({ isError: false, errorCode: null });

          let queryString = APIQueryBuilder({
            ensemble_id: selectedEnsemble,
            station: station,
            im_component: selectedScenarioIMComponent,
          });
          if (vs30 !== defaultVS30) {
            queryString += `&vs30=${vs30}`;
          }

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_SCENARIOS_ENDPOINT +
              queryString,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          )
            .then(handleErrors)
            .then(async (scenarioResponse) => {
              const responseData = await scenarioResponse.json();
              setScenarioData(responseData);
              setDownloadToken(responseData["download_token"]);

              setExtraInfo({
                from: "hazard",
                lat: siteSelectionLat,
                lng: siteSelectionLng,
              });

              setIsLoading(false);
            })
            .catch((error) => {
              if (error.name !== "AbortError") {
                setIsLoading(false);
                setShowErrorMessage({ isError: true, errorCode: error });
              }
              console.log(error);
            });
        } catch (error) {
          setIsLoading(false);
          setShowErrorMessage({ isError: false, errorCode: error });
        }
      }
    };

    computeEnsembleScenario();

    return () => {
      abortController.abort();
    };
  }, [ScenarioComputeClick]);

  // Reset tabs if users change Station
  useEffect(() => {
    setScenarioComputeClick(null);
    setShowErrorMessage({ isError: false, errorCode: null });
  }, [station]);

  return (
    <div className="scenario-viewer">
      {ScenarioComputeClick === null && (
        <GuideMessage
          header={CONSTANTS.SCENARIOS}
          body={CONSTANTS.SCENARIO_VIEWER_GUIDE_MSG}
          instruction={CONSTANTS.SCENARIO_VIEWER_GUIDE_INSTRUCTION}
        />
      )}
      {ScenarioComputeClick !== null &&
        isLoading === true &&
        showErrorMessage.isError === false && <LoadingSpinner />}
      {isLoading === false && showErrorMessage.isError === true && (
        <ErrorMessage errorCode={showErrorMessage.errorCode} />
      )}
      {isLoading === false &&
        scenarioData !== null &&
        showErrorMessage.isError === false && (
          <Fragment>
            <ScenarioPlot
              scenarioData={scenarioData}
              scenarioSelectedRuptures={scenarioSelectedRuptures}
              extra={extraInfo}
            />
            <DownloadButton
              downloadURL={CONSTANTS.CORE_API_SCENARIOS_DOWNLOAD_ENDPOINT}
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
