# Build-Anleitung - Taktische Zeichen Druckgenerator

## 📦 Release-Build erstellen

### Schnellstart

**Windows (Primäres System):**
```bash
build_exe.bat
```

**Linux (Experimentell - wird getestet):**
```bash
chmod +x build_linux.sh
./build_linux.sh
```

**Hinweis:** macOS wird derzeit **nicht unterstützt**. Windows ist das primär unterstützte System, Linux-Support ist experimentell.

Das Skript führt **automatisch** alle notwendigen Schritte aus:
1. ✅ Liest Version aus `constants.py`
2. ✅ Baut Executable/Binary mit PyInstaller
3. ✅ Kopiert Release Notes (MD + PDF falls vorhanden)
4. ✅ Erstellt versionierten Release-Ordner
5. ✅ Erstellt ZIP-Archiv

### Voraussetzungen

#### Erforderlich (alle Plattformen)
- Python 3.8+
- PyInstaller: `pip install pyinstaller`
- Alle Projekt-Dependencies: `pip install -r requirements.txt`

#### Windows-spezifisch
- ImageMagick wird als portable Version mitgeliefert (im Repo enthalten)

#### Linux-spezifisch
- **ImageMagick:** `sudo apt-get install imagemagick` (Debian/Ubuntu)
  - Fedora: `sudo dnf install ImageMagick`
  - Arch: `sudo pacman -S imagemagick`
- **zip:** `sudo apt-get install zip`
- **Hinweis:** ImageMagick wird NICHT ins Binary gebündelt, muss auf Zielsystem installiert sein

#### Optional (für PDF-Release-Notes)
- Erstelle manuell `release_notes\RELEASE_NOTES_v{VERSION}.pdf`
- Wird automatisch mitkopiert falls vorhanden

---

## 📁 Output-Struktur

Nach dem Build:

```
releases/
├── TaktischeZeichenDruckgenerator_v0.8.0/
│   ├── TaktischeZeichenDruckgenerator.exe
│   ├── imagemagick/                    # ImageMagick portable
│   ├── resources/                       # Logo & Icon
│   ├── gui/ui_files/                   # UI-Definitionen
│   ├── RELEASE_NOTES_v0.8.0.md         # Release Notes (immer)
│   ├── RELEASE_NOTES_v0.8.0.pdf        # Release Notes (optional, wenn pandoc verfügbar)
│   └── [weitere DLLs & Dependencies]
│
└── TaktischeZeichenDruckgenerator_v0.8.0.zip  # Fertiges Distributions-Archiv
```

---

## 🔧 Was macht build_exe.bat?

Das Skript führt folgende Schritte automatisch aus:

1. **Alte Builds löschen** - `build/` und `dist/` Ordner
2. **Optimierte .pyc erstellen** - Schnellerer Import
3. **PyInstaller Build** - Erstellt Executable
4. **Zusätzliche Dateien kopieren** - README, Release Notes (MD + PDF)
5. **ImageMagick verschieben** - Von `_internal/` nach Root
6. **Versionierten Release-Ordner erstellen** - `releases\TaktischeZeichenDruckgenerator_v{VERSION}\`
7. **ZIP-Archiv erstellen** - `releases\TaktischeZeichenDruckgenerator_v{VERSION}.zip`

Alles vollautomatisch!

---

## 📝 Version ändern - Checklist

Beim Erstellen einer neuen Version:

- [ ] `constants.py` → `PROGRAM_VERSION` erhöhen
- [ ] `release_notes/RELEASE_NOTES_v{VERSION}.md` erstellen
- [ ] Optional: `release_notes/RELEASE_NOTES_v{VERSION}.pdf` manuell erstellen
- [ ] Alle Änderungen commiten
- [ ] `build_exe.bat` ausführen
- [ ] Release testen (starte .exe aus `releases/` Ordner)
- [ ] Git-Tag erstellen: `git tag v{VERSION}`
- [ ] Tag pushen: `git push origin v{VERSION}`
- [ ] ZIP zu GitHub Releases hochladen

---

## 🐛 Troubleshooting

### Fehler: "PROGRAM_VERSION nicht gefunden"
**Ursache:** `constants.py` fehlt oder Format ist falsch

**Lösung:**
```python
# constants.py muss enthalten:
PROGRAM_VERSION = "0.8.0"  # Exakt dieses Format!
```

### Fehler: "PyInstaller Build fehlgeschlagen"
**Häufige Ursachen:**
- Dependencies fehlen → `pip install -r requirements.txt`
- `.spec` Datei defekt → Aus Git wiederherstellen
- Alte Build-Artefakte → `pyinstaller --clean` verwenden

**Debugging:**
```bash
# Verbose Output
pyinstaller --clean --log-level DEBUG TaktischeZeichenDruckgenerator.spec
```

### Info: "Keine PDF-Release-Notes gefunden"
**Ursache:** `release_notes\RELEASE_NOTES_v{VERSION}.pdf` nicht vorhanden

**Auswirkung:** Release enthält nur `.md` Release Notes

**Behebung:** Optional - PDF manuell erstellen und in `release_notes/` ablegen

### ZIP-Datei zu groß (>100 MB)
**Ursache:** Build-Optimierungen in `.spec` nicht aktiv

**Prüfen:**
```python
# TaktischeZeichenDruckgenerator.spec sollte enthalten:
excludes=[
    'numpy', 'pandas', 'matplotlib',  # ~30-50 MB
    'PyQt6.QtNetwork', ...            # ~10-15 MB
]

# Und:
a.binaries = [x for x in a.binaries if not x[0].startswith('opengl32sw')]  # ~20 MB
```

**Erwartete Größe:** ~50-70 MB (ZIP)

---

## 📊 Build-Performance

Typische Build-Zeiten (Intel i7, SSD):

| Schritt | Dauer |
|---------|-------|
| PyInstaller Clean Build | ~60s |
| Release-Ordner kopieren | ~5s |
| PDF-Konvertierung (optional) | ~10s |
| ZIP-Erstellung | ~15s |
| **Gesamt** | **~90s** |

---

## 🔮 Zukünftige Verbesserungen

Geplante Features für `build_exe.bat`:

- [ ] Automatische Changelog-Generierung aus Git-Commits
- [ ] Code-Signierung (Windows Authenticode)
- [ ] Automatischer Upload zu GitHub Releases
- [ ] Build-Matrix (32-bit / 64-bit)
- [ ] Checksummen-Dateien (SHA256)
- [ ] Installer-Erstellung (NSIS / Inno Setup)
- [ ] Automatische PDF-Konvertierung (falls pandoc installiert)

---

## 🐧 Plattform-spezifische Hinweise

### Linux

**Build:**
- Binary heißt `TaktischeZeichenDruckgenerator` (ohne .exe)
- Ausgabe: `releases/TaktischeZeichenDruckgenerator_v{VERSION}_Linux.zip`

**Distribution:**
- ImageMagick MUSS auf Zielsystem installiert sein
- Empfohlene Installation auf Zielsystem:
  ```bash
  # Debian/Ubuntu
  sudo apt-get install imagemagick python3-pyqt6

  # Fedora
  sudo dnf install ImageMagick python3-qt6

  # Arch
  sudo pacman -S imagemagick python-pyqt6
  ```

**Schriftarten:**
- Installiere Schriftarten systemweit: `/usr/share/fonts/truetype/`
- Oder user-spezifisch: `~/.local/share/fonts/`
- RobotoSlab empfohlen: `sudo apt-get install fonts-roboto`

**Ausführung:**
```bash
cd TaktischeZeichenDruckgenerator_v{VERSION}_Linux
./TaktischeZeichenDruckgenerator
```

**Bekannte Probleme:**
- Manche Linux-Distributionen benötigen zusätzliche Qt6-Plugins
- Fehlende Bibliotheken: `ldd TaktischeZeichenDruckgenerator` zeigt fehlende Dependencies
- **Linux-Support ist experimentell** - bitte melde Probleme als GitHub Issue

### Windows (Primäres System)

**Build:**
- Binary heißt `TaktischeZeichenDruckgenerator.exe`
- ImageMagick ist portable mitgeliefert (keine Installation nötig)
- Ausgabe: `releases/TaktischeZeichenDruckgenerator_v{VERSION}.zip`

**Distribution:**
- **Vollständig eigenständig** (portable)
- Keine Installation von ImageMagick nötig
- Schriftarten optional (Arial Fallback vorhanden)
- **Primär getestet und unterstützt**

### macOS (Nicht unterstützt)

**Status:** macOS wird derzeit **nicht unterstützt**.

**Gründe:**
- Keine extensiven Tests durchgeführt
- App-Bundling (.app) nicht implementiert
- Gatekeeper-Kompatibilität nicht gewährleistet
- Kein Zugriff auf macOS-Testsystem

**Hinweis:** Falls du macOS-Support benötigst, erstelle bitte ein GitHub Issue. Community-Beiträge sind willkommen!

---

## 📞 Support

Bei Problemen:
1. Prüfe diese Anleitung
2. Suche in GitHub Issues
3. Erstelle neues Issue mit:
   - Build-Log (`build_exe.bat` Output)
   - Python-Version (`python --version`)
   - PyInstaller-Version (`pyinstaller --version`)

---

**Letzte Aktualisierung:** 2025-11-16 (v0.8.0)
