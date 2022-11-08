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

To get started using the template infrastructure on your project, install the template by cloning the template repository and copying the following folders/files to your repository:

```bash
# fetch latest version of the template
git clone --single-branch --branch main --depth 1 git@github.com:navapbc/template-application-flask.git

cp -r \
  template-application-flask/.github \
  template-application-flask/bin \
  template-application-flask/docs \
  template-application-flask/app \
  template-application-flask/docker-compose.yml \
  .

# clean up the template folder
rm -fr template-application-flask
```

Now you're ready to [get started](./getting-started.md).
