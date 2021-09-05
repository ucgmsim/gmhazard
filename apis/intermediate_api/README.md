# SeisTech - Intermediate API

## Contents

- [Requirements](#requirements)
- [Intermediate API](#intermediate-api)

## Requirements

- Python 3.6+
- Environment variables in one of the following options:
  - Set environment variables within Pycharm's run configurations.
  - Update `~/.bahsrc`

## Intermediate API

Intermediate API is an extra layer sitting in between the Frontend and the Core/Project API.

Main tasks with the Intermediate API

1. Forward requests/responses between the Frontend and Core/Project APIs.
2. Communicate with the database.
3. Communicate with Auth0.

### Environment variables

Add the following code to `~/.bashrc` or update Pycharm's run configurations.

```bash
# For Intermediate API
export ENV=
# Check Auth0's APIs - Custom API documents
export API_AUDIENCE=
export ALGORITHMS=
# Secret key
# Check https://pyjwt.readthedocs.io/en/stable/
export CORE_API_SECRET=
export PROJECT_API_SECRET=
# Port number for Intermediate API
export INTER_PORT=
# Number of Processes for Intermediate API
export N_PROCS=
# Target URL for Core and Project API
export CORE_API_BASE=
export PROJECT_API_BASE=

# To connect MariaDB from Intermediate API
export DB_USERNAME=
export DB_PASSWORD=
export DB_SERVER="127.0.0.1:3306"
export DB_NAME=

# For Auth0 Management API - To pull existing users.
# Check Auth0's Applications - Machine to Machine documents
export AUTH0_CLIENT_ID=
export AUTH0_CLIENT_SECRET=
export AUTH0_AUDIENCE=
export AUTH0_GRANT_TYPE=
export AUTH0_DOMAIN=
```
