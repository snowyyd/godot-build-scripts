#!/bin/bash
set -e

# Based on: https://github.com/godotengine/godot-build-scripts/blob/3348432f38773fcaaba0d90432832663fe65cc4d/build-windows/build.sh

# Config

export SCONS="scons -j${NUM_CORES} verbose=no warnings=no progress=no"
export OPTIONS="production=yes use_mingw=yes angle_libs=/root/angle mesa_libs=/root/mesa d3d12=yes accesskit_sdk_path=/root/accesskit/accesskit-c"
export OPTIONS_MONO="module_mono_enabled=yes"
export OPTIONS_LLVM="use_llvm=yes mingw_prefix=/root/llvm-mingw"
export TERM=xterm

# Setup
case "$1" in
  v8) echo "Using v8 JS Engine!"; BUILD_NAME="${BUILD_NAME}.v8";;
  qjs_ng) echo "Using QuickJS-NG JS Engine!"; OPTIONS="${OPTIONS} use_quickjs_ng=yes"; BUILD_NAME="${BUILD_NAME}.ng";;
  qjs) echo "Using QuickJS JS Engine!"; OPTIONS="${OPTIONS} use_quickjs=yes"; BUILD_NAME="${BUILD_NAME}.qjs";;
  *) echo "Usage: $0 <js engine> (Available engines: v8, qjs_ng, qjs)"; exit 1;;
esac

rm -rf godot
mkdir godot
cd godot
tar xf /root/godot.tar.gz --strip-components=1

# GodotJS: fix for mingw
sed -i -e 's/winmm.lib/-lwinmm/' -e 's/Dbghelp.lib/-ldbghelp/' modules/GodotJS/SCsub

if [[ "$1" == "v8" ]]; then
  # TODO: fix v8 on mingw
  # sed -i -e 's/v8_monolith.lib/libv8_monolith.a/' modules/GodotJS/SCsub
  echo "v8 builds are not yet supported on mingw!"
  exit 1
else
  # TODO: fix lws on mingw
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

  # if [ "${STEAM}" == "1" ]; then
  #   build_name=${BUILD_NAME}
  #   export BUILD_NAME="steam"
  #   $SCONS platform=windows arch=x86_64 $OPTIONS target=editor steamapi=yes
  #   $SCONS platform=windows arch=x86_32 $OPTIONS target=editor steamapi=yes
  #   mkdir -p /root/out/steam
  #   cp -rvp bin/* /root/out/steam
  #   rm -rf bin
  #   export BUILD_NAME=${build_name}
  # fi
fi

# Mono

if [ "${MONO}" == "1" ]; then
  echo "Starting Mono build for Windows..."
  BUILD_NAME="mono.${BUILD_NAME}"

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
