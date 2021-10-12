import gmhazard_utils.src.test as tu
from core_api import constants

# UHS Tests
def test_get_uhs(config):
    """ Tests the successful get request of a UHS Ensemble"""
    response = tu.send_test_request(
        constants.ENSEMBLE_UHS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
            "exceedances": str(config["nzs1170p5"]["exceedances"]),
            "calc_percentiles": config["hazard"]["calc_percentiles"],
        },
    )
    tu.response_checks(
        response,
        [
            ("download_token", str),
            ("ensemble_id", str),
            ("station", str),
            ("uhs_df", object),
            (["uhs_df", str(config["uhs"]["return_period"]) + "_mean"], dict),
            (["uhs_df", str(config["uhs"]["return_period"]) + "_16th"], dict),
            (["uhs_df", str(config["uhs"]["return_period"]) + "_84th"], dict),
            ("uhs_results", dict),
            (["uhs_results", str(config["nzs1170p5"]["exceedances"])], dict),
            (
                ["uhs_results", str(config["nzs1170p5"]["exceedances"]), "percentiles"],
                dict,
            ),
            (
                [
                    "uhs_results",
                    str(config["nzs1170p5"]["exceedances"]),
                    "percentiles",
                    "16th",
                ],
                dict,
            ),
            (
                [
                    "uhs_results",
                    str(config["nzs1170p5"]["exceedances"]),
                    "percentiles",
                    "84th",
                ],
                dict,
            ),
        ],
        [
            ("ensemble_id", config["general"]["ensemble_id"]),
            ("station", config["general"]["station"]),
        ],
    )


def test_get_uhs_missing_parameter(config):
    """ Tests the failed get request of a UHS Ensemble with missing parameters"""
    response = tu.send_test_request(
        constants.ENSEMBLE_UHS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
        },
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("exceedances"))], 400
    )


def test_get_uhs_download(config):
    """ Tests the successful get request of a UHS Ensemble download"""
    response_uhs = tu.send_test_request(
        constants.ENSEMBLE_UHS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
            "exceedances": config["nzs1170p5"]["exceedances"],
            "calc_percentiles": config["hazard"]["calc_percentiles"],
        },
    )
    response_nsz1170p5 = tu.send_test_request(
        constants.NZS1170p5_UHS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
            "exceedances": config["nzs1170p5"]["exceedances"],
        },
    )
    response = tu.send_test_request(
        constants.ENSEMBLE_UHS_DOWNLOAD_ENDPOINT,
        {
            "uhs_token": response_uhs.json()["download_token"],
            "nzs1170p5_hazard_token": response_nsz1170p5.json()["download_token"],
        },
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_get_uhs_download_missing_parameter(config):
    """ Tests the failed get request of a UHS Ensemble download with missing parameters"""
    response = tu.send_test_request(
        constants.ENSEMBLE_UHS_DOWNLOAD_ENDPOINT,
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("uhs_token"))], 400
    )


def test_get_uhs_user_vs30(config):
    """Tests the successful get request of a UHS with a
    different set of vs30 and ensure the result is different to the db vs30 calculations"""
    response_db = tu.send_test_request(
        constants.ENSEMBLE_UHS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
            "exceedances": str(config["nzs1170p5"]["exceedances"]),
            "calc_percentiles": config["hazard"]["calc_percentiles"],
        },
    )
    response_user = tu.send_test_request(
        constants.ENSEMBLE_UHS_ENDPOINT,
        {
            "ensemble_id": config["general"]["ensemble_id"],
            "station": config["general"]["station"],
            "exceedances": str(config["nzs1170p5"]["exceedances"]),
            "calc_percentiles": config["hazard"]["calc_percentiles"],
            "vs30": config["user_vs30"],
        },
    )
    tu.response_user_vs30_checks(
        response_db,
        response_user,
        [
            ["uhs_df", str(config["uhs"]["return_period"]) + "_mean"],
        ],
    )
