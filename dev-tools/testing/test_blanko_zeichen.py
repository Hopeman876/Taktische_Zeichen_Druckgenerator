#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_blanko_zeichen.py - Unit-Tests fuer Blanko-Zeichen Handling

Testet das korrekte Handling von Blanko-Zeichen (virtuelle SVG-Pfade):
- SVGLoaderLocal.is_blanko_zeichen()
- TaktischeZeichenGenerator._is_pseudo_svg()
- TaktischeZeichenGenerator._sanitize_svg_content()

WICHTIG: Diese Tests verhindern Regression des v0.8.3 Bugs, bei dem
Blanko-Zeichen als echte Dateien behandelt wurden und zu
"No such file or directory" Fehlern fuehrten.

Ausfuehrung: python dev-tools/testing/test_blanko_zeichen.py
Datum: 2025-12-11
Version: 1.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from modules
from svg_loader_local import SVGLoaderLocal
from constants import (
    BLANKO_SVG_PATH,
    BLANKO_S1_LEER,
    BLANKO_S1_LINIEN,
    BLANKO_S1_LINIEN_STAERKE,
)


def print_section(title: str):
    """Formatierte Sektion-Ueberschrift ausgeben"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_test(test_name: str):
    """Formatierte Test-Ueberschrift ausgeben"""
    print("\n[TEST] {}".format(test_name))


def test_is_blanko_zeichen_standard():
    """
    Test 1: Prueft is_blanko_zeichen() fuer Standard-Blanko (BLANKO_modus)
    """
    print_test("is_blanko_zeichen() - Standard-Blanko")

    # Standard-Blanko-Zeichen (BLANKO_modus Format)
    test_cases = [
        (Path("BLANKO_ov_staerke"), True),
        (Path("BLANKO_ort_staerke"), True),
        (Path("BLANKO_schreiblinie_staerke"), True),
        (Path("BLANKO_ruf"), True),
        (Path("BLANKO_ohne_text"), True),
        (Path("BLANKO_freitext"), True),
        (Path("BLANKO_dateiname"), True),
    ]

    for path, expected in test_cases:
        result = SVGLoaderLocal.is_blanko_zeichen(path)
        assert result == expected, (
            "FEHLER: is_blanko_zeichen({}) = {}, erwartet {}".format(
                path, result, expected
            )
        )
        print("  [OK] {} -> {}".format(path.stem, result))

    return True


def test_is_blanko_zeichen_s1():
    """
    Test 2: Prueft is_blanko_zeichen() fuer S1-Blanko-Varianten
    """
    print_test("is_blanko_zeichen() - S1-Blanko")

    # S1-Blanko-Zeichen
    test_cases = [
        (Path(BLANKO_S1_LEER), True),
        (Path(BLANKO_S1_LINIEN), True),
        (Path(BLANKO_S1_LINIEN_STAERKE), True),
    ]

    for path, expected in test_cases:
        result = SVGLoaderLocal.is_blanko_zeichen(path)
        assert result == expected, (
            "FEHLER: is_blanko_zeichen({}) = {}, erwartet {}".format(
                path, result, expected
            )
        )
        print("  [OK] {} -> {}".format(path.stem, result))

    return True


def test_is_blanko_zeichen_normale_zeichen():
    """
    Test 3: Prueft is_blanko_zeichen() fuer normale Zeichen (nicht Blanko)
    """
    print_test("is_blanko_zeichen() - Normale Zeichen")

    # Normale Zeichen (keine Blanko)
    test_cases = [
        (Path("normale_datei.svg"), False),
        (Path("THW_Bergungsgruppe.svg"), False),
        (Path("Feuerwehr_Loeschzug.svg"), False),
        # HINWEIS: "BLANKO" ohne Unterstrich wird auch als Blanko erkannt (startswith)
        (Path("blanko_test.svg"), False),  # Kleingeschrieben
        (Path("test_BLANKO.svg"), False),  # BLANKO nicht am Anfang
    ]

    for path, expected in test_cases:
        result = SVGLoaderLocal.is_blanko_zeichen(path)
        assert result == expected, (
            "FEHLER: is_blanko_zeichen({}) = {}, erwartet {}".format(
                path, result, expected
            )
        )
        print("  [OK] {} -> {}".format(path.stem, result))

    return True


def test_has_staerke_anzeige():
    """
    Test 4: Prueft has_staerke_anzeige() fuer S1-Blanko
    """
    print_test("has_staerke_anzeige()")

    test_cases = [
        (Path(BLANKO_S1_LEER), False),  # Ohne Staerke
        (Path(BLANKO_S1_LINIEN), False),  # Ohne Staerke
        (Path(BLANKO_S1_LINIEN_STAERKE), True),  # MIT Staerke
        (Path("BLANKO_ov_staerke"), False),  # Standard-Blanko (kein S1)
        (Path("normale_datei.svg"), False),  # Normales Zeichen
    ]

    for path, expected in test_cases:
        result = SVGLoaderLocal.has_staerke_anzeige(path)
        assert result == expected, (
            "FEHLER: has_staerke_anzeige({}) = {}, erwartet {}".format(
                path, result, expected
            )
        )
        print("  [OK] {} -> {}".format(path.stem, result))

    return True


def test_is_blanko_s1_both():
    """
    Test 5: Prueft is_blanko_s1_both() fuer S1 mit beidseitigen Schreiblinien
    """
    print_test("is_blanko_s1_both()")

    test_cases = [
        (Path(BLANKO_S1_LEER), False),  # Ohne Linien
        (Path(BLANKO_S1_LINIEN), True),  # MIT Linien
        (Path(BLANKO_S1_LINIEN_STAERKE), True),  # MIT Linien + Staerke
        (Path("BLANKO_ov_staerke"), False),  # Standard-Blanko
    ]

    for path, expected in test_cases:
        result = SVGLoaderLocal.is_blanko_s1_both(path)
        assert result == expected, (
            "FEHLER: is_blanko_s1_both({}) = {}, erwartet {}".format(
                path, result, expected
            )
        )
        print("  [OK] {} -> {}".format(path.stem, result))

    return True


def test_get_blanko_modus():
    """
    Test 6: Prueft get_blanko_modus() fuer Modus-Extraktion
    """
    print_test("get_blanko_modus()")

    test_cases = [
        (Path("BLANKO_ov_staerke"), "ov_staerke"),
        (Path("BLANKO_ort_staerke"), "ort_staerke"),
        (Path("BLANKO_ruf"), "ruf"),
        (Path("BLANKO_freitext"), "freitext"),
        (Path(BLANKO_S1_LEER), None),  # S1 hat keinen Modus
        (Path(BLANKO_S1_LINIEN), None),  # S1 hat keinen Modus
        (Path("normale_datei.svg"), None),  # Kein Blanko
    ]

    for path, expected in test_cases:
        result = SVGLoaderLocal.get_blanko_modus(path)
        assert result == expected, (
            "FEHLER: get_blanko_modus({}) = {}, erwartet {}".format(
                path, result, expected
            )
        )
        print("  [OK] {} -> {}".format(path.stem, result))

    return True


def test_get_blanko_display_name():
    """
    Test 7: Prueft get_blanko_display_name() fuer schoene Namen
    """
    print_test("get_blanko_display_name()")

    test_cases = [
        (Path("BLANKO_ov_staerke"), "Leer - OV + Staerke"),
        (Path("BLANKO_ort_staerke"), "Leer - Ort + Staerke"),
        (Path("BLANKO_ruf"), "Leer - Rufname"),
        (Path(BLANKO_S1_LEER), "S1 Leer"),
        (Path(BLANKO_S1_LINIEN), "S1 mit Linien"),
        (Path(BLANKO_S1_LINIEN_STAERKE), "S1 mit Linien + Staerke"),
    ]

    for path, expected in test_cases:
        result = SVGLoaderLocal.get_blanko_display_name(path)
        assert result == expected, (
            "FEHLER: get_blanko_display_name({}) = '{}', erwartet '{}'".format(
                path, result, expected
            )
        )
        print("  [OK] {} -> '{}'".format(path.stem, result))

    return True


def test_is_pseudo_svg_with_blanko():
    """
    Test 8: Prueft _is_pseudo_svg() mit Blanko-Zeichen

    WICHTIG: Verhindert v0.8.3 Bug - Blanko sollten NICHT als Pseudo-SVG erkannt werden
    """
    print_test("_is_pseudo_svg() mit Blanko-Zeichen")

    try:
        from taktische_zeichen_generator import TaktischeZeichenGenerator
        generator = TaktischeZeichenGenerator()
    except ImportError as e:
        print("  [SKIP] TaktischeZeichenGenerator kann nicht importiert werden: {}".format(e))
        print("  [INFO] Test wird uebersprungen (erfordert vollstaendige Abhaengigkeiten)")
        return True

    # Blanko-Zeichen sollten NICHT als Pseudo-SVG erkannt werden
    blanko_paths = [
        Path("BLANKO_ov_staerke"),
        Path("BLANKO_freitext"),
        Path(BLANKO_S1_LEER),
    ]

    for path in blanko_paths:
        result = generator._is_pseudo_svg(path)
        assert result == False, (
            "FEHLER: _is_pseudo_svg({}) = True, erwartet False\n"
            "HINWEIS: Blanko-Zeichen sind virtuelle Pfade, keine echten SVGs!"
        ).format(path)
        print("  [OK] {} -> False (korrekt)".format(path.stem))

    return True


def test_sanitize_svg_content_with_blanko():
    """
    Test 9: Prueft _sanitize_svg_content() mit Blanko-Zeichen

    WICHTIG: Verhindert v0.8.3 Bug - Blanko sollten NICHT gelesen werden
    """
    print_test("_sanitize_svg_content() mit Blanko-Zeichen")

    try:
        from taktische_zeichen_generator import TaktischeZeichenGenerator
        generator = TaktischeZeichenGenerator()
    except ImportError as e:
        print("  [SKIP] TaktischeZeichenGenerator kann nicht importiert werden: {}".format(e))
        print("  [INFO] Test wird uebersprungen (erfordert vollstaendige Abhaengigkeiten)")
        return True

    # Blanko-Zeichen sollten unveraendert zurueckgegeben werden (kein Lesen)
    blanko_paths = [
        Path("BLANKO_ov_staerke"),
        Path(BLANKO_S1_LINIEN_STAERKE),
    ]

    for path in blanko_paths:
        result = generator._sanitize_svg_content(path)
        assert result == path, (
            "FEHLER: _sanitize_svg_content({}) != original path\n"
            "HINWEIS: Blanko-Zeichen sollten unveraendert zurueckgegeben werden!"
        ).format(path)
        print("  [OK] {} -> unveraendert (korrekt)".format(path.stem))

    return True


def run_all_tests():
    """Fuehrt alle Tests aus und gibt Zusammenfassung aus"""
    print_section("BLANKO-ZEICHEN UNIT TESTS (v1.0)")
    print("Testet Blanko-Zeichen Handling und verhindert v0.8.3 Regression")

    tests = [
        test_is_blanko_zeichen_standard,
        test_is_blanko_zeichen_s1,
        test_is_blanko_zeichen_normale_zeichen,
        test_has_staerke_anzeige,
        test_is_blanko_s1_both,
        test_get_blanko_modus,
        test_get_blanko_display_name,
        test_is_pseudo_svg_with_blanko,
        test_sanitize_svg_content_with_blanko,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print("\n[FEHLER] Test fehlgeschlagen:")
            print(str(e))
            failed += 1
        except Exception as e:
            print("\n[FEHLER] Unerwarteter Fehler:")
            print(str(e))
            failed += 1

    # Zusammenfassung
    print_section("ZUSAMMENFASSUNG")
    print("Tests bestanden: {}".format(passed))
    print("Tests fehlgeschlagen: {}".format(failed))
    print("Gesamt: {}".format(len(tests)))

    if failed == 0:
        print("\n[OK] Alle Tests bestanden!")
        return 0
    else:
        print("\n[FEHLER] {} Test(s) fehlgeschlagen!".format(failed))
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
