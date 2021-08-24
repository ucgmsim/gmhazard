import os
import tempfile

import flask
from flask_cors import cross_origin

import seistech_utils as su
import project_api.constants as const
import project_api.utils as utils
from project_api.server import (
    app,
    requires_auth,
    DOWNLOAD_URL_SECRET_KEY,
    DOWNLOAD_URL_VALID_FOR,
    BASE_PROJECTS_DIR,
)


@app.route(const.PROJECT_GMS_RUNS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_gms_runs():
    app.logger.info(f"Received request at {const.PROJECT_GMS_RUNS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    project_id = su.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    app.logger.debug(f"Request parameters {project_id}")

    # Load the project config
    project = utils.get_project(version_str, project_id)

    return flask.jsonify(
        {cur_params.id: cur_params.to_dict() for cur_params in project.gms_params}
    )


@app.route(const.PROJECT_GMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_ensemble_gms():
    app.logger.info(f"Received request at {const.PROJECT_GMS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    (project_id, station_id, gms_id), _ = su.api.get_check_keys(
        flask.request.args, ("project_id", "station_id", "gms_id")
    )
    app.logger.debug(f"Request parameters {project_id}, {station_id}, {gms_id}")

    results_dir = BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    gms_result, cs_param_bounds = utils.load_gms_data(results_dir, gms_id)

    return flask.jsonify(
        su.api.get_ensemble_gms(
            gms_result,
            su.api.get_download_token(
                dict(project_id=project_id, station_id=station_id, gms_id=gms_id),
                DOWNLOAD_URL_SECRET_KEY,
                DOWNLOAD_URL_VALID_FOR,
            ),
        )
    )


@app.route(f"{const.PROJECT_GMS_DOWNLOAD_ENDPOINT}/<token>", methods=["GET"])
@su.api.endpoint_exception_handling(app)
def download_gms_results(token):
    app.logger.info(f"Received request at {const.PROJECT_GMS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")
    payload = su.api.get_token_payload(token, DOWNLOAD_URL_SECRET_KEY)
    project_id, station_id = payload["project_id"], payload["station_id"]
    gms_id = payload["gms_id"]

    results_dir = BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    gms_result, cs_param_bounds = utils.load_gms_data(results_dir, gms_id)

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = su.api.download_gms_result(gms_result, app, tmp_dir)
        return flask.send_file(
            zip_ffp, as_attachment=True, attachment_filename=os.path.basename(zip_ffp)
        )


@app.route(f"{const.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT}", methods=["GET"])
@su.api.endpoint_exception_handling(app)
def get_default_causal_params():
    app.logger.info(
        f"Received request at {const.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT}"
    )

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    (project_id, station_id, gms_id), _ = su.api.get_check_keys(
        flask.request.args, ("project_id", "station_id", "gms_id")
    )
    app.logger.debug(f"Request parameters {project_id}, {station_id}, {gms_id}")

    results_dir = BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    gms_result, cs_param_bounds = utils.load_gms_data(results_dir, gms_id)

    return flask.jsonify(su.api.get_default_causal_params(cs_param_bounds))
