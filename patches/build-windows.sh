#!/bin/bash
set -e

# Based on: https://github.com/godotengine/godot-build-scripts/blob/3348432f38773fcaaba0d90432832663fe65cc4d/build-windows/build.sh

if [[ "$JS_ENGINE" == "v8" ]]; then
  echo "ERR: v8 is not yet supported on mingw builds."
  exit 1
fi

# Config

export SCONS="scons -j${NUM_CORES} verbose=no warnings=no progress=no"
export OPTIONS="production=yes use_mingw=yes angle_libs=/root/angle mesa_libs=/root/mesa d3d12=yes accesskit_sdk_path=/root/accesskit/accesskit-c"
export OPTIONS_MONO="module_mono_enabled=yes"
export OPTIONS_LLVM="use_llvm=yes mingw_prefix=/root/llvm-mingw"
export TERM=xterm

# Ensure workspace
FOLDER_NAME="godot"
if [[ "$DEBUG_MODE" -eq 1 && -d "$FOLDER_NAME" ]]; then
    echo "The debug mode is enabled, using the already existing folder..."
    cd $FOLDER_NAME
else
    rm -rf $FOLDER_NAME
    mkdir $FOLDER_NAME
    cd $FOLDER_NAME
    tar xf /root/godot.tar.gz --strip-components=1
fi

# Setup
case "$JS_ENGINE" in
  None) echo "JS_ENGINE is not set, GodotJS will not be compiled";;
  v8) echo "Using v8 JS Engine!"; BUILD_NAME="${BUILD_NAME}-v8";;
  qjs_ng) echo "Using QuickJS-NG JS Engine!"; OPTIONS="${OPTIONS} use_quickjs_ng=yes"; BUILD_NAME="${BUILD_NAME}-ng";;
  qjs) echo "Using QuickJS JS Engine!"; OPTIONS="${OPTIONS} use_quickjs=yes"; BUILD_NAME="${BUILD_NAME}-qjs";;
  *) echo "Invalid js engine. Available engines: v8, qjs_ng, qjs"; exit 1;;
esac

if [[ "$JS_ENGINE" != "None" ]]; then
  # GodotJS: compilation fix
  sed -i 's|../../|../|' -e modules/GodotJS/weaver-editor/jsb_editor_helper.cpp

  # GodotJS: fix for mingw
  sed -i -e 's/winmm.lib/-lwinmm/' -e 's/Dbghelp.lib/-ldbghelp/' modules/GodotJS/SCsub
  sed -i -E 's/lws_support = .+$/lws_support = None/' modules/GodotJS/SCsub
fi

# Classical

if [ "${CLASSICAL}" == "1" ]; then
  echo "Starting classical build for Windows..."

  $SCONS platform=windows arch=x86_64 $OPTIONS target=editor
  mkdir -p /root/out/x86_64/tools
  cp -rvp bin/* /root/out/x86_64/tools
  rm -rf bin

  $SCONS platform=windows arch=x86_64 $OPTIONS target=template_debug
  $SCONS platform=windows arch=x86_64 $OPTIONS target=template_release
  mkdir -p /root/out/x86_64/templates
  cp -rvp bin/* /root/out/x86_64/templates
  rm -rf bin

  # $SCONS platform=windows arch=x86_32 $OPTIONS target=editor
  # mkdir -p /root/out/x86_32/tools
  # cp -rvp bin/* /root/out/x86_32/tools
  # rm -rf bin

  # $SCONS platform=windows arch=x86_32 $OPTIONS target=template_debug
  # $SCONS platform=windows arch=x86_32 $OPTIONS target=template_release
  # mkdir -p /root/out/x86_32/templates
  # cp -rvp bin/* /root/out/x86_32/templates
  # rm -rf bin

  # $SCONS platform=windows arch=arm64 $OPTIONS $OPTIONS_LLVM target=editor
  # mkdir -p /root/out/arm64/tools
  # cp -rvp bin/* /root/out/arm64/tools
  # rm -rf bin

  # $SCONS platform=windows arch=arm64 $OPTIONS $OPTIONS_LLVM target=template_debug
  # $SCONS platform=windows arch=arm64 $OPTIONS $OPTIONS_LLVM target=template_release
  # mkdir -p /root/out/arm64/templates
  # cp -rvp bin/* /root/out/arm64/templates
  # rm -rf bin

  if [ "${STEAM}" == "1" ]; then
    build_name=${BUILD_NAME}
    BUILD_NAME="${BUILD_NAME}-steam"
    $SCONS platform=windows arch=x86_64 $OPTIONS target=editor steamapi=yes
    # $SCONS platform=windows arch=x86_32 $OPTIONS target=editor steamapi=yes
    mkdir -p /root/out/steam
    cp -rvp bin/* /root/out/steam
    rm -rf bin
    BUILD_NAME=${build_name}
  fi
fi

# Mono

if [ "${MONO}" == "1" ]; then
  echo "Starting Mono build for Windows..."

  cp -r /root/mono-glue/GodotSharp/GodotSharp/Generated modules/mono/glue/GodotSharp/GodotSharp/
  cp -r /root/mono-glue/GodotSharp/GodotSharpEditor/Generated modules/mono/glue/GodotSharp/GodotSharpEditor/

  $SCONS platform=windows arch=x86_64 $OPTIONS $OPTIONS_MONO target=editor
  ./modules/mono/build_scripts/build_assemblies.py --godot-output-dir=./bin --godot-platform=windows
  mkdir -p /root/out/x86_64/tools-mono
  cp -rvp bin/* /root/out/x86_64/tools-mono
  rm -rf bin

  $SCONS platform=windows arch=x86_64 $OPTIONS $OPTIONS_MONO target=template_debug
  $SCONS platform=windows arch=x86_64 $OPTIONS $OPTIONS_MONO target=template_release
  mkdir -p /root/out/x86_64/templates-mono
  cp -rvp bin/* /root/out/x86_64/templates-mono
  rm -rf bin

  # $SCONS platform=windows arch=x86_32 $OPTIONS $OPTIONS_MONO target=editor
  # ./modules/mono/build_scripts/build_assemblies.py --godot-output-dir=./bin --godot-platform=windows
  # mkdir -p /root/out/x86_32/tools-mono
  # cp -rvp bin/* /root/out/x86_32/tools-mono
  # rm -rf bin

  # $SCONS platform=windows arch=x86_32 $OPTIONS $OPTIONS_MONO target=template_debug
  # $SCONS platform=windows arch=x86_32 $OPTIONS $OPTIONS_MONO target=template_release
  # mkdir -p /root/out/x86_32/templates-mono
  # cp -rvp bin/* /root/out/x86_32/templates-mono
  # rm -rf bin

  # $SCONS platform=windows arch=arm64 $OPTIONS $OPTIONS_MONO $OPTIONS_LLVM target=editor
  # ./modules/mono/build_scripts/build_assemblies.py --godot-output-dir=./bin --godot-platform=windows
  # mkdir -p /root/out/arm64/tools-mono
  # cp -rvp bin/* /root/out/arm64/tools-mono
  # rm -rf bin

  # $SCONS platform=windows arch=arm64 $OPTIONS $OPTIONS_MONO $OPTIONS_LLVM target=template_debug
  # $SCONS platform=windows arch=arm64 $OPTIONS $OPTIONS_MONO $OPTIONS_LLVM target=template_release
  # mkdir -p /root/out/arm64/templates-mono
  # cp -rvp bin/* /root/out/arm64/templates-mono
  # rm -rf bin
fi

echo "Windows build successful"
