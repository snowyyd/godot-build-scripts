#!/bin/bash
set -e

OPTIND=1

export basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pushd ${basedir}

mkdir -p ${basedir}/out
mkdir -p ${basedir}/out/logs
mkdir -p ${basedir}/mono-glue

# Log output to a file automatically.
exec > >(tee -a "out/logs/build") 2>&1

# Config

# For default registry and number of cores.
if [ ! -e config.sh ]; then
  echo "No config.sh, copying default values from config.sh.in."
  cp config.sh.in config.sh
fi
source ./config.sh

if [ -z "${BUILD_NAME}" ]; then
  export BUILD_NAME="custom_build"
fi

if [ -z "${NUM_CORES}" ]; then
  export NUM_CORES=16
fi

godot_version=""
git_treeish="master"
build_classical=1
build_mono=1
build_steam=0
godotjs_ref=""
godotjs_deps_ref=""
target_os=""

while getopts "h?t:v:j:d:g:b:fsc" opt; do
  case "$opt" in
  h|\?)
    echo "Usage: $0 [OPTIONS...]"
    echo
    echo "  -v target os (e.g. linux) [mandatory]"
    echo "  -v godot version (e.g. 3.1-alpha5) [mandatory]"
    echo "  -j godotjs branch (e.g. main) [mandatory]"
    echo "  -d godotjs deps ref (e.g. v8_12.4.254.21_r13) [mandatory]"
    echo "  -g git treeish (e.g. master)"
    echo "  -b all|classical|mono (default: all)"
    echo
    exit 1
    ;;
  t)
    target_os=$OPTARG
    ;;
  v)
    godot_version=$OPTARG
    ;;
  j)
    godotjs_ref=$OPTARG
    ;;
  d)
    godotjs_deps_ref=$OPTARG
    ;;
  g)
    git_treeish=$OPTARG
    ;;
  b)
    if [ "$OPTARG" == "classical" ]; then
      build_mono=0
    elif [ "$OPTARG" == "mono" ]; then
      build_classical=0
    fi
    ;;
  esac
done

export podman=${PODMAN}

REPOSITORY_PREFIX="localhost/"
if [[ ${podman} == "docker" ]]; then
  REPOSITORY_PREFIX=""
fi

if [ -z "${target_os}" ]; then
  echo "-t <target> is mandatory!"
  exit 1
fi

if [ -z "${godot_version}" ]; then
  echo "-v <version> is mandatory!"
  exit 1
fi

if [ -z "${godotjs_ref}" ]; then
  echo "-j <branch> is mandatory!"
  exit 1
fi

if [ -z "${godotjs_deps_ref}" ]; then
  echo "-d <ref> is mandatory!"
  exit 1
fi

IFS=- read version status <<< "$godot_version"
echo "Building Godot ${version} ${status} from commit or branch ${git_treeish}."
# read -p "Is this correct (y/n)? " choice
# case "$choice" in
#   y|Y ) echo "yes";;
#   n|N ) echo "No, aborting."; exit 0;;
#   * ) echo "Invalid choice, aborting."; exit 1;;
# esac
export GODOT_VERSION_STATUS="${status}"

# if [ "${status}" == "stable" ]; then
  # build_steam=1
# fi

# macOS needs MoltenVK
if [ ! -d "deps/moltenvk" ]; then
  echo "Missing MoltenVK for macOS, downloading it."
  mkdir -p deps/moltenvk
  pushd deps/moltenvk
  curl -L -o moltenvk.tar https://github.com/godotengine/moltenvk-osxcross/releases/download/vulkan-sdk-1.3.283.0-2/MoltenVK-all.tar
  tar xf moltenvk.tar && rm -f moltenvk.tar
  mv MoltenVK/MoltenVK/include/ MoltenVK/
  mv MoltenVK/MoltenVK/static/MoltenVK.xcframework/ MoltenVK/
  popd
fi

# accesskit-c for Windows, macOS and Linux
if [ ! -d "deps/accesskit" ]; then
  echo "Missing accesskit, downloading it."
  mkdir -p deps/accesskit
  pushd deps/accesskit
  curl -L -o accesskit.zip https://github.com/godotengine/godot-accesskit-c-static/releases/download/0.15.1/accesskit-c-0.15.1.zip
  unzip -o accesskit.zip && rm -f accesskit.zip
  mv accesskit-c-* accesskit-c
  popd
fi

# Windows and macOS need ANGLE
if [ ! -d "deps/angle" ]; then
  echo "Missing ANGLE libraries, downloading them."
  mkdir -p deps/angle
  pushd deps/angle
  base_url=https://github.com/godotengine/godot-angle-static/releases/download/chromium%2F6601.2/godot-angle-static
  curl -L -o windows_arm64.zip $base_url-arm64-llvm-release.zip
  curl -L -o windows_x86_64.zip $base_url-x86_64-gcc-release.zip
  curl -L -o windows_x86_32.zip $base_url-x86_32-gcc-release.zip
  curl -L -o macos_arm64.zip $base_url-arm64-macos-release.zip
  curl -L -o macos_x86_64.zip $base_url-x86_64-macos-release.zip
  unzip -o windows_arm64.zip && rm -f windows_arm64.zip
  unzip -o windows_x86_64.zip && rm -f windows_x86_64.zip
  unzip -o windows_x86_32.zip && rm -f windows_x86_32.zip
  unzip -o macos_arm64.zip && rm -f macos_arm64.zip
  unzip -o macos_x86_64.zip && rm -f macos_x86_64.zip
  popd
fi

if [ ! -d "deps/mesa" ]; then
  echo "Missing Mesa/NIR libraries, downloading them."
  mkdir -p deps/mesa
  pushd deps/mesa
  curl -L -o mesa_arm64.zip https://github.com/godotengine/godot-nir-static/releases/download/23.1.9-1/godot-nir-static-arm64-llvm-release.zip
  curl -L -o mesa_x86_64.zip https://github.com/godotengine/godot-nir-static/releases/download/23.1.9-1/godot-nir-static-x86_64-gcc-release.zip
  curl -L -o mesa_x86_32.zip https://github.com/godotengine/godot-nir-static/releases/download/23.1.9-1/godot-nir-static-x86_32-gcc-release.zip
  unzip -o mesa_arm64.zip && rm -f mesa_arm64.zip
  unzip -o mesa_x86_64.zip && rm -f mesa_x86_64.zip
  unzip -o mesa_x86_32.zip && rm -f mesa_x86_32.zip
  popd
fi

if [ ! -d "deps/swappy" ]; then
  echo "Missing Swappy libraries, downloading them."
  mkdir -p deps/swappy
  pushd deps/swappy
  curl -L -O https://github.com/godotengine/godot-swappy/releases/download/from-source-2025-01-31/godot-swappy.7z
  7z x godot-swappy.7z && rm godot-swappy.7z
  popd
fi

# Keystore for Android editor signing
# Optional - the config.sh will be copied but if it's not filled in,
# it will do an unsigned build.
if [ ! -d "deps/keystore" ]; then
  mkdir -p deps/keystore
  cp config.sh deps/keystore/
  if [ ! -z "$GODOT_ANDROID_SIGN_KEYSTORE" ]; then
    cp "$GODOT_ANDROID_SIGN_KEYSTORE" deps/keystore/
    sed -i deps/keystore/config.sh -e "s@$GODOT_ANDROID_SIGN_KEYSTORE@/root/keystore/$GODOT_ANDROID_SIGN_KEYSTORE@"
  fi
fi

# Clone Godot, GodotJS and GodotJS deps
TARBALL_TEMPLATE_NAME="godot-${godot_version}"
TARBALL_GZIP_NAME="${TARBALL_TEMPLATE_NAME}.tar.gz"
if [ ! -f ${TARBALL_GZIP_NAME} ]; then
  git clone https://github.com/godotengine/godot git || /bin/true
  pushd git
  # git checkout -b ${git_treeish} origin/${git_treeish} || git checkout ${git_treeish}
  # git reset --hard
  # git clean -fdx
  # git pull origin ${git_treeish} || /bin/true

  # I'm not gonna make python3 a local dependency just for this simple check lol
  # Validate version
  # correct_version=$(python3 << EOF
  # import version;
  # if hasattr(version, "patch") and version.patch != 0:
  # git_version = f"{version.major}.{version.minor}.{version.patch}"
  # else:
  # git_version = f"{version.major}.{version.minor}"
  # print(git_version == "${version}")
  # EOF
  # )
  # if [[ "$correct_version" != "True" ]]; then
  #   echo "Version in version.py doesn't match the passed ${version}."
  #   exit 1
  # fi

  # Download GodotJS
  GODOTJS_MOD_DIR="modules/GodotJS"
  if [ ! -d ${GODOTJS_MOD_DIR} ]; then
    git clone --depth 1 --recursive --branch ${godotjs_ref} https://github.com/godotjs/godotjs ${GODOTJS_MOD_DIR}
  fi

  # Download GodotJS deps
  if [ ! -d ${GODOTJS_MOD_DIR}/v8 ]; then
    if [ ! -f v8.zip ]; then
      echo "Downloading v8 dependency..."
      curl -L https://github.com/ialex32x/GodotJS-Dependencies/releases/download/${godotjs_deps_ref}/${godotjs_deps_ref}.zip --output ./v8.zip
    fi

    echo "Extracting v8..."
    7z x -o${GODOTJS_MOD_DIR} ./v8.zip
    rm ./v8.zip || /bin/true
  fi

  # add GodotJS
  rm -rf ${GODOTJS_MOD_DIR}/.git
  
  # make tarball
  HEAD=$(git rev-parse $git_treeish)
  TMPDIR=$(mktemp -d -t godot-XXXXXX)

  echo "Generating tarball for revision $HEAD with folder name '$TARBALL_TEMPLATE_NAME'."
  echo
  echo "The tarball will be written to the parent folder:"
  echo "    $(pwd)/$TARBALL_GZIP_NAME"

  tar --exclude='.git' --exclude 'v8.zip' -cf $TMPDIR/$TARBALL_TEMPLATE_NAME.tar --transform "s,^,$TARBALL_TEMPLATE_NAME/," -C . $(ls -A)

  # Adding custom .git/HEAD to tarball so that we can generate GODOT_VERSION_HASH.
  pushd $TMPDIR
  mkdir -p $TARBALL_TEMPLATE_NAME/.git
  echo $HEAD > $TARBALL_TEMPLATE_NAME/.git/HEAD
  tar -uf $TARBALL_TEMPLATE_NAME.tar $TARBALL_TEMPLATE_NAME
  popd
  gzip -c $TMPDIR/$TARBALL_TEMPLATE_NAME.tar > ../$TARBALL_GZIP_NAME
  rm -rf $TMPDIR

  popd
else
  echo "${TARBALL_GZIP_NAME} already exists, skipping downloads..."
fi

export podman_run="${podman} run -it --rm --env BUILD_NAME=${BUILD_NAME} --env GODOT_VERSION_STATUS=${GODOT_VERSION_STATUS} --env NUM_CORES=${NUM_CORES} --env CLASSICAL=${build_classical} --env MONO=${build_mono} -v ${basedir}/${TARBALL_GZIP_NAME}:/root/godot.tar.gz -v ${basedir}/mono-glue:/root/mono-glue -w /root/"
export img_version=$IMAGE_VERSION

case "$target_os" in
  mono-glue)
    echo "Building the common mono-glue..."
    mkdir -p ${basedir}/mono-glue
    ${podman_run} -v ${basedir}/build-mono-glue:/root/build ${REPOSITORY_PREFIX}godot-linux:${img_version} bash build/build.sh 2>&1 | tee ${basedir}/out/logs/mono-glue
    echo "Done! Now exec this script again with a real target os"
    ;;
  windows)
    echo "Building for Windows..."
    mkdir -p ${basedir}/out/windows
    ${podman_run} -v ${basedir}/build-windows:/root/build -v ${basedir}/out/windows:/root/out -v ${basedir}/deps/angle:/root/angle -v ${basedir}/deps/mesa:/root/mesa -v ${basedir}/deps/accesskit:/root/accesskit --env STEAM=${build_steam} ${REPOSITORY_PREFIX}godot-windows:${img_version} bash build/build.sh 2>&1 | tee ${basedir}/out/logs/windows
    ;;
  linux)
    echo "Building for Linux..."
    mkdir -p ${basedir}/out/linux
    ${podman_run} -v ${basedir}/build-linux:/root/build -v ${basedir}/out/linux:/root/out -v ${basedir}/deps/accesskit:/root/accesskit ${REPOSITORY_PREFIX}godot-linux:${img_version} bash build/build.sh 2>&1 | tee ${basedir}/out/logs/linux
    ;;
  web)
    echo "Building for web..."
    mkdir -p ${basedir}/out/web
    ${podman_run} -v ${basedir}/build-web:/root/build -v ${basedir}/out/web:/root/out ${REPOSITORY_PREFIX}godot-web:${img_version} bash build/build.sh 2>&1 | tee ${basedir}/out/logs/web
    ;;
  macos)
    echo "Building for macOS..."
    mkdir -p ${basedir}/out/macos
    ${podman_run} -v ${basedir}/build-macos:/root/build -v ${basedir}/out/macos:/root/out -v ${basedir}/deps/accesskit:/root/accesskit -v ${basedir}/deps/moltenvk:/root/moltenvk -v ${basedir}/deps/angle:/root/angle ${REPOSITORY_PREFIX}godot-osx:${img_version} bash build/build.sh 2>&1 | tee ${basedir}/out/logs/macos
    ;;
  android)
    echo "Building for android..."
    mkdir -p ${basedir}/out/android
    ${podman_run} -v ${basedir}/build-android:/root/build -v ${basedir}/out/android:/root/out -v ${basedir}/deps/swappy:/root/swappy -v ${basedir}/deps/keystore:/root/keystore ${REPOSITORY_PREFIX}godot-android:${img_version} bash build/build.sh 2>&1 | tee ${basedir}/out/logs/android
    ;;
  ios)
    echo "Building for iOS..."
    mkdir -p ${basedir}/out/ios
    ${podman_run} -v ${basedir}/build-ios:/root/build -v ${basedir}/out/ios:/root/out ${REPOSITORY_PREFIX}godot-ios:${img_version} bash build/build.sh 2>&1 | tee ${basedir}/out/logs/ios
    ;;
  *)
    echo "Valid targets: mono-glue, windows, linux, macos, web, android, ios"
    exit 1
    ;;
esac

uid=$(id -un)
gid=$(id -gn)
if [ ! -z "$SUDO_UID" ]; then
  uid="${SUDO_UID}"
  gid="${SUDO_GID}"
fi
chown -R -f $uid:$gid ${basedir}/git ${basedir}/out ${basedir}/mono-glue ${basedir}/godot*.tar.gz

popd
