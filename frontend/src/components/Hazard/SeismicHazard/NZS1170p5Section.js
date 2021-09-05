import React, { useState, useEffect, useContext, Fragment } from "react";

import TextField from "@material-ui/core/TextField";
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

const NZS1170p5Section = () => {
  const { getTokenSilently } = useAuth0();

  const {
    selectedEnsemble,
    station,
    selectedIM,
    selectedIMPeriod,
    selectedIMComponent,
    setHazardNZS1170p5Data,
    setUHSNZS1170p5Data,
    nzs1170p5SoilClass,
    nzs1170p5DefaultParams,
    selectedNZS1170p5SoilClass,
    setSelectedNZS1170p5SoilClass,
    selectedNZS1170p5ZFactor,
    setSelectedNZS1170p5ZFactor,
    setIsNZS1170p5Computed,
    computedNZS1170p5SoilClass,
    setComputedNZS1170p5SoilClass,
    computedNZS1170p5ZFactor,
    setComputedNZS1170p5ZFactor,
    hazardCurveComputeClick,
    uhsComputeClick,
    uhsRateTable,
    setHazardNZS1170p5Token,
    setUHSNZS1170p5Token,
    nzs1170p5DefaultSoilClass,
  } = useContext(GlobalContext);

  const [computeButton, setComputeButton] = useState({
    text: "Compute",
    isFetching: false,
  });

  // Local vars Z-factor & Soil Class
  const [localZFactor, setLocalZFactor] = useState(-1);
  const [localSelectedSoilClass, setLocalSelectedSoilClass] = useState({});

  /*
    When app managed to get a default params (Z Factor and Soil Class)
    Set for Local&Global selected variable
  */
  useEffect(() => {
    if (
      nzs1170p5DefaultParams.length !== 0 &&
      nzs1170p5SoilClass.length !== 0 &&
      !isEmptyObj(nzs1170p5DefaultSoilClass)
    ) {
      /* 
        Set the default selected soil class
        1. Global
        Only if the global variable is an empty object
        (Very first set location)
      */
      if (isEmptyObj(selectedNZS1170p5SoilClass)) {
        setSelectedNZS1170p5SoilClass(nzs1170p5DefaultSoilClass);
      }

      /*
        Based on feedback, Z Factor will never be a negative number, and using this magic number to set default value.
        This was the only way I could find to avoid a warning about having uncrontrolled & controlled form at the same time.
        (React doesn't recommend having a form with controlled and uncontrolled at the same time.)
      */
      if (localZFactor === -1) {
        setLocalZFactor(Number(nzs1170p5DefaultParams["z_factor"]));
        setSelectedNZS1170p5ZFactor(Number(nzs1170p5DefaultParams["z_factor"]));
      }
    }
  }, [nzs1170p5DefaultParams, nzs1170p5SoilClass, nzs1170p5DefaultSoilClass]);

  /*
    Use the globally set NZS1170.5 Soil class if it exists
    Otherwise, use the default one
  */
  useEffect(() => {
    if (!isEmptyObj(selectedNZS1170p5SoilClass)) {
      setLocalSelectedSoilClass(selectedNZS1170p5SoilClass);
    } else {
      setLocalSelectedSoilClass(nzs1170p5DefaultSoilClass);
    }
  }, [selectedNZS1170p5SoilClass]);

  const onClickDefaultZFactor = () => {
    setLocalZFactor(Number(nzs1170p5DefaultParams["z_factor"]));
    setSelectedNZS1170p5ZFactor(Number(nzs1170p5DefaultParams["z_factor"]));
  };

  const onClickDefaultSoilClass = () => {
    setLocalSelectedSoilClass(nzs1170p5DefaultSoilClass);
    setSelectedNZS1170p5SoilClass(nzs1170p5DefaultSoilClass);
  };

  const computeBothNZS1170p5Code = async () => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const token = await getTokenSilently();

    const exceedances = uhsRateTable.map((entry, idx) => {
      return parseFloat(entry) > 0 ? parseFloat(entry) : 1 / parseFloat(entry);
    });

    setComputeButton({
      text: <FontAwesomeIcon icon="spinner" spin />,
      isFetching: true,
    });

    // To be used to compare with local Z Factor and Soil class to validate Compute Button.
    setComputedNZS1170p5ZFactor(selectedNZS1170p5ZFactor);
    setComputedNZS1170p5SoilClass(selectedNZS1170p5SoilClass);

    setIsNZS1170p5Computed(false);

    await Promise.all([
      fetch(
        CONSTANTS.INTERMEDIATE_API_URL +
          CONSTANTS.CORE_API_HAZARD_NZS1170P5_ENDPOINT +
          APIQueryBuilder({
            ensemble_id: selectedEnsemble,
            station: station,
            im: combineIMwithPeriod(selectedIM, selectedIMPeriod),
            soil_class: selectedNZS1170p5SoilClass["value"],
            distance: Number(nzs1170p5DefaultParams["distance"]),
            z_factor: selectedNZS1170p5ZFactor,
            im_component: selectedIMComponent,
          }),
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: signal,
        }
      ),
      fetch(
        CONSTANTS.INTERMEDIATE_API_URL +
          CONSTANTS.CORE_API_HAZARD_UHS_NZS1170P5_ENDPOINT +
          APIQueryBuilder({
            ensemble_id: selectedEnsemble,
            station: station,
            exceedances: `${exceedances.join(",")}`,
            soil_class: selectedNZS1170p5SoilClass["value"],
            distance: Number(nzs1170p5DefaultParams["distance"]),
            z_factor: selectedNZS1170p5ZFactor,
            im_component: selectedIMComponent,
          }),
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: signal,
        }
      ),
    ])
      .then(handleErrors)
      .then(async ([hazard, uhs]) => {
        const hazardNZS1170p5Data = await hazard.json();
        const uhsNZS1170p5Data = await uhs.json();
        setHazardNZS1170p5Data(
          hazardNZS1170p5Data["nzs1170p5_hazard"]["im_values"]
        );
        setUHSNZS1170p5Data(uhsNZS1170p5Data["nzs1170p5_uhs_df"]);

        setHazardNZS1170p5Token(hazardNZS1170p5Data["download_token"]);
        setUHSNZS1170p5Token(uhsNZS1170p5Data["download_token"]);

        setIsNZS1170p5Computed(true);
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

  const computeHazardNZS1170p5Code = async () => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const token = await getTokenSilently();

    setComputeButton({
      text: <FontAwesomeIcon icon="spinner" spin />,
      isFetching: true,
    });

    // To be used to compare with local Z Factor and Soil class to validate Compute Button.
    setComputedNZS1170p5ZFactor(selectedNZS1170p5ZFactor);
    setComputedNZS1170p5SoilClass(selectedNZS1170p5SoilClass);

    setIsNZS1170p5Computed(false);

    await fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.CORE_API_HAZARD_NZS1170P5_ENDPOINT +
        APIQueryBuilder({
          ensemble_id: selectedEnsemble,
          station: station,
          im: combineIMwithPeriod(selectedIM, selectedIMPeriod),
          soil_class: selectedNZS1170p5SoilClass["value"],
          distance: Number(nzs1170p5DefaultParams["distance"]),
          z_factor: selectedNZS1170p5ZFactor,
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
        const hazardNZS1170p5Data = await response.json();
        setHazardNZS1170p5Data(
          hazardNZS1170p5Data["nzs1170p5_hazard"]["im_values"]
        );

        setHazardNZS1170p5Token(hazardNZS1170p5Data["download_token"]);

        setIsNZS1170p5Computed(true);
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

  const computeUHSNZS1170p5Code = async () => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const token = await getTokenSilently();

    setComputeButton({
      text: <FontAwesomeIcon icon="spinner" spin />,
      isFetching: true,
    });

    // To be used to compare with local Z Factor and Soil class to validate Compute Button.
    setComputedNZS1170p5ZFactor(selectedNZS1170p5ZFactor);
    setComputedNZS1170p5SoilClass(selectedNZS1170p5SoilClass);

    const exceedances = uhsRateTable.map((entry, idx) => {
      return parseFloat(entry) > 0 ? parseFloat(entry) : 1 / parseFloat(entry);
    });

    setIsNZS1170p5Computed(false);

    await fetch(
      CONSTANTS.INTERMEDIATE_API_URL +
        CONSTANTS.CORE_API_HAZARD_UHS_NZS1170P5_ENDPOINT +
        APIQueryBuilder({
          ensemble_id: selectedEnsemble,
          station: station,
          exceedances: `${exceedances.join(",")}`,
          soil_class: selectedNZS1170p5SoilClass["value"],
          distance: Number(nzs1170p5DefaultParams["distance"]),
          z_factor: selectedNZS1170p5ZFactor,
          im_component:
            selectedIMComponent === null ? "RotD50" : selectedIMComponent,
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
        const uhsNZS1170p5Data = await response.json();
        setUHSNZS1170p5Data(uhsNZS1170p5Data["nzs1170p5_uhs_df"]);

        setUHSNZS1170p5Token(uhsNZS1170p5Data["download_token"]);

        setIsNZS1170p5Computed(true);
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
    When NZS1170.5 code's Compute gets clicked
    Depends on the situation, it has three different scenarios
    1. Only Hazard Curve is computed, call Hazard Curve's NZS1170.5 to update its NZS1170.5 code data
    2. Only UHS is computed, call UHSs NZS1170P5 to update its NZS1170.5 code data
    3. Both Hazard Curve and UHS are computed, check the selected IM
      if selected IM is either PGA or pSA, then call both API to update their NZS1170.5 code data
      if not, only update the UHS's NZS1170.5 code data
  */

  const computeNZS11705pCode = () => {
    if (hazardCurveComputeClick === null && uhsComputeClick !== null) {
      computeUHSNZS1170p5Code();
    } else if (uhsComputeClick === null && hazardCurveComputeClick !== null) {
      computeHazardNZS1170p5Code();
    } else if (uhsComputeClick !== null && hazardCurveComputeClick !== null) {
      if (selectedIM === "PGA" || selectedIM === "pSA") {
        computeBothNZS1170p5Code();
      } else {
        computeUHSNZS1170p5Code();
      }
    }
  };

  /*
    Button stays disabled in the following situation
    1. The Soil Class hasn't been changed from the default value or
    2. The Z Factor hasn't been changed from the default value or
    3. Hazard Curve got computed but selected IM is not PGA nor pSA or
    4. UHS didn't get computed
      (Does not matter whether the Hazard Curve got computed or not)
  */
  const invalidInputs = () => {
    return !(
      (selectedNZS1170p5SoilClass["value"] !==
        computedNZS1170p5SoilClass["value"] ||
        selectedNZS1170p5ZFactor !== computedNZS1170p5ZFactor) &&
      ((hazardCurveComputeClick !== null &&
        uhsComputeClick === null &&
        (selectedIM === "PGA" || selectedIM === "pSA")) ||
        uhsComputeClick !== null)
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
              options={nzs1170p5SoilClass}
              isDisabled={nzs1170p5SoilClass.length === 0}
              menuPlacement="auto"
              menuPortalTarget={document.body}
            />
          </div>
        </div>

        <div className="form-row">
          <button
            id="set-soil-class"
            type="button"
            className="btn btn-primary"
            disabled={
              selectedNZS1170p5SoilClass["value"] ===
              localSelectedSoilClass["value"]
            }
            onClick={() =>
              setSelectedNZS1170p5SoilClass(localSelectedSoilClass)
            }
          >
            Set Soil Class
          </button>
          <button
            id="soil-class-default-button"
            type="button"
            className="btn btn-primary default-button"
            disabled={
              selectedNZS1170p5SoilClass["value"] ===
              nzs1170p5DefaultSoilClass["value"]
            }
            onClick={() => onClickDefaultSoilClass()}
          >
            Use Default
          </button>
        </div>

        <div className="form-group">
          <div className="d-flex align-items-center">
            <label
              id="label-z-factor"
              htmlFor="z-factor"
              className="control-label"
            >
              Z Factor
            </label>
            <TextField
              id="z-factor"
              className="flex-grow-1"
              type="number"
              value={localZFactor}
              onChange={(e) => setLocalZFactor(e.target.value)}
              variant="outlined"
            />
          </div>
        </div>
        <div className="form-row">
          <button
            id="set-z-factor"
            type="button"
            className="btn btn-primary"
            disabled={
              localZFactor === "" || localZFactor === selectedNZS1170p5ZFactor
            }
            onClick={() => setSelectedNZS1170p5ZFactor(localZFactor)}
          >
            Set Z-factor
          </button>
          <button
            id="vs30-use-default"
            type="button"
            className="btn btn-primary default-button"
            disabled={
              selectedNZS1170p5ZFactor ===
              Number(nzs1170p5DefaultParams["z_factor"])
            }
            onClick={() => onClickDefaultZFactor()}
          >
            Use Default
          </button>
        </div>

        <div className="form-row">
          <button
            id="compute-nzs1170p5-code"
            type="button"
            className="btn btn-primary"
            disabled={invalidInputs()}
            onClick={() => computeNZS11705pCode()}
          >
            {computeButton.text}
          </button>
        </div>
      </form>
    </Fragment>
  );
};

export default NZS1170p5Section;
