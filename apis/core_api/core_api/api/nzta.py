import flask
from flask_cors import cross_origin
from werkzeug.contrib.cache import BaseCache

import seistech_calc as si
import seistech_calc.nz_code.nzta_2018 as nzta
import seistech_utils as su
from ..server import app, requires_auth, DOWNLOAD_URL_SECRET_KEY, DOWNLOAD_URL_VALID_FOR
from .. import constants as const


class NZTACachedData(su.api.BaseCacheData):
    """Wrapper for caching NZTA hazard data"""

    def __init__(
        self,
        ensemble: si.gm_data.Ensemble,
        site_info: si.site.SiteInfo,
        nzta_hazard: nzta.NZTAResult,
    ):
        super().__init__(ensemble, site_info)
        self.nzta_hazard = nzta_hazard

    def __iter__(self):
        return iter((self.ensemble, self.site_info, self.nzta_hazard))


@app.route(const.NZTA_DEFAULT_PARAMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_nzta_default_params():
    """Gets the default parameters for NZ Code NZS1170.5"""
    app.logger.info(f"Received request at {const.NZTA_DEFAULT_PARAMS_ENDPOINT}")

    (ensemble_id, station), optional_params_dict = su.api.get_check_keys(
        flask.request.args, ("ensemble_id", "station"), ("vs30",)
    )

    user_vs30 = optional_params_dict.get("vs30")
    ensemble = si.gm_data.Ensemble(ensemble_id)
    site_info = si.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

    return flask.jsonify({"soil_class": nzta.get_soil_class(site_info.vs30).value})


@app.route(const.NZTA_HAZARD_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_nzta_hazard():
    """Retrieves the NZS1170p5 hazard for the station"""
    app.logger.info(f"Received request at {const.NZTA_HAZARD_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (ensemble_id, station, soil_class), optional_kwargs = su.api.get_check_keys(
        flask.request.args,
        (("ensemble_id", str), ("station", str), ("soil_class", si.NZTASoilClass)),
        (("im_component", si.im.IMComponent, si.im.IMComponent.Larger,),)
    )

    app.logger.debug(f"Request parameters {ensemble_id}, {station}, {soil_class}")
    im_component = optional_kwargs.get("im_component")

    ensemble, site_info, nzta_hazard = get_nzta_result(
        ensemble_id, station, soil_class, cache, im_component=im_component
    )
    return flask.jsonify(
        {
            "nzta_hazard": nzta_hazard.to_dict(nan_to_string=True),
            "download_token": su.api.get_download_token(
                {
                    "type": "nzta_hazard",
                    "ensemble_id": ensemble_id,
                    "station": station,
                    "soil_class": soil_class.value,
                    "im_component": str(im_component)
                },
                DOWNLOAD_URL_SECRET_KEY,
                DOWNLOAD_URL_VALID_FOR,
            ),
        }
    )


@app.route(const.NZTA_SOIL_CLASS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_nzta_soil_class():
    """Gets the soil classes for NZ Code NZTA"""
    app.logger.info(f"Received request at {const.NZTA_SOIL_CLASS_ENDPOINT}")

    soil_class = {soil.value: soil.name for soil in si.NZTASoilClass}
    return flask.jsonify({"soil_class": soil_class})


def get_nzta_result(
    ensemble_id: str,
    station: str,
    soil_class: si.NZTASoilClass,
    cache: BaseCache,
    user_vs30: float = None,
    im_component: si.im.IMComponent = si.im.IMComponent.RotD50
):
    # Get the cached result, if there is one
    cache_key = su.api.get_cache_key(
        "nzta_hazard",
        ensemble_id=ensemble_id,
        station=station,
        soil_class=soil_class.value,
        im_component=str(im_component),
    )
    cached_data = cache.get(cache_key)

    if cached_data is None:
        app.logger.debug(
            f"Computing NZTA - Hazard - version {su.api.get_repo_version()}"
        )
        ensemble = si.gm_data.Ensemble(ensemble_id)
        site_info = si.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

        nzta_hazard = nzta.run_ensemble_nzta(ensemble, site_info, soil_class=soil_class, im_component=im_component)

        cache.set(cache_key, NZTACachedData(ensemble, site_info, nzta_hazard))
    else:
        app.logger.debug(f"Using cached result with key {cache_key}")
        ensemble, site_info, nzta_hazard = cached_data

    return ensemble, site_info, nzta_hazard
