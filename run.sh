#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 [--build|-b] (--prod|-p | --test|-t)

Options:
  -p, --prod     Run the production stack (project name: prod)
  -t, --test     Run the test stack (project name: test)
  -b, --build    Pass --build to 'docker compose up'
  -h, --help     Show this help message and exit

Examples:
  $0 --prod
  $0 -p -b
  $0 --test
  $0 -t --build
EOF
}

error() {
  echo "Error: $*" >&2
  echo >&2
  usage >&2
  exit 1
}

parse_args() {
  local mode=""
  local build="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -b|--build)
        build="true"
        shift
        ;;
      -p|--prod)
        if [[ -n "$mode" ]]; then
          error "choose exactly one of --prod/--test."
        fi
        mode="prod"
        shift
        ;;
      -t|--test)
        if [[ -n "$mode" ]]; then
          error "choose exactly one of --prod/--test."
        fi
        mode="test"
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

  if [[ -z "$mode" ]]; then
    error "you must specify --prod/-p or --test/-t."
  fi

  # "Return" via stdout: "<mode> <build>"
  printf '%s %s\n' "$mode" "$build"
}

set_mode_env() {
  local mode="$1"

  case "$mode" in
    prod)
      export DEVOPS_PORT=8081
      export WEIGHT_PORT=8082
      export BILLING_PORT=8083
      ;;
    test)
      export DEVOPS_PORT=8084
      export WEIGHT_PORT=8085
      export BILLING_PORT=8086
      ;;
    *)
      error "invalid mode: $mode"
      ;;
  esac
}

run_compose() {
  local mode="$1"
  local build="$2"

  local project="$mode"
  local docker_cmd=(docker compose -p "$project" up)

  if [[ "$build" == "true" ]]; then
    docker_cmd+=(--build)
  fi

  docker_cmd+=(-d)

  # Print the command we're about to run
  printf 'Running command:'
  printf ' %q' "${docker_cmd[@]}"
  printf '\n'

  "${docker_cmd[@]}"
}

main() {
  cd "$(dirname "$0")"
  export PROJECT_ROOT="$(pwd)"

  local parsed
  parsed="$(parse_args "$@")"

  local mode build
  read -r mode build <<<"$parsed"

  set_mode_env "$mode"
  run_compose "$mode" "$build"
}

main "$@"