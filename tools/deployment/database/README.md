# GMHazard - DB

## Contents

- [Requirements](#requirements)
- [Running locally](#running-locally)
  - [MariaDB](#mariadb)
  - [Adminer](#adminer)

## Requirements

1. Docker
   Tested on Docker version 19.03.12
2. Docker-compose
   Tested on docker-compose version 1.26.2
3. `.env` with some environment variables for docker-compose

```env
MYSQL_DATABASE=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_ROOT_PASSWORD=
```

**docker-compose.yml**

```yml
# docker-compose.yml

version: "3.8"

services:
  db:
    image: mariadb
    restart: always
    ports:
      - 3306:3306
    environment:
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      # TZ is not necessary.
      - TZ=Pacific/Auckland

    # Assuming we don't mind store db_data directory in the current directory.
    # For instance, the directory could look like this (Database is a root directory)
    # Database
    # |- .env
    # |- docker-compose.yml
    # |- db_data <- this directory will be created upon using the following volumes command
    # Now we store data in this directory (externally), not inside the docker container.
    volumes:
      - ./db_data:/var/lib/mysql

  # Not necessary for AWS but is recommended for a local setup due to having DB Viewer via a web browser
  adminer:
    image: adminer
    restart: always
    ports:
      - 8080:8080

volumes:
  db_data:
```

## Running locally

### MariaDB

1. Change the directory to where this `docker-compose.yml` is. (Make sure to have `.env` in the same directory.)
2. Type one of the following commands:
   - `docker-compose up -d` -> Run images as a container in background.
   - `docker-compose up` -> Do the monitoring at the same time.
3. You can either access/check data via the browser at `localhost:8080` or via command, `mysql -h 127.0.0.1 -P 3306 -u {MYSQL_USER} -p{MYSQL_PASSWORD}.` (Space after -u but no space after -p)

#### IF THIS IS YOUR FIRST TIME SETTING UP THE DB

1. Make sure the DB is up and running
2. Type the following command within the working venv. (Python 3.6+)
   - `python /your_path_to_cloned_repo/gmhazard/apis/intermediate_api/intermediate_api/create_db.py`
3. Project table needs to be filled to use the Projects tab under the GMHazard.
   - Refer to the `create_db.py`, projects vary on their application.

This will create some initial tables for the DEV environment and Auth0 users under the application.
Please check the `create_db.py` to get further information.

#### Adminer

Adminer is for development purpose

1. Open up a browser and type `localhost:8080`
2. Put the following details:

- Username = `${MYSQL_USER}`
- Password = `${MYSQL_PASSWORD}`
- Database = `${MYSQL_DATABASE}`

### IMPORTANT - Make sure to run the DB first then run the Intermediate API as it needs to be connected to DB. If you use the `docker-compose.yml` above, no need to worry about it.
