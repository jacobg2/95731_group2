#!/usr/bin/env bash
# Runs on every container start: apply any pending migrations (idempotent).
set -euo pipefail

python manage.py migrate
