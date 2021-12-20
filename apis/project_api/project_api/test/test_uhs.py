import api_utils.test as tu
from project_api import constants


def test_get_uhs_rps(config):
    """ Tests the successful get request of a UHS rps"""
    response = tu.send_test_request(
        constants.PROJECT_UHS_RPS_ENDPOINT,
        {
            "project_id": config["general"]["project_id"],
        },
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [
            ("rps", list),
        ],
    )


def test_get_uhs_rps_missing_parameter():
    """ Tests the failed get request of a UHS rps with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_UHS_RPS_ENDPOINT,
        {},
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("project_id"))], 400
    )


def test_get_uhs(config):
    """ Tests the successful get request of a UHS"""
    response = tu.send_test_request(
        constants.PROJECT_UHS_ENDPOINT,
        {
            **config["general"],
            **config["uhs"],
        },
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [
            ("download_token", str),
            ("ensemble_id", str),
            ("station", str),
            ("uhs_df", dict),
            ("uhs_results", dict),
            ("branch_uhs_results", dict),
            ("nzs1170p5_results", list),
            ("nzs1170p5_uhs_df", dict),
        ],
        [
            ("ensemble_id", config["general"]["project_id"]),
            ("station", config["general"]["station_id"]),
        ],
    )


def test_get_uhs_missing_parameter():
    """ Tests the failed get request of a UHS with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_UHS_ENDPOINT,
        {},
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("project_id"))], 400
    )


def test_get_uhs_download(config):
    """ Tests the successful get request of a UHS download"""
    response_uhs = tu.send_test_request(
        constants.PROJECT_UHS_ENDPOINT,
        {
            **config["general"],
            **config["uhs"],
        },
        api="PROJECT",
    )
    response = tu.send_test_request(
        constants.PROJECT_UHS_DOWNLOAD_ENDPOINT,
        {
            "uhs_token": response_uhs.json()["download_token"],
        },
        api="PROJECT",
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_uhs_download_missing_parameter():
    """ Tests the failed get request of a UHS download with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_UHS_DOWNLOAD_ENDPOINT,
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("uhs_token"))], 400
    )
