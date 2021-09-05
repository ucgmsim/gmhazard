import React, { useEffect, useContext } from "react";
import { Route, withRouter } from "react-router-dom";

import PropTypes from "prop-types";

import { useAuth0 } from "components/common/ReactAuth0SPA";
import { GlobalContext } from "context";

const PrivateRoute = ({
  component: Component,
  path,
  permission,
  location,
  ...rest
}) => {
  const { hasPermission } = useContext(GlobalContext);
  const { isAuthenticated, loginWithRedirect } = useAuth0();

  useEffect(() => {
    const fn = async () => {
      if (!isAuthenticated) {
        await loginWithRedirect({
          appState: { targetUrl: location.pathname },
        });
      }
    };
    fn();
  }, [isAuthenticated, loginWithRedirect, path, location]);

  // Replace error part to a proper component, e.g., 403 forbidden template
  const render = (props) =>
    /* 
      if user is authenticated (logged in) and has permission to access, they can access to the page
      if user is authenticated (logged in) but has no permission to access, they will see the error message
    */
    isAuthenticated === true && hasPermission(permission) === true ? (
      <Component {...props} />
    ) : isAuthenticated === true && hasPermission(permission) === false ? (
      <div>
        <strong>You do not have permission to view this page.</strong>
      </div>
    ) : null;

  return <Route path={path} render={render} {...rest} />;
};

PrivateRoute.propTypes = {
  component: PropTypes.oneOfType([PropTypes.element, PropTypes.func])
    .isRequired,
  location: PropTypes.shape({
    pathname: PropTypes.string.isRequired,
  }).isRequired,
  path: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.arrayOf(PropTypes.string),
  ]).isRequired,
};

export default withRouter(PrivateRoute);
