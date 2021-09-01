import React from "react";

import Plot from "react-plotly.js";

import { getPlotData } from "utils/Utils";
import { PLOT_MARGIN, PLOT_CONFIG } from "constants/Constants";
import { ErrorMessage } from "components/common";

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
        name: "Fault",
        line: { color: "red" },
        hoverinfo: "none",
        hovertemplate:
          "<b>Fault</b><br><br>" +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      },
      // DS
      {
        x: plotData["ds"].index,
        y: plotData["ds"].values,
        type: "scatter",
        mode: "lines",
        name: "Distributed",
        line: { color: "green" },
        hoverinfo: "none",
        hovertemplate:
          "<b>Distributed</b><br><br>" +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      },
      // Total
      {
        x: plotData["total"].index,
        y: plotData["total"].values,
        type: "scatter",
        mode: "lines",
        name: "Total",
        line: { color: "black" },
        hoverinfo: "none",
        hovertemplate:
          "<b>Total</b><br><br>" +
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
        name: "NZS1170.5",
        marker: {
          symbol: "triangle-up",
          size: 8,
        },
        line: { color: "black", dash: "dot" },
        visible: showNZCode,
        hoverinfo: "none",
        hovertemplate:
          "<b>NZS1170.5</b><br><br>" +
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
          name: "NZTA",
          marker: {
            symbol: "square-open",
            size: 8,
          },
          line: { color: "black", dash: "dot" },
          visible: showNZCode,
          hoverinfo: "none",
          hovertemplate:
            "<b>NZTA</b><br><br>" +
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
          name: "16th Percentile",
          line: { color: "black", dash: "dash" },
          hoverinfo: "none",
          hovertemplate:
            "<b>16<sup>th</sup> percentiles</b><br><br>" +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        },
        // Percentile 84
        {
          x: percentile84.index,
          y: percentile84.values,
          type: "scatter",
          mode: "lines",
          name: "84th Percentile",
          line: { color: "black", dash: "dash" },
          hoverinfo: "none",
          hovertemplate:
            "<b>84<sup>th</sup> percentiles</b><br><br>" +
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
          },
          yaxis: {
            type: "log",
            title: { text: "Annual rate of exceedance" },
            showexponent: "first",
            exponentformat: "power",
            range: [-5, 0],
          },
          autosize: true,
          margin: PLOT_MARGIN,
          hovermode: "closest",
          hoverlabel: { bgcolor: "#FFF" },
        }}
        useResizeHandler={true}
        config={{
          ...PLOT_CONFIG,
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
