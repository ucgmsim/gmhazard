import api_utils.test as tu
from project_api import constants


# Hazard Tests
def test_get_hazard(config):
    """ Tests the successful get request of a hazard"""
    response = tu.send_test_request(
        constants.PROJECT_HAZARD_ENDPOINT,
        {**config["general"], **config["hazard"]},
        api="PROJECT",
    )
    check_list = [
        ("ensemble_id", str),
        ("im", str),
        ("station", str),
        ("branches_hazard", object),
        ("nzs1170p5_hazard", object),
        ("nzta_hazard", object),
        ("download_token", str),
        ("ensemble_hazard", object),
        (["ensemble_hazard", "ds"], object),
        (["ensemble_hazard", "fault"], object),
        (["ensemble_hazard", "total"], object),
        ("percentiles", object),
        (["percentiles", "16th"], object),
        (["percentiles", "84th"], object),
    ]
    # Adding in the parts of the json that are not static
    assert "branches_hazard" in response.json()
    for key in response.json()["branches_hazard"].keys():
        check_list.append((["branches_hazard", key, "ds"], object))
        check_list.append((["branches_hazard", key, "fault"], object))
        check_list.append((["branches_hazard", key, "total"], object))
    tu.response_checks(
        response,
        check_list,
        [
            ("ensemble_id", config["general"]["project_id"]),
            ("station", config["general"]["station_id"]),
            ("im", config["hazard"]["im"]),
        ],
    )


def test_get_hazard_missing_param(config):
    """ Tests the failed get request of a hazard without parameters"""
    response = tu.send_test_request(
        constants.PROJECT_HAZARD_ENDPOINT,
        {"station_id": config["general"]["station_id"], "im": config["hazard"]["im"]},
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("project_id"))], 400
    )


def test_get_hazard_download(config):
    """ Tests the successful get request of a hazard download"""
    response_hazard = tu.send_test_request(
        constants.PROJECT_HAZARD_ENDPOINT,
        {**config["general"], **config["hazard"]},
        api="PROJECT",
    )
    response = tu.send_test_request(
        constants.PROJECT_HAZARD_DOWNLOAD_ENDPOINT,
        {
            "hazard_token": response_hazard.json()["download_token"],
        },
        api="PROJECT",
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_hazard_download_missing_param():
    """ Tests the failed get request of a hazard download without parameters"""
    response = tu.send_test_request(
        constants.PROJECT_HAZARD_DOWNLOAD_ENDPOINT,
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("hazard_token"))],
        400,
    )
