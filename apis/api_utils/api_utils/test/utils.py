import os
import requests

MISSING_PARAM_MSG = "Request is missing parameter: {}"


def send_test_request(
    endpoint, parameters=None, method="GET", json=None, url_extension="", api="CORE"
):
    """Send a request to the core api with a
    given endpoint and parameters, returns the response"""
    url = f'{os.environ[api + "_API_BASE_TEST"]}{endpoint}{url_extension}'
    header = {"Authorization": "Bearer " + os.environ[api + "_API_TOKEN"]}

    if method == "GET":
        return requests.get(url, headers=header, params=parameters)
    elif method == "POST":
        return requests.post(url, headers=header, params=parameters, json=json)


def response_checks(
    response,
    type_check_list=[],
    value_check_list=[],
    response_code=200,
    content_type="application/json",
):
    """ Checks for valid response keys, types, values, response code and content type"""
    json_body = response.json() if content_type == "application/json" else ""
    assert response.status_code == response_code
    assert response.headers["Content-Type"] == content_type
    # Checks for correct types
    for key, type in type_check_list:
        # Manages depth levels of json for checking
        if isinstance(key, list):
            depth_json = json_body
            for depth in key:
                assert depth in depth_json
                depth_json = depth_json[depth]
            assert isinstance(depth_json, type)
        else:
            assert key in json_body
            assert isinstance(json_body[key], type)
    # Checks for correct values
    for key, value in value_check_list:
        # Manages depth levels of json for checking
        if isinstance(key, list):
            depth_json = json_body
            for depth in key:
                depth_json = depth_json[depth]
            assert depth_json == value
        else:
            assert json_body[key] == value


def response_user_vs30_checks(
    response_db,
    response_user,
    compare_list=[],
    response_code=200,
    content_type="application/json",
):
    """ Checks that the values between the db and user responses are different for items in the compare list"""
    json_body_db = response_db.json() if content_type == "application/json" else ""
    json_body_user = response_user.json() if content_type == "application/json" else ""
    assert response_db.status_code == response_code
    assert response_user.status_code == response_code
    assert response_db.headers["Content-Type"] == content_type
    assert response_user.headers["Content-Type"] == content_type

    # Checks for different values
    for key in compare_list:
        # Manages depth levels of json for checking
        if isinstance(key, list):
            depth_json_db = json_body_db
            depth_json_user = json_body_user
            for depth in key:
                depth_json_db = depth_json_db[depth]
                depth_json_user = depth_json_user[depth]
            assert depth_json_db != depth_json_user
        else:
            assert json_body_db[key] != json_body_user[key]
