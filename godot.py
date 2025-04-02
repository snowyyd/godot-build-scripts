#!/usr/bin/env python3

import argparse
import json
import os
from utils import *

# == Load configs ==
# config = Config("config.py")

# == Variables ==
work_dir = os.path.dirname(os.path.abspath(__file__))
patches_dir = os.path.abspath(os.path.join(work_dir, "patches"))
containers_dir = os.path.abspath(os.path.join(work_dir, "tmp/build-containers"))
scripts_dir = os.path.abspath(os.path.join(work_dir, "tmp/godot-build-scripts"))

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
    "-t", "--tool", default="docker", choices=["podman", "docker"], help=f"containers manangement tool"
)

build_parser = subparsers.add_parser("build", help="build Godot Engine")
build_parser.add_argument("-t", "--target", required=True, choices=build_targets, help=f"build target")
build_parser.add_argument("-v", "--godot-version", default="4.4.1-stable", help="godot engine version")
build_parser.add_argument("-j", "--godotjs-ref", default="main", help="godot-js git ref")
build_parser.add_argument("-d", "--deps-ref", default="v8_12.4.254.21_r13", help="godot-js dependencies release ref")
build_parser.add_argument("-g", "--godot-ref", default="4.4.1-stable", help="godot engine git ref")
build_parser.add_argument("-b", "--build-type", default=build_types[0], choices=build_types, help="build type")
build_parser.add_argument("-e", "--js-engine", default=js_engines[2], choices=js_engines, help="js engine")
build_parser.add_argument("-z", "--debug", action="store_true", help="toggle debug mode")

args = parser.parse_args()

if args.command == "repos":
    if os.path.exists(containers_dir):
        Log.err(f"The 'build-containers' dir already exists ({containers_dir}), exiting...")
        exit(1)
    if os.path.exists(scripts_dir):
        Log.err(f"The 'godot-build-scripts' dir already exists ({scripts_dir}), exiting...")
        exit(1)

    Git.clone_repo("https://github.com/godotengine/build-containers.git", args.containers_ref, containers_dir)
    Git.clone_repo("https://github.com/godotengine/godot-build-scripts.git", args.scripts_ref, scripts_dir)

elif args.command == "containers":
    Containers.build(args.tool, args.target, containers_dir)

elif args.command == "build":
    # == Check if the system has the required commands ==
    CMDChecker.check()

    # == Print config ==
    for k, v in vars(args).items():
        Log.kv(k, v)
    Log.kv("aes_encryption", "enabled" if os.getenv("SCRIPT_AES256_ENCRYPTION_KEY") else "disabled")

    # == Do prerequisites ==
    Log.info("Patching required files...")
    Patcher.copy_files("patch", patches_dir, scripts_dir)

    # == Start build ==
    # TODO: merge build.sh with this script
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

    subprocess.run(["bash", os.path.join(scripts_dir, "build.sh"), json.dumps(build_config)], check=True)

Log.info("All done!")
