import React, { Fragment } from "react";

import * as CONSTANTS from "constants/Constants";

import { renderSigfigs } from "utils/Utils";
import { ErrorMessage } from "components/common";

const MetadataTable = ({ metadata, scenarioRuptures }) => {
  if (
    metadata !== null &&
    !metadata.hasOwnProperty("error") &&
    scenarioRuptures !== null &&
    !scenarioRuptures.hasOwnProperty("error")
  ) {
    const contributionTableRows = [];
    console.log(metadata)

    // Polish contributionData to be used in <table>
    let contribRowClassname = "";
    

    scenarioRuptures.forEach((rupture, rowIdx) => {
      const ruptureName = Object.keys(metadata["rupture_name"]).find(
        (ruptureName) =>
          metadata["rupture_name"][ruptureName] === rupture
      );
  
      // // let secondCol =
      // //   entry[2] === undefined
      // //     ? "-"
      // //     : Number(entry[2] * 100).toLocaleString(undefined, {
      // //         maximumSignificantDigits: 4,
      // //       });
      
      // let fourthCol = entry[4] === undefined ? "-" : entry[4];
      // let fifthCol =
      //   entry[5] === undefined || isNaN(entry[3])
      //     ? "-"
      //     : renderSigfigs(entry[5], CONSTANTS.APP_UI_SIGFIGS);

      // if (rowIdx === CONSTANTS.APP_UI_CONTRIB_TABLE_ROWS - 1) {
      //   contribRowClassname = "contrib-toggle-row contrib-row-hidden";
      // }

      contributionTableRows.push(
        <tr key={rowIdx} className={contribRowClassname}>
          <td>{metadata["rupture_name"][ruptureName]}</td>
          {/* <td>{secondCol}</td> */}
          <td>{Number(metadata["annual_rec_prob"][ruptureName]).toExponential(4)}</td>
          <td>{metadata["magnitude"][ruptureName]}</td>
          <td>{renderSigfigs(metadata["rrup"][ruptureName], CONSTANTS.APP_UI_SIGFIGS)}</td>
        </tr>
      );
    });

    return (
      <div className="d-flex flex-column align-items-md-center">
        {/* Mean table */}
        {/* {meanValueObj !== null ? (
          <Fragment>
            <table className="table thead-dark table-striped table-bordered mt-2 w-auto">
              <thead>
                <tr>
                  <th scope="col">{CONSTANTS.INTENSITY_MEASURE}</th>
                  <th scope="col">{CONSTANTS.MEAN_MAGNITUDE}</th>
                  <th scope="col">
                    {CONSTANTS.MEAN_RRUP} {CONSTANTS.KILOMETRE_UNIT}
                  </th>
                  <th scope="col">{CONSTANTS.MEAN_EPSILON}</th>
                </tr>
              </thead>
              <tbody>
                <tr key="first-table">
                  <td>{meanData["im"]}</td>
                  <td>
                    {renderSigfigs(
                      meanValueObj["magnitude"],
                      CONSTANTS.APP_UI_SIGFIGS
                    )}
                  </td>
                  <td>
                    {renderSigfigs(
                      meanValueObj["rrup"],
                      CONSTANTS.APP_UI_SIGFIGS
                    )}
                  </td>
                  <td>
                    {renderSigfigs(
                      meanValueObj["epsilon"],
                      CONSTANTS.APP_UI_SIGFIGS
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
            <br />
          </Fragment>
        ) : null} */}

        {/* Contribution table */}
        <table className="table thead-dark table-striped table-bordered mt-2 w-auto">
          <thead>
            <tr>
              <th scope="col">{CONSTANTS.NAME}</th>
              {/* <th scope="col">
                {CONSTANTS.CONTRIBUTION} {CONSTANTS.PERCENTAGE_UNIT}
              </th> */}
              <th scope="col">{CONSTANTS.ANNUAL_RECURRENCE_RATE}</th>
              <th scope="col">{CONSTANTS.MAGNITUDE}</th>
              <th scope="col">
                {CONSTANTS.RRUP} {CONSTANTS.KILOMETRE_UNIT}
              </th>
            </tr>
          </thead>
          <tbody>{contributionTableRows}</tbody>
        </table>
      </div>
    );
  }
  return <ErrorMessage />;
};

export default MetadataTable;
