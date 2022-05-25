import React, { Fragment, useContext, useEffect, useState } from "react";

import Select from "react-select";
import dompurify from "dompurify";
import { Tabs, Tab } from "react-bootstrap";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

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
import { getProjectGMS } from "apis/ProjectAPI";
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
  const { isAuthenticated, getTokenSilently } = useAuth0();

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
    projectSiteSelectionGetClick,
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

  // Reset tabs if users click Get button from Site Selection
  useEffect(() => {
    if (projectSiteSelectionGetClick !== null) {
      setIsLoading(false);
      setShowErrorMessage({
        isError: false,
        errorCode: null,
      });
      setComputedGMS(null);
      setProjectGMSGetClick(null);
    }
  }, [projectSiteSelectionGetClick]);

  // Create IM array of objects for IM Distributions plot (react-select dropdown)
  useEffect(() => {
    if (IMVectors.length > 0) {
      let localIMs = sortIMs(IMVectors).map((IM) => ({
        value: IM,
        label: GMSIMLabelConverter(IM),
      }));
      // Insert spectra, disagg distribution plots before any IM
      localIMs.splice(0, 0, {
        value: `${CONSTANTS.SPECTRA}`,
        label: `${CONSTANTS.PSEUDO_ACCELERATION_RESPONSE_SPECTRA}`,
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
        value: `${CONSTANTS.MAG_RRUP_PLOT}`,
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

    if (projectGMSGetClick !== null) {
      setShowErrorMessage({ isError: false, errorCode: null });
      setIsLoading(true);

      let token = null;
      const gms_id = projectGMSIDs.find((GMSId) => {
        return (
          GMSId.includes(
            `${projectGMSConditionIM}_${projectGMSSelectedIMPeriod.replace(
              ".",
              "p"
            )}`
          ) &&
          GMSId.includes(projectGMSExceedance.toString().replace(".", "p")) &&
          GMSId.includes(
            [
              ...new Set(projectGMSIMVector.replace(/[0-9]/g, "").split(", ")),
            ].join("_")
          )
        );
      });
      const queryString = APIQueryBuilder({
        project_id: projectId["value"],
        station_id: createStationID(
          projectLocationCode[projectLocation],
          projectVS30,
          projectZ1p0,
          projectZ2p5
        ),
        gms_id: gms_id,
      });

      (async () => {
        if (isAuthenticated) token = await getTokenSilently();

        getProjectGMS(queryString, signal, token)
          .then(handleErrors)
          .then(async ([gms, defaultCausalParam]) => {
            const gmsData = await gms.json();
            const defaultCausalParamData = await defaultCausalParam.json();

            updateGMSPlots(gmsData, defaultCausalParamData, gms_id);
          })
          .catch((error) => catchError(error));
      })();
    }

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

  const updateGMSPlots = (gmsData, defaultCausalParamsData, gms_id) => {
    setComputedGMS(gmsData);
    setGMSSpectraData(calculateGMSSpectra(gmsData, projectGMSNumGMs[gms_id]));
    setIMVectors(gmsData["IMs"]);
    setDownloadToken(gmsData["download_token"]);

    // Min/Max values for CausalParamPlot
    setCausalParamBounds({
      mag: {
        min: defaultCausalParamsData["mw_low"],
        max: defaultCausalParamsData["mw_high"],
      },
      rrup: {
        min: defaultCausalParamsData["rrup_low"],
        max: defaultCausalParamsData["rrup_high"],
      },
      vs30: {
        min: defaultCausalParamsData["vs30_low"],
        max: defaultCausalParamsData["vs30_high"],
        vs30: projectVS30,
      },
    });
    setContributionDFData(defaultCausalParamsData["contribution_df"]);

    // For MwRrup plot (Both MwRrup and available GMs)
    setMwRrupBounds(
      createBoundsCoords(
        defaultCausalParamsData["rrup_low"],
        defaultCausalParamsData["rrup_high"],
        defaultCausalParamsData["mw_low"],
        defaultCausalParamsData["mw_high"]
      )
    );

    setDisaggMeanValues(gmsData["disagg_mean_values"]);

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
    <div className="gms-viewer">
      <Tabs defaultActiveKey="GMSIMDistributionsPlot">
        <Tab
          eventKey="GMSIMDistributionsPlot"
          title={CONSTANTS.GMS_IM_DISTRIBUTIONS_PLOT}
        >
          {projectGMSGetClick === null && (
            <GuideMessage
              header={CONSTANTS.GROUND_MOTION_SELECTION}
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
                {specifiedIM.value === `${CONSTANTS.SPECTRA}` ? (
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
        <Tab eventKey="GMSCausalParamPlot" title={CONSTANTS.CAUSAL_PARAMETERS}>
          {projectGMSGetClick === null && (
            <GuideMessage
              header={CONSTANTS.GROUND_MOTION_SELECTION}
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
                {specifiedMetadata.value === `${CONSTANTS.MAG_RRUP_PLOT}` ? (
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
