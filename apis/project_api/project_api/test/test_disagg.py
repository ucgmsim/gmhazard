import api_utils.test as tu
from project_api import constants


# Disagg Tests
def test_get_disagg_rps(config):
    """ Tests the successful get request of a Disagg RP's"""
    response = tu.send_test_request(
        constants.PROJECT_DISAGG_RPS_ENDPOINT,
        {"project_id": config["general"]["project_id"]},
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [
            ("rps", list),
        ],
        [],
    )


def test_get_disagg_rps_missing_parameter():
    """ Tests the successful get request of a Disagg RP's"""
    response = tu.send_test_request(
        constants.PROJECT_DISAGG_RPS_ENDPOINT, {}, api="PROJECT"
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("project_id"))], 400
    )


def test_get_disagg(config):
    """ Tests the successful get request of a Disagg"""
    response = tu.send_test_request(
        constants.PROJECT_DISAGG_ENDPOINT,
        {**config["general"], **config["disagg"]},
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [
            ("disagg_data", dict),
            (["disagg_data", "im"], str),
            (["disagg_data", "im_value"], float),
            (["disagg_data", "mean_values"], dict),
            (["disagg_data", "station"], str),
            (["disagg_data", "total_contribution"], dict),
            ("download_token", str),
            ("ensemble_id", str),
            ("extra_info", dict),
            (["extra_info", "annual_rec_prob"], dict),
            (["extra_info", "magnitude"], dict),
            (["extra_info", "rrup"], dict),
            (["extra_info", "rupture_name"], dict),
            ("im", str),
            ("station", str),
        ],
        [
            ("ensemble_id", config["general"]["project_id"]),
            ("im", config["disagg"]["im"]),
            (["disagg_data", "im"], config["disagg"]["im"]),
            ("station", config["general"]["station_id"]),
            (["disagg_data", "station"], config["general"]["station_id"]),
        ],
    )


def test_get_disagg_missing_parameter(config):
    """ Tests the failed get request of a Disagg with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_DISAGG_ENDPOINT, config["general"], api="PROJECT"
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("im"))], 400
    )


def test_get_disagg_download(config):
    """ Tests the successful get request of a Disagg download"""
    disagg_response = tu.send_test_request(
        constants.PROJECT_DISAGG_ENDPOINT,
        {**config["general"], **config["disagg"]},
        api="PROJECT",
    )
    response = tu.send_test_request(
        constants.PROJECT_DISAGG_DOWNLOAD_ENDPOINT,
        {"disagg_token": disagg_response.json()["download_token"]},
        api="PROJECT",
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_disagg_download_missing_parameter():
    """ Tests the failed get request of a Disagg download without the download token"""
    response = tu.send_test_request(
        constants.PROJECT_DISAGG_DOWNLOAD_ENDPOINT, api="PROJECT"
    )
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("disagg_token"))],
        400,
    )
