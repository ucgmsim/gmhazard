import React, { Fragment, useState, useEffect, useContext } from "react";

import Select from "react-select";
import { v4 as uuidv4 } from "uuid";
import makeAnimated from "react-select/animated";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import { createSelectArray } from "utils/Utils";
import { IMCustomSelect, GuideTooltip } from "components/common";

const ScenarioForm = () => {
  const animatedComponents = makeAnimated();

  const {
    station,
    setScenarioComputeClick,
    setSelectedScenarioIMComponent,
    scenarioIMComponentOptions,
    scenarioData,
    setScenarioData,
    setScenarioSelectedRuptures,
  } = useContext(GlobalContext);

  const [localSelectedIMComponent, setLocalSelectedIMComponent] =
    useState(null);
  const [localRuptureOptions, setLocalRuptureOptions] = useState([]);
  const [localRuptures, setLocalRuptures] = useState([]);

  useEffect(() => {
    if (localSelectedIMComponent !== null) {
      setSelectedScenarioIMComponent(localSelectedIMComponent["value"]);
    } else {
      setLocalSelectedIMComponent(null);
    }
  }, [localSelectedIMComponent]);

  useEffect(() => {
    if (scenarioData !== null) {
      setLocalRuptureOptions(
        createSelectArray(
          Object.keys(scenarioData["ensemble_scenario"]["mu_data"])
        )
      );
    } else {
      setLocalRuptureOptions([]);
    }
  }, [scenarioData]);

  useEffect(() => {
    if (localRuptures !== []) {
      const rupture_values = [];
      for (const key in localRuptures) {
        rupture_values.push(localRuptures[key]["value"]);
      }
      setScenarioSelectedRuptures(rupture_values);
    }
  }, [localRuptures]);

  // Reset tabs if users change Station
  useEffect(() => {
    setLocalRuptures([]);
    setLocalSelectedIMComponent(null);
    setScenarioData(null);
  }, [station]);

  return (
    <Fragment>
      <div className="form-group form-section-title">
        {CONSTANTS.SCENARIOS}
        <GuideTooltip explanation={CONSTANTS.TOOLTIP_MESSAGES["SCENARIOS"]} />
      </div>
      <div className="form-group">
        <IMCustomSelect
          title={CONSTANTS.COMPONENT}
          setSelect={setLocalSelectedIMComponent}
          options={scenarioIMComponentOptions}
          selectedIM={"pSA"}
          placeholder={`${CONSTANTS.PLACEHOLDER_LOADING}`}
        />
      </div>

      <div className="form-group">
        <button
          id="hazard-component-scenario-select"
          type="button"
          className="btn btn-primary"
          disabled={localSelectedIMComponent === null}
          onClick={() => setScenarioComputeClick(uuidv4())}
        >
          {CONSTANTS.COMPUTE_BUTTON}
        </button>
      </div>

      <div className="form-group">
        <label
          id="label-hazard-scenarios"
          htmlFor="scenario-ruptures"
          className="control-label"
        >
          {CONSTANTS.SCENARIO_RUPTURES}
        </label>
        <Select
          id="hazard-scenarios-select"
          closeMenuOnSelect={false}
          components={animatedComponents}
          isMulti
          placeholder={
            localRuptureOptions.length === 0
              ? `${CONSTANTS.PLACEHOLDER_NOT_AVAILABLE}`
              : `${CONSTANTS.PLACEHOLDER_SELECT_SIGN}`
          }
          value={localRuptures.length === 0 ? [] : localRuptures}
          onChange={(value) => setLocalRuptures(value || [])}
          options={localRuptureOptions}
          isDisabled={localRuptureOptions.length === 0}
          menuPlacement="auto"
          menuPortalTarget={document.body}
        />
      </div>
    </Fragment>
  );
};

export default ScenarioForm;
