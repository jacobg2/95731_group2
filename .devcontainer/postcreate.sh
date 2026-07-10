#!/usr/bin/env bash
# One-time setup after the devcontainer is created: dev dependencies and
# a local .env from the template if one doesn't exist yet.
set -euo pipefail

pip install -r requirements.txt -r requirements-dev.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi
