# 📦 ImageMagick Portable Installation für Windows

Diese Anleitung zeigt, wie du ImageMagick **portable** (ohne Installation) für das Projekt einrichtest.

---

## 🎯 Übersicht

Wand (Python-Wrapper) benötigt die ImageMagick-DLLs. Wir packen diese direkt ins Projekt-Verzeichnis, sodass keine System-Installation nötig ist.

---

## 📥 Schritt 1: ImageMagick Portable herunterladen

### Option A: Von offizieller Seite (Empfohlen)

1. Gehe zu: **https://imagemagick.org/script/download.php#windows**

2. Lade die **portable** Version herunter:
   - Suche nach: `ImageMagick-7.x.x-portable-Q16-HDRI-x64.zip`
   - Beispiel: `ImageMagick-7.1.1-21-portable-Q16-HDRI-x64.zip`
   - **WICHTIG:** "portable" und "x64" muss im Namen sein!

3. Entpacke das ZIP

### Option B: Direktlink (falls verfügbar)

```
https://imagemagick.org/archive/binaries/ImageMagick-7.1.1-21-portable-Q16-HDRI-x64.zip
```
*(Versionsnummer kann abweichen - nimm die neueste)*

---

## 📂 Schritt 2: DLLs ins Projekt kopieren

### 2.1 Ordner erstellen

Im Projekt-Verzeichnis:
```
TaktischeZeichenDruckgenerator/
└── imagemagick/
```

### 2.2 DLLs kopieren

Aus dem entpackten ImageMagick-Ordner kopiere **ALLE** Dateien nach `imagemagick/`:

**Wichtigste Dateien:**
- `magick.exe`
- `CORE_RL_*.dll` (alle!)
- `IM_MOD_*.dll` (alle!)
- `libxml2.dll`
- `zlib1.dll`
- `liblzma.dll`
- Etc. (ca. 50-100 Dateien)

**Tipp:** Kopiere einfach den **kompletten Inhalt** des entpackten Ordners!

### 2.3 Dateistruktur prüfen

Dein Projekt sollte jetzt so aussehen:
```
TaktischeZeichenDruckgenerator/
├── imagemagick/
│   ├── magick.exe
│   ├── CORE_RL_*.dll
│   ├── IM_MOD_*.dll
│   └── ... (viele weitere Dateien)
├── src/
├── exports/
├── poc_main_v2.py
└── requirements.txt
```

---

## 🔧 Schritt 3: Python-Pakete installieren

### 3.1 Alte Pakete deinstallieren

```bash
pip uninstall cairosvg cairocffi -y
```

### 3.2 Neue Pakete installieren

```bash
pip install -r requirements.txt
```

Oder direkt:
```bash
pip install Wand>=0.6.13
```

---

## ⚙️ Schritt 4: Umgebungsvariable setzen

Damit Wand die DLLs findet, müssen wir die Umgebungsvariable setzen.

### Option A: Im Code (Automatisch)

Füge am Anfang von `poc_constants_v2.py` hinzu:

```python
import os
from pathlib import Path

# ImageMagick Portable-Pfad setzen
IMAGEMAGICK_DIR = Path(__file__).parent / "imagemagick"
if IMAGEMAGICK_DIR.exists():
    os.environ['MAGICK_HOME'] = str(IMAGEMAGICK_DIR)
    # DLL-Pfad zum PATH hinzufügen
    os.environ['PATH'] = str(IMAGEMAGICK_DIR) + os.pathsep + os.environ.get('PATH', '')
```

### Option B: Manuell setzen (für Tests)

**PowerShell:**
```powershell
$env:MAGICK_HOME = "C:\Programmierung\Taktische_Zeichen_Editor\imagemagick"
$env:PATH = "C:\Programmierung\Taktische_Zeichen_Editor\imagemagick;" + $env:PATH
```

**CMD:**
```cmd
set MAGICK_HOME=C:\Programmierung\Taktische_Zeichen_Editor\imagemagick
set PATH=C:\Programmierung\Taktische_Zeichen_Editor\imagemagick;%PATH%
```

---

## ✅ Schritt 5: Test

### 5.1 ImageMagick direkt testen

```bash
cd imagemagick
.\magick.exe --version
```

Sollte ausgeben: `Version: ImageMagick 7.x.x ...`

### 5.2 Wand testen

```bash
python -c "from wand.image import Image; print('Wand OK')"
```

Sollte ausgeben: `Wand OK`

### 5.3 SVG-Konvertierung testen

```bash
python poc_main_v2.py
```

---

## 🐛 Troubleshooting

### Problem: "Wand can't find ImageMagick"

**Lösung 1:** Prüfe `MAGICK_HOME`:
```bash
echo $env:MAGICK_HOME  # PowerShell
echo %MAGICK_HOME%     # CMD
```

**Lösung 2:** Füge Code in `poc_constants_v2.py` hinzu (siehe Option A oben)

**Lösung 3:** Starte neues Terminal (PATH-Änderungen werden erst nach Neustart aktiv)

---

### Problem: "DLL not found"

**Lösung:** Stelle sicher, dass **ALLE** Dateien aus dem ImageMagick-Portable-ZIP kopiert wurden, nicht nur die DLLs!

---

### Problem: "magick.exe funktioniert nicht"

**Lösung:** Lade die **portable** Version herunter, nicht die "static" Version!

---

## 📦 Für .exe-Build (später)

Wenn wir später mit PyInstaller eine .exe bauen:

1. **ImageMagick-Ordner mitpacken**
2. **In .spec-Datei hinzufügen:**

```python
datas=[
    ('imagemagick', 'imagemagick'),
],
```

3. **Im Code MAGICK_HOME setzen** (wie in Option A)

Dann ist die .exe komplett **portable** und funktioniert auf jedem Windows-PC!

---

## 🔧 Troubleshooting

### Fehler: "RegistryKeyLookupFailed 'CoderModulesPath'"

**Problem:**
```
ERROR | Fehler bei SVG-Konvertierung: RegistryKeyLookupFailed `CoderModulesPath' @ error/module.c/GetMagickModulePath/679
```

**Ursache:**
ImageMagick versucht, die Windows-Registry zu lesen, anstatt die Environment-Variablen zu verwenden.

**Lösung:**
Die Anwendung setzt automatisch folgende Environment-Variablen:
- `MAGICK_HOME`
- `MAGICK_CODER_MODULE_PATH`
- `MAGICK_FILTER_MODULE_PATH`
- `MAGICK_CONFIGURE_PATH`
- `MAGICK_MODULE_PATH`

**Prüfen:**
1. Aktiviere Debug-Logging in den Einstellungen (Log-Level: DEBUG)
2. Starte die Anwendung neu
3. Prüfe die Log-Datei in `Logs/` - du solltest sehen:
   ```
   DEBUG | MAGICK_HOME: C:\...\imagemagick
   DEBUG | MAGICK_CODER_MODULE_PATH: C:\...\imagemagick\modules\coders
   DEBUG | MAGICK_FILTER_MODULE_PATH: C:\...\imagemagick\modules\filters
   DEBUG | MAGICK_CONFIGURE_PATH: C:\...\imagemagick
   DEBUG | MAGICK_MODULE_PATH: C:\...\imagemagick\modules
   ```

**Falls die Variablen nicht gesetzt sind:**
- Prüfe, ob der `imagemagick/` Ordner existiert
- Prüfe, ob `imagemagick/modules/coders/` und `imagemagick/modules/filters/` existieren
- Prüfe, ob alle DLL-Dateien vorhanden sind

**Falls die Variablen gesetzt sind, aber der Fehler weiterhin auftritt:**
- Stelle sicher, dass KEINE System-Installation von ImageMagick vorhanden ist (diese kann Konflikte verursachen)
- Deinstalliere ggf. eine vorhandene ImageMagick-Installation
- Lösche Registry-Keys: `HKEY_LOCAL_MACHINE\SOFTWARE\ImageMagick` (als Administrator)

---

## ✅ Fertig!

Nach diesen Schritten sollte alles funktionieren:
- ✅ ImageMagick portable im Projekt
- ✅ Keine System-Installation nötig
- ✅ Funktioniert auf jedem PC
- ✅ Bereit für .exe-Build

---

## 📊 Speicherplatz

Der `imagemagick/` Ordner ist ca. **80-120 MB** groß.

Für Versionskontrolle (Git):
- ❌ **NICHT** in Git committen (zu groß!)
- ✅ In `.gitignore` eintragen: `imagemagick/`
- ✅ Separat bereitstellen (z.B. als ZIP-Download)

---

## 🔗 Weitere Infos

- **ImageMagick Doku:** https://imagemagick.org/
- **Wand Doku:** https://docs.wand-py.org/
- **Download-Seite:** https://imagemagick.org/script/download.php

---

**Viel Erfolg!** 🚀
