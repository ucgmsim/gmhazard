import api_utils.test as tu
from core_api import constants


# Hazard Tests
def test_get_ensemble_hazard(config):
    """ Tests the successful get request of a ensemble hazard"""
    response = tu.send_test_request(
        constants.ENSEMBLE_HAZARD_ENDPOINT, {**config["general"], **config["hazard"]},
    )
    check_list = [
        ("ensemble_id", str),
        ("im", str),
        ("station", str),
        ("branches_hazard", object),
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
            ("ensemble_id", config["general"]["ensemble_id"]),
            ("station", config["general"]["station"]),
            ("im", config["general"]["im"]),
        ],
    )


def test_get_ensemble_hazard_missing_param(config):
    """ Tests the failed get request of a Ensemble's hazard without parameters"""
    response = tu.send_test_request(
        constants.ENSEMBLE_HAZARD_ENDPOINT,
        {"station": config["general"]["station"], "im": config["general"]["im"]},
    )
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("ensemble_id"))],
        400,
    )


def test_get_ensemble_hazard_download(config):
    """ Tests the successful get request of a ensemble hazard download"""
    response_hazard = tu.send_test_request(
        constants.ENSEMBLE_HAZARD_ENDPOINT, {**config["general"], **config["hazard"]},
    )
    response_nzs1170p5 = tu.send_test_request(
        constants.NZS1170p5_HAZARD_ENDPOINT, config["general"],
    )
    response = tu.send_test_request(
        constants.ENSEMBLE_HAZARD_DOWNLOAD_ENDPOINT,
        {
            "hazard_token": response_hazard.json()["download_token"],
            "nzs1170p5_hazard_token": response_nzs1170p5.json()["download_token"],
        },
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_ensemble_hazard_download_missing_param():
    """ Tests the failed get request of a Ensemble's hazard download without parameters"""
    response = tu.send_test_request(constants.ENSEMBLE_HAZARD_DOWNLOAD_ENDPOINT)
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("hazard_token"))],
        400,
    )


def test_get_ensemble_hazard_user_vs30(config):
    """Tests the successful get request of a ensemble hazard with a
    different set of vs30 and ensure the result is different to the db vs30 calculations"""
    response_db = tu.send_test_request(
        constants.ENSEMBLE_HAZARD_ENDPOINT, {**config["general"], **config["hazard"]},
    )
    response_user = tu.send_test_request(
        constants.ENSEMBLE_HAZARD_ENDPOINT,
        {**config["general"], **config["hazard"], "vs30": config["user_vs30"]},
    )
    tu.response_user_vs30_checks(
        response_db,
        response_user,
        ["branches_hazard", "ensemble_hazard", "percentiles"],
    )
