import React, { Fragment, useState, useContext } from "react";

import { v4 as uuidv4 } from "uuid";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import { CustomSelect, GuideTooltip } from "components/common";

import "assets/style/GMSForm.css";

const GMSForm = () => {
  const {
    projectGMSIMTypes,
    projectGMSIMPeriods,
    projectGMSExceedances,
    projectGMSIMVectors,
    setProjectGMSGetClick,
    setProjectGMSConditionIM,
    setProjectGMSSelectedIMPeriod,
    setProjectGMSExceedance,
    setProjectGMSIMVector,
  } = useContext(GlobalContext);

  const [localGMSConditionIM, setLocalGMSConditionIM] = useState(null);
  const [localGMSIMPeriod, setLocalGMSIMperiod] = useState(null);
  const [localGMSExceedance, setLocalGMSExceedance] = useState(null);
  const [localGMSIMVector, setLocalGMSIMVector] = useState(null);

  const invalidInputs = () => {
    return (
      localGMSConditionIM === null ||
      (localGMSConditionIM["value"] === "pSA" && localGMSIMPeriod === null) ||
      localGMSExceedance === null ||
      localGMSIMVector === null
    );
  };

  const setGlobalVariables = () => {
    setProjectGMSConditionIM(localGMSConditionIM["value"]);
    setProjectGMSSelectedIMPeriod(localGMSIMPeriod["value"]);
    setProjectGMSExceedance(localGMSExceedance["value"]);
    setProjectGMSIMVector(localGMSIMVector["value"]);
    setProjectGMSGetClick(uuidv4());
  };

  return (
    <Fragment>
      <div className="form-group form-section-title">
        {CONSTANTS.GMS_CONDITIONING_IM_NAME}
        <GuideTooltip
          explanation={
            CONSTANTS.TOOLTIP_MESSAGES["HAZARD_GMS_CONDITIONING_IM_NAME"]
          }
        />
      </div>
      <div className="form-group">
        <CustomSelect
          setSelect={setLocalGMSConditionIM}
          options={projectGMSIMTypes}
        />
      </div>
      <div className="form-group form-section-title">
        {CONSTANTS.VIBRATION_PERIOD} {CONSTANTS.SECONDS_UNIT}
        <GuideTooltip
          explanation={CONSTANTS.TOOLTIP_MESSAGES["GMS_VIBRATION_PERIOD"]}
        />
      </div>
      <div className="form-group">
        <CustomSelect
          setSelect={setLocalGMSIMperiod}
          options={projectGMSIMPeriods}
          selectedIM={localGMSConditionIM}
          isProjectGMS={true}
        />
      </div>
      <div className="form-group form-section-title">
        {CONSTANTS.EXCEEDANCE_RATE} (yr<sup>-1</sup>)
        <GuideTooltip
          explanation={
            CONSTANTS.TOOLTIP_MESSAGES["PROJECTS_GMS_EXCEEDANCE_RATE_LEVEL"]
          }
        />
      </div>
      <div className="form-group">
        <CustomSelect
          setSelect={setLocalGMSExceedance}
          options={projectGMSExceedances}
        />
      </div>
      <div className="form-group form-section-title">
        {CONSTANTS.IM_VECTOR}
        <GuideTooltip
          explanation={CONSTANTS.TOOLTIP_MESSAGES["PROJECTS_GMS_IM_VECTOR"]}
        />
      </div>
      <div className="form-group">
        <CustomSelect
          setSelect={setLocalGMSIMVector}
          options={projectGMSIMVectors}
        />
      </div>
      <div className="form-group">
        <button
          id="project-gms-get-btn"
          type="button"
          className="btn btn-primary"
          disabled={invalidInputs()}
          onClick={() => setGlobalVariables()}
        >
          {CONSTANTS.GET_BUTTON}
        </button>
      </div>
    </Fragment>
  );
};

export default GMSForm;
