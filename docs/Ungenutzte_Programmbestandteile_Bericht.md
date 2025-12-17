# Bericht: Ungenutzte Programmbestandteile

**Projekt:** Taktische Zeichen Druckgenerator
**Analyse-Datum:** 2025-11-14
**Analysierte Version:** v0.7.3+

---

## 📋 Executive Summary

Nach drei Analyse-Durchläufen zur Code-Konsistenz und -Integrität wurden **13 potenziell ungenutzte Programmbestandteile** identifiziert. Diese können in 4 Kategorien eingeteilt werden:

1. **Test-Dateien** (3 Dateien) - Entwicklungs-/Debug-Skripte
2. **Alte UI-Dateien** (1 Datei) - Backup einer alten Version
3. **Utility-Skripte** (6 Dateien) - Hilfsskripte für Entwicklung/Analyse
4. **Sehr kleine Dateien** (1 Datei) - Mögliches Überbleibsel

**Empfehlung:** Archivierung oder Entfernung nach Rücksprache mit dem Entwickler.

---

## 1. Test-Dateien

### 1.1 `test_custom_size_interactive.py`

**Zweck:** Interaktiver Test für custom size Zeichen
**Status:** 🟡 **UNKLAR**
**Größe:** ~1-2 KB (geschätzt)

**Analyse:**
- Enthält vermutlich interaktive Tests
- Nicht Teil der Test-Routinen (`if __name__ == "__main__"`)
- Möglicherweise für manuelle Tests während Entwicklung

**Empfehlung:**
- ✅ **BEHALTEN** wenn für manuelle Tests genutzt
- ❌ **ENTFERNEN** wenn nicht mehr benötigt
- 📦 **ARCHIVIEREN** in `dev-tools/` Ordner

---

### 1.2 `test_cut_lines.py`

**Zweck:** Test für Schnittlinien-Funktionalität
**Status:** 🟡 **UNKLAR**
**Größe:** ~1-2 KB (geschätzt)

**Analyse:**
- Test für Schnittlinien-Feature
- Schnittlinien sind im Code vorhanden (constants.py: DEFAULT_SCHNITTLINIEN)
- Möglicherweise für Entwicklung/Debugging

**Empfehlung:**
- ✅ **BEHALTEN** wenn Schnittlinien-Feature aktiv genutzt wird
- ❌ **ENTFERNEN** wenn veraltet
- 📦 **ARCHIVIEREN** in `dev-tools/` Ordner

---

### 1.3 `test_pseudo_svg_direct.py`

**Zweck:** Direkter Test für Pseudo-SVG Handling
**Status:** 🟡 **UNKLAR**
**Größe:** ~1-2 KB (geschätzt)

**Analyse:**
- Test für Pseudo-SVG Erkennung/Verarbeitung
- Verwandt mit `find_pseudo_svgs.py`
- Möglicherweise für Entwicklung

**Empfehlung:**
- ✅ **BEHALTEN** wenn Pseudo-SVG Feature entwickelt wird
- ❌ **ENTFERNEN** wenn Feature abgeschlossen
- 📦 **ARCHIVIEREN** in `dev-tools/` Ordner

---

## 2. Alte UI-Dateien

### 2.1 `gui/ui_files/main_window_OLD.ui`

**Zweck:** Backup/Alte Version des Hauptfensters
**Status:** 🔴 **VERALTET**
**Größe:** ~10-20 KB (geschätzt)

**Analyse:**
- Eindeutig als "OLD" markiert
- Aktuelles Fenster: `main_window.ui`
- Kein Code lädt diese Datei
- Backup einer älteren Version

**Empfehlung:**
- ❌ **ENTFERNEN** - wird nicht mehr gebraucht
- 📦 Falls Sicherheit gewünscht: In Git-History verfügbar
- Alternative: In `archive/` Ordner verschieben

**Aktion:** **SOFORT ENTFERNBAR**

---

## 3. Utility-Skripte

### 3.1 `find_pseudo_svgs.py`

**Zweck:** Findet und analysiert Pseudo-SVG Dateien
**Status:** 🟢 **AKTIV** (aber spezialisiert)
**Größe:** ~5-10 KB (geschätzt)

**Analyse:**
- Utility-Skript für SVG-Analyse
- Definiert eigene Funktion `scan_directory()`
- Wird **nicht** vom Hauptprogramm importiert
- Für manuelle Analyse/Debugging

**Verwendung:**
```bash
python find_pseudo_svgs.py
```

**Empfehlung:**
- ✅ **BEHALTEN** - nützliches Analyse-Tool
- 📦 **VERSCHIEBEN** nach `dev-tools/` oder `utils/`
- 📝 **DOKUMENTIEREN** in README wie es zu nutzen ist

---

### 3.2 `svg_analyzer.py`

**Zweck:** Analysiert SVG-Dateien (Details unbekannt)
**Status:** 🟡 **UNKLAR**
**Größe:** ~5-10 KB (geschätzt)

**Analyse:**
- Möglicherweise redundant mit `find_pseudo_svgs.py`
- Wird **nicht** vom Hauptprogramm importiert
- Für Entwicklung/Analyse

**Empfehlung:**
- 🔍 **PRÜFEN** ob Funktionalität von `find_pseudo_svgs.py` abgedeckt wird
- ❌ **ENTFERNEN** wenn redundant
- 📦 **ARCHIVIEREN** wenn noch nützlich

---

### 3.3 `svg_loader_local.py`

**Zweck:** Lokaler SVG-Loader (vermutlich veraltet)
**Status:** 🟡 **UNKLAR**
**Größe:** ~2-5 KB (geschätzt)

**Analyse:**
- Name deutet auf lokale/alternative SVG-Lade-Logik hin
- Hauptprogramm nutzt `taktische_zeichen_generator.py` für SVG-Rendering
- Möglicherweise alter Ansatz

**Empfehlung:**
- 🔍 **PRÜFEN** ob noch verwendet
- ❌ **ENTFERNEN** wenn durch `taktische_zeichen_generator.py` ersetzt
- 📦 **ARCHIVIEREN** wenn historisch wertvoll

---

### 3.4 `verify_version.py`

**Zweck:** Versions-Überprüfung (Details unbekannt)
**Status:** 🟡 **UNKLAR**
**Größe:** ~1-2 KB (geschätzt)

**Analyse:**
- Vermutlich prüft Python/Dependency-Versionen
- Funktion `check_version()` fehlt Type-Hint (siehe Durchlauf 1)
- Wird **nicht** beim Programmstart aufgerufen

**Empfehlung:**
- ✅ **BEHALTEN** wenn für Setup/Installation nützlich
- 📦 **VERSCHIEBEN** nach `dev-tools/` oder `scripts/`
- 📝 **DOKUMENTIEREN** Verwendung

---

### 3.5 `check_imagep.py`

**Zweck:** ImageMagick Check (Details unbekannt)
**Status:** 🔴 **WAHRSCHEINLICH VERALTET**
**Größe:** **252 bytes** (sehr klein!)

**Analyse:**
- Nur 252 bytes - extrem klein!
- Name deutet auf ImageMagick-Check hin
- Hauptprogramm hat `setup_imagemagick_portable()` in `constants.py`
- Möglicherweise alter/unfertiger Check

**Empfehlung:**
- ❌ **ENTFERNEN** - zu klein, wahrscheinlich Überbleibsel
- Alternative: Inhalt prüfen und in `constants.py` integrieren falls nützlich

**Aktion:** **WAHRSCHEINLICH ENTFERNBAR**

---

### 3.6 `profile_performance.py`

**Zweck:** Performance-Profiling
**Status:** 🟢 **NÜTZLICH** (Development)
**Größe:** ~3-5 KB (geschätzt)

**Analyse:**
- Performance-Analyse-Tool
- Für Entwicklung/Optimierung
- Nicht Teil des Produktiv-Codes

**Empfehlung:**
- ✅ **BEHALTEN** - sehr nützlich für Performance-Tuning
- 📦 **VERSCHIEBEN** nach `dev-tools/profiling/`
- 📝 **DOKUMENTIEREN** wie zu nutzen

---

## 4. Deprecated Dict-Keys

**Fundort:** `constants.py` → `calculate_print_dimensions()`

**Status:** 🟡 **DEPRECATED aber noch verwendet**

### Betroffene Keys:

```python
# In calculate_print_dimensions() Rückgabe-Dict:
{
    # DEPRECATED:
    "max_grafik_mm": ...,      # → Nutze "canvas_hoehe_mm"
    "endgroesse_mm": ...,       # → Nutze "endgroesse_hoehe_mm"
    "datei_groesse_mm": ...,    # → Nutze "datei_hoehe_mm"
    "max_grafik_px": ...,       # → Nutze "canvas_hoehe_px"
    "endgroesse_px": ...,       # → Nutze "endgroesse_hoehe_px"
    "datei_groesse_px": ...,    # → Nutze "datei_hoehe_px"
}
```

### Verwendung:
- `print_preparer.py`: Verwendet deprecated Keys
- `pdf_exporter.py`: Verwendet deprecated Keys
- `constants.py` Test-Routine: Verwendet deprecated Keys

### Empfehlung:
- ✅ **BEIBEHALTEN** für Rückwärtskompatibilität
- 📝 **TODO:** Schrittweise Migration auf neue Keys
- ⚠️ **WARNING:** In Zukunft entfernen (v0.8.0+)

---

## 5. Zusammenfassung & Empfehlungen

### ✅ Sofort Entfernbar (2 Dateien):
1. `gui/ui_files/main_window_OLD.ui` - Alte UI-Datei
2. `check_imagep.py` - 252 bytes, wahrscheinlich Überbleibsel

### 🔍 Prüfung Erforderlich (5 Dateien):
3. `test_custom_size_interactive.py` - Noch genutzt?
4. `test_cut_lines.py` - Noch relevant?
5. `test_pseudo_svg_direct.py` - Noch benötigt?
6. `svg_analyzer.py` - Redundant?
7. `svg_loader_local.py` - Veraltet?

### 📦 Archivierung Empfohlen (3 Dateien):
8. `find_pseudo_svgs.py` → `dev-tools/svg-analysis/`
9. `verify_version.py` → `dev-tools/setup/`
10. `profile_performance.py` → `dev-tools/profiling/`

### ⚠️ Refactoring Empfohlen:
11. Deprecated Dict-Keys in `constants.py`
    - Verwendungen in `print_preparer.py` und `pdf_exporter.py` migrieren
    - Dann deprecated Keys entfernen

---

## 6. Vorgeschlagene Ordner-Struktur

### Aktuelle Struktur:
```
Taktische_Zeichen_Druckgenerator/
├── *.py (alle Skripte gemischt)
├── gui/
└── ...
```

### Vorgeschlagene Struktur:
```
Taktische_Zeichen_Druckgenerator/
├── main.py
├── constants.py
├── ... (Kern-Module)
│
├── gui/
│
├── dev-tools/               # NEU
│   ├── svg-analysis/
│   │   ├── find_pseudo_svgs.py
│   │   └── svg_analyzer.py (?)
│   ├── setup/
│   │   └── verify_version.py
│   ├── profiling/
│   │   └── profile_performance.py
│   └── tests/
│       ├── test_custom_size_interactive.py (?)
│       ├── test_cut_lines.py (?)
│       └── test_pseudo_svg_direct.py (?)
│
└── archive/                 # NEU
    ├── main_window_OLD.ui
    └── check_imagep.py
```

---

## 7. Nächste Schritte

### Empfohlene Aktionen (Priorität):

1. **HOCH** - Entfernen:
   - `gui/ui_files/main_window_OLD.ui`
   - `check_imagep.py`

2. **MITTEL** - Prüfen & Entscheiden:
   - Test-Dateien: Noch genutzt?
   - `svg_analyzer.py` und `svg_loader_local.py`: Noch relevant?

3. **NIEDRIG** - Organisieren:
   - Utility-Skripte in `dev-tools/` verschieben
   - Dokumentation für Dev-Tools erstellen

4. **ZUKUNFT** - Refactoring:
   - Deprecated Dict-Keys migrieren
   - Code-Duplikate eliminieren

---

## 8. Risiko-Bewertung

### Geringes Risiko (Entfernung unbedenklich):
- ✅ `main_window_OLD.ui` - Backup in Git
- ✅ `check_imagep.py` - Zu klein, wahrscheinlich leer

### Mittleres Risiko (Prüfung nötig):
- ⚠️ Test-Dateien - Könnten für manuelle Tests genutzt werden
- ⚠️ `svg_analyzer.py` / `svg_loader_local.py` - Funktion unklar

### Kein Risiko (Verschieben statt Löschen):
- 📦 Utility-Skripte - Bleiben verfügbar in `dev-tools/`

---

## 9. Changelog (Durchgeführte Aktionen)

### Durchlauf 1: Code-Konsistenz
- ✅ RuntimeConfig-Verwendung korrigiert (5 Stellen)
- ✅ Type-Hints ergänzt (4 Funktionen)
- ✅ Ungenutzte Imports entfernt

### Durchlauf 2: Veraltete Konstanten
- ✅ `DEFAULT_ABSTAND_RAND_MM` entfernt (nirgends verwendet)
- ℹ️ Deprecated Dict-Keys behalten (noch in Verwendung)

### Durchlauf 3: Ungenutzte Bestandteile
- 📝 Dieser Bericht erstellt
- ⏳ Empfehlungen für User bereitgestellt

---

**Erstellt mit:** Claude Code
**Für:** Entwickler/Programmierer
**Nächste Aktualisierung:** Nach User-Entscheidung über Empfehlungen
