import React, { memo } from "react";

import * as CONSTANTS from "constants/Constants";

import { renderSigfigs } from "utils/Utils";
import { ErrorMessage } from "components/common";

const ScenarioRuptureMetaTable = ({ metadata }) => {
  if (metadata !== null && !metadata.hasOwnProperty("error")) {
    const metadataTableRows = [];

    Object.keys(metadata["rupture_name"]).forEach((rupture, rowIdx) => {
      metadataTableRows.push(
        <tr key={rowIdx}>
          <td>{metadata["rupture_name"][rupture]}</td>
          <td>{renderSigfigs(metadata["annual_rec_prob"][rupture], 3)}</td>
          <td>{metadata["magnitude"][rupture]}</td>
          <td>
            {renderSigfigs(metadata["rrup"][rupture], CONSTANTS.APP_UI_SIGFIGS)}
          </td>
        </tr>
      );
    });

    return (
      <div className="d-flex flex-column align-items-md-center">
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
