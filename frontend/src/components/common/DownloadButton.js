import React, { useState } from "react";

import axios from "axios";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { useAuth0 } from "components/common/ReactAuth0SPA";

import { INTERMEDIATE_API_URL } from "constants/Constants";
import { handleErrors } from "utils/Utils";

const DownloadButton = ({
  downloadURL,
  downloadToken = null,
  fileName,
  disabled,
}) => {
  const { isAuthenticated, getTokenSilently } = useAuth0();

  const [downloadButtonLabel, setDownloadButtonLabel] = useState({
    icon: <FontAwesomeIcon icon="download" className="mr-3" />,
    isFetching: false,
  });

  const downloadData = async () => {
    const token = await getTokenSilently();
    setDownloadButtonLabel({
      icon: <FontAwesomeIcon icon="spinner" className="mr-3" spin />,
      isFetching: true,
    });

    let queryString = "";
    if (downloadToken !== null) {
      queryString += "?";
      // downloadToken is now an object form
      for (const [param, value] of Object.entries(downloadToken)) {
        // if IM is not pSA nor PGA, NZ Code will be an empty string
        if (value !== "") {
          queryString += `${param}=${value}&`;
        }
      }
      // remove the last character which is an extra &
      queryString = queryString.slice(0, -1);
    }

    axios({
      url: INTERMEDIATE_API_URL + downloadURL + queryString,
      headers: {
        Authorization: `Bearer ${token}`,
      },
      method: "GET",
      responseType: "blob",
    })
      .then(handleErrors)
      .then((response) => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", fileName);
        document.body.appendChild(link);
        link.click();
        setDownloadButtonLabel({
          icon: <FontAwesomeIcon icon="download" className="mr-3" />,
          isFetching: false,
        });
      })
      .catch((error) => {
        // Later on, maybe can add Modal to tell users an error msg.
        setDownloadButtonLabel({
          icon: <FontAwesomeIcon icon="download" className="mr-3" />,
          isFetching: false,
        });
        console.log(error);
      });
  };

  const publicDownloadData = async () => {
    setDownloadButtonLabel({
      icon: <FontAwesomeIcon icon="spinner" className="mr-3" spin />,
      isFetching: true,
    });

    let queryString = "";
    if (downloadToken !== null) {
      queryString += "?";
      // downloadToken is now an object form
      for (const [param, value] of Object.entries(downloadToken)) {
        // if IM is not pSA nor PGA, NZ Code will be an empty string
        if (value !== "") {
          queryString += `${param}=${value}&`;
        }
      }
      // remove the last character which is an extra &
      queryString = queryString.slice(0, -1);
    }

    axios({
      url: INTERMEDIATE_API_URL + downloadURL + queryString,
      method: "GET",
      responseType: "blob",
    })
      .then(handleErrors)
      .then((response) => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", fileName);
        document.body.appendChild(link);
        link.click();
        setDownloadButtonLabel({
          icon: <FontAwesomeIcon icon="download" className="mr-3" />,
          isFetching: false,
        });
      })
      .catch((error) => {
        // Later on, maybe can add Modal to tell users an error msg.
        setDownloadButtonLabel({
          icon: <FontAwesomeIcon icon="download" className="mr-3" />,
          isFetching: false,
        });
        console.log(error);
      });
  };

  return (
    <button
      className="download-button btn btn-primary"
      disabled={disabled || downloadButtonLabel.isFetching === true}
      onClick={() => (isAuthenticated ? downloadData() : publicDownloadData())}
    >
      {downloadButtonLabel.icon}
      Download Data
    </button>
  );
};

export default DownloadButton;
