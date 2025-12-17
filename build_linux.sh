#!/bin/bash
# ============================================================================
# build_linux.sh - Linux Build Script
# ============================================================================
# Erstellt ein distributionsfähiges Binary für Linux
#
# Verwendung:
#   chmod +x build_linux.sh
#   ./build_linux.sh
#
# Voraussetzungen:
#   - Python 3.8+
#   - PyInstaller: pip install pyinstaller
#   - ImageMagick: sudo apt-get install imagemagick (oder dnf/pacman)
#   - zip: sudo apt-get install zip
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "BUILD-SKRIPT FÜR LINUX"
echo "============================================================================"
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Schritt 1: Version aus constants.py lesen
echo -e "${GREEN}[1/8]${NC} Lese Version aus constants.py..."
VERSION=$(python3 -c "
import re
with open('constants.py', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'PROGRAM_VERSION\s*=\s*[\"\']([\d.]+)[\"\']', content)
    if match:
        print(match.group(1))
    else:
        print('ERROR')
")

if [ "$VERSION" = "ERROR" ]; then
    echo -e "${RED}FEHLER: Version konnte nicht aus constants.py gelesen werden!${NC}"
    echo "Stelle sicher dass PROGRAM_VERSION definiert ist."
    exit 1
fi

echo "   Version: $VERSION"
echo ""

# Schritt 2: Prüfe ob ImageMagick installiert ist
echo -e "${GREEN}[2/8]${NC} Prüfe System-Abhängigkeiten..."
if ! command -v convert &> /dev/null; then
    echo -e "${YELLOW}WARNUNG: ImageMagick nicht gefunden!${NC}"
    echo "   Installiere mit: sudo apt-get install imagemagick"
    echo "   Das Binary wird ohne ImageMagick funktionieren, wenn es auf dem Zielsystem installiert ist."
fi

if ! command -v zip &> /dev/null; then
    echo -e "${RED}FEHLER: zip nicht gefunden!${NC}"
    echo "   Installiere mit: sudo apt-get install zip"
    exit 1
fi

echo "   Abhängigkeiten OK"
echo ""

# Schritt 3: Alte Builds löschen
echo -e "${GREEN}[3/8]${NC} Lösche alte Build-Artefakte..."
rm -rf build dist
echo "   build/ und dist/ gelöscht"
echo ""

# Schritt 4: Optimierte .pyc erstellen
echo -e "${GREEN}[4/8]${NC} Erstelle optimierte Bytecode-Dateien..."
python3 -OO -m compileall . 2>/dev/null || true
echo "   .pyc Dateien erstellt"
echo ""

# Schritt 5: PyInstaller Build
echo -e "${GREEN}[5/8]${NC} Starte PyInstaller Build..."
echo "   (Dies kann einige Minuten dauern...)"
pyinstaller --clean TaktischeZeichenDruckgenerator.spec

if [ $? -ne 0 ]; then
    echo -e "${RED}FEHLER: PyInstaller Build fehlgeschlagen!${NC}"
    exit 1
fi

echo "   Build erfolgreich"
echo ""

# Schritt 6: Release Notes kopieren
echo -e "${GREEN}[6/8]${NC} Kopiere Release Notes..."
RELEASE_NOTES_MD="release_notes/RELEASE_NOTES_v${VERSION}.md"
RELEASE_NOTES_PDF="release_notes/RELEASE_NOTES_v${VERSION}.pdf"

if [ -f "$RELEASE_NOTES_MD" ]; then
    cp "$RELEASE_NOTES_MD" "dist/TaktischeZeichenDruckgenerator/"
    echo "   $RELEASE_NOTES_MD kopiert"
else
    echo -e "${YELLOW}   WARNUNG: $RELEASE_NOTES_MD nicht gefunden${NC}"
fi

if [ -f "$RELEASE_NOTES_PDF" ]; then
    cp "$RELEASE_NOTES_PDF" "dist/TaktischeZeichenDruckgenerator/"
    echo "   $RELEASE_NOTES_PDF kopiert"
else
    echo "   $RELEASE_NOTES_PDF nicht vorhanden (optional)"
fi

echo ""

# Schritt 6b: Resources von _internal nach root verschieben (falls vorhanden)
echo -e "${GREEN}[6b/8]${NC} Verschiebe Resources von _internal nach root..."
if [ -d "dist/TaktischeZeichenDruckgenerator/_internal/resources" ]; then
    mv "dist/TaktischeZeichenDruckgenerator/_internal/resources" "dist/TaktischeZeichenDruckgenerator/resources"
    echo "   Resources verschoben: _internal/resources => resources/"
else
    echo -e "${YELLOW}   WARNUNG: Resources nicht in _internal gefunden${NC}"
fi

echo ""

# Schritt 7: Release-Ordner erstellen
echo -e "${GREEN}[7/8]${NC} Erstelle versionierten Release-Ordner..."
RELEASE_NAME="TaktischeZeichenDruckgenerator_v${VERSION}_Linux"
RELEASE_DIR="releases/$RELEASE_NAME"

mkdir -p "$RELEASE_DIR"

# Kopiere Build-Output
cp -r dist/TaktischeZeichenDruckgenerator/* "$RELEASE_DIR/"

echo "   Release-Ordner erstellt: $RELEASE_DIR"
echo ""

# Schritt 8: ZIP-Archiv erstellen
echo -e "${GREEN}[8/8]${NC} Erstelle ZIP-Archiv..."
cd releases
zip -r "${RELEASE_NAME}.zip" "$RELEASE_NAME" -q

if [ $? -eq 0 ]; then
    echo "   ZIP erstellt: releases/${RELEASE_NAME}.zip"
else
    echo -e "${RED}   FEHLER beim Erstellen des ZIP-Archivs${NC}"
fi

cd ..
echo ""

# Zusammenfassung
echo "============================================================================"
echo -e "${GREEN}BUILD ERFOLGREICH ABGESCHLOSSEN!${NC}"
echo "============================================================================"
echo ""
echo "Release-Informationen:"
echo "   Version: $VERSION"
echo "   Plattform: Linux"
echo "   Binary: $RELEASE_DIR/TaktischeZeichenDruckgenerator"
echo "   Archiv: releases/${RELEASE_NAME}.zip"
echo ""
echo "Größe:"
du -sh "$RELEASE_DIR"
du -sh "releases/${RELEASE_NAME}.zip"
echo ""
echo "Nächste Schritte:"
echo "   1. Binary testen: cd $RELEASE_DIR && ./TaktischeZeichenDruckgenerator"
echo "   2. ZIP verteilen: releases/${RELEASE_NAME}.zip"
echo ""
echo "HINWEIS FÜR LINUX:"
echo "   - ImageMagick muss auf dem Zielsystem installiert sein:"
echo "     sudo apt-get install imagemagick    (Debian/Ubuntu)"
echo "     sudo dnf install ImageMagick        (Fedora)"
echo "     sudo pacman -S imagemagick          (Arch)"
echo "   - Schriftarten sollten installiert sein (z.B. RobotoSlab)"
echo ""
echo "============================================================================"
