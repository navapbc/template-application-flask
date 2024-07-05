# Getting started

This application is dockerized. Take a look at [Dockerfile](/app/Dockerfile) to see how it works.

A very simple [docker-compose.yml](/app/docker-compose.yml) has been included to support local development and deployment. Take a look at [docker-compose.yml](/app/docker-compose.yml) for more information.

## Prerequisites

1. Install the version of Python specified in [.python-version](/app/.python-version)
   [pyenv](https://github.com/pyenv/pyenv#installation) is one popular option for installing Python,
   or [asdf](https://asdf-vm.com/).

2. After installing and activating the right version of Python, install
   [poetry](https://python-poetry.org/docs/#installation) and follow the instructions to add poetry to your path if necessary.

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. If you are using an M1 mac, you will need to install postgres as well: `brew install postgresql` (The psycopg2-binary is built from source on M1 macs which requires the postgres executable to be present)

4. You'll also need [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

## Run the application

**Note:** Run everything from within the `/app` folder:

1. Run `make init start` to build the image and start the container.
2. Navigate to `localhost:8080/docs` to access the Swagger UI.
3. Run `make run-logs` to see the logs of the running API container
4. Run `make stop` when you are done to stop the container.

## (Optional) Configure local secrets

If you need to pass secrets to the application via environment variables, copy the provided [/app/docker-compose.override.yml.example](/docker-compose.override.yml.example) to `/app/docker-compose.override.yml`. Then create an `/app/.env` file with your secrets. The override will pass this file to the Docker container with your application.

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
touch app/.env
```

## Next steps

Now that you're up and running, read the [application docs](README.md) to familiarize yourself with the application.
