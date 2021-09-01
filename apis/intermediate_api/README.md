# SeisTech - Backend - API Layer

## Contents

- [Requirements](#requirements)
- [Middleware](#middleware)
- [Running locally](#running-locally)

## Requirements

Please contact **Tom** to get environment variables.

## Middleware

We run middleware simultaneously (One for DEV and another one for EA). However, you don't have to worry about this if you run it locally.

Add the following code to `~/.bashrc`

```vim
# For Intermediate API
export ENV=dev
export AUTH0_DOMAIN=
export API_AUDIENCE=
export ALGORITHMS=
export CORE_API_SECRET=
export INTER_PORT=
export N_PROCS=
export CORE_API_BASE=
export PROJECT_API_BASE=

# To connect MariaDB from Intermediate API DEV
export DB_USERNAME=
export DB_PASSWORD=
export DB_SERVER="127.0.0.1:3306"
export DB_NAME=

# For Auth0 Management API - To pull existing users.
export AUTH0_CLIENT_ID=
export AUTH0_CLIENT_SECRET=
export AUTH0_AUDIENCE=
export AUTH0_GRANT_TYPE=
```

## Running locally

Assuming we are using Core API and Project API that are hosted by UCQuakeCore1p.

Open a terminal to do the following steps

1. Create Python virtual environment first.

2. We need to install some packages for Middleware (a.k.a Intermediate API).

```shell
cd {seistech_psha_frontend_directory}/middleware/middleware
pip install -r requirements.txt
```

3. After installation is done, run the following command

```shell
python app.py
```
