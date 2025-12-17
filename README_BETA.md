# Taktische Zeichen Druckgenerator - Beta v0.6.1

**BETA-VERSION** - Nur für Test-Zwecke!

**✨ NEU in v0.6.1:** PNG mit Transparenz (RGBA) für perfektes Anti-Aliasing auf allen Untergründen!

---

## 🎯 Zweck und Zielgruppe

Dieses Programm wurde **speziell für die ehrenamtliche und hauptamtliche Arbeit im Zivil- und Katastrophenschutz** entwickelt. Es soll Feuerwehren, Rettungsdiensten, dem THW und anderen Hilfsorganisationen eine **kostenlose Open-Source-Lösung** bieten, um die Erstellung taktischer Zeichen zu erleichtern.

**Lizenz:** GPL v3 - Kostenlos für alle Zwecke (auch kommerzielle Nutzung)

**Freundliche Bitte an kommerzielle Nutzer:**
Falls Sie dieses Tool kommerziell einsetzen, würden wir uns über eine kurze Mitteilung freuen (keine rechtliche Verpflichtung). Kontakt: Ramon-Hoffmann@gmx.de

Weitere Details: Siehe `LICENSE` und `User-documentation/BENUTZERHANDBUCH.md`

---

## 📦 Installation

1. **Ordner entpacken** in ein beliebiges Verzeichnis
2. **TaktischeZeichenDruckgenerator.exe** starten
3. Fertig!

---

## 🚀 Erste Schritte

### 1. SVG-Vorlagen bereitstellen

Lege deine **SVG-Dateien** in Unterordnern im Ordner `Taktische_Zeichen_Grafikvorlagen/` ab:

```
Taktische_Zeichen_Grafikvorlagen/
├── Einheiten/
│   ├── Trupp.svg
│   ├── Gruppe.svg
│   └── ...
├── Fahrzeuge/
│   ├── MTW.svg
│   └── ...
└── ...
```

**Ordnerstruktur:**
- Jeder Unterordner = eine Kategorie
- **NEU:** SVG-Dateien direkt im Hauptordner werden als "(Root)"-Kategorie angezeigt


### 1.1 Schriftart installieren
Für die taktischen Zeichen aus Jonas Köritz Sammlung wird die Schriftart RobotoSlab benötigt. Die habe ich euch in den Programmordner gepackt. Einfach Zip-Datei öffnen, auf die Datei im Grundverzeichnis klicken und im aufploppenden Windows-Dialog auf "Installieren" klicken.
Wenn diese Schriftart nicht installiert ist, fällt das Programm auf Arial zurück, allerdings werden dann Texte wie "MTW FGr" größer als das Fahrzeugsymbol sein.

### 2. Ordner laden

- Klicke **"Vorlagen-Ordner auswählen"**
- Wähle den Ordner `Taktische_Zeichen_Grafikvorlagen` aus
- Die Kategorien werden geladen
- **Tipp:** Der Dialog merkt sich den zuletzt gewählten Ordner

### 3. Zeichen suchen & konfigurieren

**Suchfunktion:**
- Suchfeld über der Kategorie-Liste
- Echtzeit-Filterung während der Eingabe
- Findet Zeichen in allen Kategorien

**Blanko-Zeichen:**
- Kategorie "Blanko-Zeichen" mit 7 vorgefertigten Blanko-Vorlagen
- Perfekt für selbst beschriftbare Zeichen

**Einstellungen pro Zeile:**
- **Kopien:** Anzahl der Wiederholungen
- **Modus:**
  - "OV + Stärke" - Organisationseinheit + Stärkemeldung
  - "Ort + Stärke" - Ortsname + Stärkemeldung
  - "Schreiblinie + Stärke" - Schreiblinie für handschriftliche Beschriftung + Stärkemeldung
  - "Schreiblinie oder Freitext" - Freitext oder Schreiblinie
  - "Ruf" - Rufname
  - "Dateiname" - Text aus Dateiname (automatisch)
  - "Nur Grafik" - Ohne Text
- **Text:** Individueller Text (je nach Modus)
- **Grafikgröße:** Nur bei "Nur Grafik" verfügbar

### 4. Export

1. Klicke **"Taktische Zeichen erstellen"**
2. Wähle im Export-Dialog:
   - **Format:** PNG, PDF - Einzelzeichen, oder PDF - Schnittbogen (A4)
   - **DPI:** 300, 600 oder 1200 (Standard: 600)
   - **Threads:** 1-32 (Standard: **6** - mehr = schneller!)
   - **Schnittlinien:** Optional zum Testen (nur in Hauptfenster aktivierbar)
3. Klicke **"Exportieren"**
4. Die Dateien werden im gewählten Ausgabe-Ordner gespeichert

**⚡ Performance-Tipp:**
- **6 Threads:** Guter Standard (funktioniert auf allen CPUs)
- **8 Threads:** Optimal für 8-Kern-CPUs
- **12-16 Threads:** Nur für High-End-CPUs sinnvoll
- Je mehr CPU-Kerne, desto schneller der Export!

---

## 📐 Technische Details

### Druckgröße
- **Endgröße:** 45 × 45 mm
- **Beschnitt:** 3 mm (rundum)
- **Datei-Größe:** 51 × 51 mm
- **Sicherheitsrand:** 3 mm (innen)

### Export-Format
- **PNG:** Ein Ordner mit allen Bildern
  - Format: `YYYY-MM-DD_hh-mm_PNG_<Anzahl>_<DPI>_dpi/`
  - Beispiel: `2025-10-27_14-30_PNG_15_600_dpi/`

---

## ⚙️ Systemanforderungen

### Empfohlen für beste Performance:
- **CPU:** 6-8 Kerne oder mehr
- **RAM:** 4 GB
- **Windows:** 10 oder 11

### Minimum:
- **CPU:** 2 Kerne (funktioniert, aber langsamer)
- **RAM:** 2 GB
- **Windows:** 10 oder 11

---

## 🐛 Bekannte Einschränkungen

- Windows Defender kann den ersten Start verlangsamen (Antivirus-Scan)
- .exe ist ca. 500-600 MB groß (PyQt6 + ImageMagick)
- Erster Start dauert länger als nachfolgende Starts
- Sehr hohe Thread-Zahlen (>16) bringen nur auf High-End-CPUs Vorteile
- **NEU:** PNG-Dateien mit RGBA sind ~20-30% größer als RGB (typisch 100-200 KB statt 80-150 KB)
- Textlängen-Validierung temporär deaktiviert (wird in v0.7.0 überarbeitet)

---

## 💬 Feedback

Bitte melde Bugs und Verbesserungsvorschläge an:
- **Email:** [Ramon-Hoffman@gmx.de]
- **Thema:** Beta-Feedback v0.6.1

### Was ich wissen möchte:
1. **Transparenz:** Funktioniert die PNG-Transparenz wie erwartet?
2. **Qualität:** Ist das Anti-Aliasing besser als in v0.6.0?
3. **Pseudo-SVGs:** Gibt es noch schwarze Flächen bei eingebetteten PNGs?
4. **Fehler:** Welche Bugs sind aufgetreten?
5. **Features:** Was fehlt noch? Was ist unklar?

**Bei Bug-Reports bitte angeben:**
- Beschreibung des Problems
- Schritte zur Reproduktion
- Screenshots (falls hilfreich)
- Windows-Version (10/11)
- CPU-Kerne und Thread-Einstellung

---

## 📝 Changelog ==> Bitte Release notes beachten. :-)

---

## 📄 Lizenz

[Füge hier deine Lizenz ein]

---

**Danke fürs Testen!** 🙏
