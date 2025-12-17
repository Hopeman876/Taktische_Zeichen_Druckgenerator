# TaktischeZeichenEditor v0.4.8-beta

**Datum:** 2025-10-29
**Status:** Beta-Release
**Build:** Produktionsreif

---

## 🎉 Wichtigste Neuerungen

### 1. **Suchfunktion für Kategorien und Zeichen**
- Suchfeld direkt über der Kategorie-Liste
- Echtzeit-Filterung während der Eingabe
- Findet Zeichen in allen Kategorien und Unterkategorien
- Automatisches Expandieren von Kategorien mit Treffern
- Clear-Button zum schnellen Löschen

**Beispiel:**
Tippe "Feuerwehr" in das Suchfeld → Alle Zeichen mit "Feuerwehr" im Namen werden angezeigt

---

### 2. **Blanko-Zeichen Kategorie**
- Neue virtuelle Kategorie "Blanko-Zeichen" (erscheint immer als erste)
- 7 vordefinierte Blanko-Zeichen (eines pro Modus):
  - Blanko - OV + Stärke
  - Blanko - Ort + Stärke
  - Blanko - Schreiblinie + Stärke
  - Blanko - Ruf
  - Blanko - Schreiblinie oder Freitext
  - Blanko - Dateiname
  - Blanko - Nur Grafik (komplett leer)
- Automatische Modus-Vorbelegung basierend auf Zeichen-Name
- Perfekt für selbst beschriftbare Vorlagen

**Verwendung:**
Wähle "Blanko-Zeichen" → Modus ist bereits vorausgewählt → Exportieren

---

### 3. **Schnitt-/Hilfslinien Export-Warnung**
- Warnung erscheint automatisch beim Öffnen des Export-Dialogs
- Nur wenn Schnittlinien aktiviert sind
- Bietet automatische 300 DPI Einstellung für schnelleren Export
- Deutsche Ja/Nein Buttons

**Hinweis:**
Schnittlinien dienen nur zur Kontrolle der Maße und dürfen NICHT in den finalen Druckdateien sein!

---

### 4. **Überarbeitete Button-Leiste**
- **Klarere Beschriftungen:**
  - "Vorlagen-Ordner auswählen" (vorher: "Vorlagen-Ordner öffnen")
  - "Vorlagen neu laden" (vorher: "Neu laden")
  - "Taktische Zeichen erstellen" (vorher: "Export")
- **Neuer Button:** "Vorlagen-Ordner in Explorer öffnen"
  - Öffnet den Vorlagen-Ordner direkt im Windows Explorer
  - Praktisch zum schnellen Hinzufügen von SVG-Dateien
- **Optische Verbesserungen:**
  - Separator zwischen Button-Gruppen
  - "Taktische Zeichen erstellen" Button hervorgehoben (fett)
  - Bessere Abstände zu den Rändern

---

## 🔧 Verbesserungen

### DU-Form in allen Dialogen
Alle Meldungen verwenden jetzt die DU-Form statt SIE-Form:
- "Bitte wähle..." statt "Bitte wählen Sie..."
- "Möchtest du..." statt "Möchten Sie..."
- Konsistente und freundlichere Ansprache

### Deutsche Button-Labels
Alle Dialoge verwenden jetzt deutsche Buttons:
- "Ja" / "Nein" statt "Yes" / "No"
- Einheitliches Erscheinungsbild

---

## 🐛 Behobene Bugs

### ImageMagick CoderModulesPath Error (KRITISCH)
- **Problem:** SVG-Konvertierung schlug fehl mit Fehler: `RegistryKeyLookupFailed 'CoderModulesPath'`
- **Ursache:** ImageMagick konnte Coder-Module (SVG, PNG, etc.) im .exe-Build nicht finden
- **Lösung:** Umgebungsvariablen `MAGICK_CODER_MODULE_PATH` und `MAGICK_CONFIGURE_PATH` werden jetzt explizit gesetzt
- **Status:** ✅ Behoben - Export funktioniert jetzt zuverlässig im .exe-Build

### Stärke-Platzhalter Format optimiert
- **Alt:** `___ / ____ / ____ = ____` (schwer manuell beschriftbar)
- **Neu:** `     /      /      / ___` (Leerzeichen für Führer/Unterführer/Helfer, Unterstriche nur für Gesamt)
- Bessere Lesbarkeit und einfachere manuelle Beschriftung

### TEXT_GRAFIK_OFFSET_MM korrekt angewendet
- Offset zwischen Grafik und Text wurde teilweise doppelt angewendet
- Jetzt korrekt: Grafik-Höhe wird um Offset reduziert (nicht Text verschoben)
- 5mm Abstand zwischen Grafik und Text wie vorgesehen

### Grafik-Einstellungen bleiben nach Filterung sichtbar
- Bug behoben: Nach Verwendung der Suchfunktion verschwanden Grafik-Spalten bei "Nur Grafik" Modus
- Widgets bleiben jetzt korrekt sichtbar durch Verwendung von `setRowHidden()`

---

## 📊 Versions-Historie

| Version | Features |
|---------|----------|
| **0.4.8** | UI-Überarbeitung, Vorschaubilder-Feature entfernt |
| 0.4.7 | Suchfunktion, Schnittlinien-Warnung, DU-Form |
| 0.4.6 | Blanko-Zeichen Feature |
| 0.4.5 | Stärke-Platzhalter Format, TEXT_GRAFIK_OFFSET_MM Fix |
| 0.4.4 | Performance-Optimierung, Export-Feedback |

---

## 🔍 Was getestet werden sollte

### Priorität 1: Kritisch
- [ ] Programm startet ohne Fehler
- [ ] Vorlagen-Ordner kann ausgewählt werden
- [ ] Zeichen können exportiert werden (PNG/PDF)
- [ ] Blanko-Zeichen funktionieren
- [ ] Schnittlinien-Warnung erscheint korrekt

### Priorität 2: Wichtig
- [ ] Suchfunktion findet Zeichen korrekt
- [ ] "Vorlagen-Ordner in Explorer öffnen" funktioniert
- [ ] Grafik-Einstellungen bleiben nach Suche sichtbar
- [ ] DPI-Einstellung bei Schnittlinien funktioniert
- [ ] Deutsche Buttons werden korrekt angezeigt

### Priorität 3: Nice-to-have
- [ ] UI-Layout sieht gut aus
- [ ] Button-Hervorhebung ist sichtbar
- [ ] Separator zwischen Buttons ist sichtbar
- [ ] Stärke-Platzhalter ist gut lesbar

---

## 💬 Feedback

Bitte melde Bugs oder Verbesserungsvorschläge an:
- **Email:** [Deine Email hier eintragen]
- **Thema:** Beta-Feedback v0.4.8

**Wichtig für Bug-Reports:**
- Beschreibung des Problems
- Schritte zur Reproduktion
- Screenshots (falls hilfreich)
- Windows-Version (10/11)

---

## 📦 Installation

1. **ZIP entpacken**
2. **Ordner öffnen:** `TaktischeZeichenEditor_Beta_v0.4.8/`
3. **Programm starten:** `TaktischeZeichenEditor.exe`
4. **Vorlagen-Ordner auswählen:** Button "Vorlagen-Ordner auswählen"
5. **SVG-Dateien hinzufügen** in den ausgewählten Ordner
6. **Vorlagen laden:** Button "Vorlagen neu laden"
7. **Loslegen!**

---

## ⚠️ Bekannte Einschränkungen

- Windows Defender kann den ersten Start verlangsamen (Antivirus-Scan)
- .exe ist ca. 500-600 MB groß (PyQt6 + ImageMagick)
- Erster Start dauert länger als nachfolgende Starts

---

## 🙏 Danke!

Vielen Dank fürs Beta-Testen! Dein Feedback hilft, das Programm besser zu machen.

**Viel Spaß beim Testen!** 🚀
