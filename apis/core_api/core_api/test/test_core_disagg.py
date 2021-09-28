import gmhazard_utils.src.test as tu
from core_api import constants


# Disagg Tests
def test_get_disagg(config):
    """ Tests the successful get request of a Disagg Ensemble"""
    response = tu.send_test_request(
        constants.ENSEMBLE_DISAGG_ENDPOINT, {**config["general"], **config["disagg"]}
    )
    tu.response_checks(
        response,
        [
            ("disagg_data", object),
            (["disagg_data", "im"], str),
            (["disagg_data", "im_value"], float),
            (["disagg_data", "mean_values"], object),
            (["disagg_data", "station"], str),
            (["disagg_data", "total_contribution"], object),
            ("download_token", str),
            ("ensemble_id", str),
            ("extra_info", object),
            (["extra_info", "annual_rec_prob"], object),
            (["extra_info", "magnitude"], object),
            (["extra_info", "rrup"], object),
            (["extra_info", "rupture_name"], object),
            ("im", str),
            ("station", str),
        ],
        [
            ("ensemble_id", config["general"]["ensemble_id"]),
            ("im", config["general"]["im"]),
            (["disagg_data", "im"], config["general"]["im"]),
            ("station", config["general"]["station"]),
            (["disagg_data", "station"], config["general"]["station"]),
        ],
    )


def test_get_disagg_missing_parameter(config):
    """ Tests the failed get request of a Disagg Ensemble with missing parameters"""
    response = tu.send_test_request(
        constants.ENSEMBLE_DISAGG_ENDPOINT, config["general"]
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("exceedance"))], 400
    )


def test_get_disagg_download(config):
    """ Tests the successful get request of a Disagg Ensemble download"""
    disagg_response = tu.send_test_request(
        constants.ENSEMBLE_DISAGG_ENDPOINT, {**config["general"], **config["disagg"]}
    )
    response = tu.send_test_request(
        constants.ENSEMBLE_DISAGG_DOWNLOAD_ENDPOINT,
        {"disagg_token": disagg_response.json()["download_token"]},
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_disagg_download_missing_parameter(config):
    """ Tests the failed get request of a Disagg Ensemble download without the download token"""
    response = tu.send_test_request(constants.ENSEMBLE_DISAGG_DOWNLOAD_ENDPOINT)
    tu.response_checks(
        response,
        [("error", str)],
        [("error", tu.MISSING_PARAM_MSG.format("disagg_token"))],
        400,
    )


def test_get_disagg_user_vs30(config):
    """Tests the successful get request of a Disagg with a
    different set of vs30 and ensure the result is different to the db vs30 calculations"""
    response_db = tu.send_test_request(
        constants.ENSEMBLE_DISAGG_ENDPOINT,
        {**config["general"], **config["disagg"]},
    )
    response_user = tu.send_test_request(
        constants.ENSEMBLE_DISAGG_ENDPOINT,
        {**config["general"], **config["disagg"], "vs30": config["user_vs30"]},
    )
    tu.response_user_vs30_checks(
        response_db,
        response_user,
        [
            ["disagg_data", "total_contribution"],
        ],
    )
