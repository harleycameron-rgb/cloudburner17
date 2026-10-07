#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image_name="${IMAGE_NAME:-invariant-engine:latest}"
container_name="${CONTAINER_NAME:-cloudburner17}"
host_port="${PORT:-8000}"

docker build \
  --tag "$image_name" \
  --file "$repository_root/backend/Dockerfile" \
  "$repository_root"

exec docker run \
  --rm \
  --name "$container_name" \
  --publish "$host_port:8000" \
  "$image_name"
