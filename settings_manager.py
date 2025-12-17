#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
settings_manager.py - Einstellungs-Verwaltung

Speichert und laedt Programm-Einstellungen
Verwendet JSON-Datei im Programm-Verzeichnis
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

from logging_manager import LoggingManager
from constants import (
    DEFAULT_ZEICHEN_HOEHE_MM,
    DEFAULT_ZEICHEN_BREITE_MM,
    DEFAULT_ABSTAND_GRAFIK_TEXT_MM,
    DEFAULT_TEXT_BOTTOM_OFFSET_MM,
    DEFAULT_BESCHNITTZUGABE_MM,
    DEFAULT_SICHERHEITSABSTAND_MM,
    DEFAULT_EXPORT_DPI,
    DEFAULT_MINIMUM_DPI_FOR_PRINT,
    DEFAULT_MODUS,
    DEFAULT_FONT_SIZE,
    DEFAULT_FONT_FAMILY,
    DEFAULT_AUTO_ADJUST_GRAFIK_SIZE,
    DEFAULT_AUTO_ADJUST_FONT_SIZE,
    DEFAULT_ASPECT_LOCKED,
    DEFAULT_GRAFIK_POSITION,
    DEFAULT_STANDARD_LAYOUT,
    DEFAULT_STANDARD_EXPORT_FORMAT,
    DEFAULT_PDF_MARGIN_HORIZONTAL_MM,
    DEFAULT_PDF_MARGIN_VERTICAL_MM,
    DEFAULT_S1_ZEICHEN_HOEHE_MM,
    DEFAULT_S1_ZEICHEN_BREITE_MM,
    DEFAULT_S1_BESCHNITTZUGABE_MM,
    DEFAULT_S1_SICHERHEITSABSTAND_MM,
    DEFAULT_S1_ASPECT_LOCKED,
    DEFAULT_S1_LINKS_PROZENT,
    DEFAULT_S1_ANZAHL_SCHREIBLINIEN,
    DEFAULT_S1_STAERKE_ANZEIGEN,
)


@dataclass
class ZeichenSettings:
    """
    Einstellungen fuer Zeichen-Generierung

    Attributes:
        zeichen_hoehe_mm: Hoehe des fertigen Zeichens in mm
        zeichen_breite_mm: Breite des fertigen Zeichens in mm
        abstand_grafik_text_mm: Abstand zwischen Grafik (unten) und Text (oben) in mm
        text_bottom_offset_mm: Abstand zwischen Text (unten) und Sicherheitsrand in mm
        beschnittzugabe_mm: Zusätzlicher Rand für Druck (wird abgeschnitten)
        sicherheitsabstand_mm: Abstand Grafik/Text zum Rand des fertigen Zeichens
        export_dpi: Standard-DPI für Export-Dialog (vorausgewählt beim Öffnen)
        minimum_dpi_for_print: Mindest-DPI für Druckqualität (Druckerei-Anforderung)
        standard_modus: Standard-Modus fuer neue Zeichen
        font_size: Schriftgroesse in Punkten (NEW v7.3)
        font_family: Schriftart (NEW v7.3)
        auto_adjust_grafik_size: Grafikgröße automatisch anpassen bei Zeichengröße-Änderung (NEW)
        auto_adjust_font_size: Schriftgröße automatisch anpassen bei Zeichengröße-Änderung (NEW)
        aspect_locked: Seitenverhältnis 1:1 fixieren (True = Breite = Höhe) (NEW v0.8.2.4)

    Note:
        schnittlinien_anzeigen wurde in v7.1 entfernt - Checkbox ist jetzt im Export-Dialog
    """
    zeichen_hoehe_mm: float = DEFAULT_ZEICHEN_HOEHE_MM
    zeichen_breite_mm: float = DEFAULT_ZEICHEN_BREITE_MM
    abstand_grafik_text_mm: float = DEFAULT_ABSTAND_GRAFIK_TEXT_MM
    text_bottom_offset_mm: float = DEFAULT_TEXT_BOTTOM_OFFSET_MM
    beschnittzugabe_mm: float = DEFAULT_BESCHNITTZUGABE_MM
    sicherheitsabstand_mm: float = DEFAULT_SICHERHEITSABSTAND_MM
    # schnittlinien_anzeigen wurde entfernt (v7.1) - jetzt im Export-Dialog
    export_dpi: int = DEFAULT_EXPORT_DPI
    minimum_dpi_for_print: int = DEFAULT_MINIMUM_DPI_FOR_PRINT
    standard_modus: str = DEFAULT_MODUS
    font_size: int = DEFAULT_FONT_SIZE
    font_family: str = DEFAULT_FONT_FAMILY
    auto_adjust_grafik_size: bool = DEFAULT_AUTO_ADJUST_GRAFIK_SIZE
    auto_adjust_font_size: bool = DEFAULT_AUTO_ADJUST_FONT_SIZE
    aspect_locked: bool = DEFAULT_ASPECT_LOCKED


@dataclass
class GrafikSettings:
    """
    Einstellungen fuer Grafik-Groesse (v7.1: Gilt für ALLE Modi)

    Attributes:
        max_hoehe_mm: Grafik-Hoehe in mm (wird bei Start auf Maximum gesetzt)
        max_breite_mm: Grafik-Breite in mm (wird bei Start auf Maximum gesetzt)
        position: Position der Grafik im Modus "Nur Grafik" (oben/mittig/unten)

    Note:
        - In Modus "Nur Grafik": Diese Werte sind die tatsächliche Grafikgröße
        - In anderen Modi: Diese Werte sind Grundlage für Berechnungen
        - Wird automatisch auf Maximum gesetzt wenn Zeichengröße sich ändert
    """
    max_hoehe_mm: float = 39.0  # Default fuer 45mm Zeichen (45 - 2x3mm)
    max_breite_mm: float = 39.0
    position: str = DEFAULT_GRAFIK_POSITION


@dataclass
class S1Settings:
    """
    Einstellungen fuer S1-Layout (Doppelschild)

    Das S1-Layout ist ein rechteckiges Zeichen (Breite = 2 x Hoehe) mit zwei Bereichen:
    - Links: Grafik + Freitext (wie S2-Layout)
    - Rechts: Schreiblinien + optionaler Staerke-Platzhalter

    Attributes:
        zeichen_hoehe_mm: Hoehe des fertigen S1-Zeichens in mm
        zeichen_breite_mm: Breite des fertigen S1-Zeichens in mm
        beschnittzugabe_mm: Beschnittzugabe fuer S1 in mm
        sicherheitsabstand_mm: Sicherheitsabstand fuer S1 in mm
        aspect_locked: Seitenverhaeltnis 2:1 fixieren (True = Breite = 2 x Hoehe)
        links_prozent: Aufteilung Links/Rechts in Prozent (Standard: 40/60)
        anzahl_schreiblinien: Anzahl gewuenschter Schreiblinien (3-10, Zeilenh\u00f6he wird berechnet)
        staerke_anzeigen: Staerke-Platzhalter in erster Zeile anzeigen
        font_size: Schriftgroesse in Punkten (NEW v0.8.2.3)
        font_family: Schriftart (NEW v0.8.2.3)
        auto_adjust_font_size: Schriftgröße automatisch anpassen bei Zeichengröße-Änderung (NEW v0.8.2.2)

    Note:
        - Blanko-Modus wird NICHT hier gespeichert (laeuft ueber TreeView)
        - S1 hat jetzt eigene Zeichenabmessungen (getrennt von S2/ZeichenSettings)
        - S1 hat jetzt eigene auto_adjust_font_size und font_size (getrennt von S2)
    """
    zeichen_hoehe_mm: float = DEFAULT_S1_ZEICHEN_HOEHE_MM
    zeichen_breite_mm: float = DEFAULT_S1_ZEICHEN_BREITE_MM
    beschnittzugabe_mm: float = DEFAULT_S1_BESCHNITTZUGABE_MM
    sicherheitsabstand_mm: float = DEFAULT_S1_SICHERHEITSABSTAND_MM
    aspect_locked: bool = DEFAULT_S1_ASPECT_LOCKED
    links_prozent: int = DEFAULT_S1_LINKS_PROZENT
    anzahl_schreiblinien: int = DEFAULT_S1_ANZAHL_SCHREIBLINIEN
    staerke_anzeigen: bool = DEFAULT_S1_STAERKE_ANZEIGEN
    font_size: int = DEFAULT_FONT_SIZE
    font_family: str = DEFAULT_FONT_FAMILY
    auto_adjust_font_size: bool = DEFAULT_AUTO_ADJUST_FONT_SIZE


@dataclass
class AppSettings:
    """
    Alle Programm-Einstellungen

    Attributes:
        zeichen_ordner: Pfad zum Zeichen-Ordner
        zeichen: Zeichen-Einstellungen
        grafik: Grafik-Einstellungen
        s1: S1-Layout-Einstellungen (NEW v0.9)
        log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        standard_layout: Standard-Layout beim Start (S1 oder S2) (NEW v0.8.2)
        standard_export_format: Standard-Exportformat (PNG, PDF_SINGLE, PDF_SHEET) (NEW v0.8.2)
        pdf_margin_horizontal_mm: Horizontale Seitenränder für PDF-Schnittbögen in mm (NEW v0.8.2)
        pdf_margin_vertical_mm: Vertikale Seitenränder für PDF-Schnittbögen in mm (NEW v0.8.2)
    """
    zeichen_ordner: str = "Taktische_Zeichen_Grafikvorlagen"
    zeichen: ZeichenSettings = None
    grafik: GrafikSettings = None
    s1: S1Settings = None  # NEW: S1-Layout Einstellungen
    log_level: str = "INFO"  # Default: INFO (nicht DEBUG!)
    standard_layout: str = DEFAULT_STANDARD_LAYOUT
    standard_export_format: str = DEFAULT_STANDARD_EXPORT_FORMAT
    pdf_margin_horizontal_mm: float = DEFAULT_PDF_MARGIN_HORIZONTAL_MM
    pdf_margin_vertical_mm: float = DEFAULT_PDF_MARGIN_VERTICAL_MM

    def __post_init__(self):
        """Initialisiert Unter-Settings falls nicht gesetzt"""
        if self.zeichen is None:
            self.zeichen = ZeichenSettings()
        if self.grafik is None:
            self.grafik = GrafikSettings()
        if self.s1 is None:  # NEW
            self.s1 = S1Settings()


class SettingsManager:
    """
    Verwaltet Programm-Einstellungen

    Features:
    - Laden/Speichern als JSON
    - Default-Werte
    - Validierung
    - Auto-Save Option

    Example:
        settings_mgr = SettingsManager()
        settings = settings_mgr.load_settings()

        # Werte aendern
        settings.zeichen.zeichen_hoehe_mm = 50.0

        # Speichern
        settings_mgr.save_settings(settings)
    """

    def __init__(self, settings_file: Optional[Path] = None):
        """
        Initialisiert Settings-Manager

        Args:
            settings_file: Pfad zur Settings-Datei (default: settings.json im Programmverzeichnis)
        """
        self.logger = LoggingManager().get_logger(__name__)

        if settings_file is None:
            # Default: settings.json im Programmverzeichnis
            self.settings_file = Path(__file__).parent / "settings.json"
        else:
            self.settings_file = settings_file

        self.logger.info(f"SettingsManager initialisiert: {self.settings_file}")

    def load_settings(self) -> AppSettings:
        """
        Laedt Einstellungen aus Datei

        Returns:
            AppSettings: Geladene Einstellungen (oder Defaults falls Datei nicht existiert)
        """
        if not self.settings_file.exists():
            self.logger.info("Settings-Datei nicht gefunden, verwende Defaults")
            return AppSettings()

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # JSON -> Dataclasses
            zeichen_data = data.get('zeichen', {})
            grafik_data = data.get('grafik', {})
            s1_data = data.get('s1', {})  # NEW: S1-Settings laden

            settings = AppSettings(
                zeichen_ordner=data.get('zeichen_ordner', 'Taktische_Zeichen_Grafikvorlagen'),
                zeichen=ZeichenSettings(**zeichen_data),
                grafik=GrafikSettings(**grafik_data),
                s1=S1Settings(**s1_data),  # NEW: S1-Settings
                log_level=data.get('log_level', 'INFO'),  # BUGFIX v0.8.2: Log-Level laden
                standard_layout=data.get('standard_layout', 'S2'),  # NEW v0.8.2
                standard_export_format=data.get('standard_export_format', 'PNG'),  # NEW v0.8.2
                pdf_margin_horizontal_mm=data.get('pdf_margin_horizontal_mm', 10.0),  # NEW v0.8.2
                pdf_margin_vertical_mm=data.get('pdf_margin_vertical_mm', 10.0)  # NEW v0.8.2
            )

            self.logger.info("Settings erfolgreich geladen")
            return settings

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Settings: {e}")
            self.logger.info("Verwende Default-Settings")
            return AppSettings()

    def save_settings(self, settings: AppSettings) -> bool:
        """
        Speichert Einstellungen in Datei

        Args:
            settings: Zu speichernde Einstellungen

        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            # Dataclasses -> JSON
            data = {
                'zeichen_ordner': settings.zeichen_ordner,
                'zeichen': asdict(settings.zeichen),
                'grafik': asdict(settings.grafik),
                's1': asdict(settings.s1),  # NEW: S1-Settings speichern
                'log_level': settings.log_level,  # BUGFIX v0.8.2: Log-Level speichern
                'standard_layout': settings.standard_layout,  # NEW v0.8.2
                'standard_export_format': settings.standard_export_format,  # NEW v0.8.2
                'pdf_margin_horizontal_mm': settings.pdf_margin_horizontal_mm,  # NEW v0.8.2
                'pdf_margin_vertical_mm': settings.pdf_margin_vertical_mm  # NEW v0.8.2
            }

            # JSON speichern (formatiert fuer Lesbarkeit)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self.logger.info("Settings erfolgreich gespeichert")
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Settings: {e}")
            return False

    def get_default_settings(self) -> AppSettings:
        """
        Gibt Default-Einstellungen zurueck

        Returns:
            AppSettings: Default-Einstellungen
        """
        return AppSettings()

    def validate_settings(self, settings: AppSettings) -> bool:
        """
        Validiert Einstellungen

        Args:
            settings: Zu validierende Einstellungen

        Returns:
            bool: True wenn gueltig, False sonst
        """
        try:
            # Zeichen-Groesse validieren
            if settings.zeichen.zeichen_hoehe_mm <= 0:
                self.logger.error("Zeichen-Hoehe muss > 0 sein")
                return False

            if settings.zeichen.zeichen_breite_mm <= 0:
                self.logger.error("Zeichen-Breite muss > 0 sein")
                return False

            # Abstaende validieren
            if settings.zeichen.abstand_grafik_text_mm < 0:
                self.logger.error("Abstand Grafik-Text muss >= 0 sein")
                return False

            if settings.zeichen.beschnittzugabe_mm < 0:
                self.logger.error("Beschnittzugabe muss >= 0 sein")
                return False

            if settings.zeichen.sicherheitsabstand_mm < 0:
                self.logger.error("Sicherheitsabstand muss >= 0 sein")
                return False

            # DPI validieren
            if settings.zeichen.export_dpi < 72:
                self.logger.error("DPI muss >= 72 sein")
                return False

            # Grafik-Groesse validieren
            if settings.grafik.max_hoehe_mm <= 0:
                self.logger.error("Grafik-Hoehe muss > 0 sein")
                return False

            if settings.grafik.max_breite_mm <= 0:
                self.logger.error("Grafik-Breite muss > 0 sein")
                return False

            # Position validieren
            valid_positions = ['oben', 'mittig', 'unten']
            if settings.grafik.position not in valid_positions:
                self.logger.error(f"Grafik-Position muss eine von {valid_positions} sein")
                return False

            # Modus validieren
            valid_modi = ['ov_staerke', 'ruf', 'freitext', 'nur_grafik']
            if settings.zeichen.standard_modus not in valid_modi:
                self.logger.error(f"Standard-Modus muss einer von {valid_modi} sein")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Fehler bei Validierung: {e}")
            return False


# ================================================================================================
# TESTING
# ================================================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SETTINGS-MANAGER TEST")
    print("=" * 80)

    # Settings-Manager erstellen
    mgr = SettingsManager(Path("test_settings.json"))

    print("\n[TEST 1] Default-Settings")
    print("-" * 80)
    defaults = mgr.get_default_settings()
    print(f"Zeichen-Hoehe: {defaults.zeichen.zeichen_hoehe_mm} mm")
    print(f"Zeichen-Breite: {defaults.zeichen.zeichen_breite_mm} mm")
    print(f"Abstand Grafik-Text: {defaults.zeichen.abstand_grafik_text_mm} mm")
    print(f"Beschnittzugabe: {defaults.zeichen.beschnittzugabe_mm} mm")
    print(f"Sicherheitsabstand: {defaults.zeichen.sicherheitsabstand_mm} mm")
    print(f"DPI für Export: {defaults.zeichen.export_dpi}")
    print(f"Min. DPI für Druckerei: {defaults.zeichen.minimum_dpi_for_print}")
    print(f"Standard-Modus: {defaults.zeichen.standard_modus}")
    print(f"Grafik max. Hoehe: {defaults.grafik.max_hoehe_mm} mm")
    print(f"Grafik max. Breite: {defaults.grafik.max_breite_mm} mm")
    print(f"Grafik-Position: {defaults.grafik.position}")

    print("\n[TEST 2] Validierung")
    print("-" * 80)
    valid = mgr.validate_settings(defaults)
    print(f"Default-Settings gueltig: {valid}")

    # Invalide Settings testen
    invalid = AppSettings()
    invalid.zeichen.zeichen_hoehe_mm = -10  # Ungueltig
    valid = mgr.validate_settings(invalid)
    print(f"Invalide Settings erkannt: {not valid}")

    print("\n[TEST 3] Speichern")
    print("-" * 80)
    test_settings = AppSettings()
    test_settings.zeichen.zeichen_hoehe_mm = 50.0
    # test_settings.zeichen.schnittlinien_anzeigen = True  # v7.1: Entfernt

    success = mgr.save_settings(test_settings)
    print(f"Speichern erfolgreich: {success}")
    print(f"Datei existiert: {mgr.settings_file.exists()}")

    print("\n[TEST 4] Laden")
    print("-" * 80)
    loaded = mgr.load_settings()
    print(f"Zeichen-Hoehe: {loaded.zeichen.zeichen_hoehe_mm} mm (erwartet: 50.0)")
    # print(f"Schnittlinien: {loaded.zeichen.schnittlinien_anzeigen} (erwartet: True)")  # v7.1: Entfernt

    # Cleanup
    if mgr.settings_file.exists():
        mgr.settings_file.unlink()
        print(f"\nTest-Datei geloescht: {mgr.settings_file}")

    print("\n" + "=" * 80)
    print("[OK] Alle Tests abgeschlossen")
    print("=" * 80)
