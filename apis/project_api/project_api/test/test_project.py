import seistech_utils.src.test as tu
from project_api import constants


def test_get_available_ids():
    """ Tests the successful get request of the available projects ids"""
    response = tu.send_test_request(
        constants.PROJECT_IDS_ENDPOINT,
        {},
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [
            ("ids", list),
        ],
    )


def test_get_available_sites(config):
    """ Tests the successful get request of the available sites for a project"""
    response = tu.send_test_request(
        constants.PROJECT_SITES_ENDPOINT,
        {"project_id": config["general"]["project_id"]},
        api="PROJECT",
    )
    check_list = []
    for key in response.json().keys():
        check_list.extend(
            [
                ([key, "lat"], float),
                ([key, "lon"], float),
                ([key, "name"], str),
                ([key, "vs30"], list),
            ]
        )
    tu.response_checks(
        response,
        check_list,
    )


def test_get_available_sites_missing_parameter():
    """ Tests the failed get request of a projects available sites with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_SITES_ENDPOINT,
        {},
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("project_id"))], 400
    )


def test_get_available_ims(config):
    """ Tests the successful get request of the available ims for a project"""
    response = tu.send_test_request(
        constants.PROJECT_IMS_ENDPOINT,
        {"project_id": config["general"]["project_id"]},
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [
            ("ims", dict),
        ],
    )


def test_get_available_ims_missing_parameter():
    """ Tests the failed get request of a projects available ims with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_IMS_ENDPOINT,
        {},
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("project_id"))], 400
    )


def test_get_context_maps(config):
    """ Tests the successful get request of the context maps"""
    response = tu.send_test_request(
        constants.PROJECT_CONTEXT_MAPS_ENDPOINT,
        {**config["general"]},
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [
            ("vs30_plot", str),
            ("context_plot", str),
        ],
    )


def test_get_context_maps_missing_parameter():
    """ Tests the failed get request of the context maps with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_CONTEXT_MAPS_ENDPOINT,
        {},
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("project_id"))], 400
    )


def test_get_download_all_token(config):
    """ Tests the successful get request of the download all token"""
    response = tu.send_test_request(
        constants.PROJECT_DOWNLOAD_TOKEN_ENDPOINT,
        {"project_id": config["general"]["project_id"]},
        api="PROJECT",
    )
    tu.response_checks(
        response,
        [
            ("download_token", str),
        ],
    )


def test_get_download_all_token_missing_parameter():
    """ Tests the failed get request of the download all token with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_CONTEXT_MAPS_ENDPOINT,
        {},
        api="PROJECT",
    )
    tu.response_checks(
        response, [("error", str)], [("error", tu.MISSING_PARAM_MSG.format("project_id"))], 400
    )


def test_download_all(config):
    """ Tests the successful download all request"""
    response_project = tu.send_test_request(
        constants.PROJECT_DOWNLOAD_TOKEN_ENDPOINT,
        {"project_id": config["general"]["project_id"]},
        api="PROJECT",
    )
    response = tu.send_test_request(
        constants.PROJECT_DOWNLOAD_ENDPOINT,
        url_extension="/" + response_project.json()["download_token"],
        api="PROJECT",
    )
    tu.response_checks(response, [], [], 200, "application/zip")


def test_download_all_missing_parameter():
    """ Tests the failed download all request with missing parameters"""
    response = tu.send_test_request(
        constants.PROJECT_DOWNLOAD_ENDPOINT,
        api="PROJECT",
    )
    tu.response_checks(response, [], [], 404, "text/html")
