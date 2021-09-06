import os
import uuid
import json
import tempfile
from typing import Any, Dict

import flask
import pandas as pd
import numpy as np
from flask_cors import cross_origin
from werkzeug.contrib.cache import BaseCache

import seistech_calc as sc
import seistech_utils as su
import sha_calc as sha_calc
from core_api import server
from core_api import constants as const


class GMSCacheData:
    """Wrapper for caching"""

    def __init__(
        self,
        params: Dict,
        ensemble: sc.gm_data.Ensemble,
        site_info: sc.site.SiteInfo,
        gm_dataset: sc.gms.GMDataset,
        gms_result: sc.gms.GMSResult,
        meta_df: pd.DataFrame,
        ks_bounds: float,
    ):
        self.params = params

        self.ensemble = ensemble
        self.site_info = site_info
        self.gm_dataset = gm_dataset

        self.gms_result = gms_result

        self.meta_df = meta_df

        self.ks_bounds = ks_bounds


@server.app.route(const.ENSEMBLE_GMS_COMPUTE_ENDPOINT, methods=["POST"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def compute_ensemble_GMS():
    """For the specified ensemble computes the GCIM,
    selects the random realisations and selects the
    GMs with minimal misfit

    Only returns the calulcation results not the actual waveform

    Since GMS is non-deterministic each result is saved (using the cache)
    using a unique ID, to allow later downloading of the waveforms

    And unlike hazard, disagg and UHS the result for specific set of parameters
    are not cached due to the non-deterministic nature, allowing users to run
    GMS multiple times if desired

    Parameters in the json POST request (all request):
    ensemble_id: string
    station: string
    IM_j: string
        The conditioning IM
    IMs: list of strings
        The IM vector
    n_gms: int
        Number of ground motions to select
    gm_dataset_ids: list of strings
        The ids of the ground motion databases
        from which to select
    exceedance: float
    im_level: float
        Either the exceedance rate or the im level have to
        be given
    n_replica: int
        Number of times the GM selection process is repeated
    IM_weights: dictionary of floats
        Weights of the different IMs (have to sum to one)
        key: IM name as specified in the IMs vector
        value: weight of the IM
    cs_param_bounds: dictionary of floats
        The pre-filter parameters to use
        Required keys: ["mag_low", "mag_high",
                        "rrup_low", "rrup_high",
                        "vs30_low", "vs30_high",
                        "sf_low", "sf_high"]
        Set value to null (for both low & high) for no filtering
    vs30: float
        Users set vs30 for the given site


    Example POST request body:
    {
        "ensemble_id": "v20p5emp",
        "station": "CCCC",
        "IM_j": "PGA",
        "IMs": ["pSA_0.5", "pSA_1.0"],
        "n_gms": 10,
        "gm_dataset_ids": ["cybershake_v19p5"],
        "exceedance": 0.04,
        "n_replica": 4,
        "IM_weights": {"pSA_0.5": 0.6, "pSA_1.0": 0.4},
        "cs_param_bounds": {"mag_low": 4.0, "mag_high": 8.0,
                            "rrup_low": 50, "rrup_high": 200,
                            "vs30_low": 100, "vs30_high": 400,
                            "sf_low": 0.3, "sf_high": 3.0},
        "vs30": 600
    }
    """
    server.app.logger.info(f"Received request at {const.ENSEMBLE_GMS_COMPUTE_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    # Check required parameters are specified
    params = json.loads(flask.request.data.decode())
    for req_param in [
        "ensemble_id",
        "station",
        "IM_j",
        "IMs",
        "n_gms",
        "gm_dataset_ids",
    ]:
        if req_param not in params.keys():
            raise su.api.MissingKeyError(req_param)

    # Require either the exceedance rate or the IM value
    if "exceedance" not in params.keys() and "im_level" not in params.keys():
        raise su.api.MissingKeyError("[exceedance|im_level]")

    server.app.logger.debug(f"Request parameters: {params}")

    (
        ensemble,
        site_info,
        gm_dataset,
        gms_result,
        meta_df,
        ks_bounds,
        cache_key,
    ) = _get_gms(params, cache)

    # Run disagg so we can get mean & 16th/84th percentile for mag and rrup
    disagg_result = sc.disagg.run_ensemble_disagg(
        ensemble,
        site_info,
        gms_result.IM_j,
        im_value=gms_result.im_j,
        calc_mean_values=True,
    )

    result = su.api.get_ensemble_gms(
        gms_result,
        su.api.get_download_token(
            {"key": cache_key},
            server.DOWNLOAD_URL_SECRET_KEY,
            server.DOWNLOAD_URL_VALID_FOR,
        ),
    )

    return flask.jsonify(
        {
            **result,
            "gm_dataset_metadata": gm_dataset.get_metadata_df(site_info).to_dict(
                orient="list"
            ),
            "n_gms_in_bounds": gm_dataset.get_n_gms_in_bounds(
                gm_dataset.get_metadata_df(site_info), gms_result.cs_param_bounds
            ),
            "disagg_mean_values": disagg_result.mean_values.to_dict(),
        }
    )


@server.app.route(f"{const.ENSEMBLE_GMS_DOWNLOAD_ENDPOINT}/<token>", methods=["GET"])
@su.api.endpoint_exception_handling(server.app)
def download_gms_results(token):
    """Handles downloading of the GMs selected via GMS"""
    server.app.logger.info(
        f"Received request at {const.ENSEMBLE_GMS_DOWNLOAD_ENDPOINT}"
    )
    cache = flask.current_app.extensions["cache"]
    cache_key = su.api.get_token_payload(token, server.DOWNLOAD_URL_SECRET_KEY)["key"]

    cached_data = cache.get(cache_key)
    if cached_data is not None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_ffp = su.api.download_gms_result(
                cached_data.gms_result, server.app, tmp_dir
            )
            return flask.send_file(
                zip_ffp,
                as_attachment=True,
                attachment_filename=os.path.basename(zip_ffp),
            )

    server.app.logger.debug(
        f"No cached data was found for the specified GMS result {cache_key}"
    )
    return (
        flask.jsonify(
            {"error": "The GMS result has either expired or something went wrong"}
        ),
        400,
    )


@server.app.route(const.GMS_DEFAULT_IM_WEIGHTS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_default_IM_weights():
    """Gets the default IM weights for the
    specified conditioning IM_j and IM vector

    Parameters:
    ----------
    IM_j: str
        conditioning IM
    IMs: comma seperated list of IMs
        IM vector

    Returns
    -------
    IM weights as dictionary
    """
    server.app.logger.info(
        f"Received request at {const.GMS_DEFAULT_IM_WEIGHTS_ENDPOINT}"
    )

    (IM_j, IMs), _ = su.api.get_check_keys(
        flask.request.args,
        (
            ("IM_j", sc.im.IM.from_str),
            "IMs",
        ),
    )

    server.app.logger.debug(f"Request parameters {IM_j}, {IMs}")

    IMs = np.asarray([sc.im.IM.from_str(im.strip()) for im in IMs.split(",")])

    server.app.logger.debug("Retrieving default IM weights")
    IM_weights = sc.gms.default_IM_weights(IM_j, IMs)

    return flask.jsonify({str(im): value for im, value in IM_weights.to_dict().items()})


@server.app.route(const.GMS_IMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_available_IMs():
    server.app.logger.info(f"Received request at {const.GMS_IMS_ENDPOINT}")

    (ensemble_id, gm_dataset_ids), _ = su.api.get_check_keys(
        flask.request.args, ("ensemble_id", "gm_dataset_ids")
    )

    ensemble = sc.gm_data.Ensemble(ensemble_id)
    gm_datasets = [
        sc.gms.GMDataset.get_GMDataset(cur_id.strip())
        for cur_id in gm_dataset_ids.split(",")
    ]

    ims = set(ensemble.ims)
    for cur_dataset in gm_datasets:
        ims.intersection_update(cur_dataset.ims)

    return flask.jsonify({"ims": sc.im.to_string_list(ims)})


@server.app.route(const.GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_default_causal_params():
    """
    Gets the default GM pre-filtering parameters
    for the specified parameters

    Parameters
    ----------
    ensemble_id: string
    station: string
    IM_j: string
    exceedance: float
    im_level: float
        Either the exceedance rate or the im level
        have to be specified
    user_vs30: float
        User specified Vs30 value
    """
    server.app.logger.info(
        f"Received request at {const.GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT}"
    )

    params, opt_params_dict = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", ("IM_j", sc.im.IM.from_str)),
        (("exceedance", float), ("im_level", float), ("user_vs30", float)),
    )

    # Require either the exceedance or the IM value
    if (
        "exceedance" not in opt_params_dict.keys()
        and "im_level" not in opt_params_dict.keys()
    ):
        raise su.api.MissingKeyError("[exceedance|im_level]")

    ensemble, station, IM_j = params

    ensemble = sc.gm_data.Ensemble(ensemble)
    site_info = sc.site.get_site_from_name(
        ensemble, station, user_vs30=opt_params_dict.get("user_vs30")
    )
    cs_param_bounds = sc.gms.default_causal_params(
        ensemble,
        site_info,
        IM_j,
        exceedance=opt_params_dict.get("exceedance"),
        im_value=opt_params_dict.get("im_level"),
    )
    return flask.jsonify(
        {
            **su.api.get_default_causal_params(cs_param_bounds),
            "sf_low": cs_param_bounds.sf_low,
            "sf_high": cs_param_bounds.sf_high,
        }
    )


@server.app.route(const.GMS_GM_DATASETS_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_gm_datasets():
    server.app.logger.info(f"Received request at {const.GMS_GM_DATASETS_ENDPOINT}")

    configs = sc.gms.load_gm_dataset_configs()
    return flask.jsonify(
        {
            cur_id: {"name": cur_config["name"], "type": cur_config["type"]}
            for cur_id, cur_config in configs.items()
        }
    )


def _get_gms(params: Dict[str, Any], cache: BaseCache):
    git_version = su.api.get_repo_version()

    # Load the required parameters
    ensemble_id, station = params["ensemble_id"], params["station"]
    IM_j, IMs, n_gms = (
        sc.im.IM.from_str(params["IM_j"]),
        np.asarray(sc.im.to_im_list(params["IMs"])),
        params["n_gms"],
    )
    gm_dataset_ids = params["gm_dataset_ids"]
    exceedance, im_j = params.get("exceedance"), params.get("im_level")
    user_vs30 = params.get("vs30") if "vs30" in params.keys() else None
    assert len(gm_dataset_ids) == 1, "Currently only support single GM dataset"

    server.app.logger.debug(f"Loading ensemble and retrieving site information")
    ensemble = sc.gm_data.Ensemble(ensemble_id)
    site_info = sc.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)
    gm_dataset = sc.gms.GMDataset.get_GMDataset(gm_dataset_ids[0])

    cs_param_bounds = params.get("cs_param_bounds")
    if cs_param_bounds is not None:
        cs_param_bounds = sc.gms.CausalParamBounds(
            ensemble,
            site_info,
            IM_j,
            (cs_param_bounds["mag_low"], cs_param_bounds["mag_high"]),
            (cs_param_bounds["rrup_low"], cs_param_bounds["rrup_high"]),
            (cs_param_bounds["vs30_low"], cs_param_bounds["vs30_high"]),
            sf_bounds=(cs_param_bounds["sf_low"], cs_param_bounds["sf_high"])
            if "sf_low" in cs_param_bounds
            else (None, None),
            exceedance=exceedance,
            im_value=im_j,
        )

    server.app.logger.debug(f"Computing GMS - version {git_version}")
    gms_result = sc.gms.run_ensemble_gms(
        ensemble,
        site_info,
        n_gms,
        IM_j,
        gm_dataset,
        IMs=IMs,
        exceedance=exceedance,
        im_j=im_j,
        n_replica=params.get("n_replica"),
        im_weights=pd.Series(params.get("IM_weights")),
        cs_param_bounds=cs_param_bounds,
    )
    meta_df = gm_dataset.get_metadata_df(site_info, gms_result.selected_gms_ids)

    # Add the scaling factor to the metadata
    if gms_result.sf is not None:
        meta_df["sf"] = gms_result.sf.loc[meta_df.index]

    # Compute the KS bounds for the GCIM plot
    ks_bounds = sha_calc.shared.ks_critical_value(gms_result.realisations.shape[0], 0.1)

    # Save this in the cache, to allow downloading of the results
    # TODO: Perhaps apply su.api.get_cache_key() instead randomly generated unique id?
    cache_key = str(uuid.uuid4())
    cache.set(
        cache_key,
        GMSCacheData(
            params,
            ensemble,
            site_info,
            gm_dataset,
            gms_result,
            meta_df,
            ks_bounds,
        ),
    )

    return (
        ensemble,
        site_info,
        gm_dataset,
        gms_result,
        meta_df,
        ks_bounds,
        cache_key,
    )
