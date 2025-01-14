# Template Application Flask

## Overview

This is a template application that can be used to quickly create an API using Python and the Flask framework. This template includes a number of already implemented features and modules, including:

* Python/Flask-based API that writes to a database using API key authentication with example endpoints
* PostgreSQL database + Alembic migrations configured for updating the database when the SQLAlchemy database models are updated
* Thorough formatting & linting tools
* Logging, with formatting in both human-readable and JSON formats
* Backend script that generates a CSV locally or on S3 with proper credentials
* Ability to run the various utility scripts inside or outside of Docker
* Restructured and improved API request and response error handling which gives more details than the out-of-the-box approach for both Connexion and Pydantic
* Easy environment variable configuration for local development using a `local.env` file

The template application is intended to work with the infrastructure from [template-infra](https://github.com/navapbc/template-infra).

## Installation

To get started using the template application on your project:

1. [Install the nava-platform tool](https://github.com/navapbc/platform-cli).
2. Install template by running in your project's root:
    ```sh
    nava-platform app install --template-uri https://github.com/navapbc/template-application-flask . <APP_NAME>
    ```
3. Follow the steps in `/docs/<APP_NAME>/getting-started.md` to set up the application locally.
4. Optional, if using the Platform infrastructure template: [Follow the steps in the `template-infra` README](https://github.com/navapbc/template-infra#installation) to set up the various pieces of your infrastructure.

## Note on memory usage

If you are using [template-infra](https://github.com/navapbc/template-infra),
you may want to increase the [default
memory](https://github.com/navapbc/template-infra/blob/main/infra/modules/service/variables.tf#L33)
allocated to the ECS service to 2048 Mb (2 Gb) to avoid the gunicorn workers
running out of memory. This is because the application is currently configured
to create multiple workers based on the number of virtual CPUs available, which
can take up more memory (see `/<APP_NAME>/gunicorn.conf.py`).
