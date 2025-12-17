#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
svg_loader_local.py - Lokaler SVG-Loader

Scannt lokalen Ordner nach SVG-Dateien und Kategorien (rekursiv)
Prueft SVG-Dateien auf verwendete Fonts

Version: 0.4.0 (Font-Pruefung implementiert)
"""

from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import logging
import re
import xml.etree.ElementTree as ET
import os
from datetime import datetime

from constants import (
    DEFAULT_ZEICHEN_DIR,
    ALLOWED_SVG_EXTENSIONS,
    MAX_PREVIEW_ITEMS,
    BLANKO_KATEGORIE_NAME,  # NEW: Blanko-Zeichen Support
    BLANKO_SVG_PATH,
    BLANKO_ZEICHEN_NAMEN,
    BLANKO_S1_LEER,  # CHANGED v0.8.2.3: S1-Blanko-Varianten
    BLANKO_S1_LINIEN,
    BLANKO_S1_LINIEN_STAERKE,
    BLANKO_S1_ZEICHEN_NAMEN,
    AVAILABLE_MODI
)


class SVGLoaderLocal:
    """
    Laedt SVG-Dateien aus lokalem Ordner (mit rekursivem Scanning)

    Ordnerstruktur (unterstuetzt Unterkategorien):
    Taktische_Zeichen_Grafikvorlagen/
    +-- Einheiten/
    |   +-- zeichen1.svg
    |   +-- zeichen2.svg
    +-- Formationen/
    |   +-- Gruppen/
    |   |   +-- gruppe1.svg
    |   +-- Trupps/
    |       +-- trupp1.svg
    +-- Fahrzeuge/
        +-- fahrzeug1.svg

    Kategorien mit Unterkategorien werden als "Formationen/Gruppen" zurueckgegeben
    """
    
    def __init__(self, zeichen_dir: Path = None):
        """
        Initialisiert lokalen SVG-Loader

        Args:
            zeichen_dir: Pfad zum Zeichen-Ordner (None = aus RuntimeConfig)
        """
        self.logger = logging.getLogger(__name__)

        # RuntimeConfig-Default laden falls nicht angegeben
        if zeichen_dir is None:
            from runtime_config import get_config
            zeichen_dir = get_config().zeichen_dir

        self.zeichen_dir = zeichen_dir

        # Pruefen ob Ordner existiert
        if not self.zeichen_dir.exists():
            self.logger.warning("Zeichen-Ordner nicht gefunden: {}".format(self.zeichen_dir))
            self.zeichen_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("Zeichen-Ordner erstellt: {}".format(self.zeichen_dir))

        self.logger.info("SVGLoaderLocal initialisiert: {}".format(self.zeichen_dir))
    
    def scan_categories(self, recursive: bool = True) -> List[str]:
        """
        Scannt Unterordner (= Kategorien) rekursiv

        NEW: Blanko-Kategorie wird IMMER als erste Kategorie zurückgegeben

        Args:
            recursive: Wenn True, werden Unterkategorien rekursiv gescannt

        Returns:
            Liste von Kategorie-Pfaden (z.B. ["Blanko-Zeichen", "Einheiten", "Formationen/Gruppen"])
        """
        categories = []

        try:
            if recursive:
                # Rekursiv alle Unterordner finden
                categories = self._scan_categories_recursive(self.zeichen_dir, "")
            else:
                # Nur erste Ebene scannen (alte Funktionalitaet)
                for item in self.zeichen_dir.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        categories.append(item.name)

            categories.sort()  # Alphabetisch sortieren

            # NEW: Blanko-Kategorie an erster Stelle einfügen
            categories.insert(0, BLANKO_KATEGORIE_NAME)

            self.logger.info("Kategorien gefunden: {} (inkl. Blanko-Zeichen)".format(len(categories)))
            for cat in categories:
                self.logger.debug("  - {}".format(cat))

            return categories

        except Exception as e:
            self.logger.error("Fehler beim Scannen der Kategorien: {}".format(e))
            return []

    def _scan_categories_recursive(self, current_dir: Path, rel_path: str) -> List[str]:
        """
        Hilfsfunktion: Scannt Ordner rekursiv nach Kategorien

        Args:
            current_dir: Aktueller Ordner
            rel_path: Relativer Pfad vom Zeichen-Ordner

        Returns:
            Liste von Kategorie-Pfaden
        """
        categories = []
        has_svg_files = False

        # Pruefen ob SVG-Dateien im aktuellen Ordner
        for item in current_dir.iterdir():
            if item.is_file() and item.suffix.lower() in ALLOWED_SVG_EXTENSIONS:
                has_svg_files = True
                break

        # Wenn SVGs vorhanden, ist dies eine Kategorie
        # FIXED: Auch Grundverzeichnis (rel_path = "") als Kategorie erkennen
        if has_svg_files:
            # Grundverzeichnis als "(Root)" anzeigen, damit es sichtbar ist
            category_name = rel_path if rel_path else "(Root)"
            categories.append(category_name)

        # Rekursiv alle Unterordner durchsuchen
        for item in current_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Neuen relativen Pfad berechnen
                new_rel_path = rel_path + "/" + item.name if rel_path else item.name
                # Rekursiv weiterscannen
                sub_categories = self._scan_categories_recursive(item, new_rel_path)
                categories.extend(sub_categories)

        return categories
    
    def get_svgs_in_category(self, category: str) -> List[Path]:
        """
        Gibt alle SVG-Dateien in einer Kategorie zurueck

        NEW: Für Blanko-Kategorie werden virtuelle Pfade zurückgegeben (eines pro Modus)

        Args:
            category: Kategorie-Pfad (z.B. "Einheiten" oder "Formationen/Gruppen")

        Returns:
            Liste von SVG-Datei-Pfaden (oder virtuelle Pfade für Blanko-Zeichen)
        """
        # NEW: Blanko-Kategorie behandeln
        if category == BLANKO_KATEGORIE_NAME:
            # CHANGED v0.8.2.3: Standard-Blanko (7 pro Modus) + S1-Blanko (3 fixe Varianten)
            blanko_paths = []

            # Standard Blanko-Zeichen (S2 oder normale Modi - eines pro Modus)
            for modus in AVAILABLE_MODI:
                # Virtueller Pfad: BLANKO_<modus>
                virtual_path = Path("{}_{}".format(BLANKO_SVG_PATH, modus))
                blanko_paths.append(virtual_path)

            # S1-Blanko-Zeichen (3 fixe Varianten)
            blanko_paths.extend([
                Path(BLANKO_S1_LEER),
                Path(BLANKO_S1_LINIEN),
                Path(BLANKO_S1_LINIEN_STAERKE)
            ])

            self.logger.info("Blanko-Zeichen generiert: {} Standard + {} S1 = {} Varianten".format(
                len(AVAILABLE_MODI), 3, len(blanko_paths)))
            return blanko_paths

        # FIXED: Grundverzeichnis "(Root)" behandeln
        if category == "(Root)":
            category_path = self.zeichen_dir
        else:
            # Kategorie-Pfad zusammensetzen (mit / fuer Unterkategorien)
            category_path = self.zeichen_dir / category.replace('/', '\\' if '\\' in str(self.zeichen_dir) else '/')

        if not category_path.exists():
            self.logger.warning("Kategorie nicht gefunden: {}".format(category))
            return []

        svg_files = []

        try:
            # Alle SVG-Dateien in Kategorie finden
            for file in category_path.iterdir():
                if file.is_file() and file.suffix.lower() in ALLOWED_SVG_EXTENSIONS:
                    svg_files.append(file)

            svg_files.sort()  # Alphabetisch sortieren

            self.logger.info("SVGs in '{}': {}".format(category, len(svg_files)))

            return svg_files

        except Exception as e:
            self.logger.error("Fehler beim Scannen der SVGs in '{}': {}".format(category, e))
            return []

    @staticmethod
    def is_blanko_zeichen(svg_path: Path) -> bool:
        """
        Prüft, ob ein Pfad ein Blanko-Zeichen ist

        CHANGED v0.8.2.3: Prüft auf Standard-Blanko + 3 S1-Blanko-Varianten

        Args:
            svg_path: Pfad zur SVG-Datei (oder virtueller Pfad)

        Returns:
            True wenn Blanko-Zeichen, sonst False
        """
        stem = str(svg_path.stem)
        # Standard-Blanko: BLANKO__modus
        # S1-Blanko: BLANKO_S1_LEER, BLANKO_S1_LINIEN, BLANKO_S1_LINIEN_STAERKE
        return (stem.startswith(BLANKO_SVG_PATH) or
                stem == BLANKO_S1_LEER or
                stem == BLANKO_S1_LINIEN or
                stem == BLANKO_S1_LINIEN_STAERKE)

    @staticmethod
    def is_blanko_s1_both(svg_path: Path) -> bool:
        """
        Prüft, ob ein Pfad ein S1-Blanko mit beidseitigen Schreiblinien ist

        CHANGED v0.8.2.3: Prüft auf BLANKO_S1_LINIEN und BLANKO_S1_LINIEN_STAERKE

        Args:
            svg_path: Pfad zur SVG-Datei (oder virtueller Pfad)

        Returns:
            True wenn S1-Blanko mit beidseitigen Linien, sonst False
        """
        stem = str(svg_path.stem)
        return (stem == BLANKO_S1_LINIEN or
                stem == BLANKO_S1_LINIEN_STAERKE)

    @staticmethod
    def has_staerke_anzeige(svg_path: Path) -> bool:
        """
        Prüft, ob ein Blanko-Zeichen die Stärkeangabe anzeigen soll

        NEW v0.8.2.2: Speziell für die 3 S1-Blanko-Varianten

        Args:
            svg_path: Pfad zur SVG-Datei (oder virtueller Pfad)

        Returns:
            True wenn Stärkeangabe angezeigt werden soll, sonst False
        """
        stem = str(svg_path.stem)
        return stem == BLANKO_S1_LINIEN_STAERKE

    @staticmethod
    def get_blanko_modus(svg_path: Path) -> Optional[str]:
        """
        Extrahiert den Modus aus einem Blanko-Zeichen-Pfad

        CHANGED v0.8.2.3: S1-Blanko haben keinen Modus, nur Standard-Blanko

        Args:
            svg_path: Virtueller Blanko-Pfad (z.B. Path("BLANKO_freitext"))

        Returns:
            Modus-String (z.B. "freitext") oder None für S1-Blanko
        """
        if not SVGLoaderLocal.is_blanko_zeichen(svg_path):
            return None

        stem = svg_path.stem

        # S1-Blanko-Zeichen haben keinen Modus
        if (stem == BLANKO_S1_LEER or
            stem == BLANKO_S1_LINIEN or
            stem == BLANKO_S1_LINIEN_STAERKE):
            return None

        # Format: BLANKO_<modus> (mit einfachem Unterstrich)
        if stem.startswith(BLANKO_SVG_PATH):
            parts = stem.split('_', 1)
            if len(parts) == 2:
                return parts[1]

        return None

    @staticmethod
    def get_blanko_display_name(svg_path: Path) -> str:
        """
        Gibt den Anzeigenamen für ein Blanko-Zeichen zurück

        CHANGED v0.8.2.3: Standard-Blanko (7) + S1-Blanko (3)

        Args:
            svg_path: Virtueller Blanko-Pfad

        Returns:
            Anzeigename (z.B. "Blanko - Freitext", "S1-Blanko nur Schreiblinien", etc.)
        """
        stem = str(svg_path.stem)

        # S1-Blanko-Varianten (3 fixe)
        if stem in BLANKO_S1_ZEICHEN_NAMEN:
            return BLANKO_S1_ZEICHEN_NAMEN[stem]

        # Standard-Blanko-Zeichen (pro Modus)
        modus = SVGLoaderLocal.get_blanko_modus(svg_path)
        if modus and modus in BLANKO_ZEICHEN_NAMEN:
            return BLANKO_ZEICHEN_NAMEN[modus]

        return svg_path.stem  # Fallback

    def get_all_svgs(self, selected_categories: Optional[List[str]] = None) -> Dict[str, List[Path]]:
        """
        Gibt alle SVGs aus gewaehlten Kategorien zurueck
        
        Args:
            selected_categories: Liste von Kategorien (None = alle)
            
        Returns:
            Dict: {kategorie: [svg_pfade]}
        """
        result = {}
        
        # Alle Kategorien holen, falls keine gewaehlt
        if selected_categories is None:
            selected_categories = self.scan_categories()
        
        # SVGs pro Kategorie laden
        for category in selected_categories:
            svgs = self.get_svgs_in_category(category)
            if svgs:
                result[category] = svgs
        
        total_svgs = sum(len(svgs) for svgs in result.values())
        self.logger.info("Gesamt: {} SVGs in {} Kategorien".format(total_svgs, len(result)))

        return result

    def scan_all_fast(self) -> Dict[str, List[Path]]:
        """
        Scannt ALLE Kategorien und SVGs in einem einzigen Durchlauf

        Nutzt os.walk() fuer maximale Performance.

        Returns:
            Dict: {kategorie: [svg_paths]} - Alle Kategorien mit ihren SVG-Dateien
        """
        start_time = datetime.now()
        categories = {}

        # os.walk() - ein einziger Durchlauf durch gesamte Verzeichnisstruktur
        for root, dirs, files in os.walk(str(self.zeichen_dir)):
            # Versteckte Ordner ueberspringen
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            # SVG-Dateien filtern (Case-insensitive)
            svg_files = [
                f for f in files
                if any(f.lower().endswith(ext) for ext in ALLOWED_SVG_EXTENSIONS)
            ]

            if svg_files:
                # Relativen Pfad als Kategorie
                try:
                    rel_path = Path(root).relative_to(self.zeichen_dir)
                    category = str(rel_path).replace('\\', '/')
                    if category == '.':
                        category = '(Root)'
                except ValueError:
                    # Falls Pfad nicht relativ ist, Ordnernamen verwenden
                    category = Path(root).name

                # SVG-Pfade erstellen (alphabetisch sortiert)
                categories[category] = sorted([
                    Path(root) / f for f in svg_files
                ])

                # Logging pro Kategorie
                self.logger.info("SVGs in '{}': {}".format(category, len(svg_files)))

        # Blanko-Kategorie hinzufügen
        # CHANGED v0.8.2.3: Standard-Blanko (7) + S1-Blanko (3) = 10 Varianten
        blanko_paths = []

        # Standard Blanko-Zeichen (S2 oder normale Modi - eines pro Modus)
        for modus in AVAILABLE_MODI:
            # Virtueller Pfad: BLANKO_<modus>
            virtual_path = Path("{}_{}".format(BLANKO_SVG_PATH, modus))
            blanko_paths.append(virtual_path)

        # S1-Blanko-Zeichen (3 fixe Varianten)
        blanko_paths.extend([
            Path(BLANKO_S1_LEER),
            Path(BLANKO_S1_LINIEN),
            Path(BLANKO_S1_LINIEN_STAERKE)
        ])

        categories[BLANKO_KATEGORIE_NAME] = blanko_paths
        self.logger.info("Blanko-Zeichen generiert: {} Standard + {} S1 = {} Varianten".format(
            len(AVAILABLE_MODI), 3, len(blanko_paths)))

        # Zeitmessung
        elapsed = (datetime.now() - start_time).total_seconds()
        total_svgs = sum(len(svgs) for svgs in categories.values())
        self.logger.info("Kategorien gescannt: {} mit {} SVGs in {:.2f}s".format(
            len(categories), total_svgs, elapsed
        ))

        return categories

    def get_svg_info(self, svg_path: Path) -> dict:
        """
        Gibt Informationen zu einer SVG-Datei zurueck

        Args:
            svg_path: Pfad zur SVG-Datei

        Returns:
            Dict mit SVG-Infos
        """
        if not svg_path.exists():
            return {}

        # Kategorie ermitteln (vollstaendiger relativer Pfad vom Zeichen-Ordner)
        try:
            rel_path = svg_path.parent.relative_to(self.zeichen_dir)
            category = str(rel_path).replace('\\', '/')
        except ValueError:
            # Falls der Pfad nicht relativ zum Zeichen-Ordner ist
            category = svg_path.parent.name

        return {
            "filename": svg_path.name,
            "stem": svg_path.stem,  # Ohne .svg
            "category": category,
            "path": svg_path,
            "size_bytes": svg_path.stat().st_size,
            "exists": True
        }
    
    def validate_svg(self, svg_path: Path) -> bool:
        """
        Prueft ob SVG-Datei gueltig ist
        
        Args:
            svg_path: Pfad zur SVG-Datei
            
        Returns:
            True wenn gueltig
        """
        if not svg_path.exists():
            self.logger.error("SVG existiert nicht: {}".format(svg_path))
            return False
        
        if not svg_path.is_file():
            self.logger.error("Kein File: {}".format(svg_path))
            return False
        
        if svg_path.suffix.lower() not in ALLOWED_SVG_EXTENSIONS:
            self.logger.error("Falsche Endung: {}".format(svg_path))
            return False
        
        # Datei darf nicht leer sein
        if svg_path.stat().st_size == 0:
            self.logger.error("SVG ist leer: {}".format(svg_path))
            return False
        
        # Inhalt pruefen (muss mit < beginnen)
        try:
            content = svg_path.read_text(encoding='utf-8')
            if not content.strip().startswith('<'):
                self.logger.error("Kein gueltiges SVG (startet nicht mit <): {}".format(svg_path))
                return False
        except Exception as e:
            self.logger.error("Fehler beim Lesen der SVG: {}".format(e))
            return False
        
        return True

    def check_svg_fonts(self, svg_path: Path) -> Tuple[bool, Set[str]]:
        """
        Prueft SVG-Datei auf verwendete Fonts

        Args:
            svg_path: Pfad zur SVG-Datei

        Returns:
            Tuple: (hat_text_elemente, set_von_font_families)
        """
        if not svg_path.exists():
            self.logger.error("SVG existiert nicht: {}".format(svg_path))
            return (False, set())

        try:
            # SVG-Datei parsen
            tree = ET.parse(str(svg_path))
            root = tree.getroot()

            # Namespace fuer SVG
            namespaces = {
                'svg': 'http://www.w3.org/2000/svg',
                '': 'http://www.w3.org/2000/svg'
            }

            fonts = set()
            has_text = False

            # Suche nach <text> und <tspan> Elementen
            # Mit und ohne Namespace
            for text_elem in root.iter():
                tag_name = text_elem.tag.split('}')[-1] if '}' in text_elem.tag else text_elem.tag

                if tag_name in ['text', 'tspan']:
                    has_text = True

                    # Font-family aus style Attribut extrahieren
                    style = text_elem.get('style', '')
                    if 'font-family' in style:
                        # Format: "font-family:Arial" oder "font-family: Arial, sans-serif"
                        match = re.search(r'font-family:\s*([^;]+)', style)
                        if match:
                            font_str = match.group(1).strip()
                            # Mehrere Fonts durch Komma getrennt
                            for font in font_str.split(','):
                                font = font.strip().strip('"').strip("'")
                                if font:
                                    fonts.add(font)

                    # Font-family als direktes Attribut
                    font_family = text_elem.get('font-family', '')
                    if font_family:
                        for font in font_family.split(','):
                            font = font.strip().strip('"').strip("'")
                            if font:
                                fonts.add(font)

            return (has_text, fonts)

        except ET.ParseError as e:
            self.logger.warning("SVG Parse-Fehler in {}: {}".format(svg_path.name, e))
            return (False, set())
        except Exception as e:
            self.logger.error("Fehler beim Font-Check {}: {}".format(svg_path.name, e))
            return (False, set())

    def scan_fonts_in_category(self, category: str) -> Dict[str, Set[str]]:
        """
        Scannt alle SVGs in einer Kategorie nach verwendeten Fonts

        Args:
            category: Kategorie-Pfad

        Returns:
            Dict: {font_name: set(svg_filenames)}
        """
        svg_files = self.get_svgs_in_category(category)
        font_usage = {}  # font -> set(files)

        for svg_path in svg_files:
            has_text, fonts = self.check_svg_fonts(svg_path)
            if has_text and fonts:
                for font in fonts:
                    if font not in font_usage:
                        font_usage[font] = set()
                    font_usage[font].add(svg_path.name)

        return font_usage

    def scan_all_fonts(self, selected_categories: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Scannt alle SVGs nach verwendeten Fonts

        Args:
            selected_categories: Liste von Kategorien (None = alle)

        Returns:
            Dict: {font_name: anzahl_verwendungen}
        """
        if selected_categories is None:
            selected_categories = self.scan_categories()

        font_usage = {}  # font -> count

        for category in selected_categories:
            self.logger.debug("Scanne Fonts in Kategorie: {}".format(category))
            svg_files = self.get_svgs_in_category(category)

            for svg_path in svg_files:
                has_text, fonts = self.check_svg_fonts(svg_path)
                if has_text and fonts:
                    for font in fonts:
                        font_usage[font] = font_usage.get(font, 0) + 1

        total_fonts = len(font_usage)
        total_usages = sum(font_usage.values())
        self.logger.info("Font-Scan: {} verschiedene Fonts, {} Verwendungen".format(
            total_fonts, total_usages
        ))

        return font_usage


# REMOVED: scan_zeichen_directory() - ungenutzte Convenience-Funktion (siehe cleanup)


# ================================================================================================
# TEST
# ================================================================================================

if __name__ == "__main__":
    # CHANGED: LoggingManager importieren
    from logging_manager import LoggingManager
    
    # Logging fuer Test
    logging_mgr = LoggingManager(log_level="DEBUG", log_to_console=True)
    
    print("=" * 80)
    print("SVG-LOADER LOCAL - TEST (v2.2 mit LoggingManager)")
    print("=" * 80)
    
    loader = SVGLoaderLocal()
    
    print("\nZeichen-Ordner: {}".format(loader.zeichen_dir))
    print("Existiert: {}".format(loader.zeichen_dir.exists()))
    
    # Kategorien scannen
    print("\n[KATEGORIEN SCANNEN]")
    print("-" * 80)
    categories = loader.scan_categories()
    
    if categories:
        print("Gefunden: {} Kategorien".format(len(categories)))
        for cat in categories:
            print("  - {}".format(cat))
    else:
        print("Keine Kategorien gefunden!")
        print("\nHinweis: Erstelle Test-Struktur:")
        print("  Taktische_Zeichen/")
        print("  +-- Test_Kategorie/")
        print("  |   +-- test.svg")
    
    # SVGs in Kategorien scannen
    if categories:
        print("\n[SVGs PRO KATEGORIE]")
        print("-" * 80)
        all_svgs = loader.get_all_svgs()
        
        for cat, svgs in all_svgs.items():
            print("\n{}: {} SVGs".format(cat, len(svgs)))
            for svg in svgs[:MAX_PREVIEW_ITEMS]:
                info = loader.get_svg_info(svg)
                valid = loader.validate_svg(svg)
                status = "[OK]" if valid else "[FEHLER]"
                print("  {} {} ({} Bytes)".format(status, info['filename'], info['size_bytes']))
            
            if len(svgs) > MAX_PREVIEW_ITEMS:
                print("  ... und {} weitere".format(len(svgs) - MAX_PREVIEW_ITEMS))
    
    # Font-Scan Test
    if categories:
        print("\n[FONT-SCAN TEST]")
        print("-" * 80)
        print("Scanne alle Kategorien nach verwendeten Fonts...")

        font_usage = loader.scan_all_fonts()

        if font_usage:
            print("\nGefundene Fonts ({} verschiedene):".format(len(font_usage)))
            # Nach Haeufigkeit sortieren
            sorted_fonts = sorted(font_usage.items(), key=lambda x: x[1], reverse=True)
            for font, count in sorted_fonts[:10]:  # Top 10
                print("  - {} ({} Verwendungen)".format(font, count))

            if len(font_usage) > 10:
                print("  ... und {} weitere Fonts".format(len(font_usage) - 10))
        else:
            print("\nKeine Fonts in SVGs gefunden (alle SVGs ohne Text)")

    print("\n" + "=" * 80)
    print("[OK] Test abgeschlossen!")
    print("=" * 80)
