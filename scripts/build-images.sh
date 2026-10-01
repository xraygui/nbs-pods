#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

cd -- "${ROOT_DIR}"

COMPOSE_FILE="${ROOT_DIR}/docker-compose.build.yml"
PODMAN_BUILD_ARGS="--ulimit nofile=65536:65536"

IMAGES=(
  bluesky
  queueserver
  gui
  viewer
  sim
)

usage() {
  echo "Usage: $0 [image ...]"
  echo "Build local nbs-pods images tagged as localhost/nbs-<name>:latest."
  echo ""
  echo "Images are built one at a time. Parallel builds from the same base"
  echo "image often fail in podman when committing large pixi layers."
  echo ""
  echo "If no images are specified, all are built (bluesky first)."
  echo ""
  echo "Available images:"
  for image in "${IMAGES[@]}"; do
    echo "  - ${image}"
  done
}

build_one() {
  local image=$1
  echo "Building ${image}..."
  podman-compose --podman-build-args="${PODMAN_BUILD_ARGS}" -f "${COMPOSE_FILE}" build "${image}"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -eq 0 ]]; then
  for image in "${IMAGES[@]}"; do
    build_one "${image}"
  done
  exit 0
fi

for image in "$@"; do
  found=0
  for known in "${IMAGES[@]}"; do
    if [[ "${image}" == "${known}" ]]; then
      found=1
      break
    fi
  done
  if [[ "${found}" -eq 0 ]]; then
    echo "Error: Unknown image '${image}'" >&2
    echo "" >&2
    usage >&2
    exit 1
  fi
done

for image in "$@"; do
  build_one "${image}"
done
