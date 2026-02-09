"""
Settings Dialog für Programmeinstellungen

Ermöglicht das Bearbeiten von:
- Standard-Werten (Größen, Abstände, Schrift, Modi)
- Logging-Einstellungen (Log-Level, Max. Anzahl Logfiles)
- Erweiterte Einstellungen (Pfade, Performance, ImageMagick)

NEW (v7.3): Settings Dialog implementiert
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
import os
import shutil

from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase
from PyQt6 import uic

from settings_manager import SettingsManager
from logging_manager import LoggingManager
from constants import (
    DEFAULT_ZEICHEN_HOEHE_MM,
    DEFAULT_ZEICHEN_BREITE_MM,
    DEFAULT_BESCHNITTZUGABE_MM,
    DEFAULT_SICHERHEITSABSTAND_MM,
    DEFAULT_ABSTAND_GRAFIK_TEXT_MM,
    DEFAULT_TEXT_BOTTOM_OFFSET_MM,
    DEFAULT_DPI,
    DEFAULT_EXPORT_DPI,
    DEFAULT_MINIMUM_DPI_FOR_PRINT,
    DEFAULT_FONT_SIZE,
    DEFAULT_FONT_FAMILY
)


class SettingsDialog(QDialog):
    """
    Dialog für Programmeinstellungen

    Lädt UI aus settings_dialog.ui und verwaltet alle Einstellungen
    """

    def __init__(self, settings_mgr: SettingsManager, parent=None):
        """
        Initialisiert den Settings Dialog

        Args:
            settings_mgr: SettingsManager Instanz
            parent: Parent Widget (MainWindow)
        """
        super().__init__(parent)
        self.settings_mgr = settings_mgr
        self.settings = settings_mgr.load_settings()  # AppSettings Objekt laden
        self.logger = LoggingManager().get_logger(__name__)

        # UI laden
        self._load_ui()

        # Werte aus settings.json laden
        self._load_values()

        # Signals verbinden
        self._connect_signals()

        self.logger.info("SettingsDialog initialisiert")

    def _load_ui(self):
        """Lädt die UI-Datei"""
        ui_path = Path(__file__).parent.parent / "ui_files" / "settings_dialog.ui"

        if not ui_path.exists():
            self.logger.error(f"UI-Datei nicht gefunden: {ui_path}")
            raise FileNotFoundError(f"UI-Datei nicht gefunden: {ui_path}")

        uic.loadUi(str(ui_path), self)
        self.logger.debug(f"UI geladen: {ui_path}")

    def _load_values(self):
        """Lädt aktuelle Werte aus settings.json in die Widgets"""
        try:
            # Standard-Werte Tab
            self.spin_hoehe.setValue(self.settings.zeichen.zeichen_hoehe_mm)
            self.spin_breite.setValue(self.settings.zeichen.zeichen_breite_mm)
            self.spin_beschnitt.setValue(self.settings.zeichen.beschnittzugabe_mm)
            self.spin_sicherheit.setValue(self.settings.zeichen.sicherheitsabstand_mm)
            self.spin_grafik_text.setValue(self.settings.zeichen.abstand_grafik_text_mm)
            self.spin_text_bottom.setValue(self.settings.zeichen.text_bottom_offset_mm)

            # Schrift
            # PyQt6: families() ist eine statische Methode
            available_fonts = QFontDatabase.families()
            self.combo_font.clear()
            self.combo_font.addItems(available_fonts)

            # Aktuellen Font auswählen (aus settings.json, sonst DEFAULT_FONT_FAMILY)
            current_font = self.settings.zeichen.font_family
            if current_font in available_fonts:
                self.combo_font.setCurrentText(current_font)
            elif DEFAULT_FONT_FAMILY in available_fonts:
                self.combo_font.setCurrentText(DEFAULT_FONT_FAMILY)

            # Schriftgröße setzen (aus settings.json)
            self.spin_fontsize.setValue(self.settings.zeichen.font_size)

            # Mindest-DPI für Druck
            if hasattr(self.settings.zeichen, 'minimum_dpi_for_print'):
                self.spin_minimum_dpi.setValue(self.settings.zeichen.minimum_dpi_for_print)
            else:
                self.spin_minimum_dpi.setValue(300)  # Default

            # Standard-DPI für Export
            if hasattr(self.settings.zeichen, 'export_dpi'):
                self.spin_export_dpi.setValue(self.settings.zeichen.export_dpi)
            else:
                self.spin_export_dpi.setValue(450)  # Default

            # Standard-Modus
            standard_modus = self.settings.zeichen.standard_modus
            modus_map = {
                "ov_staerke": 0,
                "ort_staerke": 1,
                "rufname": 2,
                "freitext": 3,
                "ohne_text": 4,
                "dateiname": 5
            }
            if standard_modus in modus_map:
                self.combo_modus.setCurrentIndex(modus_map[standard_modus])

            # Grafik-Position
            grafik_position = self.settings.grafik.position
            position_map = {
                "oben": 0,
                "mittig": 1,
                "unten": 2
            }
            if grafik_position in position_map:
                self.combo_position.setCurrentIndex(position_map[grafik_position])

            # Grafik-Größe
            self.spin_max_hoehe.setValue(self.settings.grafik.max_hoehe_mm)
            self.spin_max_breite.setValue(self.settings.grafik.max_breite_mm)

            # NEW: Auto-Adjust Checkboxen
            if hasattr(self.settings.zeichen, 'auto_adjust_grafik_size'):
                self.check_auto_grafik_size.setChecked(self.settings.zeichen.auto_adjust_grafik_size)
            else:
                self.check_auto_grafik_size.setChecked(True)  # Default

            if hasattr(self.settings.zeichen, 'auto_adjust_font_size'):
                self.check_auto_font_size.setChecked(self.settings.zeichen.auto_adjust_font_size)
            else:
                self.check_auto_font_size.setChecked(True)  # Default

            # Logging Tab
            # Log-Level aus Settings laden (mit Fallback auf aktuellen Loglevel)
            if hasattr(self.settings, 'log_level'):
                log_level = self.settings.log_level
            else:
                log_level = LoggingManager().log_level  # Fallback für alte Settings

            if log_level == "DEBUG":
                self.radio_debug.setChecked(True)
            elif log_level == "INFO":
                self.radio_info.setChecked(True)
            elif log_level == "WARNING":
                self.radio_warning.setChecked(True)
            elif log_level == "ERROR":
                self.radio_error.setChecked(True)

            # Max Logfiles - Default: 10 (wenn nicht in LoggingManager konfiguriert)
            # Aktuell nicht implementiert in LoggingManager, daher Placeholder
            self.spin_max_logs.setValue(10)

            # Log-Verzeichnis Info
            from constants import LOGS_DIR
            self.label_log_dir.setText(f"Log-Verzeichnis: {LOGS_DIR}")

            # Log-Größe berechnen
            log_size = self._calculate_log_size(LOGS_DIR)
            self.label_log_size.setText(f"Aktuelle Größe: {log_size}")

            # Programmverhalten (NEW v0.8.2)
            # Standard-Layout
            if hasattr(self.settings, 'standard_layout'):
                if self.settings.standard_layout == "S1":
                    self.combo_standard_layout.setCurrentIndex(1)
                else:
                    self.combo_standard_layout.setCurrentIndex(0)  # Default: S2
            else:
                self.combo_standard_layout.setCurrentIndex(0)  # Fallback: S2

            # Standard-Export-Format
            if hasattr(self.settings, 'standard_export_format'):
                self.logger.debug(f"Lade Standard-Export-Format: {self.settings.standard_export_format}")
                format_map = {
                    "PNG": 0,
                    "PDF_SINGLE": 1,
                    "PDF_SHEET": 2
                }
                index = format_map.get(self.settings.standard_export_format, 0)
                self.logger.debug(f"Mapped zu Index: {index}")
                self.combo_standard_export.setCurrentIndex(index)
            else:
                self.logger.warning("Settings hat kein standard_export_format Attribut, verwende Fallback PNG")
                self.combo_standard_export.setCurrentIndex(0)  # Fallback: PNG

            # PDF-Seitenränder
            if hasattr(self.settings, 'pdf_margin_horizontal_mm'):
                self.spin_pdf_margin_h.setValue(self.settings.pdf_margin_horizontal_mm)
            else:
                self.spin_pdf_margin_h.setValue(10.0)  # Fallback

            if hasattr(self.settings, 'pdf_margin_vertical_mm'):
                self.spin_pdf_margin_v.setValue(self.settings.pdf_margin_vertical_mm)
            else:
                self.spin_pdf_margin_v.setValue(10.0)  # Fallback

            # Seitenverhältnis-Fixierung (NEW v0.8.4)
            # S2: 1:1 (Breite = Höhe)
            if hasattr(self.settings.zeichen, 'aspect_locked'):
                self.check_s2_aspect_locked.setChecked(self.settings.zeichen.aspect_locked)
            else:
                self.check_s2_aspect_locked.setChecked(True)  # Default: fixiert

            # S1: 2:1 (Breite = 2 x Höhe)
            if hasattr(self.settings.s1, 'aspect_locked'):
                self.check_s1_aspect_locked.setChecked(self.settings.s1.aspect_locked)
            else:
                self.check_s1_aspect_locked.setChecked(True)  # Default: fixiert

            # Erweitert Tab
            zeichen_ordner = self.settings.zeichen_ordner
            self.edit_zeichen_ordner.setText(zeichen_ordner)

            # Performance-Flags (aktuell fest aktiviert, keine Settings-Option)
            self.chk_template_opt.setChecked(True)
            self.chk_template_opt.setEnabled(False)  # Nicht änderbar
            self.chk_chunk_processing.setChecked(True)
            self.chk_chunk_processing.setEnabled(False)  # Nicht änderbar

            # ImageMagick Status
            self._check_imagemagick_status()

            self.logger.debug("Werte aus settings.json geladen")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Werte: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Fehler",
                f"Fehler beim Laden der Einstellungen:\n{str(e)}"
            )

    def _connect_signals(self):
        """Verbindet alle Signals mit Slots"""
        # ButtonBox
        self.buttonBox.accepted.connect(self._on_ok_clicked)
        self.buttonBox.rejected.connect(self._on_cancel_clicked)

        # Apply button finden und verbinden
        apply_button = self.buttonBox.button(self.buttonBox.StandardButton.Apply)
        if apply_button:
            apply_button.clicked.connect(self._on_apply_clicked)

        # Standard-Werte Tab
        self.btn_restore_defaults.clicked.connect(self._on_restore_defaults)

        # Logging Tab
        self.btn_open_logs.clicked.connect(self._on_open_logs)
        self.btn_delete_logs.clicked.connect(self._on_delete_logs)

        # Erweitert Tab
        self.btn_browse_ordner.clicked.connect(self._on_browse_folder)

        self.logger.debug("Signals verbunden")

    def _on_ok_clicked(self):
        """OK-Button: Speichern und schließen"""
        if self._save_settings():
            self.accept()

    def _on_apply_clicked(self):
        """Apply-Button: Speichern ohne zu schließen"""
        self._save_settings()

    def _on_cancel_clicked(self):
        """Cancel-Button: Verwerfen und schließen"""
        self.reject()

    def _save_settings(self) -> bool:
        """
        Speichert alle Einstellungen in settings.json

        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            # Validierung
            if not self._validate_settings():
                return False

            # AppSettings Objekt aktualisieren
            self.settings.zeichen_ordner = self.edit_zeichen_ordner.text()
            self.settings.zeichen.zeichen_hoehe_mm = self.spin_hoehe.value()
            self.settings.zeichen.zeichen_breite_mm = self.spin_breite.value()
            self.settings.zeichen.abstand_grafik_text_mm = self.spin_grafik_text.value()
            self.settings.zeichen.text_bottom_offset_mm = self.spin_text_bottom.value()
            self.settings.zeichen.beschnittzugabe_mm = self.spin_beschnitt.value()
            self.settings.zeichen.sicherheitsabstand_mm = self.spin_sicherheit.value()
            self.settings.zeichen.standard_modus = self._get_selected_modus()
            self.settings.zeichen.font_size = self.spin_fontsize.value()  # NEW (v7.3)
            self.settings.zeichen.font_family = self.combo_font.currentText()  # NEW (v7.3)
            self.settings.zeichen.export_dpi = self.spin_export_dpi.value()  # NEW: Standard-DPI
            self.settings.zeichen.minimum_dpi_for_print = self.spin_minimum_dpi.value()  # NEW: Mindest-DPI
            self.settings.zeichen.auto_adjust_grafik_size = self.check_auto_grafik_size.isChecked()  # NEW
            self.settings.zeichen.auto_adjust_font_size = self.check_auto_font_size.isChecked()  # NEW
            self.settings.grafik.max_hoehe_mm = self.spin_max_hoehe.value()
            self.settings.grafik.max_breite_mm = self.spin_max_breite.value()
            self.settings.grafik.position = self._get_selected_position()

            # Log-Level ermitteln und speichern
            if self.radio_debug.isChecked():
                self.settings.log_level = "DEBUG"
            elif self.radio_info.isChecked():
                self.settings.log_level = "INFO"
            elif self.radio_warning.isChecked():
                self.settings.log_level = "WARNING"
            elif self.radio_error.isChecked():
                self.settings.log_level = "ERROR"

            # Programmverhalten (NEW v0.8.2)
            # Standard-Layout
            layout_index = self.combo_standard_layout.currentIndex()
            self.settings.standard_layout = "S1" if layout_index == 1 else "S2"

            # Standard-Export-Format
            export_formats = ["PNG", "PDF_SINGLE", "PDF_SHEET"]
            export_index = self.combo_standard_export.currentIndex()
            self.settings.standard_export_format = export_formats[export_index]
            self.logger.debug(f"Standard-Export-Format gespeichert: {self.settings.standard_export_format} (Index: {export_index})")

            # PDF-Seitenränder
            self.settings.pdf_margin_horizontal_mm = self.spin_pdf_margin_h.value()
            self.settings.pdf_margin_vertical_mm = self.spin_pdf_margin_v.value()

            # Seitenverhältnis-Fixierung (NEW v0.8.4)
            self.settings.zeichen.aspect_locked = self.check_s2_aspect_locked.isChecked()
            self.settings.s1.aspect_locked = self.check_s1_aspect_locked.isChecked()

            # Über SettingsManager speichern
            self.settings_mgr.save_settings(self.settings)

            # Log-Level zur Laufzeit setzen
            LoggingManager().set_log_level(self.settings.log_level)

            self.logger.info("Einstellungen gespeichert")

            QMessageBox.information(
                self,
                "Gespeichert",
                "Einstellungen wurden erfolgreich gespeichert."
            )

            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Einstellungen: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Speichern der Einstellungen:\n{str(e)}"
            )
            return False

    def _validate_settings(self) -> bool:
        """
        Validiert alle Einstellungen

        Returns:
            True wenn valide, False bei Fehler
        """
        # Zeichen-Ordner prüfen
        zeichen_ordner = Path(self.edit_zeichen_ordner.text())
        if not zeichen_ordner.exists():
            QMessageBox.warning(
                self,
                "Ungültiger Pfad",
                f"Der Zeichen-Ordner existiert nicht:\n{zeichen_ordner}"
            )
            return False

        # Größen-Validierung (wird automatisch durch SpinBox Min/Max gemacht)
        # Aber wir prüfen die Logik: Grafik muss kleiner als Zeichen sein
        zeichen_hoehe = self.spin_hoehe.value()
        zeichen_breite = self.spin_breite.value()
        grafik_hoehe = self.spin_max_hoehe.value()
        grafik_breite = self.spin_max_breite.value()

        if grafik_hoehe > zeichen_hoehe:
            QMessageBox.warning(
                self,
                "Ungültige Werte",
                "Die maximale Grafik-Höhe darf nicht größer sein als die Zeichen-Höhe."
            )
            return False

        if grafik_breite > zeichen_breite:
            QMessageBox.warning(
                self,
                "Ungültige Werte",
                "Die maximale Grafik-Breite darf nicht größer sein als die Zeichen-Breite."
            )
            return False

        return True

    def _get_selected_modus(self) -> str:
        """Gibt den ausgewählten Standard-Modus zurück"""
        index_to_modus = {
            0: "ov_staerke",
            1: "ort_staerke",
            2: "rufname",
            3: "freitext",
            4: "ohne_text",
            5: "dateiname"
        }
        return index_to_modus.get(self.combo_modus.currentIndex(), "freitext")

    def _get_selected_position(self) -> str:
        """Gibt die ausgewählte Grafik-Position zurück"""
        index_to_position = {
            0: "oben",
            1: "mittig",
            2: "unten"
        }
        return index_to_position.get(self.combo_position.currentIndex(), "mittig")

    def _on_restore_defaults(self):
        """Stellt Standard-Werte aus constants.py wieder her"""
        reply = QMessageBox.question(
            self,
            "Standard wiederherstellen",
            "Möchten Sie wirklich alle Werte auf die Standardeinstellungen zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Standard-Werte setzen
            self.spin_hoehe.setValue(DEFAULT_ZEICHEN_HOEHE_MM)
            self.spin_breite.setValue(DEFAULT_ZEICHEN_BREITE_MM)
            self.spin_beschnitt.setValue(DEFAULT_BESCHNITTZUGABE_MM)
            self.spin_sicherheit.setValue(DEFAULT_SICHERHEITSABSTAND_MM)
            self.spin_grafik_text.setValue(DEFAULT_ABSTAND_GRAFIK_TEXT_MM)
            self.spin_text_bottom.setValue(DEFAULT_TEXT_BOTTOM_OFFSET_MM)

            # Font-Defaults (v7.3)
            self.spin_fontsize.setValue(DEFAULT_FONT_SIZE)
            if DEFAULT_FONT_FAMILY in QFontDatabase.families():
                self.combo_font.setCurrentText(DEFAULT_FONT_FAMILY)

            # Mindest-DPI Default
            self.spin_minimum_dpi.setValue(DEFAULT_MINIMUM_DPI_FOR_PRINT)

            # Standard-DPI Default (NEW)
            self.spin_export_dpi.setValue(DEFAULT_EXPORT_DPI)

            self.combo_modus.setCurrentIndex(3)  # freitext

            self.combo_position.setCurrentIndex(1)  # mittig
            default_grafik_hoehe = DEFAULT_ZEICHEN_HOEHE_MM - (2 * DEFAULT_SICHERHEITSABSTAND_MM)
            default_grafik_breite = DEFAULT_ZEICHEN_BREITE_MM - (2 * DEFAULT_SICHERHEITSABSTAND_MM)
            self.spin_max_hoehe.setValue(default_grafik_hoehe)
            self.spin_max_breite.setValue(default_grafik_breite)

            self.edit_zeichen_ordner.setText("Taktische_Zeichen_Grafikvorlagen")

            self.logger.info("Standard-Werte wiederhergestellt")

            QMessageBox.information(
                self,
                "Wiederhergestellt",
                "Standard-Werte wurden wiederhergestellt.\nKlicken Sie auf OK oder Anwenden zum Speichern."
            )

    def _calculate_log_size(self, log_dir: Path) -> str:
        """
        Berechnet die Gesamtgröße aller Log-Dateien

        Args:
            log_dir: Log-Verzeichnis

        Returns:
            Formatierte Größenangabe (z.B. "2.5 MB")
        """
        try:
            total_size = 0
            for log_file in log_dir.glob("*.log"):
                total_size += log_file.stat().st_size

            # Formatierung
            if total_size < 1024:
                return f"{total_size} Bytes"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f} KB"
            else:
                return f"{total_size / (1024 * 1024):.1f} MB"

        except Exception as e:
            self.logger.error(f"Fehler beim Berechnen der Log-Größe: {e}")
            return "Unbekannt"

    def _on_open_logs(self):
        """Öffnet das Log-Verzeichnis im Explorer"""
        try:
            from constants import LOGS_DIR

            if not LOGS_DIR.exists():
                QMessageBox.warning(
                    self,
                    "Verzeichnis nicht gefunden",
                    f"Das Log-Verzeichnis existiert nicht:\n{LOGS_DIR}"
                )
                return

            # Dateimanager plattformuebergreifend oeffnen
            import subprocess
            import sys as _sys
            if _sys.platform == 'win32':
                os.startfile(str(LOGS_DIR))
            elif _sys.platform == 'linux':
                subprocess.run(['xdg-open', str(LOGS_DIR)])
            else:
                raise OSError(f"Nicht unterstuetztes Betriebssystem: {_sys.platform}")
            self.logger.info(f"Log-Verzeichnis geöffnet: {LOGS_DIR}")

        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Log-Verzeichnisses: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Öffnen des Log-Verzeichnisses:\n{str(e)}"
            )

    def _on_delete_logs(self):
        """Löscht alle Log-Dateien"""
        reply = QMessageBox.question(
            self,
            "Logs löschen",
            "Möchten Sie wirklich alle Log-Dateien löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from constants import LOGS_DIR
                deleted_count = 0

                for log_file in LOGS_DIR.glob("*.log"):
                    try:
                        log_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        self.logger.error(f"Fehler beim Löschen von {log_file}: {e}")

                # Log-Größe aktualisieren
                log_size = self._calculate_log_size(LOGS_DIR)
                self.label_log_size.setText(f"Aktuelle Größe: {log_size}")

                self.logger.info(f"{deleted_count} Log-Dateien gelöscht")

                QMessageBox.information(
                    self,
                    "Gelöscht",
                    f"{deleted_count} Log-Datei(en) wurden gelöscht."
                )

            except Exception as e:
                self.logger.error(f"Fehler beim Löschen der Log-Dateien: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Fehler beim Löschen der Log-Dateien:\n{str(e)}"
                )

    def _on_browse_folder(self):
        """Öffnet Dialog zur Auswahl des Zeichen-Ordners"""
        current_path = self.edit_zeichen_ordner.text()

        folder = QFileDialog.getExistingDirectory(
            self,
            "Zeichen-Ordner auswählen",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            self.edit_zeichen_ordner.setText(folder)
            self.logger.info(f"Zeichen-Ordner ausgewählt: {folder}")

    def _check_imagemagick_status(self):
        """Prüft ImageMagick Status und aktualisiert Labels"""
        try:
            from constants import IMAGEMAGICK_SETUP_RESULT

            success, imagemagick_dir, message = IMAGEMAGICK_SETUP_RESULT

            if success:
                self.label_im_status.setText("Status: Verfügbar")

                # Pfad anzeigen
                if imagemagick_dir:
                    self.label_im_path.setText(f"Pfad: {imagemagick_dir}")
                else:
                    self.label_im_path.setText("Pfad: System-PATH")
            else:
                self.label_im_status.setText("Status: Nicht verfügbar")
                self.label_im_path.setText("Pfad: -")

        except Exception as e:
            self.logger.error(f"Fehler beim Prüfen von ImageMagick: {e}")
            self.label_im_status.setText("Status: Nicht verfügbar")
            self.label_im_path.setText("Pfad: -")
