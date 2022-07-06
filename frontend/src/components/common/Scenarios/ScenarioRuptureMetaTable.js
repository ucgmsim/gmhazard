import React, { memo } from "react";

import * as CONSTANTS from "constants/Constants";

import { renderSigfigs } from "utils/Utils";
import { ErrorMessage } from "components/common";

const ScenarioRuptureMetaTable = ({ metadata }) => {
  if (metadata !== null && !metadata.hasOwnProperty("error")) {
    const metadataTableRows = [];
    let contribRowClassname = "";

    Object.keys(metadata["rupture_name"]).forEach((rupture, rowIdx) => {
      if (rowIdx === CONSTANTS.APP_UI_CONTRIB_TABLE_ROWS - 1) {
        contribRowClassname =
          "scenario-contrib-toggle-row scenario-contrib-row-hidden";
      }

      metadataTableRows.push(
        <tr key={rowIdx} className={contribRowClassname}>
          <td>{metadata["rupture_name"][rupture]}</td>
          <td>
            {Number(metadata["annual_rec_prob"][rupture]).toExponential(3)}
          </td>
          <td>{metadata["magnitude"][rupture]}</td>
          <td>
            {renderSigfigs(metadata["rrup"][rupture], CONSTANTS.APP_UI_SIGFIGS)}
          </td>
        </tr>
      );
    });

    return (
      <div className="d-flex flex-column align-items-md-center">
        {/* metadata table */}
        <table className="table thead-dark table-striped table-bordered mt-2 w-auto">
          <thead>
            <tr>
              <th scope="col">{CONSTANTS.NAME}</th>
              <th scope="col">{CONSTANTS.ANNUAL_RECURRENCE_RATE}</th>
              <th scope="col">{CONSTANTS.MAGNITUDE}</th>
              <th scope="col">
                {CONSTANTS.RRUP} {CONSTANTS.KILOMETRE_UNIT}
              </th>
            </tr>
          </thead>
          <tbody>{metadataTableRows}</tbody>
        </table>
      </div>
    );
  }
  return <ErrorMessage />;
};

export default memo(ScenarioRuptureMetaTable);
