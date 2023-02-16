# Use the official python3 image based on Debian 11 "Bullseye".
# https://hub.docker.com/_/python

# The build stage that will be used to deploy to the various environments
# This is what the other stages will call as their base
FROM python:3.11-slim-bullseye AS build

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
    (useradd -mU --home "/home/${RUN_USER}" --uid ${RUN_UID} "${RUN_USER}" \
    && mkdir /app \
    && chown -R ${RUN_UID} "/home/${RUN_USER}" /app)

USER ${RUN_USER}

#-------------------------------------------------------------------------------
# Development build environment
#-------------------------------------------------------------------------------
FROM build as dev

# Runtime arguement for what user will the bulk of this stage run as
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
CMD ["poetry", "run", "python", "-m", "api"]

#-------------------------------------------------------------------------------
# Non-development build environment
#-------------------------------------------------------------------------------
FROM build as app-build

# Runtime arguement for what user will the bulk of this stage run as
ARG RUN_USER

# In between ARG RUN_USER and USER ${RUN_USER}, the user is still root
# If there is anything that needs to be ran as root, this is the spot

# Change the user from root to ${RUN_USER}
USER ${RUN_USER}

# Set the application working directory.
WORKDIR /app

# Install dependencies
# Use a project-local virtualenv to be easy to find
ENV POETRY_VIRTUALENVS_IN_PROJECT true
COPY . /app
RUN poetry install --no-root --without dev

# Install application dependencies
# The name of the wheel file comes from pyproject.toml
RUN poetry build --format wheel && poetry run pip install 'dist/template_application_flask-0.1.0-py3-none-any.whl'

#-------------------------------------------------------------------------------
# Production Application Image only
#-------------------------------------------------------------------------------
# Now copy over just the installed components into the final image
FROM scratch as release

# Runtime arguement for what user will the bulk of this stage run as
ARG RUN_USER

# In between ARG RUN_USER and USER ${RUN_USER}, the user is still root
# If there is anything that needs to be ran as root, this is the spot

# Change the user from root to ${RUN_USER}
USER ${RUN_USER}

# Any required files or directories will need to be explicitly copied to
# the release image
COPY --from=app-build /etc/passwd /etc/group /etc/
COPY --from=app-build /app/.venv /app/.venv

COPY --from=app-build /usr/share/ca-certificates/* /usr/share/ca-certificates/
COPY --from=app-build /usr/local/bin/python* /usr/local/bin/

# Include etc files that link to /usr/local/lib/
COPY --from=app-build /etc/ld.so.conf /etc/ld.so.cache /etc/
COPY --from=app-build /etc/ld.so.conf.d/ /etc/ld.so.conf.d/

# Include required libs
COPY --from=app-build /usr/lib/x86_64-linux-gnu/ /usr/lib/x86_64-linux-gnu/
COPY --from=app-build /lib/* /lib/
COPY --from=app-build /usr/local/lib/ /usr/local/lib/
COPY --from=app-build /usr/local/include/python* /usr/local/include/
COPY --from=app-build /lib64/* /lib64/
COPY --from=app-build --chown=${RUN_USER} /tmp/ /tmp/

ENV PATH="/app/.venv/bin:$PATH"

# run the application
CMD ["run-api"]
