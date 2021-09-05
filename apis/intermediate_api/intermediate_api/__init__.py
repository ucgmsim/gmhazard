import os
import logging
import pathlib

from jose import jwt
from flask_cors import CORS
from flask import Flask

import intermediate_api.custom_sqlalchemy as cs
from intermediate_api.custom_log_handler import MultiProcessSafeTimedRotatingFileHandler

app = Flask("seistech_web")
CORS(app)

logfile_dir = pathlib.Path(__file__).resolve().parent / "logs"
logfile_dir.mkdir(parents=True, exist_ok=True)

logfile = logfile_dir / "logfile.log"
TRFhandler = MultiProcessSafeTimedRotatingFileHandler(filename=logfile, when="midnight")

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    level=logging.DEBUG,
    handlers=[TRFhandler],
)
# Only want WARNING status for requests' logging level
logging.getLogger("requests").setLevel(logging.WARNING)
# library that requests use and also set the log level
logging.getLogger("urllib3").setLevel(logging.WARNING)

TRFhandler.setLevel(logging.DEBUG)
# To prevent having a same log twice
app.logger.propagate = False
app.logger.addHandler(TRFhandler)

# Connection details for the DB
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://{0}:{1}@{2}/{3}".format(
    os.environ["DB_USERNAME"],
    os.environ["DB_PASSWORD"],
    os.environ["DB_SERVER"],
    os.environ["DB_NAME"],
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = cs.CustomSQLALchemy(app)

# For Project API with ENV
PROJECT_API_BASE = os.environ["PROJECT_API_BASE"]

# Generate the projectAPI token
PROJECT_API_TOKEN = "Bearer {}".format(
    jwt.encode({"env": os.environ["ENV"]}, os.environ["PROJECT_API_SECRET"], algorithm="HS256")
)

# See Circular Import section on here for some attempt at justification of this
# https://flask.palletsprojects.com/en/1.1.x/patterns/packages/
from intermediate_api.api import core_api, project_api, intermediate_api
