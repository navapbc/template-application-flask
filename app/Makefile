##################################################
# Constants
##################################################

APP_NAME := main-app

# Adding this to the end of a script that outputs JSON will convert
# it to a readable format with timestamps and color-coding.
#
# Note that you can also change the LOG_FORMAT env var to switch
# between JSON & human readable format. This is left in place
# in the event JSON is output from a process we don't log.
DECODE_LOG := 2>&1 | python3 -u api/logging/util/decodelog.py

# A few commands need adjustments if they're run in CI, specify those here
# TODO - when CI gets hooked up, actually test this.
ifdef CI
 DOCKER_EXEC_ARGS := -T -e CI -e PYTEST_ADDOPTS="--color=yes"
 FLAKE8_FORMAT := '::warning file=api/%(path)s,line=%(row)d,col=%(col)d::%(path)s:%(row)d:%(col)d: %(code)s %(text)s'
 MYPY_FLAGS := --no-pretty
 MYPY_POSTPROC := | perl -pe "s/^(.+):(\d+):(\d+): error: (.*)/::warning file=api\/\1,line=\2,col=\3::\4/"
 SPECTRAL_POSTPROC := --format=text | perl -pe "s/^\/tmp\/(.+):(\d+):(\d+) (error|warning) (.*)/::warning file=api\/\1,line=\2,col=\3::\4 \5/"
else
 FLAKE8_FORMAT := default
endif

# By default, all python/poetry commands will run inside of the docker container
# if you wish to run this natively, add PY_RUN_APPROACH=local to your environment vars
# You can set this by either running `export PY_RUN_APPROACH=local` in your shell or add
# it to your ~/.zshrc file (and run `source ~/.zshrc`)
ifeq "$(PY_RUN_APPROACH)" "local"
PY_RUN_CMD := poetry run
else
PY_RUN_CMD := docker-compose run $(DOCKER_EXEC_ARGS) --rm $(APP_NAME) poetry run
endif

##################################################
# API Build & Run
##################################################

build:
	docker-compose build

start:
	docker-compose up --detach

run-logs: start
	docker-compose logs --follow --no-color $(APP_NAME)


init: build init-db

clean-volumes: ## Remove project docker volumes (which includes the DB state)
	docker-compose down --volumes

stop:
	docker-compose down

##################################################
# DB & migrations
##################################################

#########################
# DB running / setup
#########################

# Docker starts the image for the DB but it's not quite
# fully ready, so add a 5 second sleep so upgrade doesn't
# fail because the DB hasn't started yet.
init-db: start-db sleep-5 db-upgrade

start-db:
	docker-compose up --detach main-db

## Destroy current DB, setup new one
db-recreate: clean-docker-volumes init-db

#########################
# DB Migrations
#########################

alembic_config := ./api/db/migrations/alembic.ini
alembic_cmd := $(PY_RUN_CMD) alembic --config $(alembic_config)

db-upgrade: ## Apply pending migrations to db
	$(PY_RUN_CMD) db-migrate-up

db-downgrade: ## Rollback last migration in db
	$(PY_RUN_CMD) db-migrate-down

db-downgrade-all: ## Rollback all migrations
	$(PY_RUN_CMD) db-migrate-down-all

check-migrate-msg:
ifndef MIGRATE_MSG
	$(error MIGRATE_MSG is undefined)
endif

db-migrate-create: check-migrate-msg
	$(alembic_cmd) revision --autogenerate -m "$(MIGRATE_MSG)"

MIGRATE_MERGE_MSG := Merge multiple heads
db-migrate-merge-heads: ## Create a new migration that depends on all existing `head`s
	$(alembic_cmd) merge heads -m "$(MIGRATE_MERGE_MSG)" $(args)

db-migrate-current: ## Show current revision for a database
	$(alembic_cmd) current $(args)

db-migrate-history: ## Show migration history
	$(alembic_cmd) history $(args)

db-migrate-heads: ## Show migrations marked as a head
	$(alembic_cmd) heads $(args)

##################################################
# Testing
##################################################

test:
	$(PY_RUN_CMD) pytest $(args)

##################################################
# Formatting and linting
##################################################

format:
	$(PY_RUN_CMD) isort --atomic api tests
	$(PY_RUN_CMD) black api tests

lint: lint-spectral lint-py

lint-py: lint-flake lint-mypy lint-poetry-version

lint-flake:
	$(PY_RUN_CMD) flake8 --format=$(FLAKE8_FORMAT) api tests

lint-mypy:
	$(PY_RUN_CMD) mypy --show-error-codes $(MYPY_FLAGS) api $(MYPY_POSTPROC)

lint-poetry-version: ## Check poetry version
	grep --quiet 'lock-version = "1.1"' poetry.lock

lint-spectral:
	docker run --rm --tty --cap-drop=ALL --network=none --read-only --volume=$(PWD):/tmp:ro \
		stoplight/spectral:6 lint /tmp/openapi.yml --ruleset /tmp/.spectral.yaml $(SPECTRAL_POSTPROC)

test-coverage:
	$(PY_RUN_CMD) coverage run --branch --source=api -m pytest $(args)
	$(PY_RUN_CMD) coverage report

test-coverage-report: ## Open HTML test coverage report
	$(PY_RUN_CMD) coverage html --directory .coverage_report
	open .coverage_report/index.html

##################################################
# Scripts
##################################################

generate-pet-csv:
	$(PY_RUN_CMD) generate-pet-csv

##################################################
# Miscellaneous Utilities
##################################################

# Pauses for 5 seconds
sleep-5:
	sleep 5