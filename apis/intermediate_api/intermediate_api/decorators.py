import os
import json
import traceback
from functools import wraps

import flask
import sqlalchemy.exc as sql_exc
from jose import jwt
from six.moves.urllib.request import urlopen
from flask import _request_ctx_stack

from intermediate_api import app
import intermediate_api.auth0 as auth0
import intermediate_api.utils as utils
import intermediate_api.constants as const


ALGORITHMS = os.environ["ALGORITHMS"]
API_AUDIENCE = os.environ["API_AUDIENCE"]


def get_authentication(f):
    """Determines if the Access Token is valid"""

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = auth0.get_token_auth_header()
            json_url = urlopen(
                "https://" + auth0.AUTH0_DOMAIN + "/.well-known/jwks.json"
            )
            jwks = json.loads(json_url.read())
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
            if rsa_key:
                try:
                    payload = jwt.decode(
                        token,
                        rsa_key,
                        algorithms=ALGORITHMS,
                        audience=API_AUDIENCE,
                        issuer="https://" + auth0.AUTH0_DOMAIN + "/",
                    )
                except jwt.ExpiredSignatureError:
                    raise auth0.AuthError(
                        {"code": "token_expired", "description": "token is expired"},
                        const.UNAUTHORIZED_CODE,
                    )
                except jwt.JWTClaimsError:
                    raise auth0.AuthError(
                        {
                            "code": "invalid_claims",
                            "description": "incorrect claims,"
                            "please check the audience and issuer",
                        },
                        const.UNAUTHORIZED_CODE,
                    )
                except Exception:
                    raise auth0.AuthError(
                        {
                            "code": "invalid_header",
                            "description": "Unable to parse authentication" " token.",
                        },
                        const.UNAUTHORIZED_CODE,
                    )

                _request_ctx_stack.top.current_user = payload
                return f(*args, **kwargs, is_authenticated=True)
        except:
            return f(*args, **kwargs, is_authenticated=False)

    return decorated


def endpoint_exception_handler(f):
    """Handle general exceptions with DB
    E.g., DB is reachable, Table exists etc...
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        # https://docs.sqlalchemy.org/en/13/errors.html#dbapi-errors
        except sql_exc.OperationalError as oe:
            # Most likely the database connection being dropped, or not being able to connect
            utils.post_err_on_slack(
                flask.request.base_url, str(oe), const.SERVICE_UNAVAILABLE_CODE,
            )
            return flask.Response(status=const.SERVICE_UNAVAILABLE_CODE)
        except sql_exc.ProgrammingError as pe:
            # Most likely a table does not exist or invalid syntax
            utils.post_err_on_slack(
                flask.request.base_url, str(pe), const.BAD_REQUEST_CODE,
            )
            return flask.Response(status=const.BAD_REQUEST_CODE)
        except Exception as e:
            # Traceback is too long, cannot post to Slack
            app.logger.error(traceback.format_exc())
            utils.post_err_on_slack(
                flask.request.base_url, str(e), const.INTERNAL_SERVER_ERROR_CODE
            )
            return flask.Response(status=const.INTERNAL_SERVER_ERROR_CODE)

    return decorated
