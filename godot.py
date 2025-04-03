#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from utils import *

# == Load configs ==
config = Config("config.py")

# == Variables ==
work_dir = Path(__file__).resolve().parent
patches_dir = work_dir / "patches"
containers_dir = work_dir / "tmp/build-containers"
scripts_dir = work_dir / "tmp/godot-build-scripts"
scripts_deps_dir = scripts_dir / "deps"
godot_dir = scripts_dir / "git"
godotjs_dir = godot_dir / "modules" / "GodotJS"
dep_v8_dir = godotjs_dir / "v8"
logs_dir = scripts_dir / "out" / "logs"
mono_glue_dir = scripts_dir / "mono-glue"
keystore_file_name = "file.keystore"

build_targets = ["mono-glue", "windows", "linux", "web", "macos", "android", "ios"]
js_engines = ["v8", "qjs", "qjs_ng", "jsc"]
build_types = ["all", "classical", "mono"]

default_encryption_key = "0" * 64
encryption_key = (
    config.encryption_key if config.encryption_key else os.getenv("SCRIPT_AES256_ENCRYPTION_KEY", "0" * 64)
)

# == Argument Parser ==
parser = argparse.ArgumentParser(description="Godot Build Script")
subparsers = parser.add_subparsers(title="subcommands", dest="command", required=True, help="available commands")

repos_parser = subparsers.add_parser("repos", help="clone base git repositories")
repos_parser.add_argument("-c", "--containers-ref", help="build-containers git ref")
repos_parser.add_argument("-s", "--scripts-ref", help="godot-build-scripts git branch/tag")

containers_parser = subparsers.add_parser("containers", help="build containers")
containers_parser.add_argument("target", choices=Containers.build_targets, help="build target")
containers_parser.add_argument(
    "-t", "--tool", default="docker", choices=["podman", "docker"], help="containers management tool"
)

build_parser = subparsers.add_parser("build", help="build Godot Engine")
build_parser.add_argument("-t", "--target", required=True, choices=build_targets, help="build target")
build_parser.add_argument("-v", "--godot-version", default="4.4.1-stable", help="godot engine version")
build_parser.add_argument("-j", "--godotjs-ref", default="main", help="godotjs git ref")
build_parser.add_argument("-d", "--deps-ref", default="v8_12.4.254.21_r13", help="godotjs dependencies release ref")
build_parser.add_argument("-g", "--godot-ref", default="4.4.1-stable", help="godot engine git ref")
build_parser.add_argument("-b", "--build-type", default=build_types[0], choices=build_types, help="build type")
build_parser.add_argument("-e", "--js-engine", default=js_engines[2], choices=js_engines, help="js engine")
build_parser.add_argument("-c", "--skip-checkout", action="store_true", help="js engine")
build_parser.add_argument("-z", "--debug", action="store_true", help="toggle debug mode")

args = parser.parse_args()


def clone_repositories():
    if containers_dir.exists():
        Log.warn(f"The 'build-containers' dir already exists ({containers_dir}). Skipping...")
    else:
        Log.info("Clonning build containers...")
        Git.clone_and_checkout(
            "https://github.com/godotengine/build-containers.git", containers_dir, args.containers_ref
        )

    if scripts_dir.exists():
        Log.warn(f"The 'godot-build-scripts' dir already exists ({scripts_dir}). Skipping...")
    else:
        Log.info("Clonning build scripts...")
        Git.clone_and_checkout("https://github.com/godotengine/godot-build-scripts.git", scripts_dir, args.scripts_ref)


def build_container():
    Containers.build(args.tool, args.target, containers_dir)


def build_godot():
    # Check system dependencies
    CMDChecker.check()

    # Print config
    for k, v in vars(args).items():
        Log.kv(k, v)
    Log.kv("aes_encryption", "enabled" if encryption_key != default_encryption_key else "disabled")

    # Apply patches
    Log.info("Patching required files...")
    Patcher.copy_files("patch", patches_dir, scripts_dir)

    # 1. Ensure dirs
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(mono_glue_dir, exist_ok=True)

    # ? add "logs/build"

    # Split godot_version
    g_version, _, g_status = args.godot_version.partition("-")
    if g_version == "" or g_status == "":
        Log.err("Make sure that --godot-version has the proper format!")
        raise SystemExit(1)

    Log.info(f"Building Godot Engine {g_version} ({g_status}) from git ref '{args.godot_ref}'...")

    # 2. Download dependencies
    Log.info("Downloading dependencies...")
    dependencies = {
        "moltenvk": {
            "target": ["macos"],
            "base_url": "https://github.com/godotengine/moltenvk-osxcross/releases/download/vulkan-sdk-1.3.283.0-2",
            "files": {"MoltenVK-all.tar": "moltenvk.tar"},
            "move": [
                ("MoltenVK/MoltenVK/include/", "MoltenVK/"),
                ("MoltenVK/MoltenVK/static/MoltenVK.xcframework/", "MoltenVK/"),
            ],
        },
        "accesskit": {
            "target": ["windows", "linux", "macos"],
            "base_url": "https://github.com/godotengine/godot-accesskit-c-static/releases/download/0.15.1",
            "files": {"accesskit-c-0.15.1.zip": "accesskit.zip"},
            "move": [("accesskit-c-*", "accesskit-c")],
        },
        "angle": {
            "target": ["windows", "macos"],
            "base_url": "https://github.com/godotengine/godot-angle-static/releases/download/chromium%2F6601.2",
            "files": {
                "godot-angle-static-arm64-llvm-release.zip": "windows_arm64.zip",
                "godot-angle-static-x86_64-gcc-release.zip": "windows_x86_64.zip",
                "godot-angle-static-x86_32-gcc-release.zip": "windows_x86_32.zip",
                "godot-angle-static-arm64-macos-release.zip": "macos_arm64.zip",
                "godot-angle-static-x86_64-macos-release.zip": "macos_x86_64.zip",
            },
        },
        "mesa": {
            "target": ["windows"],
            "base_url": "https://github.com/godotengine/godot-nir-static/releases/download/23.1.9-1",
            "files": {
                "godot-nir-static-arm64-llvm-release.zip": "mesa_arm64.zip",
                "godot-nir-static-x86_64-gcc-release.zip": "mesa_x86_64.zip",
                "godot-nir-static-x86_32-gcc-release.zip": "mesa_x86_32.zip",
            },
        },
        "swappy": {
            "target": ["android"],
            "base_url": "https://github.com/godotengine/godot-swappy/releases/download/from-source-2025-01-31",
            "files": {"godot-swappy.7z": "godot-swappy.7z"},
        },
    }

    for name, opts in dependencies.items():
        Dependencies.ensure(name, opts, args.target, scripts_deps_dir)

    if args.target == "android":
        dep_keystore_path = scripts_deps_dir / "keystore"
        os.makedirs(dep_keystore_path, exist_ok=True)
        keystore_file_path = Path(config.keystore["path"]) if config.keystore["path"] != "" else None
        if not keystore_file_path:
            Log.warn("Android keystore path is not defined, the build will not be signed!")
        elif not keystore_file_path.is_file():
            Log.err("The keystore path you configured does not exists or is not a file, exiting...")
            raise SystemExit(1)
        else:
            Log.info(f"Copying keystore file located at {keystore_file_path}...")
            shutil.copy(keystore_file_path, dep_keystore_path / keystore_file_name)

    # 3. Checkout Godot Engine
    if args.skip_checkout and godot_dir.exists():
        Log.warn("Godot Engine is already downloaded and you opted to skip checkouts, skipping...")
    else:
        Log.info("Downloading Godot Engine...")
        Git.clone_and_checkout("https://github.com/godotengine/godot.git", godot_dir, args.godot_ref)

    # ? Add validate version again?

    # 4. Checkout GodotJS
    if args.skip_checkout and godotjs_dir.exists():
        Log.warn("GodotJS is already downloaded and you opted to skip checkouts, skipping...")
    else:
        Log.info("Downloading GodotJS...")
        Git.clone_and_checkout("https://github.com/godotjs/godotjs.git", godotjs_dir, args.godotjs_ref)

    # 5. Download GodotJS dependencies
    if args.skip_checkout and dep_v8_dir.exists():
        Log.warn("v8 is already downloaded and you opted to skip checkouts, skipping...")
    else:
        v8_file = godot_dir / "v8.zip"
        Log.info("Downloading v8...")
        download_file(
            f"https://github.com/ialex32x/GodotJS-Dependencies/releases/download/{args.deps_ref}/{args.deps_ref}.zip",
            v8_file,  # ? Use tmpdir?
        )

        Log.info("Extracting v8...")
        FileExtractor.extract_file(v8_file, dep_v8_dir)
        v8_file.unlink(True)

    # 6. Create gzipped tarball
    name_template = f"godot-{args.godot_version}"
    final_tar_path = scripts_dir / f"{name_template}.tar.gz"

    if final_tar_path.exists():
        Log.warn(f"{name_template}.tar.gz already exists, skipping...")
    else:
        commit_hash = Git.get_commit_hash(godot_dir)

        if not commit_hash:
            Log.err("Failed to get commit hash.")
            raise SystemExit(1)

        with tempfile.TemporaryDirectory(prefix="godot-") as temp_dir:
            tar_path = Path(temp_dir) / "godot.tar.gz"
            Log.info(f"Writing temporal tar.gz file on {tar_path}...")

            filter_func = lambda tarinfo: (None if ".git" in tarinfo.name.split(os.sep) else tarinfo)

            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(godot_dir, arcname=name_template, filter=filter_func)
                head_path = Path(temp_dir) / "HEAD"
                head_path.write_text(commit_hash)
                tar.add(head_path, f"{name_template}/.git/HEAD", False)

            tar_path.rename(final_tar_path)
            Log.info(f"File is available on {final_tar_path}")

    # 7. Start container
    def gen_args(env: Optional[Dict[str, str]] = None, volumes: Optional[Dict[str, str]] = None) -> List[str]:
        args = []
        if env:
            args.extend(["--env", f"{key}={value}"] for key, value in env.items())
        if volumes:
            args.extend(["-v", f"{local}:{container}"] for local, container in volumes.items())
        return [arg for sublist in args for arg in sublist]

    repository_prefix = "localhost/" if config.tool != "docker" else ""
    cmd_image: Optional[str] = None
    cmd_suffix: Optional[List[str]] = None
    cmd_prefix = [config.tool, "run", "-it", "--rm", "-w", "/root/"] + gen_args(
        {
            "BUILD_NAME": config.build_name,
            "GODOT_VERSION_STATUS": g_status,
            "NUM_CORES": config.num_cores,
            "CLASSICAL": "1" if args.build_type in ("all", "classical") else "0",
            "MONO": "1" if args.build_type in ("all", "mono") else "0",
            "STEAM": "1" if config.build_steam else "0",
            "SCRIPT_AES256_ENCRYPTION_KEY": encryption_key,
            "JS_ENGINE": args.js_engine,
        },
        {
            final_tar_path: "/root/godot.tar.gz",
            mono_glue_dir: "/root/mono-glue",
        },
    )

    # ? add logs/*?
    platforms = {
        "mono-glue": {
            "image": "godot-linux",
            "volumes": {f"{scripts_dir}/build-mono-glue": "/root/build"},
        },
        "windows": {
            "image": "godot-windows",
            "volumes": {
                f"{scripts_dir}/build-windows": "/root/build",
                f"{scripts_dir}/out/windows": "/root/out",
                f"{scripts_dir}/deps/angle": "/root/angle",
                f"{scripts_dir}/deps/mesa": "/root/mesa",
                f"{scripts_dir}/deps/accesskit": "/root/accesskit",
            },
        },
        "linux": {
            "image": "godot-linux",
            "volumes": {
                f"{scripts_dir}/build-linux": "/root/build",
                f"{scripts_dir}/out/linux": "/root/out",
                f"{scripts_dir}/deps/accesskit": "/root/accesskit",
            },
        },
        "web": {
            "image": "godot-web",
            "volumes": {
                f"{scripts_dir}/build-web": "/root/build",
                f"{scripts_dir}/out/web": "/root/out",
            },
        },
        "macos": {
            "image": "godot-osx",
            "volumes": {
                f"{scripts_dir}/build-macos": "/root/build",
                f"{scripts_dir}/out/macos": "/root/out",
                f"{scripts_dir}/deps/accesskit": "/root/accesskit",
                f"{scripts_dir}/deps/moltenvk": "/root/moltenvk",
                f"{scripts_dir}/deps/angle": "/root/angle",
            },
        },
        "android": {
            "image": "godot-android",
            "volumes": {
                f"{scripts_dir}/build-android": "/root/build",
                f"{scripts_dir}/out/android": "/root/out",
                f"{scripts_dir}/deps/swappy": "/root/swappy",
                f"{scripts_dir}/deps/keystore": "/root/keystore",
            },
            "env": {
                "OSSRH_GROUP_ID": config.ossrh["group_id"],
                "OSSRH_USERNAME": config.ossrh["username"],
                "OSSRH_PASSWORD": config.ossrh["password"],
                "SONATYPE_STAGING_PROFILE_ID": config.sonatype_staging_profile_id,
                "SIGNING_KEY_ID": config.signing["key_id"],
                "SIGNING_PASSWORD": config.signing["password"],
                "SIGNING_KEY": config.signing["key"],
                "GODOT_ANDROID_SIGN_KEYSTORE": f"/root/keystore/{keystore_file_name}",
                "GODOT_ANDROID_KEYSTORE_ALIAS": config.keystore["alias"],
                "GODOT_ANDROID_SIGN_PASSWORD": config.keystore["password"],
            },
        },
        "ios": {
            "image": "godot-ios",
            "volumes": {
                f"{scripts_dir}/build-ios": "/root/build",
                f"{scripts_dir}/out/ios": "/root/out",
            },
        },
    }

    run_command = "bash build/build.sh"
    if args.debug:
        run_command = "sleep infinity"
        Log.warn("You are in debug mode, no build will be actually perfomed")

    if args.target in platforms:
        config_data = platforms[args.target]
        cmd_image = config_data["image"]
        cmd_suffix = gen_args(config_data["env"] if "env" in config_data else None, config_data["volumes"])
    else:
        raise ValueError(f"Unknown target: {args.target}")

    Log.info(f"Starting build with target: {args.target}...")
    docker_cmd = (
        cmd_prefix + cmd_suffix + [f"{repository_prefix}{cmd_image}:{config.image_version}"] + run_command.split(" ")
    )

    Log.debug(f"Final command: {' '.join(docker_cmd).replace(encryption_key, '***')}")
    subprocess.run(docker_cmd, cwd=scripts_dir, check=True)
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
