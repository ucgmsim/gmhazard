import React from "react";

import Plot from "react-plotly.js";

import { getPlotData } from "utils/Utils.js";
import { PLOT_MARGIN, PLOT_CONFIG } from "constants/Constants";
import { ErrorMessage } from "components/common";

import "assets/style/UHSPlot.css";

const UHSPlot = ({
  from,
  uhsData,
  nzs1170p5Data,
  showNZS1170p5 = true,
  extra,
}) => {
  if (uhsData !== null && !uhsData.hasOwnProperty("error")) {
    const createLegendLabel = (isNZCode) => {
      const selectedRPs = extra.selectedRPs;

      selectedRPs.sort((a, b) => a - b);
      /*
        Based on a sorted array, add each RP
        Depends on the isNZCode status, newLabel starts with NZ Code - or an empty string
      */
      let newLabel =
        isNZCode === true ? "NZS1170.5 [RP = " : "Site-specific [RP = ";

      /*
        Only display to legend the RP that has values if its for Projects
      */
      if (from === "projects") {
        const dataToCheck = isNZCode === true ? nzs1170p5Data : uhsData;
        for (let i = 0; i < selectedRPs.length; i++) {
          if (
            !Object.values(
              dataToCheck[`${1 / Number(selectedRPs[i]).toString()}`]
            ).includes("nan")
          ) {
            newLabel += `${selectedRPs[i].toString()}, `;
          }
        }
      } else {
        for (let i = 0; i < selectedRPs.length; i++) {
          newLabel += `${selectedRPs[i].toString()}, `;
        }
      }

      // Remove last two character (, ) and add closing bracket
      newLabel = newLabel.slice(0, -2) + "]";

      return newLabel;
    };

    // Create NZS1170p5 Code UHS scatter objs
    const scatterObjs = [];
    let nzCodeDataCounter = 0;

    for (let [curExcd, curData] of Object.entries(nzs1170p5Data)) {
      // The object contains the value of NaN, so we dont plot
      if (Object.values(curData).includes("nan")) {
        continue;
        // Else we plot
      } else {
        let curPlotData = getPlotData(curData);
        // Convert the Annual exdance reate to Return period in a string format
        let displayRP = (1 / Number(curExcd)).toString();
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
            `<b>NZS1170.5 [RP ${displayRP}]</b><br><br>` +
            "%{xaxis.title.text}: %{x}<br>" +
            "%{yaxis.title.text}: %{y}<extra></extra>",
        });
        nzCodeDataCounter += 1;
      }
    }

    // UHS scatter objs
    let dataCounter = 0;
    for (let [curExcd, curData] of Object.entries(uhsData)) {
      let displayRP = (1 / Number(curExcd)).toString();
      scatterObjs.push({
        x: curData.period_values,
        y: curData.sa_values,
        type: "scatter",
        mode: "lines",
        line: { color: "blue" },
        name: createLegendLabel(false),
        legendgroup: "site-specific",
        showlegend: dataCounter === 0 ? true : false,
        hoverinfo: "none",
        hovertemplate:
          `<b>Site-specific [RP ${displayRP}]</b><br><br>` +
          "%{xaxis.title.text}: %{x}<br>" +
          "%{yaxis.title.text}: %{y}<extra></extra>",
      });
      dataCounter += 1;
    }

    return (
      <Plot
        className={"uhs-plot"}
        data={scatterObjs}
        layout={{
          xaxis: {
            title: { text: "Period (s)" },
          },
          yaxis: {
            title: { text: "Spectral acceleration (g)" },
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
