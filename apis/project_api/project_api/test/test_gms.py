import api_utils.test as tu
from project_api import constants


# GMS Tests
def test_gms_runs(config):
    """ Tests the successful get request of the gms runs"""
    response = tu.send_test_request(
        constants.PROJECT_GMS_RUNS_ENDPOINT,
        {"project_id": config["general"]["project_id"]},
        api="PROJECT",
    )
    check_list = []
    for key in response.json().keys():
        check_list.extend(
            [
                ([key, "IM_j"], str),
                ([key, "IMs"], list),
                ([key, "dataset_id"], str),
                ([key, "exceedance"], float),
                ([key, "im_j"], type(None)),
                ([key, "n_gms"], int),
                ([key, "n_replica"], int),
            ]
        )
    tu.response_checks(
        response,
        check_list,
        [],
    )


def test_get_gms(config):
    """ Tests the successful get request of a GMS"""
    response = tu.send_test_request(
        constants.PROJECT_GMS_ENDPOINT,
        {**config["general"], **config["gms"]},
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [
            ("download_token", str),
            ("IM_j", str),
            ("IMs", list),
            ("gcim_cdf_x", dict),
            ("gcim_cdf_y", dict),
            ("im_j", float),
            ("ks_bounds", float),
            ("realisations", dict),
            ("selected_GMs", dict),
            ("selected_gms_metadata", object),
            (["selected_gms_metadata", "mag"], list),
            (["selected_gms_metadata", "ks_bounds"], float),
            (["selected_gms_metadata", "rrup"], list),
            (["selected_gms_metadata", "selected_gms_agg"], dict),
            (["selected_gms_metadata", "sf"], list),
            (["selected_gms_metadata", "vs30"], list),
        ],
        [],
    )


def test_get_gms_missing_parameter(config):
    """ Tests the failed get request of a GMS with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_GMS_ENDPOINT,
        {**config["general"]},
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("gms_id"))], 400
    )


def test_get_gms_download(config):
    """ Tests the sucessful get request of a GMS download"""
    response_gms = tu.send_test_request(
        constants.PROJECT_GMS_ENDPOINT,
        {**config["general"], **config["gms"]},
        api="PROJECT",
    )
    response = tu.send_test_request(
        constants.PROJECT_GMS_DOWNLOAD_ENDPOINT,
        url_extension="/" + response_gms.json()["download_token"],
        api="PROJECT",
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_gms_download_missing_token():
    """ Tests the failed get request of a GMS download with missing token"""
    response = tu.send_test_request(
        constants.PROJECT_GMS_DOWNLOAD_ENDPOINT, api="PROJECT"
    )
    tu.response_checks(response, [], [], 404, "text/html; charset=utf-8")


def test_get_gms_default_casual_parameters(config):
    """ Tests the sucessful get request of a GMS default Casual Parameters"""
    response = tu.send_test_request(
        constants.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT,
        {**config["general"], **config["gms"]},
        api="PROJECT",
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
            ("vs30_high", float),
            ("vs30_low", float),
        ],
        [],
    )


def test_get_gms_default_casual_parameters_missing_parameter(config):
    """ Tests the failed get request of a GMS default Casual Parameters with missing parameter"""
    response = tu.send_test_request(
        constants.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT,
        {**config["general"]},
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("gms_id"))], 400
    )
