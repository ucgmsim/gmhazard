import os
import tempfile

import flask
from flask_cors import cross_origin

import api_utils as au
import gmhazard_calc as sc
import gmhazard_utils as su
from project_api import server
from project_api import constants as const
from project_api import utils


@server.app.route(const.PROJECT_DISAGG_RPS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@au.api.endpoint_exception_handling(server.app)
def get_disagg_rps():
    server.app.logger.info(f"Received request at {const.PROJECT_DISAGG_RPS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    project_id = au.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    server.app.logger.debug(f"Request parameters {project_id}")

    # Load the project config
    project = utils.get_project(version_str, project_id)

    return flask.jsonify({"rps": project.disagg_rps})


@server.app.route(const.PROJECT_DISAGG_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@au.api.endpoint_exception_handling(server.app)
def get_ensemble_disagg():
    server.app.logger.info(f"Received request at {const.PROJECT_DISAGG_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (project_id, station_id, im), optional_kwargs = au.api.get_check_keys(
        flask.request.args,
        ("project_id", "station_id", ("im", sc.im.IM.from_str)),
        (("im_component", str),),
    )
    im.component = (
        sc.im.IMComponent.RotD50
        if optional_kwargs.get("im_component") is None
        else sc.im.IMComponent[optional_kwargs.get("im_component")]
    )
    server.app.logger.debug(f"Request parameters {project_id}, {station_id}, {im}")

    # Get Disagg return periods
    rps = utils.get_project(version_str, project_id).disagg_rps

    # Load the data
    (
        ensemble_disagg_data,
        metadata_df_data,
        src_png_data,
        eps_png_data,
    ) = utils.load_disagg_data(
        server.BASE_PROJECTS_DIR
        / version_str
        / project_id
        / "results"
        / station_id
        / str(im.component),
        im,
        rps,
    )

    return flask.jsonify(
        au.api.get_ensemble_disagg(
            ensemble_disagg_data,
            metadata_df_data,
            src_png_data,
            eps_png_data,
            rps,
            au.api.get_download_token(
                {
                    "project_id": project_id,
                    "station_id": station_id,
                    "im": str(im),
                    "im_component": str(im.component),
                },
                server.DOWNLOAD_URL_SECRET_KEY,
            ),
        )
    )


@server.app.route(const.PROJECT_DISAGG_DOWNLOAD_ENDPOINT, methods=["Get"])
@au.api.endpoint_exception_handling(server.app)
def download_project_disagg():
    server.app.logger.info(
        f"Received request at {const.PROJECT_DISAGG_DOWNLOAD_ENDPOINT}"
    )

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (token), _ = au.api.get_check_keys(flask.request.args, ("disagg_token",))

    payload = au.api.get_token_payload(token[0], server.DOWNLOAD_URL_SECRET_KEY)
    project_id, station_id, im, im_component, rp = (
        payload["project_id"],
        payload["station_id"],
        sc.im.IM.from_str(payload["im"]),
        payload["im_component"],
        int(payload["rp"]),
    )
    server.app.logger.debug(
        f"Token parameters {project_id}, {station_id}, {im}, {im_component}, {rp}"
    )

    # Load the data
    ensemble_disagg, metadata_df, src_png_data, eps_png_data = utils.load_disagg_data(
        server.BASE_PROJECTS_DIR
        / version_str
        / project_id
        / "results"
        / station_id
        / im_component,
        im,
        rp,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = au.api.create_disagg_download_zip(
            ensemble_disagg,
            metadata_df,
            tmp_dir,
            src_plot_data=src_png_data,
            eps_plot_data=eps_png_data,
        )

        return flask.send_file(
            zip_ffp, as_attachment=True, attachment_filename=os.path.basename(zip_ffp)
        )
