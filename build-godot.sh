#!/bin/bash
set -e

# == Load exports ==
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ${SCRIPT_DIR}/utils/exports.sh

# == Setup ==
source ${G_UTILS_DIR}/setup.sh

# == Begin Menu ==
target_os=""
godot_version="4.4.1-stable"
git_treeish="4.4.1-stable"
build_type="all"
godotjs_ref="main"
godotjs_deps_ref="v8_12.4.254.21_r13"
js_engine="qjs_ng"

printHelp()
{
  echo "Usage: $0 [OPTIONS...]"
  echo
  printf "  -t <target os>\tRequired. Target os\n\t\t\tPossible values: mono-glue, windows, linux, web, macos, android, ios\n"
  printf "  -v <version>\t\tOptional. Godot Engine version (e.g. 4.4.1-stable)\n"
  printf "  -j <ref>\t\tOptional. GodotJS git ref (e.g. main)\n"
  printf "  -d <ref>\t\tOptional. GodotJS-Dependencies release ref (e.g. v8_12.4.254.21_r13)\n"
  printf "  -g [ref]\t\tOptional. Godot Engine git ref (e.g. master)\n"
  printf "  -b [type=all]\t\tOptional. Build type. Possible values: all, classical, mono\n"
  printf "  -e [engine=qjs_ng]\tOptional. JS Engine. Possible values: v8, qjs, qjs_ng, jsc\n"
  printf "  -z\t\t\tOptional. Toggle debug mode\n"
  echo
}

checkArg() {
  local var_name="$1"
  local flag="$2"
  
  if [ -z "${!var_name}" ]; then
    echo "Error: Argument '$flag' is required."
    exit 1
  fi
}

if [[ $# -eq 0 ]]; then
  printHelp
  exit 1
fi

while getopts ":ht:v:j:d:g:b:e:z" option; do
  case $option in
    h) printHelp; exit;;
    \?) echo "Error: Invalid option."; printHelp; exit;;
    :) echo "Error: Argument '-$OPTARG' requires a value."; exit;;
    t) target_os=$OPTARG;;
    v) godot_version=$OPTARG;;
    j) godotjs_ref=$OPTARG;;
    d) godotjs_deps_ref=$OPTARG;;
    g) git_treeish=$OPTARG;;
    b) build_type=$OPTARG;;
    e) js_engine=$OPTARG;;
  esac
done

checkArg "target_os" "-t"
# == End Menu ==

echo "Working dir: ${G_GODOT_SCRIPTS_DIR}"

# == Setup requirements ==
echo "Setting up requirements..."
bash ${G_UTILS_DIR}/patch.sh apply

if [ -f "${G_WORKING_DIR}/config.sh" ]; then
	echo "Copying config file..."
	cp ${G_WORKING_DIR}/config.sh ${G_GODOT_SCRIPTS_DIR}/config.sh
fi

# == Start build ==
GREEN='\033[1;32m'
NC='\033[0m'
echo "Build parameters:"
echo -e "  ${GREEN}target os:${NC} ${target_os}"
echo -e "  ${GREEN}godot version:${NC} ${godot_version}"
echo -e "  ${GREEN}godot ref:${NC} ${git_treeish}"
echo -e "  ${GREEN}godotjs ref:${NC} ${godotjs_ref}"
echo -e "  ${GREEN}godotjs deps ref:${NC} ${godotjs_deps_ref}"
echo -e "  ${GREEN}build type:${NC} ${build_type}"
echo -e "  ${GREEN}js engine:${NC} ${js_engine}"

bash ${G_GODOT_SCRIPTS_DIR}/build.sh -t ${target_os} -v ${godot_version} -j ${godotjs_ref} -d ${godotjs_deps_ref} -g ${git_treeish} -b ${build_type} -e ${js_engine}

# Example: bash build-godot.sh mono-glue && bash build-godot.sh linux

# == After build ==
# bash ${G_UTILS_DIR}/patch.sh restore

echo "All done! :-)"
