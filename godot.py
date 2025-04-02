#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
from pathlib import Path
from utils import *

# == Load configs ==
# config = Config("config.py")

# == Variables ==
work_dir = Path(__file__).resolve().parent
patches_dir = work_dir / "patches"
containers_dir = work_dir / "tmp/build-containers"
scripts_dir = work_dir / "tmp/godot-build-scripts"

build_targets = ["mono-glue", "windows", "linux", "web", "macos", "android", "ios"]
js_engines = ["v8", "qjs", "qjs_ng", "jsc"]
build_types = ["all", "classical", "mono"]

# == Argument Parser ==
parser = argparse.ArgumentParser(description="Godot Build Script")
subparsers = parser.add_subparsers(title="subcommands", dest="command", required=True, help="available commands")

repos_parser = subparsers.add_parser("repos", help="clone base git repositories")
repos_parser.add_argument("-c", "--containers-ref", default="main", help="build-containers git branch/tag")
repos_parser.add_argument("-s", "--scripts-ref", default="main", help="godot-build-scripts git branch/tag")

containers_parser = subparsers.add_parser("containers", help="build containers")
containers_parser.add_argument("target", choices=Containers.build_targets, help="build target")
containers_parser.add_argument(
    "-t", "--tool", default="docker", choices=["podman", "docker"], help="containers management tool"
)

build_parser = subparsers.add_parser("build", help="build Godot Engine")
build_parser.add_argument("-t", "--target", required=True, choices=build_targets, help="build target")
build_parser.add_argument("-v", "--godot-version", default="4.4.1-stable", help="godot engine version")
build_parser.add_argument("-j", "--godotjs-ref", default="main", help="godot-js git ref")
build_parser.add_argument("-d", "--deps-ref", default="v8_12.4.254.21_r13", help="godot-js dependencies release ref")
build_parser.add_argument("-g", "--godot-ref", default="4.4.1-stable", help="godot engine git ref")
build_parser.add_argument("-b", "--build-type", default=build_types[0], choices=build_types, help="build type")
build_parser.add_argument("-e", "--js-engine", default=js_engines[2], choices=js_engines, help="js engine")
build_parser.add_argument("-z", "--debug", action="store_true", help="toggle debug mode")

args = parser.parse_args()


def clone_repositories():
    if containers_dir.exists():
        Log.warn(f"The 'build-containers' dir already exists ({containers_dir}). Skipping...")
    else:
        Git.clone_repo("https://github.com/godotengine/build-containers.git", args.containers_ref, containers_dir)

    if scripts_dir.exists():
        Log.warn(f"The 'godot-build-scripts' dir already exists ({scripts_dir}). Skipping...")
    else:
        Git.clone_repo("https://github.com/godotengine/godot-build-scripts.git", args.scripts_ref, scripts_dir)


def build_container():
    Containers.build(args.tool, args.target, containers_dir)


def build_godot():
    # Check system dependencies
    CMDChecker.check()

    # Print config
    for k, v in vars(args).items():
        Log.kv(k, v)
    Log.kv("aes_encryption", "enabled" if os.getenv("SCRIPT_AES256_ENCRYPTION_KEY") else "disabled")

    # Apply patches
    Log.info("Patching required files...")
    Patcher.copy_files("patch", patches_dir, scripts_dir)

    # Prepare build configuration
    build_config = {
        "target_os": args.target,
        "godot_version": args.godot_version,
        "git_treeish": args.godot_ref,
        "godotjs_ref": args.godotjs_ref,
        "godotjs_deps_ref": args.deps_ref,
        "build_type": args.build_type,
        "js_engine": args.js_engine,
        "debug_mode": str(int(args.debug)),
    }

    # Execute the build script
    subprocess.run(["bash", str(scripts_dir / "build.sh"), json.dumps(build_config)], check=True)
    Log.info("Build completed successfully!")


# == Command Execution ==
match args.command:
    case "repos":
        clone_repositories()
    case "containers":
        build_container()
    case "build":
        build_godot()

Log.info("All done!")
