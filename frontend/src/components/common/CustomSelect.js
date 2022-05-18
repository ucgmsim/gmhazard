import React, {
  Fragment,
  useEffect,
  useState,
  useRef,
  useContext,
} from "react";

import Select from "react-select";

import { GlobalContext } from "context";

import { GuideTooltip } from "components/common";
import {
  createSelectArray,
  createProjectIDArray,
  createVs30Array,
  createZArray,
} from "utils/Utils";

const CustomSelect = ({
  title = null,
  setSelect,
  options,
  placeholder = "Loading...",
  guideMSG = null,
  isProjectID = false,
  isVs30 = false,
  isZ = false,
  resettable = true,
  resetOnChange = null,
}) => {
  const { locationSetClick, projectSiteSelectionGetClick } =
    useContext(GlobalContext);
  const [localOptions, setLocalOptions] = useState([]);
  const selectInputRef = useRef();

  useEffect(() => {
    if (options !== undefined && options.length !== 0) {
      let tempOptions =
        isProjectID === true
          ? createProjectIDArray(options)
          : isZ === true
          ? createZArray(options)
          : createSelectArray(options);

      setLocalOptions(tempOptions);
    } else {
      setLocalOptions([]);
    }
  }, [options]);

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

  /*
    Projects
    Resets Site selection dropdowns on change
  */
  useEffect(() => {
    setSelect(null);
    selectInputRef.current.select.clearValue();
  }, [resetOnChange]);

  return (
    <Fragment>
      {title !== null ? <label className="control-label">{title}</label> : null}

      {guideMSG !== null ? <GuideTooltip explanation={guideMSG} /> : null}

      <Select
        ref={selectInputRef}
        placeholder={localOptions.length === 0 ? placeholder : "Select..."}
        onChange={(e) => setSelect(e)}
        options={localOptions}
        isDisabled={localOptions.length === 0}
        menuPlacement="auto"
        menuPortalTarget={document.body}
      />
    </Fragment>
  );
};

export default CustomSelect;
