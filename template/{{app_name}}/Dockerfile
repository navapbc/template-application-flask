# Use the official python3 image based on Debian 11 "Bullseye".
# https://hub.docker.com/_/python

# The build stage that will be used to deploy to the various environments
# needs to be called `release` in order to integrate with the repo's
# top-level Makefile
FROM python:3.14-slim AS base
# See docs for details on upgrading your Python version


RUN apt-get update \
    # Install security updates
    # https://pythonspeed.com/articles/security-updates-in-docker/
    && apt-get upgrade --yes \
    && apt-get install --no-install-recommends --yes \
    build-essential \
    libpq-dev \
    postgresql \
    wget \
    # Reduce the image size by clear apt cached lists
    # Complies with https://github.com/codacy/codacy-hadolint/blob/master/codacy-hadolint/docs/description/DL3009.md
    && rm -fr /var/lib/apt/lists/* \
    && rm /etc/ssl/private/ssl-cert-snakeoil.key

ARG RUN_UID
ARG RUN_USER

# Install UV, the package manager.
# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.11.9 /uv /uvx /bin/

# Disable dev dependencies in UV sync
ENV UV_NO_DEV=1
# Compile python to *.pyc files for performance
ENV UV_COMPILE_BYTECODE=1


# The following logic creates the RUN_USER home directory and the directory where
# we will be storing the application in the image. This runs when the user is not root
RUN : "${RUN_USER:?RUN_USER and RUN_UID need to be set and non-empty.}" && \
    [ "${RUN_USER}" = "root" ] || \
    (useradd --create-home --create --user-group --home "/home/${RUN_USER}" --uid ${RUN_UID} "${RUN_USER}" \
    && mkdir /app \
    && mkdir -p /opt/venv \
    && chown -R ${RUN_UID} "/home/${RUN_USER}" /app /opt/venv)

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY . /app

RUN uv sync --locked --no-dev

#-----------
# Dev image
#-----------

FROM base AS dev
ARG RUN_USER
USER ${RUN_USER}
WORKDIR /app

# We want dev dependencies in the dev image
ENV UV_NO_DEV=0
# In dev, prefer external venv to avoid mutating release venv
ENV VIRTUAL_ENV=/opt/venv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
# Place entry points in the environment at the front of the path
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

COPY . /app

# Install all dependencies including dev dependencies
RUN uv venv /opt/venv && uv sync --locked --all-groups


# Set the host to 0.0.0.0 to make the server available external
# to the Docker container that it's running in.
ENV HOST=0.0.0.0

# Run the application.
CMD ["flask", "--app", "src.app", "run", "--host", "0.0.0.0", "--port", "8080", "--reload"]

#---------
# Release
#---------

FROM base AS release
ARG RUN_USER

# Gunicorn requires this workaround to create writable temporary directory in
# our readonly root file system. https://github.com/aws/containers-roadmap/issues/736
RUN mkdir -p /tmp
VOLUME ["/tmp"]

# TODO(https://github.com/navapbc/template-application-flask/issues/23) Productionize the Docker image

WORKDIR /app

COPY . /app

# Remove any existing virtual environments that might exist. This
# might happen if testing out building the release image from a local machine
# that has a virtual environment within the project app folder.
RUN rm -fr /app/.venv

# Build the application binary (python wheel) defined in pyproject.toml
# Note that this will only copy over python files, and files stated in the
# include section in pyproject.toml. Also note that if you change the name or
# version section in pyproject.toml, you will need to change the dist/... to match
# or the application will not build
RUN uv build --format wheel && uv pip install 'dist/template_application_flask-0.1.0-py3-none-any.whl'

# Add project's virtual env to the PATH so we can directly run scripts from the .venv folder
# defined in pyproject.toml
ENV PATH="/app/.venv/bin:$PATH"

# Set the host to 0.0.0.0 to make the server available external
# to the Docker container that it's running in.
ENV HOST=0.0.0.0

USER ${RUN_USER}

# Run the application.
CMD ["gunicorn", "src.app:create_app()"]
