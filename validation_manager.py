#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validation_manager.py - Zentrale Validierung für taktische Zeichen

Features:
- Validierung von Grafikgrößen (max. Bereich)
- Validierung von Textlängen (max. Canvas-Größe)
- Validierung bei Schriftgrößen-Änderungen
- Zentrale Warndialoge für alle Validierungsfehler
"""

from typing import List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from PyQt6.QtWidgets import QMessageBox, QWidget

from logging_manager import LoggingManager
from runtime_config import get_config
from constants import (
    TEXT_LENGTH_VALIDATION_ENABLED,
    LINE_HEIGHT_FACTOR,
    POINTS_PER_INCH,
    mm_to_pixels,
    pixels_to_mm,
    AVAILABLE_MODI,
    AVAILABLE_GRAFIK_POSITIONS
)


@dataclass
class ValidationError:
    """Validierungsfehler"""
    item_name: str
    error_type: str  # "grafik_size", "text_overflow", "font_size"
    details: str
    current_value: float
    max_value: float


class ValidationManager:
    """
    Zentrale Validierung für taktische Zeichen

    Features:
    - Grafikgrößen-Validierung
    - Textlängen-Validierung
    - Schriftgrößen-Validierung
    - Warndialoge
    """

    def __init__(self):
        """Initialisiert ValidationManager"""
        self.logger = LoggingManager().get_logger(__name__)

    def validate_grafik_size(
        self,
        hoehe: float,
        breite: float,
        max_hoehe: float,
        max_breite: float,
        item_name: str = "Zeichen"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validiert Grafikgröße gegen Maximum

        Args:
            hoehe: Grafik-Höhe in mm
            breite: Grafik-Breite in mm
            max_hoehe: Maximale Höhe in mm
            max_breite: Maximale Breite in mm
            item_name: Name des Items für Fehlermeldung

        Returns:
            tuple: (is_valid, error_message)
        """
        errors = []

        if hoehe > max_hoehe:
            errors.append(f"Höhe: {hoehe:.1f} mm > {max_hoehe:.1f} mm (max)")

        if breite > max_breite:
            errors.append(f"Breite: {breite:.1f} mm > {max_breite:.1f} mm (max)")

        if errors:
            error_msg = (
                f"Grafikgröße von '{item_name}' überschreitet das Maximum:\n\n"
                + "\n".join([f"  • {e}" for e in errors])
            )
            return False, error_msg

        return True, None

    def validate_text_length(
        self,
        text: str,
        modus: str,
        zeichen_hoehe_mm: float,
        zeichen_breite_mm: float,
        sicherheitsabstand_mm: float,
        font_size: Optional[int] = None,
        item_name: str = "Zeichen"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validiert ob Text in Canvas passt

        WICHTIG: Diese Methode berechnet die Text-Höhe und prüft,
        ob Text + Grafik in den sicheren Bereich passen.

        Args:
            text: Eingegebener Text
            modus: Zeichen-Modus (ov_staerke, freitext, etc.)
            zeichen_hoehe_mm: Zeichengröße Höhe
            zeichen_breite_mm: Zeichengröße Breite
            sicherheitsabstand_mm: Sicherheitsabstand (Grafik/Text zum fertigen Rand)
            font_size: Schriftgröße in pt (None = aus RuntimeConfig)
            item_name: Name des Items für Fehlermeldung

        Returns:
            tuple: (is_valid, error_message)
        """
        if not TEXT_LENGTH_VALIDATION_ENABLED:
            return True, None

        # FIXED: Font-Size aus RuntimeConfig wenn nicht übergeben
        if font_size is None:
            font_size = get_config().font_size

        # Berechne tatsächliche Text-Höhe
        try:
            from text_overlay import TextOverlayPlaceholder, ZeichenConfig

            # FIXED: DPI aus RuntimeConfig verwenden
            runtime_cfg = get_config()

            # Erstelle temporäre Config
            config = ZeichenConfig(
                zeichen_id="validation_temp",
                svg_path=Path("temp.svg"),
                modus=modus,
                ov_name=text if modus in ["ov_staerke", "ort_staerke"] else None,
                freitext=text if modus in ["freitext", "dateiname"] else None,
                font_size=font_size,
                dpi=runtime_cfg.export_dpi
            )

            # Berechne Text-Höhe (inkl. Offsets!)
            overlay = TextOverlayPlaceholder()
            text_hoehe_mm = overlay.calculate_text_height_mm(config)

            # NEW: Berechne Text-Breite
            text_breite_mm = overlay.calculate_text_width_mm(config)

            # Verfügbare Höhe im sicheren Bereich
            sicherer_bereich_hoehe_mm = zeichen_hoehe_mm - (2 * sicherheitsabstand_mm)
            sicherer_bereich_breite_mm = zeichen_breite_mm - (2 * sicherheitsabstand_mm)

            # NEW: Prüfe BREITE zuerst (kritischer!)
            if text_breite_mm > sicherer_bereich_breite_mm:
                error_msg = (
                    f"Text von '{item_name}' ist zu BREIT für den sicheren Bereich:\n\n"
                    f"  • Text-Breite: {text_breite_mm:.1f} mm\n"
                    f"  • Verfügbar: {sicherer_bereich_breite_mm:.1f} mm\n"
                    f"  • Überschreitung: {text_breite_mm - sicherer_bereich_breite_mm:.1f} mm\n\n"
                    f"ACHTUNG: Text läuft über den Canvas hinaus!\n\n"
                    f"Lösungen:\n"
                    f"  1. Text KÜRZEN (empfohlen)\n"
                    f"  2. Schriftgröße reduzieren\n"
                    f"  3. Zeichengröße erhöhen"
                )
                return False, error_msg

            # Prüfe HÖHE
            if text_hoehe_mm > sicherer_bereich_hoehe_mm:
                error_msg = (
                    f"Text von '{item_name}' ist zu HOCH für den sicheren Bereich:\n\n"
                    f"  • Text-Höhe: {text_hoehe_mm:.1f} mm\n"
                    f"  • Verfügbar: {sicherer_bereich_hoehe_mm:.1f} mm\n"
                    f"  • Überschreitung: {text_hoehe_mm - sicherer_bereich_hoehe_mm:.1f} mm\n\n"
                    f"Hinweis: Text-Höhe beinhaltet bereits die Offsets:\n"
                    f"  - Grafik↔Text: {runtime_cfg.abstand_grafik_text_mm:.1f} mm\n"
                    f"  - Text↔Sicherheitsrand: {runtime_cfg.text_bottom_offset_mm:.1f} mm\n\n"
                    f"Lösungen:\n"
                    f"  1. Text kürzen\n"
                    f"  2. Schriftgröße reduzieren\n"
                    f"  3. Zeichengröße erhöhen"
                )
                return False, error_msg

            # NEW: Warnung bei knapper Breite (< 5mm Reserve)
            breite_reserve = sicherer_bereich_breite_mm - text_breite_mm
            if breite_reserve < 5.0:
                self.logger.warning(
                    f"'{item_name}': Text ist sehr breit! "
                    f"Nur {breite_reserve:.1f}mm Reserve"
                )

            # Warnung bei knappem Platz (< 5mm für Grafik)
            remaining_space = sicherer_bereich_hoehe_mm - text_hoehe_mm
            if remaining_space < 5.0:
                self.logger.warning(
                    f"'{item_name}': Wenig Platz für Grafik! "
                    f"Nur {remaining_space:.1f}mm verfügbar"
                )

        except Exception as e:
            self.logger.error(f"Fehler bei Text-Validierung: {e}")
            return True, None  # Bei Fehler durchlassen, nicht blockieren

        return True, None

    def validate_font_size(
        self,
        font_size: int,
        zeichen_hoehe_mm: float,
        abstand_rand_mm: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validiert ob Schriftgröße für Zeichengröße geeignet ist

        Args:
            font_size: Schriftgröße in pt
            zeichen_hoehe_mm: Zeichengröße Höhe
            abstand_rand_mm: Randabstand

        Returns:
            tuple: (is_valid, error_message)
        """
        # Berechne minimale benötigte Höhe für 2 Zeilen Text
        # FIXED: DPI aus RuntimeConfig verwenden
        runtime_cfg = get_config()

        # Font-Größe in mm
        font_size_px = int((font_size / POINTS_PER_INCH) * runtime_cfg.export_dpi)  # FIXED: Aus RuntimeConfig
        line_height_px = int(font_size_px * LINE_HEIGHT_FACTOR)
        text_height_px = line_height_px * 2  # 2 Zeilen (OV+Stärke Modus)

        # Plus Offsets (FIXED: Aus RuntimeConfig statt DEFAULT_*)
        grafik_offset_px = mm_to_pixels(runtime_cfg.abstand_grafik_text_mm, runtime_cfg.export_dpi)
        bottom_offset_px = mm_to_pixels(runtime_cfg.text_bottom_offset_mm, runtime_cfg.export_dpi)
        total_height_px = text_height_px + grafik_offset_px + bottom_offset_px

        total_height_mm = pixels_to_mm(total_height_px, runtime_cfg.export_dpi)

        # Verfügbarer Bereich
        sicherer_bereich_mm = zeichen_hoehe_mm - (2 * abstand_rand_mm)

        if total_height_mm > sicherer_bereich_mm:
            error_msg = (
                f"Schriftgröße {font_size} pt ist zu groß für die Zeichengröße:\n\n"
                f"  • Benötigte Höhe (2 Zeilen): {total_height_mm:.1f} mm\n"
                f"  • Verfügbar: {sicherer_bereich_mm:.1f} mm\n"
                f"  • Überschreitung: {total_height_mm - sicherer_bereich_mm:.1f} mm\n\n"
                f"Lösungen:\n"
                f"  1. Schriftgröße reduzieren\n"
                f"  2. Zeichengröße erhöhen\n"
                f"  3. Randabstand verkleinern"
            )
            return False, error_msg

        # Warnung wenn < 10mm für Grafik bleibt
        remaining_space = sicherer_bereich_mm - total_height_mm
        if remaining_space < 10.0:
            self.logger.warning(
                f"Font {font_size}pt: Wenig Platz für Grafik! "
                f"Nur {remaining_space:.1f}mm verfügbar"
            )

        return True, None

    def show_validation_warning(
        self,
        parent: QWidget,
        title: str,
        message: str
    ) -> None:
        """
        Zeigt Validierungs-Warnung als MessageBox

        Args:
            parent: Parent-Widget
            title: Titel der MessageBox
            message: Fehlermeldung
        """
        QMessageBox.warning(parent, title, message)

    def show_grafik_size_exceeded_warning(
        self,
        parent: QWidget,
        items_exceeding: List[str],
        max_hoehe: float,
        max_breite: float
    ) -> None:
        """
        Zeigt Warnung für überschrittene Grafikgrößen

        Args:
            parent: Parent-Widget
            items_exceeding: Liste von Item-Namen
            max_hoehe: Maximale Höhe
            max_breite: Maximale Breite
        """
        item_names = "\n".join([f"  • {name}" for name in items_exceeding[:10]])
        if len(items_exceeding) > 10:
            item_names += f"\n  ... und {len(items_exceeding) - 10} weitere"

        message = (
            f"Die folgenden Zeichen haben Grafikgrößen, die das neue Maximum "
            f"({max_hoehe:.1f} x {max_breite:.1f} mm) überschreiten:\n\n"
            f"{item_names}\n\n"
            f"Die Werte wurden automatisch auf das Maximum angepasst."
        )

        QMessageBox.warning(parent, "Grafikgröße überschritten", message)

    def show_batch_text_length_warning(
        self,
        parent: QWidget,
        items_exceeding: List[str]
    ) -> None:
        """
        Zeigt EINE Warnung für mehrere Zeichen mit zu langem Text

        Args:
            parent: Parent-Widget
            items_exceeding: Liste von Item-Namen die zu lang sind
        """
        # Max 3-4 Beispiele zeigen
        max_examples = 4
        example_names = "\n".join([f"  - {name}" for name in items_exceeding[:max_examples]])

        total_count = len(items_exceeding)
        remaining = total_count - max_examples

        if remaining > 0:
            example_names += f"\n  ... und {remaining} weitere"

        message = (
            f"Die folgenden {total_count} Zeichen haben Texte, die zu lang sind:\n\n"
            f"{example_names}\n\n"
            f"Alle betroffenen Zeilen wurden ROT markiert.\n"
            f"Bitte kürze die Texte manuell!"
        )

        QMessageBox.warning(parent, "Texte zu lang", message)


# ================================================================================================
# TESTING
# ================================================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("ValidationManager Test")
    print("=" * 80)

    manager = ValidationManager()

    # Test 1: Grafikgröße
    print("\n[Test 1] Grafikgroesse validieren")
    valid, error = manager.validate_grafik_size(40.0, 40.0, 39.0, 39.0, "Test.svg")
    print(f"  Ergebnis: {'Gueltig' if valid else 'Ungueltig'}")
    if error:
        print(f"  Fehler: {error}")

    # Test 2: Textlänge
    print("\n[Test 2] Textlaenge validieren")
    valid, error = manager.validate_text_length(
        "Sehr langer OV-Name der wahrscheinlich zu lang ist",
        "ov_staerke",
        45.0, 45.0, 3.0,
        item_name="Test.svg"
    )
    print(f"  Ergebnis: {'Gueltig' if valid else 'Ungueltig'}")
    if error:
        print(f"  Fehler: {error}")

    # Test 3: Schriftgröße
    print("\n[Test 3] Schriftgroesse validieren")
    valid, error = manager.validate_font_size(20, 45.0, 3.0)
    print(f"  Ergebnis: {'Gueltig' if valid else 'Ungueltig'}")
    if error:
        print(f"  Fehler: {error}")

    print("\n" + "=" * 80)


# ================================================================================================
# RUNTIME CONFIG VALIDIERUNG
# ================================================================================================

class RuntimeConfigValidator:
    """
    Validator für RuntimeConfig-Einstellungen

    Validiert alle User-Settings bevor sie in RuntimeConfig gespeichert werden.

    Features:
    - Range-Checks (Min/Max)
    - Type-Checks
    - Enum-Validierung (z.B. Modi, Positionen)
    - Abhängigkeits-Validierung
    """

    def __init__(self):
        """Initialisiert Validator"""
        self.logger = LoggingManager().get_logger(__name__)

        # Import Ranges
        self.AVAILABLE_MODI = AVAILABLE_MODI
        self.AVAILABLE_GRAFIK_POSITIONS = AVAILABLE_GRAFIK_POSITIONS

    def validate_setting(self, key: str, value) -> Tuple[bool, Optional[str]]:
        """
        Validiert einzelne Einstellung

        Args:
            key: Setting-Name (z.B. "standard_modus")
            value: Wert

        Returns:
            tuple: (is_valid: bool, error_message: Optional[str])
        """
        # Mapping zu spezifischen Validierungsmethoden
        validators = {
            'standard_modus': self._validate_modus,
            'font_size': self._validate_font_size,
            'dpi': self._validate_dpi,
            'zeichen_hoehe_mm': self._validate_zeichen_hoehe,
            'zeichen_breite_mm': self._validate_zeichen_breite,
            'beschnittzugabe_mm': self._validate_beschnittzugabe,
            'sicherheitsabstand_mm': self._validate_sicherheitsabstand,
            'abstand_grafik_text_mm': self._validate_abstand_grafik_text,
            'text_bottom_offset_mm': self._validate_text_bottom_offset,
            'ov_length': self._validate_placeholder_length,
            'ruf_length': self._validate_placeholder_length,
            'ort_length': self._validate_placeholder_length,
            'freitext_length': self._validate_placeholder_length,
            'staerke_digits': self._validate_staerke_digits,
            'schnittlinien_anzeigen': self._validate_bool,
            # NEW: S1-Layout Zeichen-Abmessungen (gleiche Validierung wie S2)
            's1_zeichen_hoehe_mm': self._validate_zeichen_hoehe,
            's1_zeichen_breite_mm': self._validate_zeichen_breite,
            's1_beschnittzugabe_mm': self._validate_beschnittzugabe,
            's1_sicherheitsabstand_mm': self._validate_sicherheitsabstand,
            's1_anzahl_schreiblinien': self._validate_s1_anzahl_schreiblinien
        }

        # Validator für Key finden
        validator_func = validators.get(key)

        if validator_func is None:
            # Unbekanntes Setting - erlauben (für Erweiterbarkeit)
            self.logger.warning(f"Keine Validierung für Setting '{key}' definiert")
            return True, None

        # Validierung durchführen
        return validator_func(value)

    def _validate_modus(self, value: str) -> Tuple[bool, Optional[str]]:
        """Validiert Modus"""
        if value not in self.AVAILABLE_MODI:
            return False, f"Ungültiger Modus '{value}'. Erlaubt: {self.AVAILABLE_MODI}"
        return True, None

    def _validate_font_size(self, value: int) -> Tuple[bool, Optional[str]]:
        """Validiert Schriftgröße"""
        if not isinstance(value, int):
            return False, f"Schriftgröße muss Integer sein, ist aber {type(value)}"

        if value < 6 or value > 200:
            return False, f"Schriftgröße muss zwischen 6 und 200 pt liegen (ist: {value})"

        return True, None

    def _validate_dpi(self, value: int) -> Tuple[bool, Optional[str]]:
        """Validiert DPI"""
        if not isinstance(value, int):
            return False, f"DPI muss Integer sein, ist aber {type(value)}"

        valid_dpis = [300, 600, 1200]  # Nur diese Werte erlaubt
        if value not in valid_dpis:
            return False, f"DPI muss einer von {valid_dpis} sein (ist: {value})"

        return True, None

    def _validate_zeichen_hoehe(self, value: float) -> Tuple[bool, Optional[str]]:
        """Validiert Zeichenhöhe"""
        if not isinstance(value, (int, float)):
            return False, f"Zeichenhöhe muss Zahl sein, ist aber {type(value)}"

        if value < 10.0 or value > 500.0:
            return False, f"Zeichenhöhe muss zwischen 10 und 500 mm liegen (ist: {value})"

        return True, None

    def _validate_zeichen_breite(self, value: float) -> Tuple[bool, Optional[str]]:
        """Validiert Zeichenbreite"""
        if not isinstance(value, (int, float)):
            return False, f"Zeichenbreite muss Zahl sein, ist aber {type(value)}"

        if value < 10.0 or value > 500.0:
            return False, f"Zeichenbreite muss zwischen 10 und 500 mm liegen (ist: {value})"

        return True, None

    def _validate_abstand_rand(self, value: float) -> Tuple[bool, Optional[str]]:
        """Validiert Rand-Abstand (DEPRECATED - für Rückwärtskompatibilität)"""
        if not isinstance(value, (int, float)):
            return False, f"Rand-Abstand muss Zahl sein, ist aber {type(value)}"

        if value < 0.0 or value > 20.0:
            return False, f"Rand-Abstand muss zwischen 0 und 20 mm liegen (ist: {value})"

        return True, None

    def _validate_beschnittzugabe(self, value: float) -> Tuple[bool, Optional[str]]:
        """Validiert Beschnittzugabe"""
        if not isinstance(value, (int, float)):
            return False, f"Beschnittzugabe muss Zahl sein, ist aber {type(value)}"

        if value < 0.0 or value > 20.0:
            return False, f"Beschnittzugabe muss zwischen 0 und 20 mm liegen (ist: {value})"

        return True, None

    def _validate_sicherheitsabstand(self, value: float) -> Tuple[bool, Optional[str]]:
        """Validiert Sicherheitsabstand (Innenabstand Grafik zum fertigen Rand)"""
        if not isinstance(value, (int, float)):
            return False, f"Sicherheitsabstand muss Zahl sein, ist aber {type(value)}"

        if value < 0.0 or value > 20.0:
            return False, f"Sicherheitsabstand muss zwischen 0 und 20 mm liegen (ist: {value})"

        return True, None

    def _validate_abstand_grafik_text(self, value: float) -> Tuple[bool, Optional[str]]:
        """Validiert Grafik-Text-Abstand"""
        if not isinstance(value, (int, float)):
            return False, f"Grafik-Text-Abstand muss Zahl sein, ist aber {type(value)}"

        if value < 0.0 or value > 20.0:
            return False, f"Grafik-Text-Abstand muss zwischen 0 und 20 mm liegen (ist: {value})"

        return True, None

    def _validate_text_bottom_offset(self, value: float) -> Tuple[bool, Optional[str]]:
        """Validiert Text-Bottom-Offset"""
        if not isinstance(value, (int, float)):
            return False, f"Text-Bottom-Offset muss Zahl sein, ist aber {type(value)}"

        if value < 0.0 or value > 10.0:
            return False, f"Text-Bottom-Offset muss zwischen 0 und 10 mm liegen (ist: {value})"

        return True, None

    def _validate_s1_anzahl_schreiblinien(self, value: int) -> Tuple[bool, Optional[str]]:
        """
        Validiert Anzahl Schreiblinien für S1-Layout

        Args:
            value: Anzahl der Schreiblinien (3-10)

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not isinstance(value, int):
            return False, f"Anzahl Schreiblinien muss Integer sein, ist aber {type(value)}"

        if value < 3 or value > 10:
            return False, f"Anzahl Schreiblinien muss zwischen 3 und 10 liegen (ist: {value})"

        return True, None

    def _validate_placeholder_length(self, value: int) -> Tuple[bool, Optional[str]]:
        """Validiert Platzhalter-Länge"""
        if not isinstance(value, int):
            return False, f"Platzhalter-Länge muss Integer sein, ist aber {type(value)}"

        if value < 8 or value > 64:
            return False, f"Platzhalter-Länge muss zwischen 8 und 64 liegen (ist: {value})"

        return True, None

    def _validate_staerke_digits(self, value: list) -> Tuple[bool, Optional[str]]:
        """Validiert Stärke-Digits Format"""
        if not isinstance(value, list):
            return False, f"Stärke-Digits muss Liste sein, ist aber {type(value)}"

        if len(value) != 4:
            return False, f"Stärke-Digits muss genau 4 Elemente haben (ist: {len(value)})"

        for i, digit in enumerate(value):
            if not isinstance(digit, int):
                return False, f"Stärke-Digits[{i}] muss Integer sein, ist aber {type(digit)}"

            if digit < 1 or digit > 20:
                return False, f"Stärke-Digits[{i}] muss zwischen 1 und 20 liegen (ist: {digit})"

        return True, None

    def _validate_bool(self, value: bool) -> Tuple[bool, Optional[str]]:
        """Validiert Boolean"""
        if not isinstance(value, bool):
            return False, f"Wert muss Boolean sein, ist aber {type(value)}"

        return True, None
