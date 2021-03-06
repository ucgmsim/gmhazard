import tempfile

import flask
from flask_cors import cross_origin

import api_utils as au
import gmhazard_utils as su
import gmhazard_calc as sc
from project_api import constants as const
from project_api import server
from project_api import utils


@server.app.route(const.PROJECT_SCENARIO_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@au.api.endpoint_exception_handling(server.app)
def get_ensemble_scenario():
    server.app.logger.info(f"Received request at {const.PROJECT_SCENARIO_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (project_id, station_id), optional_kwargs = au.api.get_check_keys(
        flask.request.args,
        ("project_id", "station_id"),
        (("im_component", sc.im.IMComponent, sc.im.IMComponent.RotD50),),
    )
    im_component = optional_kwargs.get("im_component")
    server.app.logger.debug(
        f"Request parameters {project_id}, {station_id}, {im_component}"
    )

    # Load the data
    project_dir = server.BASE_PROJECTS_DIR / version_str / project_id
    ensemble_scenario = sc.scenario.EnsembleScenarioResult.load(
        project_dir / "results" / station_id / str(im_component) / "scenario",
    )

    return flask.jsonify(
        {
            **au.api.get_ensemble_scenario_response(
                # Filters the ruptures to the top 20 based on geometric mean
                sc.scenario.filter_ruptures(ensemble_scenario),
                au.api.get_download_token(
                    {
                        "type": "ensemble_scenario",
                        "project_id": project_id,
                        "station": ensemble_scenario.site_info.station_name,
                        "user_vs30": ensemble_scenario.site_info.user_vs30,
                        "im_component": str(im_component),
                    },
                    server.DOWNLOAD_URL_SECRET_KEY,
                ),
            ),
            "rupture_metadata": utils.load_scenario_rupture_metadata(
                project_dir,
                project_id,
                station_id,
                im_component,
                list(
                    sc.scenario.filter_ruptures(ensemble_scenario)
                    .to_dict()["mu_data"]
                    .keys()
                ),
            ).to_dict(),
        }
    )


@server.app.route(const.PROJECT_SCENARIO_DOWNLOAD_ENDPOINT, methods=["GET"])
@au.api.endpoint_exception_handling(server.app)
def download_ens_scenario():
    """Handles downloading of the scenario data,
    specified by the given token"""
    server.app.logger.info(
        f"Received request at {const.PROJECT_SCENARIO_DOWNLOAD_ENDPOINT}"
    )

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    server.app.logger.debug(f"API - version {version_str}")

    (token,), _ = au.api.get_check_keys(flask.request.args, ("scenario_token",))

    payload = au.api.get_token_payload(token, server.DOWNLOAD_URL_SECRET_KEY)

    project_id, station, im_component = (
        payload["project_id"],
        payload["station"],
        payload["im_component"],
    )

    server.app.logger.debug(f"Token parameters {project_id}, {station}, {im_component}")

    project_dir = server.BASE_PROJECTS_DIR / version_str / project_id
    # Load the data
    ensemble_scenario = sc.scenario.EnsembleScenarioResult.load(
        project_dir / "results" / station / im_component / "scenario",
    )
    # Load rupture metadata
    rupture_metadata = utils.load_scenario_rupture_metadata(
        project_dir,
        project_id,
        station,
        sc.im.IMComponent[im_component],
        list(
            sc.scenario.filter_ruptures(ensemble_scenario).to_dict()["mu_data"].keys()
        ),
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = au.api.create_scenario_download_zip(
            ensemble_scenario, rupture_metadata, tmp_dir
        )

        return flask.send_file(
            zip_ffp,
            as_attachment=True,
            attachment_filename=f"{project_id}_{ensemble_scenario.site_info.station_name}_scenario.zip",
        )
