import os
import json
import requests
import http.client

from jose import jwt
import flask

from intermediate_api import app
import intermediate_api.utils as utils
import intermediate_api.constants as const


# To communicate with Management API
AUTH0_CLIENT_ID = os.environ["AUTH0_CLIENT_ID"]
AUTH0_CLIENT_SECRET = os.environ["AUTH0_CLIENT_SECRET"]
AUTH0_AUDIENCE = os.environ["AUTH0_AUDIENCE"]
AUTH0_GRANT_TYPE = os.environ["AUTH0_GRANT_TYPE"]
AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = flask.jsonify(ex.error)
    response.status_code = ex.status_code
    return response


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = flask.request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(
            {
                "code": "authorization_header_missing",
                "description": "Authorization header is expected",
            },
            const.UNAUTHORIZED_CODE,
        )

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must start with" " Bearer",
            },
            const.UNAUTHORIZED_CODE,
        )
    elif len(parts) == 1:
        raise AuthError(
            {"code": "invalid_header", "description": "Token not found"},
            const.UNAUTHORIZED_CODE,
        )
    elif len(parts) > 2:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must be" " Bearer token",
            },
            const.UNAUTHORIZED_CODE,
        )

    token = parts[1]
    return token


def get_user_id():
    """We are storing Auth0 id to the DB so no need any extra steps.
    Just pull sub's value in a return dictionary which is the unique user_id from Auth0
    """
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)

    user_id = unverified_claims["sub"].split("|")[1]

    return user_id


def _get_management_api_token():
    """Connect to AUTH0 Management API to get access token"""
    conn = http.client.HTTPSConnection(AUTH0_DOMAIN)

    payload = json.dumps(
        {
            "client_id": AUTH0_CLIENT_ID,
            "client_secret": AUTH0_CLIENT_SECRET,
            "audience": AUTH0_AUDIENCE,
            "grant_type": AUTH0_GRANT_TYPE,
        }
    )

    headers = {"content-type": "application/json"}

    conn.request("POST", "/oauth/token", payload, headers)

    res = conn.getresponse()
    # Convert the string dictionary to dictionary
    data = json.loads(res.read().decode("utf-8"))

    return data["access_token"]


def get_users():
    """Get all users

    Returns
    -------
    dictionary:
        In the form of
        { user_id : email | provider}
        The reason we keep both email and provider is due to preventing confusion
        Based on having the same emails but different provider
        For instance, email A with Google and email A with Auth0
    """
    try:
        resp = requests.get(
            AUTH0_AUDIENCE + "users",
            headers={"Authorization": "Bearer {}".format(_get_management_api_token())},
        )
    # https://docs.python-requests.org/en/latest/user/quickstart/#errors-and-exceptions
    except requests.exceptions.RequestException:
        error_msg = "Cannot connect to Auth0"
        utils.post_err_on_slack(
            flask.request.base_url, error_msg, const.SERVICE_UNAVAILABLE_CODE
        )
        return {"error": error_msg}, const.SERVICE_UNAVAILABLE_CODE

    user_list, user_dict = resp.json(), {}

    for user_dic in user_list:
        if "user_id" in user_dic.keys():
            temp_value = "{} | {}".format(
                user_dic["email"], user_dic["identities"][0]["provider"]
            )
            user_dict[user_dic["user_id"].split("|")[1]] = temp_value
        else:
            print(f"WARNING: No user_id found for user_dict {user_dict}")

    return user_dict, const.OK_CODE


def requires_permission(required_permission):
    """Determines if the required scope is present in the Access Token

    Parameters
    ----------
    required_permission: string
        The scope required to access the resource
    """
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)

    if unverified_claims.get("permissions"):
        token_permissions = unverified_claims["permissions"]
        return required_permission in token_permissions

    return False


def is_admin():
    return requires_permission("admin")
