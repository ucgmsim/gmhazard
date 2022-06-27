import React from "react";

import Plot from "react-plotly.js";

import { ErrorMessage } from "components/common";
import * as CONSTANTS from "constants/Constants";
import { getPlotData, createAxisLabel, convertRPtoAER } from "utils/Utils";

import "assets/style/UHSPlot.css";

const UHSPlot = ({ uhsData, nzs1170p5Data, extra, showNZS1170p5 = true }) => {
  if (uhsData && !uhsData.hasOwnProperty("error")) {
    const createLegendLabel = (isNZCode) => {
      const selectedRPs = extra.selectedRPs;

      selectedRPs.sort((a, b) => a - b);
      /*
        Based on a sorted array, add each Annual Exceedance Rate
        Depends on the isNZCode status, newLabel starts with NZ Code - or an empty string
      */
      let newLabel =
        isNZCode === true
          ? `${CONSTANTS.NZS1170P5} [Rate = `
          : `${CONSTANTS.SITE_SPECIFIC} [Rate = `;

      /*
        Only display to legend the Annual Exceedance Rate
        that has values if it's for Projects
      */
      if (extra.from === "project") {
        const dataToCheck = isNZCode === true ? nzs1170p5Data : uhsData;
        for (let i = 0; i < selectedRPs.length; i++) {
          if (
            !Object.values(
              dataToCheck[`${1 / Number(selectedRPs[i])}`]
            ).includes("nan")
          ) {
            /* 
            With projects, UHS is based on RP, not Annual Exceedance Rate.
            Hence, we convert the selected RPs to Annual Exceedance Rate
            */
            newLabel += `${convertRPtoAER(selectedRPs[i])}, `;
          }
        }
      } else {
        for (let i = 0; i < selectedRPs.length; i++) {
          newLabel += `${convertRPtoAER(selectedRPs[i])}, `;
        }
      }

      // Remove last two character (, ) and add closing bracket
      newLabel = newLabel.slice(0, -2) + "]";

      return newLabel;
    };

    // UHS scatter objs
    const scatterObjs = [];
    let dataCounter = 0;
    for (let [curExcd, curData] of Object.entries(uhsData)) {
      if (!curData.sa_values.includes("nan")) {
        // The first value is from PGA, hence do not inlcude
        scatterObjs.push({
          x: curData.period_values.slice(1),
          y: curData.sa_values.slice(1),
          type: "scatter",
          mode: "lines",
          line: { color: "red" },
          name: createLegendLabel(false),
          legendgroup: "site-specific",
          showlegend: dataCounter === 0 ? true : false,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.SITE_SPECIFIC} [Rate = ${Number(
              Number(curExcd).toFixed(4)
            )}]</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        });
        dataCounter += 1;
      }
    }

    // Create NZS1170p5 Code UHS scatter objs
    let nzCodeDataCounter = 0;
    for (let [curExcd, curData] of Object.entries(nzs1170p5Data)) {
      // Plots only if it does not include nan
      if (!Object.values(curData).includes("nan")) {
        let curPlotData = getPlotData(curData);
        scatterObjs.push({
          x: curPlotData.index,
          y: curPlotData.values,
          type: "scatter",
          mode: "lines",
          line: { color: "black" },
          name: createLegendLabel(true),
          visible: showNZS1170p5,
          legendgroup: "NZS1170.5",
          showlegend: nzCodeDataCounter === 0 ? true : false,
          hoverinfo: "none",
          hovertemplate:
            `<b>${CONSTANTS.NZS1170P5} [Rate = ${Number(
              Number(curExcd).toFixed(4)
            )}]</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        });
        nzCodeDataCounter += 1;
      }
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
            showline: true,
            linewidth: 3,
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
            linewidth: 3,
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

export default UHSPlot;
