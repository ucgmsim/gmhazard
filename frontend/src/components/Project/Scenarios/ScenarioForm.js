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
    projectId,
    projectVS30,
    projectLocation,
    projectZ1p0,
    projectZ2p5,
  } = useContext(GlobalContext);

  const [localSelectedIMComponent, setLocalSelectedIMComponent] =
    useState(null);
  const [localRuptureOptions, setLocalRuptureOptions] = useState([]);
  const [localRuptures, setLocalRuptures] = useState([]);

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
    if (localRuptures !== []) {
      const rupture_values = [];
      for (const key in localRuptures) {
        rupture_values.push(localRuptures[key]["value"]);
      }
      setProjectScenarioSelectedRuptures(rupture_values);
    }
  }, [localRuptures]);

  // Reset tabs if users change Project ID, Vs30, Z values or Location
  useEffect(() => {
    setLocalRuptures([]);
    setLocalSelectedIMComponent(null);
    setProjectScenarioData(null);
  }, [projectId, projectVS30, projectLocation, projectZ1p0, projectZ2p5]);

  return (
    <Fragment>
      <div className="form-group form-section-title">
        Scenarios
        <GuideTooltip
          explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_HAZARD"]} // TODO - Correct message for Scenarios
        />
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
          onClick={() => setProjectScenarioGetClick(uuidv4())}
        >
          Compute
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
