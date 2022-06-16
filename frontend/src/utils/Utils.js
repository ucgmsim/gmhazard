import $ from "jquery";

/* 
  disable mousewheel on number input fields when in focus
  (to prevent Cromium browsers change the value when scrolling)
*/
export const disableScrollOnNumInput = () => {
  $("form").on("focus", "input[type=number]", (e) => {
    $(e.currentTarget).on("wheel.disableScroll", (e) => {
      e.preventDefault();
    });
  });
  $("form").on("blur", "input[type=number]", (e) => {
    $(e.currentTarget).off("wheel.disableScroll");
  });

  // Disable the up and down arrow button changing values
  $("form").on("focus", "input[type=number]", (e) => {
    $(e.currentTarget).on("keydown", (e) => {
      if (e.which === 38 || e.which === 40) {
        e.preventDefault();
      }
    });
  });
};

/*
  Handle the response
  response is an array of objects if Promise.all is used
  response is an object if fetch is used
*/
export const handleErrors = (response) => {
  /*
    For Promise.all with an empty array - Promise.all([])
    With Hazard Curve, if IM is not PGA nor pSA_XX, we cannot get NZS1170.5 and NZTA.
    Hence the response length will be 0
  */
  if (response.length === 0) {
    return response;
  }
  /*
    For Promise.all which is sending multiple requests simultaneously (array format)
    However, single request is an object, not an array.
    Hence, cannot use isArray() method
  */
  if (response.length >= 1) {
    for (const eachResponse of response) {
      if (eachResponse.status !== 200) {
        console.log(Error(response.statusText));
        throw response.status;
      }
    }
  } else {
    if (response.status !== 200) {
      /* 
        Debug purpose
        This can be replaced if we implement front-end logging just like we did on Core API (Saving logs in a file somehow)
        Until then, console.log to invest while developing
      */
      console.log(Error(response.statusText));
      throw response.status;
    }
  }

  return response;
};

/*
  Converts the Series json (which is a dict with each index value as a key),
  to two arrays ready for plotting.
*/
export const getPlotData = (data) => {
  const index = [];
  const values = [];
  for (let [key, value] of Object.entries(data)) {
    index.push(Number(key));
    values.push(value);
  }

  return { index: index, values: values };
};

// Implement x sig figs for numeric float values
export const renderSigfigs = (fullprecision, sigfigs) => {
  return Number.parseFloat(fullprecision).toPrecision(sigfigs);
};

/* 
  Create an Array from start to stop by step
  For instance, range(0, 1, 0.04) =
  [0, 0.04, 0.08, 0.12....., 1]
  To make empirical CDFs valid from 0-1 not just 1/N to 1
  Reference: https://en.wikipedia.org/wiki/Empirical_distribution_function
*/
export const range = (start, stop, step) => {
  let tempArr = [start];
  let curValue = start;

  while (curValue < stop) {
    tempArr.push((curValue += step || 1));
  }

  return curValue.toFixed(1) > stop ? tempArr.slice(0, -1) : tempArr;
};

/*
  Sort and duplicate every element
  Special sort & duplicate function for GMS Plots for X range
*/
export const sortDuplicateXRange = (givenArr) => {
  return givenArr
    .sort((a, b) => {
      return a - b;
    })
    .flatMap((x) => Array(2).fill(x));
};

/*
  Similar to sortDuplicateXRange() except it only duplicates 
  every element but the first and the last element.
  Special sort & duplicate function for GMS Plots for X range
*/
export const sortDuplicateYRange = (givenArr) => {
  return givenArr.flatMap((x, i) =>
    Array(i === 0 || i === givenArr.length - 1 ? 1 : 2).fill(x)
  );
};

/*
  react-select required a form in an array of objects
  [{
    value: value,
    label: readable value to display as options
  },...]
*/
export const createSelectArray = (options) => {
  return options.map((option) => ({
    value: option,
    label: option,
  }));
};

/* 
  For react-select but different to above
  Specially made for Project IDs - value and label are different
*/
export const createProjectIDArray = (options) => {
  let selectOptions = [];

  for (const [key, value] of Object.entries(options)) {
    selectOptions.push({ value: key, label: value });
  }

  return selectOptions;
};

/* 
  For react-select but different to above
  Specially made for Projects Vs30 - label to contain unit, m/s
*/
export const createVs30Array = (options) => {
  return options.map((option) => ({
    value: option,
    label: `${option} m/s`,
  }));
};

/* 
  For react-select but different to above
  Specially made for Projects Z1.0/Z2.5 - label to contain both Z1.0 and Z2.5 seperated and values to be a dictionary
*/
export const createZArray = (options) => {
  let selectOptions = options.map((option) => ({
    value: option,
    label:
      option["Z1.0"] == null && option["Z2.5"] == null
        ? "Default"
        : `${option["Z1.0"]}  |  ${option["Z2.5"]}`,
  }));
  selectOptions.sort((a, b) => {
    return a.value["Z1.0"] - b.value["Z1.0"];
  });
  return selectOptions;
};

// Check the Object is empty
export const isEmptyObj = (obj) => {
  return !Object.entries(obj).length;
};

/* 
  Disable the UHS input field.
  if pSA not in IM list
*/
export const isPSANotInIMList = (givenIMList) => {
  return !givenIMList.includes("pSA");
};

// Compare two arrays and check whether they are same
export const arrayEquals = (a, b) => {
  return (
    Array.isArray(a) &&
    Array.isArray(b) &&
    a.length === b.length &&
    a.every((val, index) => val === b[index])
  );
};

// For GMS - IM Contribution to convert IM to a proper readable format
export const GMSIMLabelConverter = (givenIM) => {
  const splitValue = givenIM.split("_");

  let convertedLabel = splitValue[0] === "pSA" ? "pSA" : splitValue[0];

  if (splitValue.length > 1) {
    convertedLabel += `(${splitValue[1]}s)`;
  }

  return convertedLabel;
};

/* 
  Query string builder for API
  Parameters:
  Key and Value pair in an Object
*/
export const APIQueryBuilder = (params) => {
  let queryString = "?";

  for (const [param, value] of Object.entries(params)) {
    queryString += `${param}=${value}&`;
  }

  // Remove last character which is an extra & symbol.
  return queryString.slice(0, -1);
};

// Create an object that contains bounds coordinates
export const createBoundsCoords = (xMin, xMax, yMin, yMax) => {
  return {
    topBoundX: [xMin, xMax],
    topBoundY: [yMax, yMax],
    rightBoundX: [xMax, xMax],
    rightBoundY: [yMin, yMax],
    bottomBoundX: [xMin, xMax],
    bottomBoundY: [yMin, yMin],
    leftBoundX: [xMin, xMin],
    leftBoundY: [yMin, yMax],
  };
};

/*
  JS version of qcore IM Sort
  Sort the IM Select dropdowns by the provided order
*/
const DEFAULT_PATTERN_ORDER = [
  "station",
  "component",
  "PGA",
  "PGV",
  "CAV",
  "AI",
  "Ds575",
  "Ds595",
  "Ds2080",
  "MMI",
  "pSA",
  "FAS",
  "IESDR",
];

export const sortIMs = (unsortedIMs) => {
  const adjIMs = [];

  if (unsortedIMs.length !== 0) {
    for (const pattern of DEFAULT_PATTERN_ORDER) {
      const curIMs = Array.from(unsortedIMs, (x) => {
        if (x.startsWith(pattern) === true) {
          return x;
        }
      });

      const filteredCurIMs = curIMs.filter((element) => {
        return element !== undefined;
      });

      if (filteredCurIMs.length === 0) {
        continue;
      } else if (filteredCurIMs.length === 1) {
        adjIMs.push(filteredCurIMs[0]);
      } else {
        const tempSortedIMs = filteredCurIMs.sort((a, b) => {
          return a.split("_")[1] - b.split("_")[1];
        });
        tempSortedIMs.forEach((x) => {
          adjIMs.push(x);
        });
      }
    }
  }

  return adjIMs;
};

/*
  Returned IM contains periods (For now, pSA)
  Split the IM and Periods
*/
export const splitIMPeriods = (IMs) => {
  const filteredIMs = [];
  const periods = [];

  for (let i = 0; i < IMs.length; i++) {
    let elements = IMs[i].split("_");
    if (elements.length > 1) {
      filteredIMs.push(elements[0]);
      periods.push(elements[1]);
    } else {
      filteredIMs.push(IMs[i]);
    }
  }

  return {
    IMs: filteredIMs,
    Periods: periods,
  };
};

/*
  Return combined IM with period
  if IM === pSA
  else IM
  In the future, instead of using IM === pSA
  ust an array to check if its in the list
  in case there are more than 1 IM with periods
*/
export const combineIMwithPeriod = (givenIM, givenPeriod) => {
  let combinedIM = givenIM;

  if (givenIM === "pSA") {
    return (combinedIM += `_${givenPeriod}`);
  }

  return combinedIM;
};

/**
 * Creates the station ID to send to the intermediate_api, adds Z1.0 / Z2.5 values only if not null
 * @param {*} projectLocation Location of the station
 * @param {*} projectVS30 The Vs30 value to use for that given station
 * @param {*} projectZ1p0 The Z1.0 value to use for that given station
 * @param {*} projectZ2p5 The Z2.5 value to use for that given station
 * @returns The station ID string to send to the intermediate API
 */
export const createStationID = (
  projectLocation,
  projectVS30,
  projectZ1p0,
  projectZ2p5
) => {
  return `${projectLocation}_${projectVS30}${
    projectZ1p0 == null ? "" : "_" + projectZ1p0.toString().replace(".", "p")
  }${
    projectZ2p5 == null ? "" : "_" + projectZ2p5.toString().replace(".", "p")
  }`;
};

/*
Create an axis label with symbol and unit
*/
export const createAxisLabel = (name, symbol = null, unit = null) => {
  let axisLabel = `${name}`;

  if (symbol) axisLabel += `, ${symbol}`;

  if (unit) {
    if (symbol) axisLabel += ` ${unit}`;
    else axisLabel += `, ${unit}`;
  }

  return axisLabel;
};
