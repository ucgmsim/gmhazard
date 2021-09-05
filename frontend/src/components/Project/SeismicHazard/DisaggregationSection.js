import React, { useState, useContext, useEffect, Fragment } from "react";

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
    projectSelectedDisagRP,
    setProjectSelectedDisagRP,
    setProjectDisaggGetClick,
  } = useContext(GlobalContext);

  const [localSelectedRP, setLocalSelectedRP] = useState(null);

  // Reset local variable to null when global changed to null (Reset)
  useEffect(() => {
    if (projectSelectedDisagRP === null) {
      setLocalSelectedRP(null);
    }
  }, [projectSelectedDisagRP]);

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
        Disaggregation
        <GuideTooltip
          explanation={CONSTANTS.TOOLTIP_MESSAGES["PROJECT_DISAGG"]}
        />
      </div>
      <div className="form-group">
        <CustomSelect
          title="Return Period"
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
          Get
        </button>
      </div>
    </Fragment>
  );
};

export default DisaggregationSection;
