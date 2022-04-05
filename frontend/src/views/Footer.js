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
      <div className="copyright-disclaimer">
        <a href="https://www.canterbury.ac.nz/theuni/copyright/" target="_blank"
                    rel="noopener noreferrer">Disclaimer</a>
      </div>
    </Fragment>
  );
};

export default Footer;
