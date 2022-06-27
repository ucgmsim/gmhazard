import React from "react";

import Plot from "react-plotly.js";

import { getPlotData } from "utils/Utils";
import { ErrorMessage } from "components/common";
import * as CONSTANTS from "constants/Constants";

import "assets/style/HazardPlots.css";

const HazardEnsemblePlot = ({
  hazardData,
  nzs1170p5Data,
  percentileData = null,
  showNZCode = true,
  nztaData = null,
  extra,
}) => {
  if (hazardData !== null && !hazardData.hasOwnProperty("error")) {
    const ensHazard = hazardData["ensemble_hazard"];
    const plotData = {};

    for (let typeKey of ["fault", "ds", "total"]) {
      plotData[typeKey] = getPlotData(ensHazard[typeKey]);
    }

    const scatterArr = [
      // Fault
      {
        x: plotData["fault"].index,
        y: plotData["fault"].values,
        type: "scatter",
        mode: "lines",
        name: `${CONSTANTS.FAULT}`,
        line: { color: "black" },
        hoverinfo: "none",
        hovertemplate:
          `<b>${CONSTANTS.FAULT}</b><br><br>` +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      },
      // DS
      {
        x: plotData["ds"].index,
        y: plotData["ds"].values,
        type: "scatter",
        mode: "lines",
        name: CONSTANTS.DISTRIBUTED_SEISMICITY,
        line: { color: "green" },
        hoverinfo: "none",
        hovertemplate:
          `<b>${CONSTANTS.DISTRIBUTED_SEISMICITY}</b><br><br>` +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      },
      // Total
      {
        x: plotData["total"].index,
        y: plotData["total"].values,
        type: "scatter",
        mode: "lines",
        name: `${CONSTANTS.TOTAL}`,
        line: { color: "red" },
        hoverinfo: "none",
        hovertemplate:
          `<b>${CONSTANTS.TOTAL}</b><br><br>` +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      },
    ];

    // NZS1170P5 code
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

    // Percentiles
    if (percentileData) {
      const percentile16 = getPlotData(percentileData["16th"]);
      const percentile84 = getPlotData(percentileData["84th"]);
      // Percentile 16
      scatterArr.push(
        {
          x: percentile16.index,
          y: percentile16.values,
          type: "scatter",
          mode: "lines",
          name: `${CONSTANTS.LOWER_PERCENTILE}`,
          line: { color: "red", dash: "dash" },
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.LOWER_PERCENTILE}</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        },
        // Percentile 84
        {
          x: percentile84.index,
          y: percentile84.values,
          type: "scatter",
          mode: "lines",
          name: `${CONSTANTS.UPPER_PERCENTILE}`,
          line: { color: "red", dash: "dash" },
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
                ? `Hazard_Plot_${hazardData["im"]}_Lat_${String(
                    parseFloat(extra.lat).toFixed(4)
                  ).replace(".", "p")}_Lng_${String(
                    parseFloat(extra.lng).toFixed(4)
                  ).replace(".", "p")}`
                : `Hazard_Plot_${extra.im}_project_id_${extra.id}_location_${extra.location}_vs30_${extra.vs30}`,
          },
        }}
      />
    );
  }
  return <ErrorMessage />;
};

export default HazardEnsemblePlot;
