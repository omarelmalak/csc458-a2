#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m pytest -q -m "not mininet"
