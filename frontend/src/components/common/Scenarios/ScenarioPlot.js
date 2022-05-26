import React from "react";

import Plot from "react-plotly.js";

import { ErrorMessage } from "components/common";
import * as CONSTANTS from "constants/Constants";

import "assets/style/ScenarioPlot.css";

const ScenarioPlot = ({ scenarioData, scenarioSelectedRuptures, extra }) => {
  if (scenarioData !== null && !scenarioData.hasOwnProperty("error")) {
    const percentileData16 =
      scenarioData["ensemble_scenario"]["percentiles"]["16th"];
    const percentileData50 =
      scenarioData["ensemble_scenario"]["percentiles"]["50th"];
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
    const x_values = [];
    ims.forEach((IM) => {
      if (IM === "PGA") x_values.push("0");
      else if (IM.includes("pSA")) x_values.push(IM.split("_")[1]);
      else x_values.push(IM);
    });

    let colourCounter = 0;
    for (let [curRup, curData] of Object.entries(percentileData50)) {
      if (scenarioSelectedRuptures.includes(curRup)) {
        scatterObjs.push({
          x: x_values,
          y: curData,
          type: "scatter",
          mode: "lines",
          line: { color: deafultColours[colourCounter % 10] },
          name: `Scenario ${curRup} [16, 50, 84 %ile]`,
          legendgroup: `${curRup}`,
          showlegend: true,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.SITE_SPECIFIC} [50th Pecentile Rupture ${curRup}]</b><br><br>` +
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
          x: x_values,
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
          x: x_values,
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
            title: { text: "Period (s)" },
          },
          yaxis: {
            type: "log",
            title: {
              text: `${CONSTANTS.SPECTRAL_ACCELERATION} ${CONSTANTS.G_FORCE_UNIT}`,
            },
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
