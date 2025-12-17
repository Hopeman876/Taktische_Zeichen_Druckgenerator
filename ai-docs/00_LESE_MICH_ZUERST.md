# AI-Docs - Navigations-Guide

**Aktualisiert:** 2025-12-14
**Version:** v0.8.4
**Für:** Claude AI

---

## Lesereihenfolge (Pflicht)

1. **00_Projektbeschreibung.md** - Projektübersicht
2. **01_code-guidelines.md** - Code-Konventionen (KRITISCH!)
3. **04_RuntimeConfig-Guidelines.md** - RuntimeConfig-System (KRITISCH!)
4. **02_GUI-Struktur.md** - GUI-Architektur
5. **03_general-guidelines.md** - Git, Versionierung
6. **06_Build-und-Release.md** - Build-Prozess & GitHub Workflow (NEU v0.8.4)
7. **05_Offene_Aufgaben.md** - Bekannte Issues

---

## Dokument-Übersicht

| Datei | Inhalt | Priorität |
|-------|--------|-----------|
| **00_Projektbeschreibung.md** | Projekt, Modi, Struktur | 🔴 Hoch |
| **01_code-guidelines.md** | Formatierung, Naming, ASCII-only | 🔴 Hoch |
| **02_GUI-Struktur.md** | Qt Designer, modus_config.py | 🟡 Mittel |
| **03_general-guidelines.md** | Git-Workflow, Dokumentation | 🟡 Mittel |
| **04_RuntimeConfig-Guidelines.md** | SYSTEM_*/DEFAULT_* Regeln | 🔴 Hoch |
| **05_Offene_Aufgaben.md** | Bekannte Warnungen/Bugs | 🟢 Niedrig |
| **06_Build-und-Release.md** | PyInstaller, GitHub Workflow | 🟡 Mittel |

---

## Quick Reference

### Code-Konventionen
→ **01_code-guidelines.md**
- 4 Spaces (KEINE Tabs)
- ASCII-only in Code-Strings
- Keine Magic Numbers
- LoggingManager statt print()
- Google-Style Docstrings

### RuntimeConfig (KRITISCH!)
→ **04_RuntimeConfig-Guidelines.md**

**Goldene Regel:**
```python
# ❌ FALSCH
from constants import DEFAULT_MODUS
modus = DEFAULT_MODUS

# ✅ RICHTIG
from runtime_config import get_config
modus = get_config().standard_modus
```

**Konstanten-Arten:**
- `SYSTEM_*` = Unveränderlich (OK direkt zu nutzen)
- `DEFAULT_*` = Überschreibbar (NUR via RuntimeConfig!)

### Modi-System
→ **Code:** `gui/modus_config.py` (Single Source of Truth)
→ **Doku:** `00_Projektbeschreibung.md`

**7 Modi:** OV+Stärke, Ort+Stärke, Schreiblinie+Stärke (S1/S2), Ruf, Freitext, Dateiname, Nur Grafik

### Projektstruktur
```
/
├── ai-docs/              # Diese Dokumentation
├── gui/
│   ├── ui_files/         # Qt Designer .ui
│   ├── dialogs/          # Dialog-Klassen
│   ├── widgets/          # Custom Widgets
│   └── modus_config.py   # Modi-Definitionen (Master)
├── constants.py          # SYSTEM_* + DEFAULT_* Konstanten
├── runtime_config.py     # Runtime-Konfiguration
├── settings_manager.py   # settings.json Persistenz
├── taktische_zeichen_generator.py  # Kern-Generator
├── text_overlay.py       # Text-Rendering
├── pdf_exporter.py       # PDF-Export
└── main.py               # Entry Point
```

### Git-Workflow
→ **03_general-guidelines.md**
→ **CLAUDE.md** (Root)

**WICHTIG:**
- KEINE automatischen Commits!
- Nur auf User-Anweisung committen
- Google-Style Commit-Messages

### Settings (settings.json)
→ **Code:** `settings_manager.py`

Wichtige Parameter:
- `zeichen.zeichen_hoehe_mm / zeichen_breite_mm`
- `zeichen.export_dpi` (Standard-DPI)
- `zeichen.standard_modus` ("freitext")
- `zeichen.font_size` / `font_family`

---

## Version v0.8.4 Highlights

**Neue Features:**
- Konfigurierbare Seitenverhältnis-Fixierung für S1 (2:1) und S2 (1:1)
- Einstellungen persistent in settings.json
- Beide Layouts standardmäßig mit fixierten Seitenverhältnissen

**Kritische Bugfixes:**
- Signal-Handler-Reihenfolge korrigiert (Aspekt-Berechnungen sofort)
- Breite-Feld wird beim Start korrekt gesperrt
- Deutsche Rechtschreibung: "Druckgröße" statt "Druckgroesse"

**Build & Release:**
- ✅ Automatische Releases via GitHub Workflow
- ✅ ReportLab vollständig in PyInstaller integriert
- ✅ pyinstaller-hooks-contrib für korrekte Builds

**Details:** `release_notes/RELEASE_NOTES_v0.8.4.md`

---

## Kritische Regeln für Claude

### 1. RuntimeConfig
❌ NIEMALS `DEFAULT_*` direkt aus constants.py
✅ IMMER `get_config()` verwenden

### 2. Code-Formatierung
- 4 Spaces (KEINE Tabs)
- ASCII-only in Code-Strings (keine →, ✓, 📁)
- Keine Magic Numbers (zentrale Konstanten)

### 3. GUI-Entwicklung
- Qt Designer für statische UI (.ui-Dateien)
- modus_config.py für Modi-Definitionen
- Keine hardcodierten GUI-Labels

### 4. Git
- Nur committen wenn User explizit anfordert
- Google-Style Commit-Messages
- Branch: siehe CLAUDE.md

---

## Wo finde ich...?

**...Code-Konventionen?**
→ 01_code-guidelines.md

**...RuntimeConfig-Regeln?**
→ 04_RuntimeConfig-Guidelines.md (VERPFLICHTEND!)

**...GUI-Architektur?**
→ 02_GUI-Struktur.md

**...Modi-Definitionen?**
→ Code: `gui/modus_config.py`
→ Doku: 00_Projektbeschreibung.md

**...Projektstruktur?**
→ 00_Projektbeschreibung.md

**...Bekannte Issues?**
→ 05_Offene_Aufgaben.md

**...Git-Workflow?**
→ 03_general-guidelines.md + CLAUDE.md (Root)

**...Build & Release Prozess?**
→ 06_Build-und-Release.md (PyInstaller, GitHub Workflow)

**...PyInstaller .spec Konfiguration?**
→ 06_Build-und-Release.md + TaktischeZeichenDruckgenerator.spec

**...GitHub Workflow?**
→ 06_Build-und-Release.md + .github/workflows/release.yml

---

**Next:** Lies **00_Projektbeschreibung.md** für Projekt-Übersicht
