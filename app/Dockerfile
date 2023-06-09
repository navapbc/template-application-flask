# Use the official python3 image based on Debian 11 "Bullseye".
# https://hub.docker.com/_/python

# The build stage that will be used to deploy to the various environments
# needs to be called `release` in order to integrate with the repo's
# top-level Makefile
FROM python:3-slim AS base

# Install poetry, the package manager.
# https://python-poetry.org
RUN pip install --no-cache-dir poetry==1.5

RUN apt-get update \
    # Install security updates
    # https://pythonspeed.com/articles/security-updates-in-docker/
    && apt-get upgrade --yes \
    && apt-get install --no-install-recommends --yes \
    build-essential \
    libpq-dev \
    postgresql \
    # Reduce the image size by clear apt cached lists
    # Complies with https://github.com/codacy/codacy-hadolint/blob/master/codacy-hadolint/docs/description/DL3009.md
    && rm -fr /var/lib/apt/lists/* \
    && rm /etc/ssl/private/ssl-cert-snakeoil.key

ARG RUN_UID
ARG RUN_USER

# The following logic creates the RUN_USER home directory and the directory where
# we will be storing the application in the image. This runs when the user is not root
RUN : "${RUN_USER:?RUN_USER and RUN_UID need to be set and non-empty.}" && \
    [ "${RUN_USER}" = "root" ] || \
    (useradd --create-home --create --user-group --home "/home/${RUN_USER}" --uid ${RUN_UID} "${RUN_USER}" \
    && mkdir /app \
    && chown -R ${RUN_UID} "/home/${RUN_USER}" /app)

#-----------
# Dev image
#-----------

FROM base AS dev
ARG RUN_USER
USER ${RUN_USER}
WORKDIR /app

COPY pyproject.toml poetry.lock ./
# Explicitly create a new virtualenv to avoid getting overridden by mounted .venv folders
RUN poetry config virtualenvs.in-project false && poetry env use python
# Install all dependencies including dev dependencies
RUN poetry install --no-root --with dev

COPY . /app

# Set the host to 0.0.0.0 to make the server available external
# to the Docker container that it's running in.
ENV HOST=0.0.0.0

# Run the application.
CMD ["poetry", "run", "python", "-m", "src"]

#---------------
# Release Build
#---------------

FROM base AS release-build

WORKDIR /app

COPY . /app

# Remove any existing virtual environments that might exist. This
# might happen if testing out building the release image from a local machine
# that has a virtual environment within the project app folder.
RUN rm -fr /app/.venv

# Set virtualenv location to be in project to be easy to find
# This will create a virtualenv in /app/.venv/
# See https://python-poetry.org/docs/configuration/#virtualenvsin-project
# See https://python-poetry.org/docs/configuration/#using-environment-variables
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install production runtime dependencies only
RUN poetry install --no-root --only main

# Build the application binary (python wheel) defined in pyproject.toml
# Note that this will only copy over python files, and files stated in the
# include section in pyproject.toml. Also note that if you change the name or
# version section in pyproject.toml, you will need to change the dist/... to match
# or the application will not build
RUN poetry build --format wheel && poetry run pip install 'dist/template_application_flask-0.1.0-py3-none-any.whl'


#---------------
# Release image
#---------------

FROM scratch AS release

ARG RUN_USER
USER ${RUN_USER}

# Any required files or directories will need to be explicitly copied to
# the release image
COPY --from=release-build /etc/passwd /etc/group /etc/

# This copies over the files generated in the application binary (python wheel)
# from the previous step
COPY --from=release-build /app/.venv /app/.venv

COPY --from=release-build /usr/local/bin/python* /usr/local/bin/

# Include required libs
COPY --from=release-build /usr/lib/x86_64-linux-gnu/ /usr/lib/x86_64-linux-gnu/
COPY --from=release-build /lib/* /lib/
COPY --from=release-build /usr/local/lib/ /usr/local/lib/
COPY --from=release-build /usr/local/include/python* /usr/local/include/
COPY --from=release-build /lib64/* /lib64/
COPY --from=release-build --chown=${RUN_USER} /tmp/ /tmp/

# By adding the application binary path, you can run scripts defined in the
# pyproject.toml file as a command directly
ENV PATH="/app/.venv/bin:$PATH"

# Run the application using the command defined in the scripts section
# of pyproject.toml
CMD ["app-start"]
