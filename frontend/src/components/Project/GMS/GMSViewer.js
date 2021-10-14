import React, { Fragment, useContext, useEffect, useState } from "react";

import { Tabs, Tab } from "react-bootstrap";
import Select from "react-select";
import dompurify from "dompurify";

import { GlobalContext } from "context";
import { useAuth0 } from "components/common/ReactAuth0SPA";
import * as CONSTANTS from "constants/Constants";

import {
  LoadingSpinner,
  DownloadButton,
  GuideMessage,
  ErrorMessage,
  GMSDisaggDistributionPlot,
  GMSIMDistributionsPlot,
  GMSSpectraPlot,
  GMSMwRrupPlot,
  GMSCausalParamPlot,
} from "components/common";
import {
  handleErrors,
  GMSIMLabelConverter,
  APIQueryBuilder,
  sortIMs,
  createBoundsCoords,
  createStationID,
} from "utils/Utils";
import { calculateGMSSpectra } from "utils/calculations/CalculateGMSSpectra";

const GmsViewer = () => {
  const { getTokenSilently } = useAuth0();

  const sanitizer = dompurify.sanitize;

  const {
    projectId,
    projectLocation,
    projectVS30,
    projectZ1p0,
    projectZ2p5,
    projectLocationCode,
    projectGMSGetClick,
    setProjectGMSGetClick,
    projectGMSIDs,
    projectGMSConditionIM,
    projectGMSSelectedIMPeriod,
    projectGMSExceedance,
    projectGMSIMVector,
    projectGMSNumGMs,
  } = useContext(GlobalContext);

  // For fetching GMS data
  const [isLoading, setIsLoading] = useState(false);
  const [showErrorMessage, setShowErrorMessage] = useState({
    isError: false,
    errorCode: null,
  });

  // For GMS Plots
  const [computedGMS, setComputedGMS] = useState(null);
  const [GMSSpectraData, setGMSSpectraData] = useState([]);
  const [causalParamBounds, setCausalParamBounds] = useState({});
  const [contributionDFData, setContributionDFData] = useState({});
  const [mwRrupBounds, setMwRrupBounds] = useState({});
  const [disaggMeanValues, setDisaggMeanValues] = useState({});

  // For Select, dropdown
  const [specifiedIM, setSpecifiedIM] = useState([]);
  const [localIMVectors, setLocalIMVectors] = useState([]);
  const [IMVectors, setIMVectors] = useState([]);
  const [specifiedMetadata, setSpecifiedMetadata] = useState([]);
  const [localmetadata, setLocalmetadata] = useState([]);

  // For Download data button
  const [downloadToken, setDownloadToken] = useState("");

  // Reset the state to prevent auto-trigger
  // E.g. change tab between Projects and Hazard Analyis
  useEffect(() => {
    setProjectGMSGetClick(null);
  }, []);

  // Reset tabs if users change project id, project location or project vs30
  useEffect(() => {
    setIsLoading(false);
    setShowErrorMessage({
      isError: false,
      errorCode: null,
    });
    setComputedGMS(null);
    setProjectGMSGetClick(null);
  }, [projectId, projectLocation, projectVS30]);

  // Create IM array of objects for IM Distributions plot (react-select dropdown)
  useEffect(() => {
    if (IMVectors.length > 0) {
      let localIMs = sortIMs(IMVectors).map((IM) => ({
        value: IM,
        label: GMSIMLabelConverter(IM),
      }));
      // Insert spectra, disagg distribution plots before any IM
      localIMs.splice(0, 0, {
        value: "spectra",
        label: "Pseudo acceleration response spectra",
      });

      setLocalIMVectors(localIMs);
      // Set the first IM as a default selected IM for the plot
      setSpecifiedIM(localIMs[1]);
    }
  }, [IMVectors]);

  // Create Metadata array of objects for Causal Parameters plot (react-select dropdown)
  useEffect(() => {
    if (computedGMS !== null) {
      // Response contains multiple metadata that we don't need
      const metadata = ["mag", "rrup", "sf", "vs30"];
      let tempmetadata = metadata.map((metadata) => ({
        value: metadata,
        label: `${CONSTANTS.GMS_LABELS[metadata]} distribution`,
      }));

      tempmetadata.splice(0, 0, {
        value: "mwrrupplot",
        label: `Magnitude and rupture distance (Mw-R${"rup".sub()}) distribution`,
      });
      setLocalmetadata(tempmetadata);

      // Set the first Metadata as a default selected metadata for the plot
      setSpecifiedMetadata(tempmetadata[1]);
    }
  }, [computedGMS]);

  /*
    Send a request to get the following data:
    1. Default Causal Parameters
    2. Computed GMS Data
    when Get button is clicked
  */
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getGMSData = async () => {
      if (projectGMSGetClick !== null) {
        try {
          setShowErrorMessage({ isError: false, errorCode: null });
          setIsLoading(true);

          const token = await getTokenSilently();

          const gms_id = projectGMSIDs.find((GMSId) => {
            return (
              GMSId.includes(
                `${projectGMSConditionIM}_${projectGMSSelectedIMPeriod.replace(
                  ".",
                  "p"
                )}`
              ) &&
              GMSId.includes(
                projectGMSExceedance.toString().replace(".", "p")
              ) &&
              GMSId.includes(
                [
                  ...new Set(
                    projectGMSIMVector.replace(/[0-9]/g, "").split(", ")
                  ),
                ].join("_")
              )
            );
          });

          let queryString = APIQueryBuilder({
            project_id: projectId["value"],
            station_id: createStationID(
              projectLocationCode[projectLocation],
              projectVS30,
              projectZ1p0,
              projectZ2p5
            ),
            gms_id: gms_id,
          });

          await Promise.all([
            fetch(
              CONSTANTS.INTERMEDIATE_API_URL +
                CONSTANTS.PROJECT_API_GMS_ENDPOINT +
                queryString,
              {
                headers: {
                  Authorization: `Bearer ${token}`,
                },
                signal: signal,
              }
            ),
            fetch(
              CONSTANTS.INTERMEDIATE_API_URL +
                CONSTANTS.PROJECT_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT +
                queryString,
              {
                headers: {
                  Authorization: `Bearer ${token}`,
                },
                signal: signal,
              }
            ),
          ])
            .then(handleErrors)
            .then(async ([computedGMS, defaultCausalParams]) => {
              const GMSData = await computedGMS.json();
              const defaultParams = await defaultCausalParams.json();

              setComputedGMS(GMSData);
              setGMSSpectraData(
                calculateGMSSpectra(GMSData, projectGMSNumGMs[gms_id])
              );
              setIMVectors(GMSData["IMs"]);
              setDownloadToken(GMSData["download_token"]);

              // Min/Max values for CausalParamPlot
              setCausalParamBounds({
                mag: {
                  min: defaultParams["mw_low"],
                  max: defaultParams["mw_high"],
                },
                rrup: {
                  min: defaultParams["rrup_low"],
                  max: defaultParams["rrup_high"],
                },
                vs30: {
                  min: defaultParams["vs30_low"],
                  max: defaultParams["vs30_high"],
                  vs30: projectVS30,
                },
              });
              setContributionDFData(defaultParams["contribution_df"]);

              // For MwRrup plot (Both MwRrup and available GMs)
              setMwRrupBounds(
                createBoundsCoords(
                  defaultParams["rrup_low"],
                  defaultParams["rrup_high"],
                  defaultParams["mw_low"],
                  defaultParams["mw_high"]
                )
              );

              setDisaggMeanValues(GMSData["disagg_mean_values"]);

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
          setShowErrorMessage({ isError: true, errorCode: error });
          console.log(error);
        }
      }
    };
    getGMSData();

    return () => {
      abortController.abort();
    };
  }, [projectGMSGetClick]);

  const invalidInputs = () => {
    return !(
      isLoading === false &&
      computedGMS !== null &&
      showErrorMessage.isError === false
    );
  };

  return (
    <div className="gms-viewer">
      <Tabs defaultActiveKey="GMSIMDistributionsPlot">
        <Tab eventKey="GMSIMDistributionsPlot" title="IM Distributions">
          {projectGMSGetClick === null && (
            <GuideMessage
              header={CONSTANTS.GMS}
              body={CONSTANTS.GMS_VIEWER_GUIDE_MSG}
              instruction={CONSTANTS.PROJECT_GMS_VIEWER_GUIDE_INSTRUCTION}
            />
          )}
          {projectGMSGetClick !== null &&
            isLoading === true &&
            showErrorMessage.isError === false && <LoadingSpinner />}
          {isLoading === false && showErrorMessage.isError === true && (
            <ErrorMessage errorCode={showErrorMessage.errorCode} />
          )}
          {isLoading === false &&
            computedGMS !== null &&
            showErrorMessage.isError === false && (
              <Fragment>
                <Select
                  id="im-vectors"
                  onChange={(value) => setSpecifiedIM(value || [])}
                  defaultValue={specifiedIM}
                  options={localIMVectors}
                  isSearchable={false}
                  menuPlacement="auto"
                  menuPortalTarget={document.body}
                />
                {specifiedIM.value === "spectra" ? (
                  <GMSSpectraPlot GMSSpectraData={GMSSpectraData} />
                ) : (
                  <GMSIMDistributionsPlot
                    gmsData={computedGMS}
                    IM={specifiedIM.value}
                  />
                )}
              </Fragment>
            )}
        </Tab>
        <Tab eventKey="GMSCausalParamPlot" title="Causal Parameters">
          {projectGMSGetClick === null && (
            <GuideMessage
              header={CONSTANTS.GMS}
              body={CONSTANTS.GMS_VIEWER_GUIDE_MSG}
              instruction={CONSTANTS.PROJECT_GMS_VIEWER_GUIDE_INSTRUCTION}
            />
          )}
          {isLoading === true && showErrorMessage.isError === false && (
            <LoadingSpinner />
          )}
          {isLoading === false && showErrorMessage.isError === true && (
            <ErrorMessage errorCode={showErrorMessage.errorCode} />
          )}
          {isLoading === false &&
            computedGMS !== null &&
            showErrorMessage.isError === false && (
              <Fragment>
                <Select
                  id="metadata"
                  onChange={(value) => setSpecifiedMetadata(value || [])}
                  defaultValue={specifiedMetadata}
                  options={localmetadata}
                  isSearchable={false}
                  menuPlacement="auto"
                  formatOptionLabel={(data) => {
                    return (
                      <span
                        dangerouslySetInnerHTML={{
                          __html: sanitizer(data.label),
                        }}
                      />
                    );
                  }}
                />
                {specifiedMetadata.value === "mwrrupplot" ? (
                  <GMSMwRrupPlot
                    metadata={computedGMS["selected_gms_metadata"]}
                    bounds={mwRrupBounds}
                    meanValues={disaggMeanValues}
                  />
                ) : specifiedMetadata.value === "mag" ? (
                  <GMSDisaggDistributionPlot
                    contribution={contributionDFData["mag_contribution"]}
                    distribution={contributionDFData["magnitude"]}
                    selectedGMSMetadata={
                      computedGMS["selected_gms_metadata"]["mag"]
                    }
                    bounds={causalParamBounds["mag"]}
                    label={"mag"}
                  />
                ) : specifiedMetadata.value === "rrup" ? (
                  <GMSDisaggDistributionPlot
                    contribution={contributionDFData["rrup_contribution"]}
                    distribution={contributionDFData["rrup"]}
                    selectedGMSMetadata={
                      computedGMS["selected_gms_metadata"]["rrup"]
                    }
                    bounds={causalParamBounds["rrup"]}
                    label={"rrup"}
                  />
                ) : (
                  <GMSCausalParamPlot
                    gmsData={computedGMS}
                    metadata={specifiedMetadata.value}
                    causalParamBounds={causalParamBounds}
                  />
                )}
              </Fragment>
            )}
        </Tab>
      </Tabs>
      <DownloadButton
        disabled={invalidInputs()}
        downloadURL={
          CONSTANTS.PROJECT_API_GMS_DOWNLOAD_ENDPOINT + "/" + downloadToken
        }
        fileName="Projects_Ground_Motion_Selection.zip"
      />
    </div>
  );
};

export default GmsViewer;
