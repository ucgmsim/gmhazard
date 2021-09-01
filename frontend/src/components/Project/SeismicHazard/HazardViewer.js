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
    hasPermission,
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
        {hasPermission("project:hazard") ? (
          <Tab eventKey="hazardCurve" title="Hazard Curve">
            <HazardViewerHazardCurve />
          </Tab>
        ) : null}

        {hasPermission("project:disagg") ? (
          <Tab eventKey="disagg" title="Disaggregation">
            <HazardViewerDisaggregation />
          </Tab>
        ) : null}
        {hasPermission("project:uhs") ? (
          <Tab eventKey="uhs" title="Uniform Hazard Spectrum">
            <HazardViewerUHS />
          </Tab>
        ) : null}
      </Tabs>
    </Fragment>
  );
};

export default HazardViewer;
