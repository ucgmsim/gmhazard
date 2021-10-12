import json

import gmhazard_utils.src.test as tu
from core_api import constants


# GMS Tests
def test_post_gms_compute(config):
    """ Tests the successful post request of a GMS compute"""
    response = tu.send_test_request(
        constants.ENSEMBLE_GMS_COMPUTE_ENDPOINT,
        method="POST",
        json=json.loads(
            json.dumps(
                {
                    **config["gms"],
                    "ensemble_id": config["general"]["ensemble_id"],
                    "station": config["general"]["station"],
                }
            )
        ),
    )
    tu.response_checks(
        response,
        [
            ("download_token", str),
            ("IM_j", str),
            ("IMs", list),
            ("disagg_mean_values", dict),
            ("gcim_cdf_x", dict),
            ("gcim_cdf_y", dict),
            ("gm_dataset_metadata", dict),
            ("im_j", float),
            ("ks_bounds", float),
            ("n_gms_in_bounds", int),
            ("realisations", dict),
            ("selected_GMs", dict),
            ("selected_gms_metadata", dict),
            (["selected_gms_metadata", "mag"], list),
            (["selected_gms_metadata", "selected_gms_agg", "mag_error_bounds"], list),
            (["selected_gms_metadata", "selected_gms_agg", "mag_mean"], float),
            (["selected_gms_metadata", "rrup"], list),
            (["selected_gms_metadata", "selected_gms_agg", "rrup_error_bounds"], list),
            (["selected_gms_metadata", "selected_gms_agg", "rrup_mean"], float),
            (["selected_gms_metadata", "sf"], list),
            (["selected_gms_metadata", "vs30"], list),
        ],
        [],
    )


def test_post_gms_compute_missing_json(config):
    """ Tests the failed post request of a GMS compute with missing json"""
    response = tu.send_test_request(
        constants.ENSEMBLE_GMS_COMPUTE_ENDPOINT,
        method="POST",
        json=json.loads(
            json.dumps(
                {**config["gms"], "ensemble_id": config["general"]["ensemble_id"]}
            )
        ),
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("station"))], 400
    )


def test_get_gms_compute_download(config):
    """ Tests the sucessful get request of a GMS compute download"""
    response_compute = tu.send_test_request(
        constants.ENSEMBLE_GMS_COMPUTE_ENDPOINT,
        method="POST",
        json=json.loads(
            json.dumps(
                {
                    **config["gms"],
                    "ensemble_id": config["general"]["ensemble_id"],
                    "station": config["general"]["station"],
                }
            )
        ),
    )
    response = tu.send_test_request(
        constants.ENSEMBLE_GMS_DOWNLOAD_ENDPOINT,
        url_extension="/" + response_compute.json()["download_token"],
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_gms_compute_download_missing_token(config):
    """ Tests the failed get request of a GMS compute download with missing token"""
    response = tu.send_test_request(constants.ENSEMBLE_GMS_DOWNLOAD_ENDPOINT)
    tu.response_checks(response, [], [], 404, "text/html")


def test_get_gms_default_im_weights(config):
    """ Tests the sucessful get request of a GMS default IM weights"""
    response = tu.send_test_request(
        constants.GMS_DEFAULT_IM_WEIGHTS_ENDPOINT,
        {"IM_j": config["gms"]["IM_j"], "IMs": config["gms"]["IMs"]},
    )
    tu.response_checks(
        response,
        [
            (config["gms"]["IMs"], float),
        ],
        [],
    )


def test_get_gms_default_im_weights_missing_parameter(config):
    """ Tests the failed get request of a GMS default IM weights with missing parameter"""
    response = tu.send_test_request(
        constants.GMS_DEFAULT_IM_WEIGHTS_ENDPOINT,
        {"IM_j": config["gms"]["IM_j"]},
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("IMs"))], 400
    )


def test_get_gms_ims(config):
    """ Tests the sucessful get request of a GMS IMs"""
    response = tu.send_test_request(
        constants.GMS_IMS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "gm_dataset_ids": config["gms"]["gm_dataset_ids"],
        },
    )
    tu.response_checks(
        response,
        [
            ("ims", list),
        ],
        [],
    )


def test_get_gms_ims_missing_parameter(config):
    """ Tests the failed get request of a GMS IMs with missing parameter"""
    response = tu.send_test_request(
        constants.GMS_IMS_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"]},
    )
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("gm_dataset_ids"))],
        400,
    )


def test_get_gms_default_casual_parameters(config):
    """ Tests the sucessful get request of a GMS default Casual Parameters"""
    response = tu.send_test_request(
        constants.GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
            "IM_j": config["gms"]["IM_j"],
            **config["gms_default"],
            "im_level": config["gms"]["im_level"],
        },
    )
    tu.response_checks(
        response,
        [
            ("contribution_df", object),
            (["contribution_df", "contribution"], list),
            (["contribution_df", "magnitude"], list),
            (["contribution_df", "rrup"], list),
            ("mw_high", float),
            ("mw_low", float),
            ("rrup_high", float),
            ("rrup_low", float),
            ("sf_high", float),
            ("sf_low", float),
            ("vs30_high", float),
            ("vs30_low", float),
        ],
        [],
    )


def test_get_gms_default_casual_parameters_missing_parameter(config):
    """ Tests the failed get request of a GMS default Casual Parameters with missing parameter"""
    response = tu.send_test_request(
        constants.GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
            "IM_j": config["gms"]["IM_j"],
            **config["gms_default"],
        },
    )
    tu.response_checks(
        response,
        [("error", str)],
        [("error", "Either the exceendance or the IM level has to be specified.")],
        400,
    )


def test_get_gms_datasets(config):
    """ Tests the sucessful get request of a GMS datasets"""
    response = tu.send_test_request(
        constants.GMS_GM_DATASETS_ENDPOINT,
    )
    check_list = []
    for dataset in config["gms_datasets"]:
        check_list.append((dataset, object))
        check_list.append(([dataset, "name"], str))
        check_list.append(([dataset, "type"], str))
    tu.response_checks(
        response,
        check_list,
        [],
    )
