import React from "react";

import Plot from "react-plotly.js";

import * as CONSTANTS from "constants/Constants";
import { ErrorMessage } from "components/common";
import { getPlotData, createAxisLabel } from "utils/Utils";

import "assets/style/UHSPlot.css";

const UHSBranchPlot = ({
  uhsData,
  uhsBranchData,
  nzs1170p5Data,
  rate,
  extra,
  showNZS1170p5 = true,
}) => {
  if (uhsData && !uhsData.hasOwnProperty("error")) {
    const createLegendLabel = (isNZCode) => {
      return isNZCode === true
        ? `${CONSTANTS.NZS1170P5} [Rate = ${rate}]`
        : `${CONSTANTS.SITE_SPECIFIC} [Rate = ${rate}]`;
    };

    // Creating the scatter objects
    const scatterObjs = [];

    // UHS Branches scatter objs
    let dataCounter = 0;
    if (uhsBranchData !== null) {
      for (let curData of Object.values(uhsBranchData)) {
        // Skip any plots if it contains nan
        if (!curData.sa_values.includes("nan")) {
          // The first value is from PGA, hence do not inlcude
          scatterObjs.push({
            x: curData.period_values.slice(1),
            y: curData.sa_values.slice(1),
            mode: "lines",
            line: { color: "grey", width: 0.8 },
            name: `${CONSTANTS.BRANCHES}`,
            legendgroup: "branches",
            showlegend: dataCounter === 0 ? true : false,
            hoverinfo: "none",
            hovertemplate:
              `<b>${curData.branch_name}</b><br><br>` +
              "%{xaxis.title.text}: %{x}<br>" +
              "%{yaxis.title.text}: %{y}<extra></extra>",
          });
          dataCounter += 1;
        }
      }
    }

    // UHS scatter objs
    if (!uhsData.sa_values.includes("nan")) {
      // The first value is from PGA, hence do not inlcude
      scatterObjs.push({
        x: uhsData.period_values.slice(1),
        y: uhsData.sa_values.slice(1),
        mode: "lines",
        line: { color: "red" },
        name: createLegendLabel(false),
        legendgroup: "site-specific",
        showlegend: true,
        hoverinfo: "none",
        hovertemplate:
          `<b>${CONSTANTS.SITE_SPECIFIC} [Rate = ${rate}]</b><br><br>` +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      });
    }

    // For Percentiles
    if (uhsData.percentiles) {
      const percentile16 = getPlotData(uhsData.percentiles["16th"]);
      const percentile84 = getPlotData(uhsData.percentiles["84th"]);
      // The first value is from PGA, hence do not inlcude
      if (!percentile16.values.includes("nan")) {
        scatterObjs.push({
          x: percentile16.index.slice(1),
          y: percentile16.values.slice(1),
          mode: "lines",
          line: { color: "red", dash: "dash" },
          name: `${CONSTANTS.LOWER_PERCENTILE}`,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.LOWER_PERCENTILE}</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        });
      }
      if (!percentile84.values.includes("nan")) {
        scatterObjs.push({
          x: percentile84.index.slice(1),
          y: percentile84.values.slice(1),
          mode: "lines",
          line: { color: "red", dash: "dash" },
          name: `${CONSTANTS.UPPER_PERCENTILE}`,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.UPPER_PERCENTILE}</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        });
      }
    }

    // Create NZS1170p5 Code UHS scatter objs
    // If object does not contain the value of NaN, we plot
    if (!Object.values(nzs1170p5Data).includes("nan")) {
      let nzs1170p5PlotData = getPlotData(nzs1170p5Data);
      scatterObjs.push({
        x: nzs1170p5PlotData.index,
        y: nzs1170p5PlotData.values,
        mode: "lines",
        line: { color: "black" },
        name: createLegendLabel(true),
        visible: showNZS1170p5,
        legendgroup: "NZS1170.5",
        showlegend: true,
        hoverinfo: "none",
        hovertemplate:
          `<b>${CONSTANTS.NZS1170P5} [Rate = ${rate}]</b><br><br>` +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      });
    }

    return (
      <Plot
        className={"uhs-plot"}
        data={scatterObjs}
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
            exponentformat: "power",
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
            exponentformat: "power",
            showline: true,
            linewidth: CONSTANTS.PLOT_LINE_WIDTH,
            zeroline: false,
          },
          autosize: true,
          margin: CONSTANTS.PLOT_MARGIN,
          hovermode: "closest",
          hoverlabel: { bgcolor: "#FFF" },
          legend: {
            x: 1,
            xanchor: "right",
            y: 1,
          },
        }}
        useResizeHandler={true}
        config={{
          ...CONSTANTS.PLOT_CONFIG,
          toImageButtonOptions: {
            filename:
              extra.from === "hazard"
                ? `UHS_Plot_Lat_${String(
                    parseFloat(extra.lat).toFixed(4)
                  ).replace(".", "p")}_Lng_${String(
                    parseFloat(extra.lng).toFixed(4)
                  ).replace(".", "p")}`
                : `UHS_Plot_project_id_${extra.id}_location_${extra.location}_vs30_${extra.vs30}`,
          },
        }}
      />
    );
  }
  return <ErrorMessage />;
};

export default UHSBranchPlot;
