# Use the official python3 image based on Debian 11 "Bullseye".
# https://hub.docker.com/_/python

# The build stage that will be used to deploy to the various environments
# needs to be called `release` in order to integrate with the repo's
# top-level Makefile
FROM python:3-slim AS release

# Install poetry, the package manager.
# https://python-poetry.org
RUN pip install poetry

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
    build-essential \
    libpq-dev \
    postgresql

# Set the application working directory.
WORKDIR /srv

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project false && poetry env use python
RUN poetry install --no-root

# Copy application files.
COPY . /srv

# Set the host to 0.0.0.0 to make the server available external
# to the Docker container that it's running in.
ENV HOST=0.0.0.0

# Install application dependencies.
# https://python-poetry.org/docs/basic-usage/#installing-dependencies
RUN poetry install
# Run the application.
CMD ["poetry", "run", "python", "-m", "src"]
