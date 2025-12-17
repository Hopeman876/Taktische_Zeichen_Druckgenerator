# Release Notes v0.7.2 - Bugfixes Modus-Wechsel

**Datum:** 2025-11-10
**Version:** 0.7.2 (Beta)
**Typ:** Bugfix-Release

---

## 🐛 Behobene Fehler

### KRITISCH: Checkbox-Deaktivierung beim Modus-Wechsel
**Problem:** Beim Wechsel des Modus zu "Dateiname" für ein einzelnes Zeichen wurden ALLE ausgewählten Checkboxen in der Zeichenliste deaktiviert. Dies trat nur beim ersten Modus-Wechsel auf.

**Ursache:** Die Highlighting-Funktionen `_highlight_row()` und `_highlight_categories()` ändern die visuelle Darstellung der TreeWidget-Items (Hintergrundfarbe, Schriftfarbe). Diese visuellen Änderungen triggerten Qt's `itemChanged`-Signal, das fälschlicherweise als Checkbox-Änderung der Root-Kategorie interpretiert wurde und dadurch rekursiv alle Kinder deaktivierte.

**Lösung:** Die gesamte `_on_modus_changed` Funktion wurde in einem `try/finally`-Block gekapselt, der das `itemChanged`-Signal während der Modus-Änderung disconnected:

```python
self.tree_zeichen.itemChanged.disconnect(self._on_item_changed)
try:
    # Alle Modus-Änderungen inkl. Highlighting
finally:
    self.tree_zeichen.itemChanged.connect(self._on_item_changed)
```

**Betroffene Datei:** `gui/main_window.py:1735-1860`

---

### Text-Persistenz bei Modus-Wechsel auf Dateiebene
**Problem:** Beim Wechsel des Modus für ein einzelnes Zeichen blieb der eingegebene Text visuell und funktional erhalten. Dies führte dazu, dass alter Text bei einem neuen Modus weiterverwendet wurde, obwohl der Modus gewechselt wurde.

**Lösung:** Beim Modus-Wechsel auf Dateiebene wird das Textfeld jetzt automatisch geleert (konsistent mit dem Verhalten auf Kategorieebene). Ausnahme: Beim Modus "Dateiname" wird der Text automatisch aus dem Dateinamen neu gesetzt.

**Betroffene Datei:** `gui/main_window.py:1747-1753`

---

### Import-Fehler: DEFAULT_FONT_SIZE nicht definiert
**Problem:** Nach dem Code-Cleanup fehlte in `export_dialog.py` der Import bzw. die Verwendung von `DEFAULT_FONT_SIZE` aus RuntimeConfig.

**Lösung:** Geändert von `DEFAULT_FONT_SIZE` zu `config.font_size` (RuntimeConfig).

**Betroffene Datei:** `gui/dialogs/export_dialog.py:181`

---

## 🧹 Code-Cleanup

### Entfernung ungenutzter Imports
Im Rahmen der RuntimeConfig-Integration (v0.7.1) wurden viele Konstanten nicht mehr direkt importiert. Diese ungenutzten Imports wurden entfernt:

- **validation_manager.py:** MAX_GRAFIK_GROESSE_MM entfernt
- **text_overlay.py:** 6 ungenutzte Konstanten entfernt (GRAFIK_POSITION_TOP, GRAFIK_POSITION_BOTTOM, BG_COLOR, TEXT_BUFFER_FACTOR, TEXT_ALIGNMENT, TEXT_LEFT_OFFSET_MM)
- **pdf_exporter.py:** Tuple und 3 CUT_LINE_COLOR-Konstanten entfernt
- **taktische_zeichen_generator.py:** 8 ungenutzte Konstanten entfernt

**Vorteil:** Sauberer Code, bessere Wartbarkeit, keine verwaisten Imports.

---

### blockSignals() Optimierung
**Änderung:** In `_on_item_changed` wurde `blockSignals()` auf dem TreeWidget durch gezieltes `disconnect()`/`connect()` des `itemChanged`-Signals ersetzt.

**Grund:** `blockSignals()` auf dem gesamten Widget ist zu weitreichend und kann zu Nebenwirkungen führen (z.B. Verlust der Selection). Das gezielte Disconnect des spezifischen Signals ist präziser.

**Betroffene Datei:** `gui/main_window.py:1990-2006`

---

## 📊 Technische Details

### Signal-Handling-Verbesserungen
Die Signal-Verwaltung in der GUI wurde robuster gestaltet:

1. **Disconnect/Connect statt blockSignals():** Präzisere Kontrolle über Event-Handling
2. **Try/Finally-Pattern:** Garantiert, dass Signals auch bei Exceptions wieder verbunden werden
3. **Debug-Logging:** Erweiterte Debug-Ausgaben für Signal-Flow-Analyse (optional)

### Betroffene Dateien
- `gui/main_window.py` (Haupt-Änderungen)
- `gui/dialogs/export_dialog.py` (RuntimeConfig-Fix)
- `validation_manager.py` (Import-Cleanup)
- `text_overlay.py` (Import-Cleanup)
- `pdf_exporter.py` (Import-Cleanup)
- `taktische_zeichen_generator.py` (Import-Cleanup)
- `constants.py` (Version Update)

---

## 🧪 Test-Empfehlungen für Beta-Tester

### Test 1: Checkbox-Persistenz bei Modus-Wechsel
1. Programm starten
2. Mehrere Zeichen auswählen (Checkboxen aktivieren)
3. Bei einem der Zeichen den Modus auf "Dateiname" wechseln
4. **Erwartung:** Alle anderen Checkboxen bleiben aktiviert

### Test 2: Text-Leerung bei Modus-Wechsel
1. Ein Zeichen auswählen
2. Modus mit Texteingabe wählen (z.B. "Schreiblinie o. Freitext")
3. Text eingeben
4. Modus wechseln (z.B. zu "Ruf")
5. **Erwartung:** Textfeld ist leer
6. Erneut Modus wechseln zu "Dateiname"
7. **Erwartung:** Textfeld enthält automatisch den Dateinamen

### Test 3: Kategorie-Modus-Wechsel
1. Eine Kategorie/Unterkategorie auswählen
2. Modus auf Kategorie-Ebene wechseln
3. **Erwartung:** Alle Kinder übernehmen den Modus, Textfelder werden geleert

---

## ⚠️ Bekannte Einschränkungen

Keine neuen Einschränkungen in diesem Release.

---

## 📝 Hinweise für Entwickler

### Debugging
Falls weiterhin Signal-Probleme auftreten, können die Debug-Ausgaben aktiviert werden:
```python
self.logger.debug(f"_on_modus_changed: item={item.name}, modus={modus_text}")
```

Diese Ausgaben sind bereits im Code vorhanden (Zeile 1733, 1983, 2033, 2038) und können bei Bedarf analysiert werden.

### Code-Review
Die Änderungen in `_on_modus_changed` sind umfangreich (try/finally um gesamte Funktion). Bei zukünftigen Änderungen an dieser Funktion darauf achten, dass alle Operationen innerhalb des try-Blocks bleiben.

---

## 🔄 Nächste Schritte

Für v0.8.0 geplant:
- Weitere Performance-Optimierungen
- Verbesserung der Textbreiten-Validierung (siehe `ai-docs/Geplante_Features/_Sammlung_offene_Punkte.md`)

---

**Feedback bitte an:** Ramon-Hoffmann@gmx.de
