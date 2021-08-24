from typing import Dict, Sequence

import flask
import numpy as np
from flask_cors import cross_origin
from werkzeug.contrib.cache import BaseCache

import seistech_calc as si
import seistech_calc.nz_code.nzs1170p5 as nzs1170p5
import seistech_utils as su
from ..server import app, requires_auth, DOWNLOAD_URL_SECRET_KEY, DOWNLOAD_URL_VALID_FOR
from .. import constants as const


class NZS1170p5CachedHazardData(su.api.BaseCacheData):
    """Just a wrapper used for caching NZS1170p5 hazard result data"""

    def __init__(
        self,
        ensemble: si.gm_data.Ensemble,
        site_info: si.site.SiteInfo,
        nzs1170p5_hazard: nzs1170p5.NZS1170p5Result,
    ):
        super().__init__(ensemble, site_info)
        self.nzs1170p5_hazard = nzs1170p5_hazard

    def __iter__(self):
        return iter((self.ensemble, self.site_info, self.nzs1170p5_hazard))


class NZS1170p5CachedUHSData(su.api.BaseCacheData):
    def __init__(
        self,
        ensemble: si.gm_data.Ensemble,
        site_info: si.site.SiteInfo,
        nzs1170p5_uhs: Sequence[nzs1170p5.NZS1170p5Result],
    ):
        super().__init__(ensemble, site_info)
        self.nzs1170p5_uhs = nzs1170p5_uhs

    def __iter__(self):
        return iter((self.ensemble, self.site_info, self.nzs1170p5_uhs))


@app.route(const.NZS1170p5_DEFAULT_PARAMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_nzs1170p5_default_params():
    """Gets the default parameters for NZ Code NZS1170.5"""
    app.logger.info(f"Received request at {const.NZS1170p5_DEFAULT_PARAMS_ENDPOINT}")

    (ensemble_id, station), optional_params_dict = su.api.get_check_keys(
        flask.request.args, ("ensemble_id", "station"), ("vs30",)
    )
    user_vs30 = optional_params_dict.get("vs30")

    ensemble = si.gm_data.Ensemble(ensemble_id)
    site_info = si.site.get_site_from_name(ensemble_id, station, user_vs30=user_vs30)

    soil_class = nzs1170p5.get_soil_class(site_info.vs30).value
    distance = nzs1170p5.get_distance_from_site_info(ensemble, site_info)
    z_factor = float(
        nzs1170p5.ll2z(
            (site_info.lon, site_info.lat), radius_search=nzs1170p5.CITY_RADIUS_SEARCH
        )
    )

    return flask.jsonify(
        {"soil_class": soil_class, "distance": distance, "z_factor": z_factor}
    )


@app.route(const.NZS1170p5_HAZARD_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_nzs1170p5_hazard():
    """Retrieves the NZS1170p5 hazard for the station"""
    app.logger.info(f"Received request at {const.NZS1170p5_HAZARD_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (ensemble_id, station, im), optional_values_dict = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", ("im", si.im.IM.from_str)),
        (
            ("soil_class", si.NZSSoilClass),
            ("distance", float),
            ("z_factor", float),
            ("z_factor_radius", float),
            ("im_component", si.im.IMComponent, si.im.IMComponent.RotD50),
        ),
    )
    optional_values_dict = {
        key: value for key, value in optional_values_dict.items() if value is not None
    }
    app.logger.debug(
        f"Request parameters {ensemble_id}, {station}, {im} and "
        f"optional parameters {optional_values_dict}"
    )
    im.component = optional_values_dict.get("im_component")

    ensemble, site_info, nzs1170p5_hazard = get_nzs1170p5_hazard(
        ensemble_id, station, im, optional_values_dict, cache
    )
    return flask.jsonify(
        {
            "nzs1170p5_hazard": nzs1170p5_hazard.to_dict(),
            "download_token": su.api.get_download_token(
                {
                    "type": "nzs1170p5",
                    "ensemble_id": ensemble_id,
                    "station": station,
                    "im": str(im),
                    **{key: str(value) for key, value in optional_values_dict.items()},
                },
                DOWNLOAD_URL_SECRET_KEY,
                DOWNLOAD_URL_VALID_FOR,
            ),
        }
    )


@app.route(const.NZS1170p5_UHS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_nzs1170p5_uhs():
    app.logger.info(f"Received request at {const.NZS1170p5_UHS_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (ensemble_id, station, exceedances), optional_args = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", "exceedances"),
        (
            ("soil_class", si.NZSSoilClass),
            ("distance", float),
            ("z_factor", float),
            ("z_factor_radius", float),
            ("im_component", str),
        ),
    )
    optional_args = {
        key: value for key, value in optional_args.items() if value is not None
    }
    app.logger.debug(f"Request parameters {ensemble_id}, {station}, {exceedances}")

    ensemble, site_info, nzs1170p5_uhs = _get_nzs1170p5_uhs(
        ensemble_id, station, exceedances, optional_args, cache
    )

    return flask.jsonify(
        {
            "ensemble_id": ensemble.name,
            "station": site_info.station_name,
            "nzs1170p5_results": [
                result.to_dict(nan_to_string=True) for result in nzs1170p5_uhs
            ],
            "nzs1170p5_uhs_df": nzs1170p5.NZS1170p5Result.combine_results(nzs1170p5_uhs)
            .replace(np.nan, "nan")
            .to_dict(),
            "download_token": su.api.get_download_token(
                {
                    "type": "nzs1170p5",
                    "ensemble_id": ensemble_id,
                    "station": station,
                    "exceedances": exceedances,
                    **{key: str(value) for key, value in optional_args.items()},
                },
                DOWNLOAD_URL_SECRET_KEY,
                DOWNLOAD_URL_VALID_FOR,
            ),
        }
    )


@app.route(const.NZS1170p5_SOIL_CLASS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_nzs1170p5_soil_class():
    """Gets the soil classes for NZ Code NZS1170p5"""
    app.logger.info(f"Received request at {const.NZS1170p5_SOIL_CLASS_ENDPOINT}")

    soil_class = {soil.value: soil.name for soil in si.NZSSoilClass}
    return flask.jsonify({"soil_class": soil_class})


def get_nzs1170p5_hazard(
    ensemble_id: str,
    station: str,
    im: si.im.IM,
    optional_params: Dict,
    cache,
    user_vs30: float = None,
):
    # Get the cached result, if there is one
    cache_key = su.api.get_cache_key(
        "nzs1170p5_hazard",
        ensemble_id=ensemble_id,
        station=station,
        im=str(im),
        **{cur_key: str(cur_val) for cur_key, cur_val in optional_params.items()},
    )
    cached_data = cache.get(cache_key)

    if cached_data is None:
        app.logger.debug(
            f"Computing NZS1170p5 - Hazard - version {su.api.get_repo_version()}"
        )
        ensemble = si.gm_data.Ensemble(ensemble_id)
        site_info = si.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)
        nzs1170p5_hazard = nzs1170p5.run_ensemble_nzs1170p5(
            ensemble,
            site_info,
            im,
            soil_class=optional_params.get("soil_class"),
            distance=optional_params.get("distance"),
            z_factor=optional_params.get("z_factor"),
            z_factor_radius=optional_params.get("z_factor_radius")
            if "z_factor_radius" in optional_params.keys()
            else nzs1170p5.CITY_RADIUS_SEARCH,
        )

        cache.set(
            cache_key, NZS1170p5CachedHazardData(ensemble, site_info, nzs1170p5_hazard)
        )
    else:
        app.logger.debug(f"Using cached result with key {cache_key}")
        ensemble, site_info, nzs1170p5_hazard = cached_data

    return ensemble, site_info, nzs1170p5_hazard


def _get_nzs1170p5_uhs(
    ensemble_id: str,
    station: str,
    exceedances: str,
    optional_args: Dict,
    cache: BaseCache,
    user_vs30: float = None,
):
    exceedances = np.asarray(list(map(float, exceedances.split(","))))

    # Get the cached result, if there is one
    cache_key = su.api.get_cache_key(
        "nzs1170p5_uhs",
        ensemble_id=ensemble_id,
        station=station,
        **{
            f"exceedance_{ix}": str(exceedance)
            for ix, exceedance in enumerate(exceedances)
        },
        **{cur_key: str(cur_val) for cur_key, cur_val in optional_args.items()},
    )
    cached_data = cache.get(cache_key)

    if cached_data is None:
        app.logger.debug(
            f"No cached result for {cache_key}, computing NZS1170p5 - UHS - version {su.api.get_repo_version()}"
        )

        ensemble = si.gm_data.Ensemble(ensemble_id)
        site_info = si.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

        nzs1170p5_results = si.uhs.run_nzs1170p5_uhs(
            ensemble, site_info, exceedances, opt_nzs1170p5_args=optional_args
        )

        cache.set(
            cache_key, NZS1170p5CachedUHSData(ensemble, site_info, nzs1170p5_results)
        )
    else:
        app.logger.debug(f"Using cached result with key {cache_key}")
        ensemble, site_info, nzs1170p5_results = cached_data

    return ensemble, site_info, nzs1170p5_results
