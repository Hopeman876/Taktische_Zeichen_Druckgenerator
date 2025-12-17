#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
logging_manager.py - Logging-Manager

Konfiguriert und verwaltet das Logging-System der Anwendung

Erstellt: 2025-10-01
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import socket
import sys
import platform
from constants import (DEFAULT_LOG_FILES_COUNT,
                       BASE_DIR,
                       LOGS_DIR,
                       LOG_LEVELS,
                       LOG_MESSAGE_FORMAT,
                       LOG_DATE_FORMAT,
                       PROGRAM_NAME,
                       PROGRAM_VERSION,
                       PROGRAM_AUTHOR,
                       PROGRAM_DESCRIPTION,
                       RUNNING_AS_EXE)

# NEW: Singleton-Pattern - Globale Instanz-Variable
_logging_manager_instance = None


class LoggingManager:
    """
    Verwaltet das Logging-System
    
    Funktionen:
    - Erstellen von Log-Dateien mit Computername
    - Rotation von Log-Dateien
    - Verschiedene Log-Level
    - Cleanup alter Logs
    - Console-Logging (optional)
    """
    
    def __new__(cls, log_level: str = "DEBUG", log_to_console: bool = False):
        """
        Singleton-Pattern: Gibt immer dieselbe Instanz zurueck

        Args:
            log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_console: Auch auf Console ausgeben

        Returns:
            LoggingManager: Singleton-Instanz
        """
        global _logging_manager_instance

        if _logging_manager_instance is None:
            # Erste Initialisierung - neue Instanz erstellen
            _logging_manager_instance = super(LoggingManager, cls).__new__(cls)
            _logging_manager_instance._initialized = False

        return _logging_manager_instance

    def __init__(self, log_level: str = "DEBUG", log_to_console: bool = False):
        """
        Initialisiert das Logging-System (nur beim ersten Aufruf)

        Args:
            log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_console: Auch auf Console ausgeben
        """
        # CHANGED: Nur initialisieren wenn noch nicht geschehen (Singleton)
        if self._initialized:
            return

        self.log_level = log_level
        self.log_to_console = log_to_console
        self.log_file = None
        self.logger = None

        # Logging-System konfigurieren
        self._setup_logging()

        # Markieren als initialisiert
        self._initialized = True
    
    def _setup_logging(self) -> None:
        """Konfiguriert das Logging-System"""

        # Logs-Verzeichnis erstellen
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Log-Dateiname erstellen (mit Datum und Computername)
        log_filename = self._create_log_filename()
        self.log_file = LOGS_DIR / log_filename

        # Root-Logger konfigurieren
        root_logger = logging.getLogger()
        root_logger.setLevel(LOG_LEVELS.get(self.log_level, logging.DEBUG))
        
        # Bestehende Handler entfernen (falls vorhanden)
        root_logger.handlers.clear()
        
        # File-Handler erstellen
        file_handler = logging.FileHandler(
            self.log_file,
            encoding='utf-8',
            mode='a'
        )
        file_handler.setLevel(LOG_LEVELS.get(self.log_level, logging.DEBUG))
        
        # Formatter erstellen
        formatter = logging.Formatter(
            LOG_MESSAGE_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )
        file_handler.setFormatter(formatter)
        
        # File-Handler hinzufuegen
        root_logger.addHandler(file_handler)
        
        # Console-Handler (optional)
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(LOG_LEVELS.get(self.log_level, logging.DEBUG))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Logger-Instanz erstellen
        self.logger = logging.getLogger(__name__)

        # NEW: PIL/Pillow Debug-Logging unterdrücken (zu verbose)
        # PIL loggt jeden PNG-Chunk auf DEBUG-Level -> nicht hilfreich
        pil_logger = logging.getLogger('PIL')
        pil_logger.setLevel(logging.INFO)  # Nur INFO und höher

        # NEW: PyQt6 UI-Parser Debug-Logging unterdrücken (zu verbose)
        # PyQt6.uic loggt jedes Property/Widget auf DEBUG-Level -> füllt Logfile
        logging.getLogger('PyQt6.uic').setLevel(logging.INFO)
        logging.getLogger('PyQt6.uic.uiparser').setLevel(logging.INFO)
        logging.getLogger('PyQt6.uic.properties').setLevel(logging.INFO)

        # NEW: Cleanup alter Log-Dateien (automatisch beim Start)
        deleted = self._cleanup_on_startup()

        # CHANGED: Start-Meldung mit deutlicher optischer Trennung
        self.logger.info("")  # Leerzeile
        self.logger.info("")  # Leerzeile
        self.logger.info("")  # Leerzeile
        self.logger.info("=" * 80)
        self.logger.info("=" * 80)
        self.logger.info(f">>> PROGRAMMSTART: {PROGRAM_NAME} v{PROGRAM_VERSION} <<<")
        self.logger.info("=" * 80)
        self.logger.info("=" * 80)
        self.logger.info(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Log-Level: {self.log_level}")
        self.logger.info(f"Log-Datei: {self.log_file}")
        self.logger.info(f"Computername: {self._get_computer_name()}")
        self.logger.info(f"Running as EXE: {RUNNING_AS_EXE}")
        if deleted > 0:
            self.logger.info(f"Cleanup: {deleted} alte Log-Dateien gelöscht")
        self.logger.info("=" * 80)
    
    def _create_log_filename(self) -> str:
        """
        Erstellt Log-Dateinamen mit Datum und Computername
        
        Format: YYYY-MM-DD_COMPUTERNAME.log
        
        Returns:
            str: Log-Dateiname
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        computer_name = self._get_computer_name()
        
        return f"{date_str}_{computer_name}.log"
    
    def _get_computer_name(self) -> str:
        """
        Ermittelt Computername

        Returns:
            str: Computername oder 'UNKNOWN'
        """
        try:
            return socket.gethostname()
        except Exception:
            return "UNKNOWN"

    def _cleanup_on_startup(self) -> int:
        """
        Räumt alte Log-Dateien beim Programmstart auf

        Wird automatisch in _setup_logging() aufgerufen.
        Benutzt cleanup_old_logs() aber unterdrückt Logger-Ausgaben
        (da Logger noch nicht vollständig initialisiert).

        Returns:
            int: Anzahl gelöschter Dateien
        """
        try:
            # Alle Log-Dateien finden
            log_files = sorted(
                LOGS_DIR.glob("*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True  # Neueste zuerst
            )

            # Alte Dateien löschen (behalte nur DEFAULT_LOG_FILES_COUNT)
            deleted_count = 0
            for old_log in log_files[DEFAULT_LOG_FILES_COUNT:]:
                try:
                    old_log.unlink()
                    deleted_count += 1
                except Exception:
                    pass  # Fehler beim Löschen ignorieren

            return deleted_count

        except Exception:
            return 0
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """
        Gibt Logger-Instanz zurueck
        
        Args:
            name: Name des Loggers (optional)
            
        Returns:
            Logger-Instanz
        """
        if name:
            return logging.getLogger(name)
        return logging.getLogger()
    
    def set_log_level(self, log_level: str) -> bool:
        """
        Aendert Log-Level zur Laufzeit

        Args:
            log_level: Neuer Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Returns:
            bool: True bei Erfolg
        """
        if log_level not in LOG_LEVELS:
            self.logger.error(f"Invalid log level: {log_level}")
            return False

        self.log_level = log_level
        level = LOG_LEVELS[log_level]
        
        # Root-Logger und alle Handler anpassen
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        for handler in root_logger.handlers:
            handler.setLevel(level)
        
        self.logger.info(f"Log-Level geaendert auf: {log_level}")
        return True
    
    def cleanup_old_logs(self, max_files: int = DEFAULT_LOG_FILES_COUNT) -> int:
        """
        Loescht alte Log-Dateien

        Behaelt nur die neuesten max_files Dateien

        Args:
            max_files: Maximale Anzahl zu behalten

        Returns:
            Anzahl geloeschter Dateien
        """
        try:
            # Alle Log-Dateien finden
            log_files = sorted(
                LOGS_DIR.glob("*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True  # Neueste zuerst
            )
            
            # Alte Dateien loeschen
            deleted_count = 0
            for old_log in log_files[max_files:]:
                try:
                    old_log.unlink()
                    deleted_count += 1
                    self.logger.debug(f"Deleted old log: {old_log.name}")
                except Exception as e:
                    self.logger.error(f"Error deleting {old_log.name}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Cleanup: {deleted_count} alte Log-Dateien geloescht")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error during log cleanup: {e}")
            return 0
    
    def get_log_files(self) -> list[Path]:
        """
        Gibt Liste aller Log-Dateien zurueck

        Returns:
            Liste von Pfaden (sortiert nach Datum, neueste zuerst)
        """
        try:
            log_files = sorted(
                LOGS_DIR.glob("*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            return log_files
        except Exception as e:
            self.logger.error(f"Error getting log files: {e}")
            return []
    
    def get_current_log_file(self) -> Path:
        """
        Gibt aktuelle Log-Datei zurueck
        
        Returns:
            Path zur aktuellen Log-Datei
        """
        return self.log_file
    
    def get_log_size(self) -> int:
        """
        Gibt Groesse der aktuellen Log-Datei zurueck
        
        Returns:
            Groesse in Bytes
        """
        try:
            if self.log_file and self.log_file.exists():
                return self.log_file.stat().st_size
            return 0
        except Exception:
            return 0
    
    def get_total_logs_size(self) -> int:
        """
        Gibt Gesamt-Groesse aller Log-Dateien zurueck

        Returns:
            Groesse in Bytes
        """
        try:
            total_size = 0
            for log_file in LOGS_DIR.glob("*.log"):
                total_size += log_file.stat().st_size
            return total_size
        except Exception as e:
            self.logger.error(f"Error calculating total log size: {e}")
            return 0
    
    def rotate_log(self) -> bool:
        """
        Forciert Log-Rotation (erstellt neue Log-Datei)
        
        Returns:
            bool: True bei Erfolg
        """
        try:
            self.logger.info("Forcing log rotation...")
            
            # Neues Logging-System initialisieren
            self._setup_logging()
            
            self.logger.info("Log rotation completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during log rotation: {e}")
            return False
    
    def log_system_info(self) -> None:
        """Loggt System-Informationen"""
        self.logger.info("=" * 80)
        self.logger.info("SYSTEM-INFORMATIONEN")
        self.logger.info("=" * 80)
        self.logger.info(f"Python Version: {platform.python_version()}")
        self.logger.info(f"Platform: {platform.platform()}")
        self.logger.info(f"Processor: {platform.processor()}")
        self.logger.info(f"Machine: {platform.machine()}")
        self.logger.info(f"System: {platform.system()}")
        self.logger.info(f"Release: {platform.release()}")
        self.logger.info("=" * 80)
    
    def log_application_info(self) -> None:
        """Loggt Applikations-Informationen"""

        self.logger.info("=" * 80)
        self.logger.info("APPLIKATIONS-INFORMATIONEN")
        self.logger.info("=" * 80)
        self.logger.info(f"Name: {PROGRAM_NAME}")
        self.logger.info(f"Version: {PROGRAM_VERSION}")
        self.logger.info(f"Autor: {PROGRAM_AUTHOR}")
        self.logger.info(f"Beschreibung: {PROGRAM_DESCRIPTION}")
        self.logger.info(f"Base Directory: {BASE_DIR}")
        self.logger.info(f"Running as EXE: {RUNNING_AS_EXE}")
        self.logger.info(f"Logs Directory: {LOGS_DIR}")
        self.logger.info(f"Templates Directory: {TEMPLATES_DIR}")
        self.logger.info("=" * 80)
    
    def shutdown(self) -> None:
        """Beendet Logging ordnungsgemaess mit deutlicher optischer Trennung"""

        # CHANGED: Deutliche optische Trennung für Programmende
        self.logger.info("=" * 80)
        self.logger.info(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 80)
        self.logger.info("=" * 80)
        self.logger.info(f"<<< PROGRAMMENDE: {PROGRAM_NAME} v{PROGRAM_VERSION} >>>")
        self.logger.info("=" * 80)
        self.logger.info("=" * 80)
        self.logger.info("")  # Leerzeile
        self.logger.info("")  # Leerzeile
        self.logger.info("")  # Leerzeile

        # Handler schliessen
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)


# ================================================================================================
# CONVENIENCE-FUNKTIONEN
# ================================================================================================

def get_logger(name: str = None) -> logging.Logger:
    """
    Convenience-Funktion zum Holen eines Loggers
    
    Args:
        name: Logger-Name (optional)
        
    Returns:
        Logger-Instanz
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()
