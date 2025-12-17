#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_svg_loader.py - Unit-Tests fuer SVG-Loading-Funktionen

Testet die SVG-Loading-Funktionalitaet, insbesondere:
- SVG-Validierung mit validate_svg()
- Font-Extraktion mit extract_fonts_from_svg()
- Blanko-Zeichen-Erkennung in verschiedenen Kontexten

WICHTIG: Diese Tests stellen sicher, dass SVG-Dateien korrekt
validiert werden und Blanko-Zeichen korrekt als virtuelle Pfade
behandelt werden (v0.8.3 Fix).

Ausfuehrung: python dev-tools/testing/test_svg_loader.py
Datum: 2025-12-11
Version: 1.0
"""

import sys
from pathlib import Path
import tempfile
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from modules
from svg_loader_local import SVGLoaderLocal
from constants import (
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


def test_validate_svg_with_real_file():
    """
    Test 1: Prueft validate_svg() mit echter SVG-Datei
    """
    print_test("validate_svg() mit echter SVG-Datei")

    # Erstelle temporaere gueltige SVG-Datei
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <rect x="10" y="10" width="80" height="80" fill="red"/>
</svg>''')
        temp_file = Path(f.name)

    try:
        # Erstelle SVGLoaderLocal mit temp-Verzeichnis
        loader = SVGLoaderLocal(zeichen_dir=temp_file.parent)

        # Validiere SVG
        result = loader.validate_svg(temp_file)

        assert result == True, (
            "FEHLER: validate_svg() sollte True fuer gueltige SVG zurueckgeben"
        )

        print("  [OK] Gueltige SVG-Datei korrekt validiert")
        return True

    finally:
        # Loesche temp-Datei
        if temp_file.exists():
            os.unlink(temp_file)


def test_validate_svg_with_non_existent_file():
    """
    Test 2: Prueft validate_svg() mit nicht-existierender Datei
    """
    print_test("validate_svg() mit nicht-existierender Datei")

    # Erstelle SVGLoaderLocal
    loader = SVGLoaderLocal()

    # Nicht-existierende Datei
    non_existent = Path("/tmp/nicht_existent_12345.svg")

    # Validiere (sollte False zurueckgeben)
    result = loader.validate_svg(non_existent)

    assert result == False, (
        "FEHLER: validate_svg() sollte False fuer nicht-existierende Datei zurueckgeben"
    )

    print("  [OK] Nicht-existierende Datei korrekt abgelehnt")
    return True


def test_validate_svg_with_blanko():
    """
    Test 3: Prueft validate_svg() mit Blanko-Zeichen

    WICHTIG: v0.8.3 Fix - validate_svg() gibt False zurueck fuer Blanko
    (da sie keine echten Dateien sind), aber der Code MUSS vorher pruefen
    ob es ein Blanko ist (mit is_blanko_zeichen()) um validate_svg() zu ueberspringen
    """
    print_test("validate_svg() mit Blanko-Zeichen")

    loader = SVGLoaderLocal()

    # Blanko-Zeichen (virtuelle Pfade, keine echten Dateien)
    blanko_paths = [
        Path("BLANKO_ov_staerke"),
        Path("BLANKO_freitext"),
        Path(BLANKO_S1_LEER),
        Path(BLANKO_S1_LINIEN_STAERKE),
    ]

    for path in blanko_paths:
        # Zuerst pruefen ob es ein Blanko ist
        is_blanko = SVGLoaderLocal.is_blanko_zeichen(path)
        assert is_blanko == True, "FEHLER: {} sollte als Blanko erkannt werden".format(path)

        # WICHTIG: validate_svg() gibt False fuer Blanko zurueck
        # (da sie nicht als Datei existieren)
        result = loader.validate_svg(path)

        assert result == False, (
            "FEHLER: validate_svg({}) sollte False zurueckgeben\n"
            "HINWEIS: Blanko-Zeichen sind virtuelle Pfade, validate_svg() muss uebersprungen werden!"
        ).format(path)

        print("  [OK] {} -> is_blanko=True, validate_svg=False (korrekt)".format(path.stem))

    return True


def test_check_svg_fonts():
    """
    Test 4: Prueft check_svg_fonts() mit SVG-Datei
    """
    print_test("check_svg_fonts() mit Font-Familie")

    # Erstelle temporaere SVG-Datei mit Font-Familie
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <text x="10" y="50" font-family="Arial">Test</text>
    <text x="10" y="70" font-family="Roboto">Test2</text>
    <text x="10" y="90" style="font-family:Helvetica">Test3</text>
</svg>'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        temp_file = Path(f.name)

    try:
        loader = SVGLoaderLocal()

        # Pruefe Fonts
        has_text, fonts = loader.check_svg_fonts(temp_file)

        # Sollte Text-Elemente haben
        assert has_text == True, "FEHLER: SVG sollte Text-Elemente haben"

        # Erwartete Fonts
        expected_fonts = {'Arial', 'Roboto', 'Helvetica'}

        assert fonts == expected_fonts, (
            "FEHLER: check_svg_fonts() hat falsche Fonts extrahiert\n"
            "Erwartet: {}\n"
            "Erhalten: {}"
        ).format(expected_fonts, fonts)

        print("  [OK] Fonts korrekt extrahiert: {}".format(fonts))
        return True

    finally:
        if temp_file.exists():
            os.unlink(temp_file)


def test_check_svg_fonts_empty():
    """
    Test 5: Prueft check_svg_fonts() mit SVG ohne Fonts
    """
    print_test("check_svg_fonts() ohne Fonts")

    # SVG ohne Text/Fonts
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <rect x="10" y="10" width="80" height="80" fill="blue"/>
</svg>'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        temp_file = Path(f.name)

    try:
        loader = SVGLoaderLocal()
        has_text, fonts = loader.check_svg_fonts(temp_file)

        # Sollte KEINE Text-Elemente haben
        assert has_text == False, "FEHLER: SVG sollte keine Text-Elemente haben"

        assert fonts == set(), (
            "FEHLER: check_svg_fonts() sollte leeres Set zurueckgeben\n"
            "Erhalten: {}"
        ).format(fonts)

        print("  [OK] Keine Text-Elemente, leeres Font-Set korrekt")
        return True

    finally:
        if temp_file.exists():
            os.unlink(temp_file)


def test_svg_loader_init_with_nonexistent_dir():
    """
    Test 6: Prueft SVGLoaderLocal-Initialisierung mit nicht-existierendem Verzeichnis
    """
    print_test("SVGLoaderLocal mit nicht-existierendem Verzeichnis")

    # Erstelle temp-Pfad der NICHT existiert
    temp_dir = Path(tempfile.gettempdir()) / "test_svg_loader_{}".format(os.getpid())

    # Stelle sicher dass er nicht existiert
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)

    try:
        # Initialisiere Loader (sollte Verzeichnis erstellen)
        loader = SVGLoaderLocal(zeichen_dir=temp_dir)

        # Pruefe dass Verzeichnis erstellt wurde
        assert temp_dir.exists(), (
            "FEHLER: SVGLoaderLocal sollte nicht-existierendes Verzeichnis erstellen"
        )

        print("  [OK] Verzeichnis automatisch erstellt: {}".format(temp_dir))
        return True

    finally:
        # Cleanup
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)


def test_blanko_zeichen_comprehensive():
    """
    Test 7: Umfassender Test aller Blanko-Zeichen Funktionen
    """
    print_test("Umfassender Blanko-Test (is_blanko, has_staerke, is_s1_both)")

    test_cases = [
        # (path, is_blanko, has_staerke, is_s1_both)
        (Path("BLANKO_ov_staerke"), True, False, False),
        (Path("BLANKO_freitext"), True, False, False),
        (Path(BLANKO_S1_LEER), True, False, False),
        (Path(BLANKO_S1_LINIEN), True, False, True),
        (Path(BLANKO_S1_LINIEN_STAERKE), True, True, True),
        (Path("normale_datei.svg"), False, False, False),
    ]

    for path, exp_blanko, exp_staerke, exp_s1_both in test_cases:
        is_blanko = SVGLoaderLocal.is_blanko_zeichen(path)
        has_staerke = SVGLoaderLocal.has_staerke_anzeige(path)
        is_s1_both = SVGLoaderLocal.is_blanko_s1_both(path)

        assert is_blanko == exp_blanko, (
            "FEHLER: is_blanko_zeichen({}) = {}, erwartet {}".format(
                path, is_blanko, exp_blanko
            )
        )

        assert has_staerke == exp_staerke, (
            "FEHLER: has_staerke_anzeige({}) = {}, erwartet {}".format(
                path, has_staerke, exp_staerke
            )
        )

        assert is_s1_both == exp_s1_both, (
            "FEHLER: is_blanko_s1_both({}) = {}, erwartet {}".format(
                path, is_s1_both, exp_s1_both
            )
        )

        print("  [OK] {} -> blanko={}, staerke={}, s1_both={}".format(
            path.stem, is_blanko, has_staerke, is_s1_both
        ))

    return True


def run_all_tests():
    """Fuehrt alle Tests aus und gibt Zusammenfassung aus"""
    print_section("SVG-LOADER UNIT TESTS (v1.0)")
    print("Testet SVG-Loading-Funktionen und v0.8.3 Blanko-Fixes")

    tests = [
        test_validate_svg_with_real_file,
        test_validate_svg_with_non_existent_file,
        test_validate_svg_with_blanko,
        test_check_svg_fonts,
        test_check_svg_fonts_empty,
        test_svg_loader_init_with_nonexistent_dir,
        test_blanko_zeichen_comprehensive,
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
