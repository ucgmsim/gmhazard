# SeisTech - Frontend

## Contents

- [Naming](#naming)
- [Overview](#overview)
- [Requirements](#requirements)
- [Running locally](#running-locally)
- [Deploying to AWS](#deploying-to-aws)

## Naming

- **Filename** : PascalCase (ex: SiteSelection.js, SiteSelectionVS30.js) except index files (ex: index.js, index.html, index.css...)
- **Variables & Functions** : camelCase (ex: siteSelectionLng, siteSelectionLat) except the function is used to render a component (ex: HazardCurveSection.js)
- **HTML Class/ID Names** : All lower case and separate with a hyphen (ex:hi-my-name-is-tom)

## Overview

This is a React/javascript SPA, using Auth0 authentication, talking to a python flask API, running on a Linux host.

## Requirements

- Node v12
- You will need a `.env.dev` file with the following environment variables.
  (Please contact **Tom** to get environment variables.)
  - REACT_APP_INTERMEDIATE_API_URL=
  - REACT_APP_DEFAULT_LAT=-43.5381
  - REACT_APP_DEFAULT_LNG=172.6474
  - REACT_APP_ENV=DEV
  - REACT_APP_MAP_BOX_TOKEN=
  - REACT_APP_AUTH0_DOMAIN=
  - REACT_APP_AUTH0_CLIENTID=
  - REACT_APP_AUTH0_AUDIENCE=

#### To run Frontend: `npm run start:dev`

## Running locally

Open a terminal to do the following steps

1. Change the directory to frontend

```shell
cd {seistech_psha_frontend_directory}/frontend
```

2. Install packages

```shell
npm install
```

3. Start an app

```shell
npm run start:dev
```

**To achieve this, you need the following file `.env.dev`**

Please check **Requirements** above.

## Deploying to AWS

Under a directory called `seistech_psha_frontend`, there is ith a directory called `docker`.

There are three directories, `master_dev`, `master_ea` and `master_test`.

Each directory has a different setting with `docker-compose.yml` file.

It also includes a shell script called `Dockerise.sh` in a `docker` directory. By running this shell script inside EC2, it will automatically pull the latest version (Frontend & Intermediate API) from the repo, create Docker images then run them. To do so, change the directory to either `master_dev` or `master_ea` as `master_test` is uesd by Jenkins, then type the following cmd.

```cmd
../Dockerise.sh {master_dev or master_ea} {master_dev or master_ea}
```

The first parameter will be added to the docker image to tell which images belong to `DEV` and `EA` version of SeisTech.

The second parameter is the target branch which tells EC2 to switch to the target branch then create docker images based on the latest information. This parameter is required for Jenkins so it can switch the branch to the PR's branch.
