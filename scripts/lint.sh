#!/bin/bash
set -euxo pipefail

poetry run cruft check
poetry run mypy --ignore-missing-imports nte/
poetry run isort --check --diff nte/ tests/
poetry run black --check nte/ tests/
poetry run flake8 nte/ tests/
poetry run safety check -i 39462 -i 40291
