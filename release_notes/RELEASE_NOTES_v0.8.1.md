# Release Notes v0.8.1 - Linux-Support & Benutzerfreundlichkeit

**Release-Datum:** 2025-11-19
**Version:** v0.8.1

---

## 🎉 Highlights dieser Version

Version 0.8.1 bringt **experimentellen Linux-Support**, eine **intelligente Text-Validierung** zur Vermeidung von Fehlern, ein **kritischer ImageMagick-Bugfix** für verbesserte Stabilität sowie ein **integriertes Benutzerhandbuch** direkt im Programm.

**Wichtig:** **Windows** bleibt das **primär unterstützte System**. Linux-Support ist **experimentell** und wird derzeit getestet. macOS wird **nicht unterstützt**.

---

## 🆕 Neue Features

### Linux-Kompatibilität (Experimentell)
- **Status:** Linux-Support ist **experimentell** und wird aktiv getestet
- **Plattformübergreifendes Ordner-Öffnen:**
  - **Windows** (primär): `explorer` - vollständig unterstützt
  - **Linux** (experimentell): `xdg-open` - wird getestet
  - Betrifft: Export-Ordner, Vorlagen-Ordner, Ausgabe-Ordner, Logs
- **Linux Build-Skript (`build_linux.sh`):**
  - Automatische Versionserkennung aus `constants.py`
  - Abhängigkeits-Prüfung (ImageMagick, zip)
  - PyInstaller-Build mit Release-ZIP-Erstellung
  - Ausführbar mit `chmod +x build_linux.sh && ./build_linux.sh`
- **Erweiterte BUILD_ANLEITUNG.md:**
  - Separate Anleitungen für Windows (primär) und Linux (experimentell)
  - Plattformspezifische Abhängigkeiten dokumentiert
  - ImageMagick-Installation für Linux erklärt
  - Bekannte Probleme und Lösungen pro Plattform
  - macOS als "nicht unterstützt" gekennzeichnet

### Text-Validierung (Stufe 1)
- **Intelligente Längenprüfung:** Validiert Texteingaben beim Verlassen des Textfelds (focusOut)
- **Layout-bewusst:** Unterscheidet zwischen S1 (1 Zeile) und S2 (2 Zeilen mit Wrapping)
- **Gelbe Warnungen:** Freundliche Hinweise wenn Text zu lang für Zeichengröße
- **Performance-optimiert:** Keine Validierung während der Eingabe → keine Verzögerung
- **Hilfreiche Empfehlungen:** Vorschläge zur Textlängen-Reduzierung oder Schriftgrößen-Anpassung
- **Integriert in Dialogs:**
  - Modus "Ruf" (Rufname-Validierung)
  - Modus "Freitext" (Freitext-Validierung)
  - Modus "OV + Stärke" (OV-Name-Validierung)

### Benutzerhandbuch im Hilfemenü
- **Neuer Menüpunkt:** "Hilfe → Benutzerhandbuch" (Tastenkombination: F1)
- **Intelligente Datei-Erkennung:**
  - Bevorzugt PDF-Version (`User-documentation/BENUTZERHANDBUCH.pdf`)
  - Fallback zu Markdown-Version (`BENUTZERHANDBUCH.md`)
  - Plattformübergreifend: Öffnet mit Standard-PDF-Reader bzw. Browser
- **In Releases enthalten:** Benutzerhandbuch (PDF + MD) wird automatisch in Releases kopiert
- **Immer verfügbar:** Auch offline nutzbar, keine Internet-Verbindung nötig

---

## 🔧 Verbesserungen

### Build-System
- **Automatisches Benutzerhandbuch-Kopieren:** `build_exe.bat` kopiert jetzt:
  - `User-documentation/BENUTZERHANDBUCH.pdf` (falls vorhanden)
  - `BENUTZERHANDBUCH.md` (Fallback)
  - Beide Dateien werden in Release-Ordner integriert
- **Versionierte Releases:** Benutzerhandbuch wird mit jeder Release-Version mitgeliefert

### Logging & Debugging
- **ImageMagick Debug-Logging:** Bei DEBUG-Level werden alle gesetzten Environment-Variablen geloggt:
  - `MAGICK_HOME`
  - `MAGICK_CODER_MODULE_PATH`
  - `MAGICK_FILTER_MODULE_PATH`
  - `MAGICK_CONFIGURE_PATH`
  - `MAGICK_MODULE_PATH`
- **Vereinfachtes Troubleshooting:** Nutzer können Variablen in Logs prüfen

---

## 🐛 Bugfixes

### Kritischer ImageMagick-Fix
- **Problem:** Registry-Lookup-Fehler auf manchen Windows-Systemen
  ```
  ERROR | RegistryKeyLookupFailed 'CoderModulesPath' @ error/module.c/GetMagickModulePath/679
  ```
- **Ursache:** ImageMagick versuchte Windows-Registry zu durchsuchen statt Environment-Variablen zu nutzen
- **Lösung:** Zusätzliche Environment-Variablen setzen:
  - `MAGICK_FILTER_MODULE_PATH` für Filter-Module hinzugefügt
  - `MAGICK_MODULE_PATH` hinzugefügt (kritisch - zwingt ImageMagick ENV-Variablen zu nutzen)
  - Verhindert Registry-Lookup komplett
- **Betroffen:** Portable ImageMagick-Installation
- **Status:** Vollständig behoben

### Dokumentation
- **Neuer Troubleshooting-Abschnitt in `docs/imagemagick_setup.md`:**
  - Detaillierte Beschreibung des Registry-Fehlers
  - Schritt-für-Schritt Diagnose-Anleitung
  - Lösungen für Konflikte mit System-Installation
  - Prüfung der Environment-Variablen

---

## 📝 Technische Details

### Gesetzte Environment-Variablen (ImageMagick)
Die Anwendung setzt nun folgende Variablen beim Start (in `constants.py`):
1. `MAGICK_HOME` - ImageMagick-Basisverzeichnis
2. `MAGICK_CODER_MODULE_PATH` - Pfad zu Coder-Modulen (SVG, PNG, etc.)
3. `MAGICK_FILTER_MODULE_PATH` - Pfad zu Filter-Modulen (**NEU**)
4. `MAGICK_CONFIGURE_PATH` - Pfad zu Konfigurationsdateien
5. `MAGICK_MODULE_PATH` - Basis-Modulpfad (**NEU - kritisch!**)
6. `PATH` - ImageMagick-DLLs zum Systempfad hinzugefügt

### Text-Validierungs-Logik
- **Methode:** `validate_text_fits()` in `text_overlay.py`
- **Rückgabewerte:** `(fits: bool, warning: str, estimated_lines: int)`
- **Validierungs-Strategie:**
  1. Prüft ob Text auf eine Zeile passt → OK
  2. Prüft ob Text auf max_lines passt (mit intelligentem Wrapping) → OK
  3. Sonst → Warnung mit Empfehlung
- **RuntimeConfig-Integration:** Nutzt aktuelle Schriftgröße, DPI und Zeichenabmessungen

### Plattform-Erkennung
- **Python-Modul:** `platform.system()` für OS-Erkennung
- **Unterstützte Systeme:**
  - `'Windows'` - **Primär unterstützt** (alle Windows-Versionen)
  - `'Linux'` - **Experimentell** (alle Distributionen, wird getestet)
  - `'Darwin'` - **Nicht unterstützt** (macOS)
- **Verhalten bei nicht unterstützten Systemen:**
  - Nutzer wird informiert mit Dialogfenster
  - Pfade werden angezeigt zum manuellen Öffnen
  - Operation wird abgebrochen (kein Fehler)

---

## 📦 Änderungen am Release-Paket

### Neue Dateien in Releases
- ✅ `User-documentation/BENUTZERHANDBUCH.pdf` (falls vorhanden)
- ✅ `BENUTZERHANDBUCH.md` (Fallback)
- ✅ `build_linux.sh` (für Linux-Nutzer, experimentell)
- ✅ `BUILD_ANLEITUNG.md` (erweitert mit Linux-Anleitungen, macOS als nicht unterstützt)

### Build-Prozess
**Windows (Primäres System):**
```batch
build_exe.bat
```
→ Erstellt `releases/TaktischeZeichenDruckgenerator_v0.8.1.zip`

**Linux (Experimentell):**
```bash
chmod +x build_linux.sh
./build_linux.sh
```
→ Erstellt `releases/TaktischeZeichenDruckgenerator_v0.8.1_Linux.zip`

**macOS:** Nicht unterstützt - kein Build-Skript verfügbar

---

## ⚠️ Breaking Changes

**Keine Breaking Changes in dieser Version!**

Alle Änderungen sind abwärtskompatibel. Bestehende `settings.json`-Dateien funktionieren weiterhin ohne Anpassungen.

---

## 🔮 Bekannte Einschränkungen

### Linux/macOS
- **ImageMagick:** Muss systemweit installiert sein (über apt/brew)
  - Windows: Portable Version im Programmordner (keine Installation nötig)
  - Linux: `sudo apt install imagemagick` erforderlich
  - macOS: `brew install imagemagick` erforderlich
- **Schriftarten:** System-Schriftarten unterscheiden sich
  - Windows: Arial standardmäßig verfügbar
  - Linux/macOS: Helvetica oder Liberation Sans empfohlen
  - SVG-Schriftarten müssen ggf. manuell installiert werden

### Text-Validierung
- **Stufe 1:** Nur Validierung beim Verlassen des Textfeldes
- **Keine Live-Vorschau:** Zeichen-Preview zeigt noch keine Text-Überlagerung
- **Geplant für v0.9.0:**
  - Stufe 2: Debounced Live-Validierung (500ms Verzögerung)
  - Stufe 3: Echtzeit-Preview mit Text-Rendering

---

## 🙏 Danksagungen

Vielen Dank an alle Beta-Tester für das Feedback, insbesondere:
- Meldung des ImageMagick Registry-Fehlers
- Wunsch nach Linux-Unterstützung
- Vorschlag für Text-Längen-Validierung
- Anfrage nach integriertem Benutzerhandbuch

---

## 📚 Weitere Ressourcen

- **Benutzerhandbuch:** Hilfe → Benutzerhandbuch (F1)
- **Build-Anleitung:** `BUILD_ANLEITUNG.md`
- **Entwickler-Docs:** `ai-docs/` Verzeichnis
- **ImageMagick Setup:** `docs/imagemagick_setup.md`
- **Test-Routinen:** `docs/Test-Routinen_Anleitung.md`

---

## 📊 Statistiken

**Code-Änderungen:**
- 7 Dateien geändert
- ~800 Zeilen hinzugefügt
- 3 neue Features
- 1 kritischer Bugfix
- Plattformübergreifende Kompatibilität für 3 Betriebssysteme

**Commits:**
- `0549c37` - S1-Layout Performance-Optimierungen + Benutzerhandbuch überarbeitet
- `01165cf` - Text-Umbruch S2 + Fehlende-Schriftarten-Tracker
- `eb1f8f0` - Du-Form in Schriftarten-Warnung
- `e5a64ce` - Linux-Kompatibilität + Text-Validierung (Stufe 1)
- `f757a4a` - ImageMagick Registry-Fehler beheben

---

**Viel Erfolg mit der neuen Version!** 🎉

Bei Fragen oder Problemen: Ramon-Hoffmann@gmx.de
