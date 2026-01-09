[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/Version-0.8.5-green.svg)](releases/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2011-lightgrey.svg)](https://www.microsoft.com/windows)

# Taktische Zeichen Druckgenerator

Generator für druckfertige taktische Zeichen mit individuellen Texten - ohne Grafikbearbeitungskenntnisse.

<img src="resources/Logo.png" alt="Logo Taktische Zeichen Druckgenerator" width="300">

## Das Problem, das wir lösen

**Schluss mit mühsamem Zusammenbasteln in Word-Vorlagen!**

Dieses Tool wurde entwickelt, um Einsatzkräften von **THW**, **Feuerwehr**, **Rettungsdiensten** und **Katastrophenschutz** das Leben zu erleichtern:

- ✅ **Keine Grafikbearbeitungskenntnisse erforderlich** - Intuitive Bedienung
- ✅ **Keine Word-Vorlagen mehr** - Schluss mit Pixelschubsen
- ✅ **Automatische Anpassung** an Druckdienstleister-Vorgaben (Größen, Beschnittränder, Abstände)
- ✅ **Druckfertige PDFs** - CMYK, PDF/X-1a:2001, 300-1200 DPI wählbar
- ✅ **Stapelverarbeitung** - Dutzende Zeichen in Minuten statt Stunden
- ✅ **Schnelle Nachproduktion im Einsatzfall** - Vorbereitete PDF-Schnittbögen einfach ausdrucken und zuschneiden

## Features

### Kernfunktionen
- 🖱️ **Einfache Bedienung** - SVG-Grafiken laden, Text eingeben, exportieren
- 📝 **7 Text-Modi** - OV+Stärke, Ort, Rufname, Freitext, Schreiblinien, Dateiname, Nur Grafik
- 📐 **Zwei Layouts** - S2 Standard (quadratisch) und S1 Doppelschild (mit Schreiblinien)
- 📄 **Schnittbögen** - Mehrere Zeichen optimal auf A4 angeordnet
- 🎨 **Blanko-Zeichen** - Für handschriftliche Beschriftung
- 🔍 **Suchfunktion** - Schnelles Finden von Zeichen

### Export-Optionen
- 💾 **PNG** - Einzeldateien mit transparentem Hintergrund (RGBA)
- 📄 **PDF Einzelzeichen** - Jedes Zeichen auf separater Seite
- 📋 **PDF Schnittbogen** - Mehrere Zeichen auf A4 mit Schnittlinien
  - **Ideal für den Einsatzfall:** Vorbereitete PDFs können auf Einsatz-PCs abgelegt werden
  - Bei Bedarf einfach ausdrucken und zuschneiden - kein Druckgenerator mehr erforderlich
  - Ermöglicht schnelle Nachproduktion taktischer Zeichen direkt vor Ort

### Technisch
- 🚀 **Multithreading** - Schnellerer Export durch Parallelverarbeitung (1-32 Threads)
- 📏 **Flexibel konfigurierbar** - Zeichengröße, Abstände, Schriftarten frei anpassbar
- ⚙️ **Persistente Einstellungen** - Alle Konfigurationen werden gespeichert
- 📦 **Portable** - Keine Installation nötig, einfach entpacken und starten

## Installation

1. **Release herunterladen** - [Releases](releases/)
2. **ZIP-Datei entpacken** in ein beliebiges Verzeichnis
3. **TaktischeZeichenDruckgenerator.exe starten**
4. Fertig!

**Schriftarten:** Das Tool erkennt automatisch fehlende Schriftarten in den SVG-Vorlagen und listet diese beim Export auf, damit sie bei Bedarf nachinstalliert werden können.

## Erste Schritte

### 1. SVG-Vorlagen bereitstellen

Erstelle einen Ordner und organisiere deine SVG-Dateien in Unterordnern:

```
Taktische_Zeichen_Grafikvorlagen/
├── Einheiten/
│   ├── Trupp.svg
│   ├── Gruppe.svg
│   └── Zug.svg
├── Fahrzeuge/
│   ├── MTW.svg
│   └── LF20.svg
└── ...
```

**Wichtig:** Jeder Unterordner wird zur Kategorie in der Programmoberfläche.

### 2. Vorlagen laden

1. Klick auf **"Vorlagen-Ordner auswählen"**
2. Wähle den Ordner `Taktische_Zeichen_Grafikvorlagen`
3. Kategorien und Zeichen werden geladen

### 3. Zeichen konfigurieren

1. **Checkbox aktivieren** vor den gewünschten Zeichen
2. **Text-Modus wählen** (z.B. "OV + Stärke", "Schreiblinie / Freitext")
3. **Text eingeben** in der Tabelle
4. **Kopien einstellen**, falls mehrere identische Zeichen benötigt werden

### 4. Exportieren

1. Klick auf **"Taktische Zeichen erstellen"**
2. **Format wählen** (PNG, PDF Einzelzeichen, PDF Schnittbogen)
3. **DPI einstellen** (300, 600 oder 1200)
4. **Exportieren** - Fertig!

Dateien liegen im Ausgabe-Ordner `Taktische_Zeichen_Ausgabe/`.

## Systemanforderungen

**Empfohlen:**
- Windows 11 (64-bit)
- 4-8 GB RAM
- Mehrkern-CPU (6+ Kerne für schnellen Export)

**Minimum:**
- Windows 11 (64-bit)
- 2 GB RAM
- Dual-Core CPU

## Dokumentation

Detaillierte Anleitungen findest du in der [Projektdokumentation](User-documentation/):
- **[Benutzerhandbuch](User-documentation/BENUTZERHANDBUCH.md)** - Vollständige Anleitung für Anwender
- **[Release Notes](release_notes/)** - Versionshinweise und Änderungen
- **[CLAUDE.md](CLAUDE.md)** - Technische Dokumentation für Entwickler
- **[Build-Anleitung](BUILD_ANLEITUNG.md)** - Anleitung zum Selbstbauen

## Lizenz

Dieses Programm steht unter der **GNU General Public License v3.0 (GPL v3)**.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Das bedeutet:**
- ✅ Kostenlos für **alle Zwecke** (auch kommerziell)
- ✅ Quellcode frei verfügbar
- ✅ Weitergabe und Modifikation erlaubt
- ✅ Keine versteckten Kosten, keine Abos

**Freundliche Bitte an kommerzielle Nutzer:**
Falls du dieses Tool kommerziell nutzt und damit Einnahmen erzielst, würden wir uns über eine kurze Mitteilung freuen (keine rechtliche Verpflichtung). Kontakt: ramon-hoffmann[at]gmx[dot]de

## Aktueller Stand

**Version v0.8.5** (Dezember 2025)

Diese Version bietet eine stabile Funktionsbasis mit vollständigem Feature-Set. Kleinere Fehler und optische Details werden noch korrigiert.

**Feedback ist herzlich willkommen!**

## Feedback und Support

**Fehler melden oder Features vorschlagen:**
- [GitHub Issues](https://github.com/Hopeman876/Taktische_Zeichen_Druckgenerator_Develop/issues)

**Bei Bug-Reports bitte angeben:**
- Beschreibung des Problems
- Schritte zur Reproduktion
- Screenshots (falls hilfreich)
- Log-Datei aus `Logs/` Ordner (bei Debug-Level)

## Verwandte Projekte

Dieses Tool arbeitet hervorragend mit SVG-Sammlungen wie der [Taktische Zeichen Sammlung von Jonas Köritz](https://github.com/jonas-koeritz/Taktische-Zeichen) zusammen.

Fehlt dein Projekt auf der Liste? Kontaktiere uns oder sende einen Pull-Request!

---

**Entwickelt mit ❤️ für die Einsatzkräfte im Zivil- und Katastrophenschutz**
