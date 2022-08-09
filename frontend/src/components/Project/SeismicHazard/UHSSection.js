import React, { useState, useContext, useEffect, Fragment } from "react";

import Select from "react-select";
import { v4 as uuidv4 } from "uuid";
import makeAnimated from "react-select/animated";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import { GuideTooltip } from "components/common";
import { createAnnualExceedanceArray, isPSANotInIMList } from "utils/Utils";

const UHSSection = () => {
  const {
    projectIMs,
    projectUHSRPs,
    setProjectUHSGetClick,
    setProjectSelectedUHSRP,
    projectSiteSelectionGetClick,
  } = useContext(GlobalContext);

  const animatedComponents = makeAnimated();

  const [localRPs, setLocalRPs] = useState([]);
  const [rpOptions, setRPOptions] = useState([]);

  // Reset local variable to empty array when global changed to empty array (Reset)
  useEffect(() => {
    setLocalRPs([]);
    if (projectUHSRPs.length !== 0) {
      setRPOptions(createAnnualExceedanceArray(projectUHSRPs));
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
          {CONSTANTS.UNIFORM_HAZARD_SPECTRUM}
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
            {CONSTANTS.ANNUAL_EXCEEDANCE_RATE} (yr<sup>-1</sup>)
          </label>
          <Select
            id="uhs-return-period"
            closeMenuOnSelect={false}
            components={animatedComponents}
            isMulti
            placeholder={
              rpOptions.length === 0
                ? `${CONSTANTS.PLACEHOLDER_NOT_AVAILABLE}`
                : `${CONSTANTS.PLACEHOLDER_SELECT_SIGN}`
            }
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
          {CONSTANTS.GET_BUTTON}
        </button>
      </div>
    </Fragment>
  );
};

export default UHSSection;
