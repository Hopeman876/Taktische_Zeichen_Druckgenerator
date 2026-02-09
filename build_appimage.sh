#!/usr/bin/env bash

# https://github.com/niess/python-appimage/releases
# Hinweis: Standard-Build (cp313) verwenden, NICHT free-threaded (cp313t),
# da PyQt6 und Pillow keine kompatiblen Wheels fuer free-threaded Python liefern.
BASE_PYTHON_IMAGE=https://github.com/niess/python-appimage/releases/download/python3.13/python3.13.9-cp313-cp313-manylinux_2_28_x86_64.AppImage
BASE_APP_IMAGE=https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-940-x86_64.AppImage

set -e  # Exit on error

SOURCE_DIR=$(pwd)
BUILD_TMP_DIR=$(mktemp -d)
TOOLS_TMP_DIR="/tmp/appimage"
APPIMAGE_BASE="python.AppImage"
APPIMAGE_TOOL="appimagetool.AppImage"

VERSION=$(grep "PROGRAM_VERSION = " constants.py | cut -d= -f2 | tr -d '[:space:]"')

echo "=== Taktische Zeichen Druckgenerator v${VERSION} - AppImage Build ==="

mkdir -p "$TOOLS_TMP_DIR"

# AppImage Root base fuer Python herunterladen
if [ ! -f "$TOOLS_TMP_DIR/$APPIMAGE_BASE" ]; then
    echo "Lade AppImage-Base herunter..."
    wget "$BASE_PYTHON_IMAGE" -O "$TOOLS_TMP_DIR/$APPIMAGE_BASE"
    chmod +x "$TOOLS_TMP_DIR/$APPIMAGE_BASE"
fi

# AppImage Tool herunterladen
if [ ! -f "$TOOLS_TMP_DIR/$APPIMAGE_TOOL" ]; then
    echo "Lade AppImage-Tool herunter..."
    wget "$BASE_APP_IMAGE" -O "$TOOLS_TMP_DIR/$APPIMAGE_TOOL"
    chmod +x "$TOOLS_TMP_DIR/$APPIMAGE_TOOL"
fi

# Extrahieren
echo "Bereite Base Image vor..."
cd "$BUILD_TMP_DIR"
"$TOOLS_TMP_DIR/$APPIMAGE_BASE" --appimage-extract
mv squashfs-root AppDir

# Applikation installieren
mkdir -p AppDir/app

echo "Kopiere Programmdateien..."
cd "$SOURCE_DIR"
cp *.py "$BUILD_TMP_DIR/AppDir/app"
cp -r gui "$BUILD_TMP_DIR/AppDir/app"
cp -r resources "$BUILD_TMP_DIR/AppDir/app"

# Logo fuer Desktop-Integration separat kopieren
cp resources/Logo.png "$BUILD_TMP_DIR/AppDir/logo.png"

# Dependencies installieren
echo "Installiere Python-Dependencies..."
cd "$BUILD_TMP_DIR"
mkdir -p AppDir/packages
"$BUILD_TMP_DIR/AppDir/usr/bin/python3" -m pip install \
    -r "$SOURCE_DIR/requirements.txt" \
    --target="$BUILD_TMP_DIR/AppDir/packages" \
    --no-cache-dir

# AppRun patchen
echo "Patche AppRun..."
cd "$BUILD_TMP_DIR/AppDir"
head --lines=-2 AppRun > AppRun.patched
cat >> AppRun.patched << 'APPRUN_EOF'
export PYTHONPATH="${APPDIR}/packages:${APPDIR}/app:${PYTHONPATH}"
exec "${APPDIR}/usr/bin/python3" "${APPDIR}/app/main.py" "$@"
APPRUN_EOF
mv AppRun.patched AppRun
chmod +x AppRun

# Applikation fuer Desktop vorbereiten
echo "Vorbereiten Desktopintegration..."
cd "$BUILD_TMP_DIR/AppDir"
rm -f python.png
rm -f *.desktop

cat > taktische-zeichen-druckgenerator.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Type=Application
Name=Taktische Zeichen Druckgenerator
Exec=AppRun
Comment=Tool zur Druckvorbereitung von taktischen Zeichen
Icon=logo
Categories=Graphics;
Terminal=false
DESKTOP_EOF

mkdir -p "$BUILD_TMP_DIR/AppDir/usr/share/applications"
cp taktische-zeichen-druckgenerator.desktop "$BUILD_TMP_DIR/AppDir/usr/share/applications/"

echo "AppImage vorbereitet unter $BUILD_TMP_DIR/AppDir"

# AppImage erzeugen
echo "Baue AppImage..."
cd "$SOURCE_DIR"
"$TOOLS_TMP_DIR/$APPIMAGE_TOOL" -s deploy "$BUILD_TMP_DIR/AppDir/usr/share/applications/taktische-zeichen-druckgenerator.desktop"

echo "=== AppImage Build abgeschlossen ==="
