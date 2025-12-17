# CLAUDE.md - AI Assistant Guide for Taktische Zeichen Druckgenerator

**Project Version:** v0.8.5
**Last Updated:** 2025-12-16
**Status:** Production-Ready

---

## 🎯 Quick Start for AI Assistants

### 1. Read This First
This file provides a **high-level overview** and **critical rules** for working on this project.

### 2. Deep Dive Documentation
All detailed guidelines are in the `ai-docs/` directory. **MUST READ** before coding:

**Recommended Reading Order:**
1. **ai-docs/00_LESE_MICH_ZUERST.md** - Documentation map and navigation
2. **ai-docs/00_Projektbeschreibung.md** - Project overview and requirements
3. **ai-docs/01_code-guidelines.md** - Code conventions (MANDATORY!)
4. **ai-docs/02_GUI-Struktur.md** - GUI architecture and patterns
5. **ai-docs/03_general-guidelines.md** - General development practices
6. **ai-docs/04_RuntimeConfig-Guidelines.md** - RuntimeConfig system (CRITICAL!)

### 3. Current Status
- **Latest Release:** v0.8.5 (2025-12-16)
- **See:** `release_notes/RELEASE_NOTES_v0.8.5.md` for recent changes
- **Major Features:** PDF-Schnittbogen layout consistency, improved cut line label positioning

---

## 📚 Project Overview

### What is this project?
A professional Windows application for preparing tactical signs (SVG graphics) for printing with customizable text overlays and export options.

### Tech Stack
- **Language:** Python 3.8+
- **GUI:** PyQt6 with Qt Designer (.ui files)
- **SVG Rendering:** ImageMagick/Wand
- **PDF Export:** ReportLab
- **Build:** PyInstaller (portable .exe)

### Key Features
- 7 different text modes (OV+Strength, Location, Callsign, Freetext, etc.)
- Batch processing with Excel/CSV import
- Multi-format export (PNG, JPG, SVG, PDF)
- Professional print preparation (CMYK, 300+ DPI, bleed areas)
- Dynamic sign dimensions (not hardcoded)
- Cutting sheets for A4 printing

---

## 🔴 CRITICAL RULES - MUST FOLLOW

### Code Formatting
- ✅ **4 Spaces indentation** (NO tabs)
- ✅ **ASCII-only in code strings** (no →, ✓, 📁 symbols)
- ✅ **No magic numbers** - centralize in constants.py
- ✅ **Type-hints required** for all functions/methods
- ✅ **Google-Style docstrings**
- ✅ **LoggingManager instead of print()**

### RuntimeConfig System (CRITICAL!)
- ✅ **NEVER use `DEFAULT_*` constants directly** from constants.py
- ✅ **ALWAYS use `get_config()`** to access runtime values
- ✅ **Two types of constants:**
  - `SYSTEM_*` = Immutable technical constants (OK to use directly)
  - `DEFAULT_*` = Factory defaults (MUST use via RuntimeConfig)

**Example:**
```python
# ❌ WRONG
from constants import DEFAULT_MODUS
modus = DEFAULT_MODUS

# ✅ CORRECT
from runtime_config import get_config
modus = get_config().standard_modus
```

### GUI Development
- ✅ **Qt Designer for static UI elements** (.ui files in `gui/ui_files/`)
- ✅ **Dynamic elements in separate configs** (e.g., modus_config.py)
- ✅ **Single Source of Truth:** modus_config.py for mode definitions

### Git Workflow
- ✅ **NO automatic commits!** Only commit when user explicitly requests it
- ✅ **Commit messages:** Follow Google Style (imperative mood)
- ✅ **Branch:** Work on claude/* branches as specified
- ✅ **Push with retry logic** (up to 4 retries with exponential backoff)

---

## 📁 Project Structure

```
Taktische_Zeichen_Druckgenerator/
│
├── CLAUDE.md                          # This file - AI assistant guide
├── BUILD_ANLEITUNG.md                 # Build instructions
├── README_BETA.md                     # User documentation
├── TaktischeZeichenDruckgenerator.spec # PyInstaller config
│
├── ai-docs/                           # 🔴 MANDATORY AI documentation
│   ├── 00_LESE_MICH_ZUERST.md        # Documentation index
│   ├── 00_Projektbeschreibung.md     # Project description
│   ├── 01_code-guidelines.md         # Code conventions (MANDATORY)
│   ├── 02_GUI-Struktur.md            # GUI architecture
│   ├── 03_general-guidelines.md      # General practices
│   ├── 04_RuntimeConfig-Guidelines.md # RuntimeConfig system (CRITICAL)
│   └── Geplante_Features/            # Future features (IGNORE)
│
├── gui/                               # GUI modules (PyQt6)
│   ├── main_window.py                 # Main application window
│   ├── modus_config.py                # Mode definitions (Single Source of Truth)
│   ├── ui_loader.py                   # .ui file loader
│   ├── ui_files/                      # Qt Designer .ui files
│   ├── dialogs/                       # Dialog windows
│   │   ├── export_dialog.py
│   │   ├── settings_dialog.py
│   │   ├── modus_*_dialog.py         # Mode-specific dialogs
│   └── widgets/                       # Custom widgets
│       ├── svg_preview_widget.py
│       └── zeichen_tree_item.py
│
├── Core Python Modules:
├── main.py                            # Application entry point
├── constants.py                       # Central constants (47KB - LARGE!)
├── runtime_config.py                  # Runtime configuration system
├── settings_manager.py                # Settings persistence (settings.json)
├── validation_manager.py              # Input validation + RuntimeConfig validator
├── logging_manager.py                 # Logging system
│
├── Generator Modules:
├── taktische_zeichen_generator.py    # Core generator (59KB)
├── text_overlay.py                    # Text overlay logic (35KB)
├── print_preparer.py                  # Print preparation
├── pdf_exporter.py                    # PDF export (40KB)
├── svg_loader_local.py                # SVG loading and processing
├── font_manager.py                    # Font management
│
├── Resources:
├── resources/                         # Logo, icons
├── imagemagick/                       # ImageMagick portable (bundled)
│
├── Build & Release:
├── build_exe.bat                      # Automated build script
├── releases/                          # Release builds (generated)
├── release_notes/                     # Version release notes
│
├── Development Tools:
├── dev-tools/                         # Testing, profiling, analysis tools
│   ├── testing/                       # Test scripts
│   ├── svg-analysis/                  # SVG analysis tools
│   └── profiling/                     # Performance profiling
│
├── Documentation:
├── docs/                              # Additional documentation
│   ├── imagemagick_setup.md
│   ├── Test-Routinen_Anleitung.md
│   └── Ungenutzte_Programmbestandteile_Bericht.md
│
└── User-documentation/                # End-user documentation

# NOT in Git (created at runtime):
├── Taktische_Zeichen_Grafikvorlagen/  # SVG source files (user-provided)
├── Taktische_Zeichen_Ausgabe/         # Export output
├── Logs/                              # Log files
└── settings.json                      # User settings (auto-generated)
```

---

## 🔧 Development Workflows

### Adding a New Feature

1. **Research Phase:**
   - Read relevant ai-docs files
   - Search codebase for similar patterns
   - Check RuntimeConfig for related settings

2. **Implementation:**
   - Follow code-guidelines.md strictly
   - Use RuntimeConfig for any configurable values
   - Add logging at important points
   - Write docstrings (Google Style)
   - Add type-hints

3. **Testing:**
   - Test manually in GUI
   - Check dev-tools/testing/ for test routines
   - Verify settings persistence (settings.json)

4. **Documentation:**
   - Update relevant ai-docs if needed
   - Add comments for complex logic
   - Update RELEASE_NOTES if applicable

### Modifying Constants

**If adding/changing a `DEFAULT_*` constant:**

1. Add to `constants.py`:
   ```python
   DEFAULT_NEW_SETTING = "value"
   ```

2. Integrate into `runtime_config.py`:
   ```python
   class RuntimeConfig:
       def _load_factory_defaults(self):
           self.new_setting = DEFAULT_NEW_SETTING

       def load_from_settings(self, settings):
           self.new_setting = getattr(settings.category, 'new_setting', self.new_setting)

       def save_to_settings(self, settings):
           settings.category.new_setting = self.new_setting
   ```

3. Add validation in `validation_manager.py`:
   ```python
   def _validate_new_setting(self, value) -> Tuple[bool, Optional[str]]:
       # Validation logic
       return True, None
   ```

### GUI Changes

**For static UI elements:**
1. Open `gui/ui_files/*.ui` in Qt Designer
2. Make visual changes
3. Save .ui file
4. Python code loads via ui_loader.py automatically

**For dynamic elements:**
1. Modify relevant Python file (e.g., modus_config.py for modes)
2. Follow naming conventions (widgets: lbl_, spin_, combo_, btn_)
3. Connect signals/slots in Python code

### Git Commit Process

**ONLY commit when user explicitly requests!**

When requested:
1. Run `git status` and `git diff` to review changes
2. Stage files: `git add <files>`
3. Commit with meaningful message:
   ```bash
   git commit -m "$(cat <<'EOF'
   Type: Brief description

   Detailed explanation if needed.
   EOF
   )"
   ```
4. Push with retry logic (see Git Development Branch Requirements)

---

## 🧪 Testing

### Manual Testing
- Start application: `python main.py`
- Test changed features in GUI
- Check Logs/ for errors
- Verify settings.json persistence

### Unit Tests
Located in `dev-tools/testing/`:
- `test_constants.py` - Constants validation
- `test_runtime_config.py` - RuntimeConfig system
- See `docs/Test-Routinen_Anleitung.md` for usage

**Run tests:**
```bash
python -m pytest dev-tools/testing/
```

### Integration Testing
- Load SVG files
- Export to all formats (PNG, JPG, SVG, PDF)
- Test batch processing
- Verify cutting sheets (Schnittbögen)

---

## 📦 Building Release

### Quick Build
```bash
build_exe.bat
```

**What it does:**
1. Reads version from constants.py
2. Builds executable with PyInstaller
3. Copies resources, UI files, ImageMagick
4. Creates versioned release folder
5. Creates ZIP archive in `releases/`

**Output:** `releases/TaktischeZeichenDruckgenerator_v0.8.0.zip`

### Before Building
- [ ] Update `PROGRAM_VERSION` in constants.py
- [ ] Create `release_notes/RELEASE_NOTES_v{VERSION}.md`
- [ ] Test all features manually
- [ ] Commit all changes

### After Building
- [ ] Test .exe from releases/ folder
- [ ] Create Git tag: `git tag v{VERSION}`
- [ ] Push tag: `git push origin v{VERSION}`

See `BUILD_ANLEITUNG.md` for detailed instructions.

---

## 📊 Key Modules Overview

### constants.py (47KB)
Central repository for all constants. Contains:
- `SYSTEM_*` - Immutable technical constants
- `DEFAULT_*` - Factory defaults (use via RuntimeConfig!)
- Calculation functions for print dimensions
- UI text constants

### runtime_config.py
Singleton pattern for runtime configuration:
- Loads defaults from constants.py
- Merges with user settings (settings.json)
- Provides validation via RuntimeConfigValidator
- Persists changes back to settings.json

**Always use:** `get_config()` to access current values

### taktische_zeichen_generator.py (59KB)
Core generator logic:
- Batch processing with threading
- SVG loading and composition
- Text overlay integration
- Export orchestration
- Progress callbacks

### pdf_exporter.py (40KB)
PDF generation with streaming:
- Single sign PDFs
- Cutting sheets (Schnittbögen) on A4
- CMYK color space (ISO Coated v2)
- PDF/X-1a:2001 standard
- Memory-efficient streaming (v0.8.0+)

### gui/main_window.py (109KB - LARGE!)
Main application window:
- v0.8.0: Complete redesign with GroupBoxes
- SVG tree with categories
- Live preview
- Mode selection and configuration
- Settings integration

### settings_manager.py
Handles settings.json persistence:
- Load/save settings
- Merge with defaults
- Backup on changes
- Type conversion

---

## 🐛 Common Issues & Solutions

### Issue: "DEFAULT_* not found" error
**Cause:** Trying to use constant that was moved to RuntimeConfig
**Solution:** Use `get_config().setting_name` instead

### Issue: Settings not persisting
**Cause:** Not calling settings_manager.save_settings()
**Solution:** Always save after RuntimeConfig changes:
```python
config = get_config()
config.set('key', value)
settings_manager.save_settings()
```

### Issue: GUI changes not appearing
**Cause:** .ui file not reloaded or Qt Designer not saved
**Solution:**
1. Save in Qt Designer
2. Restart application
3. Check ui_loader.py for correct .ui file path

### Issue: Build fails with PyInstaller
**Cause:** Missing dependencies or .spec file issues
**Solution:**
1. Install all requirements: `pip install -r requirements.txt`
2. Clean build: `pyinstaller --clean TaktischeZeichenDruckgenerator.spec`
3. Check BUILD_ANLEITUNG.md troubleshooting section

---

## 📝 Recent Changes (v0.8.5)

**Critical Bugfixes:**
- ✅ **PDF-Schnittbogen layout now consistent** - Layout identical with/without cut lines
- ✅ **Grid always based on final sign size** - No more layout changes when enabling cut lines
- ✅ **Always crop to final size** - Red bleed line correctly cropped off
- ✅ **Cut line labels repositioned** - Labels now closer to their respective lines

**Technical Improvements:**
- ✅ Simplified PDF export logic (-29 lines of code)
- ✅ Consistent behavior for all schnittbogen exports
- ✅ Better visual hierarchy for cut line labels

**User Impact:**
- Same number of signs fit on A4 page regardless of cut line setting
- Red bleed line (Beschnittzugabe) correctly cropped off in schnittbogen
- Blue and green cut lines visible inside final sign area
- Clearer label positioning for cut lines

See `release_notes/RELEASE_NOTES_v0.8.5.md` for complete details.

---

## 🚀 Performance Considerations

### Memory Management
- PDF export uses streaming (not in-memory accumulation)
- PNG copies use file operations (not image rendering)
- Dynamic batch sizes for large signs
- Frequent garbage collection for large signs

### Threading
- Batch processing uses ThreadPoolExecutor
- Thread count reduced for large signs (stability)
- Progress callbacks on main thread (GUI safety)

### Optimization Tips
- Use RuntimeConfig values (cached, not re-calculated)
- Avoid creating unnecessary QPixmap objects
- Close file handles promptly with `with` statements
- Log at appropriate levels (DEBUG vs INFO)

---

## 🔮 Future Development

### Planned Features (ai-docs/Geplante_Features/)
- Enhanced layout preview
- Additional export formats
- Batch editing capabilities
- Template system

**Note:** Ignore Geplante_Features/ during normal development unless specifically working on planned features.

---

## 📚 Additional Resources

### Documentation Files
- `ai-docs/00_LESE_MICH_ZUERST.md` - Documentation navigation guide
- `docs/imagemagick_setup.md` - ImageMagick configuration
- `docs/Test-Routinen_Anleitung.md` - Testing procedures
- `README_BETA.md` - User-facing documentation

### Important Code Files
- `gui/modus_config.py` - **Single Source of Truth** for modes
- `constants.py` - All constants and calculations
- `runtime_config.py` - Runtime configuration system

---

## ⚠️ Final Reminders for AI Assistants

1. **READ ai-docs/** before making any code changes
2. **NEVER use `DEFAULT_*` directly** - always use `get_config()`
3. **NO automatic commits** - only when user explicitly requests
4. **4 spaces, ASCII-only, type-hints, docstrings** - non-negotiable
5. **Qt Designer for static UI** - don't hardcode GUI layouts
6. **Log instead of print** - use LoggingManager
7. **Validate all inputs** - use validation_manager.py
8. **Test before committing** - manual testing minimum

---

## 🆘 Getting Help

### For AI Assistants
1. Check this CLAUDE.md
2. Read relevant ai-docs/ files
3. Search codebase for similar patterns
4. Review recent commits for context

### For Users
- See `README_BETA.md` for user documentation
- Check `release_notes/` for version-specific info
- Review `docs/` for technical setup guides

---

**Project Repository:** https://github.com/Hopeman876/Taktische_Zeichen_Druckgenerator_Develop
**Last Updated:** 2025-11-16 (v0.8.0 Release)
**Maintained by:** AI-assisted development with human oversight

---

## 📋 Quick Reference Checklist

Before starting work:
- [ ] Read CLAUDE.md (this file)
- [ ] Read ai-docs/00_LESE_MICH_ZUERST.md
- [ ] Read ai-docs/01_code-guidelines.md
- [ ] Read ai-docs/04_RuntimeConfig-Guidelines.md
- [ ] Understand the current branch strategy

During development:
- [ ] Follow all CRITICAL RULES above
- [ ] Use RuntimeConfig for all configurable values
- [ ] Add logging at important points
- [ ] Write docstrings and type-hints
- [ ] Test changes manually

Before committing:
- [ ] Review all changed files
- [ ] Verify no `DEFAULT_*` used directly
- [ ] Check code follows guidelines
- [ ] Test in GUI
- [ ] User explicitly requested commit

---

**End of CLAUDE.md**
