import React, { useState, useContext, useEffect, Fragment } from "react";

import { v4 as uuidv4 } from "uuid";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import TextField from "@material-ui/core/TextField";

import * as CONSTANTS from "constants/Constants";
import { GlobalContext } from "context";
import { GuideTooltip } from "components/common";

import {
  renderSigfigs,
  disableScrollOnNumInput,
  isPSANotInIMList,
} from "utils/Utils";

const UHSSection = () => {
  disableScrollOnNumInput();

  const {
    locationSetClick,
    uhsRateTable,
    setUHSComputeClick,
    hasPermission,
    uhsTableAddRow,
    uhsTableDeleteRow,
    showUHSNZS1170p5,
    setShowUHSNZS1170p5,
    IMs,
  } = useContext(GlobalContext);

  const [disableButtonUHSCompute, setDisableButtonUHSCompute] = useState(true);

  const [uhsAnnualProb, setUHSAnnualProb] = useState("");

  // If there are no UHS inputs or no permission, cannot compute UHS
  useEffect(() => {
    setDisableButtonUHSCompute(
      uhsRateTable.length === 0 || hasPermission("hazard:uhs") !== true
    );
  }, [uhsRateTable]);

  // A user clicked the Set button in site selection, reset values
  useEffect(() => {
    if (locationSetClick !== null) {
      setUHSAnnualProb("");
    }
  }, [locationSetClick]);

  // rate calcs
  const onClickUHSTableAdd = () => {
    if (uhsRateTable.some((item) => item === uhsAnnualProb)) {
      return;
    }
    uhsTableAddRow(uhsAnnualProb);
    setUHSAnnualProb("");
  };

  const invalidExdRate = () => {
    return !(uhsAnnualProb > 0 && uhsAnnualProb < 1);
  };

  let localUHSRateTable = uhsRateTable.map((rate, idx) => {
    const returnPeriod = renderSigfigs(
      1 / parseFloat(rate),
      CONSTANTS.APP_UI_SIGFIGS
    );

    return (
      <tr id={"uhs-row-" + idx} key={idx}>
        <td>
          {renderSigfigs(rate, CONSTANTS.APP_UI_UHS_RATETABLE_RATE_SIGFIGS)}
        </td>
        <td>{returnPeriod}</td>
        <td>
          <div
            className="uhs-delete-row"
            title="Delete Row"
            onClick={() => onClickDeleteRow(idx)}
          >
            <FontAwesomeIcon icon="trash" />
          </div>
        </td>
      </tr>
    );
  });

  const onClickDeleteRow = (id) => {
    if (id === 0 && uhsRateTable[0] === CONSTANTS.UHS_TABLE_MESSAGE) {
      return;
    }
    uhsTableDeleteRow(id);
  };

  return (
    <Fragment>
      <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group form-section-title">
          Uniform Hazard Spectrum
          <GuideTooltip
            explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_UHS"]}
          />
        </div>
        <div className="form-group">
          <label
            id="label-annual-rate"
            htmlFor="uhs-annual-rate"
            className="control-label"
          >
            Annual Exceedance Rate
          </label>
          <TextField
            id="uhs-annual-rate"
            type="number"
            value={uhsAnnualProb}
            onChange={(e) => setUHSAnnualProb(e.target.value)}
            placeholder="(0, 1)"
            fullWidth
            variant="outlined"
            error={
              (uhsAnnualProb > 0 && uhsAnnualProb < 1) || uhsAnnualProb === ""
                ? false
                : true
            }
            helperText={
              (uhsAnnualProb > 0 && uhsAnnualProb < 1) || uhsAnnualProb === ""
                ? " "
                : "Annual Exceedance Rate must be between 0 and 1. (0 < X < 1)"
            }
            disabled={isPSANotInIMList(IMs)}
          />
        </div>
        <div className="form-group">
          <button
            type="button"
            className="btn btn-primary uhs-add-btn"
            onClick={() => onClickUHSTableAdd()}
            disabled={invalidExdRate()}
          >
            Add
          </button>
        </div>
      </form>

      <div className="form-group">Add one or more rates for calculation</div>

      <div className="form-group">
        <table id="uhs-added">
          <thead>
            <tr>
              <th>Rate</th>
              <th>Return Period</th>
              <th className="uhs-delete-row" title="Click to Delete the Row">
                Delete
              </th>
            </tr>
          </thead>
          <tbody>{localUHSRateTable}</tbody>
        </table>
      </div>

      <div className="form-group">
        <button
          id="uhs-update-plot"
          type="button"
          className="btn btn-primary mt-2"
          disabled={disableButtonUHSCompute || isPSANotInIMList(IMs)}
          onClick={() => setUHSComputeClick(uuidv4())}
        >
          Compute
        </button>
      </div>

      <div className="form-group">
        <input
          type="checkbox"
          checked={showUHSNZS1170p5}
          onChange={() => setShowUHSNZS1170p5(!showUHSNZS1170p5)}
        />
        <span className="show-nzs1170p5">&nbsp;Show NZS1170.5</span>
      </div>
    </Fragment>
  );
};

export default UHSSection;
