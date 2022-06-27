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
          ? `${CONSTANTS.SHORTEN_SELECTED_GM}, ${CONSTANTS.NUMBER_OF_GROUND_MOTIONS_SUBSCRIPT}=${numGMs}`
          : `${CONSTANTS.SHORTEN_SELECTED_GM}, ${CONSTANTS.NUMBER_OF_GROUND_MOTIONS_SUBSCRIPT}=${metadata["mag"].length}`,
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
        name: `${CONSTANTS.MW_RRUP_PLOT_DISAGG_MEAN_VALUES_LABEL}`,
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
        name: `${CONSTANTS.MW_RRUP_PLOT_SELECTED_GMS_METADATA_LABEL}`,
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
            text: `${CONSTANTS.GMS_PLOT_RRUP_AXIS_LABEL}`,
          },
          showexponent: "first",
          exponentformat: "power",
          range: [Math.log10(rangeXMin), Math.log10(rangeXMax)],
          autorange: false,
          showline: true,
          linewidth: 3,
          zeroline: false,
        },
        yaxis: {
          title: { text: `${CONSTANTS.GMS_PLOT_MAG_AXIS_LABEL}` },
          autorange: true,
          showline: true,
          linewidth: 3,
          zeroline: false,
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
