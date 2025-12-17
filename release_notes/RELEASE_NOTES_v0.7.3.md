# Release Notes v0.7.3 - Settings Dialog

**Release-Datum:** 2025-11-13
**Version:** v0.7.3

## Neue Features

### Settings Dialog (Programmeinstellungen)
- **Zugriff:** Menüleiste → Datei → Einstellungen... (Tastenkürzel: `Ctrl+,`)
- **Beschreibung:** Umfassender Einstellungsdialog für alle Programmeinstellungen

#### Tab 1: Standard-Werte
- **Zeichengröße:** Höhe und Breite (10-200mm)
- **Abstände:**
  - Beschnittzugabe (0-20mm)
  - Sicherheitsabstand (0-20mm)
  - Abstand Grafik ↔ Text (0-20mm)
  - Abstand Text ↔ Unterrand (0-20mm)
- **Schrift:**
  - Schriftart (Dropdown mit allen verfügbaren Systemschriften)
  - Schriftgröße (6-72pt)
- **Standard-Modus:** Auswahl des Standard-Textmodus für neue Zeichen
  - OV + Stärke
  - Ort + Stärke
  - Rufname
  - Freitext
  - Ohne Text
  - Dateiname
- **Grafik:**
  - Position (Oben, Mittig, Unten)
  - Maximale Höhe (10-100mm)
  - Maximale Breite (10-100mm)
- **Button "Standard wiederherstellen":** Setzt alle Werte auf Factory Defaults aus `constants.py`

#### Tab 2: Logging
- **Log-Level:** Auswahl per Radio-Buttons
  - DEBUG - Detaillierte Debugging-Informationen
  - INFO - Normale Programmausführung (Standard)
  - WARNING - Warnungen und wichtige Hinweise
  - ERROR - Nur Fehler
- **Max. Anzahl Logfiles:** Konfiguration (1-100, aktuell Placeholder)
- **Informationen:**
  - Anzeige des Log-Verzeichnisses
  - Anzeige der aktuellen Log-Größe
- **Buttons:**
  - "Logs öffnen" - Öffnet Log-Verzeichnis im Windows Explorer
  - "Logs löschen" - Löscht alle Log-Dateien nach Bestätigung

#### Tab 3: Erweitert
- **Zeichen-Ordner:**
  - Anzeige des aktuellen Pfads
  - Button "Durchsuchen" für Ordnerauswahl
- **Performance-Einstellungen:**
  - Template-Optimierung (fest aktiviert)
  - Chunk-basierte Verarbeitung (fest aktiviert)
- **ImageMagick Status:**
  - Verfügbarkeit-Status
  - Versions-Information (automatisch erkannt)

#### Funktionalität
- **OK-Button:** Speichert Einstellungen in `settings.json` und schließt Dialog
- **Anwenden-Button:** Speichert Einstellungen ohne Dialog zu schließen
- **Abbrechen-Button:** Verwirft alle Änderungen und schließt Dialog
- **Automatische Aktualisierung:** Nach Speichern wird RuntimeConfig neu geladen und Main Window aktualisiert
- **Validierung:**
  - Zeichen-Ordner muss existieren
  - Grafik-Größe darf nicht größer als Zeichen-Größe sein
  - SpinBox-Bereiche automatisch validiert

## Technische Details

### Neue Dateien
1. **gui/dialogs/settings_dialog.py** (528 Zeilen)
   - Qt Dialog-Klasse mit kompletter Logik
   - Trennung von UI und Logik (Qt Designer kompatibel)
   - Umfassende Fehlerbehandlung und Logging

2. **gui/ui_files/settings_dialog.ui** (753 Zeilen)
   - Qt Designer UI-Definition
   - 3-Tab-Struktur mit allen Widgets
   - Vollständig editierbar in Qt Designer (qtpy6)

### Modifizierte Dateien
1. **gui/main_window.py**
   - `_on_einstellungen()`: TODO entfernt, vollständige Implementierung
   - Dialog öffnen und Ergebnis verarbeiten
   - RuntimeConfig reload nach Speichern

2. **runtime_config.py**
   - Neue Methode `reload_from_settings()`: Lädt `settings.json` neu und aktualisiert RuntimeConfig
   - Wird vom Settings Dialog nach Speichern aufgerufen

### Architektur
- **UI/Logic Separation:** UI in .ui-Datei, Logik in .py-Datei
- **Qt Designer Support:** Vollständig editierbar via Qt Designer
- **Settings Flow:**
  1. Dialog lädt Werte aus `settings.json` via `SettingsManager`
  2. Benutzer ändert Werte
  3. Dialog speichert in `settings.json`
  4. `RuntimeConfig.reload_from_settings()` aktualisiert Runtime-Werte
  5. Main Window lädt aktualisierte Settings

### Validierung
- **Pfad-Validierung:** Zeichen-Ordner muss existieren
- **Logik-Validierung:** Grafik-Größe ≤ Zeichen-Größe
- **Range-Validierung:** Automatisch durch QSpinBox/QDoubleSpinBox Min/Max

### Logging
- Alle Aktionen werden geloggt (INFO-Level)
- Fehler mit vollständigem Stack-Trace (ERROR-Level)
- Debug-Informationen für Entwicklung

## Bekannte Einschränkungen
- **Max. Logfiles:** Aktuell Placeholder (10), nicht funktional implementiert
- **Schriftart-Speicherung:** Wird aktuell noch nicht in `settings.json` gespeichert (kommt in v7.4)
- **Performance-Flags:** Fest aktiviert, nicht änderbar (bewusste Design-Entscheidung)

## Nächste Schritte (geplant für v7.4)
- Schriftart und Schriftgröße in `settings.json` speichern und anwenden
- Max. Logfiles funktional implementieren in `LoggingManager`
- Runtime-Anwendung von Log-Level (aktuell erst nach Neustart aktiv)
- Erweiterte Validierung für Schrift-Verfügbarkeit

## Migration
- **Keine Migration erforderlich**
- Bestehende `settings.json` bleibt kompatibel
- Neue Einstellungen haben sinnvolle Defaults aus `constants.py`

## Kompatibilität
- **PyQt6:** Kompatibel
- **Qt Designer:** Vollständig kompatibel
- **Python:** 3.9+
- **Windows:** Getestet auf Windows 10/11

---

**Wichtig:** Nach dem Update können alle Programmeinstellungen über das Menü (Datei → Einstellungen...) bearbeitet werden. Die Einstellungen werden sofort in `settings.json` gespeichert und zur Laufzeit aktualisiert.
