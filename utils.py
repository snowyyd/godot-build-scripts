import importlib.util
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Literal, List

if __name__ == "__main__":
    raise Exception("This module cannot be run directly")


class Colors:
    RESET = "\033[0m"

    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Styles
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    REVERSED = "\033[7m"

    # Backgrounds
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Bright backgrounds
    BG_BRIGHT_BLACK = "\033[100m"
    BG_BRIGHT_RED = "\033[101m"
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"

    @staticmethod
    def color_text(text: str, color: str) -> str:
        return f"{color}{text}{Colors.RESET}"

    @staticmethod
    def color_text_bold(text: str, color: str) -> str:
        return f"{color}{Colors.BOLD}{text}{Colors.RESET}"


class Log:
    @staticmethod
    def warn(text: str) -> str:
        return print(Colors.color_text_bold("WARN:", Colors.YELLOW), text)

    @staticmethod
    def err(text: str) -> str:
        return print(Colors.color_text_bold("ERR:", Colors.RED), text)

    @staticmethod
    def info(text: str) -> str:
        return print(Colors.color_text_bold("INFO:", Colors.GREEN), text)

    @staticmethod
    def kv(k: str, v: str):
        return print(Colors.color_text(k + ":", Colors.GREEN), v)


class CMDChecker:
    commands_to_check: List[str] = ["bash", "git", "curl", "docker", "7z", "tar", "unzip", "gzip", "jq"]

    @staticmethod
    def check(cmds: List[str] = commands_to_check):
        missing: List[str] = [cmd for cmd in cmds if shutil.which(cmd) is None]

        if missing:
            Log.err(f"missing commands: {', '.join(missing)}")
            exit(1)

    @staticmethod
    def checkSingle(cmd: str):
        if shutil.which(cmd) is None:
            Log.err(f"missing command: {cmd}")
            exit(1)


class Git:
    @staticmethod
    def clone_repo(repo_url: str, branch: str, target_dir: Path) -> None:
        CMDChecker.checkSingle("git")
        cmd = shlex.split(f"git clone --recursive --depth 1 --branch {branch} {repo_url} {str(target_dir)}")
        subprocess.run(cmd, check=True)


class Containers:
    build_targets: List[str] = ["base", "windows", "linux", "web", "osx", "android", "ios"]

    @staticmethod
    def build(tool: str, target: str, containers_dir: str | Path):
        CMDChecker.checkSingle(tool)
        Log.info(f"Building {target} using {tool}...")
        cmd = shlex.split(
            f'{tool} build --build-arg="img_version=latest" -t godot-{"fedora" if target == "base" else target}:latest -f {containers_dir}/Dockerfile.{target} {containers_dir}'
        )
        subprocess.run(cmd, check=True)


class Patcher:
    files = [
        # format (source [patches folder], dest [godot-build-scripts folder])
        ("build.sh", "build.sh"),
        ("build-windows.sh", "build-windows/build.sh"),
        ("build-linux.sh", "build-linux/build.sh"),
        ("config.sh.in", "config.sh.in"),
    ]

    @staticmethod
    def backup_and_patch(patch_file: str | Path, dest_file: str | Path):
        if not os.path.isfile(dest_file):
            Log.err(f"{dest_file} does not exist")
            exit(1)

        backup_path = dest_file + ".bak"

        if not os.path.isfile(backup_path):
            shutil.copy(dest_file, backup_path)

        Log.info(f"Patching {dest_file}...")
        shutil.copy(patch_file, dest_file)

    @staticmethod
    def restore_backup(file_path: os.PathLike):
        backup_path = file_path + ".bak"

        if os.path.isfile(backup_path):
            Log.info(f"Restoring backup of {file_path}...")
            shutil.copy(backup_path, file_path)
        else:
            Log.warn(f"No backup found for {file_path}, skipping...")

    @staticmethod
    def copy_files(action: Literal["patch", "restore"], patches_dir: str | Path, scripts_dir: str | Path):

        patches_path = Path(patches_dir)
        scripts_path = Path(scripts_dir)
        if not patches_path.is_absolute():
            raise Exception("The patches_dir is not absolute!")
        if not scripts_path.is_absolute():
            raise Exception("The scripts_dir is not absolute!")

        match action:
            case "patch":
                for src, dst in Patcher.files:
                    Patcher.backup_and_patch(
                        os.path.join(patches_path, src),
                        os.path.join(scripts_path, dst),
                    )

            case "restore":
                for _, dst in Patcher.files:
                    Patcher.restore_backup(
                        os.path.join(scripts_path, dst),
                    )

            case _:
                raise TypeError("Invalid action")


class Config:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path).resolve()

        if not self.config_path.is_file():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        self._load_config()

    def _load_config(self):
        spec = importlib.util.spec_from_file_location("config", self.config_path)
        module = importlib.util.module_from_spec(spec)

        if spec.loader is None:
            raise ImportError(f"Could not load module from {self.config_path}")

        spec.loader.exec_module(module)

        for key, value in vars(module).items():
            if not key.startswith("__"):
                setattr(self, key, value)

    def __repr__(self):
        return f"Config({self.config_path})"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "config_path"}

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)
