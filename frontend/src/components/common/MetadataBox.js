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
        case CONSTANTS.NZS_1170P5_SOIL_CLASS:
          metadataText.push(
            <p key={key}>
              {key}: {CONSTANTS.NZS_SOIL_CLASS_OBJ[value]}
            </p>
          );
          break;
        case CONSTANTS.NZTA_SOIL_CLASS:
          metadataText.push(
            <p key={key}>
              {key}: {CONSTANTS.NZTA_SOIL_CLASS_OBJ[value]}
            </p>
          );
          break;
        case CONSTANTS.SITE_SELECTION_VS30_TITLE:
          metadataText.push(
            <p key={key}>
              V<sub>s30</sub>: {value}
            </p>
          );
          break;
        case CONSTANTS.METADATA_Z1P0_LABEL:
          metadataText.push(
            <p key={key}>
              Z<sub>1.0</sub>: {value}
            </p>
          );
          break;
        case CONSTANTS.METADATA_Z2P5_LABEL:
          metadataText.push(
            <p key={key}>
              Z<sub>2.5</sub>: {value}
            </p>
          );
          break;
        case CONSTANTS.DISCLAIMER:
          metadataText.push(
            <span key={key} onClick={() => console.log("TEXT CLICKED")}>
              {key}: {value}
            </span>
          );
      }
    }

    return metadataText;
  };
  return <div className="custom-metadata-box">{createMetadataText()}</div>;
};

export default MetadataBox;
