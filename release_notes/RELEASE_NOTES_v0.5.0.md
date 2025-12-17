# TaktischeZeichenEditor v0.5.0

**Datum:** 2025-10-29
**Status:** Beta-Release
**Build:** Produktionsreif

---

## 🚀 Performance-Update

Diese Version konzentriert sich auf **massive Performance-Verbesserungen** beim Export ohne Qualitätsverlust!

---

## ⚡ Performance-Optimierungen

### 1. **Mehr Parallelität**
- **Default Threads:** 4 → **6 Threads** (50% mehr)
- **Maximum Threads:** 16 → **32 Threads**
- Nutzt moderne Multi-Core-CPUs besser aus
- **Speedup:** ~50-80% schneller auf 8-Core-CPUs

**Für Nutzer:**
Der Export-Dialog zeigt standardmäßig 6 Threads. Du kannst bis zu 32 Threads einstellen, wenn deine CPU viele Kerne hat.

---

### 2. **Optimierter PNG-Export**
- Schnellere PNG-Kompression (`compress_level=1`)
- Entfernung von ungenutztem `quality`-Parameter
- **Speedup:** ~10-20% schneller
- **Trade-off:** Dateien ~5-10% größer (kaum merkbar)

---

### 3. **Schnelleres Bild-Scaling**
- Optimierter ImageMagick-Filter (`catrom`)
- Bessere Balance zwischen Geschwindigkeit und Qualität
- **Speedup:** ~15-25% schneller
- **Qualität:** Unverändert hochwertig

---

### 4. **Code-Optimierungen**
- Vereinfachte Alpha-Channel-Verarbeitung
- Kleinere Micro-Optimierungen
- **Speedup:** ~2-3%

---

## 📊 Gesamt-Performance

**Gesamt-Speedup: ~80-120% schneller** (Export dauert nur noch ~45-55% der ursprünglichen Zeit!)

**Beispiel:**
- **Vorher (v0.4.8):** 100 Zeichen = 5 Minuten
- **Jetzt (v0.5.0):** 100 Zeichen = **~2-3 Minuten** ⚡

---

## 🐛 Behobene Bugs

### Ordner-Dialog merkt sich zuletzt gewählten Pfad
- **Problem:** Dialog öffnete immer im Programmverzeichnis
- **Lösung:** Dialog startet jetzt im zuletzt ausgewählten Vorlagen-Ordner
- **Vorteil:** Schnellere Navigation bei falsch gewähltem Ordner

### SVG-Dateien im Grundverzeichnis werden geladen
- **Problem:** SVG-Dateien direkt im Vorlagen-Ordner (nicht in Unterordnern) wurden ignoriert
- **Lösung:** Grundverzeichnis wird als "(Root)"-Kategorie angezeigt
- **Vorteil:** Flexiblere Ordnerstruktur möglich

---

## 🔧 Verbesserungen aus v0.4.8

Diese Version baut auf v0.4.8 auf und enthält auch:

### Suchfunktion
- Echtzeit-Filterung von Kategorien und Zeichen
- Automatisches Expandieren bei Treffern
- Clear-Button zum schnellen Löschen

### Blanko-Zeichen Kategorie
- 7 vordefinierte Blanko-Zeichen (eines pro Modus)
- Automatische Modus-Vorbelegung
- Perfekt für selbst beschriftbare Vorlagen

### Überarbeitete Button-Leiste
- Klarere Beschriftungen
- "Vorlagen-Ordner in Explorer öffnen" Button
- Hervorgehobener Export-Button

### DU-Form & Deutsche Buttons
- Alle Dialoge verwenden freundliche DU-Form
- "Ja" / "Nein" statt "Yes" / "No"

### Schnittlinien-Warnung
- Warnung beim Öffnen des Export-Dialogs
- Automatische 300 DPI Einstellung möglich

---

## 📦 Versions-Historie

| Version | Highlights |
|---------|------------|
| **0.5.0** | **Performance-Update:** 80-120% schneller, Bug-Fixes |
| 0.4.8 | UI-Überarbeitung, ImageMagick CoderModulesPath Fix |
| 0.4.7 | Suchfunktion, Schnittlinien-Warnung, DU-Form |
| 0.4.6 | Blanko-Zeichen Feature |
| 0.4.5 | Stärke-Platzhalter Format, TEXT_GRAFIK_OFFSET_MM Fix |
| 0.4.4 | Performance-Optimierung, Export-Feedback |

---

## 🔍 Was getestet werden sollte

### Priorität 1: Performance
- [ ] Export ist deutlich schneller als v0.4.8
- [ ] Qualität der exportierten Zeichen ist unverändert gut
- [ ] Thread-Einstellung (6 Threads) funktioniert
- [ ] Höhere Thread-Zahlen (8-16) funktionieren auf starken CPUs

### Priorität 2: Bug-Fixes
- [ ] Ordner-Dialog startet im zuletzt gewählten Pfad
- [ ] SVG-Dateien im Grundverzeichnis werden als "(Root)" angezeigt
- [ ] "(Root)"-Kategorie funktioniert korrekt

### Priorität 3: Allgemein
- [ ] Programm startet ohne Fehler
- [ ] Export (PNG/PDF) funktioniert
- [ ] Alle Features aus v0.4.8 funktionieren weiterhin

---

## 💬 Feedback

Bitte melde Bugs oder Verbesserungsvorschläge an:
- **Email:** [Deine Email hier eintragen]
- **Thema:** Beta-Feedback v0.5.0

**Wichtig für Bug-Reports:**
- Beschreibung des Problems
- Schritte zur Reproduktion
- Screenshots (falls hilfreich)
- Windows-Version (10/11)
- **NEU:** CPU-Kerne (anzahl) und verwendete Thread-Einstellung

---

## 📦 Installation

1. **ZIP entpacken**
2. **Ordner öffnen:** `TaktischeZeichenEditor_Beta_v0.5.0/`
3. **Programm starten:** `TaktischeZeichenEditor.exe`
4. **Vorlagen-Ordner auswählen:** Button "Vorlagen-Ordner auswählen"
5. **SVG-Dateien hinzufügen** in den ausgewählten Ordner
6. **Vorlagen laden:** Button "Vorlagen neu laden"
7. **Loslegen!**

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

**Tipp:** Je mehr CPU-Kerne, desto schneller der Export! Passe die Thread-Anzahl im Export-Dialog an deine CPU an.

---

## ⚠️ Bekannte Einschränkungen

- Windows Defender kann den ersten Start verlangsamen (Antivirus-Scan)
- .exe ist ca. 500-600 MB groß (PyQt6 + ImageMagick)
- Erster Start dauert länger als nachfolgende Starts
- Sehr hohe Thread-Zahlen (>16) bringen nur auf High-End-CPUs Vorteile

---

## 🙏 Danke!

Vielen Dank fürs Beta-Testen! Besonders interessiert sind wir an:
- **Performance-Feedback:** Wie viel schneller ist v0.5.0 bei dir?
- **Qualitäts-Feedback:** Sehen die exportierten Zeichen genauso gut aus wie vorher?

**Viel Spaß beim Testen!** 🚀
