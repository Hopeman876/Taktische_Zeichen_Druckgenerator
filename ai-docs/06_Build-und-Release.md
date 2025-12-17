# Build und Release Prozess

**Projekt:** Taktische Zeichen Druckgenerator
**Aktuelle Version:** v0.8.4
**Datum:** 2025-12-14

---

## Übersicht

Seit v0.8.4 werden Releases **automatisch über GitHub Actions Workflow** erstellt.

**Lokale Builds:**
- Für Entwicklung und Tests
- Nutzen `build_exe.bat` (Windows) oder `build_linux.sh` (Linux)
- Sofort verfügbar ohne Push

**GitHub Workflow Builds:**
- Für offizielle Releases
- Automatisch beim Erstellen eines Git-Tags
- Erstellt ZIP-Archiv und GitHub Release

---

## 📦 Build-System

### PyInstaller Konfiguration

**Hauptdatei:** `TaktischeZeichenDruckgenerator.spec`

Die `.spec` Datei konfiguriert den PyInstaller-Build-Prozess.

#### Wichtige Komponenten:

**1. Hidden Imports (hiddenimports)**

Dynamisch geladene Module müssen **explizit** angegeben werden, da PyInstaller sie nicht automatisch erkennt.

**Beispiel: ReportLab (PDF-Export)**
```python
hiddenimports=[
    # PyQt6
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',

    # Wand (SVG-Rendering)
    'wand',
    'wand.image',

    # ReportLab PDF-Generierung (v0.8.4)
    # CRITICAL: Diese Module werden dynamisch importiert!
    'reportlab',
    'reportlab.rl_config',
    'reportlab.pdfgen',
    'reportlab.pdfgen.canvas',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.lib.utils',
    'reportlab.lib.colors',
    'reportlab.pdfbase',
    'reportlab.pdfbase.pdfdoc',
    'reportlab.pdfbase._fontdata',

    # Font-Encoding Module (für Standard-PDF-Fonts)
    'reportlab.pdfbase._fontdata_enc_winansi',
    'reportlab.pdfbase._fontdata_enc_macroman',
    'reportlab.pdfbase._fontdata_enc_standard',
    'reportlab.pdfbase._fontdata_enc_symbol',
    'reportlab.pdfbase._fontdata_enc_zapfdingbats',

    # Font-Width Module (Courier, Helvetica, Times-Roman)
    'reportlab.pdfbase._fontdata_widths_courierboldoblique',
    'reportlab.pdfbase._fontdata_widths_courierbold',
    'reportlab.pdfbase._fontdata_widths_courieroblique',
    'reportlab.pdfbase._fontdata_widths_courier',
    'reportlab.pdfbase._fontdata_widths_helveticaboldoblique',
    'reportlab.pdfbase._fontdata_widths_helveticabold',
    'reportlab.pdfbase._fontdata_widths_helveticaoblique',
    'reportlab.pdfbase._fontdata_widths_helvetica',
    'reportlab.pdfbase._fontdata_widths_timesromanbi',
    'reportlab.pdfbase._fontdata_widths_timesromanbold',
    'reportlab.pdfbase._fontdata_widths_timesromanitalic',
    'reportlab.pdfbase._fontdata_widths_timesroman',

    # Font-Handling
    'reportlab.pdfbase.pdfmetrics',
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfbase._cidfontdata',
],
```

**Warum so viele reportlab Module?**
- ReportLab lädt Font-Module **zur Laufzeit** dynamisch
- PyInstaller kann dynamische Imports **nicht automatisch erkennen**
- Ohne explizite Angabe: `ModuleNotFoundError` zur Laufzeit
- Wir nutzen nur Standard-PDF-Fonts (Helvetica, Times-Roman, Courier)
- Keine TTF/Custom-Fonts → keine Datendateien nötig

**2. Data Files (datas)**

```python
datas=[
    ('gui/ui_files/*.ui', 'gui/ui_files'),  # Qt Designer UI-Dateien
    ('imagemagick', 'imagemagick'),         # ImageMagick portable
    ('resources', 'resources'),             # Logo & Icon
],
```

**3. Excludes (excludes)**

Nicht benötigte Module ausschließen (spart ~30-50 MB):

```python
excludes=[
    'numpy',      # Nicht verwendet
    'pandas',     # Nicht verwendet
    'matplotlib', # Nicht verwendet
    'scipy',      # Nicht verwendet
    'tkinter',    # PyQt6 statt tkinter
    # ... weitere siehe .spec
],
```

**4. Size Optimization**

```python
# OpenGL Software-Renderer entfernen (~20 MB)
a.binaries = [x for x in a.binaries if not x[0].startswith('opengl32sw')]

# Qt6 Translations entfernen (~6 MB)
a.datas = [x for x in a.datas if not x[0].startswith('PyQt6/Qt6/translations')]

# Nur PNG/JPEG/SVG Image-Format-Plugins behalten (~1.5 MB gespart)
a.datas = [x for x in a.datas if not (
    x[0].startswith('PyQt6/Qt6/plugins/imageformats') and
    not ('qpng' in x[0] or 'qjpeg' in x[0] or 'qsvg' in x[0])
)]
```

**Ergebnis:** ~35-40 MB kleiner bei gleicher Funktionalität

---

## 🔨 Lokaler Build-Prozess

### Windows: build_exe.bat

```bash
build_exe.bat
```

**Schritte:**
1. Alte Build-Dateien löschen (`build/`, `dist/`)
2. Optimierte .pyc-Dateien erstellen
3. PyInstaller Build mit `.spec`
4. Zusätzliche Dateien kopieren:
   - README_BETA.md
   - RELEASE_NOTES_v{VERSION}.md
   - BENUTZERHANDBUCH.pdf
5. ImageMagick von `_internal/` nach `root/` verschieben
6. Resources von `_internal/` nach `root/` verschieben
7. Release-Ordner erstellen: `releases/TaktischeZeichenDruckgenerator_v{VERSION}/`
8. ZIP-Archiv erstellen: `releases/TaktischeZeichenDruckgenerator_v{VERSION}.zip`

**Output:**
```
releases/
└── TaktischeZeichenDruckgenerator_v0.8.4/
    ├── TaktischeZeichenDruckgenerator.exe
    ├── _internal/           # PyInstaller Dependencies
    ├── imagemagick/         # ImageMagick portable (verschoben!)
    ├── resources/           # Logo & Icon (verschoben!)
    ├── README_BETA.md
    ├── RELEASE_NOTES_v0.8.4.md
    └── User-documentation/
        └── BENUTZERHANDBUCH.pdf
```

**Wichtig:** ImageMagick und resources werden von `_internal/` verschoben, weil der Code sie im Root-Verzeichnis erwartet!

### Linux: build_linux.sh

Analog zu Windows, aber mit Bash-Syntax.

```bash
./build_linux.sh
```

---

## 🚀 GitHub Workflow Build (Automatisch)

### Workflow-Datei

**Location:** `.github/workflows/release.yml`

### Trigger

Der Workflow startet **automatisch** wenn ein Git-Tag gepusht wird:

```bash
# Tag erstellen
git tag v0.8.4

# Tag pushen (triggert Workflow)
git push origin v0.8.4
```

**Pattern:** Tags mit `v*` (z.B. v0.8.4, v1.0.0)

### Workflow-Schritte

```yaml
name: Build and Release EXE

on:
  push:
    tags:
      - "v*"

jobs:
  build-and-release:
    runs-on: windows-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller pyinstaller-hooks-contrib

      - name: Run build_exe.bat
        shell: cmd
        run: |
          call build_exe.bat

      - name: Create GitHub Release with ZIP
        uses: ncipollo/release-action@v1
        with:
          tag: ${{ github.ref_name }}
          name: "Release ${{ github.ref_name }}"
          draft: false
          prerelease: false
          artifacts: "releases/TaktischeZeichenDruckgenerator_v*.zip"
          artifactContentType: application/zip
```

**Wichtig: pyinstaller-hooks-contrib**

```yaml
pip install pyinstaller pyinstaller-hooks-contrib
```

Dieses Paket ist **kritisch**! Es enthält:
- Offizielle PyInstaller-Hooks für reportlab
- Automatische Erkennung benötigter Module
- Ohne diese werden reportlab-Module nicht gefunden!

**Lokal funktioniert's ohne:** Viele Entwickler haben `pyinstaller-hooks-contrib` installiert
**GitHub Workflow:** Muss **explizit** installiert werden!

### Output

Der Workflow erstellt automatisch:
1. **GitHub Release** mit Tag-Namen (z.B. "Release v0.8.4")
2. **ZIP-Archiv** als Release-Attachment
3. Release ist **sofort öffentlich verfügbar**

**Download-URL:**
```
https://github.com/Hopeman876/Taktische_Zeichen_Druckgenerator_Develop/releases/tag/v0.8.4
```

---

## 📋 Checkliste: Neues Release erstellen

### 1. Vorbereitung

- [ ] Version in `constants.py` erhöhen:
  ```python
  PROGRAM_VERSION = "0.8.4"
  ```

- [ ] Release Notes erstellen:
  ```
  release_notes/RELEASE_NOTES_v0.8.4.md
  ```

- [ ] Benutzerhandbuch aktualisieren (falls nötig):
  ```
  User-documentation/BENUTZERHANDBUCH.md
  User-documentation/BENUTZERHANDBUCH.pdf
  ```

- [ ] Alle Änderungen committen und pushen:
  ```bash
  git add .
  git commit -m "chore: prepare v0.8.4 release"
  git push origin main
  ```

### 2. Lokaler Test-Build (Optional aber empfohlen)

```bash
# Windows
build_exe.bat

# Testen der .exe
cd releases/TaktischeZeichenDruckgenerator_v0.8.4/
TaktischeZeichenDruckgenerator.exe

# Alle Funktionen testen:
# - SVG laden
# - Text-Modi
# - PNG/JPG Export
# - PDF Export (Einzelzeichen & Schnittbogen)
# - Settings
```

**Kritischer Test:** PDF-Export!
- Wenn lokal funktioniert, sollte Workflow auch funktionieren
- Wenn lokal **nicht** funktioniert → `.spec` Datei prüfen

### 3. Tag erstellen und Release triggern

```bash
# Tag erstellen (annotated tag empfohlen)
git tag -a v0.8.4 -m "Release v0.8.4: Aspect ratio configuration"

# Tag pushen (triggert Workflow!)
git push origin v0.8.4
```

### 4. Workflow überwachen

**GitHub → Actions Tab:**
```
https://github.com/Hopeman876/Taktische_Zeichen_Druckgenerator_Develop/actions
```

**Workflow-Status prüfen:**
- ✅ Grün = Erfolgreich
- ❌ Rot = Fehlgeschlagen

**Bei Fehlschlag:**
1. Workflow-Logs lesen
2. Fehler identifizieren (meist Dependencies oder .spec)
3. Fix implementieren
4. Tag löschen und neu erstellen:
   ```bash
   git tag -d v0.8.4
   git push origin :refs/tags/v0.8.4
   # Fix committen
   git tag v0.8.4
   git push origin v0.8.4
   ```

### 5. Release verifizieren

**Release-Page prüfen:**
```
https://github.com/Hopeman876/Taktische_Zeichen_Druckgenerator_Develop/releases
```

- [ ] Release existiert mit korrektem Tag
- [ ] ZIP-Datei vorhanden
- [ ] ZIP-Größe plausibel (~80-120 MB)

**ZIP herunterladen und testen:**
- [ ] Entpacken
- [ ] .exe starten
- [ ] PDF-Export testen (kritisch!)

---

## 🐛 Troubleshooting

### Problem: PDF-Export funktioniert nicht in gebauter .exe

**Symptom:**
```
ModuleNotFoundError: No module named 'reportlab'
```

**Ursachen & Lösungen:**

**1. hiddenimports unvollständig**

Prüfen: `TaktischeZeichenDruckgenerator.spec`

Alle reportlab-Module in hiddenimports? (siehe oben)

**2. pyinstaller-hooks-contrib fehlt (Workflow)**

Prüfen: `.github/workflows/release.yml`

```yaml
pip install pyinstaller pyinstaller-hooks-contrib  # WICHTIG!
```

**3. requirements.txt fehlt reportlab**

Prüfen: `requirements.txt`

```python
reportlab>=4.2.5  # Muss vorhanden sein!
```

**Debug-Strategie:**
1. Lokalen Build testen → funktioniert = .spec ist OK
2. Workflow-Logs lesen → welcher Schritt schlägt fehl?
3. Dependencies vergleichen (lokal vs. Workflow)

### Problem: ImageMagick nicht gefunden

**Symptom:**
```
ImageMagick not found
```

**Lösung:**
- `build_exe.bat` verschiebt ImageMagick von `_internal/` nach `root/`
- Prüfen ob Verschiebung funktioniert (Logs)
- `.spec` Datei: `('imagemagick', 'imagemagick')` in datas?

### Problem: Logo/Icon fehlt

**Symptom:**
Kein Logo in GUI

**Lösung:**
- `build_exe.bat` verschiebt `resources/` von `_internal/` nach `root/`
- Prüfen: `.spec` → `('resources', 'resources')` in datas?
- Prüfen: Verschiebung in build_exe.bat (Zeilen 62-68)

### Problem: UI-Dateien nicht gefunden

**Symptom:**
```
FileNotFoundError: *.ui not found
```

**Lösung:**
- `.spec` → `('gui/ui_files/*.ui', 'gui/ui_files')` in datas?
- UI-Dateien im korrekten Verzeichnis?

---

## 🔧 Build-Konfiguration: Best Practices

### Requirements (requirements.txt)

**Aktuelle Versionen (v0.8.4):**
```python
# Core Dependencies
Pillow>=10.4.0

# PDF-Generierung
reportlab>=4.2.5  # KRITISCH!

# SVG-Verarbeitung
Wand>=0.6.13

# GUI Framework
PyQt6>=6.7.0
PyQt6-Qt6>=6.7.0

# Optional
openpyxl>=3.1.5  # Excel-Import
```

**Wichtig:**
- Versionen mit `>=` für Flexibilität
- reportlab **muss** vorhanden sein (PDF-Export)
- PyQt6 und PyQt6-Qt6 Versionen synchron halten

### PyInstaller Spec File

**Dos:**
- ✅ Alle dynamisch geladenen Module in `hiddenimports`
- ✅ Alle Daten-Dateien in `datas`
- ✅ Nicht benötigte Module in `excludes` (spart Platz)
- ✅ Build-Optimierungen (opengl32sw, translations, etc.)

**Don'ts:**
- ❌ Keine `collect_data_files('reportlab')` (nur Standard-Fonts)
- ❌ Keine unnötigen Data Files (vergrößert Build)
- ❌ `strip=True` auf Windows (benötigt extra Tools)
- ❌ `upx=True` (langsamer Start, größere Binaries)

### Workflow-Konfiguration

**Python-Version:**
```yaml
python-version: "3.11"  # Stabil, gut supported
```

**Empfehlung:** Python 3.11 oder 3.12 (nicht zu alt, nicht bleeding edge)

**Windows Runner:**
```yaml
runs-on: windows-latest
```

Für Windows .exe **immer** Windows-Runner verwenden!

---

## 📚 Weiterführende Dokumentation

**Build-Anleitung für Nutzer:**
- `BUILD_ANLEITUNG.md` (Root)

**PyInstaller-Spec Details:**
- `TaktischeZeichenDruckgenerator.spec` (kommentiert)

**GitHub Actions Docs:**
- https://docs.github.com/en/actions

**PyInstaller Docs:**
- https://pyinstaller.org/en/stable/

---

## 🎯 Zusammenfassung

**Lokale Builds:**
- Schnell für Tests
- `build_exe.bat` oder `build_linux.sh`
- Sofort nutzbar

**GitHub Workflow:**
- Automatisch bei Git-Tag
- Erstellt Release + ZIP
- Öffentlich verfügbar
- **Wichtig:** pyinstaller-hooks-contrib installieren!

**Kritische Komponenten:**
- reportlab in requirements.txt
- Alle reportlab Module in hiddenimports
- pyinstaller-hooks-contrib im Workflow
- ImageMagick & resources Verschiebung

**Bei Problemen:**
1. Lokalen Build testen
2. Workflow-Logs lesen
3. Dependencies vergleichen
4. .spec Datei prüfen

---

**Letzte Aktualisierung:** 2025-12-14 (v0.8.4)
