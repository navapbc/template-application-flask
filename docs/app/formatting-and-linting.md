# Formatting and Linting

## Formatting

Run `make format` to run all of the formatters.

When we run migrations via alembic, we autorun the formatters on the generated files. See [alembic.ini](/app/src/db/migrations/alembic.ini) for configuration.

### Isort
[isort](https://pycqa.github.io/isort/) is used to sort our Python imports. Configuration options can be found in [pyproject.toml - tool.isort](/app/pyproject.toml)

### Black
[black](https://black.readthedocs.io/en/stable/) is used to format our Python code. Configuration options can be found in [pyproject.toml - tool.black](/app/pyproject.toml)

## Linting

Run `make lint` to run all of the linters. It's recommended you run the formatters first as they fix several linting issues automatically.

### Flake
[flake](https://flake8.pycqa.org/en/latest/) is used to validate the format of our Python code. Configuration options can be found in [setup.cfg](/app/setup.cfg).

We use two flake extensions:
* [bugbear](https://pypi.org/project/flake8-bugbear/) for finding likely bugs and design problems.
* [alfred](https://pypi.org/project/flake8-alfred/) for finding unsafe/obsolete symbols.

### Mypy
[mypy](https://mypy.readthedocs.io/en/stable/) is used to validate and enforce typechecking in python. Configuration options can be found in [pyproject.toml - tool.mypy](/app/pyproject.toml)

