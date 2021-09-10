import flask
from flask_cors import cross_origin

import seistech_calc as sc
import seistech_utils as su
from core_api import server
from core_api import constants as const


@server.app.route(const.RUPTURES_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_rupture_df():
    """Gets the ruptures for the specified ensemble id

    Valid request has to contain the following
    URL parameters: ensemble_id
    """
    server.app.logger.info(f"Received request at {const.RUPTURES_ENDPOINT}")

    (ensemble_id,), *_ = su.api.get_check_keys(flask.request.args, ("ensemble_id",))

    server.app.logger.debug(f"Request parameters {ensemble_id}")

    server.app.logger.debug(f"Loading ensemble and rupture information")
    ensemble = sc.gm_data.Ensemble(ensemble_id)

    return flask.jsonify({"ruptures": ensemble.rupture_df_id.to_json()})
