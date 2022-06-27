import React from "react";

import Plot from "react-plotly.js";

import { createAxisLabel } from "utils/Utils";
import { ErrorMessage } from "components/common";
import * as CONSTANTS from "constants/Constants";

import "assets/style/ScenarioPlot.css";

const ScenarioPlot = ({ scenarioData, scenarioSelectedRuptures, extra }) => {
  if (scenarioData !== null && !scenarioData.hasOwnProperty("error")) {
    const percentileData16 =
      scenarioData["ensemble_scenario"]["percentiles"]["16th"];
    const muData = scenarioData["ensemble_scenario"]["mu_data"];
    const percentileData84 =
      scenarioData["ensemble_scenario"]["percentiles"]["84th"];
    const ims = scenarioData["ensemble_scenario"]["ims"];
    const scatterObjs = [];
    const deafultColours = [
      "blue",
      "darkorange",
      "green",
      "red",
      "purple",
      "yellow",
      "pink",
      "lightblue",
      "maroon",
      "grey",
    ];

    // Gets all the periods if PGA or pSA else adds IM's for the x values
    const xValues = [];
    ims.forEach((IM) => {
      if (IM === "PGA") xValues.push("0");
      else if (IM.includes("pSA")) xValues.push(IM.split("_")[1]);
      else xValues.push(IM);
    });

    let colourCounter = 0;
    for (let [curRup, curData] of Object.entries(muData)) {
      if (scenarioSelectedRuptures.includes(curRup)) {
        scatterObjs.push({
          x: xValues,
          y: curData,
          type: "scatter",
          mode: "lines",
          line: { color: deafultColours[colourCounter % 10] },
          name: `${curRup} [mean and 16<sup>th</sup>, 84<sup>th</sup> percentile]`,
          legendgroup: `${curRup}`,
          showlegend: true,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.SITE_SPECIFIC} [Mean Rupture ${curRup}]</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        });
        colourCounter += 1;
      }
    }

    // Percentiles
    colourCounter = 0;
    for (let [curRup, curData] of Object.entries(percentileData16)) {
      if (scenarioSelectedRuptures.includes(curRup)) {
        scatterObjs.push({
          x: xValues,
          y: curData,
          type: "scatter",
          mode: "lines",
          line: { color: deafultColours[colourCounter % 10], dash: "dash" },
          name: "Rupture 16th Percentile",
          legendgroup: `${curRup}`,
          showlegend: false,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.SITE_SPECIFIC} [16th Pecentile Rupture ${curRup}]</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        });
        colourCounter += 1;
      }
    }
    colourCounter = 0;
    for (let [curRup, curData] of Object.entries(percentileData84)) {
      if (scenarioSelectedRuptures.includes(curRup)) {
        scatterObjs.push({
          x: xValues,
          y: curData,
          type: "scatter",
          mode: "lines",
          line: { color: deafultColours[colourCounter % 10], dash: "dash" },
          name: "Rupture 84th Percentile",
          legendgroup: `${curRup}`,
          showlegend: false,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.SITE_SPECIFIC} [84th Pecentile Rupture ${curRup}]</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        });
        colourCounter += 1;
      }
    }

    return (
      <Plot
        className={"scenario-plot"}
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
            showline: true,
            linewidth: CONSTANTS.PLOT_LINE_WIDTH,
            zeroline: false,
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
                ? `Scenario_Plot_Lat_${String(
                    parseFloat(extra.lat).toFixed(4)
                  ).replace(".", "p")}_Lng_${String(
                    parseFloat(extra.lng).toFixed(4)
                  ).replace(".", "p")}`
                : `Scenario_Plot_project_id_${extra.id}_location_${extra.location}_vs30_${extra.vs30}`,
          },
        }}
      />
    );
  }
  return <ErrorMessage />;
};

export default ScenarioPlot;
