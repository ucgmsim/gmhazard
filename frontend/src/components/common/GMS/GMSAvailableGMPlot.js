import React from "react";

import Plot from "react-plotly.js";

import * as CONSTANTS from "constants/Constants";

import "assets/style/GMSPlot.css";

const GMSAvailableGMPlot = ({ metadata, bounds, numGMs }) => {
  // To set a range for X-axis to get a gap
  const rangeXMin = Math.min(...metadata["rrup"], bounds["topBoundX"][0]) * 0.9;
  const rangeXMax = Math.max(...metadata["rrup"], bounds["topBoundX"][1]) * 1.1;

  return (
    <Plot
      className={"third-plot"}
      data={[
        {
          x: metadata["rrup"],
          y: metadata["mag"],
          mode: "markers",
          name:
            `Dataset GMs (for the datapoints), N=${metadata["rrup"].length}<br>` +
            `Causal params bounding box (for the bounding box), N=${numGMs}`,
          marker: { symbol: "square-open" },
          line: { color: "grey" },
          type: "scattergl",
        },
        {
          x: bounds.topBoundX,
          y: bounds.topBoundY,
          legendgroup: "Bounds",
          mode: "lines",
          name: `${CONSTANTS.BOUNDS}`,
          line: { color: "red", dash: "dot" },
          type: "scatter",
          showlegend: false,
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
      ]}
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
        },
        yaxis: {
          title: { text: `${CONSTANTS.GMS_PLOT_MAG_AXIS_LABEL}` },
          autorange: true,
          showline: true,
          linewidth: 3,
        },
        legend: {
          x: 0,
          y: 1,
          font: { size: 12, color: "#000" },
          bgcolor: "#FFF",
          bordercolor: "#000",
          borderwidth: 1,
        },
        autosize: true,
        margin: CONSTANTS.PLOT_MARGIN,
      }}
      onLegendClick={() => false}
      useResizeHandler={true}
      config={CONSTANTS.PLOT_CONFIG}
    />
  );
};

export default GMSAvailableGMPlot;
