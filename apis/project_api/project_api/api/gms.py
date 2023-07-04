import os
import tempfile

import flask
from flask_cors import cross_origin

import api_utils as au
import gmhazard_utils as su
from project_api import constants as const
from project_api import utils
from project_api import server


@server.app.route(const.PROJECT_GMS_RUNS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@au.api.endpoint_exception_handling(server.app)
def get_gms_runs():
    server.app.logger.info(f"Received request at {const.PROJECT_GMS_RUNS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    project_id = au.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    server.app.logger.debug(f"Request parameters {project_id}")

    # Load the project config
    project = utils.get_project(version_str, project_id)

    return flask.jsonify(
        {cur_params.id: cur_params.to_dict() for cur_params in project.gms_params}
    )


@server.app.route(const.PROJECT_GMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@au.api.endpoint_exception_handling(server.app)
def get_ensemble_gms():
    server.app.logger.info(f"Received request at {const.PROJECT_GMS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (project_id, station_id, gms_id), _ = au.api.get_check_keys(
        flask.request.args, ("project_id", "station_id", "gms_id")
    )
    server.app.logger.debug(f"Request parameters {project_id}, {station_id}, {gms_id}")

    results_dir = (
        server.BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    )
    gms_result, cs_param_bounds, disagg_data = utils.load_gms_data(results_dir, gms_id)

    return flask.jsonify(
        au.api.get_ensemble_gms(
            gms_result,
            au.api.get_download_token(
                dict(project_id=project_id, station_id=station_id, gms_id=gms_id),
                server.DOWNLOAD_URL_SECRET_KEY,
            ),
            disagg_data,
            project_id,
        )
    )


@server.app.route(const.PROJECT_GMS_DOWNLOAD_ENDPOINT, methods=["GET"])
@au.api.endpoint_exception_handling(server.app)
def download_gms_results():
    server.app.logger.info(f"Received request at {const.PROJECT_GMS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (gms_token,), _ = au.api.get_check_keys(flask.request.args, ("gms_token",))
    payload = au.api.get_token_payload(gms_token, server.DOWNLOAD_URL_SECRET_KEY)
    project_id, station_id, gms_id = (
        payload["project_id"],
        payload["station_id"],
        payload["gms_id"],
    )

    results_dir = (
        server.BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    )
    gms_result, cs_param_bounds, disagg_data = utils.load_gms_data(results_dir, gms_id)

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp, missing_waveforms = au.api.create_gms_download_zip(
            gms_result, tmp_dir, disagg_data
        )

        if missing_waveforms > 0:
            server.app.logger.info(
                f"Failed to find waveforms for simulations: {missing_waveforms}"
            )

        return flask.send_file(
            zip_ffp, as_attachment=True, attachment_filename=os.path.basename(zip_ffp)
        )


@server.app.route(
    f"{const.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT}", methods=["GET"]
)
@au.api.endpoint_exception_handling(server.app)
def get_default_causal_params():
    server.app.logger.info(
        f"Received request at {const.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT}"
    )

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (project_id, station_id, gms_id), _ = au.api.get_check_keys(
        flask.request.args, ("project_id", "station_id", "gms_id")
    )
    server.app.logger.debug(f"Request parameters {project_id}, {station_id}, {gms_id}")

    results_dir = (
        server.BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    )
    gms_result, cs_param_bounds, disagg_data = utils.load_gms_data(results_dir, gms_id)

    return flask.jsonify(au.api.get_default_causal_params(cs_param_bounds))
