import flask
import pandas as pd
from flask_cors import cross_origin

import gmhazard_calc as sc
import seistech_utils as su
from core_api import server
from core_api import constants as const


@server.app.route(const.SITE_SOURCE_DISTANCES_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_distance_df():
    """Gets the distances for the specified station

    Valid request has to contain the following
    URL parameters: ensemble_id, station
    """
    server.app.logger.info(
        f"Received request at {const.SITE_SOURCE_DISTANCES_ENDPOINT}"
    )

    (ensemble_id, station), *_ = su.api.get_check_keys(
        flask.request.args, ("ensemble_id", "station")
    )

    server.app.logger.debug(f"Request parameters {ensemble_id}, {station}")

    server.app.logger.debug(f"Loading ensemble and site source distance information")
    ensemble = sc.gm_data.Ensemble(ensemble_id)
    site_info = sc.site.get_site_from_name(ensemble, station)

    flt_df = sc.site_source.get_distance_df(ensemble.flt_ssddb_ffp, site_info)
    ds_df = sc.site_source.get_distance_df(ensemble.ds_ssddb_ffp, site_info)

    dist_df = pd.concat([flt_df, ds_df])

    return flask.jsonify({"distances": dist_df.to_json()})
