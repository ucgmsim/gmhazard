import React, { Fragment, useContext, useEffect } from "react";

import { Tabs, Tab } from "react-bootstrap";
import { GlobalContext } from "context";

import { TwoColumnView } from "components/common";

import {
  SiteSelectionForm,
  SiteSelectionViewer,
} from "components/Project/SiteSelection";
import { GMSForm, GMSViewer } from "components/Project/GMS";
import { HazardForm, HazardViewer } from "components/Project/SeismicHazard";
import { ScenarioForm, ScenarioViewer } from "components/Project/Scenarios";

const Project = () => {
  const {
    projectId,
    projectLocation,
    projectVS30,
    setProjectSiteSelectionGetClick,
    setProjectHazardCurveGetClick,
    setProjectDisaggGetClick,
    setProjectUHSGetClick,
    setProjectGMSGetClick,
    setProjectScenarioGetClick,
  } = useContext(GlobalContext);

  // Reset some global variables when this component gets unmounted
  useEffect(() => {
    return () => {
      setProjectSiteSelectionGetClick(null);
      setProjectHazardCurveGetClick(null);
      setProjectDisaggGetClick(null);
      setProjectUHSGetClick(null);
      setProjectGMSGetClick(null);
      setProjectScenarioGetClick(null);
    };
  }, []);

  const invalidTab = () => {
    return (
      projectId === null || projectLocation === null || projectVS30 === null
    );
  };

  return (
    <Fragment>
      <Tabs defaultActiveKey="siteselection" className="hazard-tabs">
        <Tab eventKey="siteselection" title="Site Selection">
          <TwoColumnView
            cpanel={SiteSelectionForm}
            viewer={SiteSelectionViewer}
          />
        </Tab>

        <Tab
          eventKey="hazard"
          title="Seismic Hazard"
          disabled={invalidTab()}
          tabClassName="seismic-hazard-tab"
        >
          <TwoColumnView cpanel={HazardForm} viewer={HazardViewer} />
        </Tab>

        <Tab
          eventKey="gms"
          title="Ground Motion Selection"
          disabled={invalidTab()}
          tabClassName="gms-tab"
        >
          <TwoColumnView cpanel={GMSForm} viewer={GMSViewer} />
        </Tab>

        <Tab
          eventKey="scenario"
          title="Scenarios"
          disabled={invalidTab()}
          tabClassName="scenarios-tab"
        >
          <TwoColumnView cpanel={ScenarioForm} viewer={ScenarioViewer} />
        </Tab>
      </Tabs>
    </Fragment>
  );
};

export default Project;
