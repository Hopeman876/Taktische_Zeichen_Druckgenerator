#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Einstiegspunkt für TaktischeZeichenDruckgenerator

Startet die Qt-basierte GUI-Anwendung
"""

import sys
from pathlib import Path

# Sicherstellen, dass Imports funktionieren
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from logging_manager import LoggingManager
from constants import PROGRAM_NAME, PROGRAM_VERSION, IMAGEMAGICK_SETUP_RESULT, ICON_PATH
from settings_manager import SettingsManager
from runtime_config import init_runtime_config
from gui.main_window import MainWindow  # Tabellarisches Layout


def main() -> None:
    """
    Hauptfunktion - Startet die Anwendung
    """
    # Logging initialisieren
    logging_manager = LoggingManager()  # CHANGED: Instanz behalten für shutdown()
    logger = logging_manager.get_logger(__name__)
    logger.info("=" * 80)
    logger.info(f"{PROGRAM_NAME} v{PROGRAM_VERSION} wird gestartet...")
    logger.info("=" * 80)

    # NEW: ImageMagick Setup-Status loggen (wurde bereits beim Import ausgefuehrt)
    success, im_path, im_message = IMAGEMAGICK_SETUP_RESULT
    if success:
        logger.info(f"{im_message}: {im_path}")
        # Debug: Environment-Variablen fuer ImageMagick loggen
        import os
        logger.debug(f"MAGICK_HOME: {os.environ.get('MAGICK_HOME', 'nicht gesetzt')}")
        logger.debug(f"MAGICK_CODER_MODULE_PATH: {os.environ.get('MAGICK_CODER_MODULE_PATH', 'nicht gesetzt')}")
        logger.debug(f"MAGICK_FILTER_MODULE_PATH: {os.environ.get('MAGICK_FILTER_MODULE_PATH', 'nicht gesetzt')}")
        logger.debug(f"MAGICK_CONFIGURE_PATH: {os.environ.get('MAGICK_CONFIGURE_PATH', 'nicht gesetzt')}")
        logger.debug(f"MAGICK_MODULE_PATH: {os.environ.get('MAGICK_MODULE_PATH', 'nicht gesetzt')}")
    else:
        logger.warning(f"{im_message}: {im_path}")
        logger.warning("Bitte siehe IMAGEMAGICK_SETUP.md fuer Installation")

    # NEW: Settings und RuntimeConfig initialisieren
    logger.info("Lade Einstellungen...")
    settings_manager = SettingsManager()
    settings = settings_manager.load_settings()

    # Log-Level aus Settings setzen (falls vorhanden)
    if hasattr(settings, 'log_level') and settings.log_level:
        logging_manager.set_log_level(settings.log_level)
        logger.info(f"Log-Level aus Settings geladen: {settings.log_level}")
    else:
        logger.info(f"Kein Log-Level in Settings - verwende Standard: {logging_manager.log_level}")

    # RuntimeConfig mit User-Settings initialisieren
    init_runtime_config(settings)
    logger.info("RuntimeConfig initialisiert mit User-Settings")

    # Windows: AppUserModelID setzen fuer Taskleisten-Icon
    # Muss VOR QApplication erstellt werden!
    import platform
    if platform.system() == 'Windows':
        try:
            import ctypes
            # AppUserModelID setzen (eindeutige ID fuer diese Anwendung)
            myappid = f'RamonHoffmann.TaktischeZeichenDruckgenerator.{PROGRAM_VERSION}'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            logger.debug(f"Windows AppUserModelID gesetzt: {myappid}")
        except Exception as e:
            logger.warning(f"Konnte AppUserModelID nicht setzen: {e}")

    # Qt-Anwendung erstellen
    app = QApplication(sys.argv)
    app.setApplicationName(PROGRAM_NAME)
    app.setApplicationVersion(PROGRAM_VERSION)

    # Anwendungs-Icon setzen
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
        logger.info(f"Anwendungs-Icon gesetzt: {ICON_PATH}")
    else:
        logger.warning(f"Icon nicht gefunden: {ICON_PATH}")

    # REMOVED: High-DPI Support (in PyQt6 automatisch aktiv)
    # PyQt6 hat AA_EnableHighDpiScaling nicht mehr

    # Hauptfenster erstellen und anzeigen
    window = MainWindow()
    window.show()

    logger.info("Anwendung gestartet - GUI angezeigt")

    # Event-Loop starten
    exit_code = app.exec()

    logger.info(f"Anwendung beendet mit Code: {exit_code}")

    # NEW: Logging ordnungsgemäß beenden
    logging_manager.shutdown()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
