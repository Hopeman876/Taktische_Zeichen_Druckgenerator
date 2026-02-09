#!/usr/bin/env bash

# https://github.com/niess/python-appimage/releases
BASE_PYTHON_IMAGE=https://github.com/niess/python-appimage/releases/download/python3.14/python3.14.0-cp314-cp314t-manylinux_2_28_x86_64.AppImage
BASE_APP_IMAGE=https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-940-x86_64.AppImage

set -e  # Exit on error

SOURCE_DIR=$(pwd $0)
BUILD_TMP_DIR=$(mktemp -d)
TOOLS_TMP_DIR="/tmp/appimage"
APPIMAGE_BASE="python.AppImage"
APPIMAGE_TOOL="appimagetool.AppImage"

VERSION=$(grep "PROGRAM_VERSION = " constants.py | cut -d= -f2 | tr -d '[:space:]"')

mkdir -p $TOOLS_TMP_DIR

# AppImage Root base für Python herunterladen
if [ ! -f "$TOOLS_TMP_DIR/$APPIMAGE_BASE" ]; then
    echo "Lade AppImage-Base herunter..."
    wget $BASE_PYTHON_IMAGE -O $TOOLS_TMP_DIR/$APPIMAGE_BASE
    chmod +x $TOOLS_TMP_DIR/$APPIMAGE_BASE
fi

# AppImage Tool herunterladen
if [ ! -f "$TOOLS_TMP_DIR/$APPIMAGE_TOOL" ]; then
    echo "Lade AppImage-Tool herunter..."
    wget $BASE_APP_IMAGE -O $TOOLS_TMP_DIR/$APPIMAGE_TOOL
    chmod +x $TOOLS_TMP_DIR/$APPIMAGE_TOOL
fi

# Extrahieren
echo "Bereite Base Image vor..."
cd $BUILD_TMP_DIR
$TOOLS_TMP_DIR/$APPIMAGE_BASE --appimage-extract
mv squashfs-root AppDir

# Applikation installieren
mkdir AppDir/app

echo "Kopiere Programmdateien"
cd $SOURCE_DIR
cp *.py $BUILD_TMP_DIR/AppDir/app
cp resources/Logo.png $BUILD_TMP_DIR/AppDir/logo.png
cp -r gui $BUILD_TMP_DIR/AppDir/app

# Dependencies installieren
echo "Bereite Python-Dependencies vor..."
cd $BUILD_TMP_DIR
mkdir -p AppDir/packages

# uv installieren
echo "Installiere uv..."
$BUILD_TMP_DIR/AppDir/usr/bin/python -m pip install uv --target=$BUILD_TMP_DIR/AppDir/packages

# jetzt die dependencies
echo "Installiere Python-Dependencies..."
cd $SOURCE_DIR
$BUILD_TMP_DIR/AppDir/packages/bin/uv run --python $BUILD_TMP_DIR/AppDir/usr/bin/python pip install -r requirements.txt --target=$BUILD_TMP_DIR/AppDir/packages

# AppRun patchen
echo "Patche AppRun..."
cd $BUILD_TMP_DIR/AppDir
head --lines=-2 AppRun > AppRun1
echo "PYTHONPATH=\"\${APPDIR}/packages\" \${APPDIR}/packages/bin/uv run --python \${APPDIR}/usr/bin/python \${APPDIR}/app/main.py" >> AppRun1
mv AppRun1 AppRun
chmod +x AppRun

# Applikation für Desktop vorbereiten
echo "Vorbereiten Desktopintegration..."
cd $BUILD_TMP_DIR/AppDir
rm python.png
rm *.desktop

echo "[Desktop Entry]
Type=Application
Name=Taktische Zeichen Druckgenerator
Exec=AppRun
Comment=
Icon=logo
Categories=Graphics;
Terminal=false
" > AppRun.desktop
mv AppRun.desktop $BUILD_TMP_DIR/AppDir/usr/share/applications/AppRun.desktop

echo "AppImage vorbereitet unter $BUILD_TMP_DIR/AppDir"

# AppImage erzeugen
echo "Bereite AppImage vor..."
cd $SOURCE_DIR
$TOOLS_TMP_DIR/$APPIMAGE_TOOL -s deploy $BUILD_TMP_DIR/AppDir/usr/share/applications/AppRun.desktop
# taktische_zeichen_generator-$VERSION.AppImage