import flask
from flask_cors import cross_origin

import gmhazard_calc as sc
import seistech_utils as su
from ..server import app, requires_auth
from .. import constants as const


@app.route(const.ENSEMBLE_IDS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_ensemble_ids():
    """Gets the available ensemble ids"""
    app.logger.info(f"Received request at {const.ENSEMBLE_IDS_ENDPOINT}")

    app.logger.debug(f"Retrieving available ensemble ids")
    ensemble_dict = sc.gm_data.ensemble_dict

    return flask.jsonify({"ensemble_ids": list(ensemble_dict.keys())})


@app.route(const.ENSEMBLE_IMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_ensemble_ims():
    """Gets the available IMs supported by the specified ensemble

    Valid request has to contain the following
    URL parameters: ensemble_id
    """
    app.logger.info(f"Received request at {const.ENSEMBLE_IMS_ENDPOINT}")

    ensemble_id, *_ = su.api.get_check_keys(flask.request.args, ("ensemble_id",))
    ensemble_id = ensemble_id[0]

    app.logger.debug(f"Request parameters {ensemble_id}")

    app.logger.debug(f"Loading ensemble and retrieving available IMs")
    ensemble = sc.gm_data.Ensemble(ensemble_id)

    return flask.jsonify(
        {"ensemble_id": ensemble_id, "ims": su.api.get_available_im_dict(ensemble.ims)}
    )
