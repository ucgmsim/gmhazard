import React, { useContext, Fragment, useEffect, useState } from "react";

import { v4 as uuidv4 } from "uuid";
import TextField from "@material-ui/core/TextField";
import InputAdornment from "@material-ui/core/InputAdornment";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import {
  APIQueryBuilder,
  disableScrollOnNumInput,
  handleErrors,
} from "utils/Utils";

const SiteConditions = () => {
  disableScrollOnNumInput();

  const {
    vs30,
    setVS30,
    defaultVS30,
    locationSetClick,
    setSelectedNZS1170p5SoilClass,
    setSelectedNZTASoilClass,
    nzs1170p5SoilClass,
    nztaSoilClass,
  } = useContext(GlobalContext);

  const { getTokenSilently } = useAuth0();

  const [localVS30, setLocalVS30] = useState("");
  const [localSetVs30Click, setLocalSetVs30Click] = useState(null);
  const [Vs30SetBtn, setVs30SetBtn] = useState({
    text: "Set Vs30",
    isFetching: false,
  });

  const onClickDefaultVS30 = () => {
    setVS30(defaultVS30);
    setLocalVS30(Number(defaultVS30).toFixed(1));
  };

  useEffect(() => {
    if (locationSetClick !== null && vs30 === defaultVS30 && vs30 !== "") {
      setLocalVS30(Number(defaultVS30).toFixed(1));
      // When we reset them
    } else if (vs30 === "" && defaultVS30 === "") {
      setLocalVS30("");
    }
  }, [vs30, defaultVS30, locationSetClick]);

  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getSoilClass = async () => {
      if (localSetVs30Click !== null) {
        try {
          const token = await getTokenSilently();

          setVs30SetBtn({
            text: <FontAwesomeIcon icon="spinner" spin />,
            isFetching: true,
          });

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_VS30_SOIL_CLASS_ENDPOINT +
              APIQueryBuilder({
                vs30: localVS30,
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

              setSelectedNZS1170p5SoilClass(
                nzs1170p5SoilClass.filter((obj) => {
                  return obj.value === responseData["nzs1170p5_soil_class"];
                })[0]
              );
              setSelectedNZTASoilClass(
                nztaSoilClass.filter((obj) => {
                  return obj.value === responseData["nzta_soil_class"];
                })[0]
              );

              setVS30(localVS30);
              setVs30SetBtn({
                text: "Set Vs30",
                isFetching: false,
              });
            })
            .catch((error) => {
              if (error.name !== "AbortError") {
                setVs30SetBtn({
                  text: "Set Vs30",
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

    getSoilClass();

    return () => {
      abortController.abort();
    };
  }, [localSetVs30Click]);

  return (
    <Fragment>
      <div className="form-row">
        <span>
          Edit V<sub>S30</sub> to use non-default value.
        </span>
      </div>
      <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group">
          <div className="d-flex align-items-center">
            <label id="label-vs30" className="control-label">
              V<sub>S30</sub>
            </label>
            <TextField
              className="flex-grow-1"
              type="number"
              value={localVS30}
              onChange={(e) => setLocalVS30(e.target.value)}
              variant={
                locationSetClick === null || vs30 === "" ? "filled" : "outlined"
              }
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    {CONSTANTS.ADORNMENT_METRE_PER_SECOND}
                  </InputAdornment>
                ),
                readOnly: locationSetClick === null || vs30 === "",
              }}
            />
          </div>
        </div>
      </form>
      <div className="form-row">
        <button
          type="button"
          className="btn btn-primary"
          disabled={locationSetClick === null || vs30 === ""}
          onClick={() => setLocalSetVs30Click(uuidv4())}
        >
          {Vs30SetBtn["text"]}
        </button>
        <button
          id="vs30-use-default"
          type="button"
          className="btn btn-primary default-button"
          disabled={vs30 === defaultVS30}
          onClick={() => onClickDefaultVS30()}
        >
          {CONSTANTS.USE_DEFAULT}
        </button>
      </div>
    </Fragment>
  );
};

export default SiteConditions;
