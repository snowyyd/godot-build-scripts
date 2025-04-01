# Godot Build Scripts

Simple build scripts for Godot Engine (+ GodotJS!).

## 🚀 Basic usage
1. Download the repos: `bash download-repos.sh`.
2. Build the base container: `bash build-containers.sh base`.
3. Build the desired container: `bash build-containers.sh linux`.
4. (Optional) Build mono for Godot Engine: `bash build-godot.sh -t mono-glue`.
5. Build Godot Engine: `bash build-godot.sh -t linux`.
