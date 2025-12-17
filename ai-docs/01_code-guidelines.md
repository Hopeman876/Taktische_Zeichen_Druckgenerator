# Code-Guidelines (ZWINGEND!)

**Version:** 2.0.0
**Aktualisiert:** 2025-12-03

---

## KRITISCHE REGELN

### 1. Formatierung
```python
# ✅ 4 Spaces (KEINE Tabs!)
def my_function():
    if condition:
        do_something()

# ✅ Max 100 Zeichen pro Zeile
# ✅ 2 Leerzeilen vor Klassen, 1 zwischen Methoden
```

### 2. ASCII-only in Code
```python
# ❌ VERBOTEN
button_text = "→ Weiter"       # Unicode-Pfeil
status = "✓ OK"                # Unicode-Häkchen
icon = "📁 Ordner"              # Emoji

# ✅ ERLAUBT
button_text = "-> Weiter"      # ASCII
status = "[OK]"                # ASCII
icon = "[Folder] Ordner"       # ASCII

# ✅ AUSNAHMEN
# Kommentare: Unicode OK
"""Docstrings: ö, ä, ü OK"""
UI_TEXTS = {"btn": "Größe"}    # UI-Texte OK
```

### 3. RuntimeConfig (KRITISCH!)
```python
# ❌ NIEMALS
from constants import DEFAULT_MODUS
modus = DEFAULT_MODUS

# ✅ IMMER
from runtime_config import get_config
modus = get_config().standard_modus

# ✅ OK (unveränderlich)
from constants import SYSTEM_POINTS_PER_INCH
```

**Konstanten-Arten:**
- `SYSTEM_*` = Unveränderlich → OK direkt nutzen
- `DEFAULT_*` = Überschreibbar → NUR via `get_config()`

### 4. Keine Magic Numbers
```python
# ❌ FALSCH
if size > 150:
    do_something()

# ✅ RICHTIG
from constants import ZEICHEN_SIZE_THRESHOLD_LARGE_MM
if size > ZEICHEN_SIZE_THRESHOLD_LARGE_MM:
    do_something()
```

### 5. Logging statt print()
```python
# ❌ FALSCH
print("Datei gespeichert")
print(f"Fehler: {error}")

# ✅ RICHTIG
from logging_manager import LoggingManager
logger = LoggingManager().get_logger(__name__)
logger.info("Datei gespeichert")
logger.error(f"Fehler: {error}")
```

---

## Naming Conventions

### Variablen & Funktionen
```python
# snake_case
project_name = "Test"
def calculate_total(): pass
def _internal_helper(): pass  # Private: führender _

# Konstanten: UPPER_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

### Klassen
```python
# PascalCase
class ProjectManager: pass
class ConfigDialog: pass

@dataclass
class ProjectInfo: pass
```

### Module/Dateien
```python
# snake_case
config_manager.py
new_project_dialog.py
txt_exporter.py
```

### Qt Widgets (Naming-Schema)
```python
# Prefix je nach Widget-Typ:
btn_export       # QPushButton
lbl_status       # QLabel
spin_width       # QSpinBox
combo_mode       # QComboBox
check_enabled    # QCheckBox
txt_name         # QLineEdit
tree_items       # QTreeWidget
```

---

## Docstrings (Google-Style)

### Funktionen
```python
def calculate(value: float, factor: int = 2) -> float:
    """
    Berechnet Wert mit Faktor

    Args:
        value: Eingabewert
        factor: Multiplikator (default: 2)

    Returns:
        Berechnetes Ergebnis

    Raises:
        ValueError: Wenn value negativ
    """
    if value < 0:
        raise ValueError("value muss positiv sein")
    return value * factor
```

### Klassen
```python
class ConfigManager:
    """
    Verwaltet Konfiguration

    Attributes:
        config_path: Pfad zur Config-Datei
        settings: Dict mit Einstellungen
    """

    def __init__(self, path: Path):
        """Initialisiert Manager mit Pfad"""
        self.config_path = path
```

---

## Type Hints (IMMER verwenden!)

```python
from typing import Optional, List, Dict, Tuple
from pathlib import Path

# Funktionen
def process(file: Path, lines: int = 100) -> Optional[str]:
    pass

# Variablen (optional aber empfohlen)
name: str = "Test"
items: List[str] = []
config: Dict[str, Any] = {}

# Optional für None-Werte
def find_user(name: str) -> Optional[User]:
    return user or None

# Tuple für multiple Returns
def get_info() -> Tuple[bool, str]:
    return True, "Success"
```

---

## Imports (Reihenfolge)

```python
# 1. Standard Library
import os
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# 2. Third-Party
from PyQt6.QtWidgets import QWidget
from PIL import Image

# 3. Eigene Module
from constants import (
    DEFAULT_DPI,
    SYSTEM_POINTS_PER_INCH
)
from runtime_config import get_config
from logging_manager import LoggingManager
```

---

## Error Handling

```python
# ✅ Spezifische Exceptions
try:
    with open(path, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    logger.error(f"File not found: {path}")
    return None
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected: {e}")
    raise

# ❌ Bare except!
try:
    do_something()
except:  # NIEMALS!
    pass
```

---

## Klassen-Struktur

```python
class MyClass:
    """Docstring"""

    # 1. Class Variables
    class_var: str = "value"

    # 2. __init__
    def __init__(self, param: str):
        self.param = param
        self.logger = LoggingManager().get_logger(__name__)

    # 3. Public Methods
    def public_method(self) -> bool:
        """Öffentliche Methode"""
        return self._private_helper()

    # 4. Private Methods
    def _private_helper(self) -> bool:
        """Private Helper"""
        return True

    # 5. Properties
    @property
    def status(self) -> str:
        return self._status

    # 6. Static Methods
    @staticmethod
    def utility_function() -> str:
        return "static"
```

---

## Code-Änderungen markieren

```python
def example_method(self):
    """Docstring"""
    unchanged_line_1()

    # NEW: Diese Zeile hinzugefügt
    new_functionality()

    # CHANGED: Von old_function() zu new_function()
    new_function()

    # REMOVED: Diese Zeile entfernt
    # old_deprecated_line()

    unchanged_line_2()
```

**Kommentar-Präfixe:**
- `# NEW:` - Neue Zeile
- `# CHANGED:` - Modifizierte Zeile
- `# REMOVED:` - Gelöschte Zeile
- `# TODO:` - Noch zu implementieren
- `# FIXME:` - Bekannter Bug
- `# NOTE:` - Wichtiger Hinweis

---

## Logging-Levels

```python
from logging_manager import LoggingManager
logger = LoggingManager().get_logger(__name__)

# DEBUG: Entwickler-Info (default: ausgeblendet)
logger.debug("Variable x = 42")

# INFO: Normaler Programmablauf
logger.info("Export gestartet")

# WARNING: Unerwartete Situation, aber OK
logger.warning("Font nicht gefunden, nutze Fallback")

# ERROR: Fehler, aber Programm läuft weiter
logger.error(f"Export fehlgeschlagen: {e}")

# CRITICAL: Schwerer Fehler, Programm stoppt
logger.critical("Datenbank nicht erreichbar")
```

---

## Qt Designer Integration

**Statische UI → Qt Designer (.ui-Dateien)**
- Fenster, Dialoge, Layouts
- Buttons, Labels, SpinBoxes
- In `gui/ui_files/*.ui`

**Dynamische Inhalte → Python**
```python
from gui.ui_loader import load_ui

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Lädt main_window.ui
        self.ui = load_ui('main_window.ui', self)

        # Dynamisch befüllen
        self.ui.combo_modus.addItems(MODI_NAMEN)
        self.ui.tree_zeichen.addTopLevelItem(item)
```

---

## Constants Organization

**In constants.py:**
```python
# SYSTEM_* - Unveränderlich
SYSTEM_POINTS_PER_INCH = 72
SYSTEM_LOG_FORMAT = "%(asctime)s - %(message)s"

# DEFAULT_* - Überschreibbar (Factory Defaults)
DEFAULT_DPI = 300
DEFAULT_FONT_SIZE = 10
DEFAULT_MODUS = "freitext"

# Berechnungs-Funktionen
def mm_to_pixels(mm: float, dpi: int) -> int:
    return int((mm / 25.4) * dpi)
```

**Neue DEFAULT_* Konstante hinzufügen:**
1. In `constants.py` definieren
2. In `runtime_config.py` integrieren (`_load_factory_defaults`, `load_from_settings`, `save_to_settings`)
3. In `validation_manager.py` validieren

Details: `04_RuntimeConfig-Guidelines.md`

---

## Neue Konstanten (v0.8.2)

```python
# A4-Dimensionen (DIN-Standard)
DIN_A4_WIDTH_MM = 210.0   # Portrait width / Landscape height
DIN_A4_HEIGHT_MM = 297.0  # Portrait height / Landscape width

# Größen-Schwellwerte für Memory-Management
ZEICHEN_SIZE_THRESHOLD_VERY_LARGE_MM = 150.0  # > 150mm
ZEICHEN_SIZE_THRESHOLD_LARGE_MM = 100.0       # > 100mm

# Text-Messung
TEMP_IMAGE_SIZE_PX = 1000  # Temp-Image für präzise Textmessungen
```

---

## Testing

```python
# Unit-Tests am Ende der Datei (bei Bedarf)
if __name__ == "__main__":
    # Test 1: Konvertierung
    pixels = mm_to_pixels(45.0, 600)
    assert pixels == 1063, f"Expected 1063, got {pixels}"

    # Test 2: Funktionalität
    result = calculate(10.0, 2)
    assert result == 20.0

    print("All tests passed!")
```

---

## Checkliste vor Commit

- [ ] 4 Spaces Einrückung (keine Tabs)
- [ ] ASCII-only in Code-Strings
- [ ] RuntimeConfig für `DEFAULT_*` verwendet
- [ ] Keine Magic Numbers
- [ ] Logging statt print()
- [ ] Type-Hints vorhanden
- [ ] Google-Style Docstrings
- [ ] Imports korrekt sortiert
- [ ] Spezifische Exceptions (kein bare except)
- [ ] Qt Widget Naming-Schema eingehalten

---

**Siehe auch:**
- `04_RuntimeConfig-Guidelines.md` - RuntimeConfig Details
- `02_GUI-Struktur.md` - Qt Designer Workflow
- `03_general-guidelines.md` - Git, Versionierung
