import os
import hashlib
import logging
import traceback
from typing import List, Iterable, Tuple, Dict, Optional, Union, Type
from datetime import datetime
from functools import wraps

import git
import flask
import itsdangerous
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from itsdangerous.url_safe import URLSafeTimedSerializer

import gmhazard_calc as sc

SALT = os.environ["SALT"]
DOWNLOAD_URL_VALID_FOR = 24 * 60 * 60


class MissingKeyError(Exception):
    def __init__(self, key):
        self.error_code = 400
        self.error_msg = f"Request is missing parameter: {key}"


class ExpiredTokenError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


def endpoint_exception_handling(app):
    def endpoint_exception_handling_decorator(f):
        """Handling exception for endpoints"""

        @wraps(f)
        def decorated(*args, **kwargs):
            request_url = flask.request.base_url
            request_args = flask.request.args.to_dict()

            if flask.request.method == "POST":
                request_args = flask.request.data.decode()

            try:
                return f(*args, **kwargs)

            except MissingKeyError as ex:
                app.logger.error(ex.error_msg, exc_info=True)
                return flask.jsonify({"error": ex.error_msg}), ex.error_code
            except ValueError as ve:
                error_msg = str(ve)
                app.logger.error(error_msg, exc_info=True)
                return (
                    flask.jsonify({"error": error_msg}),
                    400,
                )
            except FileNotFoundError as ex:
                error_msg = f"Result file {ex.filename} does not exist."
                error_code = 404
                app.logger.error(error_msg + f" Error message:{traceback.format_exc()}")
                post_err_on_slack(
                    request_url,
                    request_args,
                    error_msg,
                    error_code,
                    traceback.format_exc(),
                    app,
                )
                return flask.jsonify({"error": error_msg}), error_code
            except Exception as e:
                error_msg = str(e)
                error_code = 500
                app.logger.error(error_msg, exc_info=True)
                post_err_on_slack(
                    request_url,
                    request_args,
                    error_msg,
                    error_code,
                    traceback.format_exc(),
                    app,
                )
                return flask.jsonify({"error": error_msg}), error_code

        return decorated

    return endpoint_exception_handling_decorator


def add_metadata_header(
    csv_ffp: str,
    ensemble: sc.gm_data.Ensemble,
    site_info: sc.site.SiteInfo,
    extra_metadata: str = None,
) -> None:
    """Adds a generic metadata header to the specified csv file

    Note: This has to be called before the actual data is written to the
    csv file, since it is at the top of the file. This means that this function
    will create/overwrite the specified file.

    Parameters
    ----------
    csv_ffp: str
        File path
    ensemble: Ensemble
        The ensemble for which the csv file contains data
    site_info: SiteInfo
        The site_info for which the csv file contains data
    extra_metadata: str
        Other extra metadata to also include in the header
    """
    metadata_header = (
        f"ensemble_id: {ensemble.name}, station: {site_info.station_name}, "
        f"lon: {site_info.lon}, lat: {site_info.lat}, vs30: {site_info.vs30}\n"
    )

    with open(csv_ffp, "w") as f:
        f.write(metadata_header)

        if extra_metadata is not None:
            f.write(extra_metadata)

        f.write("\n")


def get_check_keys(
    data_dict: Dict,
    keys: Iterable[Union[str, Tuple[str, Type], Tuple[str, Type, any]]],
    optional_keys: Optional[
        Iterable[Union[str, Tuple[str, Type], Tuple[str, Type, any]]]
    ] = None,
) -> Tuple[List[str], Dict[str, object]]:
    """Retrieves the specified keys from the data dict, throws a
    MissingKey exception if one of the keys does not have a value.

    If a type is specified with a key (as a tuple of [key, type]) then the
    value is also converted to the specified type

    If a default is specified with a key and type (as a tuple of [key, type, default]) then the
    value is also converted to the given type and if not specified then that default value is used
    """
    values = []
    for key_val in keys:
        # Check if a type is specified with the key
        if isinstance(key_val, tuple):
            cur_key, cur_type = key_val
        else:
            cur_key, cur_type = key_val, None

        value = data_dict.get(cur_key)
        if value is None:
            raise MissingKeyError(cur_key)

        # Perform a type conversion if one was given & append value
        values.append(value if cur_type is None else cur_type(value))

    optional_values_dict = {}
    if optional_keys is not None:
        for key_val in optional_keys:
            # Check if a type is specified with the key
            if isinstance(key_val, tuple):
                cur_key, cur_type, cur_default = (
                    key_val if len(key_val) == 3 else (*key_val, None)
                )
            else:
                cur_key, cur_type, cur_default = key_val, None, None

            value = data_dict.get(cur_key, cur_default)

            # Perform a type conversion if one was specified
            if value is not cur_default and cur_type is not None:
                value = cur_type(value)

            optional_values_dict[cur_key] = value

    return values, optional_values_dict


def get_download_token(params: Dict[str, object], secret_key: str):
    """Creates a temporary url for downloading of data

    All params specified are encoded into the url and can be
    retrieved when the urls is hit"""
    s = URLSafeTimedSerializer(secret_key=secret_key, salt=SALT)
    token = s.dumps(params)

    return token


def get_token_payload(token: str, secret_key: str):
    """Retrieves the parameters from an encoded url"""
    s = URLSafeTimedSerializer(secret_key=secret_key, salt=SALT)

    try:
        payload = s.loads(token, max_age=DOWNLOAD_URL_VALID_FOR)
    except itsdangerous.exc.SignatureExpired as e:
        raise ExpiredTokenError()
    except Exception as e:
        raise InvalidTokenError()

    return payload


def get_cache_key(type: str, logger: logging.Logger = None, **kwargs):
    """Computes the cache for the given parameters"""
    if logger is not None:
        logger.debug(f"Generating cache with key-value pairs: {kwargs}")

    return hashlib.sha256(
        f"{type}-{'-'.join(list(kwargs.values()))}".encode()
    ).hexdigest()


def get_repo_version():
    """Gets the current commit hash"""
    logging.disable(logging.ERROR)
    repo = git.Repo(search_parent_directories=True)
    logging.disable(logging.NOTSET)

    return repo.head.object.hexsha


class BaseCacheData:
    """Base cache that contains common values,
    should not be instantiated, only use as base class"""

    def __init__(self, ensemble: sc.gm_data.Ensemble, site_info: sc.site.SiteInfo):
        self.ensemble = ensemble
        self.site_info = site_info


def post_err_on_slack(
    request_url: str,
    request_args: Dict,
    error_msg: str,
    error_code: int,
    traceback_msg: str,
    app: object,
):
    """Posts a message to Slack to notify that
    an error occurred in Core and Project API

    Parameters
    ----------
    request_url: str
    request_args: Dict
    error_msg: str
    error_code: int
    traceback_msg: str
        To tell where the error occurred
    app: object
        Flask app
    """
    # Bot's token
    client = WebClient(token=os.getenv("SLACK_TOKEN"))
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        client.chat_postMessage(
            channel=os.getenv("SLACK_CHANNEL"),
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
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Detailed message:\n{traceback_msg}",
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"Request URL: {request_url}"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"Request args: {request_args}"},
                },
                {"type": "divider"},
            ],
        )
    except SlackApiError as e:
        app.logger.error(f"Slack WebClient failed with: {e.response.get('error')}")
