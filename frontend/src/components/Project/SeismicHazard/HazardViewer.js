import React, { Fragment, useEffect, useState, useContext } from "react";

import { Tabs, Tab } from "react-bootstrap";

import { GlobalContext } from "context";

import {
  HazardViewerHazardCurve,
  HazardViewerDisaggregation,
  HazardViewerUHS,
} from "components/Project/SeismicHazard";

import "assets/style/HazardForms.css";

const HazardViewer = () => {
  const {
    projectHazardCurveGetClick,
    projectDisaggGetClick,
    projectUHSGetClick,
  } = useContext(GlobalContext);

  const [selectedTab, setSelectedTab] = useState("hazardCurve");

  // When users click Get button, change the current to tab its tab to display plots/images
  useEffect(() => {
    if (projectHazardCurveGetClick !== null) {
      setSelectedTab("hazardCurve");
    }
  }, [projectHazardCurveGetClick]);

  useEffect(() => {
    if (projectDisaggGetClick !== null) {
      setSelectedTab("disagg");
    }
  }, [projectDisaggGetClick]);

  useEffect(() => {
    if (projectUHSGetClick !== null) {
      setSelectedTab("uhs");
    }
  }, [projectUHSGetClick]);

  return (
    <Fragment>
      <Tabs
        activeKey={selectedTab}
        className="hazard-viewer-tabs"
        onSelect={(key) => setSelectedTab(key)}
      >
        <Tab eventKey="hazardCurve" title={CONSTANTS.HAZARD_CURVE}>
          <HazardViewerHazardCurve />
        </Tab>

        <Tab eventKey="disagg" title="Disaggregation">
          <HazardViewerDisaggregation />
        </Tab>

        <Tab eventKey="uhs" title={CONSTANTS.UNIFORM_HAZARD_SPECTRUM}>
          <HazardViewerUHS />
        </Tab>
      </Tabs>
    </Fragment>
  );
};

export default HazardViewer;
