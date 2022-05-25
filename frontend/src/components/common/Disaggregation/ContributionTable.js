import React, { Fragment } from "react";

import * as CONSTANTS from "constants/Constants";

import { renderSigfigs } from "utils/Utils";
import { ErrorMessage } from "components/common";

const ContributionTable = ({ meanData, contributionData }) => {
  if (
    meanData !== null &&
    !meanData.hasOwnProperty("error") &&
    contributionData !== null &&
    !contributionData.hasOwnProperty("error")
  ) {
    const contributionTableRows = [];

    const meanValueObj = meanData["mean_values"];

    // Polish contributionData to be used in <table>
    let contribRowClassname = "";

    contributionData.forEach((entry, rowIdx) => {
      let firstCol = entry[1] === undefined ? entry[0] : entry[1];
      let secondCol =
        entry[2] === undefined
          ? "-"
          : Number(entry[2] * 100).toLocaleString(undefined, {
              maximumSignificantDigits: 4,
            });
      let thirdCol =
        entry[3] === undefined || isNaN(entry[3])
          ? "-"
          : Number(entry[3]).toExponential(4);
      let fourthCol = entry[4] === undefined ? "-" : entry[4];
      let fifthCol =
        entry[5] === undefined || isNaN(entry[3])
          ? "-"
          : renderSigfigs(entry[5], CONSTANTS.APP_UI_SIGFIGS);

      if (rowIdx === CONSTANTS.APP_UI_CONTRIB_TABLE_ROWS - 1) {
        contribRowClassname = "contrib-toggle-row contrib-row-hidden";
      }

      contributionTableRows.push(
        <tr key={entry[0]} className={contribRowClassname}>
          <td>{firstCol}</td>
          <td>{secondCol}</td>
          <td>{thirdCol}</td>
          <td>{fourthCol}</td>
          <td>{fifthCol}</td>
        </tr>
      );
    });

    return (
      <div className="d-flex flex-column align-items-md-center">
        {/* Mean table */}
        {meanValueObj !== null ? (
          <Fragment>
            <table className="table thead-dark table-striped table-bordered mt-2 w-auto">
              <thead>
                <tr>
                  <th scope="col">{CONSTANTS.INTENSITY_MEASURE}</th>
                  <th scope="col">{CONSTANTS.MEAN_MAGNITUDE}</th>
                  <th scope="col">
                    {CONSTANTS.MEAN_RRUP} {CONSTANTS.KILOMETRE}
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
        ) : null}

        {/* Contribution table */}
        <table className="table thead-dark table-striped table-bordered mt-2 w-auto">
          <thead>
            <tr>
              <th scope="col">{CONSTANTS.NAME}</th>
              <th scope="col">
                {CONSTANTS.CONTRIBUTION} {CONSTANTS.PERCENTAGE}
              </th>
              <th scope="col">{CONSTANTS.ANNUAL_RECURRENCE_RATE}</th>
              <th scope="col">{CONSTANTS.MAGNITUDE}</th>
              <th scope="col">
                {CONSTANTS.RRUP} {CONSTANTS.KILOMETRE}
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

export default ContributionTable;
