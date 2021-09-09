import React, { Fragment, useContext, useEffect, useState } from "react";

import { v4 as uuidv4 } from "uuid";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import TextField from "@material-ui/core/TextField";

import * as CONSTANTS from "constants/Constants";
import { GlobalContext } from "context";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import { GuideTooltip } from "components/common";
import {
  APIQueryBuilder,
  disableScrollOnNumInput,
  handleErrors,
  sortIMs,
  isEmptyObj,
} from "utils/Utils";
import {
  EnsembleSelect,
  SiteSelectionVS30SiteConditions,
  SiteSelectionBasinDepth,
} from "components/Hazard/SiteSelection";

import "assets/style/HazardForms.css";

const SiteSelectionForm = () => {
  disableScrollOnNumInput();

  const { getTokenSilently } = useAuth0();

  const {
    setLocationSetClick,
    setIMs,
    setIMDict,
    setScenarioIMComponentOptions,
    nzs1170p5SoilClass,
    setNZS1170p5SoilClass,
    nztaSoilClass,
    setNZTASoilClass,
    setVS30,
    setDefaultVS30,
    setStation,
    selectedEnsemble,
    setSiteSelectionLat,
    setSiteSelectionLng,
    mapBoxCoordinate,
    setMapBoxCoordinate,
    setSelectedIM,
    setHazardCurveComputeClick,
    setDisaggComputeClick,
    setUHSComputeClick,
    setScenarioComputeClick,
    setUHSRateTable,
    setNZS1170p5DefaultParams,
    setNZTADefaultParams,
    setNZS1170p5DefaultSoilClass,
    setNZTADefaultSoilClass,
    setSelectedNZTASoilClass,
  } = useContext(GlobalContext);

  // For station data fetcher
  const [localSetClick, setLocalSetClick] = useState(null);
  const [locationSetButton, setLocationSetButton] = useState({
    text: "Set",
    isFetching: false,
  });
  // For Location inputs
  const [localLat, setLocalLat] = useState(CONSTANTS.DEFAULT_LAT);
  const [localLng, setLocalLng] = useState(CONSTANTS.DEFAULT_LNG);
  /* 
    InputSource is either `input` or `mapbox`
    `input` for input fields
    `mapbox` for MapBox click
  */
  const [inputSource, setInputSource] = useState({
    lat: "input",
    lng: "input",
  });

  /*
    Two scenarios
    1. User click on the MapBox
    2. User clicks Set after they put Lat and/or Lng
    By setting inputSource differently, app knows whether they display in 4dp or full
  */
  useEffect(() => {
    if (mapBoxCoordinate.input === "MapBox") {
      setInputSource({ lat: "MapBox", lng: "MapBox" });
    } else if (mapBoxCoordinate.input === "input") {
      setInputSource({ lat: "input", lng: "input" });
    }

    setLocalLat(mapBoxCoordinate.lat);
    setLocalLng(mapBoxCoordinate.lng);
  }, [mapBoxCoordinate]);

  /*
    Run this useEffect only once when this page gets rendered
    The time it gets rendered is when users come to seistech.nz/hazard
    For instance, users were at /home and come to /hazard or /dashboard -> /hazard or even
    /hazard -> /home -> /hazard
    So reset those global values to prevent auto-trigger to get a station, Regional image and Vs30 image
  */
  useEffect(() => {
    resetVariables();
    setLocationSetClick(null);
    setLocalLat(CONSTANTS.DEFAULT_LAT);
    setLocalLng(CONSTANTS.DEFAULT_LNG);
    // For location button
    setLocationSetButton({
      text: "Set",
      isFetching: false,
    });
  }, []);

  // Get station
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getStation = async () => {
      if (localSetClick !== null) {
        try {
          const token = await getTokenSilently();

          resetVariables();
          setLocationSetButton({
            text: <FontAwesomeIcon icon="spinner" spin />,
            isFetching: true,
          });

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_STATION_ENDPOINT +
              APIQueryBuilder({
                ensemble_id: selectedEnsemble,
                lon: localLng,
                lat: localLat,
              }),
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          )
            .then(handleErrors)
            .then(async (response) => {
              const responseData = await response.json();
              setStation(responseData.station);
              setVS30(responseData.vs30);
              setDefaultVS30(responseData.vs30);

              let nzCodeQueryString = APIQueryBuilder({
                ensemble_id: selectedEnsemble,
                station: responseData.station,
              });

              return Promise.all([
                fetch(
                  CONSTANTS.INTERMEDIATE_API_URL +
                    CONSTANTS.CORE_API_HAZARD_NZS1170P5_DEFAULT_PARAMS_ENDPOINT +
                    nzCodeQueryString,
                  {
                    headers: {
                      Authorization: `Bearer ${token}`,
                    },
                    signal: signal,
                  }
                ),
                fetch(
                  CONSTANTS.INTERMEDIATE_API_URL +
                    CONSTANTS.CORE_API_HAZARD_NZTA_DEFAULT_PARAMS_ENDPOINT +
                    nzCodeQueryString,
                  {
                    headers: {
                      Authorization: `Bearer ${token}`,
                    },
                    signal: signal,
                  }
                ),
              ]);
            })
            .then(handleErrors)
            .then(async ([nzs1170p5, nzta]) => {
              const nzs1170p5DefaultParams = await nzs1170p5.json();
              const nztaDefaultParams = await nzta.json();
              /* 
                When site gets changed, reset the selected NZTA Soil Class
                So without rendering the NZTA tab(By clicking the NZTA radio)
                Compute Hazard Curve can get the NZTA with updated NZTA which is default
              */
              setSelectedNZTASoilClass({});

              setNZS1170p5DefaultParams(nzs1170p5DefaultParams);
              setNZTADefaultParams(nztaDefaultParams);

              setNZS1170p5DefaultSoilClass(
                nzs1170p5SoilClass.filter((obj) => {
                  return obj.value === nzs1170p5DefaultParams["soil_class"];
                })[0]
              );
              setNZTADefaultSoilClass(
                nztaSoilClass.filter((obj) => {
                  return obj.value === nztaDefaultParams["soil_class"];
                })[0]
              );

              setLocationSetButton({
                text: "Set",
                isFetching: false,
              });
            })
            .catch((error) => {
              if (error.name !== "AbortError") {
                setLocationSetButton({
                  text: "Set",
                  isFetching: false,
                });
              }
              console.log(error);
            });
        } catch (error) {
          console.log(error);
        }
      }
    };

    getStation();

    return () => {
      abortController.abort();
    };
  }, [localSetClick]);

  // Getting IMs for Seismic Hazard and Soil Class
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getIMandSoilClass = async () => {
      try {
        const token = await getTokenSilently();

        await Promise.all([
          fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_IMS_ENDPOINT +
              APIQueryBuilder({
                ensemble_id: selectedEnsemble,
              }),
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          ),
          fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_HAZARD_NZS1170P5_SOIL_CLASS_ENDPOINT,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          ),
          fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.CORE_API_HAZARD_NZTA_SOIL_CLASS_ENDPOINT,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: signal,
            }
          ),
        ])
          .then(handleErrors)
          .then(
            async ([
              responseIM,
              responseNZS1170p5SoilClass,
              responseNZTASoilClass,
            ]) => {
              const IMData = await responseIM.json();
              const nzs1170p5SoilClass =
                await responseNZS1170p5SoilClass.json();
              const nztaSoilClass = await responseNZTASoilClass.json();

              setIMs(sortIMs(Object.keys(IMData.ims)));
              setIMDict(IMData.ims);
              setScenarioIMComponentOptions(IMData.ims["pSA"]["components"]);
              setNZS1170p5SoilClass(
                setSoilClassOptions(nzs1170p5SoilClass["soil_class"])
              );
              setNZTASoilClass(
                setSoilClassOptions(nztaSoilClass["soil_class"])
              );
            }
          )
          .catch((error) => {
            console.log(error);
          });
      } catch (error) {
        console.log(error);
      }
    };
    getIMandSoilClass();

    return () => {
      abortController.abort();
    };
  }, [selectedEnsemble]);

  const setSoilClassOptions = (givenObj) => {
    const tempArr = [];

    if (!isEmptyObj(givenObj)) {
      for (const [key, value] of Object.entries(givenObj)) {
        tempArr.push({
          value: key,
          label: `${key} - ${value.replaceAll("_", " ")}`,
        });
      }
    }

    return tempArr;
  };

  const resetVariables = () => {
    // For Site Selection
    setVS30("");
    setDefaultVS30("");
    setStation("");
    setNZS1170p5DefaultParams([]);
    // For Seismic Hazard Tab
    setSelectedIM(null);
    setHazardCurveComputeClick(null);
    setDisaggComputeClick(null);
    setUHSComputeClick(null);
    setScenarioComputeClick(null);
    // Table rows in UHS section
    setUHSRateTable([]);
  };

  const invalidEnsembleLatLng = () => {
    return !(
      nzs1170p5SoilClass.length > 0 &&
      selectedEnsemble !== "Choose" &&
      selectedEnsemble !== "Loading" &&
      localLat >= -47.4 &&
      localLat <= -34.3 &&
      localLng >= 165 &&
      localLng <= 180
    );
  };

  // When Set button is clicked, chech whether the last action is from input fields or MapBox
  const onClickLocationSet = () => {
    setLocalSetClick(uuidv4());
    setSiteSelectionLat(localLat);
    setSiteSelectionLng(localLng);

    if (inputSource.lat === "input" || inputSource.lng === "input") {
      setMapBoxCoordinate({
        lat: localLat,
        lng: localLng,
        input: "input",
      });
    } else {
      setMapBoxCoordinate({
        lat: localLat,
        lng: localLng,
        input: "MapBox",
      });
    }

    setLocationSetClick(uuidv4());
  };

  const setttingLocalLat = (e) => {
    setInputSource((prevState) => ({
      ...prevState,
      lat: "input",
    }));
    setLocalLat(e);
  };

  const settingLocalLng = (e) => {
    setInputSource((prevState) => ({
      ...prevState,
      lng: "input",
    }));
    setLocalLng(e);
  };

  return (
    <Fragment>
      {CONSTANTS.ENV === "DEV" ? (
        <div>
          <div className="form-group form-section-title">
            <span>Ensemble</span>
          </div>
          <div className="im-custom-form-group">
            <EnsembleSelect />
          </div>
        </div>
      ) : null}

      <div className="form-group form-section-title">
        Location
        <GuideTooltip
          explanation={CONSTANTS.TOOLTIP_MESSAGES["SITE_SELECTION_LOCATION"]}
        />
      </div>

      <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group">
          <div className="d-flex align-items-center">
            <label
              id="label-haz-lat"
              htmlFor="haz-lat"
              className="control-label"
            >
              Latitude
            </label>
            <TextField
              id="haz-lat"
              className="flex-grow-1"
              type="number"
              value={
                inputSource.lat === "input"
                  ? localLat
                  : Number(localLat).toFixed(4)
              }
              onChange={(e) => setttingLocalLat(e.target.value)}
              placeholder="[-47.4, -34.3]"
              error={
                (localLat >= -47.4 && localLat <= -34.3) || localLat === ""
                  ? false
                  : true
              }
              helperText={
                (localLat >= -47.4 && localLat <= -34.3) || localLat === ""
                  ? " "
                  : "Latitude must be within the range of NZ."
              }
              variant="outlined"
            />
          </div>

          <div className="form-group">
            <div className="d-flex align-items-center">
              <label
                id="label-haz-lng"
                htmlFor="haz-lng"
                className="control-label"
              >
                Longitude
              </label>
              <TextField
                id="haz-lng"
                className="flex-grow-1"
                type="number"
                value={
                  inputSource.lng === "input"
                    ? localLng
                    : Number(localLng).toFixed(4)
                }
                onChange={(e) => settingLocalLng(e.target.value)}
                placeholder="[165, 180]"
                error={
                  (localLng >= 165 && localLng <= 180) || localLng === ""
                    ? false
                    : true
                }
                helperText={
                  (localLng >= 165 && localLng <= 180) || localLng === ""
                    ? " "
                    : "Longitude must be within the range of NZ."
                }
                variant="outlined"
              />
            </div>
          </div>
        </div>

        <div className="form-row">
          <button
            id="site-selection"
            type="button"
            className="btn btn-primary"
            onClick={() => onClickLocationSet()}
            disabled={invalidEnsembleLatLng()}
          >
            {locationSetButton.text}
          </button>
        </div>
      </form>

      <div className="form-group form-section-title">
        Site Conditions
        <GuideTooltip
          explanation={
            CONSTANTS.TOOLTIP_MESSAGES["SITE_SELECTION_SITE_CONDITION"]
          }
        />
      </div>

      <SiteSelectionVS30SiteConditions />
      <SiteSelectionBasinDepth />
    </Fragment>
  );
};

export default SiteSelectionForm;
