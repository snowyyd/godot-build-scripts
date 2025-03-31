#!/bin/bash

check_commands() {
	for cmd in "$@"; do
		if ! command -v "$cmd" &>/dev/null; then
			echo "$cmd is not available in the PATH."
			return 1
		fi
	done
	return 0
}

check_commands git curl docker 7z tar unzip
