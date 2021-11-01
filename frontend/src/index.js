import React from "react";
import ReactDOM from "react-dom";

import { stopReportingRuntimeErrors } from "react-error-overlay";

import { Auth0Provider } from "./components/common/ReactAuth0SPA";

import App from "./App";
import History from "utils/History";

import "assets/style/index.css";

// Discuss first whether we want to disable the error overlays for EA
if (process.env.REACT_APP_ENV === "EA") {
  stopReportingRuntimeErrors(); // disables error overlays
}

const onRedirectCallback = (appState) => {
  History.push(
    appState && appState.targetUrl
      ? appState.targetUrl
      : window.location.pathname
  );
};

// AUTH0 details from the .env file
ReactDOM.render(
  <Auth0Provider
    domain={process.env.REACT_APP_AUTH0_DOMAIN}
    client_id={process.env.REACT_APP_AUTH0_CLIENTID}
    redirect_uri={window.location.origin + "/gmhazard"}
    audience={process.env.REACT_APP_AUTH0_AUDIENCE}
    onRedirectCallback={onRedirectCallback}
  >
    <App />
  </Auth0Provider>,
  document.getElementById("root")
);
