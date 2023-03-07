# Use the official python3 image based on Debian 11 "Bullseye".
# https://hub.docker.com/_/python

# The build stage that will be used to deploy to the various environments
# This is what the other stages will call as their base
FROM python:3.11-slim-bullseye AS base

# Keep container packages up-to-date.
RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
    build-essential \
    libpq-dev \
    postgresql

# Install poetry, the package manager - https://python-poetry.org
# We use --no-cache-dir here because the pip caches normally, and if
# we don't cache, it will reduce the overall image size
# The version is pinned so that there is a known good configuration
# that we have better control over vs a range that can be used
RUN pip install --no-cache-dir poetry==1.3.1

# setup user stuff
ARG RUN_UID
ARG RUN_USER

# The following logic creates the RUN_USER home directory and the directory where
# we will be storing the application in the image. This runs when the user is not root
RUN : "${RUN_USER:?RUN_USER and RUN_UID need to be set and non-empty.}" && \
    [ "${RUN_USER}" = "root" ] || \
    (useradd --create-home --create --user-group --home "/home/${RUN_USER}" --uid ${RUN_UID} "${RUN_USER}" \
    && mkdir /app \
    && chown -R ${RUN_UID} "/home/${RUN_USER}" /app)

USER ${RUN_USER}

######################
##    Dev  Image    ##
######################
FROM base as dev

# Runtime argument for what user will the bulk of this stage run as
ARG RUN_USER

# In between ARG RUN_USER and USER ${RUN_USER}, the user is still root
# If there is anything that needs to be ran as root, this is the spot

# Change the user from root to ${RUN_USER}
USER ${RUN_USER}

# Set the application working directory.
WORKDIR /app

COPY . /app
RUN poetry config virtualenvs.in-project false && poetry env use python
RUN poetry install --no-root --with dev

# Set the host to 0.0.0.0 to make the server available external
# to the Docker container that it's running in.
ENV HOST=0.0.0.0

# Install application dependencies.
# https://python-poetry.org/docs/basic-usage/#installing-dependencies
RUN poetry install

# Run the application.
CMD ["poetry", "run", "python", "-m", "src"]

#####################
## Release Builder ##
#####################
# This stage is to configure the image that will be used to copy from in
# the production stage below
FROM base as release-build

# Runtime argument for what user will the bulk of this stage run as
ARG RUN_USER

# In between ARG RUN_USER and USER ${RUN_USER}, the user is still root
# If there is anything that needs to be ran as root, this is the spot

# Change the user from root to ${RUN_USER}
USER ${RUN_USER}

# Set the application working directory.
WORKDIR /app

# Install dependencies
# Set virtualenv location to be in project to be easy to find
# This will create a virtualenv in /app/.venv/
# See https://python-poetry.org/docs/configuration/#virtualenvsin-project
# See https://python-poetry.org/docs/configuration/#using-environment-variables
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
COPY . /app

# Install application dependencies
RUN poetry install --no-root --without dev

# Build the application binary (python wheel) defined in pyproject.toml
# Note that this will only copy over python files, and files stated in the
# include section in pyproject.toml. Also note that if you change the name or
# version section in pyproject.toml, you will need to change the dist/... to match
# or the application will not build
RUN poetry build --format wheel && poetry run pip install 'dist/template_application_flask-0.1.0-py3-none-any.whl'

######################
## Production Image ##
######################
# Now copy over just the installed components into the final image
FROM scratch as release

# Runtime argument for what user will the bulk of this stage run as
ARG RUN_USER

# In between ARG RUN_USER and USER ${RUN_USER}, the user is still root
# If there is anything that needs to be ran as root, this is the spot

# Change the user from root to ${RUN_USER}
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
CMD ["run-api"]
