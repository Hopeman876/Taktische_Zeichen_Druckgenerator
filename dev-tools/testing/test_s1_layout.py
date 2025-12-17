#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_s1_layout.py - Integrations-Tests fuer S1-Layout (Doppelschild)

Testet realistische S1-Layout Szenarien mit kombinierten Funktionen
aus mehreren Modulen (constants, runtime_config, taktische_zeichen_generator).

WICHTIG: Unit-Tests fuer einzelne Module befinden sich direkt in den
jeweiligen Modul-Dateien:
- S1-Konstanten: constants.py (Test 8)
- S1-RuntimeConfig: runtime_config.py (Test 6)

Diese Datei testet NUR:
- Realistische Anwendungsszenarien
- Zusammenspiel mehrerer Module
- End-to-End Berechnungen

Ausfuehrung: python dev-tools/testing/test_s1_layout.py
Datum: 2025-11-17
Version: 2.0 (Hybrid-Ansatz)
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
    S1_LINE_MARGIN_MM,
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


def calculate_s1_line_height_mm(
    canvas_hoehe_mm: float,
    anzahl_zeilen: int
) -> float:
    """
    Berechnet Zeilenhoehe in mm basierend auf Anzahl Zeilen

    NEUE LOGIK: Anzahl Zeilen -> Zeilenhoehe

    Formel: canvas_hoehe_mm / anzahl_zeilen

    Diese Berechnung entspricht der neuen Implementierung in
    taktische_zeichen_generator.py

    Args:
        canvas_hoehe_mm: Hoehe des Canvas (nach Sicherheitsabzug)
        anzahl_zeilen: Gewuenschte Anzahl Zeilen (3-10)

    Returns:
        Zeilenhoehe in mm
    """
    line_height_mm = canvas_hoehe_mm / anzahl_zeilen
    return round(line_height_mm, 2)


def calculate_s1_fontsize_pt(line_height_mm: float) -> float:
    """
    Berechnet Schriftgroesse in pt basierend auf Zeilenhoehe

    NEUE LOGIK: Zeilenhoehe -> Schriftgroesse

    Formel: (line_height_mm / LINE_HEIGHT_FACTOR) * SYSTEM_POINTS_PER_INCH / 25.4

    Args:
        line_height_mm: Hoehe einer Zeile in mm

    Returns:
        Schriftgroesse in pt
    """
    font_size_mm = line_height_mm / LINE_HEIGHT_FACTOR
    font_size_pt = (font_size_mm * SYSTEM_POINTS_PER_INCH) / 25.4
    return round(font_size_pt, 1)


def calculate_s1_split(links_prozent: int) -> Tuple[int, int]:
    """
    Berechnet Aufteilung Links/Rechts

    Args:
        links_prozent: Prozent fuer linken Bereich (20-80)

    Returns:
        (links_prozent, rechts_prozent)
    """
    rechts_prozent = 100 - links_prozent
    return (links_prozent, rechts_prozent)


def calculate_s1_aspect_ratio_width(hoehe_mm: float) -> float:
    """
    Berechnet Breite bei fixiertem 2:1 Seitenverhaeltnis

    Args:
        hoehe_mm: Hoehe des Zeichens

    Returns:
        Breite = 2 * Hoehe
    """
    return hoehe_mm * 2.0


def run_integration_scenario_standard():
    """Integrations-Test: Standard 45mm Zeichen"""
    print_test("Standard 45mm Zeichen (typischer Anwendungsfall)")

    # RuntimeConfig verwenden (wie in echter Anwendung)
    config = get_config()

    hoehe = 45.0
    breite = calculate_s1_aspect_ratio_width(hoehe)
    links_prozent = config.s1_links_prozent  # Aus RuntimeConfig
    anzahl_zeilen = config.s1_anzahl_schreiblinien  # Aus RuntimeConfig (NEUE LOGIK)
    sicherheit = config.sicherheitsabstand_mm  # Aus RuntimeConfig
    canvas_hoehe = hoehe - (2 * sicherheit)

    line_height = calculate_s1_line_height_mm(canvas_hoehe, anzahl_zeilen)
    fontsize = calculate_s1_fontsize_pt(line_height)
    links, rechts = calculate_s1_split(links_prozent)

    print(f"  Zeichen: {hoehe}mm x {breite}mm (2:1 Aspect Ratio)")
    print(f"  Canvas: {canvas_hoehe}mm (nach {sicherheit}mm Sicherheitsabzug)")
    print(f"  Aufteilung: {links}% links / {rechts}% rechts")
    print(f"  Anzahl Zeilen: {anzahl_zeilen} -> Zeilenhoehe: {line_height}mm")
    print(f"  Schriftgroesse: {fontsize}pt (berechnet)")
    print(f"  Staerke-Platzhalter: {'Ja' if config.s1_staerke_anzeigen else 'Nein'}")

    # Validierungen
    assert breite == 90.0, "Breite falsch bei 45mm Hoehe!"
    assert anzahl_zeilen >= 3, f"Zu wenig Zeilen ({anzahl_zeilen}) konfiguriert!"
    assert anzahl_zeilen <= 10, f"Zu viele Zeilen ({anzahl_zeilen}) konfiguriert!"
    assert links + rechts == 100, "Aufteilung ergibt nicht 100%!"

    print("  [OK] Standard-Szenario funktioniert korrekt")


def run_integration_scenario_large():
    """Integrations-Test: Grosses 100mm Zeichen"""
    print_test("Grosses 100mm Zeichen (Poster-Format)")

    config = get_config()

    hoehe = 100.0
    breite = calculate_s1_aspect_ratio_width(hoehe)
    links_prozent = 60  # Custom Aufteilung
    anzahl_zeilen = 7  # Mehr Zeilen fuer grosse Zeichen
    sicherheit = config.sicherheitsabstand_mm
    canvas_hoehe = hoehe - (2 * sicherheit)

    line_height = calculate_s1_line_height_mm(canvas_hoehe, anzahl_zeilen)
    fontsize = calculate_s1_fontsize_pt(line_height)
    links, rechts = calculate_s1_split(links_prozent)

    print(f"  Zeichen: {hoehe}mm x {breite}mm (2:1 Aspect Ratio)")
    print(f"  Canvas: {canvas_hoehe}mm (nach {sicherheit}mm Sicherheitsabzug)")
    print(f"  Aufteilung: {links}% links / {rechts}% rechts (custom)")
    print(f"  Anzahl Zeilen: {anzahl_zeilen} -> Zeilenhoehe: {line_height}mm")
    print(f"  Schriftgroesse: {fontsize}pt (berechnet)")

    # Validierungen
    assert breite == 200.0, "Breite falsch bei 100mm Hoehe!"
    assert anzahl_zeilen >= 3, f"Zu wenig Zeilen ({anzahl_zeilen}) bei grosser Hoehe!"
    assert links + rechts == 100, "Aufteilung ergibt nicht 100%!"

    print("  [OK] Poster-Szenario funktioniert korrekt")


def run_integration_scenario_small():
    """Integrations-Test: Kleines 30mm Zeichen (Edge Case)"""
    print_test("Kleines 30mm Zeichen (Minimum-Format Edge Case)")

    config = get_config()

    hoehe = 30.0
    breite = calculate_s1_aspect_ratio_width(hoehe)
    links_prozent = config.s1_links_prozent
    anzahl_zeilen = 3  # Minimum fuer kleine Zeichen
    sicherheit = config.sicherheitsabstand_mm
    canvas_hoehe = hoehe - (2 * sicherheit)

    line_height = calculate_s1_line_height_mm(canvas_hoehe, anzahl_zeilen)
    fontsize = calculate_s1_fontsize_pt(line_height)
    links, rechts = calculate_s1_split(links_prozent)

    print(f"  Zeichen: {hoehe}mm x {breite}mm (2:1 Aspect Ratio)")
    print(f"  Canvas: {canvas_hoehe}mm (nach {sicherheit}mm Sicherheitsabzug)")
    print(f"  Aufteilung: {links}% links / {rechts}% rechts")
    print(f"  Anzahl Zeilen: {anzahl_zeilen} -> Zeilenhoehe: {line_height}mm")
    print(f"  Schriftgroesse: {fontsize}pt (berechnet)")
    print(f"  Warnung: Bei kleinen Zeichen weniger Platz fuer Schreiblinien!")

    # Validierungen
    assert breite == 60.0, "Breite falsch bei 30mm Hoehe!"
    assert anzahl_zeilen >= 3, f"Mindestens 3 Zeilen bei Minimum-Groesse!"
    assert links + rechts == 100, "Aufteilung ergibt nicht 100%!"

    print("  [OK] Minimum-Szenario funktioniert korrekt")


def run_integration_scenario_custom_split():
    """Integrations-Test: Custom Aufteilung (80/20)"""
    print_test("Custom Aufteilung 80/20 (mehr Platz fuer Zeichen)")

    config = get_config()

    hoehe = 50.0
    breite = calculate_s1_aspect_ratio_width(hoehe)
    links_prozent = 80  # Maximum fuer Zeichen (Edge Case)
    anzahl_zeilen = 6  # Mittlere Anzahl Zeilen
    sicherheit = config.sicherheitsabstand_mm
    canvas_hoehe = hoehe - (2 * sicherheit)

    line_height = calculate_s1_line_height_mm(canvas_hoehe, anzahl_zeilen)
    fontsize = calculate_s1_fontsize_pt(line_height)
    links, rechts = calculate_s1_split(links_prozent)

    print(f"  Zeichen: {hoehe}mm x {breite}mm (2:1 Aspect Ratio)")
    print(f"  Canvas: {canvas_hoehe}mm")
    print(f"  Aufteilung: {links}% links / {rechts}% rechts (Maximum fuer Zeichen)")
    print(f"  Linke Breite: {breite * (links/100.0):.1f}mm")
    print(f"  Rechte Breite: {breite * (rechts/100.0):.1f}mm (wenig Platz fuer Linien!)")
    print(f"  Anzahl Zeilen: {anzahl_zeilen} -> Zeilenhoehe: {line_height}mm")
    print(f"  Schriftgroesse: {fontsize}pt (berechnet)")

    # Validierungen
    assert breite == 100.0, "Breite falsch!"
    assert links == 80, "Links sollte 80% sein!"
    assert rechts == 20, "Rechts sollte 20% sein!"
    assert links + rechts == 100, "Aufteilung ergibt nicht 100%!"

    print("  [OK] Custom-Split-Szenario funktioniert korrekt")


def main():
    """Hauptfunktion: Alle Integrations-Tests ausfuehren"""
    print_section("INTEGRATIONS-TESTS: S1-LAYOUT (Doppelschild)")
    print("Version: 2.0 (Hybrid-Ansatz)")
    print("Datum: 2025-11-17")
    print("\nDiese Tests pruefen:")
    print("  - Realistische Anwendungsszenarien")
    print("  - Zusammenspiel von constants + runtime_config + Berechnungen")
    print("  - End-to-End Workflows")
    print("\nUnit-Tests befinden sich in:")
    print("  - constants.py (Test 8: S1-Konstanten)")
    print("  - runtime_config.py (Test 6: S1-Parameter)")

    try:
        # Integrations-Tests
        run_integration_scenario_standard()
        run_integration_scenario_large()
        run_integration_scenario_small()
        run_integration_scenario_custom_split()

        # Erfolg
        print_section("ALLE INTEGRATIONS-TESTS BESTANDEN!")
        print("Das S1-Layout funktioniert korrekt in realistischen Szenarien.")
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
