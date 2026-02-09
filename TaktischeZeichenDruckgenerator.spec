# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

is_windows = sys.platform == 'win32'

# Plattformabhaengige Daten
datas_list = [
    ('gui/ui_files/*.ui', 'gui/ui_files'),  # UI-Dateien einbinden
    ('resources', 'resources'),  # Logo und Icon einbinden
]
if is_windows and os.path.isdir('imagemagick'):
    datas_list.append(('imagemagick', 'imagemagick'))  # ImageMagick portable (nur Windows)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'wand',
        'wand.image',
        # ReportLab PDF-Generierung (v0.8.4)
        # CRITICAL: Diese Module werden dynamisch importiert und müssen explizit angegeben werden
        'reportlab',
        'reportlab.rl_config',
        'reportlab.pdfgen',
        'reportlab.pdfgen.canvas',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'reportlab.lib.utils',
        'reportlab.lib.colors',
        'reportlab.pdfbase',
        'reportlab.pdfbase.pdfdoc',
        'reportlab.pdfbase._fontdata',
        'reportlab.pdfbase._fontdata_enc_winansi',
        'reportlab.pdfbase._fontdata_enc_macroman',
        'reportlab.pdfbase._fontdata_enc_standard',
        'reportlab.pdfbase._fontdata_enc_symbol',
        'reportlab.pdfbase._fontdata_enc_zapfdingbats',
        'reportlab.pdfbase._fontdata_widths_courierboldoblique',
        'reportlab.pdfbase._fontdata_widths_courierbold',
        'reportlab.pdfbase._fontdata_widths_courieroblique',
        'reportlab.pdfbase._fontdata_widths_courier',
        'reportlab.pdfbase._fontdata_widths_helveticaboldoblique',
        'reportlab.pdfbase._fontdata_widths_helveticabold',
        'reportlab.pdfbase._fontdata_widths_helveticaoblique',
        'reportlab.pdfbase._fontdata_widths_helvetica',
        'reportlab.pdfbase._fontdata_widths_timesromanbi',
        'reportlab.pdfbase._fontdata_widths_timesromanbold',
        'reportlab.pdfbase._fontdata_widths_timesromanitalic',
        'reportlab.pdfbase._fontdata_widths_timesroman',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.pdfbase.ttfonts',
        'reportlab.pdfbase._cidfontdata',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # CHANGED: Nicht benötigte Module ausschließen (spart ~30-50 MB)
        'numpy',           # Nicht verwendet
        'pandas',          # Nicht verwendet
        'matplotlib',      # Nicht verwendet
        'scipy',           # Nicht verwendet
        'tkinter',         # Nicht verwendet (wir nutzen PyQt6)
        '_tkinter',        # Tkinter Backend

        # PyQt6 Module (nicht benötigt)
        'PyQt6.QtNetwork', # Nicht verwendet (nur wenn Netzwerk benötigt)
        'PyQt6.QtBluetooth',
        'PyQt6.QtDBus',
        'PyQt6.QtDesigner',
        'PyQt6.QtHelp',
        'PyQt6.QtMultimedia',
        'PyQt6.QtOpenGL',
        'PyQt6.QtPdf',     # PDF-Rendering nicht benötigt
        'PyQt6.QtPrintSupport',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.QtWebChannel',
        'PyQt6.QtWebEngine',
        'PyQt6.QtWebSockets',
        'PyQt6.QtXml',

        # Pillow unnötige Codecs (spart ~8-10 MB)
        'PIL._avif',       # AVIF-Codec (7,5 MB) - nicht benötigt
        'PIL._webp',       # WebP-Codec (400 KB) - nicht verwendet
        'PIL._imagingtk',  # Tkinter-Integration - nicht vorhanden

        # Requests & Abhängigkeiten (nicht verwendet - spart ~3 MB)
        'requests',
        'urllib3',
        'charset_normalizer',
        'idna',
        'certifi',

        # Python Stdlib (nicht benötigt - spart ~3-5 MB)
        # REMOVED 'distutils' - wird von setuptools benötigt!
        'test',            # Test-Framework
        '_testcapi',
        'lib2to3',         # Code-Migration Tool
        'ensurepip',       # pip nicht nötig
        'venv',            # venv nicht nötig
        'pydoc_data',
        'unittest',        # Nicht verwendet
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# CHANGED: Grosse unnoetige Dateien entfernen (spart weitere ~30-35 MB)
if is_windows:
    a.binaries = [x for x in a.binaries if not x[0].startswith('opengl32sw')]  # 20 MB Software-OpenGL nicht benoetigt

# Qt6 Translations komplett entfernen (~6 MB)
a.datas = [x for x in a.datas if not x[0].startswith('PyQt6/Qt6/translations')]

# Qt6 Image-Format Plugins reduzieren - nur PNG & JPEG behalten (~1,5 MB Ersparnis)
a.datas = [x for x in a.datas if not (
    x[0].startswith('PyQt6/Qt6/plugins/imageformats') and
    not ('qpng' in x[0] or 'qjpeg' in x[0] or 'qsvg' in x[0])
)]

# PIL AVIF-Codec entfernen falls vorhanden (~7,5 MB)
a.binaries = [x for x in a.binaries if '_avif' not in x[0].lower()]

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TaktischeZeichenDruckgenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=not is_windows,  # strip auf Linux verwenden, auf Windows nicht verfuegbar
    upx=False,  # UPX deaktiviert fuer bessere Performance
    console=False,  # Kein Console-Fenster
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if is_windows else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=not is_windows,
    upx=False,
    upx_exclude=[],
    name='TaktischeZeichenDruckgenerator',
)
