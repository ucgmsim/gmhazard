import React, { Fragment } from "react";

import "assets/style/Footer.css";

const Footer = () => {
  return (
    <Fragment>
      <div className="sw-version">
        SW version: {process.env.REACT_APP_GIT_SHA}
      </div>
      <div className="build-date">
        Build Date: {process.env.REACT_APP_BUILD_DATE}
      </div>
    </Fragment>
  );
};

export default Footer;
