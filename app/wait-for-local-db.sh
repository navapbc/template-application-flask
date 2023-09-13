#!/bin/bash
# wait-for-local-db

set -e

# Color formatting
RED='\033[0;31m'
NO_COLOR='\033[0m'

MAX_WAIT_TIME=30 # seconds
wait_time=0

# Use pg_isready to wait for the DB to be ready to accept connections
# We check every 3 seconds and consider it failed if it gets to 30+
# https://www.postgresql.org/docs/current/app-pg-isready.html
while ! pg_isready -h localhost -d main-db -q;
do
    echo "waiting on Postgres DB to initialize..."
    sleep 3

    wait_time=$(($wait_time+3))
    if [ $wait_time -gt $MAX_WAIT_TIME ]
    then
        echo -e "${RED}ERROR: Database appears to not be starting up, running \"docker logs main-db\" to see what the issue is${NO_COLOR}"
        docker logs main-db
        exit 1
    fi
done

echo "Postgres DB is ready after ~${wait_time} seconds"
