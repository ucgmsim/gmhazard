import flask
from flask_cors import cross_origin

import gmhazard_calc as sc
import gmhazard_utils as su
from core_api import server
from core_api import utils
from core_api import constants as const


@server.app.route(const.NZTA_DEFAULT_PARAMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_nzta_default_params():
    """Gets the default parameters for NZ Code NZS1170.5"""
    server.app.logger.info(f"Received request at {const.NZTA_DEFAULT_PARAMS_ENDPOINT}")

    (ensemble_id, station), optional_params_dict = su.api.get_check_keys(
        flask.request.args, ("ensemble_id", "station"), ("vs30",)
    )

    user_vs30 = optional_params_dict.get("vs30")
    ensemble = sc.gm_data.Ensemble(ensemble_id)
    site_info = sc.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

    return flask.jsonify(
        {"soil_class": sc.nz_code.nzta_2018.get_soil_class(site_info.vs30).value}
    )


@server.app.route(const.NZTA_HAZARD_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_nzta_hazard():
    """Retrieves the NZS1170p5 hazard for the station"""
    server.app.logger.info(f"Received request at {const.NZTA_HAZARD_ENDPOINT}")
    cache = server.cache

    (ensemble_id, station, soil_class), optional_kwargs = su.api.get_check_keys(
        flask.request.args,
        (("ensemble_id", str), ("station", str), ("soil_class", sc.NZTASoilClass)),
        (("im_component", sc.im.IMComponent, sc.im.IMComponent.RotD50,),),
    )

    server.app.logger.debug(
        f"Request parameters {ensemble_id}, {station}, {soil_class}"
    )
    im_component = optional_kwargs.get("im_component")

    ensemble, site_info, nzta_hazard = utils.get_nzta_result(
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
                    "im_component": str(im_component),
                },
                server.DOWNLOAD_URL_SECRET_KEY,
            ),
        }
    )


@server.app.route(const.NZTA_SOIL_CLASS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_nzta_soil_class():
    """Gets the soil classes for NZ Code NZTA"""
    server.app.logger.info(f"Received request at {const.NZTA_SOIL_CLASS_ENDPOINT}")

    soil_class = {soil.value: soil.name for soil in sc.NZTASoilClass}
    return flask.jsonify({"soil_class": soil_class})
