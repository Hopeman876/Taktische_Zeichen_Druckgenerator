📋 Projekt-Übersicht
Name: Taktische Zeichen Druckgenerator (Arbeitstitel)
Zweck: Professionelles Windows-Tool zur Vorbereitung taktischer Zeichen für den Druck mit zusätzlichen Beschriftungen.
Workflow:

Zeichen aus lokalem Verzeichnis und Unterverzeichnis laden (SVG-Basis)
Unterverzeichnisse als Kategorie darstellen
Zu bearbeitende Zeichen auswählen
Informationen ergänzen (7 Modi):

1. **OV + Stärke** - OV-Name + Stärkeverhältnis (Führer/Unterführer/Helfer//Gesamt)
2. **Ort + Stärke** - Ort-Name + Stärkeverhältnis
3. **Schreiblinie + Stärke** - Schreiblinie + Stärkeverhältnis
4. **Schreiblinie oder Freitext** - Flexible Textzeile (Standard-Modus)
5. **Ruf** - Rufname
6. **Dateiname** - Automatisch aus Dateinamen
7. **Nur Grafik** - Ohne Text, Grafik-Position wählbar (oben/mittig/unten)

**Single Source of Truth:** `gui/modus_config.py` (Code-Definition)
**Details:** Siehe Abschnitt "Modi-System" unten

Druckparameter einstellen (Größe, Sicherheitsränder)
Einstellen wie oft ein taktisches Zeichen wiederholt werden soll
Export als PNG/JPG/SVG/PDF (druckfertig, CMYK, 600+ DPI)
Massenverarbeitung (>30 Zeichen)
Bei PDF-Export, sollen alle erstellten taktischen Zeichennals einzelne Seite in eine Datei ausgegeben werden

🎯 Kern-Anforderungen
Funktional:

✅ SVG-Zeichen aus lokalem Verzeichnis als Basis
✅ Drei Modi für Zusatzinformationen
✅ GUI mit Vorschau
✅ Excel/CSV-Import für Massenverarbeitung
✅ Export: PNG/PDF (druckfertig)
✅ Verpflichtende Einhaltung der zur Verfügung code-guidlines ==> Datei 01_code-guidelines.md wird zur Verfügung gestellt
✅ Verpflichtende Einhaltung der zur Verfügung general-guidlines ==> Datei 03_general-guidelines.md wird zur Verfügung gestellt
✅ Implementierung des zur Verfügung gestellten Logging-Managers und mitloggen an relevanten Stellen im Code
✅ Implementierung eines AI-Docs-System, das die AI-Doc-Dateien mittels Script aktualisiert. Ziel: Jederzeit mit diesen Dateien eine Claude-Instanz starten zu können und am aktuellen Projektstand weiterarbeiten.
✅ GUI-Entwicklung mit GUI-Designer (Qt Designer oder ähnlich)
✅ SVG-Font-Prüfung vor Generierung (fehlende Fonts erkennen und User fragen)
✅ Schnittlinien optional ausgeben (Standard: AUS)
✅ Zeitschätzung vor Batch-Start anzeigen
✅ Vorhandene Dateien überschreiben ohne Fehler
 

Technisch:

✅ Druckspezifikation:

Ausrichtung des Textes am unteren, sowie linken Rand des Mindestabstands, Text linksbündig
Ausrichtung der Grafik oberhalb des Textes, horizontal zentriert
Größe in mm definierbar, Defaultwert 45 x 45 mm
Mindestabstand Grafik → Rand: y = 3mm (Default)
Beschnittzugabe (Bleed): x = 3mm (Default)
Auflösung: min. 600 DPI
Farbraum: CMYK
Spezielle Vorgaben für die PDF-Erstelllung:
    - Größe und Ausrichtung der Seiten: identisch
    - Farbprofil: ISO Coated v2 300 %
    - PDF-Standard: PDF X1a:2001 1.3
    - Schriften: vollständig eingebettet, alternativ in Pfade umwandeln
    - Transparenz-Überblendung: CMYK


Plattform:

Windows (portable .exe via PyInstaller)
Python + GUI (tkinter oder PyQt mit Designer)
ImageMagick für SVG-Rendering (svglib entfernt - benötigt Cairo DLLs)

- Python 3.8+
- GUI: tkinter oder PyQt (mit GUI-Designer)
- SVG-Verarbeitung: ImageMagick/Wand, Pillow
- Multithreading: concurrent.futures.ThreadPoolExecutor
- Export: Pillow (PNG/JPG), svgwrite (SVG)
- Excel-Import: openpyxl
- Packaging: PyInstaller
- Logging: Dein LoggingManager (übernommen)
```

## 📁 Aktuelle Projekt-Struktur (v0.6.1)
```
Taktische_Zeichen_Editor/
│
├── .git/
├── .gitignore
│
├── ai-docs/                           # ⭐ AI-Dokumentation
│   ├── 00_Projektbeschreibung.md
│   ├── 01_code-guidelines.md
│   ├── 02_GUI-Struktur.md
│   ├── 03_general-guidelines.md
│   ├── AKTUELL_Projektstand_*.md
│   └── Alte_Projektstaende/
│
├── gui/                               # 🔵 GUI (PyQt6)
│   ├── __init__.py
│   ├── main_window.py                 # Hauptfenster
│   ├── ui_loader.py                   # .ui-Loader
│   ├── modus_config.py                # Modi-Konfiguration (Master)
│   │
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── export_dialog.py           # Export-Dialog
│   │   ├── modus_ov_dialog.py         # OV+Stärke Dialog
│   │   ├── modus_ruf_dialog.py        # Ruf Dialog
│   │   ├── modus_ohne_dialog.py       # Ohne Text Dialog
│   │   └── modus_freitext_dialog.py   # Freitext Dialog
│   │
│   └── widgets/
│       ├── __init__.py
│       ├── svg_preview_widget.py      # SVG-Vorschau (Wand-Rendering)
│       └── zeichen_tree_item.py       # TreeWidget-Item
│
├── main.py                            # Einstiegspunkt
├── constants.py                       # Zentrale Konstanten
├── logging_manager.py                 # Logging-System
├── settings_manager.py                # Settings-Verwaltung
├── validation_manager.py              # Input-Validierung
│
├── taktische_zeichen_generator.py    # Generator (Core)
├── text_overlay.py                    # Text-Overlay
├── print_preparer.py                  # Druckvorbereitung
├── svg_loader_local.py                # SVG-Loader
├── pdf_exporter.py                    # PDF-Export
├── font_manager.py                    # Font-Verwaltung
├── svg_analyzer.py                    # SVG-Analyse
│
├── Taktische_Zeichen_Grafikvorlagen/  # 🚫 SVG-Vorlagen (NOT in Git)
│   ├── Kategorie1/
│   │   └── *.svg
│   └── Kategorie2/
│       ├── Unterkategorie/
│       │   └── *.svg
│       └── *.svg
│
├── Taktische_Zeichen_Ausgabe/         # 🚫 Export-Ausgabe (NOT in Git)
│   ├── 2025-11-02_14-30_PNG_Einzelzeichen_*.../
│   └── 2025-11-02_14-30_PDF_Schnittbogen_*.../
│
├── Logs/                              # 🚫 Log-Dateien (NOT in Git)
│   └── YYYY-MM-DD_*.log
│
├── requirements.txt
├── README.md
├── CHANGELOG.md
└── TaktischeZeichenDruckgenerator_v*.spec  # PyInstaller Build-Config


Ordnerstruktur = Kategorien (REKURSIV)
/Taktische_Zeichen_Grafikvorlagen/
   ├── Einheiten/                      # Kategorie
   │   ├── N.svg
   │   └── TZ-.svg
   ├── Fahrzeuge/                      # Kategorie
   │   └── ...
   ├── Personen/                       # Kategorie
   │    └── ...
   |── Taktische_Formationen_THW/      # Kategorie
   │    └── Gruppen/                   # Unterkategorie
   |    │    └── *.svg
   │    └── Trupps/                    # Unterkategorie
   |    │    └── *.svg
   │    └── Einzelpersonen/            # Unterkategorie
   |    │    └── *.svg
```
   - **Alle Unterordner rekursiv durchsuchen**
   - Unterordner = Kategorienamen
   - Unter-Unterordner = Unterkategorien
   - User wählt, welche Kategorien geladen werden

---

## 📚 Technische Grundlagen

### SVG-Rendering
- **ImageMagick/Wand** - Hauptrenderer für SVG → PNG/PDF
- **Pseudo-SVG Erkennung** - PNG-in-SVG Wrapper Detection
- **Whitespace-Trimming** - Automatische Randentfernung

### Platzhalter-System
- OV/Ruf: Konfigurierbare Länge (Default: 15 Unterstriche)
- Stärke: Default 3-stellig (999 max), konfigurierbar 2-4 Stellen
- Schriftgröße in Settings definiert

### GUI-Entwicklung
- **Qt Designer (PyQt6)** - Erstellt .ui-Dateien (XML)
- Programmatische Widget-Erstellung nur für dynamische Inhalte (TreeWidget-Items, etc.)
- Alle statischen UI-Elemente in .ui-Dateien

---

**Naechste Datei fuer KI:** Lese als naechstes `ai-docs/01_code-guidelines.md`
