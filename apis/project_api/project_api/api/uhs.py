import os
import tempfile

import flask
import numpy as np
from flask_cors import cross_origin

import api_utils as au
import gmhazard_calc as sc
import gmhazard_utils as su
from project_api import server
from project_api import constants as const
from project_api import utils


@server.app.route(const.PROJECT_UHS_RPS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@au.api.endpoint_exception_handling(server.app)
def get_uhs_rps():
    server.app.logger.info(f"Received request at {const.PROJECT_UHS_RPS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    project_id = au.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    server.app.logger.debug(f"Request parameters {project_id}")

    return flask.jsonify(
        {"rps": utils.get_project(version_str, project_id).uhs_return_periods}
    )


@server.app.route(const.PROJECT_UHS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@au.api.endpoint_exception_handling(server.app)
def get_ensemble_uhs():
    server.app.logger.info(f"Received request at {const.PROJECT_UHS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (project_id, station_id), optional_kwargs = au.api.get_check_keys(
        flask.request.args, ("project_id", "station_id"), (("im_component", str),),
    )
    im_component = (
        sc.im.IMComponent.RotD50
        if optional_kwargs.get("im_component") is None
        else sc.im.IMComponent[optional_kwargs.get("im_component")]
    )
    server.app.logger.debug(f"Request parameters {project_id}, {station_id}")

    # Get UHS return periods
    rps = utils.get_project(version_str, project_id).uhs_return_periods

    # Load the data
    uhs_results, nzs1170p5_results = utils.load_uhs_data(
        server.BASE_PROJECTS_DIR
        / version_str
        / project_id
        / "results"
        / station_id
        / str(im_component),
        rps,
    )

    return flask.jsonify(
        {
            **au.api.get_ensemble_uhs(
                uhs_results,
                au.api.get_download_token(
                    {
                        "project_id": project_id,
                        "station_id": station_id,
                        "im_component": str(im_component),
                    },
                    server.DOWNLOAD_URL_SECRET_KEY,
                ),
            ),
            "nzs1170p5_uhs_df": sc.nz_code.nzs1170p5.NZS1170p5Result.combine_results(
                nzs1170p5_results
            )
            .replace(np.nan, "nan")
            .to_dict(),
            "nzs1170p5_results": [
                result.to_dict(nan_to_string=True) for result in nzs1170p5_results
            ],
        }
    )


@server.app.route(const.PROJECT_UHS_DOWNLOAD_ENDPOINT, methods=["GET"])
@au.api.endpoint_exception_handling(server.app)
def download_ensemble_uhs():
    """Handles downloading of the UHS raw data"""
    server.app.logger.info(f"Received request at {const.PROJECT_UHS_DOWNLOAD_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (token), _ = au.api.get_check_keys(flask.request.args, ("uhs_token",))

    payload = au.api.get_token_payload(token[0], server.DOWNLOAD_URL_SECRET_KEY)
    project_id, station_id, im_component = (
        payload["project_id"],
        payload["station_id"],
        payload["im_component"],
    )
    server.app.logger.debug(f"Request parameters {project_id}, {station_id}")

    # Get UHS return periods
    rps = utils.get_project(version_str, project_id).uhs_return_periods

    # Load the data
    uhs_results, nzs1170p5_results = utils.load_uhs_data(
        server.BASE_PROJECTS_DIR
        / version_str
        / project_id
        / "results"
        / station_id
        / im_component,
        rps,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = au.api.create_uhs_download_zip(
            uhs_results, nzs1170p5_results, tmp_dir
        )

        return flask.send_file(
            zip_ffp, as_attachment=True, attachment_filename=os.path.basename(zip_ffp)
        )
