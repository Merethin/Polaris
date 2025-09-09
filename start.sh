#!/usr/bin/bash

set -euo pipefail

# Export git version info
export GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
export GIT_COMMIT=$(git rev-parse --short HEAD)

# If already running, stop
docker compose down

# Build a new image
docker compose build

# Start the new image in the background
docker compose up -d

echo "Started. Run 'docker compose logs -f' to view logs."