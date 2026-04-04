#!/usr/bin/env bash
set -euo pipefail

python3 -m compileall app scripts tests
pytest
