import os
import base64
import tempfile
from pathlib import Path

import flask
from flask_cors import cross_origin

import gmhazard_calc as sc
import seistech_utils as su
from core_api import server
from core_api import constants as const


VS30_GRID_FFP = os.getenv("VS30_GRID_FFP")


@server.app.route(const.SITE_LOCATION_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_station_from_loc():
    """Gets the closest station for the specified lat/lon

    Valid request has to contain the following
    URL parameters: ensemble_id, lat, lon
    """
    server.app.logger.info(f"Received request at {const.SITE_LOCATION_ENDPOINT}")

    (ensemble_id, lat, lon), _ = su.api.get_check_keys(
        flask.request.args, ("ensemble_id", "lat", "lon")
    )

    server.app.logger.debug(f"Request parameters {ensemble_id}, {lat}, {lon}")

    server.app.logger.debug(f"Loading ensemble and retrieving site information")
    ensemble = sc.gm_data.Ensemble(ensemble_id)
    site, d = sc.site.get_site_from_coords(ensemble, float(lat), float(lon))

    return flask.jsonify(
        {
            "station": site.station_name,
            "lat": str(site.lat),
            "lon": str(site.lon),
            "vs30": str(site.vs30),
            "distance": str(d),
        }
    )


@server.app.route(const.SITE_NAME_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_station_from_name():
    """Gets the station details

    Valid request has to contain the following
    URL parameters: ensemble_id, station
    """

    server.app.logger.info(f"Received request at {const.SITE_NAME_ENDPOINT}")
    (ensemble_id, station), *_ = su.api.get_check_keys(
        flask.request.args, ("ensemble_id", "station")
    )
    server.app.logger.debug(f"Loading ensemble and retrieving site information")

    ensemble = sc.gm_data.Ensemble(ensemble_id)
    site = sc.site.get_site_from_name(ensemble, station)

    return flask.jsonify(
        {
            "station": site.station_name,
            "lat": str(site.lat),
            "lon": str(site.lon),
            "vs30": str(site.vs30),
        }
    )


@server.app.route(const.SITE_CONTEXT_MAP_ENDPOINT, methods=["GET"])
@cross_origin()
@su.api.endpoint_exception_handling(server.app)
def download_context_map():
    """Handles generation & downloading of the gmt context map"""
    server.app.logger.info(f"Received request at {const.SITE_CONTEXT_MAP_ENDPOINT}")

    (ensemble_id, lon, lat), optional_values_dict = su.api.get_check_keys(
        flask.request.args, (("ensemble_id", str), ("lon", float), ("lat", float))
    )

    server.app.logger.debug(
        f"Request parameters {ensemble_id}, {lon}, {lat} "
        f"optional parameters {optional_values_dict}"
    )

    with tempfile.TemporaryDirectory() as cur_dir:
        context_plot_ffp = Path(cur_dir) / "context_plot"
        sc.plots.gmt_context(lon, lat, str(context_plot_ffp))

        with (Path(f"{context_plot_ffp}.png")).open(mode="rb") as f:
            context_png_data = f.read()

        return flask.jsonify(
            {"context_plot": base64.b64encode(context_png_data).decode()}
        )


@server.app.route(const.SITE_VS30_MAP_ENDPOINT, methods=["GET"])
@cross_origin()
@su.api.endpoint_exception_handling(server.app)
def download_vs30_map():
    """Handles generation & downloading of the gmt context map"""
    server.app.logger.info(f"Received request at {const.SITE_VS30_MAP_ENDPOINT}")

    (ensemble_id, lon, lat), optional_values_dict = su.api.get_check_keys(
        flask.request.args, (("ensemble_id", str), ("lon", float), ("lat", float))
    )

    server.app.logger.debug(
        f"Request parameters {ensemble_id}, {lon}, {lat} "
        f"optional parameters {optional_values_dict}"
    )

    ensemble = sc.gm_data.Ensemble(ensemble_id)
    site_info, d = sc.site.get_site_from_coords(ensemble, lat, lon)

    with tempfile.TemporaryDirectory() as cur_dir:
        context_plot_ffp = Path(cur_dir) / "vs30_plot.png"
        sc.plots.gmt_vs30(
            str(context_plot_ffp),
            lon,
            lat,
            site_info.lon,
            site_info.lat,
            site_info.vs30,
            ensemble._config["stations"],
            VS30_GRID_FFP,
        )

        with context_plot_ffp.open(mode="rb") as f:
            vs30_png_data = f.read()

        return flask.jsonify({"vs30_plot": base64.b64encode(vs30_png_data).decode()})


@server.app.route(const.SITE_VS30_SOIL_CLASS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_soil_class_from_vs30():
    """Gets the Soil Class for NZ Codes from the Vs30
    (NZTA and NZS1170.5)

    Valid request has to contain the following
    URL parameter: vs30
    """
    server.app.logger.info(f"Received request at {const.SITE_VS30_SOIL_CLASS_ENDPOINT}")
    vs30 = su.api.get_check_keys(flask.request.args, ["vs30"])[0][0]
    server.app.logger.debug(f"Request parameters {vs30}")

    return flask.jsonify(
        {
            "nzs1170p5_soil_class": sc.nz_code.nzs1170p5.get_soil_class(
                float(vs30)
            ).value,
            "nzta_soil_class": sc.nz_code.nzta_2018.get_soil_class(float(vs30)).value,
        }
    )
