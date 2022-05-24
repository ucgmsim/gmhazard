import React, {
  Fragment,
  useEffect,
  useState,
  useRef,
  useContext,
} from "react";

import Select from "react-select";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import { GuideTooltip } from "components/common";
import { createSelectArray } from "utils/Utils";

const IMCustomSelect = ({
  title = null,
  setSelect,
  options,
  placeholder = `${CONSTANTS.PLACEHOLDER_LOADING}`,
  guideMSG = null,
  selectedIM = null,
  resettable = true,
}) => {
  const { locationSetClick, projectSiteSelectionGetClick } =
    useContext(GlobalContext);
  const [localOptions, setLocalOptions] = useState([]);
  const selectInputRef = useRef();

  useEffect(() => {
    if (options !== undefined && options.length !== 0) {
      let tempOptions = createSelectArray(options);
      setLocalOptions(tempOptions);
      /* 
        Select the first one
        if there is only one option
        and only if title is Component
        (We may extend but Component for now)
        setSelect is from parents, hence no need to set again
        in parents component
      */
      if (options.length === 1 && title === "Component") {
        setSelect(tempOptions[0]);
        selectInputRef.current.select.setValue(tempOptions[0]);
      }
    } else {
      setLocalOptions([]);
    }
  }, [options]);

  /*
    Reset the react-select to display N/A 
    if the selected IM is not pSA (This is only for Period's select)
  */
  useEffect(() => {
    if (selectedIM !== null && selectedIM["value"] !== "pSA") {
      setSelect(null);
      selectInputRef.current.select.clearValue();
    }
  }, [selectedIM]);

  /* 
    Non-projects
    By user, the site got changed by clicking setting location 
    Reset selected values
  */
  useEffect(() => {
    if (locationSetClick !== null && resettable === true) {
      setSelect(null);
      selectInputRef.current.select.clearValue();
    }
  }, [locationSetClick]);

  /*
    Projects
    By user, Get button got clicked from the Site Selection
    only if its resetable components.
    Projects' Site Selection's dropdowns are not resettable
  */
  useEffect(() => {
    if (projectSiteSelectionGetClick !== null && resettable === true) {
      setSelect(null);
      selectInputRef.current.select.clearValue();
    }
  }, [projectSiteSelectionGetClick]);

  return (
    <Fragment>
      {title !== null ? <label className="control-label">{title}</label> : null}

      {guideMSG !== null ? <GuideTooltip explanation={guideMSG} /> : null}

      <Select
        ref={selectInputRef}
        placeholder={
          localOptions.length === 0
            ? placeholder
            : title === `${CONSTANTS.VIBRATION_PERIOD} ${CONSTANTS.SECONDS}` &&
              selectedIM["value"] === "pSA"
            ? "Select period..."
            : title === `${CONSTANTS.VIBRATION_PERIOD} ${CONSTANTS.SECONDS}` &&
              selectedIM["value"] !== "pSA"
            ? "N/A"
            : title === "Component" && localOptions.length > 1
            ? "Select component..."
            : `${CONSTANTS.PLACEHOLDER_SELECT_SIGN}`
        }
        onChange={(e) => setSelect(e)}
        options={localOptions}
        isDisabled={
          localOptions.length === 0 ||
          (selectedIM !== null &&
            selectedIM["value"] !== "pSA" &&
            title === `${CONSTANTS.VIBRATION_PERIOD} ${CONSTANTS.SECONDS}`) ||
          (selectedIM === null &&
            (title === `${CONSTANTS.VIBRATION_PERIOD} ${CONSTANTS.SECONDS}` ||
              title === "Component"))
        }
        menuPlacement="auto"
        menuPortalTarget={document.body}
      />
    </Fragment>
  );
};

export default IMCustomSelect;
