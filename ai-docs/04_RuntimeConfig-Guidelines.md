# RuntimeConfig-Guidelines - VERPFLICHTEND für KI

**Version:** 1.0.0
**Datum:** 2025-11-04
**Status:** 🔴 VERPFLICHTEND

---

## ⚠️ KRITISCH: Diese Regeln MÜSSEN eingehalten werden!

Diese Guidelines sind **verpflichtend** für alle KI-Assistenten, die an diesem Projekt arbeiten.

---

## 🏛️ Regel 1: Konstanten-Kategorisierung

### Es gibt nur 2 Arten von Konstanten:

1. **SYSTEM_\*** = Unveränderliche technische Konstanten
   - **NIEMALS** zur Laufzeit ändern
   - **NIEMALS** vom User konfigurierbar
   - Beispiele: `SYSTEM_POINTS_PER_INCH = 72`, `SYSTEM_LOG_FORMAT`

2. **DEFAULT_\*** = Factory Defaults (überschreibbar)
   - **KÖNNEN** zur Laufzeit geändert werden
   - **KÖNNEN** vom User in settings.json gespeichert werden
   - Beispiele: `DEFAULT_MODUS`, `DEFAULT_FONT_SIZE`, `DEFAULT_DPI`

### Verwendung:

```python
# ❌ FALSCH: from constants import DEFAULT_MODUS; modus = DEFAULT_MODUS
# ✅ RICHTIG: from runtime_config import get_config; modus = get_config().standard_modus
# ✅ OK: from constants import SYSTEM_POINTS_PER_INCH  # Unveränderlich
```

---

## 🔧 Regel 2: Neue Konstanten hinzufügen

### Schritt 1: In constants.py

```python
# Als DEFAULT_* wenn User es ändern können soll
DEFAULT_NEUE_EINSTELLUNG = "wert"

# Als SYSTEM_* wenn es NIEMALS geändert werden darf
SYSTEM_NEUE_KONSTANTE = 123
```

### Schritt 2: Falls DEFAULT_*, in runtime_config.py

```python
class RuntimeConfig:
    def _load_factory_defaults(self):
        # ...
        self.neue_einstellung: type = DEFAULT_NEUE_EINSTELLUNG

    def load_from_settings(self, settings):
        # ...
        self.neue_einstellung = getattr(z, 'neue_einstellung', self.neue_einstellung)

    def save_to_settings(self, settings):
        # ...
        settings.zeichen.neue_einstellung = self.neue_einstellung

    def to_dict(self) -> dict:
        return {
            # ...
            'neue_einstellung': self.neue_einstellung
        }
```

### Schritt 3: Validierung hinzufügen

```python
# In validation_manager.py - RuntimeConfigValidator

def validate_setting(self, key: str, value) -> Tuple[bool, Optional[str]]:
    validators = {
        # ...
        'neue_einstellung': self._validate_neue_einstellung
    }

def _validate_neue_einstellung(self, value: type) -> Tuple[bool, Optional[str]]:
    """Validiert neue_einstellung"""
    # Range-Check, Type-Check, etc.
    if not isinstance(value, type):
        return False, "Muss type sein"

    if value < min or value > max:
        return False, f"Muss zwischen {min} und {max} liegen"

    return True, None
```

---

## 📦 Regel 3: Dataclass Defaults

### ❌ FALSCH: Hardcodierte Defaults

```python
@dataclass
class ZeichenConfig:
    modus: str = "freitext"  # BAD: Hardcodiert!
    font_size: int = 8        # BAD: Ignoriert User-Settings
```

### ✅ RICHTIG: RuntimeConfig nutzen

**Option A: __post_init__**

```python
from runtime_config import get_config

@dataclass
class ZeichenConfig:
    modus: str = None
    font_size: int = None

    def __post_init__(self):
        config = get_config()

        if self.modus is None:
            self.modus = config.standard_modus

        if self.font_size is None:
            self.font_size = config.font_size
```

**Option B: Factory-Method (EMPFOHLEN)**

```python
from runtime_config import get_config

@dataclass
class ZeichenConfig:
    zeichen_id: str
    svg_path: Path
    modus: str
    font_size: int
    dpi: int
    # ... weitere Felder

    @classmethod
    def create_from_defaults(cls, zeichen_id: str, svg_path: Path, **kwargs):
        """
        Factory-Method: Erstellt ZeichenConfig mit RuntimeConfig-Defaults

        Args:
            zeichen_id: Zeichen-ID
            svg_path: SVG-Pfad
            **kwargs: Überschreibungen (optional)

        Returns:
            ZeichenConfig mit Defaults aus RuntimeConfig
        """
        config = get_config()

        # Defaults aus RuntimeConfig
        defaults = {
            'modus': config.standard_modus,
            'font_size': config.font_size,
            'dpi': config.dpi,
            'zeichen_hoehe_mm': config.zeichen_hoehe_mm,
            'zeichen_breite_mm': config.zeichen_breite_mm,
            'abstand_rand_mm': config.abstand_rand_mm,
            # ...
        }

        # Überschreibe mit kwargs
        defaults.update(kwargs)

        return cls(
            zeichen_id=zeichen_id,
            svg_path=svg_path,
            **defaults
        )
```

---

## 🎯 Regel 4: Code-Review-Checkliste

### Vor jedem Code-Commit prüfen:

- [ ] Werden `DEFAULT_*` Konstanten direkt verwendet? → ❌ Ändern zu RuntimeConfig
- [ ] Werden neue `DEFAULT_*` Konstanten hinzugefügt? → ✅ In RuntimeConfig integrieren
- [ ] Werden Dataclass-Defaults hardcodiert? → ❌ Auf RuntimeConfig umstellen
- [ ] Wird Validierung benötigt? → ✅ In RuntimeConfigValidator hinzufügen
- [ ] Sind alle SYSTEM_* vs. DEFAULT_* korrekt kategorisiert? → ✅ Prüfen

---

## 📊 Quick-Reference

### Verwendung in verschiedenen Kontexten

| Kontext | Richtige Verwendung |
|---------|-------------------|
| **Neue Konstante** | `DEFAULT_*` in constants.py, dann in RuntimeConfig |
| **Default in Dataclass** | Factory-Method mit get_config() |
| **Validierung** | RuntimeConfigValidator erweitern |
| **GUI-Änderung** | RuntimeConfig updaten, dann save_settings() |
| **Programm-Start** | init_runtime_config(settings) aufrufen |

### API-Übersicht

```python
from runtime_config import get_config
config = get_config()
modus = config.standard_modus       # Lesen
config.set('font_size', 10)         # Ändern (mit Validierung)
all_values = config.to_dict()       # Exportieren
```

---

## 🚨 Häufige Fehler vermeiden

### Fehler 1: DEFAULT_* direkt nutzen

```python
# ❌ FALSCH
from constants import DEFAULT_MODUS
config = ZeichenConfig(modus=DEFAULT_MODUS)

# ✅ RICHTIG
config = ZeichenConfig.create_from_defaults(...)
```

### Fehler 2: Hardcodierte Defaults

```python
# ❌ FALSCH
@dataclass
class Foo:
    size: int = 8  # Hardcodiert

# ✅ RICHTIG
@dataclass
class Foo:
    size: int = None

    def __post_init__(self):
        if self.size is None:
            self.size = get_config().font_size
```

### Fehler 3: Keine Validierung

```python
# ❌ FALSCH
config.dpi = 9999  # Kein Check!

# ✅ RICHTIG
config.set('dpi', 9999)  # ValueError bei ungültigem Wert
```

---

## 📚 Siehe auch

- [RuntimeConfig_System.md](RuntimeConfig_System.md) - Vollständige Dokumentation
- [01_code-guidelines.md](01_code-guidelines.md) - Code-Richtlinien
- [constants.py](../constants.py) - Alle Konstanten
- [runtime_config.py](../runtime_config.py) - Implementierung
- [validation_manager.py](../validation_manager.py) - Validierung

---

**WICHTIG:** Diese Regeln sind **verpflichtend** und **MÜSSEN** von allen KI-Assistenten eingehalten werden!

**Lese als naechstes:** `ai-docs/AKTUELL_Projektstand_*.md` (aktuellen Projektstand)

Dort findest du:
- Was wurde bereits implementiert?
- Welche Features sind offen?
- Bekannte Issues
- Naechste geplante Schritte
