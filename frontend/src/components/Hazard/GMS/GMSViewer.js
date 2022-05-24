import React, { Fragment, useContext, useState, useEffect } from "react";

import { Tabs, Tab } from "react-bootstrap";
import Select from "react-select";
import dompurify from "dompurify";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import {
  LoadingSpinner,
  DownloadButton,
  GuideMessage,
  ErrorMessage,
  GMSIMDistributionsPlot,
  GMSSpectraPlot,
  GMSMwRrupPlot,
  GMSCausalParamPlot,
  GMSAvailableGMPlot,
} from "components/common";
import {
  handleErrors,
  GMSIMLabelConverter,
  arrayEquals,
  createBoundsCoords,
  combineIMwithPeriod,
} from "utils/Utils";
import { calculateGMSSpectra } from "utils/calculations/CalculateGMSSpectra";

import "assets/style/GMSViewer.css";

const GMSViewer = () => {
  const { getTokenSilently } = useAuth0();

  const sanitizer = dompurify.sanitize;

  const {
    selectedEnsemble,
    station,
    vs30,
    defaultVS30,
    GMSComputeClick,
    GMSIMLevel,
    GMSExcdRate,
    GMSIMVector,
    GMSRadio,
    GMSIMType,
    GMSIMPeriod,
    GMSNum,
    GMSReplicates,
    GMSWeights,
    GMSMwMin,
    GMSMwMax,
    GMSRrupMin,
    GMSRrupMax,
    GMSVS30Min,
    GMSVS30Max,
    GMSSFMin,
    GMSSFMax,
    GMSDatabase,
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
  const [mwRrupBounds, setMwRrupBounds] = useState({});
  const [numGMsInBounds, setNumGMsInBounds] = useState(0);
  // This state holds mw/rrup mean & 16/84th percentiles
  const [disaggMeanValues, setDisaggMeanValues] = useState({});

  // GMS data validator
  const [isValidGMSData, setIsValidGMSData] = useState(false);

  // For Select, dropdown
  const [selectedIMVectors, setSelectedIMVectors] = useState([]);
  const [specifiedIM, setSpecifiedIM] = useState([]);
  const [localIMVectors, setLocalIMVectors] = useState([]);
  const [specifiedMetadata, setSpecifiedMetadata] = useState([]);
  const [localmetadata, setLocalmetadata] = useState([]);

  // For Download data button
  const [downloadToken, setDownloadToken] = useState("");

  // Get GMS data
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const computeEnsembleGMS = async () => {
      if (
        GMSComputeClick !== null &&
        (GMSIMLevel !== "" || GMSExcdRate !== "")
      ) {
        try {
          const token = await getTokenSilently();

          setIsLoading(true);
          setComputedGMS(null);
          setShowErrorMessage({ isError: false, errorCode: null });

          // Create an IMVectors array with only values
          const newIMVector = GMSIMVector.map((vector) => vector.value);

          const causalParamsBounds = {
            mag_low: Number(GMSMwMin),
            mag_high: Number(GMSMwMax),
            rrup_low: Number(GMSRrupMin),
            rrup_high: Number(GMSRrupMax),
            vs30_low: Number(GMSVS30Min),
            vs30_high: Number(GMSVS30Max),
            sf_low: Number(GMSSFMin),
            sf_high: Number(GMSSFMax),
          };

          // Min/Max values for CausalParamPlot
          setCausalParamBounds({
            mag: {
              min: GMSMwMin,
              max: GMSMwMax,
            },
            rrup: {
              min: GMSRrupMin,
              max: GMSRrupMax,
            },
            vs30: {
              min: GMSVS30Min,
              max: GMSVS30Max,
              vs30: vs30,
            },
            sf: {
              min: GMSSFMin,
              max: GMSSFMax,
            },
          });

          // For MwRrup plot (Both MwRrup and available GMs)
          setMwRrupBounds(
            createBoundsCoords(GMSRrupMin, GMSRrupMax, GMSMwMin, GMSMwMax)
          );

          let requestOptions = {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            signal: signal,
          };

          let gmsRequestDataDict = {
            ensemble_id: selectedEnsemble,
            station: station,
            IM_j: combineIMwithPeriod(GMSIMType, GMSIMPeriod),
            IMs: newIMVector,
            n_gms: Number(GMSNum),
            gm_dataset_ids: [GMSDatabase],
            n_replica: Number(GMSReplicates),
            IM_weights: GMSWeights,
            cs_param_bounds: causalParamsBounds,
          };

          if (vs30 !== defaultVS30) {
            gmsRequestDataDict["vs30"] = Number(vs30);
          }

          if (GMSRadio === "im-level") {
            gmsRequestDataDict["im_level"] = Number(GMSIMLevel);
          } else if (GMSRadio === "exceedance-rate") {
            gmsRequestDataDict["exceedance"] = Number(GMSExcdRate);
          }

          requestOptions["body"] = JSON.stringify(gmsRequestDataDict);

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL + CONSTANTS.CORE_API_GMS_ENDPOINT,
            requestOptions
          )
            .then(handleErrors)
            .then(async (response) => {
              const responseData = await response.json();
              setComputedGMS(responseData);
              setSelectedIMVectors(newIMVector);
              setDownloadToken(responseData["download_token"]);
              setNumGMsInBounds(responseData["n_gms_in_bounds"]);
              setDisaggMeanValues(responseData["disagg_mean_values"]);

              // Validate the computed data to see whether its valid
              setIsValidGMSData(validateComputedGMS(responseData));

              setGMSSpectraData(
                calculateGMSSpectra(responseData, Number(GMSNum))
              );

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
          console.log(error);
        }
      }
    };

    computeEnsembleGMS();

    return () => {
      abortController.abort();
    };
  }, [GMSComputeClick]);

  // Create proper IM array for react-select package
  useEffect(() => {
    let localIMs = selectedIMVectors.map((IM) => ({
      value: IM,
      label: GMSIMLabelConverter(IM),
    }));

    localIMs.splice(0, 0, {
      value: "spectra",
      label: "Pseudo acceleration response spectra",
    });
    setLocalIMVectors(localIMs);

    // Set the first IM as a default IM for plot
    setSpecifiedIM(localIMs[1]);
  }, [selectedIMVectors]);

  // Create a readable array for react-select dropdown and
  // set the default metadata to display a default plot
  useEffect(() => {
    if (computedGMS !== null) {
      const metadata = computedGMS["selected_gms_metadata"];
      // Create an array of objects first then filter the one needed
      // rrup, sf, vs30 and mag
      let tempmetadata = Object.getOwnPropertyNames(metadata)
        .map((metadata) => ({
          value: metadata,
          label: `${CONSTANTS.GMS_LABELS[metadata]} distribution`,
        }))
        .filter((metadata) =>
          Object.keys(CONSTANTS.GMS_LABELS).includes(metadata.value)
        );

      tempmetadata.splice(0, 0, {
        value: "mwrrupplot",
        label: `Magnitude and rupture distance (Mw-R${"rup".sub()}) distribution`,
      });
      tempmetadata.splice(1, 0, {
        value: "availablegms",
        label: "Available ground motions",
      });

      // Set the first Metadata as a default metadata for plot
      setSpecifiedMetadata(tempmetadata[2]);

      setLocalmetadata(tempmetadata);
    }
  }, [computedGMS]);

  const invalidDownload = () => {
    return (
      !(
        isLoading === false &&
        computedGMS !== null &&
        showErrorMessage.isError === false
      ) && !isValidGMSData
    );
  };

  /*
    Validate Computed GMS data
    Return false
    if
    - null or undefined
    - no values for a certain property
    - properties of the object(E.g., gcim_cdf_x, gcim_cdf_y)
      are equal to the selected IM Vectors
    - metadata object's properties are not [mag, rrup, sf, vs30]
    else true
  */
  const validateComputedGMS = (providedGMSData) => {
    if (providedGMSData === undefined || providedGMSData === null) {
      return false;
    }

    Object.values(providedGMSData).forEach((x) => {
      // Like ks_bound value is Number and is not working with Object.keys(x).length
      if (!isNaN(x)) {
        return;
      }
      if (Object.keys(x).length === 0) {
        return false;
      }
    });

    const sortedSelectedIMVector = GMSIMVector.map((im) => im.value).sort();

    if (!arrayEquals(providedGMSData["IMs"].sort(), sortedSelectedIMVector)) {
      setShowErrorMessage({ isError: true, errorCode: "gms_im" });
      return false;
    }

    if (
      !arrayEquals(
        Object.keys(providedGMSData["gcim_cdf_x"]).sort(),
        sortedSelectedIMVector
      )
    ) {
      setShowErrorMessage({ isError: true, errorCode: "gms_gcim_cdf_x" });
      return false;
    }

    if (
      !arrayEquals(
        Object.keys(providedGMSData["gcim_cdf_y"]).sort(),
        sortedSelectedIMVector
      )
    ) {
      setShowErrorMessage({ isError: true, errorCode: "gms_gcim_cdf_y" });
      return false;
    }

    if (
      !arrayEquals(
        Object.keys(providedGMSData["realisations"]).sort(),
        sortedSelectedIMVector
      )
    ) {
      setShowErrorMessage({ isError: true, errorCode: "gms_realisations" });
      return false;
    }

    if (
      providedGMSData["IM_j"] !== combineIMwithPeriod(GMSIMType, GMSIMPeriod)
    ) {
      setShowErrorMessage({ isError: true, errorCode: "gms_IM_j" });
      return false;
    }

    if (
      !(Object.keys(providedGMSData["selected_gms_metadata"]).sort(),
      Object.keys(CONSTANTS.GMS_LABELS).sort())
    ) {
      setShowErrorMessage({ isError: true, errorCode: "gms_metadata" });
      return false;
    }

    return true;
  };

  return (
    <div className="gms-viewer">
      <Tabs defaultActiveKey="GMSIMDistributionsPlot">
        <Tab
          eventKey="GMSIMDistributionsPlot"
          title={CONSTANTS.GMS_IM_DISTRIBUTIONS_PLOT}
        >
          {GMSComputeClick === null && (
            <GuideMessage
              header={CONSTANTS.GMS}
              body={CONSTANTS.GMS_VIEWER_GUIDE_MSG}
              instruction={CONSTANTS.GMS_VIEWER_GUIDE_INSTRUCTION}
            />
          )}
          {GMSComputeClick !== null &&
            isLoading === true &&
            showErrorMessage.isError === false && <LoadingSpinner />}
          {isLoading === false && showErrorMessage.isError === true && (
            <ErrorMessage errorCode={showErrorMessage.errorCode} />
          )}
          {isLoading === false &&
            computedGMS !== null &&
            showErrorMessage.isError === false && (
              <Fragment>
                {isValidGMSData ? (
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
                ) : (
                  <ErrorMessage errorCode={showErrorMessage.errorCode} />
                )}
              </Fragment>
            )}
        </Tab>
        <Tab eventKey="GMSCausalParamPlot" title={CONSTANTS.CAUSAL_PARAMETERS}>
          {GMSComputeClick === null && (
            <GuideMessage
              header={CONSTANTS.GMS}
              body={CONSTANTS.GMS_VIEWER_GUIDE_MSG}
              instruction={CONSTANTS.GMS_VIEWER_GUIDE_INSTRUCTION}
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
                {isValidGMSData ? (
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
                        numGMs={Number(GMSNum)}
                      />
                    ) : specifiedMetadata.value === "availablegms" ? (
                      <GMSAvailableGMPlot
                        metadata={computedGMS["gm_dataset_metadata"]}
                        bounds={mwRrupBounds}
                        numGMs={numGMsInBounds}
                      />
                    ) : (
                      <GMSCausalParamPlot
                        gmsData={computedGMS}
                        metadata={specifiedMetadata.value}
                        causalParamBounds={causalParamBounds}
                      />
                    )}
                  </Fragment>
                ) : (
                  <ErrorMessage errorCode={showErrorMessage.errorCode} />
                )}
              </Fragment>
            )}
        </Tab>
      </Tabs>
      <DownloadButton
        disabled={invalidDownload()}
        downloadURL={CONSTANTS.CORE_API_GMS_DOWNLOAD_ENDPOINT}
        downloadToken={{
          gms_token: downloadToken,
        }}
        fileName="Ground_Motion_Selection.zip"
      />
    </div>
  );
};

export default GMSViewer;
