#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pdf_exporter.py - Unit-Tests fuer PDF-Export-Funktionen

Testet die PDF-Export-Funktionalitaet, insbesondere:
- create_pdf_filename() Funktionssignatur und Ausgabe
- Dateinamen-Konventionen
- Keine Namenskonflikte zwischen constants.py und pdf_exporter.py

WICHTIG: Diese Tests verhindern Regression des v0.8.3 Bugs, bei dem
eine lokale Funktion create_pdf_filename() den Import ueberschrieben hat.

Ausfuehrung: python dev-tools/testing/test_pdf_exporter.py
Datum: 2025-12-11
Version: 1.0
"""

import sys
from pathlib import Path
from datetime import datetime
import inspect

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from modules
from constants import create_pdf_filename, EXPORT_TIMESTAMP_FORMAT

# HINWEIS: pdf_exporter wird nur bei Bedarf importiert (wegen PIL-Abhaengigkeit)


def print_section(title: str):
    """Formatierte Sektion-Ueberschrift ausgeben"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_test(test_name: str):
    """Formatierte Test-Ueberschrift ausgeben"""
    print("\n[TEST] {}".format(test_name))


def test_create_pdf_filename_signature():
    """
    Test 1: Prueft create_pdf_filename() Funktionssignatur

    WICHTIG: Stellt sicher, dass die Funktion die richtige Signatur hat
    und nicht durch eine lokale Funktion ueberschrieben wurde (v0.8.3 Bug)
    """
    print_test("create_pdf_filename() Signatur")

    # Hole Funktion aus constants.py
    sig = inspect.signature(create_pdf_filename)
    params = list(sig.parameters.keys())

    # Erwartete Parameter (aus constants.py)
    expected_params = [
        'timestamp',
        'export_format',
        'start_idx',
        'end_idx',
        'file_idx',
        'total_files'
    ]

    # Vergleiche
    assert params == expected_params, (
        "FEHLER: create_pdf_filename() hat falsche Signatur!\n"
        "Erwartet: {}\n"
        "Erhalten: {}\n"
        "HINWEIS: Pruefe ob lokale Funktion den Import ueberschreibt!"
    ).format(expected_params, params)

    print("  [OK] Signatur korrekt: {}".format(params))
    return True


def test_create_pdf_filename_output():
    """
    Test 2: Prueft create_pdf_filename() Ausgabe-Format

    Testet ob die Funktion korrekte Dateinamen generiert
    """
    print_test("create_pdf_filename() Ausgabe-Format")

    # Test-Parameter
    timestamp = "2025-12-11_01-23"
    export_format = "Schnittbogen"
    start_idx = 1
    end_idx = 50
    file_idx = 1
    total_files = 2

    # Funktion aufrufen
    result = create_pdf_filename(
        timestamp=timestamp,
        export_format=export_format,
        start_idx=start_idx,
        end_idx=end_idx,
        file_idx=file_idx,
        total_files=total_files
    )

    # Erwartetes Format (aus EXPORT_PDF_FILENAME_TEMPLATE)
    expected = "2025-12-11_01-23_Schnittbogen_Zeichen_1_bis_50_Datei_1_von_2.pdf"

    assert result == expected, (
        "FEHLER: Falscher Dateiname!\n"
        "Erwartet: {}\n"
        "Erhalten: {}"
    ).format(expected, result)

    print("  [OK] Dateiname korrekt: {}".format(result))
    return True


def test_create_pdf_filename_einzelzeichen():
    """
    Test 3: Prueft create_pdf_filename() fuer Einzelzeichen-PDFs
    """
    print_test("create_pdf_filename() Einzelzeichen-Format")

    timestamp = "2025-12-11_02-30"
    export_format = "Einzelzeichen"
    start_idx = 10
    end_idx = 25
    file_idx = 2
    total_files = 3

    result = create_pdf_filename(
        timestamp=timestamp,
        export_format=export_format,
        start_idx=start_idx,
        end_idx=end_idx,
        file_idx=file_idx,
        total_files=total_files
    )

    expected = "2025-12-11_02-30_Einzelzeichen_Zeichen_10_bis_25_Datei_2_von_3.pdf"

    assert result == expected, (
        "FEHLER: Falscher Dateiname!\n"
        "Erwartet: {}\n"
        "Erhalten: {}"
    ).format(expected, result)

    print("  [OK] Dateiname korrekt: {}".format(result))
    return True


def test_no_name_collision():
    """
    Test 4: Prueft dass kein Namenskonflikt zwischen constants und pdf_exporter existiert

    WICHTIG: Verhindert v0.8.3 Bug, bei dem lokale Funktion Import ueberschrieb
    """
    print_test("Keine Namenskonflikte zwischen Modulen")

    try:
        import pdf_exporter
    except ImportError as e:
        print("  [SKIP] pdf_exporter kann nicht importiert werden: {}".format(e))
        print("  [INFO] Test wird uebersprungen (erfordert vollstaendige Abhaengigkeiten)")
        return True

    # Pruefe ob pdf_exporter._create_test_pdf_filename existiert (neue interne Funktion)
    assert hasattr(pdf_exporter, '_create_test_pdf_filename'), (
        "FEHLER: _create_test_pdf_filename() nicht in pdf_exporter gefunden!\n"
        "HINWEIS: Lokale Test-Funktion sollte '_create_test_pdf_filename' heissen"
    )

    # Pruefe dass pdf_exporter.create_pdf_filename der Import ist (nicht lokal definiert)
    # Die importierte Funktion sollte aus constants.py kommen
    import constants
    assert pdf_exporter.create_pdf_filename == constants.create_pdf_filename, (
        "FEHLER: pdf_exporter.create_pdf_filename ist nicht der Import aus constants.py!\n"
        "HINWEIS: Lokale Funktion ueberschreibt Import"
    )

    print("  [OK] Kein Namenskonflikt - Import korrekt")
    print("  [OK] _create_test_pdf_filename() existiert fuer Tests")
    return True


def test_timestamp_format():
    """
    Test 5: Prueft dass Timestamp-Format konsistent mit EXPORT_TIMESTAMP_FORMAT ist
    """
    print_test("Timestamp-Format Konsistenz")

    # Erzeuge Timestamp mit konstantem Format
    test_time = datetime(2025, 12, 11, 14, 30, 45)
    timestamp = test_time.strftime(EXPORT_TIMESTAMP_FORMAT)

    # Erwartetes Format (OHNE Sekunden: %Y-%m-%d_%H-%M)
    expected_format = "2025-12-11_14-30"

    assert timestamp == expected_format, (
        "FEHLER: EXPORT_TIMESTAMP_FORMAT ist inkonsistent!\n"
        "Erwartet: {}\n"
        "Erhalten: {}"
    ).format(expected_format, timestamp)

    print("  [OK] Timestamp-Format: {} = '{}'".format(EXPORT_TIMESTAMP_FORMAT, timestamp))
    return True


def run_all_tests():
    """Fuehrt alle Tests aus und gibt Zusammenfassung aus"""
    print_section("PDF-EXPORTER UNIT TESTS (v1.0)")
    print("Testet create_pdf_filename() und verhindert v0.8.3 Regression")

    tests = [
        test_create_pdf_filename_signature,
        test_create_pdf_filename_output,
        test_create_pdf_filename_einzelzeichen,
        test_no_name_collision,
        test_timestamp_format,
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
