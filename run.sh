#!/usr/bin/env bash
set -euo pipefail

# Globals (kept simple)
DOCKER_COMPOSE=()   # will be filled in init_docker_compose

usage() {
  cat <<EOF
Usage:
  $0 [--build|-b] (--prod|-p | --test|-t)
  $0 down (--prod|-p | --test|-t | --all)

Commands (implicit):
  (no command)   Start the stack (same as "up")
  down           Stop one or both stacks

Options:
  -p, --prod     Use the production stack (project name: prod)
  -t, --test     Use the test stack (project name: test)
  --all          With "down", stop both prod and test stacks
  -b, --build    Pass --build to 'docker compose up'
  -h, --help     Show this help message and exit

Examples:
  $0 --prod
  $0 -p -b
  $0 --test
  $0 -t --build
  $0 down --prod
  $0 down --test
  $0 down --all
EOF
}

error() {
  echo "Error: $*" >&2
  echo >&2
  usage >&2
  exit 1
}

init_docker_compose() {
  # Detect docker compose flavor: prefer "docker compose", fallback to "docker-compose"
  if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE=(docker-compose)
  else
    echo "Error: neither 'docker compose' nor 'docker-compose' is available in PATH." >&2
    exit 1
  fi
}

ensure_compose_file() {
  # Require some compose file to exist in PROJECT_ROOT
  local found=""
  local candidates=(
    "docker-compose.yml"
    "docker-compose.yaml"
    "compose.yml"
    "compose.yaml"
  )

  for f in "${candidates[@]}"; do
    if [[ -f "$f" ]]; then
      found="$f"
      break
    fi
  done

  if [[ -z "$found" ]]; then
    echo "Error: no docker compose file found in $PROJECT_ROOT" >&2
    echo "Looked for: ${candidates[*]}" >&2
    exit 1
  fi
}

parse_args() {
  local action="up"  # default action
  local mode=""
  local build=""     # empty = false; non-empty = true
  local all=""       # empty = false; non-empty = true

  # Optional first argument: "down" or "up"
  if [[ $# -gt 0 ]]; then
    case "$1" in
      down)
        action="down"
        shift
        ;;
      up)
        action="up"
        shift
        ;;
    esac
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -b|--build)
        build=1
        shift
        ;;
      -p|--prod)
        if [[ -n "$mode" || -n "$all" ]]; then
          error "choose exactly one of --prod/--test/--all."
        fi
        mode="prod"
        shift
        ;;
      -t|--test)
        if [[ -n "$mode" || -n "$all" ]]; then
          error "choose exactly one of --prod/--test/--all."
        fi
        mode="test"
        shift
        ;;
      --all)
        if [[ "$action" != "down" ]]; then
          error "--all is only valid with the 'down' command."
        fi
        if [[ -n "$mode" ]]; then
          error "cannot combine --all with --prod/--test."
        fi
        all=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        error "unknown argument: $1"
        ;;
    esac
  done

  if [[ "$action" == "up" ]]; then
    if [[ -z "$mode" ]]; then
      error "for 'up' you must specify --prod/-p or --test/-t."
    fi
    if [[ -n "$all" ]]; then
      error "--all is not valid with 'up'."
    fi
  else
    # action == down
    if [[ -z "$mode" && -z "$all" ]]; then
      error "for 'down' specify --all or one of --prod/--test."
    fi
    if [[ -n "$build" ]]; then
      error "--build/-b is not valid with 'down'."
    fi
  fi

  # Encode "--all" as a pseudo-mode to simplify main()
  if [[ "$action" == "down" && -n "$all" ]]; then
    mode="all"
  fi

  # "Return": "<action> <mode> <build_flag>"
  printf '%s %s %s\n' "$action" "$mode" "${build:+true}"
}

set_mode_env() {
  local mode="$1"

  case "$mode" in
    prod)
      export ENV=prod
      export DEVOPS_PORT=8081
      export WEIGHT_PORT=8082
      export BILLING_PORT=8083
      export WEIGHT_MYSQL_PORT=3037

      export DB_HOST=billing-db
      export DB_USER=root
      export DB_PASSWORD=password
      export DB_NAME=billdb
      export DB_PORT=3306

      export WEIGHT_BASE_URL=http://weight-app:5000
      ;;
    test)
      export ENV=test
      export DEVOPS_PORT=8084
      export WEIGHT_PORT=8085
      export BILLING_PORT=8086
      export WEIGHT_MYSQL_PORT=3456

      export DB_HOST=billing-db
      export DB_USER=root
      export DB_PASSWORD=password
      export DB_NAME=billdb
      export DB_PORT=3306

      export WEIGHT_BASE_URL=http://weight-app:5000
      ;;
    *)
      error "invalid mode: $mode"
      ;;
  esac
}

run_compose_up() {
  local mode="$1"
  local build="$2"

  local project="$mode"
  local docker_cmd=("${DOCKER_COMPOSE[@]}" -p "$project" up)

  if [[ "$build" == "true" ]]; then
    docker_cmd+=(--build)
  fi

  docker_cmd+=(-d)

  printf 'Running command:'
  printf ' %q' "${docker_cmd[@]}"
  printf '\n'

  "${docker_cmd[@]}"
}

run_compose_down() {
  local mode="$1"

  # ensure env vars are set for interpolation (avoids warnings)
  set_mode_env "$mode"

  local project="$mode"
  local docker_cmd=("${DOCKER_COMPOSE[@]}" -p "$project" down)

  printf 'Running command:'
  printf ' %q' "${docker_cmd[@]}"
  printf '\n'

  "${docker_cmd[@]}"
}

run_compose_down_all() {
  local m
  for m in prod test; do
    set_mode_env "$m"
    local project="$m"
    local docker_cmd=("${DOCKER_COMPOSE[@]}" -p "$project" down)

    printf 'Running command:'
    printf ' %q' "${docker_cmd[@]}"
    printf '\n'

    "${docker_cmd[@]}"
  done
}

main() {
  cd "$(dirname "$0")"
  export PROJECT_ROOT="$(pwd)"

  init_docker_compose
  ensure_compose_file

  local parsed
  parsed="$(parse_args "$@")"

  local action mode build
  read -r action mode build <<<"$parsed"

  if [[ "$action" == "up" ]]; then
    set_mode_env "$mode"
    run_compose_up "$mode" "$build"
  else
    # action == down
    if [[ "$mode" == "all" ]]; then
      run_compose_down_all
    else
      run_compose_down "$mode"
    fi
  fi
}

main "$@"