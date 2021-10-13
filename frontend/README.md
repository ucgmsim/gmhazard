# GMHazard - Frontend

## Contents

- [Naming](#naming)
- [Overview](#overview)
- [Requirements](#requirements)
- [Running locally](#running-locally)
- [Using Docker](#using-docker)

## Naming

- **Filename** : PascalCase (ex: SiteSelection.js, SiteSelectionVS30.js) except index files (ex: index.js, index.html, index.css...)
- **Variables & Functions** : camelCase (ex: siteSelectionLng, siteSelectionLat) except the function is used to render a component (ex: HazardCurveSection.js)
- **HTML Class/ID Names** : All lower case and separate with a hyphen (ex:hi-my-name-is-tom)

## Overview

This is a React/Javascript SPA, using Auth0 authentication, talking to Python Flask APIs, running on a Linux host.

## Requirements

- Node v12
- `.env.dev` with the following environment variables for development version.
  - REACT_APP_INTERMEDIATE_API_URL=
  - REACT_APP_ENV=DEV
  - REACT_APP_MAP_BOX_TOKEN= Your own MapBox public/private token
  - REACT_APP_AUTH0_DOMAIN= Your own Auth0 application information
  - REACT_APP_AUTH0_CLIENTID=
  - REACT_APP_AUTH0_AUDIENCE=
- Optional environment variables so don't have to manually type coordinates on re-render.
  - REACT_APP_DEFAULT_LAT=-43.5381
  - REACT_APP_DEFAULT_LNG=172.6474

#### To run Frontend: `npm run start:dev`

## Running locally

Open a terminal to do the following steps

1. Change the directory to frontend

```shell
cd /your_path/gmhazard/frontend
```

2. Install packages

```shell
npm install
```

3. Start an app

```shell
npm run start:dev
```

## Using Docker

Under a directory called `docker`.

There are three directories, `develop`, `early_access` and `test`.

- `develop` -> This is for the development version of the frontend.
- `early_access` -> This is the early access version of the frontend. Similar to the development version but aim to be more stable.
- `test` -> This is designed for test purposes with Selenium. (To be implemented.)

Each directory has a different setting with `docker-compose.yml` file.

It also includes a shell script called `Dockerise.sh` in the `docker` directory. By running this shell script, it will automatically pull the latest version (Frontend & Intermediate API) from the repo, create Docker images then run them as containers. To do so, change the directory to either `develop` or `early_access`.

```cmd
../Dockerise.sh {develop or early_access}
```

###### `test` directory will be uesd by Jenkins.
