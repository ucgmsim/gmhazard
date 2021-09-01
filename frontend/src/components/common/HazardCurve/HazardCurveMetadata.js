import React from "react";

import { NZTA_SOIL_CLASS, NZS_SOIL_CLASS } from "constants/Constants";

const HazardCurveMetadata = ({ metadata }) => {
  const createMetadataText = () => {
    let metadataText = "";
    for (const [key, value] of Object.entries(metadata)) {
      if (key.includes("NZS1170.5 Soil")) {
        metadataText += `${key}: ${NZS_SOIL_CLASS[value]}\n`;
      } else if (key.includes("NZTA Soil")) {
        metadataText += `${key}: ${NZTA_SOIL_CLASS[value]}\n`;
      } else {
        metadataText += `${key}: ${value}\n`;
      }
    }

    return metadataText.slice(0, -1);
  };
  return (
    <div className="form-group">
      <textarea
        style={{ color: "red", resize: "none" }}
        className="form-control"
        disabled
        rows={Object.keys(metadata).length}
        value={createMetadataText()}
      ></textarea>
    </div>
  );
};

export default HazardCurveMetadata;
