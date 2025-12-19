#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
constants.py - Konstanten fuer das Programm "Taktische Zeichen Druckgenerator"
Alle Default-Werte, Festlegungen, wie z.B. Dateinamen, Modusnamen, usw. sind hier zu erstellen.

"""

from pathlib import Path
from typing import Optional
import sys
import os

# ================================================================================================
# IMAGEMAGICK PORTABLE SETUP
# ================================================================================================

def setup_imagemagick_portable():
    """
    Setzt MAGICK_HOME fuer portable ImageMagick-Installation

    HINWEIS: Logging erfolgt spaeter in main.py, da LoggingManager
    noch nicht initialisiert ist beim Import von constants.py

    Returns:
        tuple: (success: bool, imagemagick_dir: Path, message: str)
    """
    # Basis-Verzeichnis ermitteln
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent.resolve()

    imagemagick_dir = base_dir / "imagemagick"

    if imagemagick_dir.exists():
        # MAGICK_HOME setzen
        os.environ['MAGICK_HOME'] = str(imagemagick_dir)

        # MAGICK_CODER_MODULE_PATH setzen (wichtig fuer .exe-Build)
        modules_coders_dir = imagemagick_dir / "modules" / "coders"
        if modules_coders_dir.exists():
            os.environ['MAGICK_CODER_MODULE_PATH'] = str(modules_coders_dir)

        # MAGICK_FILTER_MODULE_PATH setzen (fuer Filter-Module)
        modules_filters_dir = imagemagick_dir / "modules" / "filters"
        if modules_filters_dir.exists():
            os.environ['MAGICK_FILTER_MODULE_PATH'] = str(modules_filters_dir)

        # MAGICK_CONFIGURE_PATH setzen (wichtig fuer config XMLs)
        os.environ['MAGICK_CONFIGURE_PATH'] = str(imagemagick_dir)

        # CRITICAL: Zusaetzliche Umgebungsvariable um Registry-Lookup zu verhindern
        # Diese Variable zwingt ImageMagick, die ENV-Variablen zu verwenden
        # statt die Windows-Registry zu durchsuchen
        os.environ['MAGICK_MODULE_PATH'] = str(imagemagick_dir / "modules")

        # DLL-Pfad zum PATH hinzufuegen
        current_path = os.environ.get('PATH', '')
        if str(imagemagick_dir) not in current_path:
            os.environ['PATH'] = str(imagemagick_dir) + os.pathsep + current_path

        # CHANGED: Rueckgabe statt direktem Logging
        return (True, imagemagick_dir, "ImageMagick portable gefunden")
    else:
        # CHANGED: Rueckgabe statt direktem Logging
        return (False, imagemagick_dir, "ImageMagick nicht gefunden")

# ImageMagick Setup beim Import ausfuehren und Ergebnis speichern
# Das Setup MUSS beim Import erfolgen, damit ENV-Variablen gesetzt sind
# Das Ergebnis wird fuer spaeteres Logging in main.py gespeichert
if sys.platform == 'win32':
    IMAGEMAGICK_SETUP_RESULT = setup_imagemagick_portable()
else:
    IMAGEMAGICK_SETUP_RESULT = (True, "", "ImageMagick")

# ================================================================================================
# PROGRAMM-INFORMATIONEN
# ================================================================================================
# KONSTANTEN-KATEGORISIERUNG
# ================================================================================================
#
# WICHTIG: Es gibt 2 Arten von Konstanten:
#
# 1. SYSTEM_* = Unveränderliche technische Konstanten
#    - Niemals zur Laufzeit ändern
#    - Niemals vom User konfigurierbar
#    - Beispiele: SYSTEM_POINTS_PER_INCH, SYSTEM_LOG_FORMAT
#
# 2. DEFAULT_* = Factory Defaults (überschreibbar durch User)
#    - Können zur Laufzeit geändert werden (via RuntimeConfig)
#    - User kann eigene Werte in settings.json speichern
#    - Beispiele: DEFAULT_MODUS, DEFAULT_FONT_SIZE, DEFAULT_DPI
#
# Verwendung:
#   - Für DEFAULT_*: Nutze RuntimeConfig.get_instance().attribut
#   - Für SYSTEM_*: Direkt aus constants.py importieren
#
# ================================================================================================

PROGRAM_NAME = "Taktische Zeichen Druckgenerator"
PROGRAM_VERSION = "0.8.5"
PROGRAM_AUTHOR = "Ramon Hoffmann"
PROGRAM_AUTHOR_EMAIL = "Ramon-Hoffmann@gmx.de"
PROGRAM_DESCRIPTION = "Taktische Zeichen Druckgenerator -  Tool zur Druckvorbereitung von taktischen Zeichen"

# ================================================================================================
# PFADE
# ================================================================================================

def get_base_path() -> Path:
    """Ermittelt Basis-Pfad (funktioniert auch als .exe)"""
    if sys.platform == 'win32':
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent.resolve()
    else:
        return Path.home()

BASE_DIR = get_base_path()
DEFAULT_ZEICHEN_DIR = BASE_DIR / "Taktische_Zeichen_Grafikvorlagen"
EXPORT_DIR = BASE_DIR / "Taktische_Zeichen_Ausgabe"
LOGS_DIR = BASE_DIR / "Logs"
RESOURCES_DIR = BASE_DIR / "resources"
LOGO_PATH = RESOURCES_DIR / "Logo.png"
ICON_PATH = RESOURCES_DIR / "icon.ico"

# ================================================================================================
# DRUCK-PARAMETER (Legacy - für Rückwärtskompatibilität)
# ================================================================================================
# DEPRECATED: Diese Konstanten sind nur für Rückwärtskompatibilität
# Nutze stattdessen DEFAULT_* Konstanten und RuntimeConfig!

# DPI-Einstellungen
# Maximale DPI für Rendering (höchste Qualität)
DEFAULT_DPI = 600

# Standard-DPI für neuen Export (vorausgewählt im Export-Dialog)
DEFAULT_EXPORT_DPI = 300

# Mindest-DPI für Druckqualität (Druckerei-Anforderung)
DEFAULT_MINIMUM_DPI_FOR_PRINT = 300

# DPI-Stufen für automatische Optimierung (v7.1+)
DPI_STUFEN = [100, 150, 200, 300, 450, 600]

# ================================================================================================
# FARBEN (RGB)
# ================================================================================================

ORGANIZATIONAL_BLUE = (0, 70, 127)  # Organizational blue color
COLOR_SCHWARZ = (0, 0, 0)
COLOR_WEISS = (255, 255, 255)

TEXT_COLOR = COLOR_SCHWARZ
BG_COLOR = COLOR_WEISS

# Farbeinstellungen
DEFAULT_BACKGROUND = (255, 255, 255)  # Weiß

# ================================================================================================
# TEXT-LAYOUT & PLATZHALTER
# ================================================================================================

DEFAULT_FONT_FAMILY = "Arial"
DEFAULT_FONT_SIZE = 10  # In Punkten

# ================================================================================================
# TEXT-ABSTÄNDE (in mm)
# ================================================================================================
# REMOVED: TEXT_GRAFIK_OFFSET_MM und TEXT_BOTTOM_OFFSET_MM (deprecated)
# → Nutze stattdessen: DEFAULT_ABSTAND_GRAFIK_TEXT_MM und DEFAULT_TEXT_BOTTOM_OFFSET_MM

# ================================================================================================
# TEXT-FORMATIERUNG
# ================================================================================================

LINE_HEIGHT_FACTOR = 2.0  # Zeilenabstand-Faktor (200% der Schriftgröße)
TEXT_BUFFER_FACTOR = 1.5  # Buffer-Faktor fuer Text-Hoehe (wird nicht mehr verwendet)

# SYSTEM: Konstanten fuer Font-Berechnungen (unveränderlich)
SYSTEM_POINTS_PER_INCH = 72  # Standard: 1 Point = 1/72 Inch
POINTS_PER_INCH = SYSTEM_POINTS_PER_INCH  # Alias für Rückwärtskompatibilität

# Grafik-Positionierung
# "top" = oben, "center" = mittig, "bottom" = unten
GRAFIK_POSITION_VERTICAL = "top"

# Text-Ausrichtung
# "left" = links, "center" = zentriert, "right" = rechts
TEXT_ALIGNMENT = "left"  # Linksbuendig

# Offset fuer linksbuendigen Text (in mm vom Sicherheitsrand)
TEXT_LEFT_OFFSET_MM = 0.0  # Direkt an der gruenen Linie

# PLATZHALTER-KONFIGURATION
PLACEHOLDER_OV_LENGTH = 16
PLACEHOLDER_RUF_LENGTH = 16
PLACEHOLDER_STAERKE_DIGITS = [5, 6, 6, 3]  # Format:      /      /      / ___
PLACEHOLDER_CHAR = "_"

# ================================================================================================
# MODI
# ================================================================================================

MODUS_OV_STAERKE = "ov_staerke"
MODUS_RUF = "ruf"
MODUS_OHNE_TEXT = "ohne_text"
MODUS_FREITEXT = "freitext"
MODUS_ORT_STAERKE = "ort_staerke"
MODUS_SCHREIBLINIE_STAERKE = "schreiblinie_staerke"
MODUS_DATEINAME = "dateiname"  # Dateiname als Text (Unterstriche → Leerzeichen)

AVAILABLE_MODI = [
    MODUS_OV_STAERKE,
    MODUS_ORT_STAERKE,
    MODUS_SCHREIBLINIE_STAERKE,
    MODUS_RUF,
    MODUS_OHNE_TEXT,
    MODUS_FREITEXT,
    MODUS_DATEINAME  # NEU
]

# Grafik-Positionierung für MODUS_OHNE_TEXT
# Mögliche Werte: "top" (oben), "center" (mittig), "bottom" (unten)
GRAFIK_POSITION_TOP = "top"
GRAFIK_POSITION_CENTER = "center"
GRAFIK_POSITION_BOTTOM = "bottom"

AVAILABLE_GRAFIK_POSITIONS = [
    GRAFIK_POSITION_TOP,
    GRAFIK_POSITION_CENTER,
    GRAFIK_POSITION_BOTTOM
]

# ================================================================================================
# FACTORY DEFAULTS - Überschreibbar durch RuntimeConfig
# ================================================================================================
# Diese Werte sind Factory Defaults und können vom User zur Laufzeit geändert werden.
# Änderungen werden in settings.json gespeichert und von RuntimeConfig verwaltet.
#
# WICHTIG: Verwende RuntimeConfig statt direkt diese Konstanten zu nutzen!
#
# Beispiel:
#   from runtime_config import get_config
#   config = get_config()
#   modus = config.standard_modus  # Nutzt User-Override oder DEFAULT_MODUS
#
# ================================================================================================

# Standard-Modus für neue Zeichen
DEFAULT_MODUS = MODUS_FREITEXT

# Zeichen-Abmessungen (in mm)
DEFAULT_ZEICHEN_HOEHE_MM = 45.0
DEFAULT_ZEICHEN_BREITE_MM = 45.0

# Druck-Parameter
DEFAULT_BESCHNITTZUGABE_MM = 3.0  # Zusätzlicher Rand für Druck (wird abgeschnitten)
DEFAULT_SICHERHEITSABSTAND_MM = 3.0  # Abstand Grafik/Text zum Rand des fertigen Zeichens
DEFAULT_ABSTAND_GRAFIK_TEXT_MM = 2.0  # Abstand zwischen Grafik (unten) und Text (oben)
DEFAULT_TEXT_BOTTOM_OFFSET_MM = 0.0  # Abstand zwischen Text (unten) und Sicherheitsrand

# REMOVED: DEFAULT_ABSTAND_RAND_MM (war deprecated, wurde nirgends verwendet)

# Font-Einstellungen
# DEFAULT_FONT_SIZE bereits oben definiert
# DEFAULT_FONT_FAMILY bereits oben definiert

# Text-Messungs-Parameter
TEMP_IMAGE_SIZE_PX = 1000  # Größe des temporären Images für Textmessungen (war 100px - zu klein!)

# Platzhalter-Längen
DEFAULT_OV_LENGTH = 16
DEFAULT_RUF_LENGTH = 16
DEFAULT_ORT_LENGTH = 16
DEFAULT_FREITEXT_LENGTH = 32

# Stärke-Format
DEFAULT_STAERKE_DIGITS = [5, 6, 6, 3]

# Schnittlinien
DEFAULT_SCHNITTLINIEN = False

# Automatische Anpassungen
DEFAULT_AUTO_ADJUST_GRAFIK_SIZE = True  # Grafikgroesse automatisch anpassen bei Zeichengroesse-Aenderung
DEFAULT_AUTO_ADJUST_FONT_SIZE = True  # Schriftgroesse automatisch anpassen bei Zeichengroesse-Aenderung

# Seitenverhaeltnis (fuer S2-Layout)
DEFAULT_ASPECT_LOCKED = True  # Seitenverhaeltnis 1:1 fixieren (Breite = Hoehe)

# Grafik-Position (fuer Modus "Nur Grafik")
DEFAULT_GRAFIK_POSITION = "mittig"  # oben, mittig, unten

# Standard-Layout und Export-Format
DEFAULT_STANDARD_LAYOUT = "S2"  # S1 oder S2
DEFAULT_STANDARD_EXPORT_FORMAT = "PNG"  # PNG, PDF_SINGLE, PDF_SHEET

# PDF-Schnittbogen Seitenraender (in mm)
DEFAULT_PDF_MARGIN_HORIZONTAL_MM = 10.0  # Links/Rechts-Rand
DEFAULT_PDF_MARGIN_VERTICAL_MM = 10.0  # Oben/Unten-Rand

# ================================================================================================
# S1-LAYOUT (DOPPELSCHILD) - Factory Defaults
# ================================================================================================
# S1-Layout Einstellungen (Rechteckiges Layout mit zwei Bereichen)
#
# Das S1-Layout ist ein rechteckiges Zeichen (Breite = 2 × Höhe) mit zwei Bereichen:
# - Links: Grafik + Freitext (wie S2-Layout)
# - Rechts: Schreiblinien + optionaler Stärke-Platzhalter
#
# Diese Werte können vom User zur Laufzeit geändert werden (via RuntimeConfig).
# ================================================================================================

# Seitenverhältnis fixieren (True = Breite = 2 × Höhe)
DEFAULT_S1_ASPECT_LOCKED = True

# Aufteilung Links/Rechts in Prozent (Standard: 40/60)
DEFAULT_S1_LINKS_PROZENT = 40

# Anzahl der Schreiblinien im rechten Bereich (Zeilenhöhe wird daraus berechnet)
DEFAULT_S1_ANZAHL_SCHREIBLINIEN = 5

# Stärke-Platzhalter in erster Zeile anzeigen
DEFAULT_S1_STAERKE_ANZEIGEN = True

# S1-Zeichenabmessungen (können vom S2-Layout abweichen)
DEFAULT_S1_ZEICHEN_HOEHE_MM = 45.0  # Höhe des fertigen S1-Zeichens
DEFAULT_S1_ZEICHEN_BREITE_MM = 90.0  # Breite (2:1 Seitenverhältnis)
DEFAULT_S1_BESCHNITTZUGABE_MM = 3.0  # Beschnittzugabe für S1
DEFAULT_S1_SICHERHEITSABSTAND_MM = 3.0  # Sicherheitsabstand für S1

# ================================================================================================
# S1-LAYOUT RENDERING - Visuelle Konstanten
# ================================================================================================

# Farbe der Schreiblinien im rechten Bereich (dunkelgrau)
S1_LINE_COLOR = (80, 80, 80)  # Dunkelgrau (RGB)

# Linienstärke für Schreiblinien in Pixeln
S1_LINE_WIDTH = 1  # 1px Linienbreite

# Horizontaler Abstand der Schreiblinien vom Rand (in mm)
S1_LINE_MARGIN_MM = 2.0  # 2mm Abstand links/rechts

# ------------------------------------------------------------------------------------------------
# STAERKEANGABE (gezeichnet, nicht als Text)
# ------------------------------------------------------------------------------------------------

# Winkel der Schrägstriche (wie Arial "/")
S1_STAERKE_SLASH_ANGLE_DEG = 75.0  # Grad zur Horizontalen

# Höhenfaktor für Stärkeangabe (relativ zur Zeilenhöhe)
S1_STAERKE_HEIGHT_FACTOR = 0.9  # 90% der Zeilenhöhe

# Anteil der Feldbreite für Unterstrich
S1_STAERKE_UNDERSCORE_WIDTH_FACTOR = 0.25  # 25% der verfügbaren Breite

# Anteil der Feldbreite für linken Rand (Platz für handschriftliche Zahlen)
S1_STAERKE_LEFT_MARGIN_FACTOR = 0.12  # 10% Rand links (genug Platz zum Schreiben)

# Anteil der Feldbreite für Gap zwischen letztem Slash und Unterstrich
S1_STAERKE_GAP_FACTOR = 0.01  # 5% fixer Abstand (optische Trennung)

# Anzahl Schrägstriche in Stärkeangabe
S1_STAERKE_SLASH_COUNT = 3  # 3 Schrägstriche

# ================================================================================================
# BLANKO-ZEICHEN
# ================================================================================================

# Kategorie-Name für Blanko-Zeichen (virtuelle Kategorie, immer an erster Stelle)
BLANKO_KATEGORIE_NAME = "Blanko-Zeichen"

# Virtueller SVG-Pfad für Blanko-Zeichen (wird erkannt und nicht gerendert)
BLANKO_SVG_PATH = "BLANKO"

# Namen für Standard-Blanko-Zeichen (pro Modus)
# Diese werden für S2-Layout und normale Modi verwendet
BLANKO_ZEICHEN_NAMEN = {
    MODUS_OV_STAERKE: "Leer - OV + Staerke",
    MODUS_ORT_STAERKE: "Leer - Ort + Staerke",
    MODUS_SCHREIBLINIE_STAERKE: "Leer - Schreiblinie + Staerke",
    MODUS_FREITEXT: "Leer - Freitext",
    MODUS_RUF: "Leer - Rufname",
    MODUS_DATEINAME: "Leer - Dateiname",
    MODUS_OHNE_TEXT: "Leer - Ohne Text"
}

# NEW v0.8.2.3: S1-Blanko-Zeichen auf 3 fixe Varianten
# Pfad-Konstanten für die 3 S1-Blanko-Varianten
BLANKO_S1_LEER = "BLANKO_S1_LEER"  # Komplett ohne Text und Stärkeangabe
BLANKO_S1_LINIEN = "BLANKO_S1_LINIEN"  # Beidseitig Schreiblinien, ohne Stärke
BLANKO_S1_LINIEN_STAERKE = "BLANKO_S1_LINIEN_STAERKE"  # Beidseitig Schreiblinien, mit Stärke

# Namen für die 3 S1-Blanko-Varianten
BLANKO_S1_ZEICHEN_NAMEN = {
    BLANKO_S1_LEER: "S1 Leer",
    BLANKO_S1_LINIEN: "S1 mit Linien",
    BLANKO_S1_LINIEN_STAERKE: "S1 mit Linien + Staerke"
}

# ================================================================================================
# SVG-OPTIONEN
# ===============================================================================================

# NEW: Image-Resampling Filter
RESAMPLING_FILTER = 'mitchell'  
# Alternativen: 'lanczos', 'cubic', 'box', 'gaussian', 'nearest', 'catrom'

# OPTIMIZED: Smart Render Scale basierend auf Zeichengröße
# Große Zeichen (>1000px) direkt in Zielauflösung rendern (kein Upscaling nötig)
# Kleine Zeichen mit 1.5x Upscaling für präzises Trimming
# Performance-Optimierung: 2 -> 1.5/1 (~50-60% schneller), 1.5 -> 1.2 (20% schneller, kaum Qualitätsverlust)
# OPTIMIERUNG: Noch aggressivere Skalierung
RESAMPLING_RENDER_SCALE_BIG_SVG = 1
RESAMPLING_RENDER_SCALE_MED_SVG = 1
RESAMPLING_RENDER_SCALE_SMALL_SVG = 1
RESAMPLING_MAX_PX_SIZE_BIG = 1500
RESAMPLING_MAX_PX_SIZE_MED = 1000

# Schwellwerte für Zeichengröße (mm) zur Chunk-Size-Berechnung
ZEICHEN_SIZE_THRESHOLD_VERY_LARGE_MM = 150.0  # Sehr große Zeichen (> 150mm)
ZEICHEN_SIZE_THRESHOLD_LARGE_MM = 100.0       # Große Zeichen (> 100mm)

# A4 Page Dimensions (DIN A4 standard)
DIN_A4_WIDTH_MM = 210.0   # Portrait width / Landscape height
DIN_A4_HEIGHT_MM = 297.0  # Portrait height / Landscape width

# NEW: PNG-Transparenz-Optionen
# Farbmodus fuer PNG-Export
PNG_COLOR_MODE_RGBA = 'RGBA'  # Mit Alpha-Kanal (Transparenz)
PNG_COLOR_MODE_RGB = 'RGB'    # Ohne Alpha-Kanal (weisser Hintergrund)

# Aktiver Farbmodus (RGBA = Transparenz fuer Druck auf farbigem Untergrund)
PNG_COLOR_MODE = PNG_COLOR_MODE_RGB

# Hintergrundfarbe fuer Canvas
# RGBA: (R, G, B, A) - A=0 bedeutet vollstaendig transparent
# RGB:  (R, G, B)    - Weisser Hintergrund
PNG_BACKGROUND_COLOR_TRANSPARENT = (255, 255, 255, 0)  # Weiss, transparent
PNG_BACKGROUND_COLOR_WHITE = (255, 255, 255)           # Weiss, opak

# ================================================================================================
# EXPORT-OPTIONEN
# ================================================================================================

EXPORT_FORMAT_PNG = "PNG"
EXPORT_FORMAT_PDF = "PDF"

AVAILABLE_EXPORT_FORMATS = [
    EXPORT_FORMAT_PNG,
    EXPORT_FORMAT_PDF
]

# PNG compress_level Parameter:
#  - compress_level=9: Maximale Kompression (langsam, kleinste Dateien)
#  - compress_level=6: Standard (Balance zwischen Geschwindigkeit und Größe)
#  - compress_level=1: Minimale Kompression (schnell, etwas größere Dateien)
#  - compress_level=0: KEINE Kompression (sehr schnell, RIESIGE Dateien) """

EXPORT_PNG_COMPRESS_LEVEL = 6

# NEW: Block-Größen für Ressourcen-Optimierung (v0.6.0)
DEFAULT_PNG_CHUNK_MULTIPLIER = 4  # Stapelgröße = num_threads * multiplier
DEFAULT_PDF_CHUNK_SIZE = 100  # Anzahl Seiten pro PDF-Datei
DEFAULT_PDF_CHUNK_SIZE_SCHNITTBOGEN = 20  # Anzahl Seiten pro PDF-Datei
MIN_PDF_LAST_CHUNK_SIZE = 5  # Minimale Seitenzahl für letzte PDF-Datei


# ================================================================================================
# EXPORT-DATEINAMEN (Namenskonventionen)
# ================================================================================================

# Zeitstempel-Format für Export-Dateien
EXPORT_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M"

# Templates für Export-Ordnernamen
# Format: YYYY-MM-DD_hh-mm_<Dateiformat>_<Exportformat>_<Anzahl Zeichen>_Zeichen_<dpi>_dpi
EXPORT_FOLDER_TEMPLATE = "{timestamp}_{file_format}_{export_format}_{count}_Zeichen_{dpi}_dpi"

# Templates für PDF-Dateinamen (innerhalb des Ordners)
# Format: YYYY-MM-DD_hh-mm_<Exportformat>_Zeichen_<start>_bis_<end>_Datei_<idx>_von_<total>.pdf
EXPORT_PDF_FILENAME_TEMPLATE = "{timestamp}_{export_format}_Zeichen_{start}_bis_{end}_Datei_{idx}_von_{total}.pdf"

def create_export_folder_name(
    count: int,
    dpi: int,
    file_format: str = "PNG",
    export_format: str = "Einzelzeichen"
) -> str:
    """
    Erstellt Export-Ordnernamen nach neuer Konvention (v0.6.0)

    Args:
        count: Anzahl der taktischen Zeichen
        dpi: Auflösung in DPI
        file_format: Dateiformat ("PNG" oder "PDF")
        export_format: Exportformat ("Einzelzeichen" oder "Schnittbogen")

    Returns:
        str: Ordnername (ohne Pfad)

    Beispiele:
        PNG: "2025-10-31_09-40_PNG_Einzelzeichen_540_Zeichen_600_dpi"
        PDF Einzelzeichen: "2025-10-31_09-40_PDF_Einzelzeichen_540_Zeichen_600_dpi"
        PDF Schnittbogen: "2025-10-31_09-40_PDF_Schnittbogen_540_Zeichen_600_dpi"
    """
    from datetime import datetime

    timestamp = datetime.now().strftime(EXPORT_TIMESTAMP_FORMAT)

    return EXPORT_FOLDER_TEMPLATE.format(
        timestamp=timestamp,
        file_format=file_format,
        export_format=export_format,
        count=count,
        dpi=dpi
    )


def create_pdf_filename(
    timestamp: str,
    export_format: str,
    start_idx: int,
    end_idx: int,
    file_idx: int,
    total_files: int
) -> str:
    """
    Erstellt PDF-Dateinamen nach neuer Konvention (v0.6.0)

    Args:
        timestamp: Zeitstempel im Format YYYY-MM-DD_HH-MM
        export_format: Exportformat ("Einzelzeichen" oder "Schnittbogen")
        start_idx: Index des erstenZeichens in dieser PDF (1-basiert)
        end_idx: Index des letztenZeichens in dieser PDF (1-basiert)
        file_idx: Index dieser PDF-Datei (1-basiert)
        total_files: Gesamtzahl der PDF-Dateien

    Returns:
        str: PDF-Dateiname

    Beispiele:
        "2025-10-31_09-40_Einzelzeichen_Zeichen_1_bis_100_Datei_1_von_5.pdf"
        "2025-10-31_09-40_Schnittbogen_Zeichen_101_bis_200_Datei_2_von_5.pdf"
    """
    return EXPORT_PDF_FILENAME_TEMPLATE.format(
        timestamp=timestamp,
        export_format=export_format,
        start=start_idx,
        end=end_idx,
        idx=file_idx,
        total=total_files
    )

# ================================================================================================
# SCHNEIDELINIEN (fuer Test-Ausgaben)
# ================================================================================================

# Konstanten fuer Schneidelinien-Darstellung
CUT_LINE_WIDTH_PX = 3
CUT_LINE_LABEL_FONT_SIZE = 24
CUT_LINE_LABEL_OFFSET_PX = 40
CUT_LINE_LABEL_STROKE_WIDTH = 1
CUT_LINE_LABEL_STROKE_COLOR = COLOR_WEISS

# Farben fuer Schneidelinien
CUT_LINE_COLOR_BESCHNITT = (255, 0, 0)    # Rot
CUT_LINE_COLOR_SCHNITT = (0, 0, 255)      # Blau
CUT_LINE_COLOR_SICHERHEIT = (0, 255, 0)   # Gruen
CUT_LINE_COLOR_S1_BORDER = (255, 140, 0)  # Orange - S1 Trennlinie Links/Rechts

# ================================================================================================
# TEST/DEBUG-KONSTANTEN
# ================================================================================================

# Konstanten fuer Test-Images
TEST_IMAGE_MARGIN_PX = 50
TEST_CIRCLE_LINE_WIDTH = 5
MAX_PREVIEW_ITEMS = 3  # Max. Anzahl Items in Vorschau

# ================================================================================================
# VALIDIERUNG
# ================================================================================================

ALLOWED_SVG_EXTENSIONS = ['.svg']
MAX_CATEGORY_NAME_LENGTH = 50
# Textlaengen-Validierung deaktivieren
TEXT_LENGTH_VALIDATION_ENABLED = False

# ================================================================================================
# LOGGING
# ================================================================================================

DEFAULT_LOG_LEVEL = "DEBUG"
DEFAULT_LOG_FILES_COUNT = 10  # Max. Anzahl Log-Dateien behalten
LOG_MESSAGE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

# Running as EXE Detection
RUNNING_AS_EXE = getattr(sys, 'frozen', False)

# ================================================================================================
# GUI COLORS - VALIDIERUNG
# ================================================================================================

# NEW: Farb-Konstanten fuer visuelle Validierungs-Hervorhebungen
VALIDATION_ERROR_BG = "#FFE6E6"    # Helles Rot - Hintergrund fuer fehlerhafte Zeilen
VALIDATION_ERROR_FG = "#CC0000"    # Dunkelrot - Textfarbe fuer Fehler und Kategorien
VALIDATION_NORMAL_BG = "white"     # Weiss - Normaler Hintergrund

# ================================================================================================
# GUI PERFORMANCE - BATCH-UPDATE-INTERVALL
# ================================================================================================

# GUI-Update-Intervall beim Tree-Aufbau (alle X Items)
GUI_BATCH_UPDATE_INTERVAL = 100  # UI-Update alle 100 Items

# ================================================================================================
# GRAFIK-GROESSE (DYNAMISCH BERECHNET)
# ================================================================================================

# WICHTIG: Die Grafik-Groesse ist NICHT fest kodiert!
# Sie wird dynamisch berechnet basierend auf:
#   - ENDGROESSE_MM (45mm -> Sicherer Bereich: 39mm)
#   - SICHERHEITSRAND_MM (3mm)
#   - TEXT_OFFSET_MM (3mm) <- NEU in v2.6!
#   - Maximaler Text-Hoehe aller Modi
#
# NEU:
# Formel (v2.5):
#   Max_Grafik = 39mm - (TEXT_OFFSET + Max_Text_Hoehe)
#   
#   Beispiel bei 8pt Font:
#   - Text OV+Stärke: ~9.18mm (2 Zeilen)
#   - TEXT_OFFSET: 3.0mm
#   - Gesamt Text-Bereich: 9.18mm + 3.0mm = 12.18mm
#   - Max_Grafik: 39mm - 12.18mm = 26.82mm
#
# WICHTIG: calculate_text_height_mm() gibt bereits Text + Offset zurück!
#
#
# AENDERBAR durch:
#   - ENDGROESSE_MM aendern (z.B. 50mm -> Grafik wird groesser)
#   - SICHERHEITSRAND_MM aendern (z.B. 5mm -> Grafik wird kleiner)
#   - TEXT_OFFSET_MM aendern (z.B. 5mm -> Grafik wird kleiner)
#   - DEFAULT_FONT_SIZE aendern (z.B. 10pt -> Text groesser -> Grafik kleiner)
#   - LINE_HEIGHT_FACTOR aendern (z.B. 2.5 -> Text hoeher -> Grafik kleiner)
#
# Die Berechnung erfolgt zur Laufzeit in calculate_max_grafik_size_mm()

# ================================================================================================
# HILFSFUNKTIONEN
# ================================================================================================

def mm_to_pixels(mm: float, dpi: int = DEFAULT_DPI) -> int:
    """
    Konvertiert Millimeter in Pixel
    
    Args:
        mm: Wert in Millimeter
        dpi: Aufloesung in DPI
        
    Returns:
        Wert in Pixel (gerundet)
    """
    inches = mm / 25.4
    pixels = inches * dpi
    return int(round(pixels))


def pixels_to_mm(pixels: int, dpi: int = DEFAULT_DPI) -> float:
    """
    Konvertiert Pixel in Millimeter
    
    Args:
        pixels: Wert in Pixel
        dpi: Aufloesung in DPI
        
    Returns:
        Wert in Millimeter
    """
    inches = pixels / dpi
    mm = inches * 25.4
    return mm


def create_placeholder_text(length: int, char: str = PLACEHOLDER_CHAR) -> str:
    """
    Erstellt Platzhalter-Text
    
    Args:
        length: Anzahl Zeichen
        char: Platzhalter-Zeichen
        
    Returns:
        Platzhalter-String (z.B. "_______________")
    """
    return char * length


def create_staerke_placeholder(digits: Optional[list[int]] = None) -> str:
    """
    Erstellt Staerke-Platzhalter

    Format:      /      /      / ___

    Args:
        digits: Liste mit Anzahl Stellen pro Feld (z.B. [5, 6, 6, 3])

    Returns:
        Staerke-Platzhalter (z.B. "     /      /      / ___")
    """
    if digits is None:
        digits = PLACEHOLDER_STAERKE_DIGITS

    # CHANGED: Erste 3 Felder mit Leerzeichen, letztes Feld mit Unterstrichen
    # CHANGED: Trennzeichen von " / ... = " zu " / ... / "
    fields = [
        " " * digits[0],  # Leerzeichen fuer Fuehrer
        " " * digits[1],  # Leerzeichen fuer Unterfuehrer
        " " * digits[2],  # Leerzeichen fuer Helfer
        PLACEHOLDER_CHAR * digits[3]  # Unterstriche fuer Gesamt
    ]
    return "{} / {} / {} / {}".format(fields[0], fields[1], fields[2], fields[3])


def calculate_print_dimensions(
    dpi: int = DEFAULT_DPI,
    zeichen_hoehe_mm: float = DEFAULT_ZEICHEN_HOEHE_MM,
    zeichen_breite_mm: float = DEFAULT_ZEICHEN_BREITE_MM,
    sicherheitsabstand_mm: Optional[float] = None,  # NEW (v7.3): Aus RuntimeConfig wenn None
    beschnittzugabe_mm: Optional[float] = None,     # NEW (v7.3): Aus RuntimeConfig wenn None
    text_grafik_offset_mm: Optional[float] = None,  # NEW (v7.3): Aus RuntimeConfig wenn None
    text_bottom_offset_mm: Optional[float] = None   # NEW (v7.3): Aus RuntimeConfig wenn None
) -> dict:
    """
    Berechnet alle relevanten Dimensionen fuer Druck (rechteckige Zeichen)

    Args:
        dpi: Aufloesung
        zeichen_hoehe_mm: Höhe des fertigen Zeichens in mm (NACH Zuschnitt)
        zeichen_breite_mm: Breite des fertigen Zeichens in mm (NACH Zuschnitt)
        sicherheitsabstand_mm: Sicherheitsabstand in mm (None = aus RuntimeConfig, v7.3)
        beschnittzugabe_mm: Beschnittzugabe in mm (None = aus RuntimeConfig, v7.3)
        text_grafik_offset_mm: Abstand Grafik-Text (None = aus RuntimeConfig, v7.3)
        text_bottom_offset_mm: Text Bottom Offset (None = aus RuntimeConfig, v7.3)

    Returns:
        Dict mit allen Massen (mm und px) - jeweils für Höhe UND Breite

    Beispiel:
        zeichen_hoehe_mm=28, zeichen_breite_mm=32, sicherheitsabstand_mm=0, beschnittzugabe_mm=3
        → Canvas: 28×32mm
        → Endgröße: 28×32mm
        → Datei: 34×38mm (mit 3mm Beschnitt)
    """
    # NEW (v7.3): Lade Werte aus RuntimeConfig falls nicht übergeben
    if (sicherheitsabstand_mm is None or beschnittzugabe_mm is None or
        text_grafik_offset_mm is None or text_bottom_offset_mm is None):
        try:
            from runtime_config import get_config
            config = get_config()
            if sicherheitsabstand_mm is None:
                sicherheitsabstand_mm = config.sicherheitsabstand_mm
            if beschnittzugabe_mm is None:
                beschnittzugabe_mm = config.beschnittzugabe_mm
            if text_grafik_offset_mm is None:
                text_grafik_offset_mm = config.abstand_grafik_text_mm
            if text_bottom_offset_mm is None:
                text_bottom_offset_mm = config.text_bottom_offset_mm
        except Exception:
            # Fallback auf Constants wenn RuntimeConfig nicht verfügbar
            if sicherheitsabstand_mm is None:
                sicherheitsabstand_mm = DEFAULT_SICHERHEITSABSTAND_MM
            if beschnittzugabe_mm is None:
                beschnittzugabe_mm = DEFAULT_BESCHNITTZUGABE_MM
            if text_grafik_offset_mm is None:
                text_grafik_offset_mm = DEFAULT_ABSTAND_GRAFIK_TEXT_MM
            if text_bottom_offset_mm is None:
                text_bottom_offset_mm = DEFAULT_TEXT_BOTTOM_OFFSET_MM

    # Typ-Absicherung: Nach try-except sollten alle Werte gesetzt sein
    assert sicherheitsabstand_mm is not None
    assert beschnittzugabe_mm is not None
    assert text_grafik_offset_mm is not None
    assert text_bottom_offset_mm is not None

    # CHANGED: Rechteckige Berechnung mit separaten Dimensionen für Höhe/Breite
    # Canvas = Endgröße - Sicherheitsabstand
    canvas_hoehe_mm = zeichen_hoehe_mm - (2 * sicherheitsabstand_mm)
    canvas_breite_mm = zeichen_breite_mm - (2 * sicherheitsabstand_mm)

    # Endgröße = Zeichengröße aus GUI
    endgroesse_hoehe_mm = zeichen_hoehe_mm
    endgroesse_breite_mm = zeichen_breite_mm

    # Datei = Endgröße + Beschnitt
    datei_hoehe_mm = zeichen_hoehe_mm + (2 * beschnittzugabe_mm)
    datei_breite_mm = zeichen_breite_mm + (2 * beschnittzugabe_mm)

    return {
        # Masse in mm - HÖHE
        "canvas_hoehe_mm": canvas_hoehe_mm,
        "endgroesse_hoehe_mm": endgroesse_hoehe_mm,
        "datei_hoehe_mm": datei_hoehe_mm,

        # Masse in mm - BREITE
        "canvas_breite_mm": canvas_breite_mm,
        "endgroesse_breite_mm": endgroesse_breite_mm,
        "datei_breite_mm": datei_breite_mm,

        # Masse in mm - Allgemein
        "BESCHNITTZUGABE_MM": beschnittzugabe_mm,
        "SICHERHEITSABSTAND_MM": sicherheitsabstand_mm,
        "text_grafik_offset_mm": DEFAULT_ABSTAND_GRAFIK_TEXT_MM,
        "text_bottom_offset_mm": DEFAULT_TEXT_BOTTOM_OFFSET_MM,

        # DEPRECATED (für Rückwärtskompatibilität - nutze canvas_* statt max_grafik_*)
        "max_grafik_mm": canvas_hoehe_mm,  # Deprecated: Nutze canvas_hoehe_mm
        "endgroesse_mm": endgroesse_hoehe_mm,  # Deprecated: Nutze endgroesse_hoehe_mm
        "datei_groesse_mm": datei_hoehe_mm,  # Deprecated: Nutze datei_hoehe_mm

        # Masse in Pixel - HÖHE
        "canvas_hoehe_px": mm_to_pixels(canvas_hoehe_mm, dpi),
        "endgroesse_hoehe_px": mm_to_pixels(endgroesse_hoehe_mm, dpi),
        "datei_hoehe_px": mm_to_pixels(datei_hoehe_mm, dpi),

        # Masse in Pixel - BREITE
        "canvas_breite_px": mm_to_pixels(canvas_breite_mm, dpi),
        "endgroesse_breite_px": mm_to_pixels(endgroesse_breite_mm, dpi),
        "datei_breite_px": mm_to_pixels(datei_breite_mm, dpi),

        # Masse in Pixel - Allgemein
        "beschnitt_px": mm_to_pixels(beschnittzugabe_mm, dpi),
        "sicherheitsrand_px": mm_to_pixels(sicherheitsabstand_mm, dpi),
        "text_grafik_offset_px": mm_to_pixels(DEFAULT_ABSTAND_GRAFIK_TEXT_MM, dpi),
        "text_bottom_offset_px": mm_to_pixels(DEFAULT_TEXT_BOTTOM_OFFSET_MM, dpi),

        # DEPRECATED (für Rückwärtskompatibilität)
        "max_grafik_px": mm_to_pixels(canvas_hoehe_mm, dpi),
        "endgroesse_px": mm_to_pixels(endgroesse_hoehe_mm, dpi),
        "datei_groesse_px": mm_to_pixels(datei_hoehe_mm, dpi),

        # DPI
        "dpi": dpi
    }


def calculate_grafik_y_offset_mm(
    text_height_mm: float,
    grafik_height_mm: float,
    position: str = GRAFIK_POSITION_VERTICAL,
    canvas_hoehe_mm: Optional[float] = None  # NEW (v7.3): Canvas-Höhe (aus RuntimeConfig wenn None)
) -> float:
    """
    Berechnet Y-Offset fuer Grafik im sicheren Bereich

    Positionierungs-Varianten:
        - "top": Grafik OBEN buendig (Luecke zwischen Grafik und Text)
        - "center": Grafik ZENTRIERT (Luecke oben und unten gleichmaessig)
        - "bottom": Grafik UNTEN am Text (Luecke oben)

    Aktuell: "top" (Variante 1)

    Formel (top) v2.4:
        Y_Offset = 0mm (immer oben!)
        Luecke = Sicherer_Bereich - Grafik_Hoehe - Text_Offset - Text_Hoehe
        Luecke = 39mm - 26.82mm - 1mm - 11.18mm = 0mm (OV+Staerke)

    Args:
        text_height_mm: Hoehe des Textes in mm
        grafik_height_mm: Hoehe der Grafik in mm
        position: Positionierung ("top", "center", "bottom")
        canvas_hoehe_mm: Canvas-Höhe in mm (None = aus RuntimeConfig, v7.3)

    Returns:
        float: Y-Offset in mm
    """
    # NEW (v7.3): Canvas-Höhe aus RuntimeConfig laden wenn nicht übergeben
    if canvas_hoehe_mm is None:
        try:
            from runtime_config import get_config
            config = get_config()
            canvas_hoehe_mm = config.zeichen_hoehe_mm - (2 * config.sicherheitsabstand_mm)
        except Exception:
            # Fallback auf Default
            canvas_hoehe_mm = DEFAULT_ZEICHEN_HOEHE_MM - (2 * DEFAULT_SICHERHEITSABSTAND_MM)

    # Verfuegbare Hoehe fuer Grafik-Bereich
    # CHANGED: text_height_mm enthält bereits TEXT_GRAFIK_OFFSET_MM + TEXT_BOTTOM_OFFSET_MM!
    available_height_mm = canvas_hoehe_mm - text_height_mm
    
    if position == "top":
        # Variante 1: OBEN buendig
        return 0.0
    elif position == "center":
        # Variante 2: ZENTRIERT
        gap = (available_height_mm - grafik_height_mm) / 2.0
        return gap
    elif position == "bottom":
        # Variante 3: UNTEN am Text
        return available_height_mm - grafik_height_mm
    else:
        # Default: oben
        return 0.0


# ================================================================================================
# ORDNER ERSTELLEN
# ================================================================================================

def create_directories():
    """Erstellt notwendige Verzeichnisse"""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    #TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    if not DEFAULT_ZEICHEN_DIR.exists():
        DEFAULT_ZEICHEN_DIR.mkdir(parents=True, exist_ok=True)
        
        info_file = DEFAULT_ZEICHEN_DIR / "README.txt"
        info_file.write_text(
            "Taktische Zeichen Ordner\n"
            "========================\n\n"
            "Lege hier deine SVG-Dateien in Unterordnern ab.\n"
            "Jeder Unterordner entspricht einer Kategorie.\n\n"
            "Beispiel-Struktur:\n"
            "  Taktische_Zeichen/\n"
            "  +-- Einheiten/\n"
            "  |   +-- N.svg\n"
            "  |   +-- TZ-.svg\n"
            "  +-- Fahrzeuge/\n"
            "  |   +-- ...\n"
            "  +-- Personen/\n"
            "      +-- ...\n",
            encoding='utf-8'
        )

# Bei Import ausfuehren
if sys.platform == 'win32':
    create_directories()


# ================================================================================================
# INFO-AUSGABE (fuer Debugging)
# ================================================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("{} - {}".format(PROGRAM_NAME, PROGRAM_VERSION))
    print("=" * 80)
    
    print("\n[PROGRAMM]")
    print("  Name: {}".format(PROGRAM_NAME))
    print("  Version: {}".format(PROGRAM_VERSION))
    
    print("\n[PFADE]")
    print("  Basis: {}".format(BASE_DIR))
    print("  Zeichen: {}".format(DEFAULT_ZEICHEN_DIR))
    print("  Export: {}".format(EXPORT_DIR))
    
    print("\n[DRUCK-MASSE]")
    dims = calculate_print_dimensions()
    print("  Endgroesse: {}mm ({}px)".format(dims['endgroesse_mm'], dims['endgroesse_px']))
    print("  Beschnitt: {}mm ({}px)".format(dims['BESCHNITTZUGABE_MM'], dims['beschnitt_px']))
    print("  Sicherheit: {}mm ({}px)".format(dims['SICHERHEITSABSTAND_MM'], dims['sicherheitsrand_px']))
    print("  Datei-Groesse: {}mm ({}px)".format(dims['datei_groesse_mm'], dims['datei_groesse_px']))
    print("  Max. Grafik: {}mm ({}px)".format(dims['max_grafik_mm'], dims['max_grafik_px']))
    print("  Text-Offset: {}mm (Abstand Grafik <-> Text)".format(DEFAULT_ABSTAND_GRAFIK_TEXT_MM))
    print("  Text-Offset: {}mm (Abstand Unterer Sicherheitsbereich <-> Text)".format(DEFAULT_TEXT_BOTTOM_OFFSET_MM))
    print("  DPI: {}".format(dims['dpi']))
    
    print("\n[PLATZHALTER]")
    #print("  OV: OV: {}".format(create_placeholder_text(PLACEHOLDER_OV_LENGTH)))
    print("  Ruf: Ruf: {}".format(create_placeholder_text(PLACEHOLDER_RUF_LENGTH)))
    print("  Staerke: {}".format(create_staerke_placeholder()))
    
    print("\n[TEXT]")
    print("  Font: {}".format(DEFAULT_FONT_FAMILY))
    print("  Size: {}pt".format(DEFAULT_FONT_SIZE))
    print("  Text-Offset: {}mm (Abstand Grafik <-> Text)".format(DEFAULT_ABSTAND_GRAFIK_TEXT_MM))
    print("  Text-Offset: {}mm (Abstand Unterer Sicherheitsbereich <-> Text)".format(DEFAULT_TEXT_BOTTOM_OFFSET_MM))
    print("  Line Height Factor: {}".format(LINE_HEIGHT_FACTOR))
    print("  Alignment: {}".format(TEXT_ALIGNMENT))
    
    print("\n[GRAFIK]")
    print("  Position: {} (oben buendig)".format(GRAFIK_POSITION_VERTICAL))
    print("  Groesse: DYNAMISCH berechnet")
    print("  Formel: 39mm - (TEXT_OFFSET + max(Text_alle_Modi))")
    print("  Beispiel: 39mm - (3mm + 9.18mm) = 26.82mm (ca.)")
    
    print("\n[SCHNEIDELINIEN (Test)]")
    print("  Linienbreite: {}px".format(CUT_LINE_WIDTH_PX))
    print("  Label Font: {}pt".format(CUT_LINE_LABEL_FONT_SIZE))
    print("  Label Offset: {}px".format(CUT_LINE_LABEL_OFFSET_PX))
    
    print("\n[MODI]")
    print("  Verfuegbar: {}".format(", ".join(AVAILABLE_MODI)))

    print("\n[DPI-OPTIMIERUNG] (v7.1+)")
    print("  DPI-Stufen: {}".format(DPI_STUFEN))

    print("\n" + "=" * 80)
    print("[OK] Alle Konstanten definiert!")
    print("[OK] Grafik-Groesse dynamisch berechenbar!")
    print("[INFO] TEXT_OFFSET_MM = 3.0mm (verhindert Ueberlappung!)")
    print("=" * 80)


# ================================================================================================
# DPI-OPTIMIERUNG (v7.1+)
# ================================================================================================

from dataclasses import dataclass

@dataclass
class RenderProfile:
    """
    Performance-Profil für verschiedene Bildgrößen

    Attributes:
        name: Profilname (z.B. "Standard", "XXL")
        dpi: Empfohlene DPI-Auflösung
        threads: Empfohlene Thread-Anzahl
        render_scale: Empfohlene Render-Skalierung
        description: Beschreibung des Profils
    """
    name: str
    dpi: int
    threads: int
    render_scale: float
    description: str


def get_lower_dpi_level(current_dpi: int) -> int:
    """
    Gibt die nächstniedrigere DPI-Stufe zurück

    Wird verwendet für Schnittlinien-Modus, um Performance zu verbessern.

    Args:
        current_dpi: Aktuelle DPI

    Returns:
        Nächstniedrigere DPI-Stufe (oder 100 wenn bereits am Minimum)

    Examples:
        >>> get_lower_dpi_level(600)
        450
        >>> get_lower_dpi_level(150)
        100
        >>> get_lower_dpi_level(100)
        100
    """
    for i, dpi in enumerate(DPI_STUFEN):
        if dpi >= current_dpi:
            # Gib vorherige Stufe zurück (wenn vorhanden)
            return DPI_STUFEN[max(0, i - 1)]

    # Fallback: niedrigste Stufe
    return DPI_STUFEN[0]


def calculate_optimal_dpi(
    zeichen_hoehe_mm: float,
    zeichen_breite_mm: float,
    base_dpi: int = 600
) -> int:
    """
    Berechnet optimale DPI basierend auf Zeichengröße

    Regel: Kleinere Zeichen = höhere DPI, größere Zeichen = niedrigere DPI
    Große Druckformate werden aus größerer Entfernung betrachtet und
    benötigen keine 600 DPI.

    Args:
        zeichen_hoehe_mm: Höhe des Zeichens in mm
        zeichen_breite_mm: Breite des Zeichens in mm
        base_dpi: Basis-DPI (Maximum, vom User gewählt)

    Returns:
        Optimale DPI für diese Größe (nie höher als base_dpi)

    DPI-Skalierung:
        - <= 50mm: 600 DPI (Standard, hohe Qualität)
        - 50-100mm: 450 DPI
        - 100-200mm: 300 DPI (Poster-Qualität)
        - 200-400mm: 200 DPI
        - >= 400mm: 150 DPI (Banner-Qualität)

    Examples:
        >>> calculate_optimal_dpi(45, 45, 600)
        600
        >>> calculate_optimal_dpi(445, 445, 600)
        150
    """
    max_dimension = max(zeichen_hoehe_mm, zeichen_breite_mm)

    if max_dimension <= 50:
        optimal_dpi = 600
    elif max_dimension <= 100:
        optimal_dpi = 450
    elif max_dimension <= 200:
        optimal_dpi = 300
    elif max_dimension <= 400:
        optimal_dpi = 200
    else:
        optimal_dpi = 150

    # Nie höher als User-Wunsch
    return min(optimal_dpi, base_dpi)


def calculate_optimal_threads(
    zeichen_hoehe_mm: float,
    zeichen_breite_mm: float,
    dpi: int,
    max_threads: int = 6  # Erhöht von 4 auf 6
) -> int:
    """
    Berechnet optimale Thread-Anzahl basierend auf Bildgröße

    Regel: Je größer das Bild, desto weniger Threads
    Bei großen Bildern ist I/O (Festplatten-Schreiben) der Flaschenhals,
    nicht CPU. Mehrere Threads verschlimmern das Problem.

    Args:
        zeichen_hoehe_mm: Höhe in mm
        zeichen_breite_mm: Breite in mm
        dpi: Verwendete DPI
        max_threads: Maximum (aus User-Einstellungen)

    Returns:
        Optimale Thread-Anzahl (1-4)

    Examples:
        >>> calculate_optimal_threads(45, 45, 600, 4)
        4
        >>> calculate_optimal_threads(445, 445, 150, 4)
        1
    """
    total_pixels = (
        mm_to_pixels(zeichen_hoehe_mm, dpi) *
        mm_to_pixels(zeichen_breite_mm, dpi)
    )

    megapixels = total_pixels / 1_000_000

    if megapixels <= 10:
        return max_threads  # 4 Threads (Standard: 45mm @ 600dpi = 7 MP)
    elif megapixels <= 25:
        return max(2, max_threads // 2)  # 2 Threads
    elif megapixels <= 50:
        return 1  # 1 Thread
    else:
        # Bei extrem großen Bildern: 1 Thread
        return 1


def calculate_render_profile(
    zeichen_hoehe_mm: float,
    zeichen_breite_mm: float,
    user_dpi: int = 600,
    max_threads: int = 6  # Erhöht von 4 auf 6
) -> RenderProfile:
    """
    Berechnet optimales Render-Profil basierend auf Zeichengröße

    Kombiniert DPI-Reduzierung + Thread-Reduzierung + Render-Scale-Anpassung
    in vordefinierte Profile.

    WICHTIG: Respektiert minimum_dpi_for_print aus RuntimeConfig (z.B. 300 DPI).
    Wenn User bewusst niedrigere DPI wählt, wird das als Test-Export interpretiert.

    Args:
        zeichen_hoehe_mm: Höhe des Zeichens in mm
        zeichen_breite_mm: Breite des Zeichens in mm
        user_dpi: Basis-DPI (vom User gewählt)
        max_threads: Maximale Thread-Anzahl (aus Einstellungen)

    Returns:
        RenderProfile mit allen optimierten Einstellungen

    Examples:
        >>> profile = calculate_render_profile(45, 45, 600, 4)
        >>> profile.name
        'Standard (hohe Qualität)'
        >>> profile.threads
        4

        >>> profile = calculate_render_profile(45, 90, 600, 4)
        >>> profile.name
        'Standard (hohe Qualität)'
        >>> profile.threads
        4

        >>> profile = calculate_render_profile(445, 445, 600, 4)
        >>> profile.name
        'XXL (Weitansicht)'
        >>> profile.dpi
        150
        >>> profile.threads
        1
    """
    max_dimension = max(zeichen_hoehe_mm, zeichen_breite_mm)

    # Profil-Definitionen (empfohlene Werte basierend auf Größe)
    if max_dimension <= 100:
        profile = RenderProfile(
            name="Standard (hohe Qualität)",
            dpi=min(user_dpi, 600),
            threads=max_threads,
            render_scale=2.0,
            description="Optimal für kleine bis mittlere Zeichen (bis 100mm)"
        )

    elif max_dimension <= 150:
        profile = RenderProfile(
            name="Mittel (gute Qualität)",
            dpi=min(user_dpi, 450),
            threads=max(2, max_threads // 2),
            render_scale=1.5,
            description="Optimal für mittlere Zeichen (100-150mm)"
        )

    elif max_dimension <= 200:
        profile = RenderProfile(
            name="Poster (Poster-Qualität)",
            dpi=min(user_dpi, 300),
            threads=2,
            render_scale=1.5,
            description="Optimal für Poster (150-200mm)"
        )

    elif max_dimension <= 400:
        profile = RenderProfile(
            name="Banner (Display-Qualität)",
            dpi=min(user_dpi, 200),
            threads=1,
            render_scale=1.2,
            description="Optimal für Banner (200-400mm)"
        )

    else:  # >= 400mm
        profile = RenderProfile(
            name="XXL (Weitansicht)",
            dpi=min(user_dpi, 150),
            threads=1,
            render_scale=1.0,
            description="Optimal für sehr große Formate (>400mm)"
        )

    # WICHTIG: Mindest-DPI aus RuntimeConfig respektieren (Druckerei-Anforderung)
    # Wenn User BEWUSST niedrigere DPI gewählt hat, ist das ein Test-Export
    try:
        from runtime_config import get_config
        config = get_config()
        minimum_dpi = config.minimum_dpi_for_print

        # Nur anwenden wenn User DPI >= Mindest-DPI (kein Test-Export)
        if user_dpi >= minimum_dpi and profile.dpi < minimum_dpi:
            profile.dpi = minimum_dpi
            # Name anpassen um Mindest-DPI-Override zu kennzeichnen
            profile.description = f"{profile.description} (DPI auf {minimum_dpi} erhöht für Druckqualität)"
    except:
        # RuntimeConfig nicht verfügbar (z.B. in Tests) -> ignorieren
        pass

    return profile


# ================================================================================================
# TEST ROUTINES
# ================================================================================================

if __name__ == "__main__":
    """
    Test-Routine für constants.py

    Testet alle Hilfsfunktionen und Berechnungen.
    Ausführung: python constants.py
    """
    print("=" * 70)
    print("TEST-ROUTINE: constants.py")
    print("=" * 70)

    # Test 1: Millimeter <-> Pixel Konvertierung
    print("\n[Test 1] mm_to_pixels() / pixels_to_mm()")
    print("-" * 70)

    test_mm = 45.0
    test_dpi = 300
    pixels = mm_to_pixels(test_mm, test_dpi)
    back_to_mm = pixels_to_mm(pixels, test_dpi)

    print(f"  Input: {test_mm} mm bei {test_dpi} DPI")
    print(f"  -> {pixels} Pixel")
    print(f"  -> {back_to_mm:.2f} mm (Rueckkonvertierung)")
    print(f"  Differenz: {abs(test_mm - back_to_mm):.6f} mm")

    assert abs(test_mm - back_to_mm) < 0.1, "Konvertierung fehlgeschlagen!"
    print("  [OK] Konvertierung korrekt")

    # Test 2: Platzhalter-Text
    print("\n[Test 2] create_placeholder_text()")
    print("-" * 70)

    placeholder_5 = create_placeholder_text(5)
    placeholder_10 = create_placeholder_text(10, "-")

    print(f"  create_placeholder_text(5): '{placeholder_5}'")
    print(f"  create_placeholder_text(10, '-'): '{placeholder_10}'")

    assert placeholder_5 == "_____", "Platzhalter 5 fehlerhaft!"
    assert placeholder_10 == "----------", "Platzhalter 10 fehlerhaft!"
    print("  [OK] Platzhalter korrekt generiert")

    # Test 3: Staerke-Platzhalter
    print("\n[Test 3] create_staerke_placeholder()")
    print("-" * 70)

    staerke_default = create_staerke_placeholder()
    staerke_custom = create_staerke_placeholder([3, 3, 3, 2])

    print(f"  Default: '{staerke_default}'")
    print(f"  Custom [3,3,3,2]: '{staerke_custom}'")

    assert "/" in staerke_default, "Trennzeichen fehlt!"
    assert staerke_custom == "    /     /     / __", "Custom Staerke fehlerhaft!"
    print("  [OK] Staerke-Platzhalter korrekt")

    # Test 4: Druckdimensionen berechnen
    print("\n[Test 4] calculate_print_dimensions()")
    print("-" * 70)

    # Test mit Defaults
    result = calculate_print_dimensions(
        dpi=300,
        zeichen_hoehe_mm=45.0,
        zeichen_breite_mm=45.0,
        sicherheitsabstand_mm=3.0,
        beschnittzugabe_mm=3.0
    )

    print(f"  Zeichen: 45x45 mm")
    print(f"  Sicherheitsabstand: 3 mm")
    print(f"  Beschnittzugabe: 3 mm")
    print(f"  -> Canvas: {result['canvas_hoehe_mm']}x{result['canvas_breite_mm']} mm")
    print(f"  -> Endgroesse: {result['endgroesse_hoehe_mm']}x{result['endgroesse_breite_mm']} mm")
    print(f"  -> Datei: {result['datei_hoehe_mm']}x{result['datei_breite_mm']} mm")

    # Validierung
    expected_canvas = 39.0  # 45 - 2*3
    expected_endgroesse = 45.0
    expected_datei = 51.0  # 45 + 2*3

    assert result['canvas_hoehe_mm'] == expected_canvas, "Canvas-Hoehe falsch!"
    assert result['endgroesse_hoehe_mm'] == expected_endgroesse, "Endgroesse-Hoehe falsch!"
    assert result['datei_hoehe_mm'] == expected_datei, "Datei-Hoehe falsch!"
    print("  [OK] Druckdimensionen korrekt berechnet")

    # Test 5: Export-Ordnername
    print("\n[Test 5] create_export_folder_name()")
    print("-" * 70)

    folder_name = create_export_folder_name(
        count=42,
        dpi=600,
        file_format="PNG",
        export_format="Einzelzeichen"
    )

    print(f"  Ordnername: {folder_name}")

    assert "PNG" in folder_name, "Format fehlt!"
    assert "Einzelzeichen" in folder_name, "Export-Format fehlt!"
    assert "42" in folder_name, "Anzahl fehlt!"
    assert "600" in folder_name, "DPI fehlt!"
    print("  [OK] Ordnername korrekt generiert")

    # Test 6: DPI-Reduktion
    print("\n[Test 6] get_lower_dpi_level()")
    print("-" * 70)

    dpi_tests = [
        (600, 450),
        (450, 300),
        (300, 200),
        (200, 150),
        (150, 100),
        (100, 100)
    ]

    for current, expected in dpi_tests:
        result = get_lower_dpi_level(current)
        print(f"  {current} DPI -> {result} DPI")
        assert result == expected, f"DPI-Reduktion {current} fehlerhaft!"

    print("  [OK] DPI-Reduktion korrekt")

    # Test 7: Optimale Thread-Anzahl
    print("\n[Test 7] calculate_optimal_threads()")
    print("-" * 70)

    # Test mit verschiedenen Zeichengrößen
    threads_small = calculate_optimal_threads(45, 45, 600, max_threads=4)
    threads_medium = calculate_optimal_threads(200, 200, 300, max_threads=4)
    threads_large = calculate_optimal_threads(445, 445, 150, max_threads=4)

    print(f"  45x45mm @ 600 DPI -> {threads_small} Threads")
    print(f"  200x200mm @ 300 DPI -> {threads_medium} Threads")
    print(f"  445x445mm @ 150 DPI -> {threads_large} Threads")

    assert threads_small >= 1, "Mindestens 1 Thread!"
    assert threads_large >= 1, "Mindestens 1 Thread!"
    assert threads_small <= 4, "Max 4 Threads!"
    print("  [OK] Thread-Berechnung korrekt")

    # Test 8: S1-Layout Konstanten
    print("\n[Test 8] S1-Layout Konstanten")
    print("-" * 70)

    # Factory Defaults
    print("  Factory Defaults:")
    print(f"    DEFAULT_S1_ASPECT_LOCKED: {DEFAULT_S1_ASPECT_LOCKED}")
    assert isinstance(DEFAULT_S1_ASPECT_LOCKED, bool), "ASPECT_LOCKED muss bool sein!"
    assert DEFAULT_S1_ASPECT_LOCKED == True, "ASPECT_LOCKED sollte standardmaessig True sein!"

    print(f"    DEFAULT_S1_LINKS_PROZENT: {DEFAULT_S1_LINKS_PROZENT}%")
    assert isinstance(DEFAULT_S1_LINKS_PROZENT, int), "LINKS_PROZENT muss int sein!"
    assert 20 <= DEFAULT_S1_LINKS_PROZENT <= 80, "LINKS_PROZENT muss zwischen 20-80 liegen!"

    print(f"    DEFAULT_S1_ANZAHL_SCHREIBLINIEN: {DEFAULT_S1_ANZAHL_SCHREIBLINIEN} Zeilen")
    assert isinstance(DEFAULT_S1_ANZAHL_SCHREIBLINIEN, int), "ANZAHL_SCHREIBLINIEN muss int sein!"
    assert 3 <= DEFAULT_S1_ANZAHL_SCHREIBLINIEN <= 10, "ANZAHL_SCHREIBLINIEN muss zwischen 3-10 liegen!"

    print(f"    DEFAULT_S1_STAERKE_ANZEIGEN: {DEFAULT_S1_STAERKE_ANZEIGEN}")
    assert isinstance(DEFAULT_S1_STAERKE_ANZEIGEN, bool), "STAERKE_ANZEIGEN muss bool sein!"

    # Rendering Konstanten
    print(f"  Rendering-Konstanten:")
    print(f"    S1_LINE_COLOR: {S1_LINE_COLOR} (RGB)")
    assert isinstance(S1_LINE_COLOR, tuple), "LINE_COLOR muss tuple sein!"
    assert len(S1_LINE_COLOR) == 3, "LINE_COLOR muss RGB haben (3 Werte)!"

    print(f"    S1_LINE_WIDTH: {S1_LINE_WIDTH}px")
    assert isinstance(S1_LINE_WIDTH, int), "LINE_WIDTH muss int sein!"
    assert S1_LINE_WIDTH > 0, "LINE_WIDTH muss positiv sein!"

    print(f"    S1_LINE_MARGIN_MM: {S1_LINE_MARGIN_MM}mm")
    assert isinstance(S1_LINE_MARGIN_MM, (int, float)), "LINE_MARGIN muss numeric sein!"
    assert S1_LINE_MARGIN_MM >= 0, "LINE_MARGIN muss nicht-negativ sein!"

    # S1 nutzt gemeinsame Konstanten von S2
    print(f"  Gemeinsame Konstanten (mit S2 geteilt):")
    print(f"    LINE_HEIGHT_FACTOR: {LINE_HEIGHT_FACTOR}")
    assert isinstance(LINE_HEIGHT_FACTOR, (int, float)), "LINE_HEIGHT_FACTOR muss numeric sein!"
    assert LINE_HEIGHT_FACTOR > 1.0, "LINE_HEIGHT_FACTOR sollte > 1 sein fuer Zeilenabstand!"

    print("  [OK] S1-Layout Konstanten korrekt")

    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ALLE TESTS BESTANDEN!")
    print("=" * 70)