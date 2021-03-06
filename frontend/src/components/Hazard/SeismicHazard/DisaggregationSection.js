import React, { useState, useContext, useEffect, Fragment } from "react";

import { v4 as uuidv4 } from "uuid";
import TextField from "@material-ui/core/TextField";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import { GuideTooltip } from "components/common";
import { disableScrollOnNumInput } from "utils/Utils";

const DisaggregationSection = () => {
  disableScrollOnNumInput();

  const {
    locationSetClick,
    setDisaggComputeClick,
    selectedIM,
    selectedIMPeriod,
    setDisaggAnnualProb,
    selectedIMComponent,
  } = useContext(GlobalContext);

  const [inputDisaggDisabled, setInputDisaggDisabled] = useState(true);

  const [localExceedance, setLocalExceedance] = useState("");

  // Disable input field if IM is not selected
  useEffect(() => {
    setInputDisaggDisabled(selectedIM === null);
  }, [selectedIM]);

  // A user clicked the Set button in site selection, reset values
  useEffect(() => {
    if (locationSetClick !== null) {
      setLocalExceedance("");
    }
  }, [locationSetClick]);

  const invalidInputsWithNonpSA = () => {
    return !(
      selectedIM !== null &&
      localExceedance > 0 &&
      localExceedance < 1 &&
      selectedIMComponent !== null
    );
  };

  const invalidInputWithpSA = () => {
    return selectedIM === "pSA" && selectedIMPeriod === null;
  };

  return (
    <Fragment>
      <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group form-section-title">
        {CONSTANTS.DISAGGREGATION}
          <GuideTooltip
            explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_DISAGG"]}
          />
        </div>
        <div className="form-group">
          <label
            id="label-annual-rate"
            htmlFor="disagg-annual-rate"
            className="control-label"
          >
            {CONSTANTS.ANNUAL_EXCEEDANCE_RATE}
          </label>
          <TextField
            id="disagg-annual-rate"
            type="number"
            value={localExceedance}
            onChange={(e) => setLocalExceedance(e.target.value)}
            placeholder="(0, 1)"
            fullWidth
            variant={inputDisaggDisabled ? "filled" : "outlined"}
            InputProps={{
              readOnly: inputDisaggDisabled,
            }}
            error={
              (localExceedance > 0 && localExceedance < 1) ||
              localExceedance === ""
                ? false
                : true
            }
            helperText={
              (localExceedance > 0 && localExceedance < 1) ||
              localExceedance === ""
                ? " "
                : `${CONSTANTS.ANNUAL_EXCEEDANCE_RATE_HELPER_TEXT}`
            }
          />
        </div>

        <div className="form-group">
          <button
            id="prob-update"
            type="button"
            className="btn btn-primary"
            disabled={invalidInputsWithNonpSA() || invalidInputWithpSA()}
            onClick={() => {
              setDisaggAnnualProb(localExceedance);
              setDisaggComputeClick(uuidv4());
            }}
          >
            {CONSTANTS.COMPUTE_BUTTON}
          </button>
        </div>
      </form>
    </Fragment>
  );
};

export default DisaggregationSection;
