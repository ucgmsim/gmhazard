import base64
import tempfile
import json
import multiprocessing as mp
from pathlib import Path

import pandas as pd
import flask
from flask_cors import cross_origin

import seistech_utils as su
import gmhazard_calc as sc
import project_gen as pg
from project_api import utils
from project_api import server
from project_api import constants as const


@server.app.route(const.PROJECT_IDS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_available_ids():
    server.app.logger.info(f"Received request at {const.PROJECT_IDS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    server.app.logger.info(
        f"Retrieving available projects for version {version_str} and "
        f"project base directory {server.BASE_PROJECTS_DIR}"
    )

    project_ids = []
    for cur_dir in (server.BASE_PROJECTS_DIR / version_str).iterdir():
        if cur_dir.is_dir():
            project_ids.append(cur_dir.name)

    return flask.jsonify({"ids": project_ids})


@server.app.route(const.PROJECT_SITES_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_available_sites():
    server.app.logger.info(f"Received request at {const.PROJECT_SITES_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    project_id = su.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    server.app.logger.debug(f"Request parameters {project_id}")

    # Load the project config
    project = utils.get_project(version_str, project_id)

    ## Hack: Have lat/lon in the project config file later
    ensemble = sc.gm_data.Ensemble(project_id, config_ffp=project.ensemble_ffp)

    loc_dict = {}

    for loc_id, loc_data in project.locations.items():
        cur_site_info = sc.site.get_site_from_name(
            ensemble,
            pg.utils.create_station_id(
                loc_id,
                loc_data.vs30_values[0],
                None if loc_data.z1p0_values is None else loc_data.z1p0_values[0],
                None if loc_data.z2p5_values is None else loc_data.z2p5_values[0],
            ),
        )
        loc_dict[loc_id] = {
            "name": loc_data.name,
            "vs30": loc_data.vs30_values,
            "Z1.0": loc_data.z1p0_values,
            "Z2.5": loc_data.z2p5_values,
            "lat": cur_site_info.lat,
            "lon": cur_site_info.lon,
        }

    return flask.jsonify(loc_dict)


@server.app.route(const.PROJECT_IMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_available_IMs():
    server.app.logger.info(f"Received request at {const.PROJECT_IMS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    project_id = su.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    server.app.logger.debug(f"Request parameters {project_id}")

    # Load the project config
    project = utils.get_project(version_str, project_id)

    return flask.jsonify(
        {
            "ims": su.api.get_available_im_dict(
                project.ims, components=project.components
            )
        }
    )


@server.app.route(const.PROJECT_CONTEXT_MAPS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_context_maps():
    server.app.logger.info(f"Received request at {const.PROJECT_CONTEXT_MAPS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (project_id, station_id), _ = su.api.get_check_keys(
        flask.request.args, ("project_id", "station_id")
    )
    server.app.logger.debug(f"Request parameters {project_id}, {station_id}")

    results_dir = (
        server.BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id
    )

    try:
        with open(results_dir / "context_map_plot.png", "rb") as f:
            context_map_data = f.read()

        with open(results_dir / "vs30_map_plot.png", "rb") as f:
            vs30_map_data = f.read()

    except FileNotFoundError as ex:
        server.app.logger.error(f"Result file {ex.filename} does not exist")
        return flask.jsonify("Failed to find one of the results file!"), 500

    return flask.jsonify(
        {
            "vs30_plot": base64.b64encode(vs30_map_data).decode(),
            "context_plot": base64.b64encode(context_map_data).decode(),
        }
    )


@server.app.route(const.PROJECT_DOWNLOAD_TOKEN_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_download_all_token():
    server.app.logger.info(
        f"Received request at {const.PROJECT_DOWNLOAD_TOKEN_ENDPOINT}"
    )

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (project_id,), _ = su.api.get_check_keys(flask.request.args, ("project_id",))
    server.app.logger.debug(f"Request parameters {project_id}")

    return flask.jsonify(
        {
            "download_token": su.api.get_download_token(
                {"project_id": project_id},
                server.DOWNLOAD_URL_SECRET_KEY,
                server.DOWNLOAD_URL_VALID_FOR,
            )
        }
    )


@server.app.route(const.PROJECT_CREATE_NEW_ENDPOINT, methods=["POST"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def create_new():
    """
    Parameters
    ----------
    project_specs: dictionary
        The project parameters,
        Example of JSON format:
        {
            "id": "test",
            "name": "Test Project",
            "locations": {
                "location_1": {
                    "name": "Location One",
                    "lat": -45.03111944,
                    "lon": 168.6589861,
                    "vs30": [200, 250],
                    "z1p0": [2, 4],
                    "z2p5": [5, 10],
                },
                "location_2": {
                    "name": "Location Two",
                    "lat": -43.7,
                    "lon": 171.51,
                    "vs30": [300, 400],
                    "z1p0": [null, 4],
                    "z2p5": [null, 10],
                },
            },
            "package_type": "pga",
        }
    """
    server.app.logger.info(f"Received request at {const.PROJECT_DOWNLOAD_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    project_params = json.loads(flask.request.data.decode())
    server.app.logger.debug(f"Project parameters {project_params}")

    server.app.logger.info(
        f"Triggering generation of new project {project_params['id']}"
    )
    seistech_root_dir = Path(__file__).resolve().parent.parent.parent.parent
    pg.tasks.create_project_task.server.apply_async(
        queue="project_gen",
        args=[
            project_params,
            str(server.BASE_PROJECTS_DIR),
            str(seistech_root_dir / "seistech_scripts/seistech_scripts/local"),
        ],
        kwargs={"new_project": True},
    )

    return ("", 200)


@server.app.route(f"{const.PROJECT_DOWNLOAD_ENDPOINT}/<token>", methods=["GET"])
@su.api.endpoint_exception_handling(server.app)
def download_all(token):
    server.app.logger.info(f"Received request at {const.PROJECT_DOWNLOAD_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    project_id = su.api.get_token_payload(token, server.DOWNLOAD_URL_SECRET_KEY)[
        "project_id"
    ]
    server.app.logger.debug(f"Token parameters {project_id}")

    with tempfile.TemporaryDirectory() as zip_tmp_dir:
        zip_ffp = utils.create_project_zip(
            server.BASE_PROJECTS_DIR, project_id, version_str, zip_tmp_dir
        )

        return flask.send_file(
            zip_ffp,
            as_attachment=True,
            attachment_filename=f"{project_id}_data.zip",
        )
