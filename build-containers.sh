#!/bin/bash
set -e

# == Load exports ==
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ${SCRIPT_DIR}/utils/exports.sh

# == Setup ==
source ${G_UTILS_DIR}/setup.sh

echo "Working dir: ${G_CONTAINERS_DIR}"

# TODO: check if ${G_CONTAINERS_DIR} exists

echo "Building Docker images..."
docker build -t godot-fedora:latest -f ${G_CONTAINERS_DIR}/Dockerfile.base ${G_CONTAINERS_DIR} &
docker build --build-arg="img_version=latest" -t godot-windows:latest -f ${G_CONTAINERS_DIR}/Dockerfile.windows ${G_CONTAINERS_DIR} &
wait
