#!/bin/bash
set -euo pipefail

echo "Fetch latest version of template-application-flask"
git clone --single-branch --branch main --depth 1 git@github.com:navapbc/template-application-flask.git

echo "Install template"
./template-application-flask/template-only-bin/install-template.sh

# Store template version in a file
cd template-application-flask
git rev-parse HEAD >../.template-flask-version
cd -

echo "Clean up template-application-flask folder"
rm -fr template-application-flask
