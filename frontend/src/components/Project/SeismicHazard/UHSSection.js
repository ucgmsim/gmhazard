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
    setProjectSelectedUHSRP,
    setProjectUHSGetClick,
    projectIMs,
    projectSiteSelectionGetClick,
  } = useContext(GlobalContext);

  const animatedComponents = makeAnimated();

  const [localRPs, setLocalRPs] = useState([]);
  const [rpOptions, setRPOptions] = useState([]);

  // Reset local variable to empty array when global changed to empty array (Reset)
  useEffect(() => {
    setLocalRPs([]);
    if (projectUHSRPs.length !== 0) {
      setRPOptions(createSelectArray(projectUHSRPs));
    } else {
      setRPOptions([]);
    }
  }, [projectSiteSelectionGetClick]);

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
            Return Period (years)
          </label>
          <Select
            id="uhs-return-period"
            closeMenuOnSelect={false}
            components={animatedComponents}
            isMulti
            placeholder={rpOptions.length === 0 ? "Not available" : "Select..."}
            value={localRPs.length === 0 ? [] : localRPs}
            onChange={(value) => setLocalRPs(value || [])}
            options={rpOptions}
            isDisabled={rpOptions.length === 0 || isPSANotInIMList(projectIMs)}
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
