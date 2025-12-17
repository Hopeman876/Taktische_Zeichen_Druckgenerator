#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
missing_fonts_tracker.py - Tracking fehlender Schriftarten in SVG-Dateien

Version: 1.0.0 (v0.8.1)

Funktionalität:
- Extrahiert Schriftarten aus SVG-Dateien
- Prüft ob Schriftarten auf dem System installiert sind
- Sammelt fehlende Schriftarten während des Exports
- Erstellt Bericht "Fehlende_Schriftarten.txt"
"""

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Set, Dict, List, Optional
import logging
from collections import defaultdict


class MissingFontsTracker:
    """
    Tracker für fehlende Schriftarten in SVG-Dateien

    Verwendung:
        tracker = MissingFontsTracker()

        # Während des Exports:
        tracker.check_svg(svg_path, zeichen_id)

        # Am Ende:
        tracker.write_report(output_dir)

    OPTIMIZED v0.8.2.4: Font-Cache als Klassen-Variable (wird nur 1x gebaut, shared zwischen Instanzen)
    """

    # Cache für System-Fonts (Klassen-Variable - shared zwischen allen Instanzen)
    _system_fonts_cache: Optional[Set[str]] = None

    def __init__(self):
        """Initialisiert den Tracker"""
        self.logger = logging.getLogger(__name__)

        # Set aller gefundenen Schriftarten (eindeutig)
        self.all_fonts_in_svgs: Set[str] = set()

        # Dictionary: {font_name: [zeichen_ids]}
        self.fonts_per_zeichen: Dict[str, List[str]] = defaultdict(list)

        # Set der fehlenden Schriftarten (werden nur einmal geprüft)
        self.missing_fonts: Set[str] = set()

        # Dictionary: {font_name: [zeichen_ids]} für fehlende Schriftarten
        self.missing_fonts_per_zeichen: Dict[str, List[str]] = defaultdict(list)

        self.logger.info("MissingFontsTracker initialisiert")

    def check_svg(self, svg_path: Path, zeichen_id: str) -> None:
        """
        Extrahiert Schriftarten aus SVG-Datei und prüft ob sie installiert sind

        Args:
            svg_path: Pfad zur SVG-Datei
            zeichen_id: Eindeutige ID des Zeichens (für Bericht)
        """
        if not svg_path.exists():
            self.logger.warning(f"SVG-Datei nicht gefunden: {svg_path}")
            return

        # Extrahiere Schriftarten aus SVG
        fonts_in_svg = self._extract_fonts_from_svg(svg_path)

        if not fonts_in_svg:
            # Keine Schriftarten in SVG → kein Problem
            return

        self.logger.debug(
            f"SVG '{svg_path.name}' ({zeichen_id}): {len(fonts_in_svg)} Schriftarten gefunden: {fonts_in_svg}"
        )

        # Prüfe jede Schriftart
        for font_name in fonts_in_svg:
            self.all_fonts_in_svgs.add(font_name)
            self.fonts_per_zeichen[font_name].append(zeichen_id)

            # Prüfe ob Schriftart installiert ist
            if not self._is_font_installed(font_name):
                if font_name not in self.missing_fonts:
                    self.logger.warning(
                        f"Fehlende Schriftart: '{font_name}' (zuerst in {zeichen_id})"
                    )
                    self.missing_fonts.add(font_name)

                self.missing_fonts_per_zeichen[font_name].append(zeichen_id)

    def _extract_fonts_from_svg(self, svg_path: Path) -> Set[str]:
        """
        Extrahiert Schriftarten aus SVG-Datei

        Sucht nach:
        - font-family Attributen
        - CSS font-family Deklarationen im style-Attribut

        Args:
            svg_path: Pfad zur SVG-Datei

        Returns:
            Set von Schriftarten-Namen
        """
        fonts = set()

        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # SVG-Namespace
            ns = {'svg': 'http://www.w3.org/2000/svg'}

            # Methode 1: font-family Attribute direkt
            for elem in root.iter():
                font_family = elem.get('font-family')
                if font_family:
                    # Mehrere Schriftarten möglich: "Arial, sans-serif"
                    for font in font_family.split(','):
                        font = font.strip().strip("'\"")
                        # Generische Schriftarten ignorieren
                        if font not in ['serif', 'sans-serif', 'monospace', 'cursive', 'fantasy']:
                            fonts.add(font)

            # Methode 2: style-Attribut mit CSS-Eigenschaften
            for elem in root.iter():
                style = elem.get('style')
                if style and 'font-family' in style:
                    # Parse CSS: "font-size:12px;font-family:'Arial';color:black"
                    for declaration in style.split(';'):
                        if 'font-family' in declaration:
                            # "font-family:'Arial'" → "'Arial'"
                            font_value = declaration.split(':', 1)[1].strip()
                            # Mehrere Schriftarten möglich
                            for font in font_value.split(','):
                                font = font.strip().strip("'\"")
                                if font not in ['serif', 'sans-serif', 'monospace', 'cursive', 'fantasy']:
                                    fonts.add(font)

            # Methode 3: <text> Elemente mit font-family
            for text_elem in root.findall('.//svg:text', ns):
                font_family = text_elem.get('font-family')
                if font_family:
                    for font in font_family.split(','):
                        font = font.strip().strip("'\"")
                        if font not in ['serif', 'sans-serif', 'monospace', 'cursive', 'fantasy']:
                            fonts.add(font)

        except ET.ParseError as e:
            self.logger.error(f"Fehler beim Parsen von {svg_path.name}: {e}")
        except Exception as e:
            self.logger.error(f"Unerwarteter Fehler bei {svg_path.name}: {e}")

        return fonts

    def _get_system_font_directories(self) -> List[Path]:
        """
        Gibt System-Font-Verzeichnisse zurück (plattformspezifisch)

        Returns:
            Liste von Font-Verzeichnissen
        """
        import platform
        import os

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
        from PIL import ImageFont

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

    def _build_system_fonts_cache(self) -> Set[str]:
        """
        Scannt System-Font-Verzeichnisse und cached verfügbare Font-Namen

        Returns:
            Set von Font-Namen (lowercase für Case-insensitive Vergleich)
        """
        import glob

        font_names = set()

        # Hole System-Font-Verzeichnisse
        font_dirs = self._get_system_font_directories()

        if not font_dirs:
            self.logger.warning("Keine System-Font-Verzeichnisse gefunden")
            return font_names

        self.logger.debug(f"Scanne {len(font_dirs)} Font-Verzeichnisse...")

        # Durchsuche alle Font-Verzeichnisse
        font_count = 0
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
                            font_names.add(system_font_name.lower())
                            font_count += 1

                    except Exception:
                        # Ignoriere fehlerhafte Font-Dateien
                        continue

        self.logger.debug(f"Font-Cache erstellt: {font_count} Schriftarten gefunden")
        return font_names

    def _is_font_installed(self, font_name: str) -> bool:
        """
        Prüft ob Schriftart auf dem System installiert ist

        CHANGED v0.8.2.4: Durchsucht System-Font-Verzeichnisse und liest Font-Namen aus Metadaten
        OPTIMIZED: Cache als Klassen-Variable (nur 1x gebaut, shared zwischen Instanzen)

        Args:
            font_name: Name der Schriftart (z.B. "Roboto Slab", "Arial")

        Returns:
            True wenn installiert, False sonst
        """
        # Baue Cache beim ersten Aufruf (Klassen-Variable)
        if MissingFontsTracker._system_fonts_cache is None:
            MissingFontsTracker._system_fonts_cache = self._build_system_fonts_cache()

            if not MissingFontsTracker._system_fonts_cache:
                # Keine Fonts gefunden - konservativ annehmen dass alle installiert sind
                self.logger.warning("Font-Cache leer - nehme an dass alle Fonts installiert sind")
                return True

        # Prüfe ob Font im Cache
        font_name_lower = font_name.lower()
        is_installed = font_name_lower in MissingFontsTracker._system_fonts_cache

        if is_installed:
            self.logger.debug(f"Schriftart '{font_name}' gefunden (installiert)")
        else:
            self.logger.debug(f"Schriftart '{font_name}' nicht gefunden (fehlt)")

        return is_installed

    def has_missing_fonts(self) -> bool:
        """
        Prüft ob fehlende Schriftarten gefunden wurden

        Returns:
            True wenn mindestens eine Schriftart fehlt
        """
        return len(self.missing_fonts) > 0

    def get_missing_fonts_count(self) -> int:
        """
        Gibt Anzahl fehlender Schriftarten zurück

        Returns:
            Anzahl fehlender Schriftarten
        """
        return len(self.missing_fonts)

    def write_report(self, output_dir: Path) -> Optional[Path]:
        """
        Erstellt Bericht über fehlende Schriftarten

        Format:
        ```
        FEHLENDE SCHRIFTARTEN
        =====================

        Es wurden folgende Schriftarten nicht gefunden:
        - Arial Narrow
        - Comic Sans MS

        DETAILS
        =======

        Schriftart: Arial Narrow
        Verwendet in folgenden Zeichen:
          - Zeichen_001_MTW
          - Zeichen_003_LF20
          - Zeichen_005_DLK23

        Schriftart: Comic Sans MS
        Verwendet in folgenden Zeichen:
          - Zeichen_002_Gruppe
        ```

        Args:
            output_dir: Ausgabe-Verzeichnis

        Returns:
            Path zur erstellten Datei, None wenn keine fehlenden Schriftarten
        """
        if not self.missing_fonts:
            self.logger.info("Keine fehlenden Schriftarten gefunden - kein Bericht erstellt")
            return None

        output_file = output_dir / "Fehlende_Schriftarten.txt"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("FEHLENDE SCHRIFTARTEN IN SVG-DATEIEN\n")
                f.write("=" * 70 + "\n\n")

                f.write("HINWEIS:\n")
                f.write("Die folgenden Schriftarten wurden in den SVG-Dateien verwendet,\n")
                f.write("sind aber auf diesem PC nicht installiert.\n\n")
                f.write("BITTE PRUEFEN SIE DIE GENERIERTEN ZEICHEN!\n")
                f.write("Fehlende Schriftarten werden durch eine Standard-Schriftart ersetzt,\n")
                f.write("was zu abweichendem Aussehen fuehren kann.\n\n")

                f.write("=" * 70 + "\n\n")

                f.write("ZUSAMMENFASSUNG\n")
                f.write("-" * 70 + "\n\n")

                f.write(f"Anzahl fehlender Schriftarten: {len(self.missing_fonts)}\n\n")

                f.write("Es wurden folgende Schriftarten nicht gefunden:\n")
                for font_name in sorted(self.missing_fonts):
                    f.write(f"  - {font_name}\n")

                f.write("\n")
                f.write("=" * 70 + "\n\n")

                f.write("DETAILS\n")
                f.write("-" * 70 + "\n\n")

                # Details für jede fehlende Schriftart
                for font_name in sorted(self.missing_fonts):
                    zeichen_list = self.missing_fonts_per_zeichen[font_name]

                    f.write(f"Schriftart: {font_name}\n")
                    f.write(f"Verwendet in {len(zeichen_list)} Zeichen:\n")

                    for zeichen_id in sorted(set(zeichen_list)):
                        f.write(f"  - {zeichen_id}\n")

                    f.write("\n")

                f.write("=" * 70 + "\n\n")

                f.write("EMPFEHLUNG\n")
                f.write("-" * 70 + "\n\n")
                f.write("1. Kopieren Sie den Schriftarten-Namen aus der Liste oben\n")
                f.write("2. Suchen Sie die Schriftart im Internet (z.B. Google Fonts, DaFont)\n")
                f.write("3. Installieren Sie die Schriftart auf Ihrem PC\n")
                f.write("4. Exportieren Sie die betroffenen Zeichen erneut\n\n")

                f.write("=" * 70 + "\n")

            self.logger.info(
                f"Bericht über fehlende Schriftarten erstellt: {output_file.name}"
            )
            return output_file

        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Berichts: {e}")
            return None

    def reset(self) -> None:
        """Setzt den Tracker zurück (für neuen Export)"""
        self.all_fonts_in_svgs.clear()
        self.fonts_per_zeichen.clear()
        self.missing_fonts.clear()
        self.missing_fonts_per_zeichen.clear()
        # Cache bleibt erhalten (muss nicht neu gebaut werden)
        self.logger.debug("MissingFontsTracker zurückgesetzt")
