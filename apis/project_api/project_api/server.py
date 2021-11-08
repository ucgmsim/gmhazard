import os
import logging
from functools import wraps
from pathlib import Path

import flask
from jose import jwt

from gmhazard_utils import MultiProcessSafeTimedRotatingFileHandler

app = flask.Flask("project_api")

logfile = os.path.join(os.path.dirname(__file__), "logs/logfile.log")
os.makedirs(os.path.dirname(logfile), exist_ok=True)

TRFhandler = MultiProcessSafeTimedRotatingFileHandler(filename=logfile, when="midnight")

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    level=logging.DEBUG,
    handlers=[TRFhandler],
)

TRFhandler.setLevel(logging.DEBUG)
# To prevent having a same log twice
app.logger.propagate = False
app.logger.addHandler(TRFhandler)
logging.getLogger("matplotlib").setLevel(logging.ERROR)

DOWNLOAD_URL_SECRET_KEY = os.getenv("PROJECT_API_DOWNLOAD_URL_SECRET_KEY")
DOWNLOAD_URL_VALID_FOR = 24 * 60
PROJECT_API_SECRET_KEY = os.getenv("PROJECT_API_SECRET")
BASE_PROJECTS_DIR = Path(os.getenv("BASE_PROJECTS_DIR"))

# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = flask.jsonify(ex.error)
    response.status_code = ex.status_code
    return response


# Format error response and append status code
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = flask.request.headers.get("Authorization", None)
    access_level = flask.request.headers.get("Access-Level", "public")
    if not auth:
        raise AuthError(
            {
                "code": "authorization_header_missing",
                "description": "Authorization header is expected",
            },
            401,
        )

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must start with" " Bearer",
            },
            401,
        )
    elif len(parts) == 1:
        raise AuthError(
            {"code": "invalid_header", "description": "Token not found"}, 401
        )
    elif len(parts) > 2:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must be" " Bearer token",
            },
            401,
        )

    token = parts[1]
    return token, access_level


def requires_auth(f):
    """Determines if the Access Token is valid"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token, access_level = get_token_auth_header()
        try:
            jwt.decode(token, PROJECT_API_SECRET_KEY)
        except jwt.ExpiredSignatureError:
            raise AuthError(
                {"code": "token_expired", "description": "token is expired"}, 401
            )
        except Exception:
            raise AuthError(
                {
                    "code": "invalid_header",
                    "description": "Unable to parse authentication" " token.",
                },
                401,
            )
        return f(*args, **kwargs)

    return decorated


# Add the endpoints
from project_api.api import disagg
from project_api.api import gms
from project_api.api import hazard
from project_api.api import project
from project_api.api import uhs
from project_api.api import scenario
