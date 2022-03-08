import api_utils.test as tu
from core_api import constants


# Scenario Tests
def test_get_ensemble_scenario(config):
    """ Tests the successful get request of an ensemble scenario"""
    response = tu.send_test_request(
        constants.ENSEMBLE_SCENARIO_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    check_list = [
        ("download_token", str),
        ("ensemble_scenario", dict),
        (["ensemble_scenario", "ensemble_id"], str),
        (["ensemble_scenario", "station"], str),
        (["ensemble_scenario", "ims"], list),
        (["ensemble_scenario", "mu_data"], dict),
        (["ensemble_scenario", "percentiles"], dict),
        (["ensemble_scenario", "percentiles", "16th"], dict),
        (["ensemble_scenario", "percentiles", "50th"], dict),
        (["ensemble_scenario", "percentiles", "84th"], dict),
    ]
    tu.response_checks(
        response,
        check_list,
        [
            (["ensemble_scenario", "ensemble_id"], config["general"]["ensemble_id"]),
            (["ensemble_scenario", "station"], config["general"]["station"]),
        ],
    )


def test_get_ensemble_scenario_missing_param(config):
    """ Tests the failed get request of an ensemble scenario without parameters"""
    response = tu.send_test_request(
        constants.ENSEMBLE_SCENARIO_ENDPOINT,
        {"station": config["general"]["station"]},
    )
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("ensemble_id"))],
        400,
    )


def test_get_ensemble_scenario_download(config):
    """ Tests the successful get request of an ensemble scenario download"""
    response_scenario = tu.send_test_request(
        constants.ENSEMBLE_SCENARIO_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    response = tu.send_test_request(
        constants.ENSEMBLE_SCENARIO_DOWNLOAD_ENDPOINT,
        {
            "scenario_token": response_scenario.json()["download_token"],
        },
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_ensemble_scenario_download_missing_param():
    """ Tests the failed get request of an ensemble scenario download without parameters"""
    response = tu.send_test_request(
        constants.ENSEMBLE_SCENARIO_DOWNLOAD_ENDPOINT,
    )
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("scenario_token"))],
        400,
    )
