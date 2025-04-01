#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export G_WORKING_DIR=$(readlink -f "${SCRIPT_DIR}/../tmp")
export G_PATCHES_DIR=$(readlink -f "${SCRIPT_DIR}/../patches")
export G_UTILS_DIR="${SCRIPT_DIR}"

export G_CONTAINERS_DIR="${G_WORKING_DIR}/build-containers"
export G_GODOT_SCRIPTS_DIR="${G_WORKING_DIR}/godot-build-scripts"
