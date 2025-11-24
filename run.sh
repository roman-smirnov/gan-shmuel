#!/usr/bin/env bash
set -euo pipefail

# 1) Go to repo root (gan-shmuel/)
cd "$(dirname "$0")/.."   

# 2) Compute and export the absolute project root (portable across machines)
export PROJECT_ROOT="$(pwd)"

# 3) Use the ROOT docker-compose.yml (with `include:`) and start EVERYTHING
docker compose up -d