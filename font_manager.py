#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
font_manager.py - Schriftarten-Management

Features:
- Überprüfung ob Schriftarten verfügbar sind
- Fallback-Mechanismus für fehlende Schriftarten
- User-Warnung bei fehlenden Schriftarten
"""

from typing import Optional, List
from pathlib import Path
import platform
import os
import glob

from PIL import ImageFont

from logging_manager import LoggingManager


class FontManager:
    """
    Schriftarten-Manager

    Features:
    - Font-Verfügbarkeit prüfen
    - Fallback-Fonts
    - User-Warnungen

    OPTIMIZED v0.8.2.4: Font-Cache als Klassen-Variable (wird nur 1x gebaut, shared zwischen Instanzen)
    """

    # Prioritäts-Liste für Schriftarten (in Reihenfolge der Präferenz)
    FONT_PRIORITY_LIST = [
        "Arial",
        "Liberation Sans",
        "DejaVu Sans",
        "Helvetica",
        "sans-serif"
    ]

    # Cache für System-Fonts (Klassen-Variable - shared zwischen allen Instanzen)
    _system_fonts_cache: Optional[List[str]] = None

    def __init__(self):
        """Initialisiert Font-Manager"""
        self.logger = LoggingManager().get_logger(__name__)

    def _get_system_font_directories(self) -> List[Path]:
        """
        Gibt System-Font-Verzeichnisse zurück (plattformspezifisch)

        Returns:
            Liste von Font-Verzeichnissen
        """
        font_dirs = []
        system = platform.system()

        if system == "Windows":
            # Windows Font-Verzeichnisse
            font_dirs.append(Path(os.environ.get('WINDIR', 'C:\\Windows')) / 'Fonts')
            # User-Fonts (Windows 10+)
            local_app_data = os.environ.get('LOCALAPPDATA')
            if local_app_data:
                font_dirs.append(Path(local_app_data) / 'Microsoft' / 'Windows' / 'Fonts')

        elif system == "Darwin":  # macOS
            font_dirs.extend([
                Path('/Library/Fonts'),
                Path('/System/Library/Fonts'),
                Path.home() / 'Library' / 'Fonts'
            ])

        elif system == "Linux":
            font_dirs.extend([
                Path('/usr/share/fonts'),
                Path('/usr/local/share/fonts'),
                Path.home() / '.fonts',
                Path.home() / '.local' / 'share' / 'fonts'
            ])

        # Filtere nur existierende Verzeichnisse
        existing_dirs = [d for d in font_dirs if d.exists()]
        return existing_dirs

    def _get_font_name_from_file(self, font_path: Path) -> Optional[str]:
        """
        Extrahiert Font-Namen aus TTF/OTF-Datei

        Args:
            font_path: Pfad zur Font-Datei

        Returns:
            Font-Name oder None bei Fehler
        """
        try:
            # Lade Font und extrahiere Namen
            font = ImageFont.truetype(str(font_path), size=12)
            # Font-Name ist im font.getname() Tuple: (family, style)
            if hasattr(font, 'getname'):
                family, style = font.getname()
                return family
            # Fallback: Verwende Dateinamen ohne Extension
            return font_path.stem

        except Exception:
            return None

    def _build_system_fonts_cache(self) -> List[str]:
        """
        Scannt System-Font-Verzeichnisse und cached verfügbare Font-Namen

        Returns:
            Liste von Font-Namen (lowercase für Case-insensitive Vergleich)
        """
        font_names = []

        # Hole System-Font-Verzeichnisse
        font_dirs = self._get_system_font_directories()

        if not font_dirs:
            self.logger.warning("Keine System-Font-Verzeichnisse gefunden")
            return font_names

        self.logger.debug(f"Scanne {len(font_dirs)} Font-Verzeichnisse...")

        # Durchsuche alle Font-Verzeichnisse
        for font_dir in font_dirs:
            # Suche .ttf und .otf Dateien (auch in Unterverzeichnissen)
            for ext in ['*.ttf', '*.TTF', '*.otf', '*.OTF']:
                pattern = str(font_dir / '**' / ext)
                for font_file_path in glob.glob(pattern, recursive=True):
                    try:
                        font_file = Path(font_file_path)
                        # Extrahiere Font-Namen aus Datei
                        system_font_name = self._get_font_name_from_file(font_file)

                        if system_font_name:
                            font_names.append(system_font_name.lower())

                    except Exception:
                        # Ignoriere fehlerhafte Font-Dateien
                        continue

        self.logger.debug(f"Font-Cache erstellt: {len(font_names)} Schriftarten gefunden")
        return font_names

    def check_font_available(self, font_name: str) -> bool:
        """
        Prüft ob Schriftart verfügbar ist

        CHANGED v0.8.2.4: Durchsucht System-Font-Verzeichnisse und liest Font-Namen aus Metadaten
        OPTIMIZED: Cache als Klassen-Variable (nur 1x gebaut, shared zwischen Instanzen)

        Args:
            font_name: Name der Schriftart (z.B. "Arial", "Roboto Slab")

        Returns:
            bool: True wenn Schriftart verfügbar, False sonst
        """
        # Baue Cache beim ersten Aufruf (Klassen-Variable)
        if FontManager._system_fonts_cache is None:
            FontManager._system_fonts_cache = self._build_system_fonts_cache()

            if not FontManager._system_fonts_cache:
                # Keine Fonts gefunden - konservativ annehmen dass verfügbar
                self.logger.warning("Font-Cache leer - nehme an dass Font verfügbar ist")
                return True

        # Prüfe ob Font im Cache
        font_name_lower = font_name.lower()
        return font_name_lower in FontManager._system_fonts_cache

    def get_available_font(self, preferred_font: str = None) -> str:
        """
        Gibt verfügbare Schriftart zurück (mit Fallback)

        Args:
            preferred_font: Bevorzugte Schriftart (optional)

        Returns:
            str: Verfügbare Schriftart
        """
        # Wenn bevorzugte Schriftart angegeben, prüfe diese zuerst
        if preferred_font:
            if self.check_font_available(preferred_font):
                self.logger.info(f"Verwende bevorzugte Schriftart: {preferred_font}")
                return preferred_font
            else:
                self.logger.warning(f"Bevorzugte Schriftart '{preferred_font}' nicht verfügbar")

        # Fallback: Prioritäts-Liste durchgehen
        for font in self.FONT_PRIORITY_LIST:
            if self.check_font_available(font):
                self.logger.info(f"Verwende Fallback-Schriftart: {font}")
                return font

        # Wenn gar nichts verfügbar: System-Default
        self.logger.error("Keine Schriftart aus Prioritäts-Liste verfügbar! Verwende System-Default.")
        return "sans-serif"

    def get_font_warning_message(self, font_name: str) -> str:
        """
        Erzeugt Warnungs-Nachricht für fehlende Schriftart

        Args:
            font_name: Name der fehlenden Schriftart

        Returns:
            str: Warnungs-Text für Message-Box
        """
        available_fonts = [f for f in self.FONT_PRIORITY_LIST if self.check_font_available(f)]

        message = (
            f"Die Schriftart '{font_name}' ist nicht auf Ihrem System installiert.\n\n"
            f"Dies kann zu abweichenden Text-Layouts führen.\n\n"
        )

        if available_fonts:
            fallback = available_fonts[0]
            message += (
                f"Es wird stattdessen '{fallback}' verwendet.\n\n"
                f"Für optimale Ergebnisse empfehlen wir die Installation von '{font_name}'.\n\n"
            )
        else:
            message += (
                f"Es wird die System-Standard-Schriftart verwendet.\n\n"
                f"WARNUNG: Text-Layouts können stark abweichen!\n\n"
            )

        # Download-Link für Arial (Microsoft)
        if font_name.lower() == "arial":
            message += (
                "Download:\n"
                "https://www.microsoft.com/en-us/download/details.aspx?id=48044\n"
                "(Microsoft TrueType Core Fonts)"
            )

        return message

    def check_and_get_font(self, preferred_font: str) -> tuple[str, bool]:
        """
        Prüft Schriftart und gibt verfügbare Font + Warning-Status zurück

        Args:
            preferred_font: Bevorzugte Schriftart

        Returns:
            tuple: (verfügbare_schriftart, needs_warning)
        """
        if self.check_font_available(preferred_font):
            return preferred_font, False
        else:
            fallback_font = self.get_available_font(preferred_font)
            return fallback_font, True


# ================================================================================================
# TESTING
# ================================================================================================

if __name__ == "__main__":
    # Test-Code
    print("=" * 80)
    print("FontManager Test")
    print("=" * 80)

    manager = FontManager()

    # Test 1: Arial prüfen
    print("\n[Test 1] Arial verfügbar?")
    arial_available = manager.check_font_available("Arial")
    print(f"  Ergebnis: {arial_available}")

    # Test 2: Fallback-Font
    print("\n[Test 2] Fallback-Font für 'NonExistentFont'")
    fallback = manager.get_available_font("NonExistentFont")
    print(f"  Ergebnis: {fallback}")

    # Test 3: Warnung generieren
    print("\n[Test 3] Warnungs-Nachricht für Arial")
    if not arial_available:
        warning = manager.get_font_warning_message("Arial")
        print(f"  Warnung:\n{warning}")

    # Test 4: Check and Get
    print("\n[Test 4] Check and Get für Arial")
    font, needs_warning = manager.check_and_get_font("Arial")
    print(f"  Font: {font}")
    print(f"  Warnung nötig: {needs_warning}")

    print("\n" + "=" * 80)
