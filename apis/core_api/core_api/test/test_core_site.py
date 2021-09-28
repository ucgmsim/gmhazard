import gmhazard_utils.src.test as tu
from core_api import constants

# Site Tests
def test_get_site_location(config):
    """ Tests the sucessful get request of a Sites location"""
    response = tu.send_test_request(
        constants.SITE_LOCATION_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"], **config["site"]},
    )
    tu.response_checks(
        response,
        [
            ("distance", str),
            ("lat", str),
            ("lon", str),
            ("station", str),
            ("vs30", str),
        ],
        [("station", config["site_found"])],
    )


def test_get_site_location_missing_parameter(config):
    """ Tests the failed get request of a Sites location with missing parameter"""
    response = tu.send_test_request(
        constants.SITE_LOCATION_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"], "lat": config["site"]["lat"]},
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("lon"))], 400
    )


def test_get_site_name(config):
    """ Tests the sucessful get request of a Sites name"""
    response = tu.send_test_request(
        constants.SITE_NAME_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    tu.response_checks(
        response,
        [
            ("lat", str),
            ("lon", str),
            ("station", str),
            ("vs30", str),
        ],
        [("station", config["general"]["station"])],
    )


def test_get_site_name_missing_parameter(config):
    """ Tests the failed get request of a Sites name with missing parameter"""
    response = tu.send_test_request(
        constants.SITE_NAME_ENDPOINT, {"ensemble_id": config["general"]["ensemble_id"]}
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("station"))], 400
    )


def test_get_site_context_map(config):
    """ Tests the sucessful get request of a Sites context map"""
    response = tu.send_test_request(
        constants.SITE_CONTEXT_MAP_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"], **config["site"]},
    )
    tu.response_checks(
        response,
        [
            ("context_plot", str),
        ],
        [],
    )


def test_get_site_context_map_missing_parameter(config):
    """ Tests the failed get request of a Sites context map with missing parameter"""
    response = tu.send_test_request(
        constants.SITE_CONTEXT_MAP_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"], "lat": config["site"]["lat"]},
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("lon"))], 400
    )


def test_get_site_vs30_map(config):
    """ Tests the sucessful get request of a Sites vs30 map"""
    response = tu.send_test_request(
        constants.SITE_VS30_MAP_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"], **config["site"]},
    )
    tu.response_checks(
        response,
        [
            ("vs30_plot", str),
        ],
        [],
    )


def test_get_site_vs30_map_missing_parameter(config):
    """ Tests the failed get request of a Sites vs30 map with missing parameter"""
    response = tu.send_test_request(
        constants.SITE_VS30_MAP_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"], "lat": config["site"]["lat"]},
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("lon"))], 400
    )
