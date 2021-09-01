# SeisTech - Docker

## Contents

- [Requirements](#requirements)
- [Running locally](#running-locally)

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
CORE_API_SECRET_DEV=
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
DEV_TZ=Pacific/Auckland

# For Auth0 Management API
AUTH0_CLIENT_ID_DEV=
AUTH0_CLIENT_SECRET_DEV=
AUTH0_AUDIENCE_DEV=
AUTH0_GRANT_TYPE_DEV=

# For Frontend
BASE_URL_DEV=
DEFAULT_ANNUAL_EXCEEDANCE_RATE=
DEFAULT_LAT=
DEFAULT_LNG=
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

**`.env` for EA**

```env
# For Intermediate API
AUTH0_DOMAIN_EA=
API_AUDIENCE_EA=
ALGORITHMS_EA=
CORE_API_SECRET_EA=
DOWNLOAD_URL_SECRET_KEY_CORE_API_EA=
DOWNLOAD_URL_SECRET_KEY_PROJECT_API_EA=
CORE_API_BASE_EA=
PROJECT_API_BASE_EA=
INTER_API_PORT_EA=
N_PROCS_EA=

# To connect MariaDB from Intermediate API EA
DB_USERNAME_EA=
DB_PASSWORD_EA=
DB_PORT_EA=
DB_NAME_EA=

# For MariaDB EA
EA_DB_PORT=
EA_MYSQL_DATABASE=
EA_MYSQL_USER=
EA_MYSQL_PASSWORD=
EA_MYSQL_ROOT_PASSWORD=
EA_TZ=Pacific/Auckland

# For Auth0 Management API
AUTH0_CLIENT_ID_EA=
AUTH0_CLIENT_SECRET_EA=
AUTH0_AUDIENCE_EA=
AUTH0_GRANT_TYPE_EA=

# For Frontend
BASE_URL_EA=
FRONT_END_PORT_EA=

# From Dockerise.sh
BUILD_DATE_EA=${BUILD_DATE_EA}
GIT_SHA_EA=${GIT_SHA_EA}

# AUTH0
REACT_APP_AUTH0_DOMAIN_EA=
REACT_APP_AUTH0_CLIENTID_EA=
REACT_APP_AUTH0_AUDIENCE_EA=

# MapBox

REACT_APP_MAP_BOX_TOKEN_EA=
```

## Running locally

1. Change the directory to either `docker/dev` or `docker/ea`
2. Run the following command.
   - `../Dockerise.sh master_dev master_dev` to run DEV version
   - `../Dockerise.sh master_ea master_ea` to run EA version

### What is happening by running `Dockerise.sh` - Deprecated but keep it for reference

1. Building images by typing the following command in a terminal

```shell
docker-compose build --build-arg SSH_PRIVATE_KEY="$(cat ~/.ssh/id_rsa)"
```

What it does is, it is building Docker images using docker-compose and passing `SSH_PRIVATE_KEY` as an argument so the time our docker-compose deals with dockerizing Intermediate API, it can pull data from a private repository
**If you have your GitHub SSH private key somewhere else, please update the path `~/.ssh/id_rsa`**

### Also, you may concern that we are passing the private key to the docker image.

[Multi-stage builds](https://vsupalov.com/build-docker-image-clone-private-repo-ssh-key/)

[Dockerfile](../seistech_inter_api/seistech_inter_api/Dockerfile)

This is the Dockerfile for Intermediate API, what it does is

- It creates one Docker image with this private key to cloning from the private repo.

- It creates another Docker image and copying python packages installed in an image called `intermediate` as, within `intermediate`, python has those packages installed (From private repo), then install any extra packages we need to run Intermediate API by running `pip install -r requirements.txt`

- By doing this, we do not leave our private key left in Dockerfile.

2. Running docker images!

```shell
docker-compose up -d
```

-d command for running it on the background.

It runs both Frontend & Intermediate API

3. Access via `localhost:5100`
   **Port can always be changed in the future and if so, will update this doc**
