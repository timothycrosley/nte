#!/bin/bash
set -euxo pipefail

poetry run isort nte/ tests/
poetry run black nte/ tests/
