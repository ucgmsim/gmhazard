import React, { Fragment, useContext } from "react";

import { Tabs, Tab } from "react-bootstrap";

import { GlobalContext } from "context";

import { TwoColumnView } from "components/common";
import {
  SiteSelectionForm,
  SiteSelectionViewer,
} from "components/Hazard/SiteSelection";
import { GMSForm, GMSViewer } from "components/Hazard/GMS";
import { HazardForm, HazardViewer } from "components/Hazard/SeismicHazard";
import { ScenarioForm, ScenarioViewer } from "components/Hazard/Scenarios";

const Hazard = () => {
  const {
    hasPermission,
    vs30,
    locationSetClick,
    nzs1170p5DefaultParams,
    scenarioData,
  } = useContext(GlobalContext);

  const invalidTab = () => {
    return locationSetClick === null || vs30 === "";
  };
  const permissionSeismicHazardTab = () => {
    return (
      hasPermission("hazard:hazard") ||
      hasPermission("hazard:disagg") ||
      hasPermission("hazard:uhs")
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
            disabled={invalidTab() || nzs1170p5DefaultParams.length === 0}
            tabClassName="seismic-hazard-tab"
          >
            <TwoColumnView cpanel={HazardForm} viewer={HazardViewer} />
          </Tab>
        ) : null}

        {hasPermission("hazard:gms") ? (
          <Tab
            eventKey="gms"
            title="Ground Motion Selection"
            disabled={invalidTab()}
            tabClassName="gms-tab"
          >
            <TwoColumnView cpanel={GMSForm} viewer={GMSViewer} />
          </Tab>
        ) : null}

        {hasPermission("hazard:scenarios") ? (
          <Tab
            eventKey="scenarios"
            title={CONSTNATS.SCENARIOS}
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

export default Hazard;
