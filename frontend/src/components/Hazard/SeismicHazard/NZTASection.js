import React, { useState, useEffect, useContext, Fragment } from "react";

import Select from "react-select";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import {
  APIQueryBuilder,
  handleErrors,
  isEmptyObj,
  combineIMwithPeriod,
} from "utils/Utils";

import "assets/style/NZCodeSection.css";

const NZTASection = () => {
  const { getTokenSilently } = useAuth0();

  const {
    selectedEnsemble,
    station,
    selectedIM,
    selectedIMPeriod,
    selectedIMComponent,
    setHazardNZTAData,
    nztaSoilClass,
    nztaDefaultParams,
    selectedNZTASoilClass,
    setSelectedNZTASoilClass,
    setIsNZTAComputed,
    computedNZTASoilClass,
    setComputedNZTASoilClass,
    hazardCurveComputeClick,
    setHazardNZTAToken,
    nztaDefaultSoilClass,
  } = useContext(GlobalContext);

  const [computeButton, setComputeButton] = useState({
    text: "Compute",
    isFetching: false,
  });

  // Local Soil Class
  const [localSelectedSoilClass, setLocalSelectedSoilClass] = useState({});

  /*
    When app managed to get a default params (Soil Class)
    Set for Local&Global selected variable
  */
  useEffect(() => {
    if (
      nztaDefaultParams.length !== 0 &&
      nztaSoilClass.length !== 0 &&
      !isEmptyObj(nztaDefaultSoilClass)
    ) {
      /* 
        Set the default selected soil class
        1. Global
        Only if the global variable is an empty object
        (Very first set location)
      */
      if (isEmptyObj(selectedNZTASoilClass)) {
        setSelectedNZTASoilClass(nztaDefaultSoilClass);
      }
    }
  }, [nztaDefaultParams, nztaSoilClass, nztaDefaultSoilClass]);

  /*
    Use the globally set NZTA Soil class if it exists
    Otherwise, use the default one
  */
  useEffect(() => {
    if (!isEmptyObj(selectedNZTASoilClass)) {
      setLocalSelectedSoilClass(selectedNZTASoilClass);
    } else {
      setLocalSelectedSoilClass(nztaDefaultSoilClass);
    }
  }, [selectedNZTASoilClass]);

  const onClickDefaultSoilClass = () => {
    setLocalSelectedSoilClass(nztaDefaultSoilClass);
    setSelectedNZTASoilClass(nztaDefaultSoilClass);
  };

  /*
    API calls that wil be eventually separated
  */
  const computeHazardNZTACode = async () => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const token = await getTokenSilently();

    setComputeButton({
      text: <FontAwesomeIcon icon="spinner" spin />,
      isFetching: true,
    });

    setComputedNZTASoilClass(selectedNZTASoilClass);

    setIsNZTAComputed(false);

    await fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.CORE_API_HAZARD_NZTA_ENDPOINT +
        APIQueryBuilder({
          ensemble_id: selectedEnsemble,
          station: station,
          im: combineIMwithPeriod(selectedIM, selectedIMPeriod),
          soil_class: selectedNZTASoilClass["value"],
          im_component: selectedIMComponent,
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
        const hazardNZTAData = await response.json();
        setHazardNZTAData(hazardNZTAData["nzta_hazard"]["pga_values"]);

        setHazardNZTAToken(hazardNZTAData["download_token"]);

        setIsNZTAComputed(true);
        setComputeButton({
          text: "Compute",
          isFetching: false,
        });
      })
      .catch((error) => {
        if (error.name !== "AbortError") {
          setComputeButton({
            text: "Compute",
            isFetching: false,
          });
        }
        console.log(error);
      });
  };

  /*
    Compute button is disabled when users haven't computed Hazard Curve.
    Button stays disabled until user changes the Soil Class
  */
  const invalidInputs = () => {
    return !(
      selectedNZTASoilClass["value"] !== computedNZTASoilClass["value"] &&
      hazardCurveComputeClick !== null
    );
  };

  return (
    <Fragment>
      <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group">
          <div className="d-flex align-items-center">
            <label
              htmlFor="soil-class"
              className="control-label label-soil-class"
            >
              Soil Class
            </label>
            <Select
              id="soil-class"
              className="flex-grow-1"
              value={localSelectedSoilClass}
              onChange={setLocalSelectedSoilClass}
              options={nztaSoilClass}
              isDisabled={nztaSoilClass.length === 0}
            />
          </div>
        </div>

        <div className="form-row">
          <button
            id="set-soil-class"
            type="button"
            className="btn btn-primary"
            disabled={
              selectedNZTASoilClass["value"] === localSelectedSoilClass["value"]
            }
            onClick={() => setSelectedNZTASoilClass(localSelectedSoilClass)}
          >
            Set Soil Class
          </button>
          <button
            id="soil-class-default-button"
            type="button"
            className="btn btn-primary default-button"
            disabled={
              selectedNZTASoilClass["value"] === nztaDefaultSoilClass["value"]
            }
            onClick={() => onClickDefaultSoilClass()}
          >
            Use Default
          </button>
        </div>

        <div className="form-row">
          <button
            id="compute-nzta-code"
            type="button"
            className="btn btn-primary"
            disabled={invalidInputs()}
            onClick={() => computeHazardNZTACode()}
          >
            {computeButton.text}
          </button>
        </div>
      </form>
    </Fragment>
  );
};

export default NZTASection;
