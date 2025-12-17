# Release Notes v0.8.3 - Bugfix Release

**Release-Datum:** 2025-12-11
**Version:** v0.8.3

---

## 🎉 Highlights dieser Version

Version 0.8.3 ist ein **kritischer Bugfix-Release**, der schwerwiegende Fehler im PDF-Export, der SVG-Verarbeitung und im Build-Prozess behebt. Zusätzlich wurden UX-Verbesserungen implementiert. Alle Fixes wurden durch umfassende Unit-Tests abgesichert.

**Wichtigste Änderungen:**
- **PDF-Export wieder funktionsfähig** für Einzelzeichen und Schnittbögen (S1 und S2)
- **Blanko-Zeichen werden korrekt verarbeitet** ohne File-Not-Found-Warnungen
- **Build-Prozess korrigiert** - Logo & Icon erscheinen jetzt in gebauten Releases
- **Fenster startet zentriert** auf dem Bildschirm
- **Logo im Benutzerhandbuch** integriert
- **21 neue Unit-Tests** für Regression-Schutz

---

## 🐛 Bugfixes

### Kritisch: PDF-Export komplett defekt

**Problem:**
```
TypeError: create_pdf_filename() got an unexpected keyword argument 'timestamp'
```

**Ursache:**
- Lokale Funktion `create_pdf_filename()` in `pdf_exporter.py` (Zeile 521) hat Import aus `constants.py` überschrieben
- Test-Funktion hatte andere Signatur: `(variant, count, dpi, output_dir)`
- Importierte Funktion erwartet: `(timestamp, export_format, start_idx, end_idx, file_idx, total_files)`
- **Resultat:** PDF-Export schlug komplett fehl (weder Einzelzeichen noch Schnittbögen)

**Fix:**
- Test-Funktion umbenannt zu `_create_test_pdf_filename()` (internes Naming mit `_`)
- Docstring hinzugefügt mit Warnung, dass dies nur für Tests ist
- Alle Aufrufe in Test-Sektion aktualisiert (Zeilen 1468, 1481)
- Import aus `constants.py` bleibt unangetastet

**Betroffene Dateien:**
- `pdf_exporter.py`: Zeilen 521-549, 1468, 1481

**Test-Coverage:**
- `test_pdf_exporter.py::test_create_pdf_filename_signature()` - Prüft korrekte Funktionssignatur
- `test_pdf_exporter.py::test_no_name_collision()` - Verhindert erneutes Shadowing

---

### Kritisch: Blanko-Zeichen verursachen FileNotFoundError

**Problem:**
```
[Errno 2] No such file or directory: 'BLANKO_ov_staerke'
wand.exceptions.CoderError: no decode delegate for this image format 'BLANKO_ov_staerke'
```

**Ursache:**
- Blanko-Zeichen sind **virtuelle Pfade** (z.B. `BLANKO_ov_staerke`, `BLANKO_S1_LEER`)
- Sie existieren nicht als echte Dateien im Dateisystem
- Code versuchte sie zu lesen/rendern/sanitizen wie normale SVG-Dateien
- **Resultat:** Warnungen im Log, potenzielle Export-Probleme

**Fix:**
Drei Stellen in `taktische_zeichen_generator.py` korrigiert:

**1. `_is_pseudo_svg()` (Zeilen 168-189):**
```python
# FIXED: Blanko-Zeichen können keine Pseudo-SVGs sein (virtueller Pfad)
if SVGLoaderLocal.is_blanko_zeichen(svg_path):
    return False

# Datei muss existieren
if not svg_path.exists():
    return False
```

**2. `_sanitize_svg_content()` (Zeilen 298-337):**
```python
# FIXED: Blanko-Zeichen sind virtuelle Pfade, keine echten Dateien
if SVGLoaderLocal.is_blanko_zeichen(svg_path):
    return svg_path

# FIXED: Datei muss existieren
if not svg_path.exists():
    return svg_path
```

**3. SVG-Template-Erstellung in S1 und S2 (Zeilen 1290-1333, 1696-1714):**
```python
for svg_path, config in chunk_tasks:
    svg_template_key = self._get_svg_template_key(svg_path, config)
    if svg_template_key not in svg_template_keys_seen:
        try:
            # FIXED: Blanko-Zeichen haben keine Grafik, kein Template nötig
            if SVGLoaderLocal.is_blanko_zeichen(svg_path):
                svg_template_keys_seen.add(svg_template_key)
                continue
            # ... Template-Erstellung ...
```

**Betroffene Dateien:**
- `taktische_zeichen_generator.py`: Zeilen 168-189, 298-337, 1290-1333, 1696-1714

**Test-Coverage:**
- `test_blanko_zeichen.py::test_is_pseudo_svg_with_blanko()` - Prüft Blanko-Erkennung
- `test_blanko_zeichen.py::test_sanitize_svg_content_with_blanko()` - Prüft korrekte Rückgabe
- `test_svg_loader.py::test_validate_svg_with_blanko()` - Prüft SVG-Validierung mit Blanko

---

### Kritisch: Logo & Icon fehlen in gebauten Releases

**Problem:**
- Nach dem Build mit PyInstaller waren Logo und Icon nicht sichtbar
- GUI zeigte kein Programm-Logo und kein Fenster-Icon
- Problem trat nur in gebauter .exe auf, nicht beim Ausführen aus VS Code

**Ursache:**
- PyInstaller packt `resources/` in `_internal/resources/`
- Code erwartet `resources/` direkt neben der .exe
- Build-Scripts verschoben bereits `imagemagick/` von `_internal/`, aber nicht `resources/`

**Fix:**
- `build_exe.bat`: Neuer Schritt [4d/5] verschiebt Resources von `_internal/resources/` nach `resources/`
- `build_linux.sh`: Neuer Schritt [6b/8] mit gleicher Logik für Linux-Builds
- Analog zum bestehenden ImageMagick-Verschiebe-Schritt

**Betroffene Dateien:**
- `build_exe.bat`: Zeilen 62-68
- `build_linux.sh`: Zeilen 116-124

---

## 🎨 Verbesserungen

### Fenster-Zentrierung beim Start

**Problem:**
- Programm-Fenster startete nicht mittig auf dem Monitor
- Fenster war nach rechts verschoben

**Lösung:**
- Neue Methode `showEvent()` überschrieben
- Fenster wird beim ersten Anzeigen automatisch zentriert
- Verwendet `QScreen.availableGeometry()` für präzise Zentrierung (berücksichtigt Taskleiste)
- Nur beim ersten Anzeigen ausgeführt (Flag `_window_centered`)

**Technische Details:**
- `showEvent()` ist der richtige Zeitpunkt - Fenster hat finale Geometrie inkl. Rahmen
- Frühere Versuche im `__init__()` schlugen fehl, da Fenster noch keine Größe hatte

**Betroffene Dateien:**
- `gui/main_window.py`: Zeilen 892-939

---

### Logo im Benutzerhandbuch

**Änderung:**
- Programm-Logo am Anfang des Benutzerhandbuchs eingefügt
- Version auf 0.8.3 aktualisiert
- Stand auf Dezember 2025 aktualisiert

**Betroffene Dateien:**
- `User-documentation/BENUTZERHANDBUCH.md`: Logo als `![Logo](../resources/Logo.png)`

---

## 🧪 Unit-Tests

Diese Version führt **21 neue Unit-Tests** ein, um die behobenen Bugs dauerhaft abzusichern:

### test_pdf_exporter.py (5 Tests)
- ✅ `test_create_pdf_filename_signature()` - Prüft Funktionssignatur
- ✅ `test_create_pdf_filename_output()` - Prüft Dateinamen-Format (Schnittbogen)
- ✅ `test_create_pdf_filename_einzelzeichen()` - Prüft Einzelzeichen-Format
- ✅ `test_no_name_collision()` - Prüft dass kein Name-Shadowing existiert
- ✅ `test_timestamp_format()` - Prüft Timestamp-Konsistenz

### test_blanko_zeichen.py (9 Tests)
- ✅ `test_is_blanko_zeichen_standard()` - Standard-Blanko (BLANKO_modus)
- ✅ `test_is_blanko_zeichen_s1()` - S1-Blanko-Varianten
- ✅ `test_is_blanko_zeichen_normale_zeichen()` - Nicht-Blanko-Zeichen
- ✅ `test_has_staerke_anzeige()` - Stärke-Anzeige-Erkennung
- ✅ `test_is_blanko_s1_both()` - S1 mit beidseitigen Schreiblinien
- ✅ `test_get_blanko_modus()` - Modus-Extraktion
- ✅ `test_get_blanko_display_name()` - Display-Namen
- ✅ `test_is_pseudo_svg_with_blanko()` - Pseudo-SVG-Erkennung
- ✅ `test_sanitize_svg_content_with_blanko()` - SVG-Content-Sanitization

### test_svg_loader.py (7 Tests)
- ✅ `test_validate_svg_with_real_file()` - Validierung echter SVG-Dateien
- ✅ `test_validate_svg_with_non_existent_file()` - Nicht-existierende Dateien
- ✅ `test_validate_svg_with_blanko()` - Blanko-Zeichen-Validierung
- ✅ `test_check_svg_fonts()` - Font-Extraktion mit Fonts
- ✅ `test_check_svg_fonts_empty()` - Font-Extraktion ohne Fonts
- ✅ `test_svg_loader_init_with_nonexistent_dir()` - Auto-Verzeichnis-Erstellung
- ✅ `test_blanko_zeichen_comprehensive()` - Umfassender Blanko-Test

**Ausführung:**
```bash
python dev-tools/testing/test_pdf_exporter.py
python dev-tools/testing/test_blanko_zeichen.py
python dev-tools/testing/test_svg_loader.py
```

**Alle Tests bestehen:** 21/21 ✅

---

## 🔧 Technische Details

### Code-Qualität

**Function Shadowing Prevention:**
- Interne Test-Funktionen werden mit `_` Präfix benannt
- Docstrings warnen explizit vor Production-Nutzung
- Unit-Test prüft dass Import nicht überschrieben wird

**Blanko-Zeichen-Handling:**
- Konsequente Prüfung mit `SVGLoaderLocal.is_blanko_zeichen()` VOR File-Operationen
- Early-Return-Pattern für bessere Performance
- Debug-Logging für bessere Nachvollziehbarkeit

**Test-Framework:**
- Alle Tests verwenden temporäre Dateien (automatisches Cleanup)
- Aussagekräftige Fehlermeldungen mit Format-Strings
- Tests überspringen PIL-abhängige Funktionen wenn PIL fehlt

**Build-Prozess:**
- Resources werden von PyInstaller's `_internal/` nach root verschoben
- Analog zu ImageMagick (bereits implementiert)
- Funktioniert für Windows (`build_exe.bat`) und Linux (`build_linux.sh`)

**Window Centering:**
- Verwendet `showEvent()` statt `__init__()` für korrektes Timing
- `QScreen.availableGeometry()` berücksichtigt Taskleiste
- Flag `_window_centered` verhindert wiederholtes Zentrieren

---

## 📊 Geänderte Dateien

```
Core Bugfixes:
constants.py                              | 1 Zeile (Version)
pdf_exporter.py                           | 28 Zeilen (Function Rename + Docstring)
taktische_zeichen_generator.py            | 45 Zeilen (Blanko-Checks)

Build & UX Improvements:
build_exe.bat                             | 7 Zeilen (Resources-Verschiebung)
build_linux.sh                            | 9 Zeilen (Resources-Verschiebung)
gui/main_window.py                        | 52 Zeilen (Window Centering)
User-documentation/BENUTZERHANDBUCH.md    | 3 Zeilen (Logo + Version)

Unit Tests (neu):
dev-tools/testing/test_pdf_exporter.py    | 256 Zeilen
dev-tools/testing/test_blanko_zeichen.py  | 353 Zeilen
dev-tools/testing/test_svg_loader.py      | 352 Zeilen
```

**Gesamt:** 1106 Zeilen hinzugefügt/geändert
- Produktionscode: 145 Zeilen
- Tests: 961 Zeilen

---

## 🚀 Installation & Upgrade

### Neue Installation
1. Download: `Taktische_Zeichen_Generator_v0.8.3.zip`
2. Entpacken in beliebiges Verzeichnis
3. `Taktische_Zeichen_Generator.exe` starten

### Upgrade von v0.8.2
- **Drop-in Replacement:** Einfach .exe ersetzen
- **Keine Breaking Changes:** Settings.json bleibt kompatibel
- **Empfehlung:** Alte Version sichern, dann ersetzen

---

## 📝 Bekannte Limitationen

**Unverändert zu v0.8.2:**
1. Layout-Preview experimentell deaktiviert
2. Max. Logfiles Setting noch nicht funktional
3. Pylance Type-Checking Warnings in main_window.py (harmlos)

---

## 🔮 Ausblick auf v0.8.4

Geplante Verbesserungen:
- Performance: Weitere Optimierungen beim PDF-Export
- Tests: Integration-Tests für komplette Export-Pipeline
- Code-Qualität: Pylance-Warnings reduzieren

---

## 🙏 Danksagungen

Danke an alle Nutzer, die Fehlerberichte eingereicht haben und geholfen haben, diese kritischen Bugs zu identifizieren!

---

**Wichtiger Hinweis:** Diese Version behebt **kritische Fehler**:
- ✅ **PDF-Export** funktioniert wieder (war komplett defekt in v0.8.2)
- ✅ **Logo & Icon** erscheinen jetzt in gebauten Releases
- ✅ **Blanko-Zeichen** verursachen keine Warnungen mehr
- ✅ **Bessere UX** durch zentriertes Fenster beim Start

Ein Upgrade von v0.8.2 wird **dringend empfohlen**!

---

🤖 **Generated with [Claude Code](https://claude.com/claude-code)**
