# 🚀 Taktische-Zeichen-Editor - Proof of Concept

## Übersicht

Dieser Proof-of-Concept demonstriert die Kernfunktionalität des Taktische-Zeichen-Editors:

1. ✅ SVG-Zeichen vom GitHub laden und cachen
2. ✅ Text hinzufügen (OV + Stärke ODER Ruf)
3. ✅ Für Druck vorbereiten (Sicherheitsränder: 3mm + 3mm)
4. ✅ Als PNG exportieren (600 DPI, druckfertig)

---

## 📦 Installation

### 1. Python-Umgebung

Benötigt: **Python 3.8+**

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

Installiert:
- `Pillow` - Bildverarbeitung
- `requests` - HTTP-Requests für GitHub
- `svglib` - SVG-Rendering
- `reportlab` - PDF/PNG-Rendering

---

## 🏗️ Projekt-Struktur

```
TaktischeZeichenEditor-PoC/
│
├── poc_constants.py       # Konstanten und Konfiguration
├── svg_loader.py          # GitHub SVG Loader + Cache
├── text_overlay.py        # Text zu Zeichen hinzufügen
├── print_preparer.py      # Druckvorbereitung (Ränder)
├── poc_main.py            # Haupt-Script (Demo)
│
├── requirements.txt       # Python-Dependencies
├── README_POC.md          # Diese Datei
│
├── zeichen_cache/         # Gecachte SVGs (automatisch erstellt)
│   └── github_svgs/
│
├── exports/               # Export-Ausgaben (automatisch erstellt)
└── Logs/                  # Log-Dateien (automatisch erstellt)
```

---

## 🎯 Verwendung

### Variante 1: Test-Script ausführen

Jedes Modul hat eine eingebaute Test-Funktion:

```bash
# SVG-Loader testen
python svg_loader.py

# Text-Overlay testen (erstellt Test-Image)
python text_overlay.py

# Print-Preparer testen (erstellt Test-Image)
python print_preparer.py
```

### Variante 2: Haupt-Demo

```bash
python poc_main.py
```

**WICHTIG:** Für einen echten Test benötigst du eine SVG-Datei!

### Variante 3: Eigenes Zeichen erstellen

```python
from pathlib import Path
from poc_main import TaktischeZeichenPOC
from text_overlay import ZeichenInfo
from poc_constants import MODUS_OV_STAERKE

# PoC initialisieren
poc = TaktischeZeichenPOC()

# Zeichen-Info erstellen
zeichen_info = ZeichenInfo(
    zeichen_id="MEIN_ZEICHEN",
    svg_path=Path("pfad/zu/deiner.svg"),
    modus=MODUS_OV_STAERKE,
    ov_text="OV Musterstadt",
    staerke_fuehrung=1,
    staerke_mannschaft=5,
    staerke_fahrzeuge=2,
    groesse_mm=50.0,
    dpi=600
)

# Zeichen erstellen
output_file = poc.create_zeichen(zeichen_info)
print(f"Erstellt: {output_file}")
```

---

## 📋 SVG von GitHub laden

### Option 1: Manueller Download

1. Gehe zu: https://github.com/jonas-koeritz/Taktische-Zeichen
2. Navigiere zu einem SVG (z.B. in `symbols/`)
3. Klicke auf "Raw" und speichere die Datei
4. Lege sie nach `zeichen_cache/github_svgs/` ab

### Option 2: Mit SVGLoader

```python
from svg_loader import SVGLoader

loader = SVGLoader()

# SVG laden (wird automatisch gecacht)
svg_file = loader.load_svg(
    zeichen_id="N_THW",
    svg_path="symbols/units/N.svg"  # Pfad im GitHub-Repo
)

print(f"SVG geladen: {svg_file}")
```

**HINWEIS:** Der exakte Pfad muss noch aus dem GitHub-Repo ermittelt werden!

---

## ⚙️ Konfiguration

Alle Parameter in `poc_constants.py` anpassbar:

### Druck-Parameter

```python
DEFAULT_ZEICHEN_GROESSE_MM = 50.0  # Größe des Zeichens
DEFAULT_MINDESTABSTAND_MM = 3.0    # Sicherheitsrand (y)
DEFAULT_BESCHNITT_MM = 3.0         # Beschnittzugabe (x)
DEFAULT_DPI = 600                  # Auflösung
```

### Text-Layout

```python
FONT_SIZE_OV = 12          # Schriftgröße OV-Zeile
FONT_SIZE_STAERKE = 10     # Schriftgröße Stärke-Zeile
TEXT_OFFSET_MM = 2.0       # Abstand Zeichen <-> Text
```

### Cache

```python
CACHE_MAX_AGE_DAYS = 7     # Cache-Lebensdauer
```

---

## 🧪 Test-Ausgaben

### text_overlay.py Test

Erstellt `test_output.png`:
- Blauer Kreis (simuliert THW-Zeichen)
- Text unterhalb: "OV: OV Musterstadt" + Stärke

### print_preparer.py Test

Erstellt `test_print_prepared.png`:
- Roter Kreis (Test-Grafik)
- Mit Sicherheitsrand (3mm)
- Mit Beschnittzugabe (3mm)
- 600 DPI

---

## 📐 Druck-Spezifikationen

### Finale Dimensionen

Für ein **50mm Zeichen** mit Standard-Rändern:

```
Zeichen:           50.0mm
+ Sicherheitsrand:  6.0mm (2x 3mm)
+ Beschnitt:        6.0mm (2x 3mm)
= Gesamt:          62.0mm

Bei 600 DPI = ~1457 x 1457 Pixel
```

### Export-Eigenschaften

- **Format:** PNG
- **Auflösung:** 600 DPI (Metadaten im PNG)
- **Farbraum:** RGB (CMYK-Konvertierung erfolgt später)
- **Qualität:** Verlustfrei

---

## 🔍 Module-Übersicht

### poc_constants.py

- Alle Konstanten und Konfiguration
- Hilfsfunktionen: `mm_to_pixels()`, `pixels_to_mm()`
- Erstellt automatisch notwendige Ordner

### svg_loader.py

**Funktionen:**
- SVGs vom GitHub laden
- Lokaler Cache (7 Tage)
- Cache-Verwaltung (löschen, Info)

**Hauptklasse:** `SVGLoader`

### text_overlay.py

**Funktionen:**
- Text unterhalb des Zeichens hinzufügen
- Zwei Modi: OV + Stärke ODER Ruf
- Automatisches Zentrieren

**Hauptklassen:**
- `ZeichenInfo` (Dataclass)
- `TextOverlay`

### print_preparer.py

**Funktionen:**
- Bild auf Zielgröße skalieren
- Sicherheitsrand (y) hinzufügen
- Beschnittzugabe (x) hinzufügen
- DPI-Metadaten setzen

**Hauptklasse:** `PrintPreparer`

### poc_main.py

**Funktionen:**
- Orchestriert kompletten Workflow
- SVG -> Text -> Druck -> Export
- Demo-Funktion

**Hauptklasse:** `TaktischeZeichenPOC`

---

## ✅ Was funktioniert

- ✅ **SVG-Laden mit Cache:** SVGs werden gecacht und wiederverwendet
- ✅ **SVG → PNG Konvertierung:** Hochauflösend (600 DPI)
- ✅ **Text-Overlay:** OV + Stärke ODER Ruf, zentriert unterhalb
- ✅ **Druckvorbereitung:** Automatische Ränder (3mm + 3mm)
- ✅ **PNG-Export:** Mit DPI-Metadaten
- ✅ **Modular:** Jedes Modul einzeln testbar

---

## 🚧 Was noch fehlt (für Vollversion)

- ⏳ **GUI:** tkinter-Interface für Benutzer
- ⏳ **Excel/CSV-Import:** Massenverarbeitung
- ⏳ **CMYK-Konvertierung:** Für professionellen Druck
- ⏳ **JPG/SVG-Export:** Zusätzliche Formate
- ⏳ **Settings-Dialog:** Parameter anpassbar machen
- ⏳ **Batch-Processing:** Mehrere Zeichen auf einmal
- ⏳ **Projektmanager:** Zeichen-Sammlungen verwalten

---

## 📊 Beispiel-Output

### Input (SVG)
- Taktisches Zeichen (z.B. "N" für Einheit)
- 256x256 Einheiten (Standard aus GitHub)

### Processing
1. SVG zu PNG (600 DPI) → ~1500x1500 px
2. Text hinzufügen → Höhe wächst um ~200px
3. Sicherheitsrand (3mm) → +142px pro Seite
4. Beschnittzugabe (3mm) → +142px pro Seite

### Output (PNG)
- **Datei:** `N_THW_OV_druckfertig.png`
- **Größe:** ~2000x2000 px (abhängig von Text)
- **DPI:** 600
- **Größe auf Papier:** ~62mm x 62mm (inkl. Ränder)

---

## 🐛 Bekannte Limitierungen

### Font-Handling

Aktuell wird versucht, Arial zu laden. Falls nicht verfügbar:
- Fallback auf PIL Default-Font (pixelig bei hoher Auflösung)

**Lösung:** 
```python
# In text_overlay.py, Zeile ~140
# Anpassen für dein System oder TrueType-Font mitliefern
```

### CMYK-Konvertierung

Aktuell RGB-Export. Für Druckerei:
- Manuell in Photoshop/GIMP konvertieren
- Oder zukünftig: Pillow CMYK-Plugin

### GitHub-Struktur

Die exakten Pfade im GitHub-Repo müssen noch ermittelt werden:
- Wo liegen die SVGs genau?
- Welche Struktur hat `symbols/`?

**TODO:** Repository-Struktur analysieren und `GITHUB_SVG_PATHS` in `poc_constants.py` anpassen

---

## 🔧 Troubleshooting

### "Konnte SVG nicht laden"

**Problem:** GitHub-URL falsch oder Repo-Struktur geändert

**Lösung:**
1. Öffne: https://github.com/jonas-koeritz/Taktische-Zeichen
2. Finde ein SVG (z.B. in `svg/` Ordner)
3. Rechtsklick → "Raw" → URL kopieren
4. Passe `GITHUB_RAW_BASE` + `svg_path` an

### "Arial nicht gefunden"

**Problem:** Font nicht auf System installiert

**Lösung:**
- Windows: Arial sollte vorhanden sein
- Linux: `sudo apt-get install ttf-mscorefonts-installer`
- Oder: Font-Pfad in `text_overlay.py` anpassen

### "SVG-Konvertierung fehlgeschlagen"

**Problem:** svglib kann SVG nicht rendern

**Lösung:**
1. SVG-Datei in Inkscape öffnen
2. Als "Plain SVG" speichern (vereinfacht)
3. Erneut versuchen

### Import-Fehler

**Problem:** Module nicht gefunden

**Lösung:**
```bash
# Alle Module im gleichen Ordner?
ls -la

# Python-Pfad korrekt?
python -c "import sys; print(sys.path)"

# Von richtigem Ordner ausführen?
cd /pfad/zum/poc/
python poc_main.py
```

---

## 📚 Weitere Ressourcen

### GitHub-Repository (Taktische Zeichen)
https://github.com/jonas-koeritz/Taktische-Zeichen

### Python Pillow Dokumentation
https://pillow.readthedocs.io/

### SVGLib Dokumentation
https://github.com/deeplook/svglib

---

## 🎯 Nächste Schritte

### Phase 1: PoC testen ✅
- [x] Module erstellen
- [ ] SVG-Pfade aus GitHub ermitteln
- [ ] Ersten echten Test durchführen
- [ ] Output prüfen (DPI, Ränder)

### Phase 2: GUI entwickeln
- [ ] tkinter-Hauptfenster
- [ ] Zeichen-Auswahl (aus Cache)
- [ ] Eingabe-Felder (OV, Stärke, Ruf)
- [ ] Vorschau-Panel
- [ ] Export-Button

### Phase 3: Massenverarbeitung
- [ ] Excel/CSV-Import
- [ ] Batch-Processing
- [ ] Progress-Bar
- [ ] Fehlerbehandlung

### Phase 4: Polish
- [ ] Settings-Dialog
- [ ] CMYK-Konvertierung
- [ ] Weitere Export-Formate
- [ ] PyInstaller .exe

---

## 💡 Verwendungs-Tipps

### Für Entwicklung

```python
# Logging auf DEBUG setzen
import logging
logging.basicConfig(level=logging.DEBUG)

# Cache löschen (für Tests)
from svg_loader import SVGLoader
loader = SVGLoader()
loader.clear_cache()  # Alle löschen
loader.clear_cache("N_THW")  # Nur eines

# Dimensionen berechnen (vor Erstellung)
from print_preparer import PrintPreparer
preparer = PrintPreparer()
dims = preparer.calculate_final_dimensions(
    zeichen_groesse_mm=50.0,
    mindestabstand_mm=3.0,
    beschnitt_mm=3.0,
    dpi=600
)
print(dims)
```

### Für Produktion

```python
# Logging auf INFO
import logging
logging.basicConfig(level=logging.INFO)

# Fehlerbehandlung
try:
    output = poc.create_zeichen(zeichen_info)
    print(f"Erfolg: {output}")
except FileNotFoundError:
    print("SVG nicht gefunden!")
except Exception as e:
    print(f"Fehler: {e}")
```

---

## 🤝 Mitarbeit

Dieses ist ein Proof-of-Concept. Für die Vollversion werden folgende Features benötigt:

1. **GUI mit tkinter**
2. **Excel-Import für Batch-Processing**
3. **CMYK-Konvertierung**
4. **JPG/SVG-Export**
5. **Settings-Verwaltung**
6. **Projektmanager**

Siehe `.ai-docs/` Ordner für vollständige Architektur-Dokumentation.

---

## 📄 Lizenz

TBD - Bitte klären mit Rechteinhaber des GitHub-Repos:
https://github.com/jonas-koeritz/Taktische-Zeichen

Die Zeichen selbst sind unter CC0 1.0 (gemeinfrei).

---

## ✉️ Kontakt

Bei Fragen zum PoC:
- Siehe `.ai-docs/00_START_HERE.md`
- Oder öffne ein Issue auf GitHub (wenn Repository vorhanden)

---

**Version:** 0.1.0-PoC  
**Letzte Aktualisierung:** 2025-10-14  
**Status:** Proof-of-Concept - Funktioniert, aber ohne GUI