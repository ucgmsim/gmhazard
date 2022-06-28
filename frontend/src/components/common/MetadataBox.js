import React from "react";

import * as CONSTANTS from "constants/Constants";

import "assets/style/MetadataBox.css";

const MetadataBox = ({ metadata }) => {
  const createMetadataText = () => {
    let metadataText = [];

    for (const [key, value] of Object.entries(metadata)) {
      if (
        key.includes("NZS") &&
        key.includes("1170.5") &&
        key.includes("Soil")
      ) {
        metadataText.push(
          <p key={key}>
            {key}: {CONSTANTS.NZS_SOIL_CLASS[value]}
          </p>
        );
      } else if (key.includes("NZTA") && key.includes("Soil")) {
        metadataText.push(
          <p key={key}>
            {key}: {CONSTANTS.NZTA_SOIL_CLASS[value]}
          </p>
        );
      } else if (key.includes("Vs30")) {
        metadataText.push(
          <p key={key}>
            V<sub>s30</sub>: {value}
          </p>
        );
      } else if (key.includes("z1p0")) {
        metadataText.push(
          <p key={key}>
            Z<sub>1.0</sub>: {value}
          </p>
        );
      } else if (key.includes("z2p5")) {
        metadataText.push(
          <p key={key}>
            Z<sub>2.5</sub>: {value}
          </p>
        );
      } else {
        metadataText.push(
          <p key={key}>
            {key}: {value}
          </p>
        );
      }
    }

    return metadataText;
  };
  return <div className="custom-metadata-box">{createMetadataText()}</div>;
};

export default MetadataBox;
