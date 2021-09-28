import tempfile
from typing import Tuple, List

import flask
from flask_cors import cross_origin
from werkzeug.contrib.cache import BaseCache

import gmhazard_calc as sc
import gmhazard_utils as su
from core_api import server
from core_api import constants as const


class ScenarioCachedData(su.api.BaseCacheData):
    """Just a wrapper for caching scenario result data"""

    def __init__(
        self,
        ensemble: sc.gm_data.Ensemble,
        site_info: sc.site.SiteInfo,
        ensemble_scenario: sc.scenario.EnsembleScenarioResult,
        branches_scenario: List[sc.scenario.BranchScenarioResult],
    ):
        super().__init__(ensemble, site_info)
        self.ensemble_hazard = ensemble_scenario
        self.branches_hazard = branches_scenario

    def __iter__(self):
        return iter(
            (
                self.ensemble,
                self.site_info,
                self.ensemble_hazard,
                self.branches_hazard,
            )
        )


@server.app.route(const.ENSEMBLE_SCENARIO_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_ensemble_scenario():
    """Retrieves the scenario for the ensemble, all its
     branches for the specified station (name)

    Valid request have to contain the following
    URL parameters: ensemble_id, station
    Optional parameters: im_component, vs30
    """
    server.app.logger.info(f"Received request at {const.ENSEMBLE_SCENARIO_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (ensemble_id, station), optional_kwargs = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station"),
        (
            ("im_component", sc.im.IMComponent, sc.im.IMComponent.RotD50),
            ("vs30", float),
        ),
    )

    im_component = optional_kwargs.get("im_component")
    user_vs30 = optional_kwargs.get("vs30")

    server.app.logger.debug(f"Request parameters {ensemble_id}, {station}")

    # Get the scenario data (either compute or from cache)
    ensemble, site_info, ensemble_scenario = _get_scenario(
        ensemble_id,
        station,
        cache,
        user_vs30=user_vs30,
        im_component=im_component,
    )

    return flask.jsonify(
        su.api.get_ensemble_scenario_response(
            # Filters the ruptures to the top 20 based on geometric mean
            sc.scenario.filter_ruptures(ensemble_scenario),
            su.api.get_download_token(
                {
                    "type": "ensemble_scenario",
                    "ensemble_id": ensemble_id,
                    "station": station,
                    "user_vs30": site_info.user_vs30,
                    "im_component": str(im_component),
                },
                server.DOWNLOAD_URL_SECRET_KEY,
                server.DOWNLOAD_URL_VALID_FOR,
            ),
        )
    )


@server.app.route(const.ENSEMBLE_SCENARIO_DOWNLOAD_ENDPOINT, methods=["GET"])
@su.api.endpoint_exception_handling(server.app)
def download_ensemble_scenario():
    """Handles downloading of the Scenario data

    The data is computed, saved in a temporary dictionary, zipped and
    then returned to the user
    """
    server.app.logger.info(
        f"Received request at {const.ENSEMBLE_SCENARIO_DOWNLOAD_ENDPOINT}"
    )
    cache = flask.current_app.extensions["cache"]

    (scenario_token,), _ = su.api.get_check_keys(
        flask.request.args, ("scenario_token",), ()
    )

    scenario_payload = su.api.get_token_payload(
        scenario_token, server.DOWNLOAD_URL_SECRET_KEY
    )
    ensemble_id, station, user_vs30, im_component = (
        scenario_payload["ensemble_id"],
        scenario_payload["station"],
        scenario_payload["user_vs30"],
        sc.im.IMComponent[scenario_payload["im_component"]],
    )

    # Get the scenario data (either compute or from cache)
    ensemble, site_info, ensemble_scenario = _get_scenario(
        ensemble_id,
        station,
        cache,
        user_vs30=user_vs30,
        im_component=im_component,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = su.api.create_scenario_download_zip(
            ensemble_scenario,
            tmp_dir,
            prefix=f"{ensemble.name}",
        )

        return flask.send_file(
            zip_ffp,
            as_attachment=True,
            attachment_filename=f"{ensemble.name}_{ensemble_scenario.site_info.station_name}_scenario.zip",
        )


def _get_scenario(
    ensemble_id: str,
    station: str,
    cache: BaseCache,
    user_vs30: float = None,
    im_component: sc.im.IMComponent = sc.im.IMComponent.RotD50,
) -> Tuple[sc.gm_data.Ensemble, sc.site.SiteInfo, sc.scenario.EnsembleScenarioResult,]:
    git_version = su.api.get_repo_version()

    # Get the cached result, if there is one
    cache_key = su.api.get_cache_key(
        "scenario",
        ensemble_id=ensemble_id,
        station=station,
        vs30=str(user_vs30),
        im_component=str(im_component),
    )
    cached_data = cache.get(cache_key)

    if cached_data is None:
        server.app.logger.debug(f"No cached result for {cache_key}, computing scenario")

        server.app.logger.debug(f"Loading ensemble and retrieving site information")
        ensemble = sc.gm_data.Ensemble(ensemble_id)
        site_info = sc.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

        server.app.logger.debug(f"Computing scenario - version {git_version}")
        ensemble_scenario = sc.scenario.run_ensemble_scenario(
            ensemble, site_info, im_component=im_component
        )

        # Save the result
        cache.set(
            cache_key,
            ScenarioCachedData(
                ensemble,
                site_info,
                ensemble_scenario,
                ensemble_scenario.branch_scenarios,
            ),
        )
    else:
        server.app.logger.debug(f"Using cached result with key {cache_key}")
        (
            ensemble,
            site_info,
            ensemble_scenario,
            branches_scenario,
        ) = cached_data

    return ensemble, site_info, ensemble_scenario
