# Release Notes v0.8.5 - PDF-Schnittbogen Bugfix Release

**Release-Datum:** 2025-12-16
**Version:** v0.8.5

---

## 🎉 Highlights dieser Version

Version 0.8.5 behebt **kritische Fehler im PDF-Schnittbogen-Export** und verbessert die **Darstellung der Schnitthilfslinien**. Das Schnittbogen-Layout ist nun **konsistent** unabhängig davon, ob Schnittlinien aktiviert sind oder nicht.

**Wichtigste Änderungen:**
- **KRITISCH: Schnittbogen-Layout korrigiert** - Layout bleibt identisch mit/ohne Schnittlinien
- **Schnitthilfslinien-Beschriftung verbessert** - Labels näher an ihren zugehörigen Linien
- **User-Anforderung erfüllt** - Rote Beschnittzugabe wird korrekt abgeschnitten

---

## 🐛 Bugfixes

### KRITISCH: Schnittbogen-Layout änderte sich mit Schnittlinien

**Problem:**
Das PDF-Schnittbogen-Layout änderte sich komplett, wenn Schnittlinien aktiviert wurden:
- **OHNE Schnittlinien:** 4×6 = 24 Zeichen auf A4 (Hochformat)
- **MIT Schnittlinien:** 3×5 = 15 Zeichen auf A4 (Hochformat)
- Zeichen erschienen größer mit Schnittlinien (51mm statt 45mm)
- Weniger Zeichen passten auf eine Seite

**User-Erwartung:**
- Layout muss **IDENTISCH** sein mit/ohne Schnittlinien
- Zeichen müssen **IMMER** die finale Größe haben (z.B. 45×45mm)
- Rote Linie (Beschnittzugabe) liegt außerhalb und wird abgeschnitten - **das ist korrekt!**

**Ursache:**
Eingeführt in Commit `4168c83` (2025-12-15):
```python
# FALSCH: Grid-Größe änderte sich basierend auf draw_cut_lines
if draw_cut_lines:
    grid_cell = zeichen + beschnitt  # 51mm (zu groß!)
else:
    grid_cell = zeichen              # 45mm

# Cropping nur ohne Schnittlinien
if draw_cut_lines:
    img_cropped = img  # Nicht gecroppt (51mm)
else:
    img_cropped = crop(img)  # Gecroppt (45mm)
```

**Resultat:**
- Grid mit Schnittlinien: 51mm pro Zeichen
- A4 Hochformat: 190mm nutzbare Breite → 190 / 51 = 3 Spalten (statt 4!)
- Layout komplett anders als ohne Schnittlinien

**Fix:**
```python
# RICHTIG: Grid IMMER auf finale Größe
grid_cell_width = zeichen_breite   # IMMER finale Größe
grid_cell_height = zeichen_hoehe

# IMMER croppen auf finale Größe
img_cropped = crop(img)  # Auch mit Schnittlinien!
# Rote Linie (Beschnittzugabe) wird abgeschnitten
```

**Ergebnis nach Fix:**
| Schnittlinien | Grid | Zeichen-Größe | Layout A4 Hochformat |
|---------------|------|---------------|---------------------|
| **AUS** | 45mm | 45mm (gecroppt) | 4×6 = 24 Zeichen ✓ |
| **AN** | 45mm | 45mm (gecroppt) | 4×6 = 24 Zeichen ✓ |

**Layout ist nun IDENTISCH!** 🎯

**Sichtbare Schnittlinien (wenn aktiviert):**
- **BLAU:** Schnittlinie (am Rand des Zeichens, 45mm)
- **GRÜN:** Canvas-Linie (3mm vom Rand, Sicherheitsbereich)
- **ROT:** Beschnittzugabe (NICHT sichtbar - liegt außerhalb, wird abgeschnitten) ✓

**Technische Details:**
- Funktion: `create_schnittbogen_pdf_streaming()` in `pdf_exporter.py`
- Grid-Berechnung: Zeile 835-849
- Cropping-Logik: Zeile 942-958
- Rahmen-Zeichnung: Zeile 987-992

**Betroffene Dateien:**
- `pdf_exporter.py`: Zeilen 835-992

---

### Schnitthilfslinien-Beschriftung zu weit von Linien entfernt

**Problem:**
Die Beschriftungen der Schnittlinien hatten alle den gleichen Abstand (40px) von ihrer Linie:
- Blaues Label (SCHNITT) war näher an der grünen Linie als an der eigenen blauen Linie
- Zuordnung der Labels zu ihren Linien war verwirrend
- Visuelle Hierarchie fehlte

**Fix:**
Unterschiedliche Abstände für äußere und innere Labels:
- **ROT (BESCHNITT):** 40px Offset (äußeres Label, viel Platz)
- **BLAU (SCHNITT):** 10px Offset (inneres Label, näher an Linie)
- **GRÜN (CANVAS):** 10px Offset (inneres Label, näher an Linie)

**Ergebnis:**
- Jedes Label ist nun klar seiner Linie zugeordnet
- Bessere visuelle Trennung zwischen den Labels
- Intuitivere Darstellung für Benutzer

**Betroffene Dateien:**
- `print_preparer.py`: Zeilen 303-334 (`_draw_cut_lines()`)

---

## 🔧 Technische Änderungen

### PDF-Export-Logik vereinfacht

**Vorher (v0.8.4):**
- Komplexe Logik mit bedingtem Cropping
- Grid-Berechnung abhängig von `draw_cut_lines` Flag
- Unterschiedliche Bildgrößen in Schnittbogen
- Bedingtes Rahmen-Zeichnen

**Nachher (v0.8.5):**
- Einfache, konsistente Logik
- Grid IMMER basierend auf finaler Zeichengröße
- Zeichen IMMER in finaler Größe (gecroppt)
- IMMER schwarzer Rahmen (Schnittlinie) für alle Zeichen

**Code-Reduktion:**
- `pdf_exporter.py`: -68 Zeilen, +39 Zeilen (29 Zeilen weniger, vereinfacht!)
- Klarere Kommentare und Struktur
- Weniger Verzweigungen (if/else)

---

## 📝 Dokumentations-Updates

### Keine Breaking Changes

Alle Änderungen sind **rückwärtskompatibel**:
- Bestehende PDFs werden identisch exportiert (wenn Schnittlinien AUS)
- Nur PDFs MIT Schnittlinien ändern sich (Korrektur des Bugs)
- Keine Änderungen an API oder Settings

---

## 🧪 Testing

### Manuelle Tests durchgeführt

✅ **PDF-Schnittbogen ohne Schnittlinien:**
- Layout: 4×6 Zeichen auf A4 Hochformat
- Zeichen: 45×45mm
- Schwarzer Rahmen um jedes Zeichen
- Keine sichtbaren Schnittlinien

✅ **PDF-Schnittbogen mit Schnittlinien:**
- Layout: 4×6 Zeichen auf A4 Hochformat (GLEICH!)
- Zeichen: 45×45mm (GLEICH!)
- Schwarzer Rahmen + blaue/grüne Schnittlinien
- Rote Linie NICHT sichtbar (abgeschnitten)

✅ **Rechteckige Zeichen (z.B. 28×32mm):**
- Layout korrekt berechnet
- Grid basiert auf tatsächlichen Abmessungen
- Cropping berücksichtigt Höhe und Breite separat

✅ **Schnitthilfslinien-Beschriftung:**
- Labels näher an ihren Linien
- Klare Zuordnung
- Keine Überlappungen

---

## 📊 Betroffene Komponenten

| Komponente | Datei | Änderung |
|------------|-------|----------|
| **PDF-Export** | `pdf_exporter.py` | Grid-Berechnung, Cropping, Rahmen |
| **Print-Vorbereitung** | `print_preparer.py` | Label-Positionierung |
| **Version** | `constants.py` | Version → 0.8.5 |

---

## 🔄 Migration

### Für Benutzer

**Keine Aktion erforderlich!**

Bestehende Einstellungen werden beibehalten. PDFs können wie gewohnt erstellt werden.

**Unterschiede bemerken:**
- Schnittbogen mit Schnittlinien haben nun gleiches Layout wie ohne Schnittlinien
- Labels der Schnitthilfslinien sind näher an ihren Linien
- Rote Linie (Beschnittzugabe) ist im Schnittbogen nicht mehr sichtbar (wurde abgeschnitten)

**Das ist korrekt und gewünscht!** Die rote Linie zeigt die Beschnittzugabe, die außerhalb der finalen Zeichengröße liegt.

---

## ⚠️ Bekannte Einschränkungen

Keine neuen Einschränkungen in dieser Version.

---

## 🙏 Danksagung

Vielen Dank an alle Benutzer für das Feedback und die Bug-Reports!

Besonderer Dank für die detaillierte Problembeschreibung, die zur schnellen Identifikation und Behebung des Schnittbogen-Bugs geführt hat.

---

## 📦 Download

**GitHub Release:** [v0.8.5](https://github.com/Hopeman876/Taktische_Zeichen_Druckgenerator_Develop/releases/tag/v0.8.5)

**Enthält:**
- Portable Windows .exe (keine Installation erforderlich)
- Source Code
- Diese Release Notes

---

## 🔗 Weitere Informationen

- **CHANGELOG:** Siehe Git-Log für vollständige Änderungshistorie
- **Benutzerhandbuch:** `User-documentation/BENUTZERHANDBUCH.md`
- **Build-Anleitung:** `BUILD_ANLEITUNG.md`

---

**Ende der Release Notes v0.8.5**

*Erstellt: 2025-12-16*
*Git-Commits: 75c9568, 526ed61*
