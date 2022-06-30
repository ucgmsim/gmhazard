import React from "react";

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

    scenarioRuptures.forEach((rupture, rowIdx) => {
      const ruptureName = Object.keys(metadata["rupture_name"]).find(
        (ruptureName) => metadata["rupture_name"][ruptureName] === rupture
      );

      contributionTableRows.push(
        <tr key={rowIdx}>
          <td>{metadata["rupture_name"][ruptureName]}</td>
          <td>
            {Number(metadata["annual_rec_prob"][ruptureName]).toExponential(4)}
          </td>
          <td>{metadata["magnitude"][ruptureName]}</td>
          <td>
            {renderSigfigs(
              metadata["rrup"][ruptureName],
              CONSTANTS.APP_UI_SIGFIGS
            )}
          </td>
        </tr>
      );
    });

    return (
      <div className="d-flex flex-column align-items-md-center">
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
