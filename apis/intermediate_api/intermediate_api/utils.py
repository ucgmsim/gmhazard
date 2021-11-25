import os
import requests
from datetime import datetime

import itsdangerous
import numpy as np
import flask
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from itsdangerous.url_safe import URLSafeTimedSerializer

from intermediate_api import app
import intermediate_api.db as db
import intermediate_api.decorators as decorators

DOWNLOAD_URL_SECRET_KEY_CORE = os.environ["DOWNLOAD_URL_SECRET_KEY_CORE_API"]
DOWNLOAD_URL_SECRET_KEY_PROJECT = os.environ["DOWNLOAD_URL_SECRET_KEY_PROJECT_API"]
DOWNLOAD_URL_VALID_FOR = 24 * 60 * 60
SALT = os.environ["SALT"]


class ExpiredTokenError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


def _get_token_payload(token: str, secret_key: str):
    """Retrieves the parameters from an encoded url"""
    s = URLSafeTimedSerializer(secret_key=secret_key, salt=SALT)
    try:
        payload = s.loads(token, max_age=DOWNLOAD_URL_VALID_FOR)
    except itsdangerous.exc.SignatureExpired as e:
        raise ExpiredTokenError()
    except Exception as e:
        raise InvalidTokenError()
    return payload


@decorators.endpoint_exception_handler
def proxy_to_api(
    request,
    route,
    methods,
    api_destination: str,
    api_token: str,
    data: dict = None,
    user_id: str = None,
    action: str = None,
    content_type: str = "application/json",
):
    """IntermediateAPI - Handling the communication between Frontend and Core/Project API.
    Parameters
    ----------
    request: object
    route: string
        URL path to Core/Project API
    methods: string
        GET/POST methods
    api_destination: string
        To determine the destination, either the CoreAPI or ProjectAPI
    api_token: string
        Special token to pass the CoreAPI/ProjectAPI's authorization check
    data: dictionary
        BODY to send, instead of decoding inside this function, get it as a parameter.
    user_id: string
        Determining the user
    action: string
        To find out what user is performing
    content_type: string
        Entry-header field indicates the media type of the entity-body sent to the recipient.
        The default media type is application/json
    """
    if action and user_id:
        if "Download" in action:
            secret_key = (
                DOWNLOAD_URL_SECRET_KEY_CORE
                if "psha-core" in api_destination or "10022" in api_destination
                else DOWNLOAD_URL_SECRET_KEY_PROJECT
            )

            decoded_payloads = {
                key: _get_token_payload(value, secret_key)
                for key, value in request.args.to_dict().items()
            }

            # Only user's inputs
            for payload in decoded_payloads.values():
                db.write_request_details(
                    user_id, action, {key: value for key, value in payload.items()},
                )

        else:
            db.write_request_details(
                user_id,
                action,
                {
                    key: value
                    for key, value in request.args.to_dict().items()
                    if "token" not in key
                },
            )

    if methods == "POST":
        resp = requests.post(
            api_destination + route, data=data, headers={"Authorization": api_token},
        )

    elif methods == "GET":
        querystring = request.query_string.decode("utf-8")

        if querystring:
            querystring = "?" + querystring

        resp = requests.get(
            api_destination + route + querystring, headers={"Authorization": api_token},
        )

    return flask.Response(resp.content, resp.status_code, mimetype=content_type)


def run_project_crosscheck(db_user_projects, public_projects, project_api_projects):
    """Compute cross-check of allowed projects for the specified user
    with the verified projects(one with values that can be used) from the projectAPI

    It finds allowed private projects from the Users_Permission table.
    Then check these allowed projects + all public projects(From Project table),
    with verified projects from Project API to check
    whether they are valid projects to perform/use

    For instance, gnzl is in the DB but some issues found and disabled from ProjectAPI,
    then the user will not see gnzl until we fix any issues.

    Parameters
    ----------
    db_user_projects: Dictionary
        All allowed private projects for the specified user

    public_projects: Dictionary
        All Public projects from the Project table

    project_api_projects: Array
        All projects from the project API

    Returns
    -------
    dictionary in the form of
    {
        project_id: project_name
    }
    """
    filtered_project_dict = {}

    for project_id in project_api_projects:
        if project_id in db_user_projects:
            filtered_project_dict[project_id] = db_user_projects[project_id]
        elif project_id in public_projects:
            filtered_project_dict[project_id] = public_projects[project_id]

    return filtered_project_dict


def calc_cdf(weights, x_values):
    """Sorting two corresponding arrays in ascending order of
    element in x_values(Mw or Rrup)

    Parameters
    ----------
    weights: array
        contribution_df: contribution
    x_values: array
        For rrup or magnitude
    """
    sort_ind = np.argsort(np.array(x_values))

    x_values = np.array(x_values)[sort_ind]
    weights = np.array(weights)[sort_ind]

    return x_values, np.cumsum(weights)


def post_err_on_slack(request_url: str, error_msg: str, error_code: int):
    """Posts a message to Slack to notify that
    an error occurred in Intermediate API

    Parameters
    ----------
    request_url: str
    error_msg: str
    error_code: int
    """
    # Bot's token
    client = WebClient(token=os.environ["SLACK_TOKEN"])
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        client.chat_postMessage(
            channel=os.environ["SLACK_CHANNEL"],
            text="TO_AVOID_WARNING_MESSAGE",
            blocks=[
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"Error occurred at {date}"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"Error message: {error_msg}"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"Error code: {error_code}"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"Request URL: {request_url}"},
                },
            ],
        )
    except SlackApiError as e:
        app.logger.error(f"Slack WebClient failed with: {e.response.get('error')}")
