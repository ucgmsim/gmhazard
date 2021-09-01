import React from "react";

import { ERROR_SET_DIFF_CODE } from "constants/Constants";

import "assets/style/Messages.css";

const ErrorMessage = ({ errorCode }) => {
  return (
    <div className="card text-white bg-danger mb-3 card-message">
      <div className="card-header">
        {errorCode && ERROR_SET_DIFF_CODE.hasOwnProperty(errorCode)
          ? ERROR_SET_DIFF_CODE[errorCode].ERROR_MSG_HEADER
          : ERROR_SET_DIFF_CODE["DEFAULT"].ERROR_MSG_HEADER}
      </div>
      <div className="card-body">
        <h5 className="card-title">
          {errorCode && ERROR_SET_DIFF_CODE.hasOwnProperty(errorCode)
            ? ERROR_SET_DIFF_CODE[errorCode].ERROR_MSG_TITLE
            : ERROR_SET_DIFF_CODE["DEFAULT"].ERROR_MSG_TITLE}
        </h5>

        <p>
          {errorCode && ERROR_SET_DIFF_CODE.hasOwnProperty(errorCode)
            ? ERROR_SET_DIFF_CODE[errorCode].ERROR_MSG_BODY
            : ERROR_SET_DIFF_CODE["DEFAULT"].ERROR_MSG_BODY}
        </p>
      </div>
    </div>
  );
};

export default ErrorMessage;
