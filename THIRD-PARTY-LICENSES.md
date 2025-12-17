# Third-Party Licenses

This document lists all open-source components used in the Taktische Zeichen Druckgenerator and their respective licenses.

---

## Overview

| Component | Version | License | Usage |
|-----------|---------|---------|-------|
| Python | 3.8+ | PSF License | Runtime Interpreter |
| PyQt6 | >=6.6.0 | GPL v3 | GUI Framework |
| Pillow | >=10.0.0 | HPND License | Image Processing |
| Wand | >=0.6.13 | MIT License | ImageMagick Python Wrapper |
| ReportLab | - | BSD-like | PDF Generation |
| openpyxl | >=3.1.0 | MIT License | Excel Import |
| ImageMagick | 7.x | Apache 2.0 | SVG Rendering (bundled) |
| PyInstaller | >=6.0.0 | GPL v2 with exception | Build Tool (not distributed) |

---

## Detailed License Information

### 1. Python (PSF License)

**License:** Python Software Foundation License
**Website:** https://www.python.org/
**License Text:** https://docs.python.org/3/license.html

Python is licensed under the PSF License, which is a permissive open-source license compatible with GPL v3.

---

### 2. PyQt6 (GPL v3)

**License:** GNU General Public License v3.0
**Website:** https://www.riverbankcomputing.com/software/pyqt/
**License Text:** https://www.gnu.org/licenses/gpl-3.0.html

PyQt6 is licensed under GPL v3, which requires the entire project to be licensed under GPL v3 as well.

**Important Note:** This is the primary reason why the entire project is GPL v3 licensed.

---

### 3. Pillow (HPND License)

**License:** Historical Permission Notice and Disclaimer (HPND)
**Website:** https://python-pillow.org/
**GitHub:** https://github.com/python-pillow/Pillow
**License Text:** https://github.com/python-pillow/Pillow/blob/main/LICENSE

Pillow is licensed under the HPND license, a permissive open-source license compatible with GPL v3.

---

### 4. Wand (MIT License)

**License:** MIT License
**Website:** https://docs.wand-py.org/
**GitHub:** https://github.com/emcconville/wand
**License Text:** https://github.com/emcconville/wand/blob/master/LICENSE

Wand is a Python wrapper for ImageMagick, licensed under the MIT License.

**MIT License Summary:**
- Permission is granted to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
- Compatible with GPL v3

---

### 5. ReportLab (BSD-like License)

**License:** BSD-like (ReportLab Open Source License)
**Website:** https://www.reportlab.com/opensource/
**GitHub:** https://github.com/MrBitBucket/reportlab-mirror
**License Text:** https://www.reportlab.com/docs/reportlab-userguide.pdf (Appendix A)

ReportLab is licensed under a BSD-style license, compatible with GPL v3.

---

### 6. openpyxl (MIT License)

**License:** MIT License
**Website:** https://openpyxl.readthedocs.io/
**GitHub:** https://github.com/theorchard/openpyxl
**License Text:** https://github.com/theorchard/openpyxl/blob/master/LICENCE.rst

openpyxl is licensed under the MIT License, compatible with GPL v3.

---

### 7. ImageMagick (Apache 2.0)

**License:** Apache License 2.0
**Website:** https://imagemagick.org/
**GitHub:** https://github.com/ImageMagick/ImageMagick
**License Text:** https://www.apache.org/licenses/LICENSE-2.0

ImageMagick is licensed under Apache 2.0, compatible with GPL v3.

**Important:** The portable ImageMagick distribution is bundled with this application in the `imagemagick/` directory.

**Attribution Requirements (Apache 2.0):**
- This product includes ImageMagick developed by ImageMagick Studio LLC
- Website: https://imagemagick.org/
- License: Apache 2.0

**ImageMagick Dependencies (bundled DLLs):**
The following libraries are bundled with ImageMagick:
- Cairo (LGPL/MPL)
- FreeType (FreeType License)
- libpng (PNG License)
- libjpeg-turbo (BSD-style)
- zlib (zlib License)
- Brotli (MIT)
- Harfbuzz (MIT)
- HEIF/HEIC (LGPL)

All bundled dependencies have licenses compatible with Apache 2.0 and GPL v3.

---

### 8. PyInstaller (GPL v2 with Runtime Exception)

**License:** GPL v2 with Runtime Exception
**Website:** https://www.pyinstaller.org/
**GitHub:** https://github.com/pyinstaller/pyinstaller
**License Text:** https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt

PyInstaller is used as a build tool and is NOT distributed with the final application. The runtime exception allows distribution of bundled applications under different licenses.

**Note:** PyInstaller is only used during the build process and does not affect the license of the final executable.

---

## License Compatibility

All third-party licenses used in this project are compatible with GPL v3:

| License Type | Compatible with GPL v3 | Notes |
|--------------|------------------------|-------|
| PSF License | Yes | Permissive |
| GPL v3 | Yes | Same license |
| HPND | Yes | Permissive |
| MIT | Yes | Permissive |
| BSD-like | Yes | Permissive |
| Apache 2.0 | Yes | Permissive, attribution required |
| GPL v2 (PyInstaller) | Yes | Build tool only, runtime exception |

---

## Attribution Requirements

### ImageMagick (Apache 2.0)

This product includes software developed by:
- **ImageMagick Studio LLC**
- Website: https://imagemagick.org/
- License: Apache License 2.0

---

## Full License Texts

For the full text of each license, please refer to:

- **GPL v3:** https://www.gnu.org/licenses/gpl-3.0.html
- **MIT License:** https://opensource.org/licenses/MIT
- **Apache 2.0:** https://www.apache.org/licenses/LICENSE-2.0
- **PSF License:** https://docs.python.org/3/license.html
- **HPND License:** https://opensource.org/licenses/HPND

---

## Contact

If you have questions about licensing or need clarification:

- **Author:** Ramon Hoffmann
- **Email:** Ramon-Hoffmann@gmx.de
- **Project:** Taktische Zeichen Druckgenerator
- **Repository:** https://github.com/Hopeman876/Taktische_Zeichen_Druckgenerator_Develop

---

**Last Updated:** 2025-12-01
