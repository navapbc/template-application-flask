#!/bin/bash
#
# This script updates template-application-flask in your project. Run
# This script from your project's root directory.
set -euo pipefail

SCRIPT_DIR=$(dirname $0)

echo "Install template"
$SCRIPT_DIR/install-template.sh
