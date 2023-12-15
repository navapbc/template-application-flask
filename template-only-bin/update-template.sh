#!/bin/bash
# -----------------------------------------------------------------------------
# This script updates template-application-flask in your project. Run
# This script from your project's root directory.
#
# Positional parameters:
#   TARGET_VERSION (optional) – the version of template-application-flask to upgrade to.
#     Defaults to main.
# -----------------------------------------------------------------------------
set -euo pipefail

TARGET_VERSION=${1:-"main"}

CURRENT_VERSION=$(cat .template-flask-version)

echo "Clone template-application-flask"
git clone https://github.com/navapbc/template-application-flask.git

echo "Creating patch"
cd template-application-flask
git checkout $TARGET_VERSION

# Get version hash to update .template-flask-version after patch is successful
TARGET_VERSION_HASH=$(git rev-parse HEAD)

# Note: Keep this list in sync with the files copied in install-template.sh
INCLUDE_PATHS=" \
  github \
  .dockleconfig \
  .hadolint.yaml \
  app \
  docker-compose.yml \
  docs"
git diff $CURRENT_VERSION $TARGET_VERSION -- $INCLUDE_PATHS >patch
cd -

echo "Applying patch"
# Note: Keep this list in sync with the removed files in install-template.sh
EXCLUDE_OPT="--exclude=.github/workflows/template-only-*"
git apply $EXCLUDE_OPT --allow-empty template-application-flask/patch

echo "Saving new template version to .template-application-flask"
echo $TARGET_VERSION_HASH >.template-flask-version

echo "Clean up template-application-flask folder"
rm -fr template-application-flask
