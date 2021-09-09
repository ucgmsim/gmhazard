import os
import tempfile

import flask
from flask_cors import cross_origin

import seistech_utils as su
from project_api import constants as const
from project_api import utils
from project_api import server


@server.app.route(const.PROJECT_GMS_RUNS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_gms_runs():
    server.app.logger.info(f"Received request at {const.PROJECT_GMS_RUNS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    project_id = su.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    server.app.logger.debug(f"Request parameters {project_id}")

    # Load the project config
    project = utils.get_project(version_str, project_id)

    return flask.jsonify(
        {cur_params.id: cur_params.to_dict() for cur_params in project.gms_params}
    )


@server.app.route(const.PROJECT_GMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_ensemble_gms():
    server.app.logger.info(f"Received request at {const.PROJECT_GMS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (project_id, station_id, gms_id), _ = su.api.get_check_keys(
        flask.request.args, ("project_id", "station_id", "gms_id")
    )
    server.app.logger.debug(f"Request parameters {project_id}, {station_id}, {gms_id}")

    results_dir = (
        server.BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    )
    gms_result, cs_param_bounds, disagg_data = utils.load_gms_data(results_dir, gms_id)

    return flask.jsonify(
        su.api.get_ensemble_gms(
            gms_result,
            su.api.get_download_token(
                dict(project_id=project_id, station_id=station_id, gms_id=gms_id),
                server.DOWNLOAD_URL_SECRET_KEY,
                server.DOWNLOAD_URL_VALID_FOR,
            ),
            disagg_data,
            project_id,
        )
    )


@server.app.route(f"{const.PROJECT_GMS_DOWNLOAD_ENDPOINT}/<token>", methods=["GET"])
@su.api.endpoint_exception_handling(server.app)
def download_gms_results(token):
    server.app.logger.info(f"Received request at {const.PROJECT_GMS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")
    payload = su.api.get_token_payload(token, server.DOWNLOAD_URL_SECRET_KEY)
    project_id, station_id = payload["project_id"], payload["station_id"]
    gms_id = payload["gms_id"]

    results_dir = (
        server.BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    )
    gms_result, cs_param_bounds, disagg_data = utils.load_gms_data(results_dir, gms_id)

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = su.api.create_gms_download_zip(
            gms_result,
            server.app,
            tmp_dir,
            disagg_data,
            cs_param_bounds=cs_param_bounds,
        )
        return flask.send_file(
            zip_ffp, as_attachment=True, attachment_filename=os.path.basename(zip_ffp)
        )


@server.app.route(
    f"{const.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT}", methods=["GET"]
)
@su.api.endpoint_exception_handling(server.app)
def get_default_causal_params():
    server.app.logger.info(
        f"Received request at {const.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT}"
    )

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (project_id, station_id, gms_id), _ = su.api.get_check_keys(
        flask.request.args, ("project_id", "station_id", "gms_id")
    )
    server.app.logger.debug(f"Request parameters {project_id}, {station_id}, {gms_id}")

    results_dir = (
        server.BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    )
    gms_result, cs_param_bounds, disagg_data = utils.load_gms_data(results_dir, gms_id)

    return flask.jsonify(su.api.get_default_causal_params(cs_param_bounds))
