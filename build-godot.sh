#!/bin/bash
set -e

# == Load exports ==
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ${SCRIPT_DIR}/utils/exports.sh

# == Setup ==
source ${G_UTILS_DIR}/setup.sh

echo "Working dir: ${G_GODOT_SCRIPTS_DIR}"

# == Setup requirements ==
echo "Setting up requirements..."
bash ${G_UTILS_DIR}/patch.sh apply

if [ -f "${G_WORKING_DIR}/config.sh" ]; then
	echo "Copying config file..."
	cp ${G_WORKING_DIR}/config.sh ${G_GODOT_SCRIPTS_DIR}/config.sh
fi

# bash ${G_GODOT_SCRIPTS_DIR}/build.sh -v ${G_GODOT_REF} -g ${G_GODOT_REF} -j ${G_GODOTJS_REF} -d ${G_GODOTJS_DEPS_REF} -t mono-glue
bash ${G_GODOT_SCRIPTS_DIR}/build.sh -v ${G_GODOT_REF} -g ${G_GODOT_REF} -j ${G_GODOTJS_REF} -d ${G_GODOTJS_DEPS_REF} -t windows

# bash ${G_UTILS_DIR}/patch.sh restore

echo "All done! :-)"
