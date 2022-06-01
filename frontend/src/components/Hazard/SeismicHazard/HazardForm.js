import React, { Fragment, useState, useEffect, useContext } from "react";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import {
  HazardCurveSection,
  DisaggregationSection,
  UHSSection,
  NZS1170p5Section,
  NZTASection,
} from "components/Hazard/SeismicHazard";

import { GuideTooltip } from "components/common";

import "assets/style/HazardForms.css";

const HazardForm = () => {
  const { selectedIM, hasPermission } = useContext(GlobalContext);

  const [NZCodeRadio, setNZCodeRadio] = useState("nzs1170p5");

  useEffect(() => {
    if (selectedIM !== "PGA") {
      setNZCodeRadio("nzs1170p5");
    }
  }, [selectedIM]);

  return (
    <Fragment>
      {hasPermission("hazard:hazard") ? <HazardCurveSection /> : null}
      {hasPermission("hazard:disagg") ? (
        <Fragment>
          <div className="hr"></div>
          <DisaggregationSection />
        </Fragment>
      ) : null}
      {hasPermission("hazard:uhs") ? (
        <Fragment>
          <div className="hr"></div>
          <UHSSection />
        </Fragment>
      ) : null}

      <div className="hr"></div>
      <div className="form-group">
        <div className="form-group form-section-title">
          {CONSTANTS.NZ_CODE}
          <GuideTooltip
            explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_NZ_CODE"]}
            hyperlink={CONSTANTS.TOOLTIP_URL["HAZARD_NZ_CODE"]}
          />
        </div>
        <div>
          <div className="form-check form-check-inline nz-code-radio">
            <input
              className="form-check-input"
              type="radio"
              name="inline-radio-options"
              id="nzs1170p5-radio"
              value="nzs1170p5"
              checked={NZCodeRadio === "nzs1170p5"}
              onChange={(e) => setNZCodeRadio(e.target.value)}
            />
            <label className="form-check-label" htmlFor="nzs1170p5">
              {CONSTANTS.NZS1170P5}
              <GuideTooltip
                explanation={
                  CONSTANTS.TOOLTIP_MESSAGES["HAZARD_NZS1170P5_CODE"]
                }
              />
            </label>
          </div>
          <div className="form-check form-check-inline">
            <input
              className="form-check-input"
              type="radio"
              name="inline-radio-options"
              id="nzta-radio"
              value="nzta"
              disabled={selectedIM !== "PGA"}
              checked={NZCodeRadio === "nzta"}
              onChange={(e) => setNZCodeRadio(e.target.value)}
            />
            <label className="form-check-label" htmlFor="nzta">
              {CONSTANTS.NZTA}
              <GuideTooltip
                explanation={CONSTANTS.TOOLTIP_MESSAGES["HAZARD_NZTA_CODE"]}
              />
            </label>
          </div>
        </div>
        {NZCodeRadio === "nzs1170p5" ? <NZS1170p5Section /> : <NZTASection />}
      </div>
    </Fragment>
  );
};

export default HazardForm;
