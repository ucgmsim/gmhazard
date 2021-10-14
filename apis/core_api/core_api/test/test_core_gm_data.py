import gmhazard_utils.src.test as tu
from core_api import constants


# Ensemble Tests
def test_get_ensemble_ids():
    """ Tests the successful get request of the Ensemble ID's"""
    response = tu.send_test_request(constants.ENSEMBLE_IDS_ENDPOINT)
    tu.response_checks(response, [("ensemble_ids", list)])


def test_get_ensemble_ims(config):
    """ Tests the successful get request of a Ensemble's IM's"""
    response = tu.send_test_request(
        constants.ENSEMBLE_IMS_ENDPOINT,
        {"ensemble_id": config["general"]["ensemble_id"]},
    )
    tu.response_checks(
        response,
        [("ensemble_id", str), ("ims", dict)],
        [("ensemble_id", config["general"]["ensemble_id"])],
    )


def test_get_ensemble_ims_missingparam(config):
    """ Tests the failed get request of a Ensemble's IM's without parameters"""
    response = tu.send_test_request(constants.ENSEMBLE_IMS_ENDPOINT)
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("ensemble_id"))], 400
    )
