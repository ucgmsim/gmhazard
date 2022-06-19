import React from "react";

import { Button } from "react-bootstrap";

import * as CONSTANTS from "constants/Constants";
import { useAuth0 } from "components/common/ReactAuth0SPA";

const LoginButton = () => {
  const { loginWithRedirect } = useAuth0();
  return (
    <Button
      id="qs-login-btn"
      color="primary"
      className="btn-margin"
      onClick={() => loginWithRedirect({})}
    >
      {CONSTANTS.LOGIN}
    </Button>
  );
};

export default LoginButton;
