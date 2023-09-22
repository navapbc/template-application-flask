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

1. Run the [download and install script](./template-only-bin/download-and-install-template.sh) in your project's root directory.

    ```bash
    curl https://raw.githubusercontent.com/navapbc/template-application-flask/main/template-only-bin/download-and-install-template.sh | bash -s
    ```

    This script will:

    1. Clone the template repository
    2. Copy the template files into your project directory
    3. Remove any files specific to the template repository.
2. Optional, if using the Platform infra template: [Follow the steps in the `template-infra` README](https://github.com/navapbc/template-infra#installation) to set up the various pieces of your infrastructure.

## Note on memory usage

If you are using [template-infra](https://github.com/navapbc/template-infra), you may want to increase the [default memory](https://github.com/navapbc/template-infra/blob/main/infra/modules/service/variables.tf#L33) allocated to the ECS service to 2048 Mb (2 Gb) to avoid the gunicorn workers running out of memory. This is because the application is currently [configured to create multiple workers](https://github.com/navapbc/template-application-flask/blob/main/app/gunicorn.conf.py#L24) based on the numberr of virtual CPUs available, which can take up more memory.

## Getting started

Now you're ready to [get started](/docs/app/getting-started.md).
