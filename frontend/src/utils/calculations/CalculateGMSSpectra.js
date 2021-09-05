import { sortIMs } from "utils/Utils";

export const calculateGMSSpectra = (gmsData, numGMs) => {
  const plotDataArr = [];

  try {
    const cdfX = gmsData["gcim_cdf_x"];
    const cdfY = gmsData["gcim_cdf_y"];
    const realisations = gmsData["realisations"];
    const selectedGMs = gmsData["selected_GMs"];
    const im_j = gmsData["im_j"];
    // Create a new array to avoid affecting the original object from any modification
    const periods = [...gmsData["IMs"]];
    const im_type = gmsData["IM_j"];

    // If IM Type starts with pSA, add it to periods array
    if (im_type.startsWith("pSA")) {
      periods.push(im_type);
    }

    // Create an object, {key = IM, value = Period}
    const localPeriods = {};
    sortIMs(periods).forEach((IM) => {
      // IM starts with pSA, has a period.
      if (IM.startsWith("pSA")) {
        localPeriods[IM] = IM.split("_")[1];
      }
    });

    const periodsArray = Object.values(localPeriods);

    const sortedCDFX = {};
    const sortedCDFY = {};
    const sortedRealisations = {};
    const sortedSelectedGMs = {};

    /*
      Create four new objects in the right order for the following data:
      - CDF X
      - CDF Y
      - Realisations
      - Selected GMs
    */
    for (const [IM, values] of Object.entries(localPeriods)) {
      /* 
        Use the original data as value
        if IM is not equal to im_type(selected IM by the user)
        else, use agreed values (values, im_j, selectedGMs[IM])
      */
      if (IM !== im_type) {
        sortedCDFX[IM] = cdfX[IM];
        sortedCDFY[IM] = cdfY[IM];
        sortedRealisations[IM] = realisations[IM];
        sortedSelectedGMs[IM] = selectedGMs[IM];
      } else {
        sortedCDFX[IM] = values;
        sortedCDFY[IM] = im_j;
        sortedRealisations[IM] = im_j;
        sortedSelectedGMs[IM] = selectedGMs[IM];
      }
    }

    // GCIM calculations
    const medianIndexObj = {};
    const lowerPercenIndexObj = {};
    const higherPercenIndexObj = {};

    // compare Y value to 0.5 (Median), 0.16 (16th percentile) and 0.84 (84th percentile)
    for (const [IM, values] of Object.entries(sortedCDFY)) {
      /* 
        Find Median, percentiles values
        if IM is not equal to im_type(selected IM by the user)
        else use im_j value
      */
      if (IM !== im_type) {
        // Median
        const medianFound = values.find((element) => element >= 0.5);
        medianIndexObj[IM] = values.indexOf(medianFound);

        // 0.16 (16th percentile)
        const lowerPercentileFound = values.find((element) => element >= 0.16);
        lowerPercenIndexObj[IM] = values.indexOf(lowerPercentileFound);

        // 0.84 (84th percentile)
        const higherPercentileFound = values.find((element) => element >= 0.84);
        higherPercenIndexObj[IM] = values.indexOf(higherPercentileFound);
      } else {
        medianIndexObj[IM] = im_j;
        lowerPercenIndexObj[IM] = im_j;
        higherPercenIndexObj[IM] = im_j;
      }
    }

    const upperPercenValues = [];
    const medianValues = [];
    const lowerPercenValues = [];

    for (const [IM, values] of Object.entries(sortedCDFX)) {
      /* 
        Find Median, percentiles values
        if IM is not equal to im_type(selected IM by the user)
      */
      if (IM !== im_type) {
        upperPercenValues.push(values[higherPercenIndexObj[IM]]);
        medianValues.push(values[medianIndexObj[IM]]);
        lowerPercenValues.push(values[lowerPercenIndexObj[IM]]);
      } else {
        upperPercenValues.push(im_j);
        medianValues.push(im_j);
        lowerPercenValues.push(im_j);
      }
    }

    // GCIM Plots
    plotDataArr.push(
      {
        x: periodsArray,
        y: upperPercenValues,
        mode: "lines",
        name: `GCIM - 84${"th".sup()} Percentile`,
        line: { dash: "dashdot", color: "red" },
        type: "scatter",
        hoverinfo: "none",
      },
      {
        x: periodsArray,
        y: medianValues,
        mode: "lines",
        name: "GCIM - Median",
        line: { color: "red" },
        type: "scatter",
        hoverinfo: "none",
      },
      {
        x: periodsArray,
        y: lowerPercenValues,
        mode: "lines",
        name: `GCIM - 16${"th".sup()} percentile`,
        line: { dash: "dashdot", color: "red" },
        type: "scatter",
        hoverinfo: "none",
      }
    );

    /*
      Realisations calculation
      The first for loop is there to set the index
      The second for loop is there to put every IM's index realisation value.

      E.g.,
      pSA_0.01: [1,2,3]
      pSA_0.02: [2,3,4]
      pSA_0.03: [4,5,6]

      after this loop, we plot three lines like the following,
      X array = [0.01, 0.02, 0.03] (Because X-axis is periods)
      Y array = [1,2,4] (first index)
              = [2,3,5] (second index)
              = [3,4,6] (third index)
    */
    for (let i = 0; i < numGMs; i++) {
      let yCoords = [];
      for (const IM of Object.keys(sortedRealisations)) {
        if (IM !== im_type) {
          yCoords.push(sortedRealisations[IM][i]);
        } else {
          yCoords.push(sortedRealisations[IM]);
        }
      }

      plotDataArr.push({
        x: periodsArray,
        y: yCoords,
        legendgroup: "Realisations",
        mode: "lines",
        name: "Realisations",
        line: { color: "blue", width: 0.7 },
        type: "scatter",
        showlegend: i === 0 ? true : false,
        hoverinfo: "none",
      });
    }
    /*
      Selected GMs calculation
      Same as Realisations calculation above.
      Except, because Selected GMs come with selected IM Type's values.
      So no need to check whether the IM Type is the same as IM.
    */
    for (let i = 0; i < numGMs; i++) {
      let yCoords = [];
      for (const IM of Object.keys(sortedSelectedGMs)) {
        yCoords.push(sortedSelectedGMs[IM][i]);
      }

      plotDataArr.push({
        x: periodsArray,
        y: yCoords,
        legendgroup: "Selected GMs",
        mode: "lines",
        name: "Selected Ground Motions",
        line: { color: "black", width: 0.7 },
        type: "scatter",
        showlegend: i === 0 ? true : false,
        hoverinfo: "none",
      });
    }

    return plotDataArr;
  } catch (err) {
    console.log(err.message);
    return [];
  }
};
