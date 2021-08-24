import os
import tempfile

import flask
import numpy as np
from flask_cors import cross_origin

import seistech_calc as si
import seistech_utils as su
from seistech_calc.im import IMComponent
from ..utils import get_project
from ..server import (
    app,
    requires_auth,
    DOWNLOAD_URL_VALID_FOR,
    DOWNLOAD_URL_SECRET_KEY,
    BASE_PROJECTS_DIR,
)
from .. import constants as const
from ..utils import load_uhs_data


@app.route(const.PROJECT_UHS_RPS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_uhs_rps():
    app.logger.info(f"Received request at {const.PROJECT_UHS_RPS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    project_id = su.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    app.logger.debug(f"Request parameters {project_id}")

    return flask.jsonify(
        {"rps": get_project(version_str, project_id).uhs_return_periods}
    )


@app.route(const.PROJECT_UHS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_ensemble_uhs():
    app.logger.info(f"Received request at {const.PROJECT_UHS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    (project_id, station_id), optional_kwargs = su.api.get_check_keys(
        flask.request.args, ("project_id", "station_id"),
        (("im_component", str),),
    )
    im_component = (
        IMComponent.RotD50
        if optional_kwargs.get("im_component") is None
        else IMComponent[optional_kwargs.get("im_component")]
    )
    app.logger.debug(f"Request parameters {project_id}, {station_id}")

    # Get UHS return periods
    rps = get_project(version_str, project_id).uhs_return_periods

    # Load the data
    uhs_results, nzs1170p5_results = load_uhs_data(
        BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id / str(im_component), rps
    )

    return flask.jsonify(
        {
            **su.api.get_ensemble_uhs(
                uhs_results,
                su.api.get_download_token(
                    {"project_id": project_id, "station_id": station_id, "im_component": str(im_component),},
                    DOWNLOAD_URL_SECRET_KEY,
                    DOWNLOAD_URL_VALID_FOR,
                ),
            ),
            "nzs1170p5_uhs_df": si.nz_code.nzs1170p5.NZS1170p5Result.combine_results(
                nzs1170p5_results
            )
            .replace(np.nan, "nan")
            .to_dict(),
            "nzs1170p5_results": [
                result.to_dict(nan_to_string=True) for result in nzs1170p5_results
            ],
        }
    )


@app.route(const.PROJECT_UHS_DOWNLOAD_ENDPOINT, methods=["GET"])
@su.api.endpoint_exception_handling(app)
def download_ensemble_uhs():
    """Handles downloading of the UHS raw data"""
    app.logger.info(f"Received request at {const.PROJECT_UHS_DOWNLOAD_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    (token), _ = su.api.get_check_keys(flask.request.args, ("uhs_token",))

    payload = su.api.get_token_payload(token[0], DOWNLOAD_URL_SECRET_KEY)
    project_id, station_id, im_component = (
        payload["project_id"],
        payload["station_id"],
        payload["im_component"],
    )
    app.logger.debug(f"Request parameters {project_id}, {station_id}")

    # Get UHS return periods
    rps = get_project(version_str, project_id).uhs_return_periods

    # Load the data
    uhs_results, nzs1170p5_results = load_uhs_data(
        BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id / im_component, rps
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = su.api.create_uhs_download_zip(
            uhs_results, nzs1170p5_results, tmp_dir
        )

        return flask.send_file(
            zip_ffp, as_attachment=True, attachment_filename=os.path.basename(zip_ffp)
        )
