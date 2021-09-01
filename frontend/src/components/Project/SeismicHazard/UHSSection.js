import React, { useState, useContext, useEffect, Fragment } from "react";

import Select from "react-select";
import makeAnimated from "react-select/animated";
import { v4 as uuidv4 } from "uuid";

import * as CONSTANTS from "constants/Constants";
import { GlobalContext } from "context";

import { createSelectArray, isPSANotInIMList } from "utils/Utils";
import { GuideTooltip } from "components/common";

const UHSSection = () => {
  const {
    projectUHSRPs,
    projectSelectedUHSRP,
    setProjectSelectedUHSRP,
    setProjectUHSGetClick,
    projectIMs,
  } = useContext(GlobalContext);

  const animatedComponents = makeAnimated();
  const [localRPs, setLocalRPs] = useState([]);

  const options = createSelectArray(projectUHSRPs);

  // Reset local variable to empty array when global changed to empty array (Reset)
  useEffect(() => {
    if (projectSelectedUHSRP.length === 0) {
      setLocalRPs([]);
    }
  }, [projectSelectedUHSRP]);

  const getUHS = () => {
    setProjectSelectedUHSRP(localRPs);
    setProjectUHSGetClick(uuidv4());
  };

  return (
    <Fragment>
      <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group form-section-title">
          Uniform Hazard Spectrum
          <GuideTooltip
            explanation={CONSTANTS.TOOLTIP_MESSAGES["PROJECT_UHS"]}
          />
        </div>
        <div className="form-group">
          <label
            id="label-uhs-return-period"
            htmlFor="uhs-return-period"
            className="control-label"
          >
            Return Period
          </label>
          <Select
            id="uhs-return-period"
            closeMenuOnSelect={false}
            components={animatedComponents}
            isMulti
            placeholder={options.length === 0 ? "Not available" : "Select..."}
            value={localRPs.length === 0 ? [] : localRPs}
            onChange={(value) => setLocalRPs(value || [])}
            options={options}
            isDisabled={options.length === 0 || isPSANotInIMList(projectIMs)}
            menuPlacement="auto"
            menuPortalTarget={document.body}
          />
        </div>
      </form>

      <div className="form-group">
        <button
          id="uhs-update-plot"
          type="button"
          className="btn btn-primary mt-2"
          disabled={localRPs.length === 0 || isPSANotInIMList(projectIMs)}
          onClick={() => getUHS()}
        >
          Get
        </button>
      </div>
    </Fragment>
  );
};

export default UHSSection;
