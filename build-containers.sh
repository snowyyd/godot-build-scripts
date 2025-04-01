#!/bin/bash
set -e

# == Load exports ==
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ${SCRIPT_DIR}/utils/exports.sh

# == Setup ==
source ${G_UTILS_DIR}/setup.sh

# TODO: check if ${G_CONTAINERS_DIR} exists

buildImage()
{
  echo "Docker target: $1"
  if [ "$1" == "base" ]; then
    docker build -t godot-fedora:latest -f ${G_CONTAINERS_DIR}/Dockerfile.base ${G_CONTAINERS_DIR}
  else
    docker build --build-arg="img_version=latest" -t godot-$1:latest -f ${G_CONTAINERS_DIR}/Dockerfile.$1 ${G_CONTAINERS_DIR}
  fi
}

case "$1" in
  base|windows|linux|web|osx|android|ios|xcode) buildImage "$1";;
  *) echo "Usage: $0 <container> (Possible values: base, windows, linux, web, osx, android, ios)"; exit 1;;
esac
