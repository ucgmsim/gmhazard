import tempfile
from typing import List, Tuple

import flask
import numpy as np
from werkzeug.contrib.cache import BaseCache
from flask_cors import cross_origin

import seistech_calc as sc
import seistech_utils as su
from core_api import server
from core_api import utils
from core_api import constants as const


class UHSCachedData:
    def __init__(
        self,
        ensemble: sc.gm_data.Ensemble,
        site_info: sc.site.SiteInfo,
        uhs_results: List[sc.uhs.UHSResult],
    ):
        self.ensemble = ensemble
        self.site_info = site_info
        self.uhs_results = uhs_results

    def __iter__(self):
        return iter((self.ensemble, self.site_info, self.uhs_results))


@server.app.route(const.ENSEMBLE_UHS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_ensemble_uhs():
    """Retrieves the ensemble UHS for the
    specified station (name)

    Valid request have to contain the following URL parameters:
    ensemble_id, station, exceedances (as a comma separated string)
    Optional parameters: calc_percentiles
    """
    server.app.logger.info(f"Received request at {const.ENSEMBLE_UHS_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (ensemble_id, station, exceedances), optional_kwargs = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", "exceedances"),
        (
            ("calc_percentiles", int),
            ("vs30", float),
            ("im_component", sc.im.IMComponent, sc.im.IMComponent.RotD50),
        ),
    )

    server.app.logger.debug(
        f"Request parameters {ensemble_id}, {station}, {exceedances}"
    )

    calc_percentiles = optional_kwargs.get("calc_percentiles")
    calc_percentiles = False if calc_percentiles is None else bool(calc_percentiles)
    user_vs30 = optional_kwargs.get("vs30")
    im_component = optional_kwargs.get("im_component")

    ensemble, site_info, uhs_results = _get_uhs(
        ensemble_id,
        station,
        exceedances,
        cache,
        user_vs30=user_vs30,
        calc_percentiles=calc_percentiles,
        im_component=im_component,
    )

    return flask.jsonify(
        su.api.get_ensemble_uhs(
            uhs_results,
            su.api.get_download_token(
                {
                    "type": "ensemble_uhs",
                    "ensemble_id": ensemble_id,
                    "station": station,
                    "user_vs30": user_vs30,
                    "exceedances": exceedances,
                    "calc_percentiles": calc_percentiles,
                    "im_component": str(im_component),
                },
                server.DOWNLOAD_URL_SECRET_KEY,
                server.DOWNLOAD_URL_VALID_FOR,
            ),
        )
    )


@server.app.route(const.ENSEMBLE_UHS_DOWNLOAD_ENDPOINT, methods=["GET"])
@su.api.endpoint_exception_handling(server.app)
def download_ensemble_uhs():
    """
    Handles downloading of the UHS raw data

    Computes UHS & NZ code UHS, saves in a temp dir, zips the files
    and returns them to the user
    """
    server.app.logger.info(
        f"Received request at {const.ENSEMBLE_UHS_DOWNLOAD_ENDPOINT}"
    )
    cache = flask.current_app.extensions["cache"]

    (uhs_token, nzs1170p5_token), _ = su.api.get_check_keys(
        flask.request.args, ("uhs_token", "nzs1170p5_hazard_token")
    )
    uhs_payload = su.api.utils.get_token_payload(
        uhs_token, server.DOWNLOAD_URL_SECRET_KEY
    )
    ensemble_id, station, user_vs30, exceedances_str, calc_percentiles, im_component = (
        uhs_payload["ensemble_id"],
        uhs_payload["station"],
        uhs_payload["user_vs30"],
        uhs_payload["exceedances"],
        uhs_payload["calc_percentiles"],
        sc.im.IMComponent(uhs_payload["im_component"]),
    )

    nzs1170p5_payload = su.api.utils.get_token_payload(
        nzs1170p5_token, server.DOWNLOAD_URL_SECRET_KEY
    )
    assert (
        ensemble_id == nzs1170p5_payload["ensemble_id"]
        and station == nzs1170p5_payload["station"]
        and exceedances_str == nzs1170p5_payload["exceedances"]
    )

    # Get the UHS data (either compute or from cache)
    ensemble, site_info, uhs_results = _get_uhs(
        ensemble_id,
        station,
        exceedances_str,
        cache,
        calc_percentiles=calc_percentiles,
        user_vs30=user_vs30,
        im_component=im_component,
    )

    # Get the NZS1170p5 UHS data from the cache
    opt_args = {
        cur_key: cur_type(nzs1170p5_payload[cur_key])
        for cur_key, cur_type in const.NZ_CODE_OPT_ARGS
        if cur_key in nzs1170p5_payload.keys()
    }
    _, __, nzs1170p5_uhs = utils.get_nzs1170p5_uhs(
        ensemble_id, station, exceedances_str, opt_args, cache, user_vs30=user_vs30
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = su.api.create_uhs_download_zip(
            uhs_results, nzs1170p5_uhs, tmp_dir, prefix=f"{ensemble.name}"
        )

        return flask.send_file(
            zip_ffp,
            as_attachment=True,
            attachment_filename=f"{ensemble.name}_{site_info.station_name}_UHS.zip",
        )


def _get_uhs(
    ensemble_id: str,
    station: str,
    exceedances: str,
    cache: BaseCache,
    calc_percentiles: bool = False,
    user_vs30: float = None,
    im_component: sc.im.IMComponent = sc.im.IMComponent.RotD50,
) -> Tuple[sc.gm_data.Ensemble, sc.site.SiteInfo, List[sc.uhs.EnsembleUHSResult],]:
    git_version = su.api.get_repo_version()
    exceedances = np.asarray(list(map(float, exceedances.split(","))))

    # Get the cached result, if there is one
    cache_key = su.api.get_cache_key(
        "uhs",
        ensemble_id=ensemble_id,
        station=station,
        user_vs30=str(user_vs30),
        **{
            f"exceedance_{ix}": str(exceedance)
            for ix, exceedance in enumerate(exceedances)
        },
        calc_percentiles=str(calc_percentiles),
        im_component=str(im_component),
    )
    cached_data = cache.get(cache_key)

    if cached_data is None:
        server.app.logger.debug(f"No cached result for {cache_key}, computing UHS")

        server.app.logger.debug(f"Loading ensemble and retrieving site information")
        ensemble = sc.gm_data.Ensemble(ensemble_id)
        site_info = sc.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

        server.app.logger.debug(f"Computing UHS - version {git_version}")

        uhs_results = sc.uhs.run_ensemble_uhs(
            ensemble,
            site_info,
            np.asarray(exceedances),
            n_procs=2,
            calc_percentiles=calc_percentiles,
            im_component=im_component,
        )

        cache.set(cache_key, UHSCachedData(ensemble, site_info, uhs_results))
    else:
        server.app.logger.debug(f"Using cached result with key {cache_key}")
        ensemble, site_info, uhs_results = cached_data

    return ensemble, site_info, uhs_results
