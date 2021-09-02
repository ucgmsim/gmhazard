# SeisTech - DB

## Contents

- [Requirements](#requirements)
- [Middleware](#middleware)
- [Running locally](#running-locally)
  - [MariaDB](#mariadb)
  - [Adminer](#adminer)

## Requirements

1. Docker
   Tested on Docker version 19.03.12
2. Docker-compose
   Tested on docker-compose version 1.26.2
3. Environment variables for docker-compose

**Environment variables under ~/.bashrc**

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

  # Not necessary for AWS but your local setup due to having DB Viewer via a web browser
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
2. Type the following command:
   `docker-compose up -d`
3. You can either accese/check data via the browser at `localhost:8080` or via command, `mysql -h 127.0.0.1 -P 3306 -u {MYSQL_USER} -p{MYSQL_PASSWORD}.` (Space after -u but -p)

#### DO THIS STEP IF IT'S YOUR FIRST TIME SETTING UP THE DB

1. Open up a Terminal.
2. run script, `python create_db.py`

As our Intermediate API now tracks users' activity and to do so, we need our DB with users ID.

#### Adminer

Adminer is for development purpose

1. Open up a browser and type `localhost:8080`
2. Put the following details:

- Username = `${MYSQL_USER}`
- Password = `${MYSQL_PASSWORD}`
- Database = `${MYSQL_DATABASE}`

### IMPORTANT - Make sure to run the DB first then run the Intermediate API as it needs to be connected to DB.
