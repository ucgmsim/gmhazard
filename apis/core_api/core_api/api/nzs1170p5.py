from typing import Dict, Sequence

import flask
import numpy as np
from flask_cors import cross_origin
from werkzeug.contrib.cache import BaseCache

import gmhazard_calc as sc
import seistech_utils as su
from core_api import server
from core_api import constants as const
from core_api import utils


@server.app.route(const.NZS1170p5_DEFAULT_PARAMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_nzs1170p5_default_params():
    """Gets the default parameters for NZ Code NZS1170.5"""
    server.app.logger.info(
        f"Received request at {const.NZS1170p5_DEFAULT_PARAMS_ENDPOINT}"
    )

    (ensemble_id, station), optional_params_dict = su.api.get_check_keys(
        flask.request.args, ("ensemble_id", "station"), ("vs30",)
    )
    user_vs30 = optional_params_dict.get("vs30")

    ensemble = sc.gm_data.Ensemble(ensemble_id)
    site_info = sc.site.get_site_from_name(ensemble_id, station, user_vs30=user_vs30)

    soil_class = sc.nz_code.nzs1170p5.get_soil_class(site_info.vs30).value
    distance = sc.nz_code.nzs1170p5.get_distance_from_site_info(ensemble, site_info)
    z_factor = float(
        sc.nz_code.nzs1170p5.ll2z(
            (site_info.lon, site_info.lat),
            radius_search=sc.nz_code.nzs1170p5.CITY_RADIUS_SEARCH,
        )
    )

    return flask.jsonify(
        {"soil_class": soil_class, "distance": distance, "z_factor": z_factor}
    )


@server.app.route(const.NZS1170p5_HAZARD_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_nzs1170p5_hazard():
    """Retrieves the NZS1170p5 hazard for the station"""
    server.app.logger.info(f"Received request at {const.NZS1170p5_HAZARD_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (ensemble_id, station, im), optional_values_dict = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", "im"),
        (
            ("soil_class", sc.NZSSoilClass),
            ("distance", float),
            ("z_factor", float),
            ("z_factor_radius", float),
            ("im_component", str, "RotD50"),
        ),
    )
    im = sc.im.IM.from_str(im, im_component=optional_values_dict.get("im_component"))

    optional_values_dict = {
        key: value for key, value in optional_values_dict.items() if value is not None
    }

    server.app.logger.debug(
        f"Request parameters {ensemble_id}, {station}, {im} and "
        f"optional parameters {optional_values_dict}"
    )

    ensemble, site_info, nzs1170p5_hazard = utils.get_nzs1170p5_hazard(
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
                server.DOWNLOAD_URL_SECRET_KEY,
                server.DOWNLOAD_URL_VALID_FOR,
            ),
        }
    )


@server.app.route(const.NZS1170p5_UHS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_nzs1170p5_uhs():
    server.app.logger.info(f"Received request at {const.NZS1170p5_UHS_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (ensemble_id, station, exceedances), optional_kwargs = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", "exceedances"),
        (
            ("soil_class", sc.NZSSoilClass),
            ("distance", float),
            ("z_factor", float),
            ("z_factor_radius", float),
            ("im_component", sc.im.IMComponent, sc.im.IMComponent.RotD50),
        ),
    )
    optional_args = {
        key: value for key, value in optional_kwargs.items() if value is not None
    }
    server.app.logger.debug(
        f"Request parameters {ensemble_id}, {station}, {exceedances} and"
        f"optional parameters {optional_args}"
    )

    ensemble, site_info, nzs1170p5_uhs = utils.get_nzs1170p5_uhs(
        ensemble_id, station, exceedances, optional_args, cache
    )

    return flask.jsonify(
        {
            "ensemble_id": ensemble.name,
            "station": site_info.station_name,
            "nzs1170p5_results": [
                result.to_dict(nan_to_string=True) for result in nzs1170p5_uhs
            ],
            "nzs1170p5_uhs_df": sc.nz_code.nzs1170p5.NZS1170p5Result.combine_results(
                nzs1170p5_uhs
            )
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
                server.DOWNLOAD_URL_SECRET_KEY,
                server.DOWNLOAD_URL_VALID_FOR,
            ),
        }
    )


@server.app.route(const.NZS1170p5_SOIL_CLASS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_nzs1170p5_soil_class():
    """Gets the soil classes for NZ Code NZS1170p5"""
    server.app.logger.info(f"Received request at {const.NZS1170p5_SOIL_CLASS_ENDPOINT}")

    soil_class = {soil.value: soil.name for soil in sc.NZSSoilClass}
    return flask.jsonify({"soil_class": soil_class})
