# Offene Aufgaben - Taktische Zeichen Druckgenerator

**Stand:** 2025-12-03
**Version:** v0.8.2

---

## ✅ Erledigte Aufgaben (v0.8.2)

### Code-Quality Cleanup
**Abgeschlossen:** 2025-12-03

- ✅ RuntimeConfig vollständig integriert (80+ Stellen gefixt)
- ✅ Magic Numbers eliminiert (A4-Dimensionen, Schwellwerte)
- ✅ Unused Imports entfernt
- ✅ Unused Files entfernt (modus_*_dialog.py + .ui)
- ✅ Temp-Image-Größe optimiert (100px → 1000px = 10x Genauigkeit)
- ✅ Alle Unit-Tests bestehen (constants, runtime_config, S1-layout, S2-layout)

**Neue Konstanten:**
- `DIN_A4_WIDTH_MM`, `DIN_A4_HEIGHT_MM`
- `ZEICHEN_SIZE_THRESHOLD_VERY_LARGE_MM`, `ZEICHEN_SIZE_THRESHOLD_LARGE_MM`
- `TEMP_IMAGE_SIZE_PX`

### S2-Layout Test-Suite
**Abgeschlossen:** 2025-12-03

- ✅ `test_s2_layout.py` erstellt (5 Integrationstests)
- ✅ Aspect Lock Feature (v0.8.2.4) getestet
- ✅ Alle S2-Tests bestehen (5/5)

**Test-Szenarien:**
1. Standard quadratisch (45×45mm, Aspect Lock ON)
2. Rechteckig (60×40mm, Aspect Lock OFF)
3. Großes Zeichen (100×80mm)
4. Kleines Zeichen (30×30mm, Edge Case)
5. Aspect Lock Toggle (45mm → 90mm Breite)

---

## ⚠️ Bekannte Warnungen

### UTF-8 Pango Warning
**Symptom:** Terminal-Warnung während Export
```
** (process:XXXXX): WARNING **: HH:MM:SS.XXX: Invalid UTF-8 string passed to pango_layout_set_text()
```

**Ursache:** Unbekannt - vermutlich ImageMagick/Wand bei SVG-Text-Rendering
**Betroffene Module:** Wahrscheinlich `taktische_zeichen_generator.py`, `text_overlay.py`, oder `wand.drawing`
**Impact:** Keine Funktionsbeeinträchtigung, nur Log-Spam
**Priorität:** LOW - Funktionalität nicht betroffen
**Nächster Schritt:** Debuggen mit spezifischer Unicode-Test-Datei

---

**Letzte Aktualisierung:** 2025-12-03
**Status:** Keine kritischen Bugs offen
