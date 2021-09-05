import React from "react";

import { Button } from "react-bootstrap";

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
      Log in
    </Button>
  );
};

export default LoginButton;
