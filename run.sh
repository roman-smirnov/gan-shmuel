#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export PROJECT_ROOT="$(pwd)"

BUILD_ARGS=()
if [[ "${1-}" == "-b" ]]; then
  BUILD_ARGS+=(--build)
  shift
fi

docker compose up "${BUILD_ARGS[@]}" -d