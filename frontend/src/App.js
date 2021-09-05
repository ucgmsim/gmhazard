import React from "react";
import { Router, Route, Switch } from "react-router-dom";

// fontawesome
import InitFontAwesome from "utils/InitFontAwesome";

import PrivateRoute from "components/PrivateRoute";

import { GlobalContextProvider } from "context";
import { useAuth0 } from "./components/common/ReactAuth0SPA";

import { Loading } from "components/common";
import { NavBar } from "components/NavBar";
import {
  Home,
  Hazard,
  Project,
  Profile,
  Footer,
  FrameworkDocView,
  PermissionConfig,
  ProjectCreate,
} from "views";

import History from "utils/History";

import "assets/style/App.css";
import "bootstrap/dist/css/bootstrap.min.css";

InitFontAwesome();

const App = () => {
  const { loading } = useAuth0();

  if (loading) {
    return <Loading />;
  }

  return (
    <GlobalContextProvider>
      <Router history={History}>
        <div id="app" className="d-flex flex-column h-100">
          <NavBar />
          <div className="container-fluid main-body">
            <div className="row justify-content-center">
              <Switch>
                <Route path="/" exact component={Home} />

                <PrivateRoute
                  path="/hazard"
                  permission="hazard"
                  exact
                  component={Hazard}
                />

                <PrivateRoute
                  path="/project"
                  permission="project"
                  exact
                  component={Project}
                />

                <PrivateRoute
                  path="/permission-config"
                  permission="psha-admin"
                  exact
                  component={PermissionConfig}
                />

                <Route path="/profile" exact component={Profile} />

                <PrivateRoute
                  path="/create-project"
                  permission="create-project"
                  exact
                  component={ProjectCreate}
                />

                <Route
                  path="/framework-docs"
                  exact
                  component={FrameworkDocView}
                />
              </Switch>
            </div>
          </div>
        </div>
      </Router>
      <Footer />
    </GlobalContextProvider>
  );
};

export default App;
