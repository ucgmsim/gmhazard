import React, { Fragment, useContext } from "react";

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
  const { hasPermission, projectId, projectLocation, projectVS30 } =
    useContext(GlobalContext);

  const invalidTab = () => {
    return (
      projectId === null || projectLocation === null || projectVS30 === null
    );
  };

  const permissionSeismicHazardTab = () => {
    return (
      hasPermission("project:hazard") ||
      hasPermission("project:disagg") ||
      hasPermission("project:uhs")
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

        {permissionSeismicHazardTab() ? (
          <Tab
            eventKey="hazard"
            title="Seismic Hazard"
            disabled={invalidTab()}
            tabClassName="seismic-hazard-tab"
          >
            <TwoColumnView cpanel={HazardForm} viewer={HazardViewer} />
          </Tab>
        ) : null}

        {hasPermission("project:gms") ? (
          <Tab
            eventKey="gms"
            title="Ground Motion Selection"
            disabled={invalidTab()}
            tabClassName="gms-tab"
          >
            <TwoColumnView cpanel={GMSForm} viewer={GMSViewer} />
          </Tab>
        ) : null}

        {hasPermission("project:scenarios") ? (
          <Tab
            eventKey="scenario"
            title="Scenarios"
            disabled={invalidTab()}
            tabClassName="scenarios-tab"
          >
            <TwoColumnView cpanel={ScenarioForm} viewer={ScenarioViewer} />
          </Tab>
        ) : null}
      </Tabs>
    </Fragment>
  );
};

export default Project;
