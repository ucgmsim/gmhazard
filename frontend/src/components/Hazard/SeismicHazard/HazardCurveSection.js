import React, { useState, useEffect, useContext, Fragment } from "react";

import { v4 as uuidv4 } from "uuid";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import { sortIMComponents } from "utils/Utils";
import { IMCustomSelect, GuideTooltip } from "components/common";

const HazardCurveSection = () => {
  const {
    IMs,
    IMDict,
    setSelectedIM,
    setSelectedIMPeriod,
    setSelectedIMComponent,
    setHazardCurveComputeClick,
    showHazardNZCode,
    setShowHazardNZCode,
  } = useContext(GlobalContext);

  const [localSelectedIM, setLocalSelectedIM] = useState(null);
  const [localSelectedIMPeriod, setLocalSelectedIMPeriod] = useState(null);
  const [localSelectedIMComponent, setLocalSelectedIMComponent] =
    useState(null);

  const [periodOptions, setPeriodOptions] = useState([]);
  const [componentOptions, setComponentOptions] = useState([]);

  /* 
    Due to performance issue, use local variable in front
    (where users see, dropdowns)
    then update the global variable behind
  */
  useEffect(() => {
    if (localSelectedIM !== null) {
      setSelectedIM(localSelectedIM["value"]);
      if (localSelectedIM["value"] === "pSA") {
        setPeriodOptions(
          IMDict[localSelectedIM["value"]]["periods"].sort((a, b) => a - b)
        );
      } else {
        setPeriodOptions([`${CONSTANTS.PLACEHOLDER_NOT_APPLICABLE}`]);
      }
      setComponentOptions(
        sortIMComponents(IMDict[localSelectedIM["value"]]["components"])
      );
    }
  }, [localSelectedIM]);

  useEffect(() => {
    if (
      localSelectedIMPeriod !== null &&
      localSelectedIMPeriod["value"] !== undefined
    ) {
      setSelectedIMPeriod(localSelectedIMPeriod["value"].toString());
    } else {
      setSelectedIMPeriod(null);
    }
  }, [localSelectedIMPeriod]);

  useEffect(() => {
    if (localSelectedIMComponent !== null) {
      setSelectedIMComponent(localSelectedIMComponent["value"]);
    } else {
      setSelectedIMComponent(null);
    }
  }, [localSelectedIMComponent]);

  const invalidInputs = () => {
    return (
      localSelectedIM === null ||
      (localSelectedIM["value"] === "pSA" && localSelectedIMPeriod === null) ||
      localSelectedIMComponent === null
    );
  };

  return (
    <Fragment>
      <div className="form-group form-section-title">
        {CONSTANTS.HAZARD_CURVE}
        <GuideTooltip
          explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_HAZARD"]}
        />
      </div>
      <div className="im-custom-form-group">
        <IMCustomSelect
          title={CONSTANTS.INTENSITY_MEASURE}
          setSelect={setLocalSelectedIM}
          options={IMs}
        />
      </div>
      <div className="im-custom-form-group">
        <IMCustomSelect
          title={`${CONSTANTS.VIBRATION_PERIOD} ${CONSTANTS.SECONDS_UNIT}`}
          setSelect={setLocalSelectedIMPeriod}
          options={periodOptions}
          selectedIM={localSelectedIM}
          placeholder={CONSTANTS.PLACEHOLDER_SELECT_IM}
        />
      </div>

      <div className="form-group">
        <IMCustomSelect
          title={CONSTANTS.COMPONENT}
          setSelect={setLocalSelectedIMComponent}
          selectedIM={localSelectedIM}
          options={componentOptions}
          placeholder={CONSTANTS.PLACEHOLDER_SELECT_IM}
        />
      </div>

      <div className="form-group">
        <button
          id="im-select"
          type="button"
          className="btn btn-primary"
          disabled={invalidInputs()}
          onClick={() => setHazardCurveComputeClick(uuidv4())}
        >
          {CONSTANTS.COMPUTE_BUTTON}
        </button>
      </div>
      <div className="form-group">
        <input
          type="checkbox"
          checked={showHazardNZCode}
          onChange={() => setShowHazardNZCode(!showHazardNZCode)}
        />
        <span className="show-nzs1170p5">&nbsp;{CONSTANTS.SHOW_NZ_CODE}</span>
      </div>
    </Fragment>
  );
};

export default HazardCurveSection;
