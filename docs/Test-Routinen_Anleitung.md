# Test-Routinen - User-Dokumentation

**Zielgruppe:** Programmierer/Entwickler
**Version:** 2.0
**Datum:** 2025-12-03

---

## 📖 Inhaltsverzeichnis

1. [Was sind Test-Routinen?](#was-sind-test-routinen)
2. [Welche Module haben Test-Routinen?](#welche-module-haben-test-routinen)
3. [Dedizierte Test-Dateien](#dedizierte-test-dateien)
4. [Wie führe ich Test-Routinen aus?](#wie-führe-ich-test-routinen-aus)
5. [Was sagen mir die Test-Ergebnisse?](#was-sagen-mir-die-test-ergebnisse)
6. [Wann sollte ich Test-Routinen nutzen?](#wann-sollte-ich-test-routinen-nutzen)
7. [Wie erweitere ich Test-Routinen?](#wie-erweitere-ich-test-routinen)
8. [Troubleshooting](#troubleshooting)

---

## Was sind Test-Routinen?

Test-Routinen sind **Python-Code am Ende jeder Modul-Datei**, der automatisch ausgeführt wird, wenn du das Modul direkt startest:

```python
if __name__ == "__main__":
    # Test-Code hier
    print("Test läuft...")
```

### Funktionsweise:

- **Direkte Ausführung:** `python modul.py` → Test-Code läuft
- **Import:** `from modul import function` → Test-Code läuft **NICHT**

### Vorteile:

✅ **Schnelles Testen** während der Entwicklung
✅ **Keine extra Test-Dateien** nötig (bei einfachen Tests)
✅ **Dokumentation** durch Beispiele
✅ **Debugging** einzelner Module
✅ **Regression Testing** - schnell prüfen, ob Änderungen etwas kaputt gemacht haben

---

## Welche Module haben Test-Routinen?

### Core Module (Pure Python - immer ausführbar):

| Modul | Tests | Status | Beschreibung |
|-------|-------|--------|--------------|
| **constants.py** | 8 Tests | ✅ Vollständig | Konstanten, Berechnungen, S1-Layout |
| **runtime_config.py** | 6 Tests | ✅ Vollständig | RuntimeConfig, Singleton, S1-Parameter |
| **settings_manager.py** | 4 Tests | ✅ Vollständig | Settings laden/speichern, Validierung |

**Gesamt Core: 18 Tests** - Keine Dependencies, immer ausführbar

### Export/Generator Module (benötigen PIL/PyQt6/Wand):

| Modul | Tests | Status | Dependencies |
|-------|-------|--------|--------------|
| **font_manager.py** | 4 Tests | ✅ Vorhanden | PyQt6 |
| **pdf_exporter.py** | 2 Tests | ✅ Vorhanden | PIL (Einzelzeichen, Schnittbogen) |
| **text_overlay.py** | 1 Test | ✅ Vorhanden | PIL |
| **print_preparer.py** | 1 Test | ✅ Vorhanden | PIL |
| **svg_loader_local.py** | 2 Tests | ✅ Vorhanden | Wand |
| **validation_manager.py** | 3 Tests | ✅ Vorhanden | PyQt6 |
| **taktische_zeichen_generator.py** | 1 Test | ✅ Vorhanden | PIL, Wand |

**Gesamt Export: ~14 Tests** - Benötigen PIL, PyQt6, Wand

---

## Dedizierte Test-Dateien

### Integrations-Tests in `dev-tools/testing/`:

| Datei | Tests | Status | Beschreibung |
|-------|-------|--------|--------------|
| **test_s1_layout.py** | 4 Tests | ✅ Vollständig | S1-Layout (Doppelschild, 2:1) |
| **test_s2_layout.py** | 5 Tests | ✅ Vollständig | S2-Layout (Standard, Aspect Lock) |
| **test_cut_lines.py** | ? Tests | ⚠️ Vorhanden | Schnittlinien (benötigt PIL) |

**Gesamt Integrations-Tests: 9+ Tests**

### S1-Layout Tests (test_s1_layout.py):

1. Standard 45mm Zeichen (typischer Anwendungsfall)
2. Großes 100mm Zeichen (Poster-Format)
3. Kleines 30mm Zeichen (Minimum-Format Edge Case)
4. Custom Aufteilung 80/20 (mehr Platz für Zeichen)

### S2-Layout Tests (test_s2_layout.py) - **NEU v2.0**:

1. Standard quadratisch (45×45mm, Aspect Lock ON)
2. Rechteckig (60×40mm, Aspect Lock OFF)
3. Großes Zeichen (100×80mm)
4. Kleines Zeichen (30×30mm, Edge Case)
5. Aspect Lock Toggle (45mm → 90mm Breite)

**Total verfügbare Tests: ~41+ Tests**

---

## Wie führe ich Test-Routinen aus?

### Grundlegende Ausführung:

#### Core Module (immer ausführbar):

```bash
# Im Projekt-Root-Verzeichnis
python constants.py          # 8 Tests
python runtime_config.py     # 6 Tests
python settings_manager.py   # 4 Tests
```

#### Integrations-Tests:

```bash
cd dev-tools/testing
python test_s1_layout.py     # 4 Tests (S1-Layout)
python test_s2_layout.py     # 5 Tests (S2-Layout)
```

#### Export-Module (benötigen Dependencies):

```bash
# Benötigt PIL/Pillow
python pdf_exporter.py       # 2 Tests
python text_overlay.py       # 1 Test
python print_preparer.py     # 1 Test

# Benötigt PyQt6
python font_manager.py       # 4 Tests
python validation_manager.py # 3 Tests

# Benötigt Wand (ImageMagick)
python svg_loader_local.py   # 2 Tests
python taktische_zeichen_generator.py  # 1 Test
```

### Schnell-Check (nur OK/FEHLER):

```bash
python constants.py && echo "✓ OK" || echo "✗ FEHLER"
```

### Alle Core-Tests auf einmal:

```bash
#!/bin/bash
# Quick test script
for module in constants.py runtime_config.py settings_manager.py; do
    echo "=== Testing $module ==="
    python $module 2>&1 | tail -10
    echo ""
done

cd dev-tools/testing
for test in test_s1_layout.py test_s2_layout.py; do
    echo "=== Testing $test ==="
    python $test 2>&1 | tail -10
    echo ""
done
```

### Ausgabe filtern:

```bash
# Nur Test-Ausgaben (ohne Startup-Messages)
python constants.py 2>&1 | grep -A 100 "TEST-ROUTINE"

# Nur die letzten 30 Zeilen
python constants.py 2>&1 | tail -30

# In Datei speichern
python constants.py > test_output.txt 2>&1
```

---

## Was sagen mir die Test-Ergebnisse?

### Erfolgreiche Ausführung:

```
======================================================================
TEST-ROUTINE: constants.py
======================================================================

[Test 1] mm_to_pixels() / pixels_to_mm()
----------------------------------------------------------------------
  Input: 45.0 mm bei 300 DPI
  -> 531 Pixel
  -> 44.96 mm (Rueckkonvertierung)
  Differenz: 0.042000 mm
  [OK] Konvertierung korrekt

...

======================================================================
ALLE TESTS BESTANDEN!
======================================================================
```

**Bedeutung:**
- ✅ Alle Funktionen arbeiten korrekt
- ✅ Keine Regressions-Fehler
- ✅ Code-Änderungen haben nichts kaputt gemacht

### Integrations-Tests (S1/S2):

```
======================================================================
INTEGRATIONS-TESTS: S2-LAYOUT (Standard-Zeichen)
======================================================================

[Integrations-Test] Standard quadratisch (45x45mm, Aspect Lock ON)
----------------------------------------------------------------------
  Zeichen: 45.0mm x 45.0mm (1:1 Aspect Ratio)
  Canvas: 39.0mm x 39.0mm (nach 3.0mm Sicherheitsabzug)
  Aspect Lock: ON
  Max. Grafikgroesse: 29.94mm
  [OK] Standard quadratisch funktioniert korrekt

======================================================================
ALLE INTEGRATIONS-TESTS BESTANDEN!
======================================================================
```

### Fehlgeschlagene Tests:

```
[Test 3] create_staerke_placeholder()
----------------------------------------------------------------------
AssertionError: Custom Staerke fehlerhaft!
```

**Bedeutung:**
- ❌ Funktion liefert unerwartetes Ergebnis
- ❌ Mögliche Regression durch Code-Änderung
- ❌ **AKTION NÖTIG:** Prüfen, ob:
  - Bug im Code?
  - Test-Erwartung falsch?
  - Intentionale Änderung?

### Skip-Meldungen:

```
[Test 3] set() Methode
----------------------------------------------------------------------
  [SKIP] ValidationManager nicht verfuegbar (PyQt6 fehlt)
```

**Bedeutung:**
- ⚠️ Test konnte nicht ausgeführt werden
- ⚠️ Abhängigkeiten fehlen (z.B. PyQt6, PIL)
- ✅ Kein Fehler - nur Umgebungsproblem

---

## Wann sollte ich Test-Routinen nutzen?

### 1. Nach Code-Änderungen

**Szenario:** Du hast eine Funktion in `constants.py` geändert.

```bash
# Schnell prüfen, ob alles noch funktioniert
python constants.py
```

**Was passiert:**
- Alle 8 Tests laufen durch
- Du siehst sofort, ob deine Änderung etwas kaputt gemacht hat

### 2. Vor Commits

**Workflow:**
```bash
# 1. Änderungen gemacht

# 2. Tests laufen lassen
python constants.py
python runtime_config.py
cd dev-tools/testing && python test_s1_layout.py
cd dev-tools/testing && python test_s2_layout.py

# 3. Wenn alle Tests bestehen → Commit
git add .
git commit -m "Feature: ..."
```

### 3. Beim Debugging

**Problem:** Eine Funktion verhält sich seltsam.

```bash
# Test zeigt dir, wie die Funktion SOLLTE funktionieren
python constants.py
```

**Beispiel aus Test:**
```python
# Test 1: Millimeter <-> Pixel Konvertierung
test_mm = 45.0
test_dpi = 300
pixels = mm_to_pixels(test_mm, test_dpi)
back_to_mm = pixels_to_mm(pixels, test_dpi)
```

→ Du siehst **konkrete Beispiele** für korrekte Verwendung!

### 4. Nach Git Pull

**Szenario:** Du pullst neue Änderungen vom Repository.

```bash
git pull
# Schnell testen, ob alles noch funktioniert
python constants.py
python runtime_config.py
cd dev-tools/testing && python test_s2_layout.py  # NEU!
```

### 5. Neue Umgebung

**Szenario:** Du richtest das Projekt auf einem neuen Rechner ein.

```bash
# Core Tests (sollten immer funktionieren)
python constants.py         # ✓ Keine externen Deps
python runtime_config.py    # ✓ Keine externen Deps
python settings_manager.py  # ✓ Keine externen Deps

# Integrations-Tests
cd dev-tools/testing
python test_s1_layout.py    # ✓ Keine externen Deps
python test_s2_layout.py    # ✓ Keine externen Deps

# Export-Tests (brauchen Dependencies)
python font_manager.py      # Braucht PyQt6
python pdf_exporter.py      # Braucht PIL
python validation_manager.py # Braucht PyQt6
```

---

## Wie erweitere ich Test-Routinen?

### Neue Test-Routine hinzufügen:

#### 1. Grundstruktur

Am Ende deiner Modul-Datei:

```python
# ================================================================================================
# TEST ROUTINES
# ================================================================================================

if __name__ == "__main__":
    """
    Test-Routine für mein_modul.py

    Testet alle wichtigen Funktionen.
    Ausführung: python mein_modul.py
    """
    print("=" * 70)
    print("TEST-ROUTINE: mein_modul.py")
    print("=" * 70)

    # Tests hier...

    print("\n" + "=" * 70)
    print("ALLE TESTS BESTANDEN!")
    print("=" * 70)
```

#### 2. Integrations-Test erstellen (wie S1/S2):

Erstelle neue Datei in `dev-tools/testing/`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mein_feature.py - Integrations-Tests für Mein Feature

Testet realistische Szenarien mit kombinierten Funktionen.
Ausführung: python dev-tools/testing/test_mein_feature.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from constants import MY_CONSTANT
from runtime_config import get_config


def run_test_scenario_1():
    """Test: Szenario 1"""
    print("\n[Test] Szenario 1")
    print("-" * 70)

    # Test-Code hier
    result = my_function()

    assert result == expected, "Fehler!"
    print("  [OK] Szenario 1 funktioniert")


if __name__ == "__main__":
    print("=" * 70)
    print("INTEGRATIONS-TESTS: Mein Feature")
    print("=" * 70)

    run_test_scenario_1()

    print("\n" + "=" * 70)
    print("ALLE TESTS BESTANDEN!")
    print("=" * 70)
```

### Best Practices:

#### ✅ DO:

- **Klare Test-Namen:** `[Test 1] mm_to_pixels()`
- **Erwartungen dokumentieren:** `print(f"Erwartet: {expected}")`
- **Assertions verwenden:** `assert result == expected, "Fehler!"`
- **Mehrere Szenarien:** Normal, Edge-Cases, Fehler-Fälle
- **Informative Ausgaben:** Zeige Input UND Output

#### ❌ DON'T:

- Keine interaktiven Eingaben (input())
- Keine Datei-Änderungen (außer temp-Dateien mit Cleanup)
- Keine langen Laufzeiten (> 5 Sekunden)
- Keine externen API-Calls
- Keine GUI-Tests (nur Logik)

---

## Troubleshooting

### Problem: ModuleNotFoundError

```bash
python pdf_exporter.py
# ModuleNotFoundError: No module named 'PIL'
```

**Ursache:** Externe Abhängigkeiten fehlen (PyQt6, PIL, etc.)

**Lösung:**
1. **Option A:** Abhängigkeiten installieren
   ```bash
   pip install PyQt6 Pillow reportlab wand
   ```

2. **Option B:** Test mit try-except absichern
   ```python
   try:
       from PIL import Image
       # Test läuft
   except ModuleNotFoundError:
       print("  [SKIP] PIL nicht verfügbar")
   ```

### Problem: AssertionError

```bash
AssertionError: Canvas-Hoehe falsch!
```

**Ursache:** Test-Erwartung stimmt nicht mit tatsächlichem Ergebnis überein.

**Lösung:**
1. **Prüfe die Ausgabe:** Was ist der tatsächliche Wert?
2. **Ist die Erwartung falsch?** → Test-Code korrigieren
3. **Ist das Ergebnis falsch?** → Funktion debuggen

### Problem: Test hängt/freezed

**Ursache:** Test wartet auf Input oder hat Endlos-Schleife.

**Lösung:**
- **Abbrechen:** Ctrl+C
- **Timeout setzen:**
  ```bash
  timeout 10 python constants.py
  ```
- **Code prüfen:** Keine `input()` oder `while True` ohne Exit

---

## Quick Reference

### Alle Core-Tests ausführen (immer verfügbar):

```bash
python constants.py          # 8 Tests, ~3 Sekunden
python runtime_config.py     # 6 Tests, ~1 Sekunde
python settings_manager.py   # 4 Tests, ~1 Sekunde

cd dev-tools/testing
python test_s1_layout.py     # 4 Tests, ~1 Sekunde
python test_s2_layout.py     # 5 Tests, ~1 Sekunde (NEU!)
```

**Gesamt: 27 Tests ohne Dependencies**

### Export-Tests (benötigen Dependencies):

```bash
python font_manager.py       # 4 Tests (PyQt6)
python pdf_exporter.py       # 2 Tests (PIL)
python validation_manager.py # 3 Tests (PyQt6)
```

### Tests mit Fehlern ignorieren:

```bash
python validation_manager.py || echo "Übersprungen (PyQt6 fehlt)"
```

### Automatisiertes Testing:

```bash
#!/bin/bash
# test_all.sh

modules=(
    "constants.py"
    "runtime_config.py"
    "settings_manager.py"
)

for module in "${modules[@]}"; do
    echo "Testing $module..."
    if python "$module" > /dev/null 2>&1; then
        echo "  ✓ $module PASSED"
    else
        echo "  ✗ $module FAILED"
    fi
done

# Integrations-Tests
cd dev-tools/testing
for test in test_s1_layout.py test_s2_layout.py; do
    echo "Testing $test..."
    if python "$test" > /dev/null 2>&1; then
        echo "  ✓ $test PASSED"
    else
        echo "  ✗ $test FAILED"
    fi
done
```

---

## Fazit

Test-Routinen sind dein **Sicherheitsnetz** beim Entwickeln:

✅ Schnelles Feedback nach Änderungen
✅ Dokumentation durch Beispiele
✅ Regression-Prevention
✅ Debugging-Hilfe
✅ 27 Tests ohne Dependencies sofort verfügbar
✅ 41+ Tests gesamt (mit Dependencies)

**Nutze sie regelmäßig** - besonders vor Commits und nach größeren Änderungen!

---

## Changelog

### v2.0 (2025-12-03)
- ✅ S2-Layout Test-Suite hinzugefügt (5 Tests)
- ✅ Integrations-Tests dokumentiert
- ✅ Test-Übersicht aktualisiert (27 Core + 14+ Export = 41+ Tests)
- ✅ Neue Test-Dateien in `dev-tools/testing/` dokumentiert

### v1.0 (2025-11-14)
- Initiale Version
- Core-Tests dokumentiert

---

**Letzte Aktualisierung:** 2025-12-03
**Autor:** Claude Code
**Projekt:** Taktische Zeichen Druckgenerator
