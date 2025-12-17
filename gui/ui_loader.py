#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui_loader.py - UI-File Loader für Qt Designer .ui Dateien

Lädt .ui Dateien und bindet sie an Python-Klassen
"""

from pathlib import Path
from typing import Optional
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QMainWindow, QDialog

from logging_manager import LoggingManager


class UILoader:
    """
    Lädt Qt Designer .ui Dateien

    Verwendung:
        widget = UILoader.load_widget("my_dialog.ui", parent)
        window = UILoader.load_window("main_window.ui")
    """

    def __init__(self):
        """Initialisiert UILoader"""
        self.logger = LoggingManager().get_logger(__name__)

        # UI-Dateien liegen in gui/ui_files/
        self.ui_dir = Path(__file__).parent / "ui_files"

        if not self.ui_dir.exists():
            self.ui_dir.mkdir(parents=True, exist_ok=True)
            self.logger.warning(f"UI-Verzeichnis erstellt: {self.ui_dir}")

    def get_ui_path(self, ui_filename: str) -> Path:
        """
        Gibt vollständigen Pfad zur .ui Datei zurück

        Args:
            ui_filename: Name der .ui Datei (z.B. "main_window.ui")

        Returns:
            Path: Vollständiger Pfad zur .ui Datei
        """
        ui_path = self.ui_dir / ui_filename

        if not ui_path.exists():
            self.logger.error(f"UI-Datei nicht gefunden: {ui_path}")
            raise FileNotFoundError(f"UI-Datei nicht gefunden: {ui_path}")

        return ui_path

    def load_ui(
        self,
        ui_filename: str,
        base_instance: Optional[object] = None
    ) -> object:
        """
        Lädt .ui Datei und gibt Widget/Window zurück

        Args:
            ui_filename: Name der .ui Datei
            base_instance: Optional - Basis-Instanz für UI-Loading

        Returns:
            Geladenes UI-Objekt

        Example:
            # Variante 1: Standalone Loading
            widget = loader.load_ui("my_dialog.ui")

            # Variante 2: In existierende Klasse laden
            class MyDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    loader = UILoader()
                    loader.load_ui("my_dialog.ui", self)
        """
        ui_path = self.get_ui_path(ui_filename)

        try:
            if base_instance:
                # UI in existierende Instanz laden
                uic.loadUi(str(ui_path), base_instance)
                self.logger.debug(f"UI geladen in Instanz: {ui_filename}")
                return base_instance
            else:
                # UI standalone laden
                ui = uic.loadUi(str(ui_path))
                self.logger.debug(f"UI standalone geladen: {ui_filename}")
                return ui

        except Exception as e:
            self.logger.error(f"Fehler beim Laden von {ui_filename}: {e}")
            raise

    @staticmethod
    def load_widget(ui_filename: str, parent: Optional[QWidget] = None) -> QWidget:
        """
        Lädt .ui Datei als Widget

        Args:
            ui_filename: Name der .ui Datei
            parent: Optional - Parent-Widget

        Returns:
            QWidget: Geladenes Widget
        """
        loader = UILoader()
        ui_path = loader.get_ui_path(ui_filename)
        return uic.loadUi(str(ui_path), parent)

    @staticmethod
    def load_window(ui_filename: str) -> QMainWindow:
        """
        Lädt .ui Datei als MainWindow

        Args:
            ui_filename: Name der .ui Datei

        Returns:
            QMainWindow: Geladenes Hauptfenster
        """
        loader = UILoader()
        ui_path = loader.get_ui_path(ui_filename)
        return uic.loadUi(str(ui_path))

    @staticmethod
    def load_dialog(ui_filename: str, parent: Optional[QWidget] = None) -> QDialog:
        """
        Lädt .ui Datei als Dialog

        Args:
            ui_filename: Name der .ui Datei
            parent: Optional - Parent-Widget

        Returns:
            QDialog: Geladener Dialog
        """
        loader = UILoader()
        ui_path = loader.get_ui_path(ui_filename)
        return uic.loadUi(str(ui_path), parent)


# ================================================================================================
# TESTING
# ================================================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("UI-LOADER TEST")
    print("=" * 80)

    loader = UILoader()
    print(f"\n[INFO] UI-Verzeichnis: {loader.ui_dir}")
    print(f"[INFO] Existiert: {loader.ui_dir.exists()}")

    # Verfügbare UI-Dateien auflisten
    ui_files = list(loader.ui_dir.glob("*.ui"))
    print(f"\n[INFO] Gefundene .ui Dateien: {len(ui_files)}")
    for ui_file in ui_files:
        print(f"  - {ui_file.name}")

    print("\n" + "=" * 80)
    print("[OK] UI-Loader bereit!")
    print("=" * 80)
