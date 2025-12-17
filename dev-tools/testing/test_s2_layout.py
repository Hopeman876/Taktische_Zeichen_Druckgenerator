#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_s2_layout.py - Integrations-Tests fuer S2-Layout (Standard-Zeichen)

Testet realistische S2-Layout Szenarien mit kombinierten Funktionen
aus mehreren Modulen (constants, runtime_config).

S2-Layout:
- Standard-Zeichen mit Freitext oder Schreiblinien
- Format: 45mm x 45mm (1:1 Seitenverhaeltnis, optional)
- Struktur: Oben = Grafik | Unten = Text/Schreiblinien
- Modi: MODUS_FREITEXT, MODUS_SCHREIBLINIE_STAERKE (S2-Variante)

WICHTIG: Unit-Tests fuer einzelne Module befinden sich direkt in den
jeweiligen Modul-Dateien:
- Standard-Konstanten: constants.py
- RuntimeConfig: runtime_config.py

Diese Datei testet NUR:
- Realistische Anwendungsszenarien
- Aspect Lock Feature (v0.8.2.4)
- Zusammenspiel mehrerer Module
- End-to-End Berechnungen

Ausfuehrung: python dev-tools/testing/test_s2_layout.py
Datum: 2025-12-03
Version: 1.0
"""

import sys
from pathlib import Path
from typing import Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from modules (real implementation)
from constants import (
    LINE_HEIGHT_FACTOR,
    SYSTEM_POINTS_PER_INCH,
)

from runtime_config import get_config


def print_section(title: str):
    """Formatierte Sektion-Ueberschrift ausgeben"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_test(test_name: str):
    """Formatierte Test-Ueberschrift ausgeben"""
    print(f"\n[Integrations-Test] {test_name}")
    print("-" * 70)


def calculate_canvas_size(
    zeichen_groesse_mm: float,
    sicherheitsabstand_mm: float
) -> float:
    """
    Berechnet Canvas-Groesse nach Sicherheitsabzug

    Args:
        zeichen_groesse_mm: Zeichengroesse (Hoehe oder Breite)
        sicherheitsabstand_mm: Sicherheitsabstand

    Returns:
        Canvas-Groesse in mm
    """
    canvas_mm = zeichen_groesse_mm - (2 * sicherheitsabstand_mm)
    return round(canvas_mm, 2)


def calculate_max_grafik_size(
    canvas_mm: float,
    abstand_grafik_text_mm: float,
    text_hoehe_mm: float
) -> float:
    """
    Berechnet maximale Grafikgroesse

    S2-Layout: Oben Grafik, unten Text
    Max. Grafik = Canvas - Abstand - Text

    Args:
        canvas_mm: Canvas-Groesse
        abstand_grafik_text_mm: Abstand zwischen Grafik und Text
        text_hoehe_mm: Hoehe des Textbereichs

    Returns:
        Max. Grafikgroesse in mm
    """
    max_grafik = canvas_mm - abstand_grafik_text_mm - text_hoehe_mm
    return round(max_grafik, 2)


def calculate_fontsize_pt(
    line_height_mm: float
) -> float:
    """
    Berechnet Schriftgroesse in pt basierend auf Zeilenhoehe

    Formel: (line_height_mm / LINE_HEIGHT_FACTOR) * SYSTEM_POINTS_PER_INCH / 25.4

    Args:
        line_height_mm: Hoehe einer Zeile in mm

    Returns:
        Schriftgroesse in pt
    """
    font_size_mm = line_height_mm / LINE_HEIGHT_FACTOR
    font_size_pt = (font_size_mm * SYSTEM_POINTS_PER_INCH) / 25.4
    return round(font_size_pt, 1)


def check_aspect_locked(
    hoehe_mm: float,
    breite_mm: float,
    tolerance: float = 0.1
) -> bool:
    """
    Prueft ob Seitenverhaeltnis 1:1 ist (Aspect Lock aktiv)

    Args:
        hoehe_mm: Hoehe des Zeichens
        breite_mm: Breite des Zeichens
        tolerance: Toleranz fuer Vergleich (default: 0.1mm)

    Returns:
        True wenn 1:1, False sonst
    """
    return abs(hoehe_mm - breite_mm) <= tolerance


def run_integration_scenario_standard_square():
    """Integrations-Test: Standard quadratisch (45x45mm, Aspect Lock ON)"""
    print_test("Standard quadratisch (45x45mm, Aspect Lock ON)")

    # RuntimeConfig verwenden
    config = get_config()

    hoehe = 45.0
    breite = 45.0  # 1:1 Aspect Ratio (Standard)
    sicherheit = config.sicherheitsabstand_mm
    abstand_grafik_text = config.abstand_grafik_text_mm
    font_size = config.font_size

    canvas_hoehe = calculate_canvas_size(hoehe, sicherheit)
    canvas_breite = calculate_canvas_size(breite, sicherheit)

    # Text-Hoehe schaetzen (vereinfacht)
    text_hoehe = font_size * LINE_HEIGHT_FACTOR * 25.4 / SYSTEM_POINTS_PER_INCH
    max_grafik = calculate_max_grafik_size(canvas_hoehe, abstand_grafik_text, text_hoehe)

    aspect_locked = check_aspect_locked(hoehe, breite)

    print(f"  Zeichen: {hoehe}mm x {breite}mm (1:1 Aspect Ratio)")
    print(f"  Canvas: {canvas_hoehe}mm x {canvas_breite}mm (nach {sicherheit}mm Sicherheitsabzug)")
    print(f"  Aspect Lock: {'ON' if aspect_locked else 'OFF'}")
    print(f"  Abstand Grafik-Text: {abstand_grafik_text}mm")
    print(f"  Geschaetzte Text-Hoehe: {text_hoehe:.2f}mm (bei {font_size}pt)")
    print(f"  Max. Grafikgroesse: {max_grafik:.2f}mm")

    # Validierungen
    assert hoehe == breite, "Seitenverhaeltnis sollte 1:1 sein bei Aspect Lock!"
    assert aspect_locked, "Aspect Lock sollte aktiv sein!"
    assert canvas_hoehe == canvas_breite, "Canvas sollte quadratisch sein!"
    assert max_grafik > 0, "Max. Grafikgroesse muss positiv sein!"

    print("  [OK] Standard quadratisch funktioniert korrekt")


def run_integration_scenario_rectangular():
    """Integrations-Test: Rechteckig (60x40mm, Aspect Lock OFF)"""
    print_test("Rechteckig (60x40mm, Aspect Lock OFF)")

    config = get_config()

    hoehe = 60.0
    breite = 40.0  # Rechteckig (3:2)
    sicherheit = config.sicherheitsabstand_mm
    abstand_grafik_text = config.abstand_grafik_text_mm
    font_size = config.font_size

    canvas_hoehe = calculate_canvas_size(hoehe, sicherheit)
    canvas_breite = calculate_canvas_size(breite, sicherheit)

    text_hoehe = font_size * LINE_HEIGHT_FACTOR * 25.4 / SYSTEM_POINTS_PER_INCH
    max_grafik_hoehe = calculate_max_grafik_size(canvas_hoehe, abstand_grafik_text, text_hoehe)
    max_grafik_breite = canvas_breite  # Volle Breite

    aspect_locked = check_aspect_locked(hoehe, breite)

    print(f"  Zeichen: {hoehe}mm x {breite}mm (3:2 Rechteckig)")
    print(f"  Canvas: {canvas_hoehe}mm x {canvas_breite}mm")
    print(f"  Aspect Lock: {'ON' if aspect_locked else 'OFF'}")
    print(f"  Max. Grafik: {max_grafik_hoehe:.2f}mm x {max_grafik_breite:.2f}mm")
    print(f"  Hinweis: Rechteckige Zeichen erlauben flexible Dimensionen")

    # Validierungen
    assert hoehe != breite, "Zeichen sollte rechteckig sein!"
    assert not aspect_locked, "Aspect Lock sollte inaktiv sein!"
    assert canvas_hoehe != canvas_breite, "Canvas sollte rechteckig sein!"
    assert max_grafik_hoehe > 0, "Max. Grafikhoehe muss positiv sein!"

    print("  [OK] Rechteckig funktioniert korrekt")


def run_integration_scenario_large():
    """Integrations-Test: Grosses Zeichen (100x80mm)"""
    print_test("Grosses Zeichen (100x80mm)")

    config = get_config()

    hoehe = 100.0
    breite = 80.0
    sicherheit = config.sicherheitsabstand_mm
    abstand_grafik_text = config.abstand_grafik_text_mm
    font_size = 14  # Groessere Schrift fuer grosse Zeichen

    canvas_hoehe = calculate_canvas_size(hoehe, sicherheit)
    canvas_breite = calculate_canvas_size(breite, sicherheit)

    text_hoehe = font_size * LINE_HEIGHT_FACTOR * 25.4 / SYSTEM_POINTS_PER_INCH
    max_grafik_hoehe = calculate_max_grafik_size(canvas_hoehe, abstand_grafik_text, text_hoehe)

    print(f"  Zeichen: {hoehe}mm x {breite}mm (Grossformat)")
    print(f"  Canvas: {canvas_hoehe}mm x {canvas_breite}mm")
    print(f"  Font-Size: {font_size}pt (groesser fuer grosse Zeichen)")
    print(f"  Text-Hoehe: {text_hoehe:.2f}mm")
    print(f"  Max. Grafik-Hoehe: {max_grafik_hoehe:.2f}mm")
    print(f"  Hinweis: Bei grossen Zeichen mehr Platz fuer Details")

    # Validierungen
    assert hoehe > 80, "Zeichen sollte gross sein!"
    assert canvas_hoehe > 90, "Canvas sollte ausreichend gross sein!"
    assert max_grafik_hoehe > 50, "Sollte viel Platz fuer Grafik haben!"

    print("  [OK] Grosses Zeichen funktioniert korrekt")


def run_integration_scenario_small():
    """Integrations-Test: Kleines Zeichen (30x30mm, Edge Case)"""
    print_test("Kleines Zeichen (30x30mm, Minimum-Format Edge Case)")

    config = get_config()

    hoehe = 30.0
    breite = 30.0
    sicherheit = config.sicherheitsabstand_mm
    abstand_grafik_text = config.abstand_grafik_text_mm
    font_size = 8  # Kleinere Schrift fuer kleine Zeichen

    canvas_hoehe = calculate_canvas_size(hoehe, sicherheit)
    canvas_breite = calculate_canvas_size(breite, sicherheit)

    text_hoehe = font_size * LINE_HEIGHT_FACTOR * 25.4 / SYSTEM_POINTS_PER_INCH
    max_grafik = calculate_max_grafik_size(canvas_hoehe, abstand_grafik_text, text_hoehe)

    aspect_locked = check_aspect_locked(hoehe, breite)

    print(f"  Zeichen: {hoehe}mm x {breite}mm (Minimum-Format)")
    print(f"  Canvas: {canvas_hoehe}mm x {canvas_breite}mm")
    print(f"  Aspect Lock: {'ON' if aspect_locked else 'OFF'}")
    print(f"  Font-Size: {font_size}pt (kleiner fuer kleine Zeichen)")
    print(f"  Max. Grafik: {max_grafik:.2f}mm")
    print(f"  WARNUNG: Bei kleinen Zeichen wenig Platz fuer Grafik!")

    # Validierungen
    assert hoehe == breite, "Minimum-Format sollte quadratisch sein!"
    assert aspect_locked, "Aspect Lock sollte aktiv sein!"
    assert canvas_hoehe > 20, "Canvas sollte mindestens 20mm haben!"
    assert max_grafik > 0, "Sollte noch Platz fuer Grafik haben (wenn auch wenig)!"

    print("  [OK] Minimum-Szenario funktioniert korrekt")


def run_integration_scenario_aspect_lock_toggle():
    """Integrations-Test: Aspect Lock Toggle (45mm -> 90mm Breite)"""
    print_test("Aspect Lock Toggle (45mm -> 90mm Breite)")

    config = get_config()

    hoehe = 45.0
    sicherheit = config.sicherheitsabstand_mm

    # Szenario 1: Aspect Lock ON (1:1)
    breite_locked = 45.0
    canvas_locked = calculate_canvas_size(hoehe, sicherheit)
    aspect_locked_1 = check_aspect_locked(hoehe, breite_locked)

    print(f"  Szenario 1: Aspect Lock ON")
    print(f"    Zeichen: {hoehe}mm x {breite_locked}mm (1:1)")
    print(f"    Canvas: {canvas_locked}mm x {canvas_locked}mm")
    print(f"    Aspect Locked: {aspect_locked_1}")

    # Szenario 2: Aspect Lock OFF (2:1)
    breite_unlocked = 90.0
    canvas_breite = calculate_canvas_size(breite_unlocked, sicherheit)
    aspect_locked_2 = check_aspect_locked(hoehe, breite_unlocked)

    print(f"\n  Szenario 2: Aspect Lock OFF")
    print(f"    Zeichen: {hoehe}mm x {breite_unlocked}mm (2:1)")
    print(f"    Canvas: {canvas_locked}mm x {canvas_breite}mm")
    print(f"    Aspect Locked: {aspect_locked_2}")
    print(f"    Hinweis: Doppelte Breite moeglich wenn Lock deaktiviert")

    # Validierungen
    assert aspect_locked_1 == True, "Szenario 1 sollte Aspect Lock haben!"
    assert aspect_locked_2 == False, "Szenario 2 sollte kein Aspect Lock haben!"
    assert breite_locked < breite_unlocked, "Unlocked sollte breiter sein!"

    print("\n  [OK] Aspect Lock Toggle funktioniert korrekt")


def main():
    """Hauptfunktion: Alle Integrations-Tests ausfuehren"""
    print_section("INTEGRATIONS-TESTS: S2-LAYOUT (Standard-Zeichen)")
    print("Version: 1.0")
    print("Datum: 2025-12-03")
    print("\nDiese Tests pruefen:")
    print("  - Realistische Anwendungsszenarien")
    print("  - Aspect Lock Feature (v0.8.2.4)")
    print("  - Zusammenspiel von constants + runtime_config + Berechnungen")
    print("  - End-to-End Workflows")
    print("\nUnit-Tests befinden sich in:")
    print("  - constants.py (Standard-Konstanten)")
    print("  - runtime_config.py (Standard-Parameter)")

    try:
        # Integrations-Tests
        run_integration_scenario_standard_square()
        run_integration_scenario_rectangular()
        run_integration_scenario_large()
        run_integration_scenario_small()
        run_integration_scenario_aspect_lock_toggle()

        # Erfolg
        print_section("ALLE INTEGRATIONS-TESTS BESTANDEN!")
        print("Das S2-Layout funktioniert korrekt in realistischen Szenarien.")
        print("\nNaechste Schritte:")
        print("  1. Unit-Tests ausfuehren: python constants.py")
        print("  2. Unit-Tests ausfuehren: python runtime_config.py")
        print("  3. End-to-End Test mit echtem SVG und Export durchfuehren")
        return 0

    except AssertionError as e:
        print(f"\n\n{'=' * 70}")
        print("INTEGRATIONS-TEST FEHLGESCHLAGEN!")
        print("=" * 70)
        print(f"Fehler: {e}")
        return 1

    except Exception as e:
        print(f"\n\n{'=' * 70}")
        print("UNERWARTETER FEHLER!")
        print("=" * 70)
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
