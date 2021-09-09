import React, { Fragment } from "react";

import { Tabs, Tab } from "react-bootstrap";

import {
  EditUserPermission,
  ProjectPermissionDashboard,
  PagePermissionDashboard,
} from "components/PermissionConfig";
import { SingleColumnView } from "components/common";

import "assets/style/AdminPage.css";

const PermissionConfig = () => {
  return (
    <Fragment>
      <Tabs defaultActiveKey="edit-user" className="admin-tabs">
        <Tab eventKey="edit-user" title="Edit Users Permission">
          <SingleColumnView pageComponent={EditUserPermission} />
        </Tab>
        <Tab
          eventKey="project-permission-dashboard"
          title="Project Permission Dashboard"
        >
          <SingleColumnView pageComponent={ProjectPermissionDashboard} />
        </Tab>
        <Tab
          eventKey="page-permission-dashboard"
          title="Page Permission Dashboard"
        >
          <SingleColumnView pageComponent={PagePermissionDashboard} />
        </Tab>
      </Tabs>
    </Fragment>
  );
};

export default PermissionConfig;
