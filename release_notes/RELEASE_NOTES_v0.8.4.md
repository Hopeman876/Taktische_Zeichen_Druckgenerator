# Release Notes v0.8.4 - Seitenverhältnis-Konfiguration & Bugfix Release

**Release-Datum:** 2025-12-14
**Version:** v0.8.4

---

## 🎉 Highlights dieser Version

Version 0.8.4 bringt eine **neue Konfigurations-Option für Seitenverhältnisse** und behebt **kritische Bugs** bei der Berechnung von Zeichenabmessungen. Die Seitenverhältnis-Fixierung für S1 (2:1) und S2 (1:1) ist nun global einstellbar und persistent.

**Wichtigste Änderungen:**
- **Seitenverhältnis-Fixierung konfigurierbar** - Beide Layouts (S1 und S2) können im Einstellungsdialog konfiguriert werden
- **Standard: Fixierte Seitenverhältnisse** - S1 (2:1) und S2 (1:1) sind standardmäßig aktiviert
- **Kritischer Bugfix: Aspekt-Berechnungen** - Berechnungen funktionieren sofort bei der ersten Änderung
- **Kritischer Bugfix: Feld-Sperrung beim Start** - Breite-Feld wird korrekt gesperrt wenn Seitenverhältnis fixiert ist
- **Deutsche Rechtschreibung korrigiert** - "Druckgröße" statt "Druckgroesse"
- **Benutzerhandbuch erweitert** - Neues Kapitel zu Seitenverhältnis-Fixierung

---

## ✨ Neue Features

### Seitenverhältnis-Fixierung konfigurierbar

**Feature:**
Die Seitenverhältnis-Fixierung für S1- und S2-Layout kann nun global im Einstellungsdialog konfiguriert werden.

**Wo:**
- Einstellungsdialog → "Zeichengröße" → Checkboxen für S1 und S2

**Vorteile:**
- ✅ **Persistent:** Einstellungen werden in `settings.json` gespeichert
- ✅ **Flexibel:** Jedes Layout einzeln konfigurierbar
- ✅ **Intuitiv:** Checkboxen direkt unter den Abmessungsfeldern
- ✅ **Standard-Verhalten:** Beide Seitenverhältnisse standardmäßig fixiert

**Technische Details:**
- **S1-Layout:** Seitenverhältnis 2:1 (Breite = 2 × Höhe)
- **S2-Layout:** Seitenverhältnis 1:1 (Breite = Höhe)
- Breite-Feld wird automatisch gesperrt/entsperrt basierend auf Checkbox-Status
- Änderungen werden sowohl im Dialog als auch im Hauptfenster gespeichert

**Betroffene Dateien:**
- `gui/ui_files/settings_dialog.ui`: Zeilen für Checkboxen in "Zeichengröße" GroupBox
- `gui/dialogs/settings_dialog.py`: Zeilen 223-234 (laden), 351-353 (speichern)
- `settings_manager.py`: Zeile 56 (Default: `aspect_locked = True`)
- `gui/main_window.py`: Zeile 847 (S2 aspect_locked speichern)

**Screenshot:**
```
[Zeichengröße]
  Höhe (mm): [40]  Breite (mm): [80]
  ☑ S1-Seitenverhältnis 2:1 fixieren (Breite = 2 x Höhe)
  ☑ S2-Seitenverhältnis 1:1 fixieren (Breite = Höhe)
```

---

## 🐛 Bugfixes

### Kritisch: Aspekt-Berechnung verzögert und fehlerhaft

**Problem:**
```
Breite wird erst ab der zweiten Änderung nachgeführt und dann falsch berechnet
```

**Symptome:**
- Beim Ändern der Höhe wurde die Breite nicht sofort angepasst
- Erst bei der **zweiten** Änderung der Höhe wurde die Breite berechnet
- Die berechnete Breite war falsch (nicht 2:1 bzw. 1:1)

**Ursache:**
- **Signal Handler Reihenfolge war falsch!**
- `_on_settings_changed()` wurde **VOR** `_on_aspect_lock()` aufgerufen
- Alte (noch nicht berechnete) Werte wurden in Settings gespeichert
- Bei nächster Änderung wurden alte Werte geladen und dann erst berechnet

**Falsche Reihenfolge (BUG):**
```python
self.spin_s1_zeichen_hoehe.valueChanged.connect(self._on_settings_changed)        # ZUERST
self.spin_s1_zeichen_hoehe.valueChanged.connect(self._on_s1_aspect_lock)          # DANACH
```

**Korrekte Reihenfolge (FIX):**
```python
self.spin_s1_zeichen_hoehe.valueChanged.connect(self._on_s1_aspect_lock)          # ZUERST
self.spin_s1_zeichen_hoehe.valueChanged.connect(self._on_s1_zeichen_size_changed)
self.spin_s1_zeichen_hoehe.valueChanged.connect(self._on_settings_changed)        # DANACH
self.spin_s1_zeichen_hoehe.valueChanged.connect(self._update_recommended_font_size)
```

**Warum das wichtig ist:**
1. **Berechnung zuerst:** `_on_aspect_lock()` berechnet neue Breite basierend auf Höhe
2. **Größen-Update:** `_on_zeichen_size_changed()` aktualisiert Anzeigen
3. **Speichern danach:** `_on_settings_changed()` speichert **korrekte** Werte
4. **Font-Update zuletzt:** `_update_recommended_font_size()` mit neuen Werten

**Fix:**
- S1-Layout: Signal-Handler-Reihenfolge korrigiert (Zeilen 353-356)
- S2-Layout: Signal-Handler-Reihenfolge korrigiert (Zeilen 305-308)

**Betroffene Dateien:**
- `gui/main_window.py`: Zeilen 305-308 (S2), 353-356 (S1)

**Commits:**
- `d544b55` - fix: S1 aspect ratio calculation now updates immediately
- `e927232` - fix: S2 aspect ratio calculation now updates immediately

---

### Kritisch: Breite-Feld nicht gesperrt beim Programmstart

**Problem:**
- Wenn Programm mit fixiertem Seitenverhältnis (S2) gestartet wurde
- Checkbox war aktiviert (☑ S2-Seitenverhältnis 1:1 fixieren)
- **ABER:** Breite-Feld war noch editierbar (sollte gesperrt sein)
- Erst nach manueller Checkbox-Änderung wurde Feld gesperrt

**Ursache:**
- `_on_s2_aspect_locked_changed()` wurde nur bei Checkbox-Änderungen aufgerufen
- Beim Laden der Settings aus `settings.json` wurde Checkbox gesetzt
- **ABER:** Handler wurde nie initial aufgerufen → Feld blieb entsperrt

**Fix:**
Nach dem Laden der Checkbox-Einstellung wird Handler explizit aufgerufen:

```python
# NEW v0.8.4: Aspect-Lock initial anwenden (sperrt Breite-Feld wenn aktiviert)
self._on_s2_aspect_locked_changed()
```

**Betroffene Dateien:**
- `gui/main_window.py`: Zeile 456

**Commit:**
- `8684bc2` - fix: S2 width field not locked on startup, fix "Druckgroesse" typo

---

### UI: Deutsche Rechtschreibung korrigiert

**Problem:**
- GUI zeigte "Druckgroesse" statt korrektem Deutsch "Druckgröße"
- Mehrere Labels betroffen (S1 und S2)

**Fix:**
Alle benutzer-sichtbaren Texte korrigiert:
- `label_s1_druckgroesse.setText("Druckgröße S1:")` (Zeile 775)
- `label_s2_druckgroesse.setText("Druckgröße S2:")` (Zeile 799)
- Kommentare von "Druckgroessen" zu "Druckgrößen" aktualisiert

**Hinweis:**
- Technische Element-Namen (z.B. `label_s2_druckgroesse`) bleiben unverändert
- Nur **Display-Texte** wurden korrigiert

**Betroffene Dateien:**
- `gui/main_window.py`: Verschiedene Zeilen (775, 799, etc.)

**Commit:**
- `8684bc2` - fix: S2 width field not locked on startup, fix "Druckgroesse" typo

---

### UI: Checkbox-Platzierung und Reihenfolge optimiert

**Problem:**
- Checkboxen waren ursprünglich unter "Programmverhalten"
- Nicht logisch gruppiert (gehören zu Zeichengröße)
- S2-Checkbox vor S1-Checkbox (unlogische Reihenfolge)

**Fix:**
1. **Checkboxen verschoben:** Von "Programmverhalten" zu "Zeichengröße"
2. **Platzierung:** Direkt unter den Höhe/Breite-Eingabefeldern
3. **Reihenfolge korrigiert:** S1-Checkbox (Zeile 2) vor S2-Checkbox (Zeile 3)

**Vorher:**
```
[Programmverhalten]
  Standard-Layout: [S2 Quadrat]
  ☑ S2-Seitenverhältnis 1:1 fixieren
  ☑ S1-Seitenverhältnis 2:1 fixieren  <-- S1 nach S2
```

**Nachher:**
```
[Zeichengröße]
  Höhe (mm): [40]  Breite (mm): [80]
  ☑ S1-Seitenverhältnis 2:1 fixieren  <-- S1 zuerst
  ☑ S2-Seitenverhältnis 1:1 fixieren
```

**Betroffene Dateien:**
- `gui/ui_files/settings_dialog.ui`: Rows 2-3 in Zeichengröße GroupBox

**Commit:**
- `6ae90e3` - fix: move aspect ratio checkboxes to size section, reorder S1 before S2

---

### Bugfix: S2 aspect_locked nicht über "Einstellungen speichern" gespeichert

**Problem:**
- Hauptfenster-Button "Einstellungen speichern" speicherte S1 aspect_locked
- **ABER:** S2 aspect_locked wurde **nicht** gespeichert
- Nur S1-Einstellung wurde persistent

**Fix:**
Fehlende Zeile in `_save_ui_to_settings()` hinzugefügt:

```python
# S2 Seitenverhältnis-Fixierung (NEW v0.8.4)
self.settings.zeichen.aspect_locked = self.check_s2_aspect_locked.isChecked()
```

**Betroffene Dateien:**
- `gui/main_window.py`: Zeile 847

**Commit:**
- `6ae90e3` - fix: move aspect ratio checkboxes to size section, reorder S1 before S2

---

## 📚 Dokumentation

### Benutzerhandbuch erweitert

**Neues Kapitel:** "Seitenverhältnis-Fixierung (NEU in v0.8.4)"

**Inhalt:**
- Erklärung der Seitenverhältnis-Fixierung für S1 (2:1) und S2 (1:1)
- Beschreibung der Checkbox-Funktion
- Screenshots der Einstellungen
- Hinweise zu Standard-Verhalten

**Änderungen:**
- Neues Kapitel in Abschnitt "Einstellungen"
- Version auf v0.8.4 aktualisiert
- Stand: Dezember 2025

**Betroffene Dateien:**
- `User-documentation/BENUTZERHANDBUCH.md`: Zeilen 948-974 (neues Kapitel), Zeilen 5-6 (Version)
- `User-documentation/BENUTZERHANDBUCH.pdf`: Neu generiert für v0.8.4

**Commits:**
- `4749841` - docs: update user manual for v0.8.4 aspect ratio settings
- `ba36cd0` - Benutzerhandbuch.pdf auf v0.8.4 aktualisiert

---

## 🔧 Technische Details

### Signal Handler Reihenfolge

**Wichtige Erkenntnis:**
Die Reihenfolge von Qt Signal-Verbindungen ist **kritisch**!

**Regel:**
1. **Berechnung zuerst** - Handler die Werte berechnen/ändern
2. **Anzeige aktualisieren** - Handler die UI aktualisieren
3. **Speichern danach** - Handler die Werte persistent speichern
4. **Nebenwirkungen zuletzt** - Handler die von den neuen Werten abhängen

**Beispiel für korrekten Ablauf:**
```python
# Höhe geändert (z.B. 40 → 50 mm)
↓
_on_aspect_lock()                # Berechnet: Breite = 50 × 2 = 100 mm
↓
_on_zeichen_size_changed()       # Aktualisiert: Labels, Preview
↓
_on_settings_changed()           # Speichert: Höhe=50, Breite=100
↓
_update_recommended_font_size()  # Berechnet: Font-Größe für 50×100 mm
```

**Anti-Pattern (führt zu Bugs):**
```python
# Höhe geändert (z.B. 40 → 50 mm)
↓
_on_settings_changed()           # Speichert: Höhe=50, Breite=80 (ALT!)
↓
_on_aspect_lock()                # Berechnet: Breite = 50 × 2 = 100 mm
↓
# Breite ist jetzt 100, aber in Settings steht 80!
# Bei nächstem Laden: Fehler!
```

### Startup-Initialisierung

**Problem:**
Qt Designer `.ui` Dateien laden Checkbox-Status, aber rufen keine Signal-Handler auf.

**Lösung:**
Nach dem Laden der UI-Elemente müssen State-abhängige Handler **manuell** aufgerufen werden:

```python
# Checkboxen wurden aus settings.json geladen
self.check_s2_aspect_locked.setChecked(self.settings.zeichen.aspect_locked)

# Handler wird NICHT automatisch aufgerufen!
# → Muss explizit gemacht werden:
self._on_s2_aspect_locked_changed()  # Sperrt/entsperrt Breite-Feld
```

**Regel:**
Für jeden State-Change-Handler der UI-Elemente sperrt/entsperrt/zeigt/versteckt:
- Handler **muss** nach `load_settings()` explizit aufgerufen werden
- Andernfalls ist UI-State inkonsistent mit Checkbox-State

---

## 📊 Geänderte Dateien

```
Version & Feature:
constants.py                              | 1 Zeile (Version: 0.8.3 → 0.8.4)
settings_manager.py                       | 1 Zeile (Default: aspect_locked = True)

GUI - Einstellungsdialog:
gui/ui_files/settings_dialog.ui           | ~40 Zeilen (Checkboxen in Zeichengröße)
gui/dialogs/settings_dialog.py            | 14 Zeilen (Load/Save aspect_locked)

GUI - Hauptfenster:
gui/main_window.py                        | ~25 Zeilen
  - Zeilen 305-308: S2 Signal-Reihenfolge
  - Zeilen 353-356: S1 Signal-Reihenfolge
  - Zeile 456: Startup-Initialisierung
  - Zeile 847: S2 aspect_locked speichern
  - Diverse: "Druckgröße" Rechtschreibung

Dokumentation:
User-documentation/BENUTZERHANDBUCH.md    | ~30 Zeilen (Neues Kapitel + Version)
User-documentation/BENUTZERHANDBUCH.pdf   | ~387 KB größer (v0.8.4 Inhalt)
release_notes/RELEASE_NOTES_v0.8.4.md     | ~650 Zeilen (diese Datei)
```

**Gesamt:** ~160 Zeilen Produktionscode geändert
- Kritische Bugfixes: ~35 Zeilen
- Neue Features: ~55 Zeilen
- UI-Verbesserungen: ~45 Zeilen
- Rechtschreibung: ~25 Zeilen

---

## 🚀 Installation & Upgrade

### Neue Installation
1. Download: `Taktische_Zeichen_Generator_v0.8.4.zip`
2. Entpacken in beliebiges Verzeichnis
3. `Taktische_Zeichen_Generator.exe` starten

### Upgrade von v0.8.3
- **Drop-in Replacement:** Einfach .exe ersetzen
- **Automatische Migration:** `settings.json` wird automatisch erweitert
- **Neue Defaults:** S1 und S2 aspect_locked = True (falls nicht vorhanden)
- **Empfehlung:** Alte Version sichern, dann ersetzen

### Upgrade von v0.8.2 oder älter
- **Dringend empfohlen:** v0.8.3 enthielt kritische Bugfixes
- **Siehe:** RELEASE_NOTES_v0.8.3.md für Details
- **Upgrade-Pfad:** v0.8.2 → v0.8.3 → v0.8.4 (oder direkt v0.8.4)

---

## 📝 Bekannte Limitationen

**Unverändert zu v0.8.3:**
1. Layout-Preview experimentell deaktiviert
2. Max. Logfiles Setting noch nicht funktional
3. Pylance Type-Checking Warnings in main_window.py (harmlos)

**Keine neuen Limitationen in v0.8.4**

---

## 🔮 Ausblick auf v0.8.5

Mögliche zukünftige Verbesserungen:
- **Font-Management:** Bessere Schriftarten-Verwaltung mit Preview
- **Templates:** Vordefinierte Einstellungs-Templates für verschiedene Druckszenarien
- **Batch-Verbesserungen:** Erweiterte Batch-Optionen mit Fortschritts-Anzeige

---

## ✅ Checkliste: Was ist neu?

Wenn Sie von v0.8.3 upgraden:

- [x] **Seitenverhältnis global einstellbar** - Beide Layouts im Dialog konfigurierbar
- [x] **Sofortige Berechnungen** - Aspekt-Ratio wird bei erster Änderung berechnet
- [x] **Korrekte Feld-Sperrung** - Breite-Feld wird beim Start richtig gesperrt
- [x] **Deutsche Rechtschreibung** - "Druckgröße" statt "Druckgroesse"
- [x] **Bessere UI-Organisation** - Checkboxen unter "Zeichengröße" statt "Programmverhalten"
- [x] **Komplettes Speichern** - Alle Settings werden über "Einstellungen speichern" persistent

---

## 🙏 Danksagungen

Danke an alle Nutzer die geholfen haben, die Bugs mit der Aspekt-Ratio-Berechnung zu identifizieren und zu testen!

---

## ⚠️ Wichtiger Hinweis für Nutzer

**Diese Version behebt kritische Bugs:**
- ✅ **Aspekt-Ratio-Berechnung** funktioniert sofort (nicht erst bei zweiter Änderung)
- ✅ **Feld-Sperrung** funktioniert jetzt beim Programmstart
- ✅ **Alle Einstellungen** werden korrekt gespeichert

**Neue Flexibilität:**
- ✅ **Seitenverhältnisse** können jetzt global konfiguriert werden
- ✅ **Standard-Verhalten** ist fixierte Seitenverhältnisse (2:1 für S1, 1:1 für S2)
- ✅ **Dokumentation** im Benutzerhandbuch erweitert

Ein Upgrade von v0.8.3 wird **empfohlen**, wenn Sie mit Seitenverhältnissen arbeiten!

---

## 🎓 Technische Lektionen (für Entwickler)

Diese Version hat wichtige Erkenntnisse gebracht:

**1. Qt Signal Handler Reihenfolge ist kritisch:**
   - Berechnung → Anzeige → Speicherung → Nebenwirkungen
   - Falsche Reihenfolge führt zu subtilen Timing-Bugs

**2. UI-Initialisierung braucht explizite Handler-Aufrufe:**
   - `.ui` Files laden State, aber rufen keine Handler auf
   - State-abhängige Handler müssen manuell nach Load aufgerufen werden

**3. Jeder Speichern-Button braucht alle Felder:**
   - Einfach zu vergessen wenn neue Settings hinzukommen
   - Systematisches Review aller Settings bei neuen Features

**4. Testing mit verschiedenen Startzuständen:**
   - Bugs erscheinen oft nur beim Programmstart
   - Nicht nur Runtime-Changes testen!

---

🤖 **Generated with [Claude Code](https://claude.com/claude-code)**
