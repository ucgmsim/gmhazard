import gmhazard_utils.src.test as tu
from core_api import constants

# Ruputure Tests
def test_get_rupture(config):
    """ Tests the sucessful get request of a Rupture"""
    response = tu.send_test_request(
        constants.RUPTURES_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"]},
    )
    tu.response_checks(
        response,
        [
            ("ruptures", object),
        ],
        [],
    )


def test_get_rupture_missing_parameter():
    """ Tests the failed get request of a Rupture with missing parameter"""
    response = tu.send_test_request(
        constants.RUPTURES_ENDPOINT,
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("ensemble_id"))], 400
    )
