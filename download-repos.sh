#!/bin/bash
set -e

# == Load exports ==
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ${SCRIPT_DIR}/utils/exports.sh

# == Setup ==
source ${G_UTILS_DIR}/setup.sh

# == Begin Menu ==
scripts_ref="main"
containers_ref="main"

printHelp()
{
  echo "Usage: $0 [OPTIONS...]"
  echo
  printf "  -s [scripts ref=main]\Git ref for Godot build scripts repository\n"
  printf "  -c [containers ref=main]\Git ref for Godot build containers repository\n"
  echo
}

while getopts ":hs:c:" option; do
  case $option in
  h) printHelp; exit;;
  \?) echo "Error: Invalid option."; printHelp; exit;;
  :) echo "Error: Argument '-$OPTARG' requires a value."; exit;;
  s) scripts_ref=$OPTARG;;
  c) containers_ref=$OPTARG;;
  esac
done
# == End Menu ==

echo "Clonning repos..."
git clone --depth 1 --recursive --branch ${containers_ref} https://github.com/godotengine/build-containers.git ${G_CONTAINERS_DIR} &
git clone --depth 1 --recursive --branch ${scripts_ref} https://github.com/godotengine/godot-build-scripts ${G_GODOT_SCRIPTS_DIR} &
wait
