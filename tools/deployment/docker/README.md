# GMHazard - Docker

## Contents

- [Docker](#docker)
- [Requirements](#requirements)

## Docker

Create images for the following applications:

1. Frontend application
2. Python Flask API - Intermediate API
3. MariaDB

We are using AWS as our cloud service with Docker to solve any potential compatibility issues. If you are planning to use those applications locally, you do not need to do any of those steps. This document is more for deployment, not running locally.

## Requirements

1. Docker
   Tested on Docker version 19.03.12
2. Docker-compose
   Tested on docker-compose version 1.26.2
3. Environment variables for docker-compose
   `.env` must be in the same directory with `docker-compose.yml`.

**`.env` for DEV**

```env
# For Intermediate API
AUTH0_DOMAIN_DEV=
API_AUDIENCE_DEV=
ALGORITHMS_DEV=
# For CoreAPI
CORE_API_SECRET_DEV=
# For ProjectAPI
PROJECT_API_SECRET_DEV=
DOWNLOAD_URL_SECRET_KEY_CORE_API_DEV=
DOWNLOAD_URL_SECRET_KEY_PROJECT_API_DEV=
CORE_API_BASE_DEV=
PROJECT_API_BASE_DEV=
INTER_API_PORT_DEV=
N_PROCS_DEV=

# To connect MariaDB from Intermediate API DEV
DB_USERNAME_DEV=
DB_PASSWORD_DEV=
DB_PORT_DEV=
DB_NAME_DEV=

# For MariaDB DEV
DEV_DB_PORT=
DEV_MYSQL_DATABASE=
DEV_MYSQL_USER=
DEV_MYSQL_PASSWORD=
DEV_MYSQL_ROOT_PASSWORD=

# For Auth0 Management API
AUTH0_CLIENT_ID_DEV=
AUTH0_CLIENT_SECRET_DEV=
AUTH0_AUDIENCE_DEV=
AUTH0_GRANT_TYPE_DEV=

# Slack SDK
SLACK_TOKEN_DEV=
SLACK_CHANNEL_DEV=

# For Frontend
BASE_URL_DEV=
DEFAULT_ANNUAL_EXCEEDANCE_RATE=0.013862943619741008
DEFAULT_LAT=-43.5381
DEFAULT_LNG=172.6474
FRONT_END_PORT_DEV=

# From Dockerise.sh
BUILD_DATE_DEV=${BUILD_DATE_DEV}
GIT_SHA_DEV=${GIT_SHA_DEV}

# AUTH0
REACT_APP_AUTH0_DOMAIN_DEV=
REACT_APP_AUTH0_CLIENTID_DEV=
REACT_APP_AUTH0_AUDIENCE_DEV=

# MapBox

REACT_APP_MAP_BOX_TOKEN_DEV=
```
