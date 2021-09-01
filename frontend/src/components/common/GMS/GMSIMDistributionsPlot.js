import React from "react";

import Plot from "react-plotly.js";

import {
  PLOT_MARGIN,
  PLOT_CONFIG,
  GMS_IM_DISTRIBUTIONS_LABEL,
} from "constants/Constants";
import { range, sortDuplicateXRange, sortDuplicateYRange } from "utils/Utils";

import "assets/style/GMSPlot.css";

const GMSIMDistributionsPlot = ({ gmsData, IM }) => {
  const cdfX = gmsData["gcim_cdf_x"][IM];
  const cdfY = gmsData["gcim_cdf_y"][IM];
  // Create a new array to avoid affecting the original object from any modification
  const realisations = [...gmsData["realisations"][IM]];
  const selectedGMs = [...gmsData["selected_GMs"][IM]];
  const ksBounds = gmsData["ks_bounds"];

  // GCIM + KS Bounds
  const upperBounds = cdfY.map((x) => x + ksBounds);
  const yLimitAtOne = upperBounds.find((element) => element > 1);
  const yLimitAtOneIndex = upperBounds.indexOf(yLimitAtOne);

  // GCIM - KS Bounds
  const lowerBounds = cdfY.map((x) => x - ksBounds);
  const yLimitAtZero = lowerBounds.find((element) => element >= 0);
  const yLimitAtZeroIndex = lowerBounds.indexOf(yLimitAtZero);

  // sort then duplicate every element
  const newRealisations = sortDuplicateXRange(realisations);
  const newSelectedGMs = sortDuplicateXRange(selectedGMs);

  // Create an array between 0 and 1 by step(third param), refer to the function for more detail
  const rangeY = range(0, 1, 1 / realisations.length);

  // Duplicate the elements except the first and the last element
  const newRangeY = sortDuplicateYRange(rangeY);

  const labelMaker = (IM) => {
    let label = "";

    if (IM.startsWith("pSA")) {
      label += `Pseudo spectral acceleration, pSA(${IM.split("_")[1]}) (g)`;
    } else {
      label += GMS_IM_DISTRIBUTIONS_LABEL[IM];
    }

    return label;
  };

  return (
    <Plot
      className={"specific-im-plot"}
      data={[
        {
          x: cdfX,
          y: cdfY,
          mode: "lines",
          name: "GCIM",
          line: { shape: "hv", color: "red" },
          type: "scatter",
        },
        {
          x: cdfX.slice(0, yLimitAtOneIndex),
          y: upperBounds.slice(0, yLimitAtOneIndex),
          mode: "lines",
          name: `KS bounds, ${String.fromCharCode(945)} = 0.1`,
          legendgroup: "KS bounds",
          line: { dash: "dashdot", shape: "hv", color: "red" },
          type: "scatter",
        },
        {
          x: cdfX.slice(yLimitAtZeroIndex),
          y: lowerBounds.slice(yLimitAtZeroIndex),
          mode: "lines",
          name: "KS bounds",
          legendgroup: "KS bounds",
          line: { dash: "dashdot", shape: "hv", color: "red" },
          type: "scatter",
          showlegend: false,
        },
        {
          x: newRealisations,
          y: newRangeY,
          mode: "lines",
          name: "Realisations",
          line: { shape: "hv", color: "blue" },
          type: "scatter",
        },
        {
          x: newSelectedGMs,
          y: newRangeY,
          mode: "lines",
          name: "Selected Ground Motions",
          line: { shape: "hv", color: "black" },
          type: "scatter",
        },
      ]}
      layout={{
        xaxis: {
          title: { text: labelMaker(IM) },
          autorange: true,
        },
        yaxis: {
          title: { text: "Cumulative Probability, CDF" },
          range: [0, 1],
        },
        autosize: true,
        margin: PLOT_MARGIN,
      }}
      useResizeHandler={true}
      config={PLOT_CONFIG}
    />
  );
};

export default GMSIMDistributionsPlot;
