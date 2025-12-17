# General Guidelines - Allgemeine Richtlinien

**Projekt:** Taktische Zeichen Druckgenerator
**Aktuelle Version:** Siehe AKTUELL_Projektstand_*.md
**Datum:** 2025-10-26

---

## Dokumentations-Struktur

### Speicherort

**ALLE Dokumentationen muessen im Ordner `ai-docs/` abgelegt werden!**

Dies betrifft:
- Projektbeschreibungen
- Code-Guidelines
- Architektur-Dokumentationen
- GUI-Dokumentationen
- Installations-Anleitungen
- README-Dateien
- Projektstaende (aktuell und archiviert)

### Dokumentations-Übersicht

**Vollständige Liste und Lesereihenfolge:** Siehe `00_LESE_MICH_ZUERST.md`

**Basis-Dokumentationen (in Lesereihenfolge):**
1. `00_Projektbeschreibung.md` - Projekt-Übersicht
2. `01_code-guidelines.md` - Code-Konventionen (ZWINGEND!)
3. `02_GUI-Struktur.md` - GUI-Architektur
4. `03_general-guidelines.md` - Diese Datei
5. `04_RuntimeConfig-Guidelines.md` - RuntimeConfig (ZWINGEND!)
6. `AKTUELL_Projektstand_*.md` - Aktueller Status

---

## Versionierung und Git

### Commit-Strategie

**Commits nur auf explizite Anweisung des Users!**

Der User entscheidet, wann ein Commit erstellt wird. Die KI soll:
- **NICHT** proaktiv Commits vorbereiten
- **NICHT** ungefragt `git add` oder `git commit` ausfuehren
- Nur auf explizite Aufforderung committen

### Commit-Messages

Format (Google-Style):
```
<Typ>: <Kurzbeschreibung>

<Detaillierte Beschreibung falls noetig>
```

Typen:
- `Feature:` - Neue Funktionalitaet
- `Fix:` - Bugfix
- `Refactor:` - Code-Umstrukturierung
- `Docs:` - Dokumentations-Aenderungen
- `Test:` - Test-Aenderungen
- `Chore:` - Build/Config-Aenderungen

### Branches

- `master` - Haupt-Branch (stabil)
- Feature-Branches bei Bedarf

---

## Projekt-Struktur

### Verzeichnis-Layout

```
Taktische_Zeichen_Druckgenerator/
├── ai-docs/                                    # ALLE Dokumentationen außer Release notes
├── gui/                                        # GUI-Code
│   ├── ui_files/                               # Qt Designer .ui Dateien (MASTER!)
│   ├── dialogs/                                # Dialog-Klassen
│   └── widgets/                                # Custom Widgets
├── release_notes/                              # Release notes. Enthält auch die älteren Stände
├── Taktische_Zeichen_Ausgabe/                  # Generierte Zeichen
├── Taktische_Zeichen_Grakfikvorlagen/          # SVG-Vorlagen (Kategorien)
├── *.py                       # Core-Module (Top-Level)
└── main.py                    # Einstiegspunkt
```

### UI-Dateien als Master

**WICHTIG:** Die `.ui` Dateien (Qt Designer) sind der Master fuer GUI-Strukturen!

**Regel 1: Statische UI-Elemente**
- GUI-Aenderungen im Qt Designer vornehmen (Fenster, Dialoge, Buttons, Labels, etc.)
- Python-Code laedt .ui Dateien dynamisch
- **NICHT** programmatisch GUI in GUI-Dateien erstellen
- GUI-Dateien (`gui/*.py`, `gui/dialogs/*.py`) duerfen **NUR** .ui-Dateien laden und Logik hinzufuegen

**Regel 2: Dynamische/Programmatische Elemente**
- Was **technisch nicht** in .ui-Dateien moeglich ist (z.B. dynamische TreeWidget-Items, ComboBox-Inhalte), **MUSS** in separaten Konfigurations-Modulen erstellt werden
- **NICHT** direkt in GUI-Dateien hardcodieren
- Separate Konfigurations-Module verwenden

**Beispiele fuer Konfigurations-Module:**
- `gui/modus_config.py` - Zentrale Definition von GUI-Labels, Mappings und Platzhaltern fuer Modi
  - Alle ComboBox-Items fuer Modi
  - GUI-Label ↔ Interner-Wert Mappings
  - Platzhalter-Texte
  - Helper-Funktionen (get_modus_gui_labels(), gui_to_internal(), etc.)

**Vorteile dieser Trennung:**
- GUI-Dateien bleiben sauber (nur UI-Loading + Logik)
- Konfigurationen sind zentral wartbar
- Aenderungen an Labels/Texten erfolgen an **einer** Stelle
- Klare Separation of Concerns

Details siehe: `ai-docs/UI_MIGRATION.md`

---

## Dokumentations-Richtlinien

### Format

- **Markdown** (.md) fuer alle Dokumentationen
- UTF-8 Encoding
- Klare Struktur mit Headings (#, ##, ###)
- Code-Bloecke mit Syntax-Highlighting

### Sprache

- **Deutsch** fuer User-facing Dokumentation
- **Deutsch** fuer Kommentare im Code
- **Englisch** fuer Variablen/Funktionsnamen (siehe Code-Guidelines)

### Aktualitaet

- Projektstaende mit Versionsnummer und Datum
- Alte Projektstaende nach `Alte_Projektstaende/` verschieben und von "AKTUELl_Projektstand_*.md" in "VERALTET_Projektstand_*.md" umbenennen
- `AKTUELL_Projektstand_*.md` immer auf neuem Stand halten

---

## Testing

### Vor Commits

- **IMMER** das Programm testen bevor committed wird
- Start: `python main.py`
- Funktionalitaet pruefen
- Keine Errors im Log

### Test-Dateien

Test-Dateien (z.B. `test_*.py`, `quick_test_*.py`) sind OK, aber:
- Nicht committen ohne Absprache
- Im Root-Verzeichnis oder `tests/` Ordner
- Klar benennen

---

## UI/UX Richtlinien

### Fenstergrössen

- **Standard-Groesse:** Nicht zu gross beim Start
- **Minimum-Groesse:** Sinnvoll setzen (nicht zu klein)
- **Responsive:** Layouts sollen sich anpassen

### Qt Designer Best Practices

1. **Layouts verwenden** (nicht absolute Positionen)
2. **ObjectNames** aussagekraeftig benennen
3. **Spacing/Margins** konsistent halten
4. **Size Policies** sinnvoll setzen

---

## Logging

### LoggingManager verwenden

```python
from logging_manager import LoggingManager

logger = LoggingManager().get_logger(__name__)
logger.info("Message")
logger.debug("Debug info")
logger.error("Error occurred")
```

### Log-Levels

- `DEBUG` - Entwicklung (detailliert)
- `INFO` - Normale Ausgaben
- `WARNING` - Warnungen (nicht kritisch)
- `ERROR` - Fehler (aber Programm laeuft weiter)

---

## Performance

### SVG-Rendering

- Wand/ImageMagick fuer SVG → PNG Konvertierung
- Preview-Widget cached gerenderte Bilder
- Groesse anpassbar (siehe `SVGPreviewWidget`)

### Kategorien-Scanning

- Rekursives Scanning unterstuetzt Unterkategorien
- Caching bei Bedarf
- Performance-Tests bei grossen Ordnern

---

## Datei-Konventionen

### Python-Dateien

- `snake_case.py` fuer Dateinamen
- Keine Leerzeichen, keine Umlaute
- Aussagekraeftige Namen

### UI-Dateien

- `widget_name.ui` (z.B. `main_window.ui`)
- Im Ordner `gui/ui_files/`
- Pro Dialog/Window eine .ui Datei

### Dokumentationen

- `UPPERCASE_Name.md` fuer wichtige Docs (z.B. `README.md`)
- `00_Name.md` fuer nummerierte Haupt-Docs
- `lowercase_name.md` fuer Detail-Docs

### Export-Ausgabe-Dateien (v0.6.1)

**Ordner-Konvention (PNG & PDF):**
```
YYYY-MM-DD_hh-mm_<Dateiformat>_<Exportformat>_<Anzahl>_Zeichen_<DPI>_dpi/
```

**Beispiele:**
```
2025-11-02_14-30_PNG_Einzelzeichen_540_Zeichen_600_dpi/
  ├── Zeichen_001.png
  ├── Zeichen_002.png
  └── ...

2025-11-02_14-30_PDF_Einzelzeichen_540_Zeichen_600_dpi/
  ├── 2025-11-02_14-30_Einzelzeichen_Zeichen_1_bis_100_Datei_1_von_6.pdf
  ├── 2025-11-02_14-30_Einzelzeichen_Zeichen_101_bis_200_Datei_2_von_6.pdf
  └── ...

2025-11-02_14-30_PDF_Schnittbogen_540_Zeichen_600_dpi/
  ├── 2025-11-02_14-30_Schnittbogen_Zeichen_1_bis_20_Datei_1_von_27.pdf
  ├── 2025-11-02_14-30_Schnittbogen_Zeichen_21_bis_40_Datei_2_von_27.pdf
  └── ...
```

**Format-Erklärung:**
- `YYYY-MM-DD_hh-mm` - Zeitstempel (z.B. 2025-11-02_14-30)
- `<Dateiformat>` - PNG oder PDF
- `<Exportformat>` - Einzelzeichen oder Schnittbogen
- `<Anzahl>_Zeichen` - Anzahl taktischer Zeichen (z.B. 540_Zeichen)
- `<DPI>_dpi` - Auflösung (z.B. 600_dpi)

**PDF-Dateinamen (innerhalb Ordner):**
```
YYYY-MM-DD_hh-mm_<Exportformat>_Zeichen_<Start>_bis_<Ende>_Datei_<Idx>_von_<Total>.pdf
```

**Chunking:**
- **PNG:** Keine Chunks (alle in einem Ordner)
- **PDF Einzelzeichen:** 100 Zeichen/Datei (konfigurierbar)
- **PDF Schnittbögen:** 20 Zeichen/Datei = 5 Seiten (konfigurierbar)

**Implementierung (constants.py):**
```python
EXPORT_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M"
EXPORT_FOLDER_TEMPLATE = "{timestamp}_{file_format}_{export_format}_{count}_Zeichen_{dpi}_dpi"
EXPORT_PDF_FILENAME_TEMPLATE = "{timestamp}_{export_format}_Zeichen_{start}_bis_{end}_Datei_{idx}_von_{total}.pdf"

# Funktionen:
create_export_folder_name(count, dpi, file_format, export_format)
create_pdf_filename(timestamp, export_format, start_idx, end_idx, file_idx, total_files)
```

---

## Naechste Schritte fuer KI

Nach dem Einlesen dieser Guidelines:

**Lese als naechstes:** `ai-docs/04_RuntimeConfig-Guidelines.md`