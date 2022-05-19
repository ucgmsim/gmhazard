import React from "react";

import Plot from "react-plotly.js";

import { PLOT_MARGIN, PLOT_CONFIG, GMS_LABELS } from "constants/Constants";
import { range, sortDuplicateXRange, sortDuplicateYRange } from "utils/Utils";

import "assets/style/GMSPlot.css";

const GMSDisaggDistributionPlot = ({
  contribution,
  distribution,
  selectedGMSMetadata,
  bounds,
  label,
}) => {
  /*
    Create a new array to avoid affecting the original object from any modification
    then sort metadata & duplicate every element
  */
  const xRange = sortDuplicateXRange([...selectedGMSMetadata]);

  // Create an array between 0 and 1 by step(third param), refer to the function for more detail
  const rangeY = range(0, 1, 1 / selectedGMSMetadata.length);

  // Duplicate the elements except the first and the last element
  const newRangeY = sortDuplicateYRange(rangeY);

  const scattersArray = [
    {
      x: xRange,
      y: newRangeY,
      mode: "lines+markers",
      name: `${GMS_LABELS[label]}`,
      line: { shape: "hv", color: "black" },
      type: "scatter",
      showlegend: true,
    },
  ];

  scattersArray.push({
    x: distribution,
    y: contribution,
    mode: "lines",
    name: "Disaggregation distribution",
    line: { color: "red", dash: "dot" },
    type: "scatter",
    showlegend: true,
  });

  // Y coordiates for bounds
  const boundsRangeY = [0, 1];

  // Add bounds (Min / Max)
  scattersArray.push(
    {
      x: [bounds["min"], bounds["min"]],
      y: boundsRangeY,
      legendgroup: label,
      name: "Lower and upper bound limits",
      mode: "lines",
      line: { color: "grey", dash: "dot" },
      type: "scatter",
    },
    {
      x: [bounds["max"], bounds["max"]],
      y: boundsRangeY,
      legendgroup: label,
      name: "Lower and upper bound limits",
      mode: "lines",
      line: { color: "grey", dash: "dot" },
      type: "scatter",
      showlegend: false,
    }
  );

  // Setting xRange with a same padding on both sides
  const minXCoord = Math.min(...xRange, ...distribution, bounds["min"]);
  const maxXCoord = Math.max(...xRange, ...distribution, bounds["max"]);

  const xAxisGap = label === "mag" ? minXCoord * 0.01 : minXCoord * 0.05;
  const xAxisMin = minXCoord - xAxisGap;
  const xAxisMax = maxXCoord + xAxisGap;

  return (
    <Plot
      className={"third-plot"}
      data={scattersArray}
      layout={{
        xaxis: {
          type: "log",
          title: { text: `${GMS_LABELS[label]}` },
          showexponent: "first",
          exponentformat: "power",
          range: [Math.log10(xAxisMin), Math.log10(xAxisMax)],
          autorange: false,
        },
        yaxis: {
          title: { text: "Cumulative Probability, CDF" },
          autorange: true,
        },
        autosize: true,
        margin: PLOT_MARGIN,
      }}
      useResizeHandler={true}
      config={PLOT_CONFIG}
    />
  );
};

export default GMSDisaggDistributionPlot;
