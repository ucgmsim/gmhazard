import React, { Fragment, useContext, useState, useEffect } from "react";

import { Tabs, Tab } from "react-bootstrap";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";

import {
  HazardViewerHazardCurve,
  HazardViewerDisaggregation,
  HazardViewerUHS,
} from "components/Hazard/SeismicHazard";

import "assets/style/HazardForms.css";

const HazardViewer = () => {
  const {
    hasPermission,
    selectedIM,
    hazardCurveComputeClick,
    disaggComputeClick,
    uhsComputeClick,
  } = useContext(GlobalContext);

  const [selectedTab, setSelectedTab] = useState("hazardCurve");

  // Hazard Form, IM selected and "Compute" clicked
  useEffect(() => {
    if (hazardCurveComputeClick !== null && selectedIM !== null) {
      setSelectedTab("hazardCurve");
    }
  }, [hazardCurveComputeClick]);

  useEffect(() => {
    if (disaggComputeClick !== null && selectedIM !== null) {
      setSelectedTab("disagg");
    }
  }, [disaggComputeClick]);

  useEffect(() => {
    if (uhsComputeClick !== null) {
      setSelectedTab("uhs");
    }
  }, [uhsComputeClick]);

  return (
    <Fragment>
      <Tabs
        activeKey={selectedTab}
        className="hazard-viewer-tabs"
        onSelect={(k) => setSelectedTab(k)}
      >
        {hasPermission("hazard:hazard") ? (
          <Tab eventKey="hazardCurve" title={CONSTANTS.HAZARD_CURVE}>
            <HazardViewerHazardCurve />
          </Tab>
        ) : null}

        {hasPermission("hazard:disagg") ? (
          <Tab eventKey="disagg" title={CONSTANTS.DISAGGREGATION}>
            <HazardViewerDisaggregation />
          </Tab>
        ) : null}
        {hasPermission("hazard:uhs") ? (
          <Tab eventKey="uhs" title={CONSTANTS.UNIFORM_HAZARD_SPECTRUM}>
            <HazardViewerUHS />
          </Tab>
        ) : null}
      </Tabs>
    </Fragment>
  );
};

export default HazardViewer;
