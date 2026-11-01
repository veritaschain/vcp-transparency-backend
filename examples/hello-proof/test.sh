#!/bin/bash
# Regression tests use temporary output; bundled evidence is not overwritten.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
python3 -B -m unittest discover -s tests -v
