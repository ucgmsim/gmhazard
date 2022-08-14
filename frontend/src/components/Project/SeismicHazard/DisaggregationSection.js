import React, { useState, useContext, Fragment } from "react";

import Select from "react-select";
import { v4 as uuidv4 } from "uuid";
import makeAnimated from "react-select/animated";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import { GuideTooltip } from "components/common";
import { createAnnualExceedanceArray } from "utils/Utils";

const DisaggregationSection = () => {
  const {
    projectDisagRPs,
    projectSelectedIM,
    projectSelectedIMPeriod,
    projectSelectedIMComponent,
    setProjectSelectedDisagRP,
    setProjectDisaggGetClick,
  } = useContext(GlobalContext);

  const animatedComponents = makeAnimated();

  const [localSelectedRP, setLocalSelectedRP] = useState(null);

  const getDisagg = () => {
    setProjectSelectedDisagRP(localSelectedRP);
    setProjectDisaggGetClick(uuidv4());
  };

  const invalidInputsWithNonpSA = () => {
    return !(
      projectSelectedIM !== null &&
      localSelectedRP !== null &&
      projectSelectedIMComponent !== null
    );
  };

  const invalidInputWithpSA = () => {
    return projectSelectedIM === "pSA" && projectSelectedIMPeriod === null;
  };

  return (
    <Fragment>
      <div className="form-group form-section-title">
        {CONSTANTS.DISAGGREGATION}
        <GuideTooltip
          explanation={CONSTANTS.TOOLTIP_MESSAGES["PROJECT_DISAGG"]}
        />
      </div>
      <div className="form-group">
        <label className="control-label" htmlFor="disagg-return-period">
          {CONSTANTS.ANNUAL_EXCEEDANCE_RATE} (yr<sup>-1</sup>)
        </label>
        <Select
          id="disagg-return-period"
          closeMenuOnSelect={false}
          components={animatedComponents}
          isMulti
          placeholder={
            projectDisagRPs.length === 0
              ? `${CONSTANTS.PLACEHOLDER_NOT_AVAILABLE}`
              : `${CONSTANTS.PLACEHOLDER_SELECT_SIGN}`
          }
          onChange={(value) => setLocalSelectedRP(value || [])}
          options={createAnnualExceedanceArray(projectDisagRPs)}
          isDisabled={projectDisagRPs.length === 0}
          menuPlacement="auto"
          menuPortalTarget={document.body}
        />
      </div>

      <div className="form-group">
        <button
          id="project-hazard-curve-get-btn"
          type="button"
          className="btn btn-primary"
          disabled={invalidInputsWithNonpSA() || invalidInputWithpSA()}
          onClick={() => getDisagg()}
        >
          {CONSTANTS.GET_BUTTON}
        </button>
      </div>
    </Fragment>
  );
};

export default DisaggregationSection;
