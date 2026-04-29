#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/SMILES2DockingFULLBuild"
DIST_ROOT="$BUILD_ROOT/dist"
WORK_ROOT="$BUILD_ROOT/build"
RELEASE_ROOT="$PROJECT_ROOT/release/linux"
APPDIR_ROOT="$RELEASE_ROOT/SMILES2DockingFULL-x86_64.AppDir"
PYINSTALLER_DIST="$DIST_ROOT/SMILES2DockingFULL"
SOURCE_ARCHIVE="$RELEASE_ROOT/SMILES2DockingFULL-source.tar.gz"
PORTABLE_ARCHIVE="$RELEASE_ROOT/SMILES2DockingFULL-linux-x86_64.tar.gz"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Este script deve ser executado em Linux."
  exit 1
fi

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "PyInstaller nao encontrado no PATH."
  exit 1
fi

mkdir -p "$RELEASE_ROOT"
rm -rf "$APPDIR_ROOT" "$PORTABLE_ARCHIVE" "$SOURCE_ARCHIVE"

pyinstaller \
  --noconfirm \
  --clean \
  --distpath "$DIST_ROOT" \
  --workpath "$WORK_ROOT" \
  "$PROJECT_ROOT/packaging/linux/smiles2docking.spec"

mkdir -p "$APPDIR_ROOT/usr/bin"
mkdir -p "$APPDIR_ROOT/usr/lib"
mkdir -p "$APPDIR_ROOT/usr/share/applications"
mkdir -p "$APPDIR_ROOT/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$APPDIR_ROOT/usr/share/doc/smiles2dockingfull"

cp -R "$PYINSTALLER_DIST" "$APPDIR_ROOT/usr/lib/smiles2dockingfull"
cp "$PROJECT_ROOT/packaging/linux/AppRun" "$APPDIR_ROOT/AppRun"
cp "$PROJECT_ROOT/packaging/linux/run_smiles2docking.sh" "$APPDIR_ROOT/usr/bin/SMILES2DockingFULL"
cp "$PROJECT_ROOT/packaging/linux/SMILES2DockingDesktop.desktop" "$APPDIR_ROOT/usr/share/applications/SMILES2DockingFULL.desktop"
cp "$PROJECT_ROOT/packaging/linux/SMILES2DockingDesktop.desktop" "$APPDIR_ROOT/SMILES2DockingFULL.desktop"
cp "$PROJECT_ROOT/packaging/linux/smiles2docking.svg" "$APPDIR_ROOT/usr/share/icons/hicolor/scalable/apps/smiles2docking.svg"
cp "$PROJECT_ROOT/packaging/linux/smiles2docking.svg" "$APPDIR_ROOT/smiles2docking.svg"

cp "$PROJECT_ROOT/LICENSE" "$APPDIR_ROOT/usr/share/doc/smiles2dockingfull/LICENSE"
cp "$PROJECT_ROOT/AUTHORS.md" "$APPDIR_ROOT/usr/share/doc/smiles2dockingfull/AUTHORS.md"
cp "$PROJECT_ROOT/CITATION.cff" "$APPDIR_ROOT/usr/share/doc/smiles2dockingfull/CITATION.cff"
cp "$PROJECT_ROOT/README.md" "$APPDIR_ROOT/usr/share/doc/smiles2dockingfull/README.md"
cp "$PROJECT_ROOT/docs/DISTRIBUTION.md" "$APPDIR_ROOT/usr/share/doc/smiles2dockingfull/DISTRIBUTION.md"
cp "$PROJECT_ROOT/docs/THIRD_PARTY_NOTICES.md" "$APPDIR_ROOT/usr/share/doc/smiles2dockingfull/THIRD_PARTY_NOTICES.md"
cp "$PROJECT_ROOT/docs/LINUX_DISTRIBUTION.md" "$APPDIR_ROOT/usr/share/doc/smiles2dockingfull/LINUX_DISTRIBUTION.md"

chmod +x "$APPDIR_ROOT/AppRun"
chmod +x "$APPDIR_ROOT/usr/bin/SMILES2DockingFULL"

tar \
  --exclude='./.git' \
  --exclude='./.pytest_cache' \
  --exclude='./build' \
  --exclude='./dist' \
  --exclude='./release' \
  --exclude='./__pycache__' \
  --exclude='./.mypy_cache' \
  -czf "$SOURCE_ARCHIVE" \
  -C "$PROJECT_ROOT" .

tar -czf "$PORTABLE_ARCHIVE" -C "$RELEASE_ROOT" "$(basename "$APPDIR_ROOT")"

if command -v appimagetool >/dev/null 2>&1; then
  ARCH=x86_64 appimagetool "$APPDIR_ROOT" "$RELEASE_ROOT/SMILES2DockingFULL-x86_64.AppImage"
fi

cat <<EOF
Build Linux concluido.
- AppDir: $APPDIR_ROOT
- Portable tar.gz: $PORTABLE_ARCHIVE
- Source tar.gz: $SOURCE_ARCHIVE
EOF
