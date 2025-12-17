# Development Tools

Dieser Ordner enthält Entwicklungs- und Debugging-Tools, die **nicht** zum Hauptprogramm gehören.

## 📁 Struktur

### `testing/`
Isolierte Test-Skripte für spezifische Features:
- `test_cut_lines.py` - Standalone-Test für Schneidelinien (PIL-Drawing)

### `svg-analysis/`
Analyse- und Debug-Tools für SVG-Dateien:
- `svg_analyzer.py` - SVG-Analyse & Reparatur-Tool (Encoding, XML-Struktur)
- `find_pseudo_svgs.py` - Scanner für Pseudo-SVGs (eingebettete PNGs)

### `setup/`
Setup- und Installations-Tools:
- `verify_version.py` - Version-Checker

### `profiling/`
Performance-Analyse:
- `profile_performance.py` - Performance-Profiling-Tool

## ℹ️ Hinweise

- **Diese Tools sind NICHT für den Produktivbetrieb gedacht**
- Einige Tools nutzen veraltete Imports oder Coding-Styles
- Tools können hardcoded Pfade enthalten
- Für Produktiv-Code siehe Hauptverzeichnis

## 🔧 Verwendung

Die meisten Tools können direkt ausgeführt werden:

```bash
python dev-tools/testing/test_cut_lines.py
python dev-tools/svg-analysis/svg_analyzer.py
```

Einige Tools benötigen möglicherweise Anpassungen (Pfade, Parameter).
