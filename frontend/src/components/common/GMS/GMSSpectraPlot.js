import React, { memo } from "react";

import Plot from "react-plotly.js";

import * as CONSTANTS from "constants/Constants";
import { createAxisLabel } from "utils/Utils";

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
          title: {
            text: createAxisLabel(
              CONSTANTS.PERIOD,
              CONSTANTS.PERIOD_SYMBOL,
              CONSTANTS.SECONDS_UNIT
            ),
          },
          showexponent: "first",
          exponentformat: "power",
          autorange: true,
          showline: true,
          linewidth: CONSTANTS.PLOT_LINE_WIDTH,
          zeroline: false,
        },
        yaxis: {
          type: "log",
          title: {
            text: createAxisLabel(
              CONSTANTS.SPECTRAL_ACCELERATION,
              CONSTANTS.SPECTRAL_ACCELERATION_SYMBOL,
              CONSTANTS.GRAVITY_UNIT
            ),
          },
          showexponent: "first",
          exponentformat: "power",
          autorange: true,
          showline: true,
          linewidth: CONSTANTS.PLOT_LINE_WIDTH,
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

export default memo(GMSSpectraPlot);
