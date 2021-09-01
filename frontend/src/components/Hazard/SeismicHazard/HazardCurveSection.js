import React, { useState, useEffect, useContext, Fragment } from "react";

import { v4 as uuidv4 } from "uuid";

import * as CONSTANTS from "constants/Constants";
import { GlobalContext } from "context";

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
        setPeriodOptions(["N/A"]);
      }
      setComponentOptions(IMDict[localSelectedIM["value"]]["components"]);
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
        Hazard Curve
        <GuideTooltip
          explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_HAZARD"]}
        />
      </div>
      <div className="im-custom-form-group">
        <IMCustomSelect
          title="Intensity Measure"
          setSelect={setLocalSelectedIM}
          options={IMs}
        />
      </div>
      <div className="im-custom-form-group">
        <IMCustomSelect
          title="Vibration Period"
          setSelect={setLocalSelectedIMPeriod}
          options={periodOptions}
          selectedIM={localSelectedIM}
          placeholder={"Please select the Intensity Measure first."}
        />
      </div>

      <div className="form-group">
        <IMCustomSelect
          title="Component"
          setSelect={setLocalSelectedIMComponent}
          selectedIM={localSelectedIM}
          options={componentOptions}
          placeholder={"Please select the Intensity Measure first."}
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
          Compute
        </button>
      </div>
      <div className="form-group">
        <input
          type="checkbox"
          checked={showHazardNZCode}
          onChange={() => setShowHazardNZCode(!showHazardNZCode)}
        />
        <span className="show-nzs1170p5">&nbsp;Show NZ Code</span>
      </div>
    </Fragment>
  );
};

export default HazardCurveSection;
