import React, { useState, useContext, useEffect, Fragment } from "react";

import { v4 as uuidv4 } from "uuid";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import { IMCustomSelect, GuideTooltip } from "components/common";

const HazardCurveSection = () => {
  const {
    setProjectSelectedIM,
    setProjectSelectedIMPeriod,
    setProjectSelectedIMComponent,
    projectIMs,
    projectIMDict,
    setProjectHazardCurveGetClick,
  } = useContext(GlobalContext);

  const [localSelectedIM, setLocalSelectedIM] = useState(null);
  const [localSelectedIMPeriod, setLocalSelectedIMPeriod] = useState(null);
  const [localSelectedIMComponent, setLocalSelectedIMComponent] =
    useState(null);

  const [periodOptions, setPeriodOptions] = useState([]);
  const [componentOptions, setComponentOptions] = useState([]);

  // When local IM gets changed, update the global instantly so can do disaggregation without getting Hazard Curve data
  useEffect(() => {
    if (localSelectedIM !== null) {
      setProjectSelectedIM(localSelectedIM["value"]);
      if (localSelectedIM["value"] === "pSA") {
        setPeriodOptions(
          projectIMDict[localSelectedIM["value"]]["periods"].sort(
            (a, b) => a - b
          )
        );
      } else {
        setPeriodOptions(["N/A"]);
      }
      setComponentOptions(
        projectIMDict[localSelectedIM["value"]]["components"]
      );
    }
  }, [localSelectedIM]);

  useEffect(() => {
    if (
      localSelectedIMPeriod !== null &&
      localSelectedIMPeriod["value"] !== undefined
    ) {
      setProjectSelectedIMPeriod(localSelectedIMPeriod["value"].toString());
    } else {
      setProjectSelectedIMPeriod(null);
    }
  }, [localSelectedIMPeriod]);

  useEffect(() => {
    if (localSelectedIMComponent !== null) {
      setProjectSelectedIMComponent(localSelectedIMComponent["value"]);
    } else {
      setProjectSelectedIMComponent(null);
    }
  }, [localSelectedIMComponent]);

  const invalidGetBtn = () => {
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
          explanation={CONSTANTS.TOOLTIP_MESSAGES["PROJECT_HAZARD"]}
        />
      </div>
      <div className="form-group">
        <IMCustomSelect
          title="Intensity Measure"
          setSelect={setLocalSelectedIM}
          options={projectIMs}
        />
      </div>

      <div className="form-group">
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
          id="project-hazard-curve-get-btn"
          type="button"
          className="btn btn-primary"
          disabled={invalidGetBtn()}
          onClick={() => setProjectHazardCurveGetClick(uuidv4())}
        >
          Get
        </button>
      </div>
    </Fragment>
  );
};

export default HazardCurveSection;
