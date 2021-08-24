import seistech_utils.src.test as tu
from core_api import constants

# NZS1170p5 Tests
def test_get_nzs1170p5_ensemble_hazard(config):
    """ Tests the successful get request of a NZS1170p5 ensemble hazard"""
    response = tu.send_test_request(
        constants.NZS1170p5_HAZARD_ENDPOINT,
        config["general"],
    )
    tu.response_checks(
        response,
        [
            ("nzs1170p5_hazard", object),
            (["nzs1170p5_hazard", "Ch"], object),
            (["nzs1170p5_hazard", "D"], float),
            (["nzs1170p5_hazard", "N"], object),
            (["nzs1170p5_hazard", "R"], object),
            (["nzs1170p5_hazard", "Z"], float),
            (["nzs1170p5_hazard", "ensemble_id"], str),
            (["nzs1170p5_hazard", "im"], str),
            (["nzs1170p5_hazard", "im_values"], object),
            (["nzs1170p5_hazard", "sa_period"], int),
            (["nzs1170p5_hazard", "soil_class"], str),
            (["nzs1170p5_hazard", "station"], str),
            ("download_token", str),
        ],
        [
            (["nzs1170p5_hazard", "ensemble_id"], config["general"]["ensemble_id"]),
            (["nzs1170p5_hazard", "station"], config["general"]["station"]),
            (["nzs1170p5_hazard", "im"], config["general"]["im"]),
        ],
    )


def test_get_nzs1170p5_ensemble_hazard_missingparam(config):
    """ Tests the failed get request of a NZS1170p5 ensemble hazard"""
    response = tu.send_test_request(
        constants.NZS1170p5_HAZARD_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("im"))], 400
    )


def test_get_nzs1170p5_uhs(config):
    """ Tests the successful get request of a NZS1170p5 UHS"""
    response = tu.send_test_request(
        constants.NZS1170p5_UHS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
            "exceedances": config["nzs1170p5"]["exceedances"],
        },
    )
    tu.response_checks(
        response,
        [
            ("download_token", str),
            ("ensemble_id", str),
            ("nzs1170p5_results", object),
            ("nzs1170p5_uhs_df", object),
            ("station", str),
        ],
        [
            ("ensemble_id", config["general"]["ensemble_id"]),
            ("station", config["general"]["station"]),
        ],
    )


def test_get_nzs1170p5_uhs_missingparam(config):
    """ Tests the failed get request of a NZS1170p5 UHS"""
    response = tu.send_test_request(
        constants.NZS1170p5_UHS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("exceedances"))], 400
    )


def test_get_nzs1170p5_default(config):
    """ Tests the successful get request of a NZS1170p5 default parameters"""
    response = tu.send_test_request(
        constants.NZS1170p5_DEFAULT_PARAMS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    tu.response_checks(
        response,
        [
            ("distance", float),
            ("soil_class", str),
            ("z_factor", float),
        ],
    )


def test_get_nzs1170p5_default_missingparam(config):
    """ Tests the failed get request of a NZS1170p5 default parameters"""
    response = tu.send_test_request(
        constants.NZS1170p5_DEFAULT_PARAMS_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"]},
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("station"))], 400
    )


def test_get_nzs1170p5_soil_class():
    """ Tests the successful get request of a NZS1170p5 soil classes"""
    response = tu.send_test_request(
        constants.NZS1170p5_SOIL_CLASS_ENDPOINT,
    )
    tu.response_checks(
        response,
        [
            ("soil_class", object),
        ],
    )
