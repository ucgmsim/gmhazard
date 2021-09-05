import React, { Fragment, useContext } from "react";

import { GlobalContext } from "context";

import {
  HazardCurveSection,
  DisaggregationSection,
  UHSSection,
} from "components/Project/SeismicHazard";

import "assets/style/HazardForms.css";

const HazardForm = () => {
  const { hasPermission } = useContext(GlobalContext);

  return (
    <Fragment>
      {hasPermission("project:hazard") ? <HazardCurveSection /> : null}
      {hasPermission("project:disagg") ? (
        <Fragment>
          <div className="hr"></div>
          <DisaggregationSection />
        </Fragment>
      ) : null}
      {hasPermission("project:uhs") ? (
        <Fragment>
          <div className="hr"></div>
          <UHSSection />
        </Fragment>
      ) : null}
    </Fragment>
  );
};

export default HazardForm;
