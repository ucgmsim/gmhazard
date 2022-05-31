import React, { useContext, useEffect, useState, Fragment } from "react";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import {
  LoadingSpinner,
  GuideMessage,
  ErrorMessage,
  ImageMap,
} from "components/common";
import { APIQueryBuilder, handleErrors } from "utils/Utils";

const SiteSelectionRegional = () => {
  const { getTokenSilently } = useAuth0();

  const {
    locationSetClick,
    selectedEnsemble,
    siteSelectionLng,
    siteSelectionLat,
  } = useContext(GlobalContext);

  const [contextPlot, setContextPlot] = useState(null);
  const [showSpinner, setShowSpinner] = useState(false);
  const [showErrorMessage, setShowErrorMessage] = useState({
    isError: false,
    errorCode: null,
  });

  // Get context plot/map
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getContextPlot = async () => {
      if (locationSetClick !== null) {
        try {
          const token = await getTokenSilently();
          setShowSpinner(true);
          setShowErrorMessage({ isError: false, errorCode: null });

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_CONTEXT_MAP_ENDPOINT +
              APIQueryBuilder({
                ensemble_id: selectedEnsemble,
                lon: siteSelectionLng,
                lat: siteSelectionLat,
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
              setShowSpinner(false);
              setContextPlot(responseData["context_plot"]);
            })
            .catch((error) => {
              if (error.name !== "AbortError") {
                setShowSpinner(false);
                setShowErrorMessage({ isError: true, errorCode: error });
              }
              console.log(error);
            });
        } catch (error) {
          setShowSpinner(false);
          setShowErrorMessage({ isError: true, errorCode: error });
          console.log(error);
        }
      }
    };
    getContextPlot();

    return () => {
      abortController.abort();
    };
  }, [locationSetClick]);

  return (
    <Fragment>
      {locationSetClick === null && (
        <GuideMessage
          header={CONSTANTS.SITE_SELECTION_REGIONAL_TITLE}
          body={CONSTANTS.SITE_SELECTION_REGIONAL_MSG}
          instruction={CONSTANTS.SITE_SELECTION_REGIONAL_INSTRUCTION}
        />
      )}

      {showSpinner === true && locationSetClick !== null && <LoadingSpinner />}

      {locationSetClick !== null &&
        showSpinner === false &&
        showErrorMessage.isError === true && (
          <ErrorMessage errorCode={showErrorMessage.errorCode} />
        )}

      {contextPlot !== null &&
        showSpinner === false &&
        showErrorMessage.isError === false && (
          <ImageMap
            header={CONSTANTS.REGIONAL_MAP_DESCRIPTION}
            src={contextPlot}
            alt={CONSTANTS.REGIONAL_MAP_IMG_ALT}
          />
        )}
    </Fragment>
  );
};

export default SiteSelectionRegional;
