import tempfile
from typing import Tuple, Dict

import flask
from flask_cors import cross_origin
from werkzeug.contrib.cache import BaseCache

import seistech_calc as si
import seistech_utils as su
from ..server import app, requires_auth, DOWNLOAD_URL_SECRET_KEY, DOWNLOAD_URL_VALID_FOR
from .. import constants as const
from .nzs1170p5 import get_nzs1170p5_hazard
from .nzta import get_nzta_result


class HazardCachedData(su.api.BaseCacheData):
    """Just a wrapper for caching hazard result data"""

    def __init__(
        self,
        ensemble: si.gm_data.Ensemble,
        site_info: si.site.SiteInfo,
        ensemble_hazard: si.hazard.EnsembleHazardResult,
        branches_hazard: Dict[str, si.hazard.BranchHazardResult],
    ):
        super().__init__(ensemble, site_info)
        self.ensemble_hazard = ensemble_hazard
        self.branches_hazard = branches_hazard

    def __iter__(self):
        return iter(
            (self.ensemble, self.site_info, self.ensemble_hazard, self.branches_hazard,)
        )


@app.route(const.ENSEMBLE_HAZARD_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_ensemble_hazard():
    """Retrieves the hazard for the ensemble, all its
     branches for the specified station (name) and NZ code

    Valid request have to contain the following
    URL parameters: ensemble_id, station, im
    Optional parameters: calc_percentiles, vs30
    """
    app.logger.info(f"Received request at {const.ENSEMBLE_HAZARD_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (ensemble_id, station, im), optional_kwargs = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", ("im", si.im.IM.from_str)),
        (
            ("calc_percentiles", int),
            ("vs30", float),
            ("im_component", si.im.IMComponent, si.im.IMComponent.RotD50),
        ),
    )

    user_vs30 = optional_kwargs.get("vs30")
    calc_percentiles = optional_kwargs.get("calc_percentiles")
    calc_percentiles = False if calc_percentiles is None else bool(calc_percentiles)
    im.component = optional_kwargs.get("im_component")

    app.logger.debug(
        f"Request parameters {ensemble_id}, {station}, {im}, {calc_percentiles}"
    )

    # Get the hazard data (either compute or from cache)
    ensemble, site_info, ensemble_hazard, branches_hazard = _get_hazard(
        ensemble_id,
        station,
        im,
        cache,
        calc_percentiles=calc_percentiles,
        user_vs30=user_vs30,
    )

    result = su.api.get_ensemble_hazard_response(
        ensemble_hazard,
        su.api.get_download_token(
            {
                "type": "ensemble_hazard",
                "ensemble_id": ensemble_id,
                "station": station,
                "user_vs30": site_info.user_vs30,
                "im": str(im),
                "im_component": str(im.component),
                "calc_percentiles": calc_percentiles,
            },
            DOWNLOAD_URL_SECRET_KEY,
            DOWNLOAD_URL_VALID_FOR,
        ),
    )

    # Adding percentiles based on flag
    if calc_percentiles:
        percentiles = {
            key: {im_value: exceedance for im_value, exceedance in value.iteritems()}
            for key, value in ensemble_hazard.percentiles.items()
        }
        result = {**result, "percentiles": percentiles}

    return flask.jsonify(result)


@app.route(const.ENSEMBLE_HAZARD_DOWNLOAD_ENDPOINT, methods=["GET"])
@su.api.endpoint_exception_handling(app)
def download_ens_hazard():
    """Handles downloading of the hazard data

    The data is computed, saved in a temporary dictionary, zipped and
    then returned to the user
    """
    app.logger.info(f"Received request at {const.ENSEMBLE_HAZARD_DOWNLOAD_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (hazard_token, nzs1170p5_token), optional_kwargs = su.api.get_check_keys(
        flask.request.args,
        ("hazard_token", "nzs1170p5_hazard_token"),
        ("nzta_hazard_token",),
    )
    nzta_hazard_token = optional_kwargs.get("nzta_hazard_token")

    hazard_payload = su.api.get_token_payload(hazard_token, DOWNLOAD_URL_SECRET_KEY)
    ensemble_id, station, user_vs30, im, calc_percentiles = (
        hazard_payload["ensemble_id"],
        hazard_payload["station"],
        hazard_payload["user_vs30"],
        si.im.IM.from_str(hazard_payload["im"]),
        hazard_payload["calc_percentiles"],
    )

    nzs1170p5_payload = su.api.get_token_payload(
        nzs1170p5_token, DOWNLOAD_URL_SECRET_KEY
    )
    assert (
        ensemble_id == nzs1170p5_payload["ensemble_id"]
        and station == nzs1170p5_payload["station"]
        and im == si.im.IM.from_str(nzs1170p5_payload["im"])
    )

    if nzta_hazard_token is not None:
        nzta_payload = su.api.get_token_payload(
            nzta_hazard_token, DOWNLOAD_URL_SECRET_KEY
        )
        assert nzta_payload is None or (
            ensemble_id == nzta_payload["ensemble_id"],
            station == nzta_payload["station"],
        )

    # Get the hazard data (either compute or from cache)
    ensemble, site_info, ensemble_hazard, branches_hazard = _get_hazard(
        ensemble_id,
        station,
        im,
        cache,
        calc_percentiles=calc_percentiles,
        user_vs30=user_vs30,
    )

    # Get the NZS1170p5 hazard data from the cache
    opt_args = {
        cur_key: cur_type(nzs1170p5_payload[cur_key])
        for cur_key, cur_type in const.NZ_CODE_OPT_ARGS
        if cur_key in nzs1170p5_payload.keys()
    }
    _, __, nzs1170p5_hazard = get_nzs1170p5_hazard(
        ensemble_id, station, im, opt_args, cache, user_vs30=user_vs30
    )

    # Get the NZTA hazard data from the cache
    nzta_hazard = None
    if nzta_hazard_token is not None:
        _, __, nzta_hazard = get_nzta_result(
            ensemble_id,
            station,
            si.NZTASoilClass(nzta_payload["soil_class"]),
            cache,
            user_vs30=user_vs30,
            im_component=im.component,
        )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = su.api.create_hazard_download_zip(
            ensemble_hazard,
            nzs1170p5_hazard,
            tmp_dir,
            nzta_hazard=nzta_hazard,
            prefix=f"{ensemble.name}",
        )

        return flask.send_file(
            zip_ffp,
            as_attachment=True,
            attachment_filename=f"{ensemble.name}_{ensemble_hazard.site.station_name}_hazard.zip",
        )


def _get_hazard(
    ensemble_id: str,
    station: str,
    im: si.im.IM,
    cache: BaseCache,
    calc_percentiles: bool = False,
    user_vs30: float = None,
) -> Tuple[
    si.gm_data.Ensemble,
    si.site.SiteInfo,
    si.hazard.EnsembleHazardResult,
    Dict[str, si.hazard.BranchHazardResult],
]:
    git_version = su.api.get_repo_version()

    # Get the cached result, if there is one
    cache_key = su.api.get_cache_key(
        "hazard",
        ensemble_id=ensemble_id,
        station=station,
        vs30=str(user_vs30),
        im=str(im),
        im_component=str(im.component),
        calc_percentiles=str(calc_percentiles),
    )
    cached_data = cache.get(cache_key)

    if cached_data is None:
        app.logger.debug(f"No cached result for {cache_key}, computing hazard")

        app.logger.debug(f"Loading ensemble and retrieving site information")
        ensemble = si.gm_data.Ensemble(ensemble_id)
        site_info = si.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

        app.logger.debug(f"Computing hazard - version {git_version}")
        ensemble_hazard, branches_hazard = si.hazard.run_full_hazard(
            ensemble, site_info, im, calc_percentiles=calc_percentiles
        )

        # Save the result
        cache.set(
            cache_key,
            HazardCachedData(ensemble, site_info, ensemble_hazard, branches_hazard),
        )
    else:
        app.logger.debug(f"Using cached result with key {cache_key}")
        (ensemble, site_info, ensemble_hazard, branches_hazard,) = cached_data

    return ensemble, site_info, ensemble_hazard, branches_hazard
