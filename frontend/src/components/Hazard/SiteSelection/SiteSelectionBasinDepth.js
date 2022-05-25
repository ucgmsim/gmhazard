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

const SiteSelectionBasinDepth = () => {
  disableScrollOnNumInput();

  const {
    locationSetClick,
    Z1p0,
    setZ1p0,
    defaultZ1p0,
    Z2p5,
    setZ2p5,
    defaultZ2p5,
  } = useContext(GlobalContext);

  const [localZ1p0, setLocalZ1p0] = useState("");
  const [localSetZ1p0Click, setLocalSetZ1p0Click] = useState(null);
  const [Z1p0SetBtn, setZ1p0SetBtn] = useState({
    text: "Set Z1.0",
    isFetching: false,
  });

  const [localZ2p5, setLocalZ2p5] = useState("");
  const [localSetZ2p5Click, setLocalSetZ2p5Click] = useState(null);
  const [Z2p5SetBtn, setZ2p5SetBtn] = useState({
    text: "Set Z2.5",
    isFetching: false,
  });

  const onClickDefaultZ1p0 = () => {
    setZ1p0(defaultZ1p0);
    setLocalZ1p0(Number(defaultZ1p0).toFixed(1));
  };

  const onClickDefaultZ2p5 = () => {
    setZ2p5(defaultZ2p5);
    setLocalZ2p5(Number(defaultZ2p5).toFixed(1));
  };

  return (
    <Fragment>
      <div className="form-row">
        <span>
          Edit Z<sub>1.0</sub> and/or Z<sub>2.5</sub> to use non-default value.
        </span>
      </div>
      <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group">
          <div className="d-flex align-items-center">
            <label id="label-z-1p0" className="control-label">
              Z<sub>1.0</sub>
            </label>
            <TextField
              className="flex-grow-1"
              type="number"
              value={localZ1p0}
              onChange={(e) => setLocalZ1p0(e.target.value)}
              variant={
                locationSetClick === null || Z1p0 === "" ? "filled" : "outlined"
              }
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    {CONSTANTS.ADORNMENT_KILOMETRE}
                  </InputAdornment>
                ),
                readOnly: locationSetClick === null || Z1p0 === "",
              }}
            />
          </div>
        </div>
      </form>
      <div className="form-row">
        <button
          type="button"
          className="btn btn-primary"
          disabled={locationSetClick === null || Z1p0 === ""}
          onClick={() => setLocalSetZ1p0Click(uuidv4())}
        >
          {Z1p0SetBtn["text"]}
        </button>
        <button
          id="Z1p0-use-default"
          type="button"
          className="btn btn-primary default-button"
          disabled={Z1p0 === defaultZ1p0}
          onClick={() => onClickDefaultZ1p0()}
        >
          {CONSTANTS.USE_DEFAULT}
        </button>
      </div>

      <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group">
          <div className="d-flex align-items-center">
            <label id="label-z-2p5" className="control-label">
              Z<sub>2.5</sub>
            </label>
            <TextField
              className="flex-grow-1"
              type="number"
              value={localZ2p5}
              onChange={(e) => setLocalZ2p5(e.target.value)}
              variant={
                locationSetClick === null || Z2p5 === "" ? "filled" : "outlined"
              }
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    {CONSTANTS.ADORNMENT_KILOMETRE}
                  </InputAdornment>
                ),
                readOnly: locationSetClick === null || Z2p5 === "",
              }}
            />
          </div>
        </div>
      </form>
      <div className="form-row">
        <button
          type="button"
          className="btn btn-primary"
          disabled={locationSetClick === null || Z2p5 === ""}
          onClick={() => setLocalSetZ2p5Click(uuidv4())}
        >
          {Z2p5SetBtn["text"]}
        </button>
        <button
          id="vs30-use-default"
          type="button"
          className="btn btn-primary default-button"
          disabled={Z2p5 === defaultZ2p5}
          onClick={() => onClickDefaultZ2p5()}
        >
          {CONSTANTS.USE_DEFAULT}
        </button>
      </div>
    </Fragment>
  );
};

export default SiteSelectionBasinDepth;
