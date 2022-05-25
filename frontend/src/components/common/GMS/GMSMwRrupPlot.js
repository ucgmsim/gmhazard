import React from "react";

import Plot from "react-plotly.js";

import * as CONSTANTS from "constants/Constants";

import "assets/style/GMSPlot.css";

const GMSMwRrupPlot = ({
  metadata,
  bounds,
  meanValues = null,
  numGMs = null,
}) => {
  // To set a range for X-axis to get a gap
  const rangeXMin = Math.min(...metadata["rrup"], bounds["topBoundX"][0]) * 0.9;
  const rangeXMax = Math.max(...metadata["rrup"], bounds["topBoundX"][1]) * 1.1;

  // Mean & 16/84th percentiles with selected_gms_metadata data
  const selectedGMSAgg = metadata["selected_gms_agg"];

  const scatterData = [
    {
      x: metadata["rrup"],
      y: metadata["mag"],
      mode: "markers",
      name:
        numGMs !== null
          ? `${CONSTANTS.SHORTEN_SELECTED_GM}, N${"gm".sub()}=${numGMs}`
          : `${CONSTANTS.SHORTEN_SELECTED_GM}, N${"gm".sub()}=${
              metadata["mag"].length
            }`,
      marker: { symbol: "square-open" },
      line: { color: "black" },
      type: "scatter",
      showlegend: true,
    },
    {
      x: bounds.topBoundX,
      y: bounds.topBoundY,
      legendgroup: "Bounds",
      mode: "lines",
      name: `${CONSTANTS.BOUNDS}`,
      line: { color: "red", dash: "dot" },
      type: "scatter",
      showlegend: true,
    },
    {
      x: bounds.rightBoundX,
      y: bounds.rightBoundY,
      legendgroup: "Bounds",
      mode: "lines",
      name: `${CONSTANTS.BOUNDS}`,
      line: { color: "red", dash: "dot" },
      type: "scatter",
      showlegend: false,
    },
    {
      x: bounds.bottomBoundX,
      y: bounds.bottomBoundY,
      legendgroup: "Bounds",
      mode: "lines",
      name: `${CONSTANTS.BOUNDS}`,
      line: { color: "red", dash: "dot" },
      type: "scatter",
      showlegend: false,
    },
    {
      x: bounds.leftBoundX,
      y: bounds.leftBoundY,
      legendgroup: "Bounds",
      mode: "lines",
      name: `${CONSTANTS.BOUNDS}`,
      line: { color: "red", dash: "dot" },
      type: "scatter",
      showlegend: false,
    },
  ];

  // Currently, projects do not have the following data yet
  if (meanValues !== null) {
    // Mean & 16/84th percentiles with disagg_mean_values data
    scatterData.push(
      {
        x: [meanValues["rrup"]],
        y: [meanValues["magnitude"]],
        name:
          `Mean M${"w".sub()}-R${"rup".sub()} of disaggregation distribution<br>` +
          `16${"th".sup()} to 84${"th".sup()} percentile M${"w".sub()}-R${"rup".sub()} limits`,
        marker: { symbol: "105", size: 12 },
        line: { color: "red" },
        error_x: {
          type: "data",
          symmetric: false,
          array: [meanValues["rrup_84th"] - meanValues["rrup"]],
          arrayminus: [meanValues["rrup"] - meanValues["rrup_16th"]],
          visible: true,
          color: "rgba(255, 0, 0, 0.4)",
        },
        error_y: {
          type: "data",
          symmetric: false,
          array: [meanValues["magnitude_84th"] - meanValues["magnitude"]],
          arrayminus: [meanValues["magnitude"] - meanValues["magnitude_16th"]],
          visible: true,
          color: "rgba(255, 0, 0, 0.4)",
        },
        type: "scatter",
      },
      // Mean & 16/84th percentiles with selected_gms_metadata data
      {
        x: [selectedGMSAgg["rrup_mean"]],
        y: [selectedGMSAgg["mag_mean"]],
        name:
          `Mean M${"w".sub()}-R${"rup".sub()} of selected GMs<br>` +
          `16${"th".sup()} to 84${"th".sup()} percentile M${"w".sub()}-R${"rup".sub()} limits`,
        marker: { symbol: "105", size: 12 },
        line: { color: "black" },
        error_x: {
          type: "data",
          symmetric: false,
          array: [
            selectedGMSAgg["rrup_error_bounds"][1] -
              selectedGMSAgg["rrup_mean"],
          ],
          arrayminus: [
            selectedGMSAgg["rrup_mean"] -
              selectedGMSAgg["rrup_error_bounds"][0],
          ],
          visible: true,
          color: "rgba(0, 0, 0, 0.4)",
        },
        error_y: {
          type: "data",
          symmetric: false,
          array: [
            selectedGMSAgg["mag_error_bounds"][1] - selectedGMSAgg["mag_mean"],
          ],
          arrayminus: [
            selectedGMSAgg["mag_mean"] - selectedGMSAgg["mag_error_bounds"][0],
          ],
          visible: true,
          color: "rgba(0, 0, 0, 0.4)",
        },
        type: "scatter",
      }
    );
  }

  return (
    <Plot
      className={"third-plot"}
      data={scatterData}
      layout={{
        xaxis: {
          type: "log",
          title: {
            text: `${CONSTANTS.RUPTURE_DISTANCE}, R${"rup".sub()} ${
              CONSTANTS.KILOMETRE
            }`,
          },
          showexponent: "first",
          exponentformat: "power",
          range: [Math.log10(rangeXMin), Math.log10(rangeXMax)],
          autorange: false,
        },
        yaxis: {
          title: { text: `${CONSTANTS.MAGNITUDE}, M${"W".sub()}` },
          autorange: true,
        },
        autosize: true,
        margin: CONSTANTS.PLOT_MARGIN,
      }}
      useResizeHandler={true}
      config={CONSTANTS.PLOT_CONFIG}
    />
  );
};

export default GMSMwRrupPlot;
