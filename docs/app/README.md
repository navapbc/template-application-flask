# Template Application Flask

# Introduction
This is the API layer of the Template Application Flask. It includes a few separate components:
- The REST API
- Backend & utility scripts

## Project Directory Structure
```
root
├── app
│   └── api
│       └── auth                Authentication code for API
│       └── db
│           └── models          DB model definitions            
│           └── migrations      DB migration configs
│               └── versions    The DB migrations
│       └── logging
│       └── route               API route definitions
│           └── handler         API route implementations
│       └── scripts             Backend scripts that run separate from the application
│       └── util                Utility methods and classes useful to most areas of the code
│
│   └── tests
│   └── local.env           Environment variable configuration for local files
│   └── Makefile            Frequently used CLI commands for docker and utilities
│   └── openapi.yml         API specification
│   └── pyproject.toml      Python project configuration file
│   └── setup.cfg           Python config for tools that don't support pyproject.toml yet
│   └── Dockerfile          Docker build file for project
│
└── docker-compose.yml  Config file for docker-compose tool, used for local development
```

# Information

* [API Technical Overview](/docs/app/technical-overview.md)
* [Database Migrations](/docs/app/database-migrations.md)
* [Formatting and Linting](/docs/app/formatting-and-linting.md)
* [Writing Tests](/docs/app/writing-tests.md)

## Some Useful Commands
`make test` will run all of the tests. Additional arguments can be passed to this command which will be passed to pytest like so: `make test args="tests/api/route -v"` which would run all tests in the route folder with verbosity increased. See the [Pytest Docs](https://docs.pytest.org/en/7.1.x/reference/reference.html#command-line-flags) for more details on CLI flags you can set.

`make clean-volumes` will spin down the docker containers + delete the volumes. This can be useful to reset your DB, or fix any bad states your local environment may have gotten into.

See the [Makefile](./app/Makefile) for a full list of commands you can run.

## Docker and Native Development
Several components like tests, linting, and scripts can be run either inside of the Docker container, or outside on your native machine.
Running in Docker is the default, but on some machines like the M1 Mac, running natively may be desirable for performance reasons.

You can switch which way many of these components are run by setting the `PY_RUN_APPROACH` env variable in your terminal.
* `export PY_RUN_APPROACH=local` will run these components natively
* `export PY_RUN_APPROACH=docker` will run these within Docker

Note that even with the native mode, many components like the DB and API will only ever run in Docker, and you should always make sure that any implementations work within docker.

Running in the native/local approach may require additional packages to be installed on your machine to get working.

## Environment Variables
Most configuration options are managed by environment variables.

Environment variables for local development are stored in the [local.env](./app/local.env) file. This file is automatically loaded when running. If running within Docker, this file is specified as an `env_file` in the [docker-compose](./docker-compose.yml) file, and loaded [by a script](./app/api/util/local.py) automatically when running most other components outside the container.

Any environment variables specified directly in the [docker-compose](./docker-compose.yml) file will take precedent over those specified in the [local.env](./app/local.env) file.

## Authentication
This API uses a very simple [ApiKey authentication approach](https://connexion.readthedocs.io/en/latest/security.html#apikey-authentication) which requires the caller to provide a static key. This is specified with the `API_AUTH_TOKEN` environment variable.
