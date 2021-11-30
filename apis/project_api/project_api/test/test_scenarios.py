import gmhazard_utils.src.test as tu
from project_api import constants


# Scenario Tests
def test_get_scenario(config):
    """ Tests the successful get request of a scenario"""
    response = tu.send_test_request(
        constants.PROJECT_SCENARIO_ENDPOINT,
        {**config["general"]},
        api="PROJECT",
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
            (["ensemble_scenario", "ensemble_id"], config["general"]["project_id"]),
            (["ensemble_scenario", "station"], config["general"]["station_id"]),
        ],
    )


def test_get_scenario_missing_param(config):
    """ Tests the failed get request of a scenario without parameters"""
    response = tu.send_test_request(
        constants.PROJECT_SCENARIO_ENDPOINT,
        {"station_id": config["general"]["station_id"]},
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("project_id"))],
        400,
    )


def test_get_scenario_download(config):
    """ Tests the successful get request of a scenario download"""
    response_scenario = tu.send_test_request(
        constants.PROJECT_SCENARIO_ENDPOINT,
        {**config["general"]},
        api="PROJECT",
    )
    response = tu.send_test_request(
        constants.PROJECT_SCENARIO_DOWNLOAD_ENDPOINT,
        {
            "scenario_token": response_scenario.json()["download_token"],
        },
        api="PROJECT",
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_scenario_download_missing_param():
    """ Tests the failed get request of a scenario download without parameters"""
    response = tu.send_test_request(
        constants.PROJECT_SCENARIO_DOWNLOAD_ENDPOINT,
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("scenario_token"))],
        400,
    )
