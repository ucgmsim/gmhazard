import React, { Fragment } from "react";

import {
  HazardCurveSection,
  DisaggregationSection,
  UHSSection,
} from "components/Project/SeismicHazard";

import "assets/style/HazardForms.css";

const HazardForm = () => {
  return (
    <Fragment>
      <HazardCurveSection />
      <Fragment>
        <div className="hr"></div>
        <DisaggregationSection />
      </Fragment>
      <Fragment>
        <div className="hr"></div>
        <UHSSection />
      </Fragment>
    </Fragment>
  );
};

export default HazardForm;
