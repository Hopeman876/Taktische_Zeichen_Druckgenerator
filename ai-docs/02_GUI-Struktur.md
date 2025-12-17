# GUI-Struktur - TaktischeZeichenDruckgenerator

Qt-basierte Benutzeroberfläche mit PyQt6

**Letzte Aktualisierung:** 2025-11-20
**Aktuelle Version:** v0.8.2

## 📝 Wichtige Änderungen in v0.8.2

### S1-Layout: Anzahl Schreiblinien statt Schriftgröße

**Widget-Namen geändert:**
- **Alt:** `spin_s1_schreiblinien_fontsize` (6-50pt)
- **Neu:** `spin_s1_anzahl_schreiblinien` (3-10 Zeilen)

**Parameter-Namen geändert:**
- **Alt:** `s1_schreiblinien_fontsize`
- **Neu:** `s1_anzahl_schreiblinien`

**Logik umgekehrt:**
- **Vorher:** User gibt Schriftgröße → System berechnet Zeilenanzahl (Output)
- **Jetzt:** User gibt Zeilenanzahl → System berechnet Schriftgröße (Output)

**Betroffene Dateien:**
- `gui/ui_files/main_window.ui` - Spinbox umkonfiguriert
- `gui/main_window.py` - Berechnungslogik umgekehrt in `_update_s1_line_metrics()`
- Alle Backend-Dateien (constants, runtime_config, settings_manager, generator, pdf_exporter)

**Info-Labels (dynamisch):**
- `label_s1_zeilenhoehe` - Zeigt berechnete Zeilenhöhe (read-only)
- `label_s1_schriftgroesse` - Zeigt berechnete Schriftgröße (read-only)

---

## 🎨 GUI-Entwicklung mit Qt Designer

### ⚠️ WICHTIG: GUI wird MIT Qt Designer erstellt!

**Statische UI-Elemente → Qt Designer (.ui-Dateien)**
- Fenster-Layout, Dialoge
- Buttons, Labels, SpinBoxes
- Layouts (QVBoxLayout, QHBoxLayout, QGridLayout)
- Gespeichert als XML in `gui/ui_files/*.ui`

**Dynamische Inhalte → Python-Code**
- TreeWidget-Items (Zeichen-Liste)
- ComboBox-Inhalte (aus modus_config.py)
- Event-Handler, Datenverarbeitung

---

## 📁 GUI-Verzeichnisstruktur

**Vollständige Projektstruktur:** Siehe `00_Projektbeschreibung.md`

**GUI-Ordner (`gui/`):**
```
gui/
├── __init__.py
├── main_window.py                 # Hauptfenster (lädt main_window.ui)
├── ui_loader.py                   # UI-File Loader
├── modus_config.py                # Modi-Konfiguration (Master)
│
├── ui_files/                      # Qt Designer .ui-Dateien
│   ├── main_window.ui
│   └── export_dialog.ui
│
├── dialogs/                       # Dialog-Fenster
│   ├── export_dialog.py           # Export-Dialog
│   └── settings_dialog.py         # Einstellungen-Dialog
│
└── widgets/                       # Custom Widgets
    ├── svg_preview_widget.py
    └── zeichen_tree_item.py

HINWEIS: modus_*_dialog.py Dateien wurden in v0.8.2 entfernt (ungenutzt).
Alle Modi-Features sind direkt im Hauptfenster implementiert.
```

---

## 📐 Architektur-Regel: Separation of Concerns

**1. UI-Master-Dateien (.ui)**
**Pfad:** `gui/ui_files/*.ui`
**Erstellt mit:** Qt Designer (PyQt6)

Enthält:
- Alle **statischen** GUI-Elemente
- Fenster, Dialoge, Buttons, Labels, Layouts
- Widget-Properties (Größe, Schriftart, etc.)

**2. Konfigurations-Module**
**Pfad:** `gui/modus_config.py`
- Alle **dynamischen/programmatischen** Inhalte, die nicht in .ui-Dateien möglich sind
- ComboBox-Items, Dropdown-Inhalte
- GUI-Labels mit Umlauten
- Mappings (GUI ↔ Intern)
- Platzhalter-Texte
- **NICHT** in GUI-Dateien hardcodieren!

**3. GUI-Python-Dateien (z.B. main_window.py)**
- Laden .ui-Dateien
- Importieren Konfigurations-Module
- Implementieren Geschäftslogik
- Verbinden Signals/Slots
- **KEINE** GUI-Struktur-Definition!
- **KEINE** hardcodierten GUI-Labels/Texte!

---

## 🔧 Modi-Konfiguration (modus_config.py)

### Zweck
Zentrale Master-Definition für alle Modi-bezogenen GUI-Elemente und Mappings.

**Warum ein separates Modul?**
- GUI-Dateien dürfen keine hardcodierten Labels enthalten
- .ui-Dateien können keine dynamischen ComboBox-Items definieren
- Zentrale Wartbarkeit: Eine Änderung → Überall wirksam
- Unterstützung für Umlaute in GUI-Labels

### Struktur

**1. GUI-Labels (Master-Liste)**

**Modi-Liste:** Siehe [00_Projektbeschreibung.md](00_Projektbeschreibung.md) - 7 Modi im Detail

```python
MODUS_GUI_LABELS: List[str] = [
    "OV + Stärke", "Ort + Stärke", "Schreiblinie + Stärke",
    "Schreiblinie o. Freitext", "Ruf", "Dateiname", "Nur Grafik"
]
```

**2. Mappings (GUI ↔ Intern)**
```python
MODUS_GUI_TO_INTERNAL: Dict[str, str] = {"OV + Stärke": "ov_staerke", ...}
MODUS_INTERNAL_TO_GUI: Dict[str, str] = {"ov_staerke": "OV + Stärke", ...}
```

**3. Platzhalter-Texte**
```python
MODUS_PLACEHOLDER_TEXT: Dict[str, str] = {"ov_staerke": "OV-Name", ...}
```

**4. Helper-Funktionen**
```python
def get_modus_gui_labels() -> List[str]:
    """Gibt GUI-Labels für ComboBox zurück"""

def gui_to_internal(gui_label: str) -> str:
    """Konvertiert GUI-Label zu internem Wert"""

def internal_to_gui(internal_value: str) -> str:
    """Konvertiert internen Wert zu GUI-Label"""

def get_placeholder_text(internal_value: str) -> str:
    """Gibt Platzhalter-Text für Textfeld zurück"""
```

### Verwendung in GUI-Code

```python
from gui.modus_config import get_modus_gui_labels, gui_to_internal, internal_to_gui

combo_modus.addItems(get_modus_gui_labels())              # ComboBox füllen
internal = gui_to_internal(combo_modus.currentText())      # GUI → Intern
gui_label = internal_to_gui(item.params.modus)             # Intern → GUI
```

### Vorteile

✅ **Single Source of Truth** - Alle Labels an einer Stelle
✅ **Einfache Wartung** - Änderung an einer Stelle wirkt überall
✅ **Unterstützt Umlaute** - "Stärke" statt "Staerke"
✅ **Klare Trennung** - GUI-Code bleibt sauber
✅ **Testbar** - Modul kann isoliert getestet werden
✅ **Erweiterbar** - Neue Modi einfach hinzufügen

---

## 🖥️ Hauptfenster (main_window.py)

### Layout-Übersicht (v0.6.1)

```
+----------------------------------------------------------------------+
| Menü: Datei  Einstellungen  Hilfe                                   |
+----------------------------------------------------------------------+
| [Ordner wählen] [Neu laden] [Export]                                |
+----------------------------------------------------------------------+
|                        |                          |                  |
| Kategorien (Links)     | Zeichen-Liste (Mitte)    | Vorschau (Rechts)|
| (TreeWidget)           | (TreeWidget mit Items)   | (SVGPreviewWidget)|
|                        |                          |                  |
| + Kategorie1 (5)       | □ Zeichen1.svg           | [SVG-Bild]       |
|   + Unterkat (2)       |   Modus: OV+Stärke       |                  |
| + Kategorie2 (3)       |   Text: ___              | Zeichen1.svg     |
|                        |   Kopien: 1              | Kategorie1       |
|                        | □ Zeichen2.svg           |                  |
|                        |   Modus: Ruf             | Modus: [v]       |
|                        |   ...                    | Text: [____]     |
|                        |                          | [OV] [Ruf]       |
|                        |                          | [Ohne] [Frei]    |
+----------------------------------------------------------------------+
| Zeichen: 8 ausgewählt | Zeichengröße: 90×80mm | DPI: 600          |
+----------------------------------------------------------------------+
```

### Komponenten

#### 1. Kategorien-Browser (links)
- **Widget:** `QTreeWidget`
- **Funktion:** Zeigt Kategorien aus `Taktische_Zeichen_Grafikvorlagen/`
- **Features:**
  - Rekursive Unterordner-Darstellung
  - Anzahl Zeichen pro Kategorie
  - Single-Selection

#### 2. Zeichen-Liste (Mitte)
- **Widget:** `QListWidget`
- **Funktion:** Zeigt SVG-Dateien der gewählten Kategorie
- **Features:**
  - Dateiname ohne Endung
  - Single-Click: Vorschau
  - Double-Click: Standard-Dialog (OV+Stärke)

#### 3. Vorschau-Bereich (rechts)
- **Widget:** `QLabel` (aktuell) → `SVGPreviewWidget` (geplant)
- **Funktion:** Zeigt SVG-Vorschau
- **Features:**
  - SVG-Rendering
  - Datei-Informationen
  - 4 Modus-Buttons

#### 4. Menüleiste
- **Datei:**
  - Ordner öffnen... (Strg+O)
  - Neu laden (F5)
  - Export... (Strg+E)
  - Beenden (Strg+Q)
- **Batch:**
  - Excel-Import...
- **Hilfe:**
  - Über...

#### 5. Statusleiste
- Zeigt aktuelle Informationen
- Anzahl Kategorien/Zeichen
- Fehler-Meldungen

---

## 🔧 UI-Loader (ui_loader.py)

### Zweck
Lädt Qt Designer .ui Dateien und bindet sie an Python-Klassen

### Verwendung

```python
from gui.ui_loader import UILoader

# Variante 1: Standalone Loading
widget = UILoader.load_widget("my_dialog.ui")

# Variante 2: In existierende Klasse laden
class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        UILoader().load_ui("my_dialog.ui", self)
        # Jetzt sind alle Widgets aus .ui verfügbar
```

### Methoden

- `load_ui(filename, base_instance)` - Flexibles Laden
- `load_widget(filename, parent)` - Lädt als QWidget
- `load_window(filename)` - Lädt als QMainWindow
- `load_dialog(filename, parent)` - Lädt als QDialog

---

## 📝 Modi-Konfiguration im Hauptfenster

**Status (v0.8.2):** Modi-spezifische Dialoge wurden entfernt (ungenutzt).
Alle Modi-Parameter werden direkt im Hauptfenster konfiguriert.

**Implementierung:**
- Alle 7 Modi haben dedizierte Bereiche im Hauptfenster
- GroupBoxes für Modi-Einstellungen (S1-Layout, S2-Layout, etc.)
- Live-Vorschau integriert
- Keine separaten Dialoge nötig

**Details zu Modi:** Siehe `00_Projektbeschreibung.md` und `gui/modus_config.py`

---

## 📤 Export-Dialog (TODO)

**Datei:** `gui/dialogs/export_dialog.py`

**Features:**
- Format-Wahl: PNG/JPG/SVG/PDF
- DPI-Einstellung: 300-1200
- Ausgabepfad wählen
- Schnittlinien: Ja/Nein
- Wiederholungen pro Zeichen
- Live-Vorschau

**Layout:**
```
Export-Einstellungen
====================

Format:         [PNG v]
DPI:            [600]
Ausgabepfad:    [C:\...\Taktische_Zeichen_Ausgabe] [Durchsuchen]

[ ] Schnittlinien anzeigen

Wiederholungen: [1]

[Vorschau]

[Abbrechen] [Exportieren]
```

---

## 📊 Batch-Import-Dialog (TODO)

**Datei:** `gui/dialogs/batch_import_dialog.py`

**Features:**
- Excel/CSV-Import
- Spalten-Mapping
- Zeitschätzung
- Progress-Bar
- Multithreading (4 Threads)
- Fehler-Handling

**Workflow:**
1. Excel/CSV auswählen
2. Spalten zuordnen (Zeichen, Modus, OV, Stärke, etc.)
3. Vorschau der ersten 5 Einträge
4. Zeitschätzung anzeigen
5. Batch starten
6. Progress-Bar mit Fortschritt

---

## 🎨 SVG-Vorschau-Widget (TODO)

**Datei:** `gui/widgets/svg_preview_widget.py`

**Features:**
- Echtes SVG-Rendering mit Wand/ImageMagick
- Zoom/Pan-Funktionalität
- Größenanpassung
- Cache für Performance

**Verwendung:**
```python
from gui.widgets.svg_preview_widget import SVGPreviewWidget

preview = SVGPreviewWidget(parent)
preview.load_svg(Path("zeichen.svg"))
preview.set_size(400, 400)
```

---

## 🚀 Einstiegspunkt (main.py)

**Datei:** `main.py` (Root-Verzeichnis)

**Funktion:**
- Startet Qt-Anwendung
- Initialisiert LoggingManager
- Zeigt MainWindow
- Startet Event-Loop

**Verwendung:**
```bash
python main.py
```

---

## 📋 Implementierungs-Status (v0.6.1)

### ✅ Vollständig implementiert
- [x] GUI-Struktur (`gui/` Package)
- [x] MainWindow mit 3-Spalten-Layout
- [x] Kategorien-Browser (TreeWidget, rekursiv)
- [x] Zeichen-Liste (TreeWidget mit Custom Items)
- [x] SVG-Vorschau (Wand-Rendering, gecacht)
- [x] **7 Modi** (siehe [00_Projektbeschreibung.md](00_Projektbeschreibung.md))
- [x] **Alle Modus-Dialoge** implementiert
- [x] **Export-Dialog** (PNG/PDF, Einzelzeichen/Schnittbögen)
- [x] **Settings-Dialog** (Zeichengröße, DPI, Rand, Pfade)
- [x] Batch-Export (Multithreading, Progress-Anzeige)
- [x] Validierung (Text-Länge, Pfade)
- [x] Blanko-Zeichen (virtuelle Kategorie)
- [x] Integration mit Generator

### 🔄 Verbesserungspotential
- [ ] Export-Vorschau in Dialog
- [ ] Batch-Import (Excel/CSV)
- [ ] Undo/Redo für Zeichen-Parameter
- [ ] Icon-Set
- [ ] Tastenkürzel optimieren

---

## 🔗 Integration mit Backend

### TaktischeZeichenGenerator

```python
from taktische_zeichen_generator import TaktischeZeichenGenerator

generator = TaktischeZeichenGenerator()
output = generator.create_zeichen(svg_path, modus="ov_staerke", output_format="PNG")
results = generator.create_zeichen_batch(zeichen_list, modus, num_threads=4, progress_callback=...)
```

### SVGLoaderLocal

```python
from svg_loader_local import SVGLoaderLocal

loader = SVGLoaderLocal(Path("Taktische_Zeichen_Grafikvorlagen"))
categories = loader.scan_available_zeichen()           # {'Einheiten': 5, ...}
zeichen = loader.get_zeichen_by_category("Einheiten")  # [Path('N.svg'), ...]
```

---

## 🎯 Nächste Schritte

1. **SVG-Vorschau-Widget implementieren**
   - Wand/ImageMagick Integration
   - QPixmap Rendering
   - Cache-System

2. **OV+Stärke Dialog erstellen**
   - UI-Design
   - Validierung
   - Live-Vorschau
   - Integration mit Generator

3. **Export-Dialog implementieren**
   - Format-Auswahl
   - DPI-Einstellung
   - Datei-Dialog

4. **Batch-Import-Dialog**
   - Excel-Import mit openpyxl
   - Progress-Bar
   - Multithreading

---

---

**Naechste Datei fuer KI:** Lese als naechstes `ai-docs/03_general-guidelines.md`
