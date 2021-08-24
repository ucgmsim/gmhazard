import os
import shutil
import base64
import tempfile
import zipfile
import json
import multiprocessing as mp
from pathlib import Path

import pandas as pd
import flask
from flask_cors import cross_origin

import seistech_utils as su
import seistech_calc as si
from project_gen import tasks, utils
from ..utils import (
    get_project,
    load_hazard_data,
    load_disagg_data,
    load_uhs_data,
    Project,
)
from ..server import (
    app,
    requires_auth,
    DOWNLOAD_URL_SECRET_KEY,
    DOWNLOAD_URL_VALID_FOR,
    BASE_PROJECTS_DIR,
)
from .. import constants as const


@app.route(const.PROJECT_IDS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_available_ids():
    app.logger.info(f"Received request at {const.PROJECT_IDS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    app.logger.info(
        f"Retrieving available projects for version {version_str} and "
        f"project base directory {BASE_PROJECTS_DIR}"
    )

    project_ids = []
    for cur_dir in (BASE_PROJECTS_DIR / version_str).iterdir():
        if cur_dir.is_dir():
            project_ids.append(cur_dir.name)

    return flask.jsonify({"ids": project_ids})


@app.route(const.PROJECT_SITES_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_available_sites():
    app.logger.info(f"Received request at {const.PROJECT_SITES_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    project_id = su.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    app.logger.debug(f"Request parameters {project_id}")

    # Load the project config
    project = get_project(version_str, project_id)

    ## Hack: Have lat/lon in the project config file later
    ensemble = si.gm_data.Ensemble(project_id, config_ffp=project.ensemble_ffp)

    loc_dict = {}

    for loc_id, loc_data in project.locations.items():
        cur_site_info = si.site.get_site_from_name(
            ensemble,
            utils.create_station_id(
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


@app.route(const.PROJECT_IMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_available_IMs():
    app.logger.info(f"Received request at {const.PROJECT_IMS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    project_id = su.api.get_check_keys(flask.request.args, ["project_id"])[0][0]
    app.logger.debug(f"Request parameters {project_id}")

    # Load the project config
    project = get_project(version_str, project_id)

    return flask.jsonify(
        {
            "ims": su.api.get_available_im_dict(
                project.ims, components=project.components
            )
        }
    )


@app.route(const.PROJECT_CONTEXT_MAPS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_context_maps():
    app.logger.info(f"Received request at {const.PROJECT_CONTEXT_MAPS_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    (project_id, station_id), _ = su.api.get_check_keys(
        flask.request.args, ("project_id", "station_id")
    )
    app.logger.debug(f"Request parameters {project_id}, {station_id}")

    results_dir = BASE_PROJECTS_DIR / version_str / project_id / "results" / station_id

    try:
        with open(results_dir / "context_map_plot.png", "rb") as f:
            context_map_data = f.read()

        with open(results_dir / "vs30_map_plot.png", "rb") as f:
            vs30_map_data = f.read()

    except FileNotFoundError as ex:
        app.logger.error(f"Result file {ex.filename} does not exist")
        return flask.jsonify("Failed to find one of the results file!"), 500

    return flask.jsonify(
        {
            "vs30_plot": base64.b64encode(vs30_map_data).decode(),
            "context_plot": base64.b64encode(context_map_data).decode(),
        }
    )


@app.route(const.PROJECT_DOWNLOAD_TOKEN_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_download_all_token():
    app.logger.info(f"Received request at {const.PROJECT_DOWNLOAD_TOKEN_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    (project_id,), _ = su.api.get_check_keys(flask.request.args, ("project_id",))
    app.logger.debug(f"Request parameters {project_id}")

    return flask.jsonify(
        {
            "download_token": su.api.get_download_token(
                {"project_id": project_id},
                DOWNLOAD_URL_SECRET_KEY,
                DOWNLOAD_URL_VALID_FOR,
            )
        }
    )


@app.route(const.PROJECT_CREATE_NEW_ENDPOINT, methods=["POST"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def create_new():
    """
    Parameters
    ----------
    project_params: dictionary
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
    app.logger.info(f"Received request at {const.PROJECT_DOWNLOAD_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    project_params = json.loads(flask.request.data.decode())
    app.logger.debug(f"Project parameters {project_params}")

    app.logger.info(f"Triggering generation of new project {project_params['id']}")
    seistech_root_dir = Path(__file__).resolve().parent.parent.parent.parent
    tasks.create_project_task.apply_async(
        queue="project_gen",
        args=[
            project_params,
            str(BASE_PROJECTS_DIR),
            str(seistech_root_dir / "seistech_scripts/seistech_scripts/local"),
        ],
        kwargs={"new_project": True},
    )

    return ("", 200)


@app.route(f"{const.PROJECT_DOWNLOAD_ENDPOINT}/<token>", methods=["GET"])
@su.api.endpoint_exception_handling(app)
def download_all(token):
    app.logger.info(f"Received request at {const.PROJECT_DOWNLOAD_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    project_id = su.api.get_token_payload(token, DOWNLOAD_URL_SECRET_KEY)["project_id"]
    app.logger.debug(f"Token parameters {project_id}")

    with tempfile.TemporaryDirectory() as zip_tmp_dir:
        zip_ffp = create_project_zip(
            BASE_PROJECTS_DIR, project_id, version_str, zip_tmp_dir
        )

        return flask.send_file(
            zip_ffp, as_attachment=True, attachment_filename=f"{project_id}_data.zip",
        )


def create_project_zip(
    base_project_dir: Path,
    project_id: str,
    version_str: str,
    output_dir: Path,
    n_procs: int = 1,
):
    """Saves the project as zip file (in download format)"""
    project = Project.load(
        base_project_dir / version_str / project_id / f"{project_id}.yaml"
    )

    with tempfile.TemporaryDirectory() as data_tmp_dir:
        data_tmp_dir = Path(data_tmp_dir)
        if n_procs == 1:
            for cur_station_id in project.station_ids:
                _write_station(
                    data_tmp_dir,
                    project,
                    base_project_dir
                    / version_str
                    / project_id
                    / "results"
                    / cur_station_id,
                    project_id,
                    cur_station_id,
                )
        else:
            with mp.Pool(n_procs) as p:
                p.starmap(
                    _write_station,
                    [
                        (
                            data_tmp_dir,
                            project,
                            base_project_dir
                            / version_str
                            / project_id
                            / "results"
                            / cur_station_id,
                            project_id,
                            cur_station_id,
                        )
                        for cur_station_id in project.station_ids
                    ],
                )

        zip_ffp = Path(output_dir) / f"{project_id}.zip"
        with zipfile.ZipFile(zip_ffp, mode="w") as cur_zip:
            for cur_dir, cur_dir_names, cur_file_names in os.walk(
                data_tmp_dir / project_id
            ):
                for cur_filename in cur_file_names:
                    cur_zip.write(
                        os.path.join(cur_dir, cur_filename),
                        os.path.relpath(
                            os.path.join(cur_dir, cur_filename),
                            os.path.join(data_tmp_dir / project_id, ".."),
                        ),
                    )

            return zip_ffp


def _write_station(
    data_tmp_dir: Path,
    project: Project,
    cur_data_dir: Path,
    project_id: str,
    station_id: str,
):
    cur_output_dir = data_tmp_dir / project_id / station_id
    cur_output_dir.mkdir(exist_ok=False, parents=True)

    shutil.copy(cur_data_dir / "context_map_plot.png", cur_output_dir)
    shutil.copy(cur_data_dir / "vs30_map_plot.png", cur_output_dir)

    for component in project.components:
        for cur_im in project.ims:
            # Load & write hazard
            ensemble_hazard, nzs1170p5_hazard, nzta_hazard = load_hazard_data(
                cur_data_dir / str(component), cur_im
            )
            su.api.write_hazard_download_data(
                ensemble_hazard,
                nzs1170p5_hazard,
                str(cur_output_dir),
                nzta_hazard=nzta_hazard,
            )

            # Load & Write disagg for all return periods
            mean_values, contributions = {}, {}
            for cur_rp in project.disagg_rps:
                (
                    ensemble_disagg,
                    metadata_df,
                    src_png_data,
                    eps_png_data,
                ) = load_disagg_data(cur_data_dir / str(component), cur_im, cur_rp)

                su.api.write_disagg_download_data(
                    ensemble_disagg,
                    metadata_df,
                    str(cur_output_dir),
                    src_plot_data=src_png_data,
                    eps_plot_data=eps_png_data,
                )

                mean_values[cur_rp] = ensemble_disagg.mean_values
                contributions[cur_rp] = ensemble_disagg.total_contributions

            pd.concat(contributions, axis=1).to_csv(
                cur_output_dir / f"{cur_im}_disagg_contributions.csv"
            )
            pd.concat(mean_values, axis=1).to_csv(
                cur_output_dir / f"{cur_im}_disagg_mean_values.csv"
            )

        # Load & Write UHS
        uhs_results, nzs1170p5_results = load_uhs_data(
            cur_data_dir / str(component), project.uhs_return_periods
        )
        su.api.write_uhs_download_data(
            uhs_results, nzs1170p5_results, str(cur_output_dir)
        )
