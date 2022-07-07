import React from "react";

import * as CONSTANTS from "constants/Constants";

import "assets/style/MetadataBox.css";

const MetadataBox = ({ metadata }) => {
  const createMetadataText = () => {
    let metadataText = [];

    for (const [key, value] of Object.entries(metadata)) {
      switch (key) {
        default:
          metadataText.push(
            <p key={key}>
              {key}: {value}
            </p>
          );
          break;
        case "NZS 1170.5 Soil Class":
          metadataText.push(
            <p key={key}>
              {key}: {CONSTANTS.NZS_SOIL_CLASS[value]}
            </p>
          );
          break;
        case "NZTA Soil Class":
          metadataText.push(
            <p key={key}>
              {key}: {CONSTANTS.NZTA_SOIL_CLASS[value]}
            </p>
          );
          break;
        case "Vs30":
          metadataText.push(
            <p key={key}>
              V<sub>s30</sub>: {value}
            </p>
          );
          break;
        case "z1p0":
          metadataText.push(
            <p key={key}>
              Z<sub>1.0</sub>: {value}
            </p>
          );
          break;
        case "z2p5":
          metadataText.push(
            <p key={key}>
              Z<sub>2.5</sub>: {value}
            </p>
          );
          break;
      }
    }

    return metadataText;
  };
  return <div className="custom-metadata-box">{createMetadataText()}</div>;
};

export default MetadataBox;
