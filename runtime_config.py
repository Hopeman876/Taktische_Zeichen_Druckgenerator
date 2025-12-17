#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
runtime_config.py - Runtime-Konfiguration (Singleton)

Verwaltet aktive Konfigurationswerte zur Laufzeit:
- Lädt Factory Defaults aus constants.py
- Überschreibt mit User-Settings aus settings.json
- Bietet globalen Zugriff auf alle konfigurierbaren Werte

Verwendung:
    from runtime_config import get_config

    config = get_config()
    modus = config.standard_modus
    font_size = config.font_size

    # Zur Laufzeit ändern
    config.font_size = 10
"""

from typing import Optional
from logging_manager import LoggingManager


class RuntimeConfig:
    """
    Singleton für Runtime-Konfiguration

    Verwaltet aktive Werte zur Laufzeit:
    1. Lädt Factory Defaults aus constants.py
    2. Überschreibt mit User-Settings (falls vorhanden)
    3. Bietet get/set-Interface für alle Werte

    Features:
    - Singleton-Pattern (nur eine Instanz)
    - Lazy Loading
    - User-Override-Tracking
    - Validierung bei set()
    """

    _instance: Optional['RuntimeConfig'] = None

    def __init__(self):
        """Private Init - Nutze get_instance() statt direkt zu instanziieren"""
        if RuntimeConfig._instance is not None:
            raise RuntimeError("Use RuntimeConfig.get_instance() instead")

        self.logger = LoggingManager().get_logger(__name__)

        # Factory Defaults laden
        self._load_factory_defaults()

        self.logger.debug("RuntimeConfig initialisiert mit Factory Defaults")

    @classmethod
    def get_instance(cls) -> 'RuntimeConfig':
        """
        Gibt Singleton-Instanz zurück (erstellt sie falls nötig)

        Returns:
            RuntimeConfig: Die einzige RuntimeConfig-Instanz
        """
        if cls._instance is None:
            cls._instance = RuntimeConfig()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """
        Setzt Singleton zurück (nur für Tests!)
        """
        cls._instance = None

    def _load_factory_defaults(self):
        """Lädt Factory Defaults aus constants.py"""
        # Lazy Import um zirkuläre Abhängigkeiten zu vermeiden
        from constants import (
            DEFAULT_MODUS,
            DEFAULT_FONT_SIZE,
            DEFAULT_FONT_FAMILY,
            DEFAULT_EXPORT_DPI,
            DEFAULT_MINIMUM_DPI_FOR_PRINT,
            DEFAULT_ZEICHEN_HOEHE_MM,
            DEFAULT_ZEICHEN_BREITE_MM,
            DEFAULT_BESCHNITTZUGABE_MM,
            DEFAULT_SICHERHEITSABSTAND_MM,
            DEFAULT_ABSTAND_GRAFIK_TEXT_MM,
            DEFAULT_TEXT_BOTTOM_OFFSET_MM,
            DEFAULT_OV_LENGTH,
            DEFAULT_RUF_LENGTH,
            DEFAULT_ORT_LENGTH,
            DEFAULT_FREITEXT_LENGTH,
            DEFAULT_STAERKE_DIGITS,
            DEFAULT_SCHNITTLINIEN,
            DEFAULT_ZEICHEN_DIR,  # NEW: Zeichen-Verzeichnis
            # NEW: S1-Layout Defaults
            DEFAULT_S1_ASPECT_LOCKED,
            DEFAULT_S1_LINKS_PROZENT,
            DEFAULT_S1_ANZAHL_SCHREIBLINIEN,
            DEFAULT_S1_STAERKE_ANZEIGEN,
            DEFAULT_S1_ZEICHEN_HOEHE_MM,
            DEFAULT_S1_ZEICHEN_BREITE_MM,
            DEFAULT_S1_BESCHNITTZUGABE_MM,
            DEFAULT_S1_SICHERHEITSABSTAND_MM
        )

        # Zeichen-Parameter
        self.zeichen_dir = DEFAULT_ZEICHEN_DIR  # NEW: Zeichen-Verzeichnis (Path)
        self.standard_modus: str = DEFAULT_MODUS
        self.font_size: int = DEFAULT_FONT_SIZE
        self.font_family: str = DEFAULT_FONT_FAMILY
        self.export_dpi: int = DEFAULT_EXPORT_DPI  # Standard-DPI für Export-Dialog
        self.minimum_dpi_for_print: int = DEFAULT_MINIMUM_DPI_FOR_PRINT

        # Abmessungen
        self.zeichen_hoehe_mm: float = DEFAULT_ZEICHEN_HOEHE_MM
        self.zeichen_breite_mm: float = DEFAULT_ZEICHEN_BREITE_MM

        # Druck-Parameter
        self.beschnittzugabe_mm: float = DEFAULT_BESCHNITTZUGABE_MM
        self.sicherheitsabstand_mm: float = DEFAULT_SICHERHEITSABSTAND_MM
        self.abstand_grafik_text_mm: float = DEFAULT_ABSTAND_GRAFIK_TEXT_MM
        self.text_bottom_offset_mm: float = DEFAULT_TEXT_BOTTOM_OFFSET_MM

        # Grafik-Größe (v7.1: Wird bei Start auf Maximum gesetzt)
        # Default: 45mm - (2 × 3mm) = 39mm
        self.grafik_hoehe_mm: float = DEFAULT_ZEICHEN_HOEHE_MM - (2 * DEFAULT_SICHERHEITSABSTAND_MM)
        self.grafik_breite_mm: float = DEFAULT_ZEICHEN_BREITE_MM - (2 * DEFAULT_SICHERHEITSABSTAND_MM)
        self.grafik_position: str = "mittig"  # Nur für Modus "Nur Grafik"

        # Platzhalter-Längen
        self.ov_length: int = DEFAULT_OV_LENGTH
        self.ruf_length: int = DEFAULT_RUF_LENGTH
        self.ort_length: int = DEFAULT_ORT_LENGTH
        self.freitext_length: int = DEFAULT_FREITEXT_LENGTH

        # Komplexe Defaults
        self.staerke_digits: list = DEFAULT_STAERKE_DIGITS.copy()

        # Flags
        self.schnittlinien_anzeigen: bool = DEFAULT_SCHNITTLINIEN

        # NEW: S1-Layout Parameter
        self.s1_zeichen_hoehe_mm: float = DEFAULT_S1_ZEICHEN_HOEHE_MM
        self.s1_zeichen_breite_mm: float = DEFAULT_S1_ZEICHEN_BREITE_MM
        self.s1_beschnittzugabe_mm: float = DEFAULT_S1_BESCHNITTZUGABE_MM
        self.s1_sicherheitsabstand_mm: float = DEFAULT_S1_SICHERHEITSABSTAND_MM
        self.s1_aspect_locked: bool = DEFAULT_S1_ASPECT_LOCKED
        self.s1_links_prozent: int = DEFAULT_S1_LINKS_PROZENT
        self.s1_anzahl_schreiblinien: int = DEFAULT_S1_ANZAHL_SCHREIBLINIEN
        self.s1_staerke_anzeigen: bool = DEFAULT_S1_STAERKE_ANZEIGEN

        self.logger.debug("Factory Defaults geladen")

    def load_from_settings(self, settings):
        """
        Überschreibt Defaults mit User-Settings

        Args:
            settings: AppSettings-Objekt aus SettingsManager
        """
        self.logger.info("Lade User-Settings in RuntimeConfig")

        try:
            # Zeichen-Settings
            if hasattr(settings, 'zeichen'):
                z = settings.zeichen
                self.standard_modus = getattr(z, 'standard_modus', self.standard_modus)
                self.zeichen_hoehe_mm = getattr(z, 'zeichen_hoehe_mm', self.zeichen_hoehe_mm)
                self.zeichen_breite_mm = getattr(z, 'zeichen_breite_mm', self.zeichen_breite_mm)
                self.abstand_grafik_text_mm = getattr(z, 'abstand_grafik_text_mm', self.abstand_grafik_text_mm)
                self.text_bottom_offset_mm = getattr(z, 'text_bottom_offset_mm', self.text_bottom_offset_mm)

                # Neue Parameter mit Fallback auf alte Namen
                self.beschnittzugabe_mm = getattr(z, 'beschnittzugabe_mm',
                                                  getattr(z, 'abstand_rand_mm', self.beschnittzugabe_mm))
                self.sicherheitsabstand_mm = getattr(z, 'sicherheitsabstand_mm',
                                                     getattr(z, 'abstand_rand_mm', self.sicherheitsabstand_mm))

                self.schnittlinien_anzeigen = getattr(z, 'schnittlinien_anzeigen', self.schnittlinien_anzeigen)
                self.export_dpi = getattr(z, 'export_dpi', self.export_dpi)  # Standard-DPI für Export
                self.minimum_dpi_for_print = getattr(z, 'minimum_dpi_for_print', self.minimum_dpi_for_print)

                # Font-Settings (v7.3)
                self.font_size = getattr(z, 'font_size', self.font_size)
                self.font_family = getattr(z, 'font_family', self.font_family)

            # Grafik-Settings (v7.1)
            if hasattr(settings, 'grafik'):
                g = settings.grafik
                self.grafik_hoehe_mm = getattr(g, 'max_hoehe_mm', self.grafik_hoehe_mm)
                self.grafik_breite_mm = getattr(g, 'max_breite_mm', self.grafik_breite_mm)
                self.grafik_position = getattr(g, 'position', self.grafik_position)

            # NEW: S1-Layout Settings (v0.9)
            if hasattr(settings, 's1'):
                s = settings.s1
                self.s1_zeichen_hoehe_mm = getattr(s, 'zeichen_hoehe_mm', self.s1_zeichen_hoehe_mm)
                self.s1_zeichen_breite_mm = getattr(s, 'zeichen_breite_mm', self.s1_zeichen_breite_mm)
                self.s1_beschnittzugabe_mm = getattr(s, 'beschnittzugabe_mm', self.s1_beschnittzugabe_mm)
                self.s1_sicherheitsabstand_mm = getattr(s, 'sicherheitsabstand_mm', self.s1_sicherheitsabstand_mm)
                self.s1_aspect_locked = getattr(s, 'aspect_locked', self.s1_aspect_locked)
                self.s1_links_prozent = getattr(s, 'links_prozent', self.s1_links_prozent)
                self.s1_anzahl_schreiblinien = getattr(s, 'anzahl_schreiblinien', self.s1_anzahl_schreiblinien)
                self.s1_staerke_anzeigen = getattr(s, 'staerke_anzeigen', self.s1_staerke_anzeigen)

            self.logger.info(f"RuntimeConfig geladen: standard_modus={self.standard_modus}, dpi={self.export_dpi}")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der User-Settings: {e}")
            self.logger.warning("Verwende Factory Defaults")

    def save_to_settings(self, settings):
        """
        Speichert aktuelle RuntimeConfig zurück in AppSettings

        Args:
            settings: AppSettings-Objekt
        """
        self.logger.info("Speichere RuntimeConfig in AppSettings")

        try:
            if hasattr(settings, 'zeichen'):
                settings.zeichen.standard_modus = self.standard_modus
                settings.zeichen.zeichen_hoehe_mm = self.zeichen_hoehe_mm
                settings.zeichen.zeichen_breite_mm = self.zeichen_breite_mm
                settings.zeichen.abstand_grafik_text_mm = self.abstand_grafik_text_mm
                settings.zeichen.text_bottom_offset_mm = self.text_bottom_offset_mm
                settings.zeichen.beschnittzugabe_mm = self.beschnittzugabe_mm
                settings.zeichen.sicherheitsabstand_mm = self.sicherheitsabstand_mm
                settings.zeichen.schnittlinien_anzeigen = self.schnittlinien_anzeigen
                # Hinweis: export_dpi und minimum_dpi_for_print werden direkt in Settings gespeichert

                # Font-Settings (v7.3)
                settings.zeichen.font_size = self.font_size
                settings.zeichen.font_family = self.font_family

            # Grafik-Settings (v7.1)
            if hasattr(settings, 'grafik'):
                settings.grafik.max_hoehe_mm = self.grafik_hoehe_mm
                settings.grafik.max_breite_mm = self.grafik_breite_mm
                settings.grafik.position = self.grafik_position

            # NEW: S1-Layout Settings (v0.9)
            if hasattr(settings, 's1'):
                settings.s1.zeichen_hoehe_mm = self.s1_zeichen_hoehe_mm
                settings.s1.zeichen_breite_mm = self.s1_zeichen_breite_mm
                settings.s1.beschnittzugabe_mm = self.s1_beschnittzugabe_mm
                settings.s1.sicherheitsabstand_mm = self.s1_sicherheitsabstand_mm
                settings.s1.aspect_locked = self.s1_aspect_locked
                settings.s1.links_prozent = self.s1_links_prozent
                settings.s1.anzahl_schreiblinien = self.s1_anzahl_schreiblinien
                settings.s1.staerke_anzeigen = self.s1_staerke_anzeigen

            self.logger.debug("RuntimeConfig in AppSettings gespeichert")

        except Exception as e:
            self.logger.error(f"Fehler beim Speichern in AppSettings: {e}")

    def reload_from_settings(self):
        """
        Lädt settings.json neu und aktualisiert RuntimeConfig

        NEW (v7.3): Wird vom Settings Dialog aufgerufen
        """
        from settings_manager import SettingsManager

        self.logger.info("Reload settings.json in RuntimeConfig")

        try:
            settings_mgr = SettingsManager()
            settings = settings_mgr.load_settings()
            self.load_from_settings(settings)

            self.logger.info("RuntimeConfig neu geladen aus settings.json")

        except Exception as e:
            self.logger.error(f"Fehler beim Neuladen von settings.json: {e}", exc_info=True)

    def get(self, key: str, default=None):
        """
        Holt Wert nach Schlüssel

        Args:
            key: Attribut-Name (z.B. "standard_modus")
            default: Fallback-Wert

        Returns:
            Wert oder default
        """
        return getattr(self, key, default)

    def set(self, key: str, value):
        """
        Setzt Wert zur Laufzeit (mit Validierung)

        Args:
            key: Attribut-Name
            value: Neuer Wert

        Raises:
            ValueError: Wenn Validierung fehlschlägt
        """
        # Validierung
        from validation_manager import RuntimeConfigValidator

        validator = RuntimeConfigValidator()
        is_valid, error_msg = validator.validate_setting(key, value)

        if not is_valid:
            self.logger.error(f"Validierung fehlgeschlagen für {key}={value}: {error_msg}")
            raise ValueError(error_msg)

        # Wert setzen
        setattr(self, key, value)
        self.logger.debug(f"RuntimeConfig.{key} = {value}")

    def to_dict(self) -> dict:
        """
        Exportiert alle konfigurierbaren Werte als Dictionary

        Returns:
            dict: Alle Werte
        """
        return {
            'zeichen_dir': str(self.zeichen_dir),  # NEW: Als String für Serialisierung
            'standard_modus': self.standard_modus,
            'font_size': self.font_size,
            'font_family': self.font_family,
            'export_dpi': self.export_dpi,
            'minimum_dpi_for_print': self.minimum_dpi_for_print,
            'zeichen_hoehe_mm': self.zeichen_hoehe_mm,
            'zeichen_breite_mm': self.zeichen_breite_mm,
            'beschnittzugabe_mm': self.beschnittzugabe_mm,
            'sicherheitsabstand_mm': self.sicherheitsabstand_mm,
            'abstand_grafik_text_mm': self.abstand_grafik_text_mm,
            'text_bottom_offset_mm': self.text_bottom_offset_mm,
            'ov_length': self.ov_length,
            'ruf_length': self.ruf_length,
            'ort_length': self.ort_length,
            'freitext_length': self.freitext_length,
            'staerke_digits': self.staerke_digits,
            'schnittlinien_anzeigen': self.schnittlinien_anzeigen,
            'grafik_hoehe_mm': self.grafik_hoehe_mm,
            'grafik_breite_mm': self.grafik_breite_mm,
            'grafik_position': self.grafik_position,
            # NEW: S1-Layout Parameter
            's1_zeichen_hoehe_mm': self.s1_zeichen_hoehe_mm,
            's1_zeichen_breite_mm': self.s1_zeichen_breite_mm,
            's1_beschnittzugabe_mm': self.s1_beschnittzugabe_mm,
            's1_sicherheitsabstand_mm': self.s1_sicherheitsabstand_mm,
            's1_aspect_locked': self.s1_aspect_locked,
            's1_links_prozent': self.s1_links_prozent,
            's1_anzahl_schreiblinien': self.s1_anzahl_schreiblinien,
            's1_staerke_anzeigen': self.s1_staerke_anzeigen
        }


# ================================================================================================
# CONVENIENCE FUNCTIONS
# ================================================================================================

def get_config() -> RuntimeConfig:
    """
    Shortcut für RuntimeConfig.get_instance()

    Returns:
        RuntimeConfig: Singleton-Instanz

    Example:
        config = get_config()
        modus = config.standard_modus
    """
    return RuntimeConfig.get_instance()


def init_runtime_config(settings):
    """
    Initialisiert RuntimeConfig mit User-Settings

    Sollte beim Programmstart (nach SettingsManager.load_settings()) aufgerufen werden

    Args:
        settings: AppSettings-Objekt

    Example:
        settings_mgr = SettingsManager()
        settings = settings_mgr.load_settings()
        init_runtime_config(settings)
    """
    config = RuntimeConfig.get_instance()
    config.load_from_settings(settings)


# ================================================================================================
# TEST ROUTINES
# ================================================================================================

if __name__ == "__main__":
    """
    Test-Routine für runtime_config.py

    Testet RuntimeConfig-Singleton und Funktionen.
    Ausführung: python runtime_config.py
    """
    print("=" * 70)
    print("TEST-ROUTINE: runtime_config.py")
    print("=" * 70)

    # Test 1: Singleton-Pattern
    print("\n[Test 1] Singleton-Pattern")
    print("-" * 70)

    config1 = get_config()
    config2 = get_config()

    print(f"  config1 ID: {id(config1)}")
    print(f"  config2 ID: {id(config2)}")
    print(f"  Gleiche Instanz: {config1 is config2}")

    assert config1 is config2, "Singleton fehlgeschlagen!"
    print("  [OK] Singleton funktioniert")

    # Test 2: Factory Defaults geladen
    print("\n[Test 2] Factory Defaults")
    print("-" * 70)

    config = get_config()

    print(f"  Standard-Modus: {config.standard_modus}")
    print(f"  Font-Size: {config.font_size}")
    print(f"  Font-Family: {config.font_family}")
    print(f"  Export-DPI: {config.export_dpi}")
    print(f"  Minimum-DPI: {config.minimum_dpi_for_print}")
    print(f"  Zeichen-Hoehe: {config.zeichen_hoehe_mm} mm")
    print(f"  Zeichen-Breite: {config.zeichen_breite_mm} mm")

    assert config.standard_modus is not None, "Standard-Modus fehlt!"
    assert config.font_size > 0, "Font-Size ungueltig!"
    assert config.export_dpi > 0, "Export-DPI ungueltig!"
    assert config.zeichen_hoehe_mm > 0, "Zeichen-Hoehe ungueltig!"
    print("  [OK] Factory Defaults geladen")

    # Test 3: set() Methode mit Validierung
    print("\n[Test 3] set() Methode")
    print("-" * 70)

    # Test nur wenn ValidationManager verfuegbar (PyQt6 needed)
    try:
        # Gueltigen Wert setzen
        config.set('font_size', 12)
        print(f"  font_size auf 12 gesetzt: {config.font_size}")
        assert config.font_size == 12, "set() fehlgeschlagen!"

        # Ungueltigen Wert setzen (sollte ValueError werfen)
        try:
            config.set('font_size', -5)
            assert False, "Validierung fehlgeschlagen - sollte ValueError werfen!"
        except ValueError as e:
            print(f"  Ungueltige font_size (-5) abgelehnt: {e}")

        print("  [OK] set() mit Validierung funktioniert")
    except ModuleNotFoundError:
        print("  [SKIP] ValidationManager nicht verfuegbar (PyQt6 fehlt)")

    # Test 4: to_dict() Export
    print("\n[Test 4] to_dict() Export")
    print("-" * 70)

    config_dict = config.to_dict()

    print(f"  Exportierte Keys: {len(config_dict)}")
    print(f"  Beispiel-Keys: {list(config_dict.keys())[:5]}...")

    assert 'standard_modus' in config_dict, "standard_modus fehlt!"
    assert 'font_size' in config_dict, "font_size fehlt!"
    assert 'export_dpi' in config_dict, "export_dpi fehlt!"
    print("  [OK] to_dict() Export funktioniert")

    # Test 5: reset_instance() (nur fuer Tests!)
    print("\n[Test 5] reset_instance()")
    print("-" * 70)

    old_id = id(config)
    RuntimeConfig.reset_instance()
    new_config = get_config()
    new_id = id(new_config)

    print(f"  Alte Instanz ID: {old_id}")
    print(f"  Neue Instanz ID: {new_id}")
    print(f"  Unterschiedlich: {old_id != new_id}")

    assert old_id != new_id, "reset_instance() fehlgeschlagen!"
    print("  [OK] reset_instance() funktioniert")

    # Test 6: S1-Layout Parameter
    print("\n[Test 6] S1-Layout Parameter")
    print("-" * 70)

    # Reset und fresh config holen
    RuntimeConfig.reset_instance()
    config = get_config()

    # Factory Defaults pruefen
    from constants import (
        DEFAULT_S1_ASPECT_LOCKED,
        DEFAULT_S1_LINKS_PROZENT,
        DEFAULT_S1_ANZAHL_SCHREIBLINIEN,
        DEFAULT_S1_STAERKE_ANZEIGEN
    )

    print(f"  s1_aspect_locked: {config.s1_aspect_locked}")
    assert config.s1_aspect_locked == DEFAULT_S1_ASPECT_LOCKED, "aspect_locked Default falsch!"

    print(f"  s1_links_prozent: {config.s1_links_prozent}%")
    assert config.s1_links_prozent == DEFAULT_S1_LINKS_PROZENT, "links_prozent Default falsch!"

    print(f"  s1_anzahl_schreiblinien: {config.s1_anzahl_schreiblinien} Zeilen")
    assert config.s1_anzahl_schreiblinien == DEFAULT_S1_ANZAHL_SCHREIBLINIEN, "anzahl_schreiblinien Default falsch!"

    print(f"  s1_staerke_anzeigen: {config.s1_staerke_anzeigen}")
    assert config.s1_staerke_anzeigen == DEFAULT_S1_STAERKE_ANZEIGEN, "staerke_anzeigen Default falsch!"

    # Pruefen ob Parameter im to_dict() Export vorhanden sind
    config_dict = config.to_dict()
    assert 's1_aspect_locked' in config_dict, "s1_aspect_locked fehlt in to_dict()!"
    assert 's1_links_prozent' in config_dict, "s1_links_prozent fehlt in to_dict()!"
    assert 's1_anzahl_schreiblinien' in config_dict, "s1_anzahl_schreiblinien fehlt in to_dict()!"
    assert 's1_staerke_anzeigen' in config_dict, "s1_staerke_anzeigen fehlt in to_dict()!"

    print("  [OK] S1-Layout Parameter korrekt")

    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ALLE TESTS BESTANDEN!")
    print("=" * 70)
