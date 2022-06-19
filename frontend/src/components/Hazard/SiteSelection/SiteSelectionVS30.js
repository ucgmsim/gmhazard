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

const SiteSelectionVS30 = () => {
  const { getTokenSilently } = useAuth0();

  const {
    locationSetClick,
    selectedEnsemble,
    siteSelectionLng,
    siteSelectionLat,
  } = useContext(GlobalContext);

  const [vs30Map, setVS30Map] = useState(null);
  const [showSpinner, setShowSpinner] = useState(false);
  const [showErrorMessage, setShowErrorMessage] = useState({
    isError: false,
    errorCode: null,
  });

  // Get Vs30 map
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getVs30Map = async () => {
      if (locationSetClick !== null) {
        try {
          const token = await getTokenSilently();
          setShowSpinner(true);
          setShowErrorMessage({ isError: false, errorCode: null });

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_VS30_MAP_ENDPOINT +
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
              setVS30Map(responseData["vs30_plot"]);
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
    getVs30Map();

    return () => {
      abortController.abort();
    };
  }, [locationSetClick]);

  return (
    <Fragment>
      {locationSetClick === null && (
        <GuideMessage
          header={CONSTANTS.SITE_SELECTION_VS30_TITLE}
          body={CONSTANTS.SITE_SELECTION_VS30_MSG}
          instruction={CONSTANTS.SITE_SELECTION_VS30_INSTRUCTION}
        />
      )}

      {showSpinner === true && locationSetClick !== null && <LoadingSpinner />}

      {locationSetClick !== null &&
        showSpinner === false &&
        showErrorMessage.isError === true && (
          <ErrorMessage errorCode={showErrorMessage.errorCode} />
        )}

      {vs30Map !== null &&
        showSpinner === false &&
        showErrorMessage.isError === false && (
          <ImageMap
            header={CONSTANTS.VS30_MAP_DESCRIPTION}
            src={vs30Map}
            alt={CONSTANTS.VS30_MAP_IMG_ALT}
          />
        )}
    </Fragment>
  );
};

export default SiteSelectionVS30;
