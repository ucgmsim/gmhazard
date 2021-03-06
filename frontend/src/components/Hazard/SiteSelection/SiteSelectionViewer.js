import React, { Fragment } from "react";

import { Tab, Nav } from "react-bootstrap";

import * as CONSTANTS from "constants/Constants";

import {
  SiteSelectionMap,
  SiteSelectionVS30,
  SiteSelectionRegional,
} from "components/Hazard/SiteSelection";

const SiteSelectionViewer = () => {
  return (
    <Fragment>
      <Tab.Container defaultActiveKey="map">
        <Nav variant="tabs">
          <Nav.Item>
            <Nav.Link eventKey="map">{CONSTANTS.MAP}</Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link eventKey="regional">{CONSTANTS.REGIONAL}</Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link eventKey="vs30">
              V<sub>S30</sub>
            </Nav.Link>
          </Nav.Item>
        </Nav>
        <Tab.Content>
          <Tab.Pane eventKey="map">
            <SiteSelectionMap />
          </Tab.Pane>
          <Tab.Pane eventKey="regional">
            <SiteSelectionRegional />
          </Tab.Pane>
          <Tab.Pane eventKey="vs30">
            <SiteSelectionVS30 />
          </Tab.Pane>
        </Tab.Content>
      </Tab.Container>
    </Fragment>
  );
};
export default SiteSelectionViewer;
