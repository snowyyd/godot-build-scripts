#!/bin/bash

export G_GODOT_REF="4.4.1-stable"
export G_GODOTJS_REF="main"
export G_GODOTJS_DEPS_REF="v8_12.4.254.21_r13"
export G_GODOT_CONTAINERS_REF="main"
export G_GODOT_SCRIPTS_REF="main"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export G_WORKING_DIR=$(readlink -f "${SCRIPT_DIR}/../tmp")
export G_PATCHES_DIR=$(readlink -f "${SCRIPT_DIR}/../patches")
export G_UTILS_DIR="${SCRIPT_DIR}"

export G_CONTAINERS_DIR="${G_WORKING_DIR}/build-containers"
export G_GODOT_SCRIPTS_DIR="${G_WORKING_DIR}/godot-build-scripts"
