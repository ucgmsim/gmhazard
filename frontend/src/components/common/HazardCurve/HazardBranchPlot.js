import React from "react";

import Plot from "react-plotly.js";

import { getPlotData } from "utils/Utils";
import * as CONSTANTS from "constants/Constants";
import { ErrorMessage } from "components/common";

import "assets/style/HazardPlots.css";

const HazardBranchPlot = ({
  hazardData,
  nzs1170p5Data,
  percentileData = null,
  showNZCode = true,
  nztaData = null,
  extra,
}) => {
  if (hazardData !== null && !hazardData.hasOwnProperty("error")) {
    const branchHazard = hazardData["branches_hazard"];
    // // Create the scatter array for the branch totals
    const scatterArr = [];
    let dataCounter = 0;

    for (let [curName, curData] of Object.entries(branchHazard)) {
      let curPlotData = getPlotData(curData["total"]);
      scatterArr.push({
        x: curPlotData.index,
        y: curPlotData.values,
        type: "scatter",
        mode: "lines",
        line: { color: "gray", width: 0.5 },
        name: `${CONSTANTS.BRANCHES}`,
        legendgroup: "branches",
        showlegend: dataCounter === 0 ? true : false,
        hoverinfo: "none",
        hovertemplate:
          `<b>${curName}</b><br><br>` +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      });
      dataCounter += 1;
    }

    // Add the scatter object for the ensemble total
    const ensHazard = hazardData["ensemble_hazard"];
    const ensTotalData = getPlotData(ensHazard["total"]);
    scatterArr.push({
      x: ensTotalData.index,
      y: ensTotalData.values,
      type: "scatter",
      mode: "lines",
      line: { color: "red" },
      name: `${CONSTANTS.ENSEMBLE_MEAN}`,
      hoverinfo: "none",
      hovertemplate:
        `<b>${CONSTANTS.ENSEMBLE_MEAN}</b><br><br>` +
        "%{xaxis.title.text}: %{x}<br>" +
        "%{yaxis.title.text}: %{y}<extra></extra>",
    });

    // For NZS1170P5 code
    if (nzs1170p5Data) {
      const nzs1170p5 = getPlotData(nzs1170p5Data);
      scatterArr.push({
        x: nzs1170p5.values,
        y: nzs1170p5.index,
        type: "scatter",
        mode: "lines+markers",
        name: `${CONSTANTS.NZS1170P5}`,
        marker: {
          symbol: "triangle-up",
          size: 8,
        },
        line: { color: "black", dash: "dot" },
        visible: showNZCode,
        hoverinfo: "none",
        hovertemplate:
          `<b>${CONSTANTS.NZS1170P5}</b><br><br>` +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      });
    }

    // For NZTA code
    if (nztaData) {
      const nzta = getPlotData(nztaData);
      // Currently, Christchurch and Akaroa will return nan
      if (!nzta.values.includes("nan")) {
        scatterArr.push({
          x: nzta.values,
          y: nzta.index,
          type: "scatter",
          mode: "lines+markers",
          name: `${CONSTANTS.NZTA}`,
          marker: {
            symbol: "square-open",
            size: 8,
          },
          line: { color: "black", dash: "dot" },
          visible: showNZCode,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.NZTA}</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        });
      }
    }

    // For Percentiles
    if (percentileData) {
      const percentile16 = getPlotData(percentileData["16th"]);
      const percentile84 = getPlotData(percentileData["84th"]);
      scatterArr.push(
        {
          x: percentile16.index,
          y: percentile16.values,
          type: "scatter",
          mode: "lines",
          line: { color: "red", dash: "dash" },
          name: `${CONSTANTS.LOWER_PERCENTILE}`,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.LOWER_PERCENTILE}</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        },
        {
          x: percentile84.index,
          y: percentile84.values,
          type: "scatter",
          mode: "lines",
          line: { color: "red", dash: "dash" },
          name: `${CONSTANTS.UPPER_PERCENTILE}`,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.UPPER_PERCENTILE}</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        }
      );
    }

    return (
      <Plot
        className={"hazard-plot"}
        data={scatterArr}
        layout={{
          xaxis: {
            type: "log",
            title: { text: hazardData["im"] },
            showexponent: "first",
            exponentformat: "power",
            showline: true,
            linewidth: 3,
          },
          yaxis: {
            type: "log",
            title: { text: `${CONSTANTS.ANNUAL_RATE_OF_EXCEEDANCE}` },
            showexponent: "first",
            exponentformat: "power",
            range: [-5, 0],
            showline: true,
            linewidth: 3,
          },
          autosize: true,
          margin: CONSTANTS.PLOT_MARGIN,
          hovermode: "closest",
          hoverlabel: { bgcolor: "#FFF" },
        }}
        useResizeHandler={true}
        config={{
          ...CONSTANTS.PLOT_CONFIG,
          toImageButtonOptions: {
            filename:
              extra.from === "hazard"
                ? `Branches_Hazard_Plot_${hazardData["im"]}_Lat_${String(
                    parseFloat(extra.lat).toFixed(4)
                  ).replace(".", "p")}_Lng_${String(
                    parseFloat(extra.lng).toFixed(4)
                  ).replace(".", "p")}`
                : `Branches_Hazard_Plot_${extra.im}_project_id_${extra.id}_location_${extra.location}_vs30_${extra.vs30}`,
          },
        }}
      />
    );
  }
  return <ErrorMessage />;
};

export default HazardBranchPlot;
