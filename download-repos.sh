#!/bin/bash
set -e

# == Load exports ==
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ${SCRIPT_DIR}/utils/exports.sh

# == Setup ==
source ${G_UTILS_DIR}/setup.sh

echo "Working dir: ${G_WORKING_DIR}"

echo "Clonning repos..."
git clone --depth 1 --recursive --branch ${G_GODOT_CONTAINERS_REF} https://github.com/godotengine/build-containers.git ${G_CONTAINERS_DIR} &
git clone --depth 1 --recursive --branch ${G_GODOT_SCRIPTS_REF} https://github.com/godotengine/godot-build-scripts ${G_GODOT_SCRIPTS_DIR} &
wait
