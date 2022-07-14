import React, { memo } from "react";

import "assets/style/ImageMap.css";

const ImageMap = ({ header, src, alt }) => {
  return (
    <div className="container">
      <h5 className="image-map-header">{header}</h5>
      <img
        className="image-map rounded mx-auto d-block img-fluid"
        src={`data:image/png;base64,${src}`}
        alt={alt}
      />
    </div>
  );
};

export default memo(ImageMap);
