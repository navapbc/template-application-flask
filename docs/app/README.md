# Application Documentation

## Introduction

This is the API layer. It includes a few separate components:

* The REST API
* Backend & utility scripts

## Project Directory Structure

```text
root
├── app
│   └── src
│       └── auth                Authentication code for API
│       └── db
│           └── models          DB model definitions
│           └── migrations      DB migration configs
│               └── versions    The DB migrations
│       └── logging
│       └── route               API route definitions
│           └── handler         API route implementations
│       └── scripts             Backend scripts that run separate from the application
|       └── services            Methods for service layer
│       └── util                Utility methods and classes useful to most areas of the code
│
│   └── tests
│   └── local.env           Environment variable configuration for local files
│   └── Makefile            Frequently used CLI commands for docker and utilities
│   └── pyproject.toml      Python project configuration file
│   └── Dockerfile          Docker build file for project
└── └── docker-compose.yml  Config file for docker-compose tool, used for local development
```

## Information

* [API Technical Overview](./technical-overview.md)
* [Database Management](./database/database-management.md)
* [Formatting and Linting](./formatting-and-linting.md)
* [Writing Tests](./writing-tests.md)

## Some Useful Commands

`make test` will run all of the tests. Additional arguments can be passed to this command which will be passed to pytest like so: `make test args="tests/api/route -v"` which would run all tests in the route folder with verbosity increased. See the [Pytest Docs](https://docs.pytest.org/en/7.1.x/reference/reference.html#command-line-flags) for more details on CLI flags you can set.

`make clean-volumes` will spin down the docker containers + delete the volumes. This can be useful to reset your DB, or fix any bad states your local environment may have gotten into.

See the [Makefile](/app/Makefile) for a full list of commands you can run.

## Docker and Native Development

Several components like tests, linting, and scripts can be run either inside of the Docker container, or outside on your native machine.
Running in Docker is the default, but on some machines like the M1 Mac, running natively may be desirable for performance reasons.

You can switch which way many of these components are run by setting the `PY_RUN_APPROACH` env variable in your terminal.

* `export PY_RUN_APPROACH=local` will run these components natively
* `export PY_RUN_APPROACH=docker` will run these within Docker

Note that even with the native mode, many components like the DB and API will only ever run in Docker, and you should always make sure that any implementations work within Docker.

Running in the native/local approach may require additional packages to be installed on your machine to get working.

### Running Natively

* Run `export PY_RUN_APPROACH=local`
* Run `make setup-local`
* Run `poetry install --all-extras --with dev` to keep your Poetry packages up to date
* Load environment variables from the local.env file, see below for one option.

One option for loading all of your local.env variables is to install `direnv`: https://direnv.net/
You can configure `direnv` to then load the local.env file by creating an `.envrc` file in the /app directory that looks like:

```sh
#!/bin/bash
set -o allexport
source local.env
set +o allexport

# Set any environment variable overrides you want here
#
# If you are running outside of the Docker container, the DB can
# be found on localhost:5432. Inside the container it's referenced via
# the name of the docker container.
export DB_HOST=localhost
```
And then running `direnv allow .` in the /app folder. You should see something like:
```shell
➜  template-application-flask git:(main) ✗ cd app
direnv: loading ~/workspace/template-application-flask/app/.envrc
direnv: export +API_AUTH_TOKEN +AWS_ACCESS_KEY_ID +AWS_DEFAULT_REGION +AWS_SECRET_ACCESS_KEY +DB_HOST +DB_NAME +DB_PASSWORD +DB_SCHEMA +DB_SSL_MODE +DB_USER +ENVIRONMENT +FLASK_APP +HIDE_SQL_PARAMETER_LOGS +LOG_ENABLE_AUDIT +LOG_FORMAT +PORT +PYTHONPATH
```

## Environment Variables

Most configuration options are managed by environment variables.

Environment variables for local development are stored in the [local.env](/app/local.env) file. This file is automatically loaded when running. If running within Docker, this file is specified as an `env_file` in the [docker-compose](/app/docker-compose.yml) file, and loaded [by a script](/app/src/util/local.py) automatically when running unit tests (see running natively above for other cases).

Any environment variables specified directly in the [docker-compose](/app/docker-compose.yml) file will take precedent over those specified in the [local.env](/app/local.env) file.

## Authentication

This API uses a very simple [ApiKey authentication approach](https://apiflask.com/authentication/#use-external-authentication-library) which requires the caller to provide a static key. This is specified with the `API_AUTH_TOKEN` environment variable.

## VSCode Remote Attach Container Debugging

The API can be run in debug mode that allows for remote attach debugging (currently only supported from VSCode) to the container.

- Requirements:

  - VSCode Python extension
  - Updated Poetry with the `debugpy` dev package in `pyproject.toml`

- First create a file `./vscode/launch.json` - as shown below. (Default name of `Python: Remote Attach`)

- Start the server in debug mode via `make start-debug` or `make start-debug run-logs`.
    - This will start the `main-app` service with port 5678 exposed.

- The server will start in waiting mode, waiting for you to attach the debugger (see `/src/app.py`) before continuing to run.

- Go to your VSCode debugger window and run the `Python: Remote Attach` option

- You should now be able to hit set breakpoints throughout the API

`./vscode/launch.json`:

```
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Remote Attach",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/app",
                    "remoteRoot": "."
                }
            ],
            "justMyCode": false,
        }
    ]
}
```

# Upgrading Python
Python does [yearly releases](https://devguide.python.org/versions/) for their minor versions (eg. 3.12 -> 3.13). They do not
use semvar versioning, and their [minor releases](https://devguide.python.org/developer-workflow/development-cycle/#devcycle) contain
breaking changes.

We have this environment configured to use a specific minor version of python just in case anything would break when the yearly release does occur.

We recommend as a starting point, only pin the minor versions of Python (eg. 3.12), and not the patch versions (eg. 3.12.1) as those contain bug and security fixes.
However, your project may have dependencies, or tools that rely on very specific patch versions of Python, so adjust your approach as necessary.

Along with any version upgrades, you should follow all best practices for upgrading software and test the functionality
of your system before deploying to production. It is also recommended to review the [changelog](https://docs.python.org/3/whatsnew/changelog.html)
for any breaking changes of features you may use.

## Local Development
If you run any of the python code outside of the Docker container, first upgrade your version
of Python locally. The exact way you upgrade will depend on how you originally installed Python,
but one strongly recommended approach is to use [pyenv](https://github.com/pyenv/pyenv) which allows
you to install and swap between different python versions locally.

If you run commands with Poetry, you'll also need to [configure](https://python-poetry.org/docs/managing-environments/#switching-between-environments)
it to use the approach python version.

## Dockerfile
The dockerfile that our API is built from specifies the Python version as the first step.
To upgrade this, simply change the version to the version you would like to use.

For example, to upgrade from 3.12 to 3.13, change the following line:
```dockerfile
FROM python:3.12-slim AS base
```
to
```dockerfile
FROM python:3.13-slim AS base
```

## Poetry
Adjust the pyproject.toml file line that specifies the version of Python used
to your new version. For example, to upgrade from 3.12 to 3.13, change it from:

```toml
[tool.poetry.dependencies]
python = "~3.12"
```

to
```toml
[tool.poetry.dependencies]
python = "~3.13"
```

You will then need to run `poetry lock --no-update` to make the lock file reflect this change.

## Misc
Some tools, include pyenv, reference the [.python-version](/app/.python-version) file in order to determine which
version of python should be used. Update this to the approach version as well.