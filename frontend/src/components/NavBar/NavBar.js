import React, { useContext } from "react";

import { Navbar, Nav, NavLink } from "reactstrap";
import { NavLink as RouterNavLink } from "react-router-dom";

import { useAuth0 } from "components/common/ReactAuth0SPA";
import { GlobalContext } from "context";

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
        Home
      </NavLink>
      {hasPermission("hazard") ? (
        <NavLink
          tag={RouterNavLink}
          to="/hazard"
          exact
          activeClassName="router-link-exact-active"
        >
          Hazard Analysis
        </NavLink>
      ) : null}

      <NavLink
        tag={RouterNavLink}
        to="/project"
        exact
        activeClassName="router-link-exact-active"
      >
        Projects
      </NavLink>

      <NavLink
        tag={RouterNavLink}
        to="/framework-docs"
        exact
        activeClassName="router-link-exact-active"
      >
        Framework Documents
      </NavLink>
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
