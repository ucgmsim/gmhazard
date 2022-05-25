import React, { Fragment, useState, useEffect, useContext } from "react";

import $ from "jquery";
import Select from "react-select";
import { v4 as uuidv4 } from "uuid";
import makeAnimated from "react-select/animated";
import { Accordion, Card } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import { CustomSelect, IMCustomSelect, GuideTooltip } from "components/common";
import {
  renderSigfigs,
  sortIMs,
  handleErrors,
  APIQueryBuilder,
  createSelectArray,
  splitIMPeriods,
  combineIMwithPeriod,
} from "utils/Utils";

import "assets/style/GMSForm.css";

const GMSForm = () => {
  const { getTokenSilently } = useAuth0();

  const {
    locationSetClick,
    selectedEnsemble,
    station,
    vs30,
    setGMSComputeClick,
    setGMSIMLevel,
    setGMSExcdRate,
    setGMSIMVector,
    setGMSRadio,
    setGMSIMType,
    setGMSIMPeriod,
    setGMSNum,
    setGMSReplicates,
    setGMSWeights,
    setGMSMwMin,
    setGMSMwMax,
    setGMSRrupMin,
    setGMSRrupMax,
    setGMSVS30Min,
    setGMSVS30Max,
    setGMSSFMin,
    setGMSSFMax,
    setGMSDatabase,
  } = useContext(GlobalContext);

  const animatedComponents = makeAnimated();

  // For react-select components (Dropdown)
  const [availableIMs, setAvailableIMs] = useState([]);
  const [availablePeriods, setAvailablePeriods] = useState([]);
  const [localIMVectors, setLocalIMVectors] = useState([]);
  const [localIMVectorsOptions, setLocalIMVectorsOptions] = useState([]);
  const [availableDatabases, setAvailableDatabases] = useState([]);

  // For advanced tab's arrow toggle
  const [arrowSets, setArrowSets] = useState({
    true: <FontAwesomeIcon icon="caret-down" size="2x" />,
    false: <FontAwesomeIcon icon="caret-up" size="2x" />,
  });
  const [arrow, setArrow] = useState(true);

  // GMS form selected inputs
  const [selectedIMType, setSelectedIMType] = useState(null);
  const [selectedIMPeriod, setSelectedIMPeriod] = useState(null);
  // IM / Exceedance rate level radio and inputs
  const [localIMExdRateRadio, setLocalImExdRateRadio] = useState("im-level");
  const [localIMLevel, setLocalIMLevel] = useState("");
  const [localExcdRate, setLocalExcdRate] = useState("");
  const [localIMVector, setLocalIMVector] = useState([]);
  const [localNumGMS, setLocalNumGMS] = useState("");
  // Inputs under the Advanced tab
  const [localWeights, setLocalWeights] = useState({});
  const [localDatabase, setLocalDatabase] = useState({
    value: "nga_west_2",
    label: "nga_west_2",
  });
  const [localReplicates, setLocalReplicates] = useState(1);
  // Causal params bounds under the advanced
  const [localMwMin, setLocalMwMin] = useState("");
  const [localMwMax, setLocalMwMax] = useState("");
  const [localRrupMin, setLocalRrupMin] = useState("");
  const [localRrupMax, setLocalRrupMax] = useState("");
  const [localVS30Min, setLocalVS30Min] = useState("");
  const [localVS30Max, setLocalVS30Max] = useState("");
  const [localSFMin, setLocalSFMin] = useState("");
  const [localSFMax, setLocalSFMax] = useState("");
  // IM Vector weights table
  const [localWeightsTable, setLocalWeightsTable] = useState([]);

  // For Causal params bounds data fetcher
  const [getPreGMParamsClick, setGetPreGMParamsClick] = useState(null);
  const [getPreGMButton, setGetPreGMButton] = useState({
    text: `${CONSTANTS.GET_CAUSAL_PARAMS_BOUNDS}`,
    isFetching: false,
  });

  // For IM Vector weights data fetcher
  const [getIMWeightsClick, setGetIMWeightsClick] = useState(null);
  const [getIMWeightMButton, setGetIMWeightMButton] = useState({
    text: `${CONSTANTS.GET_IM_VECTOR_WEIGHTS}`,
    isFetching: false,
  });

  // Reset selected inputs as location got changed
  useEffect(() => {
    if (locationSetClick !== null) {
      setLocalIMLevel("");
      setLocalExcdRate("");
      setLocalImExdRateRadio("im-level");
      setLocalIMVector([]);
      setLocalNumGMS("");
      setLocalMwMin("");
      setLocalMwMax("");
      setLocalRrupMin("");
      setLocalRrupMax("");
      setLocalVS30Min("");
      setLocalVS30Max("");
      setLocalSFMin("");
      setLocalSFMax("");
      setLocalWeightsTable([]);
      setLocalReplicates(1);
    }
  }, [locationSetClick]);

  // Get available GMS's IMs & IM Vectors
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    // To prevent recomputing by itself
    setGMSComputeClick(null);

    const getGMSIMs = async () => {
      try {
        const token = await getTokenSilently();

        await fetch(
          CONSTANTS.INTERMEDIATE_API_URL +
            CONSTANTS.CORE_API_GMS_DATASETS_ENDPOINT,
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
            const gmDatasetIDs = Object.keys(responseData);

            setAvailableDatabases(createSelectArray(gmDatasetIDs));

            return await fetch(
              CONSTANTS.INTERMEDIATE_API_URL +
                CONSTANTS.CORE_API_GMS_IMS_ENDPOINT_ENDPOINT +
                APIQueryBuilder({
                  ensemble_id: selectedEnsemble,
                  gm_dataset_ids: `${gmDatasetIDs.join(",")}`,
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

                const splitIMs = splitIMPeriods(responseData["ims"]);
                const periods = [...splitIMs["Periods"]];

                setAvailableIMs(sortIMs([...new Set(splitIMs["IMs"])]));
                setAvailablePeriods(periods.sort((a, b) => a - b));

                setLocalIMVectors(
                  createSelectArray(sortIMs(responseData["ims"]))
                );
              })
              // Catch error for the second fetch, IMs
              .catch((error) => {
                console.log(error);
              });
          })
          // Catch error for the first fetch, GM Dataset
          .catch((error) => {
            console.log(error);
          });
      } catch (error) {
        console.log(error);
      }
    };
    getGMSIMs();

    return () => {
      abortController.abort();
    };
  }, []);

  // Get default causal params
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const defaultCausalParams = async () => {
      if (getPreGMParamsClick !== null) {
        let queryString = APIQueryBuilder({
          ensemble_id: selectedEnsemble,
          station: station,
          IM_j: combineIMwithPeriod(
            selectedIMType["value"],
            selectedIMPeriod !== null ? selectedIMPeriod["value"] : null
          ),
          user_vs30: vs30,
        });
        if (localIMExdRateRadio === "im-level") {
          queryString += `&im_level=${localIMLevel}`;
        } else if (localIMExdRateRadio === "exceedance-rate") {
          queryString += `&exceedance=${localExcdRate}`;
        }

        try {
          const token = await getTokenSilently();

          setGetPreGMButton({
            text: <FontAwesomeIcon icon="spinner" spin />,
            isFetching: true,
          });

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT +
              queryString,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          )
            .then(async function (response) {
              const responseData = await response.json();

              setLocalMwMin(responseData.mw_low);
              setLocalMwMax(responseData.mw_high);
              setLocalRrupMin(
                renderSigfigs(responseData.rrup_low, CONSTANTS.APP_UI_SIGFIGS)
              );
              setLocalRrupMax(
                renderSigfigs(responseData.rrup_high, CONSTANTS.APP_UI_SIGFIGS)
              );
              setLocalVS30Min(
                renderSigfigs(responseData.vs30_low, CONSTANTS.APP_UI_SIGFIGS)
              );
              setLocalVS30Max(
                renderSigfigs(responseData.vs30_high, CONSTANTS.APP_UI_SIGFIGS)
              );
              setLocalSFMin(responseData.sf_low);
              setLocalSFMax(responseData.sf_high);

              setGetPreGMButton({
                text: `${CONSTANTS.GET_CAUSAL_PARAMS_BOUNDS}`,
                isFetching: false,
              });
            })
            .catch(function (error) {
              if (error.name !== "AbortError") {
                setGetPreGMButton({
                  text: `${CONSTANTS.GET_CAUSAL_PARAMS_BOUNDS}`,
                  isFetching: false,
                });
              }
              console.log(error);
            });
        } catch (error) {
          console.log(error);
        }
      }
    };

    defaultCausalParams();

    return () => {
      abortController.abort();
    };
  }, [getPreGMParamsClick]);

  // Get a default weight for each IM Vector.
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const defaultIMWeights = async () => {
      if (localIMVector.length !== 0 && getIMWeightsClick !== null) {
        let queryString =
          APIQueryBuilder({
            IM_j: combineIMwithPeriod(
              selectedIMType["value"],
              selectedIMPeriod !== null ? selectedIMPeriod["value"] : null
            ),
          }) + "&IMs=";

        // Create a new array from an object to contain only values
        const newIMVector = Array.from(localIMVector, (x) => x.value);
        sortIMs(newIMVector).forEach((IM) => (queryString += IM + ","));
        queryString = queryString.slice(0, -1);

        try {
          const token = await getTokenSilently();

          setGetIMWeightMButton({
            text: <FontAwesomeIcon icon="spinner" spin />,
            isFetching: true,
          });

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_GMS_DEFAULT_IM_WEIGHTS_ENDPOINT +
              queryString,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          )
            .then(async function (response) {
              const responseData = await response.json();
              setLocalWeights(responseData);

              setGetIMWeightMButton({
                text: `${CONSTANTS.GET_IM_VECTOR_WEIGHTS}`,
                isFetching: false,
              });
            })
            .catch(function (error) {
              if (error.name !== "AbortError") {
                setGetIMWeightMButton({
                  text: `${CONSTANTS.GET_IM_VECTOR_WEIGHTS}`,
                  isFetching: false,
                });
              }
              console.log(error);
            });
        } catch (error) {
          console.log(error);
        }
      }
    };

    defaultIMWeights();

    return () => {
      abortController.abort();
    };
  }, [getIMWeightsClick]);

  // IM Vector -> Create Weights Table inside the Advanced tab
  useEffect(() => {
    if (Object.keys(localWeights).length !== 0) {
      setLocalWeightsTable(
        localIMVector.map((imVector) => {
          return (
            <tr id={"weight-row-" + imVector.value} key={imVector.value}>
              <td>{imVector.value}</td>
              <td className="text-center">
                {renderSigfigs(
                  localWeights[imVector.value],
                  CONSTANTS.APP_UI_SIGFIGS
                )}
              </td>
            </tr>
          );
        })
      );
    }
    /*
      Reset weights table under the Advanced tab
      if a user removes all IM Vectors.
    */
    if (localIMVector.length === 0) {
      setLocalWeightsTable([]);
    }
  }, [localIMVector, localWeights]);

  // Disable table's input
  useEffect(() => {
    if (
      selectedIMType !== null &&
      (localIMLevel !== "" || localExcdRate !== "")
    ) {
      $("table input").prop("disabled", false);
    } else {
      $("table input").prop("disabled", true);
    }
  }, [selectedIMType, localIMLevel, localExcdRate]);

  /*
    Filter out the chosen IM Type 
    if it exists in the selected IM Vectors
  */
  useEffect(() => {
    if (selectedIMType !== null && localIMVector.length !== 0) {
      // IM is not pSA so no need vibration period
      if (selectedIMType["value"] !== "pSA") {
        setLocalIMVector(
          localIMVector.filter(
            (vector) => vector.value !== selectedIMType["value"]
          )
        );
        // IM is pSA so need vibration period
      } else {
        if (selectedIMPeriod !== null) {
          setLocalIMVector(
            localIMVector.filter(
              (vector) =>
                vector.value !==
                combineIMwithPeriod(
                  selectedIMType["value"],
                  selectedIMPeriod["value"]
                )
            )
          );
        }
      }
    }
  }, [selectedIMType, selectedIMPeriod]);

  /* 
    Filter the possible IM Vector options 
    Similar to above useEffect but this is for options
    not selected IM Vectors
  */
  useEffect(() => {
    if (selectedIMType !== null && localIMVectors.length !== 0) {
      // IM is not pSA so no need vibration period
      if (selectedIMType["value"] !== "pSA") {
        setLocalIMVectorsOptions(
          localIMVectors.filter(
            (vector) => vector.value !== selectedIMType["value"]
          )
        );
        // IM is pSA so need vibration period
      } else {
        if (selectedIMPeriod !== null) {
          setLocalIMVectorsOptions(
            localIMVectors.filter(
              (vector) =>
                vector.value !==
                combineIMwithPeriod(
                  selectedIMType["value"],
                  selectedIMPeriod["value"]
                )
            )
          );
        }
      }
    }
  }, [selectedIMType, selectedIMPeriod]);

  const invalidInputs = () => {
    // Input validator for Period when IM is pSA
    let imIsInvalid = false;
    if (selectedIMType !== null) {
      imIsInvalid =
        selectedIMType["value"] === "pSA" && selectedIMPeriod === null;
    }
    return (
      imIsInvalid ||
      selectedEnsemble === ("" || null) ||
      station === ("" || null) ||
      selectedIMType === null ||
      localIMVector.length === 0 ||
      localNumGMS === ("" || null) ||
      localReplicates === ("" || null) ||
      Object.keys(localWeights).length === 0 ||
      localMwMin === "" ||
      localMwMax === "" ||
      localRrupMin === "" ||
      localRrupMax === "" ||
      localVS30Min === "" ||
      localVS30Max === "" ||
      (localIMExdRateRadio === "exceedance-rate" && localExcdRate === "") ||
      (localIMExdRateRadio === "im-level" && localIMLevel === "")
    );
  };

  const invalidIMVectors = () => {
    return localIMVector.length === 0;
  };

  const invalidGetPreGMParams = () => {
    if (localIMExdRateRadio === "im-level") {
      if (selectedIMType !== null) {
        if (
          (selectedIMType["value"] !== "pSA" ||
            (selectedIMType["value"] === "pSA" && selectedIMPeriod !== null)) &&
          localIMLevel !== ""
        ) {
          return false;
        }
      }
    } else if (localIMExdRateRadio === "exceedance-rate") {
      if (selectedIMType !== null) {
        if (
          (selectedIMType["value"] !== "pSA" ||
            (selectedIMType["value"] === "pSA" && selectedIMPeriod !== null)) &&
          localExcdRate !== ""
        ) {
          return false;
        }
      }
    }

    return true;
  };

  const computeGMS = () => {
    localIMExdRateRadio === "im-level"
      ? setGMSIMLevel(localIMLevel)
      : setGMSExcdRate(localExcdRate);
    setGMSIMVector(localIMVector);
    setGMSRadio(localIMExdRateRadio);
    setGMSIMType(selectedIMType["value"]);
    if (selectedIMPeriod !== null) {
      setGMSIMPeriod(selectedIMPeriod["value"]);
    }
    setGMSNum(localNumGMS);
    setGMSReplicates(localReplicates);
    setGMSWeights(localWeights);
    setGMSMwMin(localMwMin);
    setGMSMwMax(localMwMax);
    setGMSRrupMin(localRrupMin);
    setGMSRrupMax(localRrupMax);
    setGMSVS30Min(localVS30Min);
    setGMSVS30Max(localVS30Max);
    setGMSSFMin(localSFMin);
    setGMSSFMax(localSFMax);
    setGMSDatabase(localDatabase["value"]);
    setGMSComputeClick(uuidv4());
  };

  const preventEnterKey = (e) => {
    e.key === "Enter" && e.preventDefault();
  };

  return (
    <Fragment>
      <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group form-section-title">
          {CONSTANTS.GROUND_MOTION_SELECTION}
        </div>

        <div className="im-custom-form-group">
          <CustomSelect
            title={CONSTANTS.GMS_CONDITIONING_IM_NAME}
            setSelect={setSelectedIMType}
            options={availableIMs}
            guideMSG={
              CONSTANTS.TOOLTIP_MESSAGES["HAZARD_GMS_CONDITIONING_IM_NAME"]
            }
          />
        </div>

        <div className="im-custom-form-group">
          <IMCustomSelect
            title={`${CONSTANTS.VIBRATION_PERIOD} ${CONSTANTS.SECONDS}`}
            setSelect={setSelectedIMPeriod}
            options={availablePeriods}
            selectedIM={selectedIMType}
            guideMSG={CONSTANTS.TOOLTIP_MESSAGES["GMS_VIBRATION_PERIOD"]}
            placeholder={"Please select the Conditioning IM Name first."}
          />
        </div>

        <div className="form-group">
          <label
            id="label-im-level"
            htmlFor="im-level"
            className="control-label"
          >
            IM / {CONSTANTS.EXCEEDANCE_RATE_LEVEL}
          </label>
          <GuideTooltip
            explanation={
              CONSTANTS.TOOLTIP_MESSAGES["HAZARD_GMS_IM_LEVEL_EXCEEDANCE_RATE"]
            }
          />
          <div>
            <div className="form-check form-check-inline">
              <input
                className="form-check-input"
                type="radio"
                name="inline-radio-options"
                id="im-level-radio"
                value="im-level"
                checked={localIMExdRateRadio === "im-level"}
                onChange={(e) => setLocalImExdRateRadio(e.target.value)}
              />
              <label className="form-check-label" htmlFor="im-level">
                IM
              </label>
            </div>
            <div className="form-check form-check-inline">
              <input
                className="form-check-input"
                type="radio"
                name="inline-radio-options"
                id="exceedance-rate-radio"
                value="exceedance-rate"
                checked={localIMExdRateRadio === "exceedance-rate"}
                onChange={(e) => setLocalImExdRateRadio(e.target.value)}
              />
              <label className="form-check-label" htmlFor="exceedance-rate">
                Exceedance Rate
              </label>
            </div>
          </div>
          {localIMExdRateRadio === "im-level" ? (
            <input
              id="im-level"
              type="number"
              onChange={(e) => setLocalIMLevel(e.target.value)}
              className="form-control"
              value={localIMLevel}
              onKeyPress={(e) => preventEnterKey(e)}
            />
          ) : (
            <input
              id="exceedance-rate"
              type="number"
              onChange={(e) => setLocalExcdRate(e.target.value)}
              className="form-control"
              value={localExcdRate}
              onKeyPress={(e) => preventEnterKey(e)}
            />
          )}
        </div>

        <div className="form-row div-with-status">
          <button
            id="get-pre-gm-params-btn"
            type="button"
            className="btn btn-primary"
            onClick={() => setGetPreGMParamsClick(uuidv4())}
            disabled={
              invalidGetPreGMParams() || getPreGMButton.isFetching === true
            }
          >
            {getPreGMButton.text}
          </button>
          <span className="status-text">
            {getPreGMButton.isFetching ? "It takes about 1 minute..." : null}
          </span>
        </div>

        <div className="im-custom-form-group">
          <label
            id="label-im-vectors"
            htmlFor="im-vector"
            className="control-label"
          >
            {CONSTANTS.IM_VECTOR}
          </label>
          <GuideTooltip
            explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_GMS_IM_VECTOR"]}
          />
          <Select
            id="im-vector"
            closeMenuOnSelect={false}
            components={animatedComponents}
            isMulti
            value={localIMVector}
            onChange={(value) => setLocalIMVector(value || [])}
            options={localIMVectorsOptions}
            isDisabled={localIMVectors.length === 0}
            menuPlacement="auto"
            menuPortalTarget={document.body}
          />
        </div>

        <div className="form-row">
          <button
            id="get-im-vector-weights-btn"
            className="btn btn-primary"
            onClick={() => setGetIMWeightsClick(uuidv4())}
            disabled={
              invalidIMVectors() || getIMWeightMButton.isFetching === true
            }
          >
            {getIMWeightMButton.text}
          </button>
        </div>

        <div className="form-group">
          <label id="label-num-gms" htmlFor="num-gms" className="control-label">
            Number of Ground Motions
          </label>
          <GuideTooltip
            explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_GMS_NUM_GMS"]}
          />
          <input
            id="num-gms"
            type="number"
            onChange={(e) => setLocalNumGMS(e.target.value)}
            className="form-control"
            value={localNumGMS}
            onKeyPress={(e) => preventEnterKey(e)}
          />
        </div>

        <div className="form-group">
          <button
            className="btn btn-primary"
            onClick={() => computeGMS()}
            disabled={invalidInputs()}
          >
            {CONSTANTS.COMPUTE_BUTTON}
          </button>
        </div>

        <Accordion>
          <Card>
            <Card.Header className="advanced-toggle-header">
              <span>
                Advanced
                <GuideTooltip
                  explanation={
                    CONSTANTS.TOOLTIP_MESSAGES["HAZARD_GMS_ADVANCED"]
                  }
                />
              </span>
              <Accordion.Toggle
                as="span"
                eventKey="0"
                onClick={() => setArrow(!arrow)}
              >
                {arrowSets[arrow]}
              </Accordion.Toggle>
            </Card.Header>
            <Accordion.Collapse eventKey="0">
              <Card.Body>
                <div className="form-group">
                  <label
                    id="label-causal-parameters"
                    htmlFor="causal-parameters"
                    className="control-label"
                  >
                    Causal parameters bounds
                  </label>
                  <GuideTooltip
                    explanation={
                      CONSTANTS.TOOLTIP_MESSAGES[
                        "HAZARD_GMS_CAUSAL_PARAMS_BOUNDS"
                      ]
                    }
                  />
                  <table className="table table-bordered">
                    <thead>
                      <tr>
                        <th className="var-name" scope="col"></th>
                        <th className="min-value" scope="col">
                          Min
                        </th>
                        <th className="min-value" scope="col">
                          Max
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <th scope="row">Mw</th>
                        <td>
                          <input
                            type="text"
                            value={localMwMin}
                            onChange={(e) => setLocalMwMin(e.target.value)}
                            onKeyPress={(e) => preventEnterKey(e)}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={localMwMax}
                            onChange={(e) => setLocalMwMax(e.target.value)}
                            onKeyPress={(e) => preventEnterKey(e)}
                          />
                        </td>
                      </tr>
                      <tr>
                        <th scope="row">Rrup (km)</th>
                        <td>
                          <input
                            type="text"
                            value={localRrupMin}
                            onChange={(e) => setLocalRrupMin(e.target.value)}
                            onKeyPress={(e) => preventEnterKey(e)}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={localRrupMax}
                            onChange={(e) => setLocalRrupMax(e.target.value)}
                            onKeyPress={(e) => preventEnterKey(e)}
                          />
                        </td>
                      </tr>
                      <tr>
                        <th scope="row">
                          V<sub>S30</sub> (m/s)
                        </th>
                        <td>
                          <input
                            type="text"
                            value={localVS30Min}
                            onChange={(e) => setLocalVS30Min(e.target.value)}
                            onKeyPress={(e) => preventEnterKey(e)}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={localVS30Max}
                            onChange={(e) => setLocalVS30Max(e.target.value)}
                            onKeyPress={(e) => preventEnterKey(e)}
                          />
                        </td>
                      </tr>
                      <tr>
                        <th scope="row">SF</th>
                        <td>
                          <input
                            type="text"
                            value={localSFMin}
                            onChange={(e) => setLocalSFMin(e.target.value)}
                            onKeyPress={(e) => preventEnterKey(e)}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={localSFMax}
                            onChange={(e) => setLocalSFMax(e.target.value)}
                            onKeyPress={(e) => preventEnterKey(e)}
                          />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div className="form-group">
                  <label
                    id="label-weights"
                    htmlFor="weights"
                    className="control-label"
                  >
                    Weights
                  </label>
                  <GuideTooltip
                    explanation={
                      CONSTANTS.TOOLTIP_MESSAGES["HAZARD_GMS_WEIGHTS"]
                    }
                  />
                  <table className="table table-bordered">
                    <thead>
                      <tr>
                        <th scope="col"></th>
                        <th className="text-center" scope="col">
                          Weights
                        </th>
                      </tr>
                    </thead>
                    <tbody>{localWeightsTable}</tbody>
                  </table>
                </div>

                {/* Options need to be changed but we do not have any yet */}
                <div className="im-custom-form-group">
                  <label
                    id="label-gms-db"
                    htmlFor="database"
                    className="control-label"
                  >
                    Database
                  </label>
                  <GuideTooltip
                    explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_GMS_DB"]}
                  />
                  <Select
                    id="database"
                    onChange={setLocalDatabase}
                    value={localDatabase}
                    isDisabled
                    options={availableDatabases}
                    menuPlacement="auto"
                  />
                </div>

                <div className="form-group">
                  <label
                    id="label-replicates"
                    htmlFor="replicates"
                    className="control-label"
                  >
                    Replicates
                  </label>
                  <GuideTooltip
                    explanation={
                      CONSTANTS.TOOLTIP_MESSAGES["HAZARD_GMS_REPLICATES"]
                    }
                  />
                  <input
                    id="replicates"
                    type="number"
                    onChange={(e) => setLocalReplicates(e.target.value)}
                    className="form-control"
                    value={localReplicates}
                    onKeyPress={(e) => preventEnterKey(e)}
                  />
                </div>
              </Card.Body>
            </Accordion.Collapse>
          </Card>
        </Accordion>
      </form>
    </Fragment>
  );
};

export default GMSForm;
