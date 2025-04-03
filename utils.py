import importlib.util
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import TypedDict, Any, List, Dict, Tuple, Literal, Optional

if __name__ == "__main__":
    raise Exception("This module cannot be run directly")


def run_command_safe(command: list[str], cwd: str = ".") -> Optional[str]:
    try:
        result = subprocess.run(command, cwd=cwd, check=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return None


class Colors:
    RESET = "\033[0m"

    # Regular Colors
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = (
        "\033[30m",
        "\033[31m",
        "\033[32m",
        "\033[33m",
        "\033[34m",
        "\033[35m",
        "\033[36m",
        "\033[37m",
    )

    # Bright Colors
    BRIGHT_BLACK, BRIGHT_RED, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_BLUE, BRIGHT_MAGENTA, BRIGHT_CYAN, BRIGHT_WHITE = (
        "\033[90m",
        "\033[91m",
        "\033[92m",
        "\033[93m",
        "\033[94m",
        "\033[95m",
        "\033[96m",
        "\033[97m",
    )

    # Styles
    BOLD, UNDERLINE, REVERSED = "\033[1m", "\033[4m", "\033[7m"

    # Background Colors
    BG_BLACK, BG_RED, BG_GREEN, BG_YELLOW, BG_BLUE, BG_MAGENTA, BG_CYAN, BG_WHITE = (
        "\033[40m",
        "\033[41m",
        "\033[42m",
        "\033[43m",
        "\033[44m",
        "\033[45m",
        "\033[46m",
        "\033[47m",
    )

    # Bright Backgrounds
    (
        BG_BRIGHT_BLACK,
        BG_BRIGHT_RED,
        BG_BRIGHT_GREEN,
        BG_BRIGHT_YELLOW,
        BG_BRIGHT_BLUE,
        BG_BRIGHT_MAGENTA,
        BG_BRIGHT_CYAN,
        BG_BRIGHT_WHITE,
    ) = ("\033[100m", "\033[101m", "\033[102m", "\033[103m", "\033[104m", "\033[105m", "\033[106m", "\033[107m")

    @staticmethod
    def color_text(text: str, color: str) -> str:
        return f"{color}{text}{Colors.RESET}"

    @staticmethod
    def color_text_bold(text: str, color: str) -> str:
        return f"{color}{Colors.BOLD}{text}{Colors.RESET}"


class Log:
    @staticmethod
    def warn(text: str) -> None:
        print(Colors.color_text_bold("WARN:", Colors.YELLOW), text)

    @staticmethod
    def err(text: str) -> None:
        print(Colors.color_text_bold("ERR:", Colors.RED), text)

    @staticmethod
    def info(text: str) -> None:
        print(Colors.color_text_bold("INFO:", Colors.GREEN), text)

    @staticmethod
    def debug(text: str) -> None:
        print(Colors.color_text_bold("DEBUG:", Colors.CYAN), text)

    @staticmethod
    def kv(k: str, v: str) -> None:
        print(Colors.color_text(f"{k}:", Colors.GREEN), v)


class CMDChecker:
    commands_to_check: List[str] = ["bash", "git", "curl", "docker", "7z", "tar", "unzip", "gzip", "jq"]

    @staticmethod
    def check(cmds: Optional[List[str]] = None):
        cmds = cmds or CMDChecker.commands_to_check
        missing = [cmd for cmd in set(cmds) if shutil.which(cmd) is None]

        if missing:
            Log.err(f"Missing commands: {', '.join(missing)}")
            raise SystemExit(1)

    @staticmethod
    def checkSingle(cmd: str):
        if shutil.which(cmd) is None:
            Log.err(f"Missing command: {cmd}")
            raise SystemExit(1)


class Git:
    @staticmethod
    def clone_repo_no_depth(repo_url: str, branch: str, target_dir: str | Path) -> None:
        CMDChecker.checkSingle("git")
        cmd = shlex.split(f"git clone --recursive --depth 1 --branch {branch} {repo_url} {str(Path(target_dir))}")
        subprocess.run(cmd, check=True)

    @staticmethod
    def clone_and_checkout(repo_url: str, dest_dir: str, git_ref: Optional[str] = None) -> None:
        if not os.path.exists(dest_dir):
            run_command_safe(["git", "clone", "--recursive", repo_url, dest_dir])
        if git_ref and os.path.isdir(dest_dir):
            run_command_safe(["git", "fetch", "origin"], cwd=dest_dir)
            if not run_command_safe(["git", "reset", "--hard", f"origin/{git_ref}"], cwd=dest_dir):
                run_command_safe(["git", "reset", "--hard", git_ref], cwd=dest_dir)
            run_command_safe(["git", "clean", "-xdf"], cwd=dest_dir)

    @staticmethod
    def get_commit_hash(repo_path: str | Path):
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_path, text=True).strip()
        except subprocess.CalledProcessError:
            return None


class Containers:
    build_targets: List[str] = ["base", "windows", "linux", "web", "osx", "android", "ios"]

    @staticmethod
    def build(tool: str, target: str, containers_dir: str | Path):
        CMDChecker.checkSingle(tool)
        Log.info(f"Building {target} using {tool}...")

        containers_dir = Path(containers_dir).resolve()

        cmd = [
            tool,
            "build",
            "--build-arg=img_version=latest",
            "-t",
            f"godot-{'fedora' if target == 'base' else target}:latest",
            "-f",
            str(containers_dir / f"Dockerfile.{target}"),
            str(containers_dir),
        ]

        subprocess.run(cmd, check=True)


class Patcher:
    files = [
        # format (source [patches folder], dest [godot-build-scripts folder])
        ("build-windows.sh", "build-windows/build.sh"),
        ("build-linux.sh", "build-linux/build.sh"),
    ]

    @staticmethod
    def backup_and_patch(patch_file: str | Path, dest_file: str | Path):
        patch_file = Path(patch_file)
        dest_file = Path(dest_file)

        if not dest_file.exists():
            raise FileNotFoundError(f"Destination file {dest_file} does not exist.")

        backup_path = dest_file.with_suffix(dest_file.suffix + ".bak")

        if not backup_path.exists():
            shutil.copy(dest_file, backup_path)

        Log.info(f"Patching {dest_file}...")
        shutil.copy(patch_file, dest_file)

    @staticmethod
    def restore_backup(file_path: str | Path):
        file_path = Path(file_path)
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")

        if backup_path.exists():
            Log.info(f"Restoring backup of {file_path}...")
            shutil.copy(backup_path, file_path)
        else:
            Log.warn(f"No backup found for {file_path}, skipping...")

    @staticmethod
    def copy_files(action: str, patches_dir: str | Path, scripts_dir: str | Path):
        patches_path = Path(patches_dir).resolve()
        scripts_path = Path(scripts_dir).resolve()

        if not patches_path.is_absolute():
            raise ValueError("The patches_dir must be an absolute path.")
        if not scripts_path.is_absolute():
            raise ValueError("The scripts_dir must be an absolute path.")

        actions = {
            "patch": lambda: [
                Patcher.backup_and_patch(patches_path / src, scripts_path / dst) for src, dst in Patcher.files
            ],
            "restore": lambda: [Patcher.restore_backup(scripts_path / dst) for _, dst in Patcher.files],
        }

        try:
            actions[action]()
        except KeyError:
            raise ValueError("Invalid action. Use 'patch' or 'restore'.")


class Config:
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path).resolve()

        if not self.config_path.is_file():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        self._load_config()

    def _load_config(self) -> None:
        spec = importlib.util.spec_from_file_location("config", self.config_path)

        if not spec or not spec.loader:
            raise ImportError(f"Could not load module from {self.config_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.__dict__.update({k: v for k, v in vars(module).items() if not k.startswith("__")})

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.config_path})"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "config_path"}

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)


def download_file(url: str, destination: str):
    destination = Path(destination)

    with urllib.request.urlopen(url) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        block_size = 8192  # 8 KB
        downloaded = 0

        Log.info(
            f"Downloading: {url} -> {destination} ({total_size / 1024:.2f} KB)"
            if total_size
            else f"Downloading: {url} -> {destination}"
        )

        with open(destination, "wb") as out_file:
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                out_file.write(buffer)
                downloaded += len(buffer)

                if total_size:
                    percentage = downloaded / total_size * 100
                    progress = int(50 * downloaded / total_size)
                    sys.stdout.write(
                        f"\r[{'#' * progress}{'.' * (50 - progress)}] {downloaded / 1024:.2f} KB ({percentage:.2f}%)"
                    )
                    sys.stdout.flush()
            print()


class FileExtractor:
    @staticmethod
    def extract_tar(file_path: Path, dest_dir: Path):
        with tarfile.open(file_path, "r:*") as tar:
            tar.extractall(dest_dir)

    @staticmethod
    def extract_zip(file_path: Path, dest_dir: Path):
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(dest_dir)

    @staticmethod
    def extract_7z(file_path: Path, dest_dir: Path):
        subprocess.run(["7z", "x", str(file_path), f"-o{dest_dir}"], capture_output=True, text=True, check=True)

    @staticmethod
    def extract_file(file_path: str, dest_dir: str = "."):
        file_path = Path(file_path)
        dest_dir = Path(dest_dir)

        formats = {
            (".tar", ".tar.gz", ".tar.bz2", ".tar.xz"): FileExtractor.extract_tar,
            (".zip",): FileExtractor.extract_zip,
            (".7z",): FileExtractor.extract_7z,
        }

        suffix = "".join(file_path.suffixes)
        for extensions, extractor in formats.items():
            if suffix in extensions:
                extractor(file_path, dest_dir)
                Log.info(f"File {file_path} extracted to {dest_dir}")
                return

        raise ValueError(f"Unsupported file type: {file_path}")


class DependencyConfig(TypedDict):
    target: List[Literal["windows", "macos", "linux", "android", "ios"]]
    base_url: str
    files: Dict[str, str]  # {"archivo_remoto": "archivo_local"}
    extract: Literal["extract_tar", "extract_zip", "extract_7z"]
    move: List[Tuple[str, str]]  # [(origen, destino)]


class Dependencies:
    @staticmethod
    def download(url: str, dest: str | Path, filename: str) -> bool:
        dest = Path(dest)

        # if dest.is_dir():
        #     Log.warn(f"{dest} already exists, skipping download...")
        #     return False

        os.makedirs(dest, exist_ok=True)
        download_file(url, dest / filename)
        return True

    @staticmethod
    def ensure(dependency_name: str, dependency: DependencyConfig, current_target: str, base_path: Path):
        full_path = base_path / dependency_name

        if full_path.exists():
            Log.warn(f"{full_path} already exists, skipping download...")
            return

        if "target" not in dependency or current_target in dependency["target"]:
            Log.info(f"Ensuring dependency '{dependency_name}'...")
            for remote_name, local_name in dependency["files"].items():
                # Log.debug(f"Downloading {dependency['base_url']}/{remote_name} -> {full_path}/{local_name}")
                ret = Dependencies.download(f"{dependency['base_url']}/{remote_name}", full_path, local_name)
                if not ret:
                    continue
                # Log.debug(f"Extracting {full_path / local_name} -> {full_path}")
                FileExtractor.extract_file(full_path / local_name, full_path)
                # Log.debug(f"Unlinking {full_path / local_name}")
                (full_path / local_name).unlink(True)

                if "move" in dependency:
                    for src, dst in dependency["move"]:
                        src_path = full_path / src
                        dst_path = full_path / dst
                        if src_path.exists() and not dst_path.exists():
                            # Log.debug(f"Renaming {src_path} -> {dst_path}")
                            src_path.rename(dst_path)
