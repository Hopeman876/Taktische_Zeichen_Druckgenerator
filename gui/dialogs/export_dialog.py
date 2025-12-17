#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_dialog.py - Export-Dialog

Features:
- Format-Auswahl (PNG/JPG)
- Ausgabe-Ordner wählen
- Progress-Bar während Export
- Multithreading-Support
"""

from pathlib import Path
from typing import List
from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox, QLabel
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QPixmap

from logging_manager import LoggingManager
from constants import (
    EXPORT_DIR,
    DPI_STUFEN,
    calculate_render_profile,
    get_lower_dpi_level,
    RenderProfile,
    LOGO_PATH
)
from gui.ui_loader import UILoader
from gui.widgets.zeichen_tree_item import ZeichenTreeItem
from taktische_zeichen_generator import TaktischeZeichenGenerator
from text_overlay import ZeichenConfig
from missing_fonts_tracker import MissingFontsTracker


class ExportWorker(QThread):
    """
    Worker-Thread für Export-Operationen

    Signals:
        preparing: (status_text)  # NEW: Für Vorbereitungsphase
        progress: (current, total, zeichen_name, status)
        finished: (successful_count, errors, actual_output_dir)  # CHANGED: actual_output_dir hinzugefügt
        error: (error_message)
    """
    preparing = pyqtSignal(str)  # NEW
    progress = pyqtSignal(int, int, str, str)
    finished = pyqtSignal(int, list, Path)  # CHANGED: Path-Parameter hinzugefügt
    error = pyqtSignal(str)

    def __init__(
        self,
        zeichen_items: List[ZeichenTreeItem],
        output_dir: Path,
        output_format: str,
        num_threads: int,
        draw_cut_lines: bool,
        dpi: int,  # NEW
        settings,
        active_layout: str = "s2"  # NEW: "s1" oder "s2"
    ):
        """
        Initialisiert Export-Worker

        Args:
            zeichen_items: Liste von ZeichenTreeItem
            output_dir: Ausgabe-Ordner
            output_format: Ausgabe-Format (PNG/PDF)
            num_threads: Anzahl paralleler Threads
            draw_cut_lines: Schnittlinien zeichnen
            dpi: Auflösung in DPI
            settings: AppSettings mit globalen Einstellungen
            active_layout: Aktives Layout ("s1" oder "s2", default: "s2")
        """
        super().__init__()
        self.zeichen_items = zeichen_items
        self.output_dir = output_dir
        self.output_format = output_format
        self.num_threads = num_threads
        self.draw_cut_lines = draw_cut_lines
        self.dpi = dpi  # NEW
        self.settings = settings
        self.active_layout = active_layout  # NEW
        self.logger = LoggingManager().get_logger(__name__)
        self.missing_fonts_report_path = None  # NEW v0.8.1: Pfad zu Fehlende_Schriftarten.txt

    def run(self):
        """Führt Export aus"""
        try:
            # NEW: Sofortiges Feedback
            self.preparing.emit("Export wird vorbereitet...")

            # CHANGED: Verwende neue Funktion aus constants.py (v0.6.0)
            from constants import create_export_folder_name

            total_zeichen = sum(item.anzahl_kopien for item in self.zeichen_items)

            # NEW: Status-Update
            self.preparing.emit(f"Erstelle Export-Ordner für {total_zeichen} Zeichen...")

            # Format-spezifischer Ausgabe-Pfad
            is_pdf_export = self.output_format.startswith("PDF")

            # CHANGED: Exportformat bestimmen für Ordnernamen (v0.6.0)
            if self.output_format == "PNG":
                file_format = "PNG"
                export_format = "Einzelzeichen"  # PNG ist immer Einzelzeichen
            elif self.output_format == "PDF - Einzelzeichen":
                file_format = "PDF"
                export_format = "Einzelzeichen"
            elif self.output_format == "PDF - Schnittbogen (A4)":
                file_format = "PDF"
                export_format = "Schnittbogen"
            else:
                # Fallback
                file_format = "PNG"
                export_format = "Einzelzeichen"

            # CHANGED: Immer Ordner erstellen (auch für PDF) (v0.6.0)
            export_folder_name = create_export_folder_name(
                count=total_zeichen,
                dpi=self.dpi,
                file_format=file_format,
                export_format=export_format
            )
            actual_output_dir = self.output_dir / export_folder_name
            actual_output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Export-Ordner erstellt: {actual_output_dir}")

            # NEW: Status-Update
            self.preparing.emit("Erstelle Konfigurations-Tasks...")

            # Generator erstellen
            generator = TaktischeZeichenGenerator()

            # NEW v0.8.1: Schriftarten-Tracker für fehlende Fonts in SVGs
            fonts_tracker = MissingFontsTracker()

            # Tasks erstellen (mit Kopien-Anzahl)
            tasks = []

            # v7.1: Werte aus RuntimeConfig holen (Single Source of Truth!)
            from runtime_config import get_config
            from constants import calculate_render_profile

            config = get_config()

            # CRITICAL: Layout-abhängige Abmessungen verwenden (S1 vs S2)
            if self.active_layout == "s1":
                zeichen_hoehe_mm = config.s1_zeichen_hoehe_mm
                zeichen_breite_mm = config.s1_zeichen_breite_mm
                sicherheitsabstand_mm = config.s1_sicherheitsabstand_mm
                beschnittzugabe_mm = config.s1_beschnittzugabe_mm
            else:  # S2-Layout
                zeichen_hoehe_mm = config.zeichen_hoehe_mm
                zeichen_breite_mm = config.zeichen_breite_mm
                sicherheitsabstand_mm = config.sicherheitsabstand_mm
                beschnittzugabe_mm = config.beschnittzugabe_mm

            # Render-Profil einmalig berechnen (optimiert DPI, Threads, render_scale)
            # basierend auf Zeichengröße und gewählter DPI
            render_profile = calculate_render_profile(
                zeichen_hoehe_mm,
                zeichen_breite_mm,
                self.dpi,
                max_threads=self.num_threads
            )

            # Verwende optimierte Thread-Anzahl aus Profil
            optimized_threads = render_profile.threads
            if optimized_threads < self.num_threads:
                self.logger.info(
                    f"Thread-Anzahl reduziert: {self.num_threads} -> {optimized_threads} "
                    f"(Zeichengröße: {zeichen_hoehe_mm}x{zeichen_breite_mm}mm, Layout: {self.active_layout.upper()})"
                )

            # Tasks erstellen
            # OPTIMIERUNG (v7.3): Für PNG nur unique Zeichen, für PDF alle Kopien
            tasks = []
            copy_map = {}  # Nur für PNG: Speichert anzahl_kopien pro Zeichen

            for item in self.zeichen_items:
                # NEW v0.8.1: Prüfe SVG auf fehlende Schriftarten (nur einmal pro unique SVG!)
                fonts_tracker.check_svg(item.svg_path, item.name.replace('.svg', ''))

                # PDF: Alle Kopien als Tasks (jede Kopie = 1 Seite)
                # PNG: Nur erste Kopie (Rest wird durch Datei-Kopieren erstellt)
                num_copies_to_create = item.anzahl_kopien if is_pdf_export else 1
                zeichen_base_id = f"{item.name.replace('.svg', '')}"

                for copy_num in range(1, num_copies_to_create + 1):
                    # v7.1: Grafik-Größe aus RuntimeConfig holen
                    grafik_position = "center"  # Default (internal name)
                    custom_hoehe = config.grafik_hoehe_mm
                    custom_breite = config.grafik_breite_mm

                    # Position nur für "ohne_text" relevant
                    if item.params.modus == "ohne_text":
                        # Konvertiere interne Position zu internen Namen
                        position_map = {"oben": "top", "mittig": "center", "unten": "bottom"}
                        grafik_position = position_map.get(config.grafik_position, "center")

                    # Text-Parameter je nach Modus
                    ov_name = None
                    ort_name = None  # NEW: Separates Feld für Ort+Stärke
                    freitext = None
                    if item.params.modus == "ov_staerke" and item.params.text:
                        ov_name = item.params.text
                    elif item.params.modus == "ort_staerke" and item.params.text:  # FIXED: Eigenes ort_name
                        ort_name = item.params.text
                    elif item.params.modus in ["freitext", "dateiname"] and item.params.text:  # CHANGED: dateiname hinzugefügt
                        freitext = item.params.text
                    # schreiblinie_staerke braucht keinen Text-Parameter

                    zeichen_config = ZeichenConfig(
                        zeichen_id=f"{zeichen_base_id}_{copy_num:03d}",
                        svg_path=item.svg_path,
                        modus=item.params.modus,
                        ov_name=ov_name,
                        ort_name=ort_name,  # NEW: Ort-Name separat übergeben
                        freitext=freitext,
                        grafik_position=grafik_position,  # v7.1: Aus RuntimeConfig
                        custom_grafik_hoehe_mm=custom_hoehe,  # v7.1: Aus RuntimeConfig (separat)
                        custom_grafik_breite_mm=custom_breite,  # v7.1: Aus RuntimeConfig (separat)
                        render_scale=render_profile.render_scale,  # v7.1 Phase 2: Performance-Optimierung
                        font_size=config.font_size,  # FIXED: Aus RuntimeConfig statt DEFAULT_FONT_SIZE
                        dpi=self.dpi,
                        # CRITICAL: Layout-abhängige Abmessungen verwenden (S1 vs S2)
                        zeichen_hoehe_mm=zeichen_hoehe_mm,
                        zeichen_breite_mm=zeichen_breite_mm,
                        sicherheitsabstand_mm=sicherheitsabstand_mm,
                        beschnittzugabe_mm=beschnittzugabe_mm,
                        # v7.1: Text-Offset-Parameter aus RuntimeConfig übernehmen
                        abstand_grafik_text_mm=config.abstand_grafik_text_mm,
                        text_bottom_offset_mm=config.text_bottom_offset_mm,
                        output_dir=actual_output_dir  # NEW: Verwende spezifischen Ausgabe-Ordner
                    )
                    tasks.append((item.svg_path, zeichen_config))

                # Speichere Kopien-Anzahl für PNG (Datei-Kopieren)
                if not is_pdf_export and item.anzahl_kopien > 1:
                    # NEW: Für S1-Layout "s1_layout" als Modus verwenden
                    modus_for_filename = "s1_layout" if self.active_layout == "s1" else item.params.modus
                    copy_map[zeichen_base_id] = (item.anzahl_kopien, modus_for_filename)

            # Progress-Callback
            def progress_callback(current, total, svg_name, status):
                self.progress.emit(current, total, svg_name, status)

            # NEW: Preparing-Callback für Template-Erstellung
            def preparing_callback(status_text):
                self.preparing.emit(status_text)

            # Batch-Verarbeitung
            if is_pdf_export:
                # PDF-Export: Stapelbasierte Verarbeitung (v0.6.0 - Ressourcen-Optimierung)
                # CHANGED: S1-Layout PDF-Export jetzt unterstützt (verwendet layout-abhängige Abmessungen)
                self.logger.info(f"Starte PDF-Export (stapelbasiert): {len(tasks)} Zeichen")

                # NEW: Stapelbasierte PDF-Export-Funktionen verwenden
                from pdf_exporter import create_einzelzeichen_pdf_chunked, create_schnittbogen_pdf_chunked
                from constants import DEFAULT_PDF_CHUNK_SIZE

                if self.output_format == "PDF - Einzelzeichen":
                    # Variante 1: Einzelzeichen (stapelbasiert)
                    self.preparing.emit("Erstelle Einzelzeichen-PDFs (stapelweise)...")

                    # Dynamische Stapelgröße basierend auf Zeichengröße (für häufigere GC)
                    # CRITICAL: Layout-abhängige Abmessungen verwenden (bereits berechnet oben)
                    max_dimension = max(zeichen_hoehe_mm, zeichen_breite_mm)
                    if max_dimension > 150:
                        pdf_chunk_size = 25  # Sehr große Zeichen: Kleinere Stapel
                    elif max_dimension > 100:
                        pdf_chunk_size = 50  # Große Zeichen: Mittlere Stapel
                    else:
                        pdf_chunk_size = DEFAULT_PDF_CHUNK_SIZE  # Normale Zeichen: Standard

                    pdf_files = create_einzelzeichen_pdf_chunked(
                        generator=generator,
                        tasks=tasks,
                        output_dir=actual_output_dir,
                        dpi=self.dpi,
                        draw_cut_lines=self.draw_cut_lines,
                        progress_callback=progress_callback,
                        chunk_size=pdf_chunk_size,
                        export_format=export_format,  # NEW (v0.6.0)
                        # CRITICAL: Layout-abhängige Abmessungen (S1 vs S2)
                        zeichen_hoehe_mm=zeichen_hoehe_mm,
                        zeichen_breite_mm=zeichen_breite_mm,
                        beschnittzugabe_mm=beschnittzugabe_mm,
                        num_threads=optimized_threads,  # Optimiert basierend auf Zeichengröße
                        # NEW: S1-Layout Parameter
                        s1_links_prozent=config.s1_links_prozent,
                        s1_anzahl_schreiblinien=config.s1_anzahl_schreiblinien,
                        s1_staerke_anzeigen=config.s1_staerke_anzeigen
                    )
                    self.logger.info(f"{len(pdf_files)} PDF-Dateien erstellt")
                else:
                    # Variante 2: Schnittbogen (stapelbasiert)
                    self.preparing.emit("Erstelle Schnittbogen-PDFs (stapelweise)...")

                    # Dynamische Stapelgröße basierend auf Zeichengröße (für häufigere GC)
                    # CRITICAL: Layout-abhängige Abmessungen verwenden (bereits berechnet oben)
                    max_dimension = max(zeichen_hoehe_mm, zeichen_breite_mm)
                    if max_dimension > 150:
                        schnittbogen_chunk_size = 10  # Sehr große Zeichen: Sehr kleine Stapel
                    elif max_dimension > 100:
                        schnittbogen_chunk_size = 20  # Große Zeichen: Kleine Stapel
                    else:
                        schnittbogen_chunk_size = 50  # Normale Zeichen: Standard (50 Seiten)

                    pdf_files = create_schnittbogen_pdf_chunked(
                        generator=generator,
                        tasks=tasks,
                        output_dir=actual_output_dir,
                        dpi=self.dpi,
                        draw_cut_lines=self.draw_cut_lines,
                        progress_callback=progress_callback,
                        chunk_size=schnittbogen_chunk_size,  # Dynamisch angepasst
                        export_format=export_format,  # NEW (v0.6.0)
                        # CRITICAL: Layout-abhängige Abmessungen (S1 vs S2)
                        zeichen_hoehe_mm=zeichen_hoehe_mm,
                        zeichen_breite_mm=zeichen_breite_mm,
                        beschnittzugabe_mm=beschnittzugabe_mm,
                        sicherheitsabstand_mm=sicherheitsabstand_mm,
                        num_threads=optimized_threads,  # Optimiert basierend auf Zeichengröße
                        # NEW: S1-Layout Parameter
                        s1_links_prozent=config.s1_links_prozent,
                        s1_anzahl_schreiblinien=config.s1_anzahl_schreiblinien,
                        s1_staerke_anzeigen=config.s1_staerke_anzeigen
                    )
                    self.logger.info(f"{len(pdf_files)} PDF-Dateien erstellt")

                successful_files = pdf_files
                errors = []

            else:
                # PNG-Export: Layout-spezifische Batch-Verarbeitung
                if self.active_layout == "s1":
                    # S1-Layout Export
                    self.logger.info(f"Starte PNG-Export (S1-Layout): {len(tasks)} Zeichen, {optimized_threads} Threads")
                    successful_files, errors = generator.create_zeichen_s1_batch(
                        tasks=tasks,
                        s1_links_prozent=config.s1_links_prozent,
                        s1_anzahl_schreiblinien=config.s1_anzahl_schreiblinien,
                        s1_staerke_anzeigen=config.s1_staerke_anzeigen,
                        draw_cut_lines=self.draw_cut_lines,
                        num_threads=optimized_threads,  # Optimiert basierend auf Zeichengröße
                        progress_callback=progress_callback,
                        preparing_callback=preparing_callback,  # NEW: Template-Vorbereitung
                        use_templates=True  # NEW: Template-Optimierung aktiviert
                    )
                else:
                    # S2-Layout Export (Standard)
                    self.logger.info(f"Starte PNG-Export (S2-Layout): {len(tasks)} Zeichen, {optimized_threads} Threads")
                    successful_files, errors = generator.create_zeichen_batch(
                        tasks=tasks,
                        draw_cut_lines=self.draw_cut_lines,
                        num_threads=optimized_threads,  # Optimiert basierend auf Zeichengröße
                        progress_callback=progress_callback,
                        preparing_callback=preparing_callback,  # NEW
                        use_templates=True
                    )

                # OPTIMIERUNG (v7.3): Kopien erstellen durch Datei-Kopieren (statt Neu-Rendern)
                if copy_map:
                    import shutil
                    self.logger.info(f"Erstelle Kopien für {len(copy_map)} Zeichen...")

                    # Dateiname-Suffix basierend auf Schnittlinien
                    suffix = "_mit_linien" if self.draw_cut_lines else "_druckfertig"

                    # Gesamtzahl für Progress-Tracking berechnen
                    total_with_copies = len(successful_files) + sum(k[0] - 1 for k in copy_map.values())
                    copy_counter = len(successful_files)  # Startet nach den gerenderten Zeichen

                    for zeichen_base_id, (anzahl_kopien, modus) in copy_map.items():
                        # Original-Datei (erste Kopie) finden - WICHTIG: Mit Modus und Suffix!
                        source_file = actual_output_dir / f"{zeichen_base_id}_001_{modus}{suffix}.png"

                        if source_file.exists():
                            # Kopien 2-N erstellen
                            for copy_num in range(2, anzahl_kopien + 1):
                                target_file = actual_output_dir / f"{zeichen_base_id}_{copy_num:03d}_{modus}{suffix}.png"

                                try:
                                    shutil.copy2(source_file, target_file)
                                    successful_files.append(target_file)
                                    copy_counter += 1

                                    # Progress-Update für Kopien
                                    progress_callback(copy_counter, total_with_copies, target_file.stem, "KOPIERT")

                                    self.logger.debug(f"Kopiert: {source_file.name} -> {target_file.name}")
                                except Exception as e:
                                    self.logger.error(f"Fehler beim Kopieren {target_file.name}: {e}")
                                    errors.append((zeichen_base_id, f"Kopier-Fehler: {e}"))

                            self.logger.info(f"Zeichen '{zeichen_base_id}': {anzahl_kopien-1} Kopien erstellt")
                        else:
                            self.logger.warning(f"Original-Datei nicht gefunden: {source_file}")
                            self.logger.debug(f"Erwarteter Pfad: {source_file}")

                    total_kopien = sum(k[0] - 1 for k in copy_map.values())
                    self.logger.info(f"{total_kopien} Kopien erfolgreich erstellt (durch Datei-Kopieren)")

            # NEW v0.8.1: Bericht über fehlende Schriftarten erstellen
            if fonts_tracker.has_missing_fonts():
                self.logger.warning(
                    f"WARNUNG: {fonts_tracker.get_missing_fonts_count()} fehlende Schriftarten in SVG-Dateien gefunden!"
                )
                self.missing_fonts_report_path = fonts_tracker.write_report(actual_output_dir)

            # Fertig
            # NOTE: missing_fonts_report_path wird im finished-Handler überprüft und User wird informiert
            self.finished.emit(len(successful_files), errors, actual_output_dir)  # CHANGED: actual_output_dir hinzugefügt

        except Exception as e:
            self.logger.error(f"Export-Fehler: {e}")
            self.error.emit(str(e))


class ExportDialog(QDialog):
    """
    Export-Dialog

    UI-Master: gui/ui_files/export_dialog.ui

    Features:
    - Format-Auswahl
    - Ausgabe-Ordner wählen
    - Progress-Bar
    """

    def __init__(self, zeichen_items: List[ZeichenTreeItem], settings, active_layout: str = "s2", parent=None):
        """
        Initialisiert Export-Dialog

        Args:
            zeichen_items: Liste von ausgewählten ZeichenTreeItem
            settings: AppSettings mit globalen Einstellungen
            active_layout: Aktives Layout ("s1" oder "s2", default: "s2")
            parent: Parent-Widget
        """
        super().__init__(parent)

        self.logger = LoggingManager().get_logger(__name__)
        self.zeichen_items = zeichen_items
        self.settings = settings
        self.active_layout = active_layout  # NEW: S1 oder S2 Layout
        self.worker = None
        self.actual_output_dir = None  # NEW: Tatsächlicher Ausgabe-Ordner nach Export
        self.export_successful = False  # NEW v0.8.2.1: Flag für erfolgreichen Export

        # UI laden
        UILoader().load_ui("export_dialog.ui", self)

        # Logo hinzufuegen
        self._add_logo_widget()

        # UI initialisieren
        self._init_ui()
        self._connect_signals()

        self.logger.info(f"Export-Dialog geöffnet: {len(zeichen_items)} Zeichen")

    def _add_logo_widget(self):
        """Laedt Logo in das label_logo Widget (definiert in .ui-Datei)"""
        if not LOGO_PATH.exists():
            self.logger.warning(f"Logo nicht gefunden: {LOGO_PATH}")
            # Label ausblenden, wenn Logo nicht existiert
            if hasattr(self, 'label_logo'):
                self.label_logo.hide()
            return

        # Logo laden und skalieren
        logo_pixmap = QPixmap(str(LOGO_PATH))
        if logo_pixmap.isNull():
            self.logger.error(f"Logo konnte nicht geladen werden: {LOGO_PATH}")
            if hasattr(self, 'label_logo'):
                self.label_logo.hide()
            return

        # Logo auf passende Groesse skalieren (max 80px Hoehe)
        logo_pixmap = logo_pixmap.scaledToHeight(
            80,
            Qt.TransformationMode.SmoothTransformation
        )

        # Logo ins Label setzen (Label ist bereits in .ui-Datei definiert)
        if hasattr(self, 'label_logo'):
            self.label_logo.setPixmap(logo_pixmap)
            self.logger.debug(f"Logo im Export-Dialog geladen: {LOGO_PATH}")
        else:
            self.logger.warning("label_logo nicht in Export-Dialog UI gefunden")

    def _init_ui(self):
        """Initialisiert UI-Elemente"""
        # Standard-Ausgabe-Ordner setzen
        self.line_ausgabe_ordner.setText(str(EXPORT_DIR))

        # v7.1.1: Standard-DPI aus RuntimeConfig holen (Single Source of Truth!)
        from runtime_config import get_config
        config = get_config()
        self._set_dpi_by_value(config.export_dpi)

        # Standard-Export-Format vorwählen (NEW v0.8.2)
        self.logger.debug(f"Settings-Objekt: {type(self.settings)}")
        self.logger.debug(f"Hat standard_export_format: {hasattr(self.settings, 'standard_export_format')}")

        if hasattr(self.settings, 'standard_export_format'):
            self.logger.debug(f"standard_export_format Wert: {self.settings.standard_export_format}")

            # Map Settings-Wert zu ComboBox-Text
            format_map = {
                "PNG": "PNG",
                "PDF_SINGLE": "PDF - Einzelzeichen",
                "PDF_SHEET": "PDF - Schnittbogen (A4)"
            }
            combo_text = format_map.get(self.settings.standard_export_format, "PNG")
            self.logger.debug(f"Mapped zu ComboBox-Text: {combo_text}")

            # ComboBox auf entsprechenden Wert setzen
            index = self.combo_format.findText(combo_text)
            self.logger.debug(f"ComboBox findText Index: {index}")

            if index >= 0:
                self.combo_format.setCurrentIndex(index)
                self.logger.info(f"Standard-Export-Format vorgewählt: {combo_text}")
            else:
                self.logger.warning(f"Standard-Export-Format '{combo_text}' nicht in ComboBox gefunden")
        else:
            self.logger.warning("settings hat kein Attribut 'standard_export_format'")

        # Zusammenfassung berechnen
        self._update_summary()

    def _connect_signals(self):
        """Verbindet Signals mit Slots"""
        self.btn_ordner_waehlen.clicked.connect(self._on_ordner_waehlen)
        self.btn_abbrechen.clicked.connect(self.reject)
        self.btn_exportieren.clicked.connect(self._on_exportieren)

        # v7.1: Schnittlinien-Checkbox Event
        self.chk_schnittlinien.stateChanged.connect(self._on_schnittlinien_changed)
        self.btn_ordner_oeffnen_nach_export.clicked.connect(self._on_ordner_oeffnen_nach_export)  # NEW

        # Zusammenfassung aktualisieren wenn DPI/Threads sich ändern
        self.combo_dpi.currentIndexChanged.connect(self._update_summary)
        self.spin_threads.valueChanged.connect(self._update_summary)

    def _check_dpi_requirements(self) -> bool:
        """
        Prüft DPI-Anforderungen (verschmolzen: Mindest-DPI + Optimierung)

        Zeigt Warnung wenn:
        1. DPI < minimum_dpi_for_print (KRITISCH - nicht druckbar)
        2. DPI > empfohlen für Zeichengröße (INFO - Optimierung möglich)

        Returns:
            True: Export fortsetzen
            False: Export abbrechen
        """
        # Aktuelle DPI aus ComboBox
        dpi_text = self.combo_dpi.currentText()
        current_dpi = int(dpi_text.split()[0])

        max_size = max(
            self.settings.zeichen.zeichen_hoehe_mm,
            self.settings.zeichen.zeichen_breite_mm
        )

        # Mindest-DPI aus RuntimeConfig holen
        from runtime_config import get_config
        config = get_config()
        minimum_dpi = config.minimum_dpi_for_print

        # Fall 1: DPI < Mindest-DPI (KRITISCH - nicht druckbar)
        if current_dpi < minimum_dpi:
            return self._show_minimum_dpi_warning(current_dpi, minimum_dpi, max_size)

        # Fall 2: DPI > empfohlen (INFO - Optimierung möglich, nur bei großen Zeichen)
        if max_size > 100:
            profile = calculate_render_profile(
                self.settings.zeichen.zeichen_hoehe_mm,
                self.settings.zeichen.zeichen_breite_mm,
                current_dpi,
                max_threads=self.spin_threads.value()
            )

            if current_dpi > profile.dpi:
                return self._show_dpi_optimization_info(current_dpi, profile, max_size)

        # Fall 3: Alles OK - Export fortsetzen
        return True

    def _show_minimum_dpi_warning(self, current_dpi: int, minimum_dpi: int, size_mm: float) -> bool:
        """
        Zeigt Warnung bei DPI < minimum_dpi_for_print

        OPTIMIZED v0.8.2.4: Wenn Schnittlinien aktiviert sind, vereinfachter Dialog
        (impliziert bereits Testdruck, keine extra Checkbox nötig)

        Args:
            current_dpi: Aktuell gewählte DPI
            minimum_dpi: Mindest-DPI aus Einstellungen
            size_mm: Maximale Zeichengröße

        Returns:
            True: Export als Test fortsetzen
            False: Export abbrechen
        """
        # OPTIMIZED: Wenn Schnittlinien aktiviert sind, ist es offensichtlich ein Testdruck
        schnittlinien_aktiv = self.chk_schnittlinien.isChecked()

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("DPI-Einstellung prüfen")

        if schnittlinien_aktiv:
            # Vereinfachter Dialog bei Schnittlinien (impliziert Testdruck)
            text = (
                f"<b>Schnitt-/Hilfslinien aktiviert</b><br><br>"
                f"Deine Einstellung: <b>{current_dpi} DPI</b><br>"
                f"Status: <span style='color: #cc6600;'>⚠ Nur für Testdruck geeignet</span><br><br>"
                f"Die Druckerei benötigt mindestens <b>{minimum_dpi} DPI</b>.<br><br>"
                f"<b>Hinweis:</b> Schnitt-/Hilfslinien sind bereits ein Testdruck-Feature."
            )
        else:
            # Normaler Dialog ohne Schnittlinien
            text = (
                f"<b>Erkannte Zeichengröße: {size_mm:.0f} mm</b><br><br>"
                f"Deine Einstellung: <b>{current_dpi} DPI</b><br>"
                f"Status: <span style='color: #cc6600;'>⚠ Nicht für Druck geeignet</span><br><br>"
                f"Die Druckerei benötigt mindestens <b>{minimum_dpi} DPI</b>.<br>"
                f"Empfohlen für diese Größe: <b>{minimum_dpi} DPI</b><br><br>"
                f"<b>Mit {minimum_dpi} DPI:</b><br>"
                f"• Druckqualität gewährleistet ✓<br>"
                f"• Optimale Performance<br>"
            )

        msg_box.setText(text)
        msg_box.setTextFormat(Qt.TextFormat.RichText)

        # Checkbox nur wenn KEINE Schnittlinien aktiv (dann ist bereits klar dass Test)
        chk_test_only = None
        if not schnittlinien_aktiv:
            from PyQt6.QtWidgets import QCheckBox
            chk_test_only = QCheckBox("Nur Test (nicht drucken)")
            msg_box.setCheckBox(chk_test_only)

        # Buttons
        btn_test = msg_box.addButton("Als Test exportieren", QMessageBox.ButtonRole.AcceptRole)
        btn_fix = msg_box.addButton(f"Auf {minimum_dpi} DPI ändern", QMessageBox.ButtonRole.ActionRole)
        btn_cancel = msg_box.addButton("Abbrechen", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(btn_fix)

        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == btn_cancel:
            self.logger.info(f"Export abgebrochen - DPI zu niedrig ({current_dpi} < {minimum_dpi})")
            return False

        elif clicked == btn_fix:
            # DPI auf Minimum ändern
            self._set_dpi_by_value(minimum_dpi)
            self.logger.info(f"DPI automatisch angepasst: {current_dpi} → {minimum_dpi} DPI")

            QMessageBox.information(
                self,
                "DPI angepasst",
                f"Export wird mit {minimum_dpi} DPI durchgeführt (Druckqualität)."
            )
            return True

        else:  # btn_test
            # OPTIMIZED: Bei Schnittlinien keine weitere Bestätigung nötig
            if schnittlinien_aktiv:
                self.logger.warning(
                    f"Export als TEST mit {current_dpi} DPI (< {minimum_dpi}) + Schnittlinien - "
                    f"NICHT druckbar!"
                )
                return True

            # Ohne Schnittlinien: Checkbox prüfen
            if chk_test_only and chk_test_only.isChecked():
                self.logger.warning(
                    f"Export als TEST mit {current_dpi} DPI (< {minimum_dpi}) - "
                    f"NICHT druckbar!"
                )
                return True
            else:
                # Checkbox nicht aktiviert - nochmal warnen
                result = QMessageBox.warning(
                    self,
                    "Wirklich fortfahren?",
                    f"Du hast die Checkbox 'Nur Test' nicht aktiviert.\n\n"
                    f"Mit {current_dpi} DPI ist das Ergebnis NICHT druckbar!\n\n"
                    f"Wirklich fortfahren?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if result == QMessageBox.StandardButton.Yes:
                    self.logger.warning(
                        f"Export OHNE Checkbox mit {current_dpi} DPI (< {minimum_dpi}) - "
                        f"User wurde gewarnt!"
                    )
                    return True
                else:
                    self.logger.info("Export abgebrochen - Checkbox nicht aktiviert")
                    return False

    def _show_dpi_optimization_info(self, current_dpi: int, profile: RenderProfile, size_mm: float) -> bool:
        """
        Zeigt Info-Dialog bei DPI > empfohlen (Optimierung möglich)

        Args:
            current_dpi: Aktuell gewählte DPI
            profile: Empfohlenes RenderProfile
            size_mm: Maximale Zeichengröße

        Returns:
            True: Export fortsetzen (egal ob optimiert oder nicht)
            False: Export abbrechen (sollte nicht vorkommen)
        """
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("DPI-Optimierung verfügbar")

        text = (
            f"<b>Erkannte Zeichengröße: {size_mm:.0f} mm</b><br><br>"
            f"Deine Einstellung: <b>{current_dpi} DPI</b><br>"
            f"Status: <span style='color: #008800;'>✓ Druckbar, aber nicht optimal</span><br><br>"
            f"Empfohlen für diese Größe: <b>{profile.dpi} DPI</b><br>"
            f"Empfohlenes Profil: {profile.name}<br><br>"
            f"<b>Vorteile mit {profile.dpi} DPI:</b><br>"
            f"• ~85% schnellere Verarbeitung<br>"
            f"• ~94% weniger RAM-Verbrauch<br>"
            f"• Kein Absturz-Risiko<br>"
            f"• Qualität bleibt optimal ({profile.dpi}+ DPI) ✓<br>"
        )
        msg_box.setText(text)
        msg_box.setTextFormat(Qt.TextFormat.RichText)

        # Buttons
        btn_keep = msg_box.addButton(f"{current_dpi} DPI beibehalten", QMessageBox.ButtonRole.RejectRole)
        btn_optimize = msg_box.addButton(f"Auf {profile.dpi} DPI optimieren", QMessageBox.ButtonRole.AcceptRole)
        msg_box.setDefaultButton(btn_optimize)

        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == btn_optimize:
            # DPI anwenden
            self._set_dpi_by_value(profile.dpi)

            # Threads anpassen
            self.spin_threads.setValue(profile.threads)

            self.logger.info(
                f"DPI-Optimierung angewendet: {current_dpi} → {profile.dpi} DPI, "
                f"Threads: {profile.threads}"
            )

            QMessageBox.information(
                self,
                "Optimierung aktiv",
                f"Export wird mit optimierten Einstellungen durchgeführt.\n"
                f"DPI: {profile.dpi}, Threads: {profile.threads}"
            )
        else:
            self.logger.info(f"DPI-Optimierung abgelehnt - Export mit {current_dpi} DPI")

        # Immer True - Export fortsetzen (DPI ist druckbar)
        return True

    def _on_schnittlinien_changed(self, state):
        """
        Schnittlinien-Checkbox geändert (v7.1)

        Note: Dialog wird asynchron angezeigt, damit Checkbox sofort visuell
        aktualisiert wird (Fix für wahrgenommene Verzögerung)
        """
        if state == Qt.CheckState.Checked.value:
            # Dialog asynchron anzeigen (nächster Event-Loop-Zyklus)
            # Dadurch kann Checkbox sofort visuell aktualisiert werden
            QTimer.singleShot(0, self._show_schnittlinien_info)

    def _show_schnittlinien_info(self):
        """
        Info-Dialog bei aktivierten Schnittlinien (v7.1)
        Setzt DPI automatisch eine Stufe niedriger

        OPTIMIZED v0.8.2.4: Zeigt Dialog nur noch wenn DPI tatsächlich reduziert wird
        """
        # Aktuelle DPI
        dpi_text = self.combo_dpi.currentText()
        current_dpi = int(dpi_text.split()[0])

        # Berechne empfohlene DPI (basierend auf Zeichengröße)
        profile = calculate_render_profile(
            self.settings.zeichen.zeichen_hoehe_mm,
            self.settings.zeichen.zeichen_breite_mm,
            current_dpi,
            max_threads=self.spin_threads.value()
        )

        # Eine Stufe niedriger für Schnittlinien
        schnittlinien_dpi = get_lower_dpi_level(profile.dpi)

        # OPTIMIZED: Nur Dialog anzeigen wenn DPI tatsächlich reduziert wird
        if schnittlinien_dpi < current_dpi:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Schnitt-/Hilfslinien aktiviert")
            msg_box.setText(
                "Die Schnitt-/Hilfslinien dienen nur zur Überprüfung der Maße "
                "und der Grafikpositionierung.\n\n"
                "⚠️ Sie dürfen NICHT in den fertigen Druckdateien enthalten sein!\n\n"
                f"Für Schnittlinien wird die Auflösung automatisch auf {schnittlinien_dpi} DPI "
                f"reduziert (statt {current_dpi} DPI) für schnellere Vorschau."
            )
            msg_box.addButton(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            # DPI automatisch setzen
            self._set_dpi_by_value(schnittlinien_dpi)
            self.logger.info(f"DPI auf {schnittlinien_dpi} gesetzt (Schnittlinien aktiv)")
        else:
            # DPI bereits minimal - kein Dialog nötig
            self.logger.info(f"Schnittlinien aktiviert - DPI bleibt bei {current_dpi} (bereits minimal)")

    def _set_dpi_by_value(self, dpi: int):
        """
        Setzt DPI-ComboBox auf bestimmten Wert (v7.1)

        Args:
            dpi: Gewünschte DPI (muss in DPI_STUFEN vorhanden sein)
        """
        # DPI-Map: {dpi_wert: index}
        # DPI-Stufen: [100, 150, 200, 300, 450, 600]
        dpi_map = {
            100: 0,
            150: 1,
            200: 2,
            300: 3,
            450: 4,
            600: 5
        }

        if dpi in dpi_map:
            self.combo_dpi.setCurrentIndex(dpi_map[dpi])
        else:
            self.logger.warning(f"DPI {dpi} nicht in DPI_STUFEN vorhanden")

    def _update_summary(self):
        """Aktualisiert Zusammenfassung"""
        total_kopien = sum(item.anzahl_kopien for item in self.zeichen_items)

        self.label_zusammenfassung.setText(
            f"Es werden {len(self.zeichen_items)} Zeichen ({total_kopien} Kopien) exportiert."
        )


    def _on_ordner_waehlen(self):
        """Ordner-Auswahl-Dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Ausgabe-Ordner wählen",
            str(EXPORT_DIR)
        )

        if folder:
            self.line_ausgabe_ordner.setText(folder)
            self.logger.info(f"Ausgabe-Ordner gewählt: {folder}")

    def _on_exportieren(self):
        """Startet Export"""
        # DPI-Anforderungen prüfen (Mindest-DPI + Optimierung)
        if not self._check_dpi_requirements():
            # User hat Export abgebrochen
            return

        # Validierung
        output_dir = Path(self.line_ausgabe_ordner.text())

        if not output_dir.exists():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle("Ordner existiert nicht")
            msg_box.setText(f"Der Ordner existiert nicht:\n{output_dir}\n\nSoll er erstellt werden?")
            btn_ja = msg_box.addButton("Ja", QMessageBox.ButtonRole.YesRole)
            btn_nein = msg_box.addButton("Nein", QMessageBox.ButtonRole.NoRole)
            msg_box.setDefaultButton(btn_ja)
            msg_box.exec()

            if msg_box.clickedButton() == btn_ja:
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Fehler",
                        f"Der Ordner konnte nicht erstellt werden:\n{e}"
                    )
                    return
            else:
                return

        # NEW: Dialog für erneuten Export zurücksetzen
        self.btn_ordner_oeffnen_nach_export.setVisible(False)
        self.btn_abbrechen.setText("Abbrechen")

        # UI für Export vorbereiten
        self.btn_exportieren.setEnabled(False)
        self.btn_ordner_waehlen.setEnabled(False)
        self.combo_format.setEnabled(False)
        self.combo_dpi.setEnabled(False)  # NEW
        self.spin_threads.setEnabled(False)
        self.check_ordner_oeffnen.setEnabled(False)  # NEW
        self.progress_bar.setVisible(True)
        self.label_status.setVisible(True)
        self.progress_bar.setValue(0)

        # NEW: DPI aus ComboBox extrahieren
        dpi_text = self.combo_dpi.currentText()
        dpi = int(dpi_text.split()[0])  # "600 DPI" -> 600

        # NEW v0.8.2: Validierung für Schnittbögen (nur im GUI-Thread!)
        if self.combo_format.currentText() == "PDF - Schnittbogen (A4)":
            from runtime_config import get_config
            config = get_config()

            # Layout-abhängige Dimensionen
            if self.active_layout == "s1":
                zeichen_hoehe_mm = config.s1_zeichen_hoehe_mm
                zeichen_breite_mm = config.s1_zeichen_breite_mm
            else:
                zeichen_hoehe_mm = config.zeichen_hoehe_mm
                zeichen_breite_mm = config.zeichen_breite_mm

            # A4-Dimensionen und Ränder
            margin_h = getattr(self.settings, 'pdf_margin_horizontal_mm', 10.0)
            margin_v = getattr(self.settings, 'pdf_margin_vertical_mm', 10.0)

            # FIXED v0.8.2.1: Prüfe BEIDE Orientierungen (wie automatische Erkennung)
            # Portrait: 210x297mm
            portrait_avail_w = 210.0 - (2 * margin_h)
            portrait_avail_h = 297.0 - (2 * margin_v)
            portrait_fits = (zeichen_breite_mm <= portrait_avail_w and zeichen_hoehe_mm <= portrait_avail_h)

            # Landscape: 297x210mm
            landscape_avail_w = 297.0 - (2 * margin_h)
            landscape_avail_h = 210.0 - (2 * margin_v)
            landscape_fits = (zeichen_breite_mm <= landscape_avail_w and zeichen_hoehe_mm <= landscape_avail_h)

            # Validierung: Mindestens EINE Orientierung muss passen
            if not portrait_fits and not landscape_fits:
                # Welche Orientierung wäre besser gewesen?
                if portrait_fits:
                    orientation_hint = "Hochformat"
                    avail_w, avail_h = portrait_avail_w, portrait_avail_h
                elif landscape_fits:
                    orientation_hint = "Querformat"
                    avail_w, avail_h = landscape_avail_w, landscape_avail_h
                else:
                    # Beide passen nicht - zeige Portrait als Referenz
                    orientation_hint = "Hoch- oder Querformat"
                    avail_w, avail_h = portrait_avail_w, portrait_avail_h

                QMessageBox.warning(
                    self,
                    "Zeichen zu groß für Schnittbogen",
                    f"Die Zeichen ({zeichen_breite_mm:.1f}x{zeichen_hoehe_mm:.1f}mm) sind zu groß für DIN A4 Schnittbögen.\n\n"
                    f"Maximale Größe ({orientation_hint}): {avail_w:.1f}x{avail_h:.1f}mm\n"
                    f"(mit {margin_h:.1f}mm horizontalen und {margin_v:.1f}mm vertikalen Rändern)\n\n"
                    f"Bitte wählen Sie:\n"
                    f"- 'PDF - Einzelzeichen' für größere Zeichen, oder\n"
                    f"- Kleinere Zeichenabmessungen in den Einstellungen, oder\n"
                    f"- Kleinere PDF-Ränder in den Einstellungen"
                )
                # UI zurücksetzen
                self.btn_exportieren.setEnabled(True)
                self.btn_ordner_waehlen.setEnabled(True)
                self.combo_format.setEnabled(True)
                self.combo_dpi.setEnabled(True)
                self.spin_threads.setEnabled(True)
                self.check_ordner_oeffnen.setEnabled(True)
                return
            # Wenn mindestens eine Orientierung passt, weitermachen
            # (PDF-Exporter wählt automatisch die beste Orientierung)

        # Worker-Thread erstellen
        self.worker = ExportWorker(
            zeichen_items=self.zeichen_items,
            output_dir=output_dir,
            output_format=self.combo_format.currentText(),
            num_threads=self.spin_threads.value(),
            draw_cut_lines=self.chk_schnittlinien.isChecked(),  # v7.1: Checkbox statt Settings
            dpi=dpi,  # NEW
            settings=self.settings,
            active_layout=self.active_layout  # NEW: S1 oder S2 Layout
        )

        # Signals verbinden
        self.worker.preparing.connect(self._on_preparing)  # NEW
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)

        # NEW: Sofortiges visuelles Feedback
        self.label_status.setText("Export wird gestartet...")
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(0)  # Indeterminate mode während Vorbereitung

        # Worker starten
        self.logger.info("Starte Export-Worker")
        self.worker.start()

    def _on_preparing(self, status_text: str):
        """Preparing-Update vom Worker (Vorbereitungsphase)"""
        self.label_status.setText(status_text)
        # Progress bar bleibt im indeterminate mode (maximum=0)

    def _on_progress(self, current: int, total: int, zeichen_name: str, status: str):
        """Progress-Update vom Worker"""
        # NEW: Beim ersten Progress-Update zurück in den normalen Modus
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setMaximum(100)

        progress_percent = int((current / total) * 100)
        self.progress_bar.setValue(progress_percent)
        # IMPROVED: Klarere Fortschrittsanzeige mit "Zeichen x von y" und Zeichenname
        self.label_status.setText(f"Zeichen {current} von {total}: {zeichen_name} - {status}")

    def _on_finished(self, successful_count: int, errors: list, actual_output_dir: Path):
        """Export abgeschlossen"""
        # CHANGED: actual_output_dir Parameter hinzugefügt
        self.logger.info(f"Export abgeschlossen: {successful_count} erfolgreich, {len(errors)} Fehler")
        self.actual_output_dir = actual_output_dir  # NEW: Speichern für späteren Zugriff
        self.export_successful = True  # NEW v0.8.2.1: Export war erfolgreich

        # Progress auf 100%
        self.progress_bar.setValue(100)
        self.label_status.setText(f"Export abgeschlossen: {successful_count} Zeichen erstellt")

        # NEW: UI-Elemente wieder aktivieren für weiteren Export
        self.btn_exportieren.setEnabled(True)
        self.btn_ordner_waehlen.setEnabled(True)
        self.combo_format.setEnabled(True)
        self.combo_dpi.setEnabled(True)
        self.spin_threads.setEnabled(True)
        self.check_ordner_oeffnen.setEnabled(True)

        # NEW: Button zum Öffnen des Ordners anzeigen
        self.btn_ordner_oeffnen_nach_export.setVisible(True)
        self.btn_abbrechen.setText("Schließen")  # CHANGED: Button-Text ändern

        # NEW: Fokus wieder auf Exportieren-Button setzen für schnellen Neustart
        self.btn_exportieren.setFocus()

        # Erfolgs-Meldung
        if errors:
            error_text = "\n".join([f"- {zeichen_id}: {msg}" for zeichen_id, msg in errors[:5]])
            if len(errors) > 5:
                error_text += f"\n... und {len(errors) - 5} weitere Fehler"

            QMessageBox.warning(
                self,
                "Export mit Fehlern",
                f"Der Export wurde mit {len(errors)} Fehler(n) abgeschlossen:\n\n{error_text}\n\n"
                f"{successful_count} Zeichen wurden erfolgreich erstellt."
            )
        else:
            # NEW: Unterschiedliche Meldung für PNG und PDF
            # Bei PDF kann successful_count die Anzahl der PDF-Dateien sein (stapelbasiert)
            # Bei PNG ist es die Anzahl der PNG-Dateien
            total_zeichen = sum(item.anzahl_kopien for item in self.zeichen_items)

            if successful_count == total_zeichen:
                # PNG-Export: Alle Zeichen erfolgreich
                message = (
                    f"Der Export wurde erfolgreich abgeschlossen!\n\n"
                    f"{successful_count} Zeichen wurden erstellt."
                )
            else:
                # PDF-Export: successful_count ist Anzahl PDF-Dateien
                message = (
                    f"Der Export wurde erfolgreich abgeschlossen!\n\n"
                    f"{successful_count} PDF-Datei(en) mit insgesamt {total_zeichen} Zeichen wurden erstellt."
                )

            QMessageBox.information(
                self,
                "Export erfolgreich",
                message
            )

        # NEW v0.8.1: Warnung für fehlende Schriftarten anzeigen
        if self.worker.missing_fonts_report_path:
            report_file = self.worker.missing_fonts_report_path
            QMessageBox.warning(
                self,
                "Fehlende Schriftarten",
                f"ACHTUNG: In den SVG-Dateien wurden Schriftarten verwendet,\n"
                f"die auf diesem PC nicht installiert sind!\n\n"
                f"Bitte pruefe die generierten Zeichen!\n\n"
                f"Details findest du in:\n"
                f"{report_file.name}\n\n"
                f"Die Datei befindet sich im Export-Ordner."
            )

        # NEW: Ausgabe-Ordner automatisch öffnen (falls aktiviert)
        if self.check_ordner_oeffnen.isChecked():
            self._on_ordner_oeffnen_nach_export()

    def _on_ordner_oeffnen_nach_export(self):
        """Öffnet Ausgabe-Ordner im Dateimanager (plattformübergreifend)"""
        import subprocess
        import platform

        # CHANGED: Verwende den tatsächlichen Ausgabe-Ordner (mit Zeitstempel-Unterordner)
        output_dir = self.actual_output_dir if self.actual_output_dir else Path(self.line_ausgabe_ordner.text())

        if not output_dir.exists():
            QMessageBox.warning(
                self,
                "Ordner nicht gefunden",
                f"Der Ausgabe-Ordner existiert nicht:\n{output_dir}"
            )
            return

        try:
            # Plattformübergreifend: Windows (primär), Linux (experimentell)
            system = platform.system()

            if system == 'Windows':
                # Windows: Primär unterstütztes System
                subprocess.run(['explorer', str(output_dir)])
            elif system == 'Linux':
                # Linux: Experimentell - wird getestet
                # xdg-open ist Standard auf den meisten Linux-Distributionen
                subprocess.run(['xdg-open', str(output_dir)])
            else:
                # Nicht unterstützte Systeme (z.B. macOS)
                self.logger.warning(f"Nicht unterstütztes Betriebssystem: {system}")
                QMessageBox.information(
                    self,
                    "Nicht unterstützt",
                    f"Ausgabe-Ordner:\n{output_dir}\n\n"
                    f"Das automatische Öffnen wird auf {system} nicht unterstützt.\n"
                    f"Bitte öffne den Ordner manuell."
                )
                return

            self.logger.info(f"Ausgabe-Ordner geöffnet ({system}): {output_dir}")

        except FileNotFoundError:
            # Kommando nicht gefunden (z.B. xdg-open nicht installiert)
            self.logger.warning(f"Dateimanager-Befehl nicht gefunden auf {platform.system()}")
            QMessageBox.information(
                self,
                "Ordner",
                f"Ausgabe-Ordner:\n{output_dir}\n\n"
                f"Bitte öffne den Ordner manuell."
            )
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Ausgabe-Ordners: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Der Ausgabe-Ordner konnte nicht geöffnet werden:\n{e}"
            )

    def _on_error(self, error_message: str):
        """Fehler beim Export"""
        # REMOVED: Doppeltes Logging (wird bereits im Worker-Thread geloggt)
        # self.logger.error(f"Export-Fehler: {error_message}")

        QMessageBox.critical(
            self,
            "Export-Fehler",
            f"Beim Export ist ein Fehler aufgetreten:\n{error_message}"
        )

        # UI zurücksetzen
        self.btn_exportieren.setEnabled(True)
        self.btn_ordner_waehlen.setEnabled(True)
        self.combo_format.setEnabled(True)
        self.spin_threads.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.label_status.setVisible(False)

    def reject(self):
        """Dialog schließen - unterscheidet zwischen Abbruch und normalem Schließen"""
        # NEW v0.8.2.1: Unterscheide zwischen Abbruch und Schließen nach Export
        if self.export_successful:
            self.logger.info("Export-Dialog geschlossen nach erfolgreichem Export")
        else:
            self.logger.info("Export abgebrochen")

        # Dialog schließen
        super().reject()


# ================================================================================================
# TESTING
# ================================================================================================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    # Dummy-Test
    app = QApplication(sys.argv)

    # Dummy-Items erstellen
    from gui.widgets.zeichen_tree_item import create_zeichen_item
    from settings_manager import SettingsManager

    items = [
        create_zeichen_item("test1.svg", Path("test1.svg"), None),
        create_zeichen_item("test2.svg", Path("test2.svg"), None),
    ]
    items[0].set_checked(True)
    items[1].set_checked(True)

    settings = SettingsManager().load_settings()

    dialog = ExportDialog(items, settings)
    dialog.show()
    sys.exit(app.exec())
