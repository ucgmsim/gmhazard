import seistech_utils.src.test as tu
from core_api import constants

# NZTA Tests
def test_get_nzta_ensemble_hazard(config):
    """ Tests the successful get request of a NZTA ensemble hazard"""
    response = tu.send_test_request(
        constants.NZTA_HAZARD_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
            **config["nzta"],
        },
    )
    tu.response_checks(
        response,
        [
            ("nzta_hazard", object),
            (["nzta_hazard", "M_eff"], float),
            (["nzta_hazard", "c0_1000"], float),
            (["nzta_hazard", "nearest_town"], str),
            (["nzta_hazard", "pga_values"], object),
            (["nzta_hazard", "ensemble_id"], str),
            (["nzta_hazard", "soil_class"], str),
            (["nzta_hazard", "station"], str),
            ("download_token", str),
        ],
        [
            (["nzta_hazard", "ensemble_id"], config["general"]["ensemble_id"]),
            (["nzta_hazard", "station"], config["general"]["station"]),
            (["nzta_hazard", "soil_class"], config["nzta"]["soil_class"]),
        ],
    )


def test_get_nzta_ensemble_hazard_missing_parameter(config):
    """ Tests the failed get request of a NZTA ensemble hazard"""
    response = tu.send_test_request(
        constants.NZTA_HAZARD_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("soil_class"))], 400
    )


def test_get_nzta_default_parameters(config):
    """ Tests the successful get request of a NZTA default parameters"""
    response = tu.send_test_request(
        constants.NZTA_DEFAULT_PARAMS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    tu.response_checks(
        response,
        [
            ("soil_class", str),
        ],
    )


def test_get_nzta_default_parameters_missing_parameter(config):
    """ Tests the failed get request of a NZTA default parameters"""
    response = tu.send_test_request(
        constants.NZTA_DEFAULT_PARAMS_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"]},
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("station"))], 400
    )


def test_get_nzta_soil_class():
    """ Tests the successful get request of a NZTA soil_class"""
    response = tu.send_test_request(
        constants.NZTA_SOIL_CLASS_ENDPOINT,
    )
    tu.response_checks(
        response,
        [
            ("soil_class", object),
        ],
    )
