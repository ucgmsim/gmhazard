import React from "react";

import Plot from "react-plotly.js";

import { PLOT_MARGIN, PLOT_CONFIG } from "constants/Constants";

import "assets/style/GMSPlot.css";

const GMSSpectraPlot = ({ GMSSpectraData }) => {
  return GMSSpectraData.length === 0 ? (
    // TODO: When we have a proper error component/page not found, replace with them.
    <p>something went wrong</p>
  ) : (
    <Plot
      className={"second-plot"}
      data={GMSSpectraData}
      layout={{
        xaxis: {
          type: "log",
          title: { text: "Period, T (s)" },
          showexponent: "first",
          exponentformat: "power",
          autorange: true,
        },
        yaxis: {
          type: "log",
          title: { text: "Spectral acceleration, SA (g)" },
          showexponent: "first",
          exponentformat: "power",
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

export default GMSSpectraPlot;
