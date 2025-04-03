# Godot Build Scripts

Simple build scripts for Godot Engine (+ GodotJS!).

## 🚀 Basic usage
1. Copy and modify the configuration file: `cp config.py.sample config.py`.
2. Download the repos: `python3 godot.py repos`.
3. Build the base container: `python3 godot.py containers base`.
4. Build the desired container: `python3 godot.py containers linux`.
5. (Optional) Build mono for Godot Engine: `python3 godot.py build -t mono-glue`.
6. Build Godot Engine: `python3 godot.py build -t linux`.
