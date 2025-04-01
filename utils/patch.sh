#!/bin/bash
set -e

# == Load exports ==
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ${SCRIPT_DIR}/exports.sh

if [ -z "$1" ]; then
  echo "Usage: $0 <action> (Possible actions: apply, restore)"
  exit 1
fi

backup_and_patch()
{
  local file_path="$1"
  local patch_file="$2"

  if [ ! -f "${file_path}.bak" ]; then
    # echo "Creating backup of ${file_path}..."
    cp "${file_path}" "${file_path}.bak"
  fi

  echo "Patching ${file_path}..."
  cp "${patch_file}" "${file_path}"
}

restore_backup()
{
  local file_path="$1"

  if [ -f "${file_path}.bak" ]; then
    echo "Restoring backup of ${file_path}..."
    cp "${file_path}.bak" "${file_path}"
  else
    echo "No backup found for ${file_path}, skipping..."
  fi
}

case "$1" in
  apply)
    echo "Applying patches..."
    backup_and_patch "${G_GODOT_SCRIPTS_DIR}/build.sh" "${G_PATCHES_DIR}/build.sh"
    backup_and_patch "${G_GODOT_SCRIPTS_DIR}/build-windows/build.sh" "${G_PATCHES_DIR}/build-windows.sh"
    backup_and_patch "${G_GODOT_SCRIPTS_DIR}/build-linux/build.sh" "${G_PATCHES_DIR}/build-linux.sh"
    backup_and_patch "${G_GODOT_SCRIPTS_DIR}/config.sh.in" "${G_PATCHES_DIR}/config.sh.in"
    ;;
  restore)
    echo "Restoring backups..."
    restore_backup "${G_GODOT_SCRIPTS_DIR}/build.sh"
    restore_backup "${G_GODOT_SCRIPTS_DIR}/build-windows/build.sh"
    restore_backup "${G_GODOT_SCRIPTS_DIR}/build-linux/build.sh"
    restore_backup "${G_GODOT_SCRIPTS_DIR}/config.sh.in"
    ;;
  *) echo "Invalid action! Possible actions: apply, restore"; exit 1;;
esac
