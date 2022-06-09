import React, { useContext } from "react";

import { Navbar, Nav, NavLink } from "reactstrap";
import { NavLink as RouterNavLink } from "react-router-dom";

import { GlobalContext } from "context";
import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

import { LogoutButton, LoginButton } from "components/NavBar";

import "assets/style/NavBar.css";

const MainNav = () => {
  const { hasPermission } = useContext(GlobalContext);

  return (
    <Nav className="mr-auto" navbar>
      <NavLink
        tag={RouterNavLink}
        to="/"
        exact
        activeClassName="router-link-exact-active"
      >
        {CONSTANTS.HOME}
      </NavLink>
      {hasPermission("hazard") ? (
        <NavLink
          tag={RouterNavLink}
          to="/hazard"
          exact
          activeClassName="router-link-exact-active"
        >
          {CONSTANTS.HAZARD_ANALYSIS}
        </NavLink>
      ) : null}

      <NavLink
        tag={RouterNavLink}
        to="/project"
        exact
        activeClassName="router-link-exact-active"
      >
        {CONSTANTS.PROJECTS}
      </NavLink>

      {hasPermission("admin") ? (
        <NavLink
          tag={RouterNavLink}
          to="/framework-docs"
          exact
          activeClassName="router-link-exact-active"
        >
          {CONSTANTS.FRAMEWORK_DOCUMENTS}
        </NavLink>
      ) : null}
    </Nav>
  );
};

const AuthNav = () => {
  const { isAuthenticated } = useAuth0();
  return (
    <Nav className="justify-content-end">
      {isAuthenticated ? <LogoutButton /> : <LoginButton />}
    </Nav>
  );
};

const NavBar = () => {
  return (
    <Navbar color="light" light expand="md" bg="dark">
      <div className="container-fluid max-width">
        <MainNav />

        <AuthNav />
      </div>
    </Navbar>
  );
};

export default NavBar;
