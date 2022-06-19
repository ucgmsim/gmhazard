import React, { useState, useEffect } from "react";

import TextField from "@material-ui/core/TextField";
import Radio from "@material-ui/core/Radio";
import RadioGroup from "@material-ui/core/RadioGroup";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import FormControl from "@material-ui/core/FormControl";
import { Accordion, Card } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Select from "react-select";
import makeAnimated from "react-select/animated";
import { v4 as uuidv4 } from "uuid";

import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import { ModalComponent } from "components/common";
import { handleErrors } from "utils/Utils";

import "assets/style/CreateProject.css";

const ProjectCreate = () => {
  const animatedComponents = makeAnimated();
  const { getTokenSilently } = useAuth0();

  const [displayName, setDisplayName] = useState("");
  const [projectID, setProjectID] = useState("");
  const [locationName, setLocationName] = useState("");
  const [accessLevel, setAccessLevel] = useState("private");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [vs30, setVs30] = useState("");
  const [z1p0, setZ1p0] = useState("");
  const [z2p5, setZ2p5] = useState("");
  const [radioValue, setRadioValue] = useState("");
  const [IM, setIM] = useState([]);
  const [IMComponent, setIMComponent] = useState([]);
  const [disaggRP, setDisaggRP] = useState("");
  const [uhsRP, setUHSRP] = useState("");
  const [accordionKey, setAccordionKey] = useState("null");
  const [locationTableState, setLocationTableState] = useState([]);
  const [submitClick, setSubmitClick] = useState(null);

  const [apiResponse, setApiResponse] = useState(null);
  const [responseModal, setResponseModal] = useState(false);

  const [submitBtnText, setSubmitBtnText] = useState({
    text: "Submit",
    isFetching: false,
  });

  // Dummy options
  const [options, setOptions] = useState([
    { value: "TEST1", label: "TEST1" },
    { value: "TEST2", label: "TEST2" },
    { value: "TEST3", label: "TEST3" },
    { value: "TEST4", label: "TEST4" },
  ]);

  const [IMComponentOptions, setIMComponentOptions] = useState([
    { value: "RotD50", label: "RotD50" },
    { value: "RotD100", label: "RotD100" },
    { value: "Larger", label: "Larger" },
  ]);

  const [arrowSets, setArrowSets] = useState({
    true: <FontAwesomeIcon icon="caret-down" size="2x" />,
    false: <FontAwesomeIcon icon="caret-up" size="2x" />,
  });

  const [arrow, setArrow] = useState(true);

  useEffect(() => {
    if (radioValue === "custom") {
      setAccordionKey("0");
      setArrow(!arrow);
    } else {
      setAccordionKey("null");
      setArrow(!arrow);
    }
  }, [radioValue]);

  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const createProjects = async () => {
      if (submitClick !== null) {
        try {
          const token = await getTokenSilently();

          setSubmitBtnText({
            text: <FontAwesomeIcon icon="spinner" spin />,
            isFetching: true,
          });

          let requestOptions = {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            signal: signal,
          };

          requestOptions["body"] = JSON.stringify({
            id: projectID,
            name: displayName,
            access_level: accessLevel,
            locations: createReadableLocations(locationTableState),
            package_type: radioValue,
          });
          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.INTERMEDIATE_API_CREATE_PROJECT_ENDPOINT,
            requestOptions
          )
            .then(handleErrors)
            .then(async (response) => {
              setApiResponse(response.status);

              setSubmitBtnText({
                text: "Submit",
                isFetching: false,
              });

              setResponseModal(true);
            })
            .catch((error) => {
              setSubmitBtnText({
                text: "Submit",
                isFetching: false,
              });

              setApiResponse(error);

              setResponseModal(true);
            });
        } catch (error) {
          setSubmitBtnText({
            text: "Submit",
            isFetching: false,
          });

          setApiResponse(error);

          setResponseModal(true);
        }
      }
    };

    createProjects();

    return () => {
      abortController.abort();
    };
  }, [submitClick]);

  const updateAccordion = () => {
    if (accordionKey === "null") {
      setAccordionKey("0");
      setArrow(!arrow);
    } else {
      setAccordionKey("null");
      setArrow(!arrow);
    }
  };

  const invalidInputs = () => {
    return !(
      displayName !== "" &&
      locationTableState.length > 0 &&
      (radioValue === "pga" ||
        radioValue === "pga+psa" ||
        (radioValue === "custom" &&
          IM.length > 0 &&
          IMComponent.length > 0 &&
          disaggRP !== "" &&
          uhsRP !== ""))
    );
  };

  const createReadableLocations = (locationArray) => {
    let tempArray = {};
    for (let i = 0; i < locationArray.length; i++) {
      let curLocation = locationArray[i];
      let locationID = curLocation["name"].toLowerCase().replaceAll(" ", "_");
      if (locationID in tempArray) {
        tempArray[locationID]["vs30"].push(parseFloat(curLocation["vs30"]));
        tempArray[locationID]["z1p0"].push(parseFloat(curLocation["z1p0"]));
        tempArray[locationID]["z2p5"].push(parseFloat(curLocation["z2p5"]));
      } else {
        let locationInfo = {
          name: curLocation["name"],
          lat: parseFloat(curLocation["lat"]),
          lon: parseFloat(curLocation["lng"]),
          vs30: [parseFloat(curLocation["vs30"])],
          z1p0: [parseFloat(curLocation["z1p0"])],
          z2p5: [parseFloat(curLocation["z2p5"])],
        };

        tempArray[locationID] = locationInfo;
      }
    }

    return tempArray;
  };

  const invalidLocationInputs = () => {
    return !(
      locationName !== "" &&
      lat >= -47.4 &&
      lat <= -34.3 &&
      lng >= 165 &&
      lng <= 180 &&
      vs30 !== ""
    );
  };

  const addLocation = () => {
    let tempObj = {
      name: locationName,
      lat: lat,
      lng: lng,
      vs30: vs30,
      z1p0: z1p0,
      z2p5: z2p5,
    };
    if (
      JSON.stringify(locationTableState).includes(JSON.stringify(tempObj)) ===
      false
    ) {
      setLocationTableState([...locationTableState, tempObj]);
      setVs30("");
      setZ1p0("");
      setZ2p5("");
    }
  };

  const onClickDeleteRow = (idx) => {
    locationTableState.splice(idx, 1);
    setLocationTableState([...locationTableState]);
  };

  let createdLocationTable = locationTableState.map((value, idx) => {
    return (
      <tr id={"locaion-row-" + idx} key={idx}>
        <td>{value.name}</td>
        <td>{value.lat}</td>
        <td>{value.lng}</td>
        <td>{value.vs30}</td>
        <td>{value.z1p0}</td>
        <td>{value.z2p5}</td>
        <td>
          <div
            className="location-delete-btn"
            onClick={() => onClickDeleteRow(idx)}
          >
            <FontAwesomeIcon icon="backspace" size="2x" />
          </div>
        </td>
      </tr>
    );
  });

  const modalBodyText = (responseCode) => {
    let bodyString = "";
    if (responseCode === 409) {
      bodyString =
        projectID.trim() === ""
          ? `Project ID - ${displayName
              .toLowerCase()
              .replaceAll(" ", "_")} already exists in the DB.` +
            "\nPlease try with a different Project ID"
          : `Project ID - ${projectID} already exists in the DB.` +
            "\nPlease try with a different Project ID";
    } else if (responseCode === 400) {
      bodyString = "Issue found in the ProjectAPI";
    } else if (responseCode === 200) {
      bodyString = "Successfully triggered to create project.\n";
      bodyString +=
        projectID.trim() === ""
          ? `Project ID - ${displayName.toLowerCase().replaceAll(" ", "_")}.`
          : `Project ID - ${projectID}.`;
    } else {
      bodyString = "Something went wrong.";
    }

    return bodyString;
  };

  return (
    <div className="container">
      <div className="row justify-content-lg-center">
        <div className="col col-lg">
          <div className="jumbotron">
            <h1 className="display-4">Create New Project</h1>
          </div>

          {/* 
            Display Name
            - Normal input
            - String 
            - Required*/}
          <div className="card  create-form-box">
            <h3 className="card-header required">Display Name</h3>
            <div className="card-body">
              <h5 className="card-title">Readable project name</h5>
              <div className="form-group required">
                <TextField
                  id="display-name-input"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  fullWidth
                  label="Required"
                  required
                />
              </div>
            </div>
          </div>

          {/* 
            ID (Internal Name, no spaces) 
            - Normal input
            - Can be left blank 
          */}
          <div className="card create-form-box">
            <h3 className="card-header">Project ID</h3>
            <div className="card-body">
              <h5 className="card-title">
                All lowercase with underscores. (E.g., gnzl, nzgs_pga)
              </h5>
              <div className="form-group">
                <TextField
                  id="project-id-input"
                  value={projectID}
                  onChange={(e) => setProjectID(e.target.value)}
                  fullWidth
                  label="Optional"
                />
              </div>
            </div>
          </div>

          {/* 
            Access Level - Optional 
            - Private
            - Public 
          */}
          <div className="card create-form-box">
            <h3 className="card-header">Access Level</h3>
            <div className="card-body">
              <FormControl component="fieldset">
                <RadioGroup
                  name="accesslevel"
                  value={accessLevel}
                  onChange={(e) => setAccessLevel(e.target.value)}
                >
                  <FormControlLabel
                    value="private"
                    control={<Radio />}
                    label="Private"
                  />
                  <FormControlLabel
                    value="public"
                    control={<Radio />}
                    label="Public"
                  />
                </RadioGroup>
              </FormControl>
            </div>
          </div>

          {/* 
            Locations 
            - Normal input for Name
            - Number(Float) input for Lat, Lon, VS30
            - Name, Lat, Lon, VS30(multiple VS30 is possible)
            - Locations can be multiple rows
            - Required
          */}
          <div className="card create-form-box">
            <h3 className="card-header required">Locations</h3>
            <div className="card-body">
              <div className="form-group required">
                <div className="d-flex align-items-center">
                  <label
                    id="label-create-name"
                    htmlFor="create-name"
                    className="control-label"
                  >
                    Name
                  </label>
                  <TextField
                    id="create-name"
                    className="flex-grow-1"
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    variant="outlined"
                    required
                    label="Required"
                  />
                </div>
              </div>
              <div className="form-group required">
                <div className="d-flex align-items-center">
                  <label
                    id="label-create-lng"
                    htmlFor="create-lng"
                    className="control-label"
                  >
                    {CONSTANTS.LATITUDE}
                  </label>
                  <TextField
                    id="create-lng"
                    className="flex-grow-1"
                    type="number"
                    value={lat}
                    onChange={(e) => setLat(e.target.value)}
                    placeholder="[-47.4, -34.3]"
                    error={
                      (lat >= -47.4 && lat <= -34.3) || lat === ""
                        ? false
                        : true
                    }
                    helperText={
                      (lat >= -47.4 && lat <= -34.3) || lat === ""
                        ? " "
                        : `${CONSTANTS.LATITUDE_HELPER_TEXT}`
                    }
                    variant="outlined"
                    required
                    label="Required"
                  />
                </div>
              </div>
              <div className="form-group required">
                <div className="d-flex align-items-center">
                  <label
                    id="label-create-lng"
                    htmlFor="create-lng"
                    className="control-label"
                  >
                    {CONSTANTS.LONGITUDE}
                  </label>
                  <TextField
                    id="create-lng"
                    className="flex-grow-1"
                    type="number"
                    value={lng}
                    onChange={(e) => setLng(e.target.value)}
                    placeholder="[165, 180]"
                    error={
                      (lng >= 165 && lng <= 180) || lng === "" ? false : true
                    }
                    helperText={
                      (lng >= 165 && lng <= 180) || lng === ""
                        ? " "
                        : `${CONSTANTS.LONGITUDE_HELPER_TEXT}`
                    }
                    variant="outlined"
                    required
                    label="Required"
                  />
                </div>
              </div>
              <div className="card create-form-box">
                <h3 className="card-header required">
                  {CONSTANTS.SITE_CONDITIONS}
                </h3>
                <div className="card-body">
                  <div className="form-group required">
                    <div className="d-flex align-items-center">
                      <label
                        id="label-create-vs30"
                        htmlFor="create-vs30"
                        className="control-label"
                      >
                        V<sub>S30</sub>
                      </label>
                      <TextField
                        id="create-vs30"
                        className="flex-grow-1"
                        value={vs30}
                        onChange={(e) => setVs30(e.target.value)}
                        placeholder="245"
                        variant="outlined"
                        required
                        label="Required"
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <div className="d-flex align-items-center">
                      <label
                        id="label-create-z1p0"
                        htmlFor="create-z1p0"
                        className="control-label"
                      >
                        Z<sub>1.0</sub>
                      </label>
                      <TextField
                        id="create-z1p0"
                        className="flex-grow-1"
                        value={z1p0}
                        onChange={(e) => setZ1p0(e.target.value)}
                        placeholder="1.2"
                        variant="outlined"
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <div className="d-flex align-items-center">
                      <label
                        id="label-create-z2p5"
                        htmlFor="create-z2p5"
                        className="control-label"
                      >
                        Z<sub>2.5</sub>
                      </label>
                      <TextField
                        id="create-z2p5"
                        className="flex-grow-1"
                        value={z2p5}
                        onChange={(e) => setZ2p5(e.target.value)}
                        placeholder="2.4"
                        variant="outlined"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <button
                className="btn btn-primary create-project-add-location"
                onClick={() => addLocation()}
                disabled={invalidLocationInputs()}
              >
                Add Location
              </button>
              <div className="form-group">
                <table id="location-added">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>{CONSTANTS.LATITUDE}</th>
                      <th>{CONSTANTS.LONGITUDE}</th>
                      <th>
                        V<sub>S30</sub>
                      </th>
                      <th>
                        Z<sub>1.0</sub>
                      </th>
                      <th>
                        Z<sub>2.5</sub>
                      </th>
                      <th>Remove</th>
                    </tr>
                  </thead>
                  <tbody>{createdLocationTable}</tbody>
                </table>
              </div>
            </div>
          </div>

          {/* 
            Package 
            - Radio button
            - PGA
            - PGA + pSA
            - Custom
            - Required   
          */}
          <div className="card create-form-box">
            <h3 className="card-header required">Package</h3>
            <div className="card-body">
              <FormControl component="fieldset">
                <RadioGroup
                  name="package"
                  value={radioValue}
                  onChange={(e) => setRadioValue(e.target.value)}
                >
                  <FormControlLabel
                    value="pga"
                    control={<Radio />}
                    label="PGA"
                  />
                  <FormControlLabel
                    value="pga+psa"
                    control={<Radio />}
                    label="PGA+pSA"
                  />
                  <FormControlLabel
                    value="custom"
                    control={<Radio />}
                    label="Custom"
                  />
                </RadioGroup>
              </FormControl>
            </div>
          </div>

          {/* 
            If Custom is chosen
            IMs
            - Dropdown
            - Multi

            pSA Periods

            Disagg RPs
            - String - However only numbers with comma
            - Multi

            UHS RPs
            - String - However only numbers with comma
            - Multi
          */}
          <Accordion activeKey={accordionKey} onSelect={updateAccordion}>
            <Card>
              <Accordion.Toggle
                as={Card.Header}
                eventKey="0"
                onClick={() => setArrow(!arrow)}
              >
                <div className="advanced-toggle-header">
                  <h3>Custom</h3>
                  {arrowSets[arrow]}
                </div>
              </Accordion.Toggle>
              <Accordion.Collapse eventKey="0">
                <Card.Body>
                  <div className="card create-form-box">
                    <h3 className="card-header required">IMs</h3>
                    <div className="card-body">
                      <div className="form-group">
                        <Select
                          id="create-project-id"
                          closeMenuOnSelect={false}
                          components={animatedComponents}
                          isMulti
                          value={IM.length === 0 ? [] : IM}
                          onChange={(value) => setIM(value || [])}
                          options={options}
                          isDisabled={radioValue !== "custom"}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="card create-form-box">
                    <h3 className="card-header required">IM Components</h3>
                    <div className="card-body">
                      <div className="form-group">
                        <Select
                          id="create-project-im-components"
                          closeMenuOnSelect={false}
                          components={animatedComponents}
                          isMulti
                          value={IMComponent.length === 0 ? [] : IMComponent}
                          onChange={(value) => setIMComponent(value || [])}
                          options={IMComponentOptions}
                          isDisabled={radioValue !== "custom"}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="card create-form-box">
                    <h3 className="card-header required">
                      Disagg Return Periods
                    </h3>
                    <div className="card-body">
                      <div className="form-group">
                        <TextField
                          id="project-custom-disagg-rp-input"
                          value={disaggRP}
                          onChange={(e) => setDisaggRP(e.target.value)}
                          fullWidth
                          disabled={radioValue !== "custom"}
                          placeholder={
                            radioValue === "custom" ? "" : "Custom usage"
                          }
                          variant={
                            radioValue === "custom" ? "outlined" : "filled"
                          }
                        />
                      </div>
                    </div>
                  </div>

                  <div className="card create-form-box">
                    <h3 className="card-header required">UHS Return Periods</h3>
                    <div className="card-body">
                      <div className="form-group">
                        <TextField
                          id="project-uhs-rp-input"
                          value={uhsRP}
                          onChange={(e) => setUHSRP(e.target.value)}
                          fullWidth
                          disabled={radioValue !== "custom"}
                          placeholder={
                            radioValue === "custom" ? "" : "Custom usage"
                          }
                          variant={
                            radioValue === "custom" ? "outlined" : "filled"
                          }
                        />
                      </div>
                    </div>
                  </div>
                </Card.Body>
              </Accordion.Collapse>
            </Card>
          </Accordion>

          <button
            className="btn btn-primary create-project-submit"
            onClick={() => setSubmitClick(uuidv4())}
            disabled={invalidInputs() || submitBtnText.isFetching === true}
          >
            {submitBtnText.text}
          </button>
        </div>
      </div>

      <ModalComponent
        modal={responseModal}
        setModal={setResponseModal}
        title="Project Creation Result"
        body={modalBodyText(apiResponse)}
      />
    </div>
  );
};

export default ProjectCreate;
