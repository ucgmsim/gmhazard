import React, { Fragment, useState, useEffect, useContext } from "react";

import { v4 as uuidv4 } from "uuid";
import Select from "react-select";
import makeAnimated from "react-select/animated";

import * as CONSTANTS from "constants/Constants";
import { GlobalContext } from "context";

import { IMCustomSelect, GuideTooltip } from "components/common";
import { createSelectArray } from "utils/Utils";

const ScenarioForm = () => {
  const animatedComponents = makeAnimated();

  const {
    setProjectScenarioGetClick,
    setProjectSelectedScenarioIMComponent,
    projectScenarioIMComponentOptions,
    projectScenarioData,
    setProjectScenarioData,
    setProjectScenarioSelectedRuptures,
    projectSiteSelectionGetClick,
  } = useContext(GlobalContext);

  const [localSelectedIMComponent, setLocalSelectedIMComponent] =
    useState(null);
  const [localRuptureOptions, setLocalRuptureOptions] = useState([]);
  const [localRuptures, setLocalRuptures] = useState([]);

  // Reset tabs if users click Get button from Site Selection
  useEffect(() => {
    if (projectSiteSelectionGetClick !== null) {
      setLocalRuptures([]);
      setLocalSelectedIMComponent(null);
      setProjectScenarioData(null);
    }
  }, [projectSiteSelectionGetClick]);

  useEffect(() => {
    if (localSelectedIMComponent !== null) {
      setProjectSelectedScenarioIMComponent(localSelectedIMComponent["value"]);
    } else {
      setLocalSelectedIMComponent(null);
    }
  }, [localSelectedIMComponent]);

  useEffect(() => {
    if (projectScenarioData !== null) {
      setLocalRuptureOptions(
        createSelectArray(
          Object.keys(projectScenarioData["ensemble_scenario"]["mu_data"])
        )
      );
    } else {
      setLocalRuptureOptions([]);
    }
  }, [projectScenarioData]);

  useEffect(() => {
    if (localRuptures.length !== 0) {
      setProjectScenarioSelectedRuptures(
        localRuptures.map((rupture) => rupture["value"])
      );
    }
  }, [localRuptures]);

  const setGlobalVariables = () => {
    setLocalRuptures([]);
    setProjectScenarioSelectedRuptures([]);
    setProjectScenarioGetClick(uuidv4());
  };

  return (
    <Fragment>
      <div className="form-group form-section-title">
        Scenarios
        <GuideTooltip explanation={CONSTANTS.TOOLTIP_MESSAGES["SCENARIOS"]} />
      </div>
      <div className="form-group">
        <IMCustomSelect
          title="Component"
          setSelect={setLocalSelectedIMComponent}
          options={projectScenarioIMComponentOptions}
          selectedIM={"pSA"}
          placeholder={"Loading..."}
        />
      </div>

      <div className="form-group">
        <button
          id="project-component-scenario-select"
          type="button"
          className="btn btn-primary"
          disabled={localSelectedIMComponent === null}
          onClick={() => setGlobalVariables()}
        >
          {CONSTANTS.GET_BUTTON}
        </button>
      </div>

      <div className="form-group">
        <label
          id="label-project-scenarios"
          htmlFor="scenario-ruptures"
          className="control-label"
        >
          Scenarios
        </label>
        <Select
          id="project-scenarios-select"
          closeMenuOnSelect={false}
          components={animatedComponents}
          isMulti
          placeholder={
            localRuptureOptions.length === 0 ? "Not available" : "Select..."
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
