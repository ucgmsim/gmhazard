import React, { useState, useContext, Fragment } from "react";

import { v4 as uuidv4 } from "uuid";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import { CustomSelect, GuideTooltip } from "components/common";

const DisaggregationSection = () => {
  const {
    projectDisagRPs,
    projectSelectedIM,
    projectSelectedIMPeriod,
    projectSelectedIMComponent,
    setProjectSelectedDisagRP,
    setProjectDisaggGetClick,
  } = useContext(GlobalContext);

  const [localSelectedRP, setLocalSelectedRP] = useState(null);

  const getDisagg = () => {
    setProjectSelectedDisagRP(localSelectedRP["value"]);
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
        <CustomSelect
          title={`${CONSTANTS.RETURN_PERIOD} ${CONSTANTS.YEARS}`}
          value={localSelectedRP}
          setSelect={setLocalSelectedRP}
          options={projectDisagRPs}
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
