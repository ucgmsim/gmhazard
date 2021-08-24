import seistech_utils.src.test as tu
from core_api import constants

# Site Source Tests
def test_get_site_source_distances(config):
    """ Tests the sucessful get request of a Site Sources distances"""
    response = tu.send_test_request(
        constants.SITE_SOURCE_DISTANCES_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    tu.response_checks(
        response,
        [
            ("distances", str),
        ],
        [],
    )


def test_get_site_source_distances_missing_parameter(config):
    """ Tests the failed get request of a Site Sources distances with missing parameter"""
    response = tu.send_test_request(
        constants.SITE_SOURCE_DISTANCES_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"]},
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("station"))], 400
    )
