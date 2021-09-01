import React from "react";

import "assets/style/SingleColumnView.css";

const SingleColumnView = ({ pageComponent }) => {
  const ChildComponent = pageComponent;
  return (
    <div className="single-column-inner">
      <div className="row">
        <ChildComponent />
      </div>
    </div>
  );
};

export default SingleColumnView;
