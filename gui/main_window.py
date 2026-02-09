#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window.py - Hauptfenster mit tabellarischem Layout

Features:
- Tabellarisches Layout
- Hierarchisches Tree-Widget mit Checkboxen
- Parameter direkt in Tabelle editierbar
- Parameter-Vererbung (Kategorie -> Unterkategorie -> Zeichen)
- Settings-System integriert
- Vorschaubilder optional
"""

import sys
from pathlib import Path
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QMainWindow, QMessageBox, QFileDialog, QDialog,
    QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox, QTreeWidgetItem,
    QTreeWidget, QPushButton, QCheckBox, QLabel, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QObject
from PyQt6.QtGui import QColor, QBrush, QAction, QPixmap, QIcon  # NEW: QPixmap und QIcon fuer Logo/Icon

from logging_manager import LoggingManager
from constants import (
    PROGRAM_NAME, PROGRAM_VERSION, PROGRAM_DESCRIPTION, PROGRAM_AUTHOR, PROGRAM_AUTHOR_EMAIL, DEFAULT_ZEICHEN_DIR,
    VALIDATION_ERROR_BG, VALIDATION_ERROR_FG, VALIDATION_NORMAL_BG, GUI_BATCH_UPDATE_INTERVAL,
    LOGO_PATH, ICON_PATH,
    DEFAULT_ASPECT_LOCKED, DEFAULT_AUTO_ADJUST_GRAFIK_SIZE, DEFAULT_AUTO_ADJUST_FONT_SIZE,
    DEFAULT_S1_LINKS_PROZENT, DEFAULT_S1_ANZAHL_SCHREIBLINIEN, DEFAULT_S1_ASPECT_LOCKED, DEFAULT_S1_STAERKE_ANZEIGEN
)
from settings_manager import SettingsManager, AppSettings
from runtime_config import get_config
from svg_loader_local import SVGLoaderLocal
from gui.ui_loader import UILoader
from gui.widgets.zeichen_tree_item import (
    ZeichenTreeItem, create_category_item, create_subcategory_item, create_zeichen_item
)
from gui.modus_config import (  # NEW: Zentrale Modi-Konfiguration
    get_modus_gui_labels,
    gui_to_internal,
    internal_to_gui,
    get_placeholder_text
)
from validation_manager import ValidationManager  # NEW

class NoScrollWheelFilter(QObject):
    """
    Event-Filter um Scrollrad und Cursor-Tasten für ComboBox/SpinBox zu blockieren

    Verhindert ungewollte Änderungen durch Scrollen oder Pfeiltasten
    """
    def eventFilter(self, a0, a1):  # CHANGED: Parameter-Namen an QObject.eventFilter angepasst
        obj, event = a0, a1  # Lokale Variablen für bessere Lesbarkeit

        # Scrollrad-Event blockieren
        if event.type() == QEvent.Type.Wheel:
            return True  # Event blockieren

        # Cursor-Tasten blockieren (nur wenn Widget keinen Focus hat)
        if event.type() == QEvent.Type.KeyPress and not obj.hasFocus():
            key = event.key()
            if key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
                return True  # Event blockieren

        return False  # Event durchlassen

def filemanager():
    """Dateimanager je nach Plattform auswählen"""
    if sys.platform == 'win32':
        return "explorer"
    elif sys.platform == 'linux':
        return "xdg-open"
    else:
        raise ValueError("unsupported os")

class MainWindow(QMainWindow):
    """
    Hauptfenster - Tabellarisches Layout

    UI-Master: gui/ui_files/main_window.ui

    Features:
    - Hierarchisches Tree-Widget mit Kategorien/Unterkategorien/Zeichen
    - Parameter direkt in Spalten editierbar
    - Parameter-Vererbung von Kategorie nach unten
    - Settings-System fuer Defaults
    - Vorschaubilder optional laden
    """

    # NEW: Modi die Text haben (alle außer ohne_text und schreiblinie_staerke)
    TEXT_MODES = ["ov_staerke", "ort_staerke", "freitext", "dateiname", "ruf"]

    # NEW: Stub-Attribute für .ui-Widgets (Type-Hints für Pylance)
    tree_zeichen: QTreeWidget
    btn_ordner_oeffnen: QPushButton
    btn_neu_laden: QPushButton
    btn_vorlagen_ordner_explorer: QPushButton
    btn_export: QPushButton

    # S2-Layout Zeichen-Abmessungen
    spin_s2_zeichen_hoehe: QDoubleSpinBox
    spin_s2_zeichen_breite: QDoubleSpinBox
    spin_s2_beschnittzugabe: QDoubleSpinBox
    spin_s2_abstand_rand: QDoubleSpinBox
    label_s2_druckgroesse: QLabel  # NOTE: UI-Name ist "druckgroesse", Text ist "Druckgröße"
    label_s2_max_grafikgroesse: QLabel

    # S2-Layout weitere Parameter
    spin_text_bottom_offset: QDoubleSpinBox  # v7.1: Abstand Text-Unterkante
    spin_abstand_grafik_text: QDoubleSpinBox
    # check_schnittlinien: QCheckBox  # v7.1: Entfernt - jetzt im Export-Dialog
    spin_grafik_hoehe: QDoubleSpinBox  # v7.1: Grafik-Höhe
    spin_grafik_breite: QDoubleSpinBox  # v7.1: Grafik-Breite
    combo_grafik_position: QComboBox  # v7.1: Grafik-Position
    btn_apply_max_grafik_size: QPushButton  # NEW: Button für max. Grafikabmessungen
    spin_font_size: QSpinBox  # NEW: Schriftgröße
    btn_apply_recommended_font_size: QPushButton  # NEW: Button für empfohlene Schriftgröße
    label_recommended_font_size: QLabel  # NEW: Label für empfohlene Schriftgröße
    check_auto_font_size: QCheckBox  # NEW: Auto-Anpassung Schriftgröße
    check_auto_grafik_size: QCheckBox  # NEW: Auto-Anpassung Grafikgröße
    check_s2_aspect_locked: QCheckBox  # NEW v0.8.2.4: Seitenverhältnis 1:1 fixieren (S2)
    line_search: QLineEdit
    statusbar: QStatusBar

    # NEW: S1-Layout Controls
    check_s1_aspect_locked: QCheckBox  # Seitenverhältnis 2:1 fixieren
    spin_s1_links_prozent: QSpinBox  # Aufteilung Links-Prozent
    label_s1_links_breite_mm: QLabel  # NEW: Linke Breite in mm (Auto-berechnet)
    label_s1_rechts_prozent_value: QLabel  # Rechts-Prozent (Auto-berechnet)
    spin_s1_anzahl_schreiblinien: QSpinBox  # Anzahl Schreiblinien (3-10)
    label_s1_zeilenhoehe: QLabel  # Zeilenhöhe (Auto-berechnet)
    label_s1_schriftgroesse: QLabel  # Schriftgröße (Auto-berechnet)
    check_s1_staerke_anzeigen: QCheckBox  # Stärke-Platzhalter anzeigen

    # S1-Layout Zeichen-Abmessungen
    spin_s1_zeichen_hoehe: QDoubleSpinBox
    spin_s1_zeichen_breite: QDoubleSpinBox
    spin_s1_beschnittzugabe: QDoubleSpinBox
    spin_s1_abstand_rand: QDoubleSpinBox
    label_s1_druckgroesse: QLabel  # NOTE: UI-Name ist "druckgroesse", Text ist "Druckgröße"

    # S1-Layout weitere Parameter (synchronized with S2)
    spin_s1_font_size: QSpinBox  # Schriftgröße (UNABHÄNGIG von S2 seit v0.8.2.3)
    btn_s1_apply_recommended_font_size: QPushButton  # Button empfohlene Schriftgröße
    label_s1_recommended_font_size: QLabel  # Label empfohlene Schriftgröße
    check_s1_auto_font_size: QCheckBox  # Auto-Anpassung Schriftgröße
    # REMOVED: S1-Grafik-Widgets entfernt (groupBox_s1_grafik geloescht)
    # S1 nutzt automatisch vollen verfuegbaren Bereich basierend auf links_prozent
    spin_s1_abstand_grafik_text: QDoubleSpinBox  # Abstand Grafik<->Text (synchronisiert mit S2)
    spin_s1_text_bottom_offset: QDoubleSpinBox  # Abstand Text-Unterkante (synchronisiert mit S2)

    # Menu-Actions
    action_vorlagen_ordner_oeffnen: QAction
    action_ausgabe_ordner_oeffnen: QAction
    action_neu_laden: QAction
    action_einstellungen: QAction
    action_beenden: QAction
    action_benutzerhandbuch: QAction
    action_logs_oeffnen: QAction
    action_ueber: QAction

    def __init__(self):
        """Initialisiert Hauptfenster"""
        super().__init__()

        self.logger = LoggingManager().get_logger(__name__)

        # NEW: Flag für Batch-Operationen (unterdrückt Einzelwarnungen)
        self._batch_operation_active = False

        # NEW: Flag um mehrfache Warnungen zu verhindern
        self._validation_warning_shown = False
        self._validation_warning_timer = None  # FIXED: Timer um Flag zu resetten

        # FIXED: Flag um Validierung während Initialisierung zu verhindern
        self._initialization_complete = False

        # NEW: Rekursions-Schutz für Font-Size-Validierung
        self._validating_font_size = False

        # NEW: EventFilter für NoScroll
        self.no_scroll_filter = NoScrollWheelFilter()

        self.logger.info("Initialisiere Hauptfenster (tabellarisch)...")

        # UI-Datei laden
        UILoader().load_ui("main_window.ui", self)
        self.setWindowTitle(f"{PROGRAM_NAME} v{PROGRAM_VERSION}")

        # Window-Icon setzen
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))
            self.logger.debug(f"Window-Icon gesetzt: {ICON_PATH}")
        else:
            self.logger.warning(f"Icon nicht gefunden: {ICON_PATH}")

        # Settings-Manager
        self.settings_mgr = SettingsManager()
        self.settings = self.settings_mgr.load_settings()

        # SVG-Loader
        self.svg_loader = SVGLoaderLocal(Path(self.settings.zeichen_ordner))

        # Validation-Manager
        self.validation_mgr = ValidationManager()  # NEW

        # UI initialisieren
        self._init_ui()
        self._connect_signals()
        self._load_settings_to_ui()

        # Standard-Layout beim Start auswählen (NEW v0.8.2)
        if hasattr(self.settings, 'standard_layout'):
            if self.settings.standard_layout == "S1":
                self.tab_layout.setCurrentIndex(1)  # S1-Tab (Index 1)
                self.logger.debug("Standard-Layout: S1-Tab ausgewählt")
            else:
                self.tab_layout.setCurrentIndex(0)  # S2-Tab (Index 0, Default)
                self.logger.debug("Standard-Layout: S2-Tab ausgewählt")
        else:
            # Fallback: S2 (Default)
            self.tab_layout.setCurrentIndex(0)
            self.logger.debug("Standard-Layout: S2-Tab ausgewählt (Fallback)")

        # v7.1: Nach Laden der Settings die maximale Grafikgröße in Settings zurückschreiben
        self._save_ui_to_settings()

        # Druckgröße initial berechnen
        self._update_druckgroesse_label()

        self.logger.info("Hauptfenster initialisiert")

        # Font-Check durchführen
        self._check_font_availability()

        # OPTIMIZED: Kategorien NACH Fenster-Anzeige laden (bessere UX)
        # Verzögerter Start mit QTimer, damit Fenster zuerst sichtbar wird
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._on_neu_laden_delayed)

    def _init_ui(self):
        """Initialisiert UI-Elemente"""
        # Logo neben GroupBox "Zeichen-Abmessungen" hinzufuegen
        self._add_logo_widget()

        # Tree-Widget konfigurieren
        self.tree_zeichen.setColumnWidth(ZeichenTreeItem.COL_NAME, 300)
        self.tree_zeichen.setColumnWidth(ZeichenTreeItem.COL_ANZAHL, 60)
        self.tree_zeichen.setColumnWidth(ZeichenTreeItem.COL_MODUS, 200)  # CHANGED: 150 -> 200 (für "Schreiblinie oder Freitext")
        self.tree_zeichen.setColumnWidth(ZeichenTreeItem.COL_TEXT, 250)
        self.tree_zeichen.setColumnWidth(ZeichenTreeItem.COL_GRAFIK_POS, 150)
        self.tree_zeichen.setColumnWidth(ZeichenTreeItem.COL_GRAFIK_HOEHE, 150)  # CHANGED: 180 -> 150 (Platz für Modus-Spalte)
        self.tree_zeichen.setColumnWidth(ZeichenTreeItem.COL_GRAFIK_BREITE, 150)  # CHANGED: 180 -> 150 (Platz für Modus-Spalte)

        # FIXED: Selection deaktivieren (verhindert blaue Hervorhebung)
        self.tree_zeichen.setSelectionMode(self.tree_zeichen.SelectionMode.NoSelection)

        # NEW: Performance-Optimierungen für Tree-Widget
        self.tree_zeichen.setUniformRowHeights(True)  # Alle Rows gleich hoch -> schnelleres Rendering
        self.tree_zeichen.setSortingEnabled(False)    # Kein Auto-Sort -> verhindert Overhead

        # Grafik-Spalten standardmaessig verstecken
        self.tree_zeichen.setColumnHidden(ZeichenTreeItem.COL_GRAFIK_POS, True)
        self.tree_zeichen.setColumnHidden(ZeichenTreeItem.COL_GRAFIK_HOEHE, True)
        self.tree_zeichen.setColumnHidden(ZeichenTreeItem.COL_GRAFIK_BREITE, True)

        # GUI-Elemente sind jetzt alle in .ui Datei definiert
        self.logger.debug("UI initialisiert")

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

        # Logo auf passende Groesse skalieren (max 100px Hoehe)
        logo_pixmap = logo_pixmap.scaledToHeight(
            100,
            Qt.TransformationMode.SmoothTransformation
        )

        # Logo ins Label setzen (Label ist bereits in .ui-Datei definiert)
        if hasattr(self, 'label_logo'):
            self.label_logo.setPixmap(logo_pixmap)
            self.logger.debug(f"Logo geladen: {LOGO_PATH}")
        else:
            self.logger.warning("label_logo nicht in UI gefunden")

    def _connect_signals(self):
        """Verbindet Signals mit Slots"""
        # Buttons
        self.btn_ordner_oeffnen.clicked.connect(self._on_vorlagen_ordner_oeffnen)  # CHANGED
        self.btn_neu_laden.clicked.connect(self._on_neu_laden)
        self.btn_vorlagen_ordner_explorer.clicked.connect(self._on_vorlagen_ordner_explorer_oeffnen)  # NEW
        self.btn_export.clicked.connect(self._on_export)
        self.btn_save_settings.clicked.connect(self._on_save_settings_clicked)  # NEW
        self.btn_apply_max_grafik_size.clicked.connect(self._on_apply_max_grafik_size)  # NEW: Max. Grafikabmessungen
        self.btn_apply_recommended_font_size.clicked.connect(self._on_apply_recommended_font_size)  # NEW: Empfohlene Schriftgröße übernehmen

        # Settings-Felder (S2-Layout)
        # S2 Zeichenabmessungen
        self.spin_s2_zeichen_hoehe.valueChanged.connect(self._on_s2_aspect_lock)  # FIRST: Aspect-Lock pruefen (MUSS VOR _on_settings_changed!)
        self.spin_s2_zeichen_hoehe.valueChanged.connect(self._on_s2_zeichen_size_changed)
        self.spin_s2_zeichen_hoehe.valueChanged.connect(self._on_settings_changed)
        self.spin_s2_zeichen_hoehe.valueChanged.connect(self._update_recommended_font_size)  # NEW: Empfehlung aktualisieren
        self.spin_s2_zeichen_breite.valueChanged.connect(self._on_s2_zeichen_size_changed)
        self.spin_s2_zeichen_breite.valueChanged.connect(self._on_settings_changed)
        self.spin_s2_beschnittzugabe.valueChanged.connect(self._on_s2_zeichen_size_changed)
        self.spin_s2_beschnittzugabe.valueChanged.connect(self._on_settings_changed)
        self.spin_s2_abstand_rand.valueChanged.connect(self._on_s2_zeichen_size_changed)
        self.spin_s2_abstand_rand.valueChanged.connect(self._on_settings_changed)

        # S2 weitere Parameter
        self.spin_font_size.valueChanged.connect(self._on_settings_changed)  # NEW: Schriftgröße
        self.spin_font_size.valueChanged.connect(self._sync_s2_to_s1_font_size)  # Sync S2->S1
        self.spin_text_bottom_offset.valueChanged.connect(self._on_settings_changed)  # v7.1: Abstand Text-Unterkante
        self.spin_text_bottom_offset.valueChanged.connect(self._sync_s2_to_s1_abstand)  # Sync S2->S1
        self.spin_abstand_grafik_text.valueChanged.connect(self._on_settings_changed)
        self.spin_abstand_grafik_text.valueChanged.connect(self._sync_s2_to_s1_abstand)  # Sync S2->S1
        # self.check_schnittlinien.stateChanged.connect(self._on_settings_changed)  # v7.1: Entfernt - jetzt im Export-Dialog

        # v7.1: Grafik-Felder
        self.spin_grafik_hoehe.valueChanged.connect(self._on_grafik_size_changed)
        # REMOVED: Signal zu _sync_s2_to_s1_grafik_size (S1 hat keine Grafik-Groupbox mehr)
        self.spin_grafik_breite.valueChanged.connect(self._on_grafik_size_changed)
        # REMOVED: Signal zu _sync_s2_to_s1_grafik_size (S1 hat keine Grafik-Groupbox mehr)
        self.combo_grafik_position.currentIndexChanged.connect(self._on_grafik_position_changed)
        # REMOVED: Signal zu _sync_s2_to_s1_grafik_position (S1 hat keine Grafik-Groupbox mehr)

        # NEW: Auto-Adjust Checkboxen
        self.check_auto_grafik_size.stateChanged.connect(self._on_settings_changed)
        # REMOVED v0.8.2.2: Auto-Font-Size Sync entfernt - S1 und S2 sind jetzt unabhängig
        self.check_auto_font_size.stateChanged.connect(self._on_settings_changed)

        # NEW v0.8.2.4: S2 Aspect-Lock Checkbox
        self.check_s2_aspect_locked.stateChanged.connect(self._on_s2_aspect_locked_changed)
        self.check_s2_aspect_locked.stateChanged.connect(self._on_settings_changed)
        self.check_s2_aspect_locked.stateChanged.connect(self._on_s2_aspect_lock)

        # NEW: S1-Layout Controls
        self.check_s1_aspect_locked.stateChanged.connect(self._on_s1_aspect_locked_changed)
        self.check_s1_aspect_locked.stateChanged.connect(self._on_settings_changed)
        self.spin_s1_links_prozent.valueChanged.connect(self._on_s1_links_prozent_changed)
        self.spin_s1_links_prozent.valueChanged.connect(self._on_settings_changed)
        self.spin_s1_anzahl_schreiblinien.valueChanged.connect(self._on_s1_anzahl_schreiblinien_changed)
        self.spin_s1_anzahl_schreiblinien.valueChanged.connect(self._on_settings_changed)
        self.check_s1_staerke_anzeigen.stateChanged.connect(self._on_settings_changed)

        # S1 Zeichenabmessungen
        self.spin_s1_zeichen_hoehe.valueChanged.connect(self._on_s1_aspect_lock)  # FIRST: Aspect-Lock pruefen (MUSS VOR _on_settings_changed!)
        self.spin_s1_zeichen_hoehe.valueChanged.connect(self._on_s1_zeichen_size_changed)
        self.spin_s1_zeichen_hoehe.valueChanged.connect(self._on_settings_changed)
        self.spin_s1_zeichen_hoehe.valueChanged.connect(self._update_recommended_font_size)  # NEW v0.8.2.2: Empfehlung aktualisieren
        self.spin_s1_zeichen_breite.valueChanged.connect(self._on_s1_zeichen_size_changed)
        self.spin_s1_zeichen_breite.valueChanged.connect(self._on_settings_changed)
        self.spin_s1_beschnittzugabe.valueChanged.connect(self._on_s1_zeichen_size_changed)
        self.spin_s1_beschnittzugabe.valueChanged.connect(self._on_settings_changed)
        self.spin_s1_abstand_rand.valueChanged.connect(self._on_s1_zeichen_size_changed)
        self.spin_s1_abstand_rand.valueChanged.connect(self._on_settings_changed)

        # S1 Aspect-Lock Checkbox
        self.check_s1_aspect_locked.stateChanged.connect(self._on_s1_aspect_lock)

        # S1-Zeichen-Parameter (synchronisiert mit S2)
        self.spin_s1_font_size.valueChanged.connect(self._sync_s1_to_s2_font_size)
        self.spin_s1_font_size.valueChanged.connect(self._on_settings_changed)
        self.btn_s1_apply_recommended_font_size.clicked.connect(self._on_apply_recommended_font_size)
        self.check_s1_auto_font_size.stateChanged.connect(self._on_settings_changed)
        # REMOVED v0.8.2.2: Auto-Font-Size Sync entfernt - S1 und S2 sind jetzt unabhängig

        # REMOVED: S1-Grafik-Widgets Signal-Connections entfernt (groupBox_s1_grafik geloescht)
        # S1 nutzt automatisch vollen verfuegbaren Bereich basierend auf links_prozent

        self.spin_s1_abstand_grafik_text.valueChanged.connect(self._sync_s1_to_s2_abstand)
        self.spin_s1_abstand_grafik_text.valueChanged.connect(self._on_settings_changed)
        self.spin_s1_text_bottom_offset.valueChanged.connect(self._sync_s1_to_s2_abstand)
        self.spin_s1_text_bottom_offset.valueChanged.connect(self._on_settings_changed)

        # Menu-Actions
        self.action_vorlagen_ordner_oeffnen.triggered.connect(self._on_vorlagen_ordner_oeffnen)  # CHANGED
        self.action_ausgabe_ordner_oeffnen.triggered.connect(self._on_ausgabe_ordner_oeffnen)  # NEW
        self.action_neu_laden.triggered.connect(self._on_neu_laden)
        self.action_einstellungen.triggered.connect(self._on_einstellungen)
        self.action_beenden.triggered.connect(self.close)
        self.action_benutzerhandbuch.triggered.connect(self._on_benutzerhandbuch)
        self.action_logs_oeffnen.triggered.connect(self._on_logs_oeffnen)
        self.action_ueber.triggered.connect(self._on_ueber)

        # Tree-Widget
        self.tree_zeichen.itemChanged.connect(self._on_item_changed)

        # Suchfeld
        self.line_search.textChanged.connect(self._on_search_text_changed)

        # Tab-Wechsel (NEW v0.8.2.2: Empfohlene Schriftgröße aktualisieren)
        self.tab_layout.currentChanged.connect(self._on_tab_changed)

    def _load_settings_to_ui(self):
        """Laedt Settings in UI-Elemente"""
        # S2-Layout Zeichenabmessungen
        self.spin_s2_zeichen_hoehe.setValue(self.settings.zeichen.zeichen_hoehe_mm)
        self.spin_s2_zeichen_breite.setValue(self.settings.zeichen.zeichen_breite_mm)

        if hasattr(self.settings.zeichen, 'beschnittzugabe_mm'):
            self.spin_s2_beschnittzugabe.setValue(self.settings.zeichen.beschnittzugabe_mm)
        else:
            self.spin_s2_beschnittzugabe.setValue(3.0)  # Default

        if hasattr(self.settings.zeichen, 'sicherheitsabstand_mm'):
            self.spin_s2_abstand_rand.setValue(self.settings.zeichen.sicherheitsabstand_mm)
        else:
            self.spin_s2_abstand_rand.setValue(3.0)  # Default

        # S2-Layout weitere Parameter
        # v7.1: Text-Offsets
        if hasattr(self.settings.zeichen, 'text_bottom_offset_mm'):
            self.spin_text_bottom_offset.setValue(self.settings.zeichen.text_bottom_offset_mm)
        else:
            self.spin_text_bottom_offset.setValue(0.0)  # Default

        self.spin_abstand_grafik_text.setValue(self.settings.zeichen.abstand_grafik_text_mm)

        # NEW: Schriftgröße
        if hasattr(self.settings.zeichen, 'font_size'):
            self.spin_font_size.setValue(self.settings.zeichen.font_size)
        else:
            self.spin_font_size.setValue(10)  # Default

        # NEW: Empfohlene Schriftgröße initial berechnen
        self._update_recommended_font_size()

        # NEW: Auto-Adjust Checkboxen
        if hasattr(self.settings.zeichen, 'auto_adjust_grafik_size'):
            self.check_auto_grafik_size.setChecked(self.settings.zeichen.auto_adjust_grafik_size)
        else:
            self.check_auto_grafik_size.setChecked(DEFAULT_AUTO_ADJUST_GRAFIK_SIZE)

        # CHANGED v0.8.2.2: S2 Auto-Font-Size aus zeichen.auto_adjust_font_size
        if hasattr(self.settings.zeichen, 'auto_adjust_font_size'):
            self.check_auto_font_size.setChecked(self.settings.zeichen.auto_adjust_font_size)
        else:
            self.check_auto_font_size.setChecked(DEFAULT_AUTO_ADJUST_FONT_SIZE)

        # NEW v0.8.2.4: S2 Aspect-Lock laden
        if hasattr(self.settings.zeichen, 'aspect_locked'):
            self.check_s2_aspect_locked.blockSignals(True)
            self.check_s2_aspect_locked.setChecked(self.settings.zeichen.aspect_locked)
            self.check_s2_aspect_locked.blockSignals(False)
        else:
            self.check_s2_aspect_locked.setChecked(DEFAULT_ASPECT_LOCKED)

        # NEW v0.8.4: Aspect-Lock initial anwenden (sperrt Breite-Feld wenn aktiviert)
        self._on_s2_aspect_locked_changed()

        # CHANGED v0.8.2.2: Wende empfohlene Schriftgröße an, wenn Auto aktiviert
        if self.check_auto_font_size.isChecked():
            recommended = self._calculate_recommended_font_size()
            self.spin_font_size.setValue(recommended)
            self.logger.debug(f"S2 Auto-Font-Size beim Start angewendet: {recommended}pt")

        # self.check_schnittlinien.setChecked(self.settings.zeichen.schnittlinien_anzeigen)  # v7.1: Entfernt - jetzt im Export-Dialog

        # v7.1: Grafik-Größe IMMER auf Maximum setzen (User-Request: "bei Programmstart auf max. setzen")
        max_hoehe, max_breite = self._calculate_max_grafik_size()

        # Maximum-Constraints setzen (Validierung)
        self.spin_grafik_hoehe.setMaximum(max_hoehe)
        self.spin_grafik_breite.setMaximum(max_breite)

        # Werte auf Maximum setzen
        self.spin_grafik_hoehe.setValue(max_hoehe)
        self.spin_grafik_breite.setValue(max_breite)

        # Update Label "Max: X x Y mm" in Grafik-GroupBox (initial)
        if hasattr(self, 'label_9'):
            self.label_9.setText(
                f"Max: {max_hoehe:.1f} x {max_breite:.1f} mm (nur Modus 'Nur Grafik')"
            )

        # Position aus Settings laden (falls vorhanden)
        if hasattr(self.settings, 'grafik') and self.settings.grafik:
            position_map = {"oben": 0, "mittig": 1, "unten": 2}
            self.combo_grafik_position.setCurrentIndex(position_map.get(self.settings.grafik.position, 1))
        else:
            self.combo_grafik_position.setCurrentIndex(1)  # mittig als Default

        # NEW: S1-Layout Settings laden
        if hasattr(self.settings, 's1') and self.settings.s1:
            # S1 Zeichenabmessungen ZUERST setzen (bevor aspect_locked!)
            self.spin_s1_zeichen_hoehe.setValue(self.settings.s1.zeichen_hoehe_mm)
            self.spin_s1_zeichen_breite.setValue(self.settings.s1.zeichen_breite_mm)
            self.spin_s1_beschnittzugabe.setValue(self.settings.s1.beschnittzugabe_mm)
            self.spin_s1_abstand_rand.setValue(self.settings.s1.sicherheitsabstand_mm)

            # S1 Doppelschild-Controls
            # CRITICAL: aspect_locked NACH Höhe/Breite setzen, dann manuell anwenden
            self.check_s1_aspect_locked.blockSignals(True)
            self.check_s1_aspect_locked.setChecked(self.settings.s1.aspect_locked)
            self.check_s1_aspect_locked.blockSignals(False)

            self.spin_s1_links_prozent.setValue(self.settings.s1.links_prozent)
            self.spin_s1_anzahl_schreiblinien.setValue(self.settings.s1.anzahl_schreiblinien)
            self.check_s1_staerke_anzeigen.setChecked(self.settings.s1.staerke_anzeigen)

            # NEW v0.8.2.2: S1 Auto-Font-Size aus s1.auto_adjust_font_size laden
            if hasattr(self.settings.s1, 'auto_adjust_font_size'):
                self.check_s1_auto_font_size.setChecked(self.settings.s1.auto_adjust_font_size)
            else:
                self.check_s1_auto_font_size.setChecked(DEFAULT_AUTO_ADJUST_FONT_SIZE)
        else:
            # Defaults (falls s1 nicht in Settings vorhanden)
            # S1 Zeichenabmessungen Defaults ZUERST (wie S2)
            self.spin_s1_zeichen_hoehe.setValue(self.settings.zeichen.zeichen_hoehe_mm)
            self.spin_s1_zeichen_breite.setValue(self.settings.zeichen.zeichen_breite_mm)
            if hasattr(self.settings.zeichen, 'beschnittzugabe_mm'):
                self.spin_s1_beschnittzugabe.setValue(self.settings.zeichen.beschnittzugabe_mm)
            else:
                self.spin_s1_beschnittzugabe.setValue(3.0)
            if hasattr(self.settings.zeichen, 'sicherheitsabstand_mm'):
                self.spin_s1_abstand_rand.setValue(self.settings.zeichen.sicherheitsabstand_mm)
            else:
                self.spin_s1_abstand_rand.setValue(3.0)

            # S1 Doppelschild-Controls
            self.check_s1_aspect_locked.blockSignals(True)
            self.check_s1_aspect_locked.setChecked(DEFAULT_S1_ASPECT_LOCKED)
            self.check_s1_aspect_locked.blockSignals(False)

            self.spin_s1_links_prozent.setValue(DEFAULT_S1_LINKS_PROZENT)
            self.spin_s1_anzahl_schreiblinien.setValue(DEFAULT_S1_ANZAHL_SCHREIBLINIEN)
            self.check_s1_staerke_anzeigen.setChecked(DEFAULT_S1_STAERKE_ANZEIGEN)

            # NEW v0.8.2.2: S1 Auto-Font-Size Default
            self.check_s1_auto_font_size.setChecked(DEFAULT_AUTO_ADJUST_FONT_SIZE)

        # CRITICAL: Aspect-Lock initial anwenden (falls aktiviert)
        self._on_s1_aspect_locked_changed()

        # S1: Auto-Berechnungen initial durchführen
        self._update_s1_rechts_prozent()
        self._update_s1_line_metrics()
        self._update_s1_max_grafik_labels()  # NEW: Max. Grafikgrößen initial berechnen

        # CHANGED v0.8.2.3: S1-Font-Size jetzt UNABHÄNGIG von S2
        # S1 nutzt settings.s1.font_size, S2 nutzt settings.zeichen.font_size
        self.spin_s1_font_size.blockSignals(True)
        if hasattr(self.settings.s1, 'font_size'):
            self.spin_s1_font_size.setValue(self.settings.s1.font_size)
        else:
            self.spin_s1_font_size.setValue(10)  # Default
        self.spin_s1_font_size.blockSignals(False)

        # S1-Parameter-Controls mit S2-Werten synchronisieren (nur Abstände, nicht Font!)
        # Diese Controls teilen sich die selben Einstellungen mit S2
        self.spin_s1_abstand_grafik_text.blockSignals(True)
        self.spin_s1_text_bottom_offset.blockSignals(True)

        self.spin_s1_abstand_grafik_text.setValue(self.spin_abstand_grafik_text.value())
        self.spin_s1_text_bottom_offset.setValue(self.spin_text_bottom_offset.value())

        self.spin_s1_abstand_grafik_text.blockSignals(False)
        self.spin_s1_text_bottom_offset.blockSignals(False)

        # REMOVED v0.8.2.2: Auto-Adjust Checkboxen-Sync entfernt - S1 und S2 sind jetzt unabhängig
        # Die Checkboxen werden separat aus ihren eigenen Settings geladen (siehe oben)

        # CHANGED v0.8.2.2: Wende empfohlene Schriftgröße für S1 an, wenn Auto aktiviert
        if self.check_s1_auto_font_size.isChecked():
            # Wechsle temporär zum S1-Tab für korrekte Berechnung
            current_tab = self.tab_layout.currentIndex()
            self.tab_layout.setCurrentIndex(1)  # S1-Tab
            recommended = self._calculate_recommended_font_size()
            self.spin_s1_font_size.setValue(recommended)
            self.tab_layout.setCurrentIndex(current_tab)  # Zurück zum ursprünglichen Tab
            self.logger.debug(f"S1 Auto-Font-Size beim Start angewendet: {recommended}pt")

    def _calculate_max_grafik_size(self) -> tuple[float, float]:
        """
        Berechnet maximale Grafikgröße basierend auf Zeichengröße

        Formel für "Nur Grafik"-Modus:
        max_grafik = zeichen_größe - (2 * sicherheitsabstand)

        Beispiel: 45mm - (2 × 3mm) = 39mm

        Hinweis: abstand_grafik_text wird NICHT abgezogen, da dieser nur
        für Text-Modi relevant ist (Abstand zwischen Grafik und Text).
        Im "Nur Grafik"-Modus gibt es keinen Text, daher kann die Grafik
        den gesamten sicheren Bereich nutzen.

        Returns:
            tuple: (max_hoehe_mm, max_breite_mm)
        """
        # CHANGED: Direkt S2-Widgets verwenden (aktuellste Werte)
        hoehe = self.spin_s2_zeichen_hoehe.value()

        # FIXED: Wenn Aspect-Lock aktiviert, Breite berechnen
        if self.check_s2_aspect_locked.isChecked():
            breite = hoehe  # 1:1 Verhältnis
        else:
            breite = self.spin_s2_zeichen_breite.value()

        sicherheitsabstand = self.spin_s2_abstand_rand.value()

        max_hoehe = hoehe - (2 * sicherheitsabstand)
        max_breite = breite - (2 * sicherheitsabstand)

        return max_hoehe, max_breite

    def _sync_runtime_config_from_gui(self):
        """
        Synchronisiert RuntimeConfig mit aktuellen GUI-Werten

        Wird aufgerufen vor:
        - Export (damit aktuelle Werte verwendet werden)
        - Speichern (damit Werte persistiert werden)

        Performance-Optimierung: Nicht bei jedem Spin-Change, nur bei Bedarf!
        """
        config = get_config()

        # S2-Layout (fuer normales S2-Layout verwendet)
        config.zeichen_hoehe_mm = self.spin_s2_zeichen_hoehe.value()
        config.zeichen_breite_mm = self.spin_s2_zeichen_breite.value()
        config.beschnittzugabe_mm = self.spin_s2_beschnittzugabe.value()
        config.sicherheitsabstand_mm = self.spin_s2_abstand_rand.value()

        # S2-Layout weitere Parameter
        config.abstand_grafik_text_mm = self.spin_abstand_grafik_text.value()
        config.text_bottom_offset_mm = self.spin_text_bottom_offset.value()
        config.font_size = self.spin_font_size.value()  # NEW: Schriftgröße
        config.aspect_locked = self.check_s2_aspect_locked.isChecked()  # NEW v0.8.2.4: S2 Aspect-Lock

        # S1-Layout (fuer S1-Doppelschild verwendet)
        config.s1_zeichen_hoehe_mm = self.spin_s1_zeichen_hoehe.value()
        config.s1_zeichen_breite_mm = self.spin_s1_zeichen_breite.value()
        config.s1_beschnittzugabe_mm = self.spin_s1_beschnittzugabe.value()
        config.s1_sicherheitsabstand_mm = self.spin_s1_abstand_rand.value()

        # S1-Layout Doppelschild-Parameter
        config.s1_aspect_locked = self.check_s1_aspect_locked.isChecked()
        config.s1_links_prozent = self.spin_s1_links_prozent.value()
        config.s1_anzahl_schreiblinien = self.spin_s1_anzahl_schreiblinien.value()
        config.s1_staerke_anzeigen = self.check_s1_staerke_anzeigen.isChecked()

        self.logger.debug("RuntimeConfig mit GUI-Werten synchronisiert")

    def _get_active_layout(self) -> str:
        """
        Ermittelt das aktuell aktive Layout basierend auf Tab-Auswahl

        Returns:
            str: "s1" wenn S1-Tab aktiv, "s2" wenn S2-Tab aktiv
        """
        # Tab-Index: 0 = S2-Tab, 1 = S1-Tab
        current_tab = self.tab_layout.currentIndex()

        if current_tab == 1:
            return "s1"
        else:
            return "s2"

    def _on_tab_changed(self, index: int):
        """
        Handler für Tab-Wechsel

        NEW v0.8.2.2: Aktualisiert empfohlene Schriftgröße beim Wechsel zwischen S1/S2

        Args:
            index: Tab-Index (0 = S2, 1 = S1)
        """
        # Empfohlene Schriftgröße für das neue Layout aktualisieren
        self._update_recommended_font_size()
        self.logger.debug(f"Tab gewechselt zu Index {index} ({'S1' if index == 1 else 'S2'})")

    def _sync_s2_to_s1_font_size(self):
        """CHANGED v0.8.2.3: Font-Size ist jetzt UNABHÄNGIG zwischen S1 und S2

        S1 nutzt settings.s1.font_size, S2 nutzt settings.zeichen.font_size"""
        pass

    def _sync_s1_to_s2_font_size(self):
        """CHANGED v0.8.2.3: Font-Size ist jetzt UNABHÄNGIG zwischen S1 und S2

        S1 nutzt settings.s1.font_size, S2 nutzt settings.zeichen.font_size"""
        pass

    # REMOVED: _sync_s2_to_s1_grafik_size und _sync_s1_to_s2_grafik_size entfernt
    # (spin_s1_grafik_hoehe/breite geloescht - groupBox_s1_grafik entfernt)

    # REMOVED: _sync_s2_to_s1_grafik_position und _sync_s1_to_s2_grafik_position entfernt
    # (combo_s1_grafik_position geloescht - groupBox_s1_grafik entfernt)

    def _sync_s2_to_s1_abstand(self):
        """
        Synchronisiert Abstaende (Grafik-Text + Text-Bottom) von S2 zu S1

        Wird aufgerufen wenn spin_abstand_grafik_text oder spin_text_bottom_offset (S2) geaendert wird.
        Blockiert Signale von S1 um Endlos-Schleife zu verhindern.
        """
        self.spin_s1_abstand_grafik_text.blockSignals(True)
        self.spin_s1_text_bottom_offset.blockSignals(True)
        self.spin_s1_abstand_grafik_text.setValue(self.spin_abstand_grafik_text.value())
        self.spin_s1_text_bottom_offset.setValue(self.spin_text_bottom_offset.value())
        self.spin_s1_abstand_grafik_text.blockSignals(False)
        self.spin_s1_text_bottom_offset.blockSignals(False)

    def _sync_s1_to_s2_abstand(self):
        """
        Synchronisiert Abstaende (Grafik-Text + Text-Bottom) von S1 zu S2

        Wird aufgerufen wenn spin_s1_abstand_grafik_text oder spin_s1_text_bottom_offset (S1) geaendert wird.
        Blockiert Signale von S2 um Endlos-Schleife zu verhindern.
        """
        self.spin_abstand_grafik_text.blockSignals(True)
        self.spin_text_bottom_offset.blockSignals(True)
        self.spin_abstand_grafik_text.setValue(self.spin_s1_abstand_grafik_text.value())
        self.spin_text_bottom_offset.setValue(self.spin_s1_text_bottom_offset.value())
        self.spin_abstand_grafik_text.blockSignals(False)
        self.spin_text_bottom_offset.blockSignals(False)

    def _sync_s2_to_s1_auto_adjust(self):
        """
        Synchronisiert Auto-Adjust Checkboxen von S2 zu S1

        CHANGED v0.8.2.2: Nur noch auto_adjust_grafik_size wird synchronisiert
        auto_adjust_font_size ist jetzt UNABHÄNGIG zwischen S1 und S2

        Wird aufgerufen wenn check_auto_grafik_size (S2) geaendert wird.
        """
        # REMOVED v0.8.2.2: Font-Size Sync entfernt - S1 und S2 sind jetzt unabhängig
        pass

    def _sync_s1_to_s2_auto_adjust(self):
        """
        Synchronisiert Auto-Adjust Checkboxen von S1 zu S2

        CHANGED v0.8.2.2: Nur noch auto_adjust_grafik_size wird synchronisiert
        auto_adjust_font_size ist jetzt UNABHÄNGIG zwischen S1 und S2

        Wird aufgerufen wenn check_s1_auto_grafik_size (S1) geaendert wird.
        """
        # REMOVED v0.8.2.2: Font-Size Sync entfernt - S1 und S2 sind jetzt unabhängig
        pass

    def _update_druckgroesse_label(self):
        """
        Aktualisiert Druckgrößen-Labels fuer S2 und S1

        CHANGED: Ruft separate S2/S1-Update-Methoden auf
        """
        # S2-Labels aktualisieren (nur wenn _initialization_complete, sonst Fehler)
        if self._initialization_complete:
            self._on_s2_zeichen_size_changed()
            self._on_s1_zeichen_size_changed()
        else:
            # Waehrend Initialisierung: Manuell berechnen
            # S2-Labels
            if hasattr(self, 'spin_s2_zeichen_hoehe'):
                hoehe = self.spin_s2_zeichen_hoehe.value()

                # FIXED: Wenn Aspect-Lock aktiviert, Breite berechnen
                if hasattr(self, 'check_s2_aspect_locked') and self.check_s2_aspect_locked.isChecked():
                    breite = hoehe  # 1:1 Verhältnis
                else:
                    breite = self.spin_s2_zeichen_breite.value()

                beschnitt = self.spin_s2_beschnittzugabe.value()
                druck_hoehe = hoehe + 2 * beschnitt
                druck_breite = breite + 2 * beschnitt

                if hasattr(self, 'label_s2_druckgroesse'):
                    self.label_s2_druckgroesse.setText(
                        f"-> Druckgröße: {druck_hoehe:.1f} x {druck_breite:.1f} mm"
                    )

                abstand = self.spin_s2_abstand_rand.value()
                verf_hoehe = hoehe - 2 * abstand
                verf_breite = breite - 2 * abstand

                if hasattr(self, 'label_s2_max_grafikgroesse'):
                    self.label_s2_max_grafikgroesse.setText(
                        f"-> Verfügbarer Bereich: {verf_hoehe:.1f} x {verf_breite:.1f} mm"
                    )

            # S1-Labels
            if hasattr(self, 'spin_s1_zeichen_hoehe'):
                hoehe = self.spin_s1_zeichen_hoehe.value()
                breite = self.spin_s1_zeichen_breite.value()
                beschnitt = self.spin_s1_beschnittzugabe.value()
                druck_hoehe = hoehe + 2 * beschnitt
                druck_breite = breite + 2 * beschnitt

                if hasattr(self, 'label_s1_druckgroesse'):
                    self.label_s1_druckgroesse.setText(
                        f"-> Druckgröße: {druck_hoehe:.1f} x {druck_breite:.1f} mm"
                    )

                abstand = self.spin_s1_abstand_rand.value()
                verf_hoehe = hoehe - 2 * abstand
                verf_breite = breite - 2 * abstand

                # REMOVED: label_s1_max_grafikgroesse entfernt (groupBox_s1_grafik geloescht)

    def _update_statusbar(self, message: str = None):
        """
        Aktualisiert Statusbar

        Args:
            message: Optional spezifische Nachricht
        """
        if message:
            self.statusbar.showMessage(message)
        else:
            # Standard-Status: Anzahl Kategorien/Zeichen
            total_categories = self.tree_zeichen.topLevelItemCount()
            total_zeichen = self._count_all_zeichen()
            checked_zeichen_list = self._get_all_checked_zeichen()
            checked_zeichen = len(checked_zeichen_list)

            # Kopienanzahl berechnen
            total_kopien = sum(item.anzahl_kopien for item in checked_zeichen_list)

            self.statusbar.showMessage(
                f"{total_categories} Kategorien | "
                f"{total_zeichen} Zeichen | "
                f"{checked_zeichen} ausgewählt | "
                f"{total_kopien} Kopien"
            )

    def _count_all_zeichen(self) -> int:
        """Zaehlt alle Zeichen im Tree"""
        count = 0
        for i in range(self.tree_zeichen.topLevelItemCount()):
            item = self.tree_zeichen.topLevelItem(i)
            if isinstance(item, ZeichenTreeItem):
                count += len(item.get_all_zeichen())
        return count

    def _save_ui_to_settings(self):
        """Speichert UI-Werte in Settings"""
        # S2-Layout (ZeichenSettings)
        self.settings.zeichen.zeichen_hoehe_mm = self.spin_s2_zeichen_hoehe.value()
        self.settings.zeichen.zeichen_breite_mm = self.spin_s2_zeichen_breite.value()
        self.settings.zeichen.beschnittzugabe_mm = self.spin_s2_beschnittzugabe.value()
        self.settings.zeichen.sicherheitsabstand_mm = self.spin_s2_abstand_rand.value()
        self.settings.zeichen.aspect_locked = self.check_s2_aspect_locked.isChecked()  # NEW v0.8.4

        # S2-Layout weitere Parameter
        self.settings.zeichen.text_bottom_offset_mm = self.spin_text_bottom_offset.value()  # v7.1
        self.settings.zeichen.abstand_grafik_text_mm = self.spin_abstand_grafik_text.value()
        # self.settings.zeichen.schnittlinien_anzeigen = self.check_schnittlinien.isChecked()  # v7.1: Entfernt - jetzt im Export-Dialog

        # NEW: Auto-Adjust Checkboxen speichern
        self.settings.zeichen.auto_adjust_grafik_size = self.check_auto_grafik_size.isChecked()
        self.settings.zeichen.auto_adjust_font_size = self.check_auto_font_size.isChecked()

        # v7.1: Grafik-Settings speichern
        if hasattr(self.settings, 'grafik') and self.settings.grafik:
            self.settings.grafik.max_hoehe_mm = self.spin_grafik_hoehe.value()
            self.settings.grafik.max_breite_mm = self.spin_grafik_breite.value()
            position_map = {0: "oben", 1: "mittig", 2: "unten"}
            self.settings.grafik.position = position_map.get(self.combo_grafik_position.currentIndex(), "mittig")

        # NEW: S1-Layout Settings speichern
        if hasattr(self.settings, 's1') and self.settings.s1:
            # S1 Doppelschild-Controls
            self.settings.s1.aspect_locked = self.check_s1_aspect_locked.isChecked()
            self.settings.s1.links_prozent = self.spin_s1_links_prozent.value()
            self.settings.s1.anzahl_schreiblinien = self.spin_s1_anzahl_schreiblinien.value()
            self.settings.s1.staerke_anzeigen = self.check_s1_staerke_anzeigen.isChecked()

            # NEW v0.8.2.2: S1 Auto-Font-Size speichern (getrennt von S2)
            self.settings.s1.auto_adjust_font_size = self.check_s1_auto_font_size.isChecked()

            # NEW v0.8.2.3: S1 Font-Size speichern (getrennt von S2)
            self.settings.s1.font_size = self.spin_s1_font_size.value()
            # Font-Family wird nicht über GUI geändert, bleibt bei "Arial"

            # S1 Zeichenabmessungen
            self.settings.s1.zeichen_hoehe_mm = self.spin_s1_zeichen_hoehe.value()
            self.settings.s1.zeichen_breite_mm = self.spin_s1_zeichen_breite.value()
            self.settings.s1.beschnittzugabe_mm = self.spin_s1_beschnittzugabe.value()
            self.settings.s1.sicherheitsabstand_mm = self.spin_s1_abstand_rand.value()

        # Speichern
        success = self.settings_mgr.save_settings(self.settings)
        if success:
            self.logger.info("Settings gespeichert")
        else:
            self.logger.error("Fehler beim Speichern der Settings")

    def showEvent(self, event):
        """
        Event-Handler wenn Fenster angezeigt wird (v0.8.3)

        Zentriert das Fenster beim ersten Anzeigen.

        Args:
            event: QShowEvent
        """
        super().showEvent(event)

        # Nur beim ersten Anzeigen zentrieren
        if not hasattr(self, '_window_centered'):
            self._center_window()
            self._window_centered = True

    def _center_window(self):
        """
        Zentriert das Fenster auf dem Bildschirm (v0.8.3)

        Verwendet die Screen-Geometrie des primären Bildschirms
        um das Fenster mittig zu positionieren.
        """
        from PyQt6.QtGui import QScreen
        from PyQt6.QtWidgets import QApplication

        # Hole primären Screen
        screen: QScreen = QApplication.primaryScreen()
        if screen is None:
            self.logger.warning("Kein primärer Screen gefunden, Zentrierung übersprungen")
            return

        # Screen-Geometrie (availableGeometry berücksichtigt Taskleiste)
        screen_geometry = screen.availableGeometry()

        # Fenster-Größe (frameGeometry inkl. Rahmen)
        window_geometry = self.frameGeometry()

        # Berechne Zentrum
        center_point = screen_geometry.center()

        # Setze Fenster-Zentrum auf Screen-Zentrum
        window_geometry.moveCenter(center_point)

        # Bewege Fenster an die berechnete Position
        self.move(window_geometry.topLeft())

        self.logger.debug(f"Fenster zentriert auf Position: {window_geometry.topLeft()}")

    def _on_settings_changed(self):
        """Settings wurden geaendert"""
        # FIXED: Settings nur speichern NACH vollständiger Initialisierung
        # Verhindert Überschreiben mit UI-Defaults (45mm) beim Programmstart
        if not self._initialization_complete:
            return

        self._save_ui_to_settings()
        self._update_druckgroesse_label()
        self._update_statusbar()

        # v7.1: Grafik-Validierung entfernt (keine per-Item-Größen mehr)

        # NEW: Validiere alle Textlängen (Canvas-Größe geändert)
        self._validate_all_text_lengths()

        # NEW: Validiere Schriftgröße gegen Zeichengröße
        self._validate_font_size_for_zeichen()

    def _on_grafik_size_changed(self):
        """
        Grafik-Größe wurde geändert (v7.1)
        Validiert gegen Maximum und speichert in Settings und RuntimeConfig
        """
        if not self._initialization_complete:
            return

        # Validierung: Darf Maximum nicht überschreiten
        max_hoehe, max_breite = self._calculate_max_grafik_size()

        hoehe_value = self.spin_grafik_hoehe.value()
        breite_value = self.spin_grafik_breite.value()

        # Werte auf Maximum begrenzen (falls manuell zu groß eingegeben)
        if hoehe_value > max_hoehe:
            self.spin_grafik_hoehe.setValue(max_hoehe)
            hoehe_value = max_hoehe
            self.logger.warning(f"Grafikgröße Höhe auf Maximum begrenzt: {max_hoehe}mm")

        if breite_value > max_breite:
            self.spin_grafik_breite.setValue(max_breite)
            breite_value = max_breite
            self.logger.warning(f"Grafikgröße Breite auf Maximum begrenzt: {max_breite}mm")

        # In Settings speichern
        if hasattr(self.settings, 'grafik') and self.settings.grafik:
            self.settings.grafik.max_hoehe_mm = hoehe_value
            self.settings.grafik.max_breite_mm = breite_value

        # In RuntimeConfig speichern
        config = get_config()
        config.grafik_hoehe_mm = hoehe_value
        config.grafik_breite_mm = breite_value

        self.logger.debug(f"Grafikgröße geändert: {hoehe_value}x{breite_value}mm")

    def _on_grafik_position_changed(self):
        """
        Grafik-Position wurde geändert (v7.1)
        Nur relevant für Modus "Nur Grafik"
        """
        if not self._initialization_complete:
            return

        position_map = {0: "oben", 1: "mittig", 2: "unten"}
        position = position_map.get(self.combo_grafik_position.currentIndex(), "mittig")

        # In Settings speichern
        if hasattr(self.settings, 'grafik') and self.settings.grafik:
            self.settings.grafik.position = position

        # In RuntimeConfig speichern
        config = get_config()
        config.grafik_position = position

        self.logger.debug(f"Grafik-Position geändert: {position}")

    def _on_apply_max_grafik_size(self):
        """
        Übernimmt die maximal möglichen Grafikabmessungen in die Spinboxen

        Button-Handler für "Setze Grafik auf max. Abmessungen"
        Berechnet die maximalen Grafikabmessungen basierend auf der aktuellen
        Zeichengröße und dem Sicherheitsabstand und überträgt diese in die
        Einstellungen.
        """
        # Berechne maximale Grafikabmessungen
        max_hoehe, max_breite = self._calculate_max_grafik_size()

        # Setze Werte in Spinboxen
        # NOTE: Das valueChanged-Signal löst automatisch _on_grafik_size_changed() aus,
        # welches die Werte in Settings und RuntimeConfig speichert
        self.spin_grafik_hoehe.setValue(max_hoehe)
        self.spin_grafik_breite.setValue(max_breite)

        self.logger.info(f"Grafik auf maximale Abmessungen gesetzt: {max_hoehe}x{max_breite}mm")

    def _calculate_recommended_font_size(self) -> int:
        """
        Berechnet die empfohlene Schriftgröße basierend auf der Zeichengröße

        FIXED v0.8.2.2: Berücksichtigt aktives Layout (S1 vs S2)

        Formel: empfohlene_font_size = (zeichen_hoehe_mm / 45.0) * 10
        - 45mm → 10pt (Referenz)
        - 60mm → 13pt
        - 30mm → 7pt
        - 90mm → 20pt
        - 600mm → 133pt
        - 900mm → 200pt

        Returns:
            Empfohlene Schriftgröße in pt (gerundet)
        """
        # FIXED v0.8.2.2: Verwende Zeichenhöhe vom aktiven Layout
        active_layout = self._get_active_layout()

        if active_layout == "s1":
            zeichen_hoehe = self.spin_s1_zeichen_hoehe.value()
        else:
            zeichen_hoehe = self.spin_s2_zeichen_hoehe.value()

        recommended = round((zeichen_hoehe / 45.0) * 10)

        # Begrenzen auf erlaubten Bereich (6-200pt)
        recommended = max(6, min(200, recommended))

        self.logger.debug(f"Empfohlene Schriftgröße für {active_layout.upper()}-Layout: {recommended}pt (Höhe: {zeichen_hoehe}mm)")
        return recommended

    def _update_recommended_font_size(self):
        """
        Aktualisiert das Label mit der empfohlenen Schriftgröße

        FIXED v0.8.2.2: Aktualisiert BEIDE Labels (S2 und S1)

        Wird aufgerufen bei:
        - Änderung der Zeichengröße
        - Initial beim Laden der Settings
        """
        # FIXED v0.8.2.2: Berechne für aktuelles Layout
        recommended = self._calculate_recommended_font_size()

        # FIXED v0.8.2.2: Aktualisiere das Label des aktiven Layouts
        active_layout = self._get_active_layout()

        if active_layout == "s1":
            self.label_s1_recommended_font_size.setText(f"Empfohlen: {recommended} pt")
            self.logger.debug(f"S1 empfohlene Schriftgröße aktualisiert: {recommended}pt")
        else:
            self.label_recommended_font_size.setText(f"Empfohlen: {recommended} pt")
            self.logger.debug(f"S2 empfohlene Schriftgröße aktualisiert: {recommended}pt")

    def _on_apply_recommended_font_size(self):
        """
        Button-Handler: Übernimmt die empfohlene Schriftgröße in die Spinbox

        Wird aufgerufen beim Klick auf den "→" Button
        """
        recommended = self._calculate_recommended_font_size()
        self.spin_font_size.setValue(recommended)
        self.logger.info(f"Empfohlene Schriftgröße übernommen: {recommended}pt")

    def _on_s2_zeichen_size_changed(self):
        """
        S2-Zeichenabmessungen geaendert

        Aktualisiert:
        - label_s2_druckgroesse (zeigt "Druckgröße")
        - label_s2_max_grafikgroesse
        - Auto-Adjust Grafikgroesse (falls aktiviert)
        - Auto-Adjust Schriftgroesse (falls aktiviert)
        """
        if not self._initialization_complete:
            return

        # Berechne Druckgroesse (Zeichengroesse + 2x Beschnittzugabe)
        hoehe = self.spin_s2_zeichen_hoehe.value()

        # FIXED: Wenn Aspect-Lock aktiviert, Breite berechnen
        if self.check_s2_aspect_locked.isChecked():
            breite = hoehe  # 1:1 Verhältnis
        else:
            breite = self.spin_s2_zeichen_breite.value()

        beschnitt = self.spin_s2_beschnittzugabe.value()
        druck_hoehe = hoehe + 2 * beschnitt
        druck_breite = breite + 2 * beschnitt

        # Update Druckgroesse-Label
        if hasattr(self, 'label_s2_druckgroesse'):
            self.label_s2_druckgroesse.setText(
                f"-> Druckgroesse: {druck_hoehe:.1f} x {druck_breite:.1f} mm"
            )

        # Berechne verfuegbaren Bereich (Zeichengroesse - 2x Sicherheitsabstand)
        abstand = self.spin_s2_abstand_rand.value()
        verf_hoehe = hoehe - 2 * abstand
        verf_breite = breite - 2 * abstand

        # Update Max-Grafikgroesse-Label
        if hasattr(self, 'label_s2_max_grafikgroesse'):
            self.label_s2_max_grafikgroesse.setText(
                f"-> Verfügbarer Bereich: {verf_hoehe:.1f} x {verf_breite:.1f} mm"
            )

        # Berechne neues Maximum fuer Grafik-Spinboxen
        max_hoehe = verf_hoehe
        max_breite = verf_breite

        # Update Maximum-Constraints der Spinboxen ZUERST (vor setValue!)
        self.spin_grafik_hoehe.setMaximum(max_hoehe)
        self.spin_grafik_breite.setMaximum(max_breite)

        # Auto-Adjust Grafikgroesse (nur wenn Checkbox aktiv)
        if self.check_auto_grafik_size.isChecked():
            # Setze Spinboxen auf Maximum
            self.spin_grafik_hoehe.setValue(max_hoehe)
            self.spin_grafik_breite.setValue(max_breite)
            self.logger.debug(f"S2 Auto-Adjust Grafik: {max_hoehe}x{max_breite}mm")
        else:
            # Nur Maximum begrenzen (wenn groesser als erlaubt)
            if self.spin_grafik_hoehe.value() > max_hoehe:
                self.spin_grafik_hoehe.setValue(max_hoehe)
            if self.spin_grafik_breite.value() > max_breite:
                self.spin_grafik_breite.setValue(max_breite)

        # Update Label "Max: X x Y mm" in Grafik-GroupBox
        if hasattr(self, 'label_9'):
            self.label_9.setText(
                f"Max: {max_hoehe:.1f} x {max_breite:.1f} mm (nur Modus 'Nur Grafik')"
            )

        # Auto-Adjust Schriftgroesse (nur wenn Checkbox aktiv)
        if self.check_auto_font_size.isChecked():
            recommended = self._calculate_recommended_font_size()
            self.spin_font_size.setValue(recommended)
            self.logger.debug(f"S2 Auto-Adjust Schriftgroesse: {recommended}pt")

    def _on_s1_zeichen_size_changed(self):
        """
        S1-Zeichenabmessungen geaendert

        Aktualisiert:
        - label_s1_druckgroesse (zeigt "Druckgröße")
        """
        if not self._initialization_complete:
            return

        # Berechne Druckgroesse (Zeichengroesse + 2x Beschnittzugabe)
        hoehe = self.spin_s1_zeichen_hoehe.value()
        breite = self.spin_s1_zeichen_breite.value()
        beschnitt = self.spin_s1_beschnittzugabe.value()
        druck_hoehe = hoehe + 2 * beschnitt
        druck_breite = breite + 2 * beschnitt

        # Update Druckgroesse-Label
        if hasattr(self, 'label_s1_druckgroesse'):
            self.label_s1_druckgroesse.setText(
                f"-> Druckgroesse: {druck_hoehe:.1f} x {druck_breite:.1f} mm"
            )

        # CHANGED: Sicherheitsabstand gilt EINMAL fuer das GESAMTE Schild
        # Schritt 1: Verfuegbaren Bereich nach Sicherheitsabstand berechnen
        abstand = self.spin_s1_abstand_rand.value()
        verfuegbar_hoehe = hoehe - 2 * abstand  # z.B. 45 - 6 = 39mm
        verfuegbar_breite = breite - 2 * abstand  # z.B. 90 - 6 = 84mm

        # Schritt 2: Aufteilung Links/Rechts INNERHALB des verfuegbaren Bereichs
        links_prozent = self.spin_s1_links_prozent.value()
        linke_breite_mm = verfuegbar_breite * (links_prozent / 100.0)  # z.B. 84 * 0.5 = 42mm

        # Schritt 3: Grafik nutzt VOLLEN linken Bereich (kein zusaetzlicher Abstand!)
        verf_hoehe = verfuegbar_hoehe  # 39mm
        verf_breite = linke_breite_mm   # 42mm (bei 50%)

        # REMOVED: label_s1_max_grafikgroesse entfernt (groupBox_s1_grafik geloescht)

        # NEW: Labels für maximale Grafikabmessungen aktualisieren
        self._update_s1_max_grafik_labels()

        # CHANGED: Auch Breiten-Anzeige aktualisieren (mm-Werte)
        self._update_s1_rechts_prozent()

        # NEW: Schreiblinien-Metriken aktualisieren (Zeilenhöhe/Schriftgröße neu berechnen)
        self._update_s1_line_metrics()

        # NEW v0.8.2.2: Auto-Adjust Schriftgroesse für S1 (nur wenn Checkbox aktiv)
        if self.check_s1_auto_font_size.isChecked():
            # Wechsle temporär zum S1-Tab für korrekte Berechnung
            current_tab = self.tab_layout.currentIndex()
            self.tab_layout.setCurrentIndex(1)  # S1-Tab
            recommended = self._calculate_recommended_font_size()
            self.spin_s1_font_size.setValue(recommended)
            self.tab_layout.setCurrentIndex(current_tab)  # Zurück zum ursprünglichen Tab
            self.logger.debug(f"S1 Auto-Adjust Schriftgroesse: {recommended}pt")

        self.logger.debug(f"S1 Zeichengroesse geaendert: {hoehe}x{breite}mm (Links: {verf_breite:.1f}mm)")

    def _on_s1_aspect_lock(self):
        """
        S1 Aspect-Lock: Breite automatisch anpassen (Breite = 2 x Hoehe)

        Wird aufgerufen wenn:
        - check_s1_aspect_locked geaendert wird
        - spin_s1_zeichen_hoehe geaendert wird
        """
        if not self.check_s1_aspect_locked.isChecked():
            # Aspect-Lock deaktiviert - nichts tun
            return

        # Berechne Breite = 2 x Hoehe
        hoehe = self.spin_s1_zeichen_hoehe.value()
        breite_berechnet = hoehe * 2.0

        # Setze Breite (blockiere Signale um Endlos-Schleife zu verhindern)
        self.spin_s1_zeichen_breite.blockSignals(True)
        self.spin_s1_zeichen_breite.setValue(breite_berechnet)
        self.spin_s1_zeichen_breite.blockSignals(False)

        self.logger.debug(f"S1 Aspect-Lock: Breite = {breite_berechnet}mm (2 x {hoehe}mm)")

    def _on_s2_aspect_lock(self):
        """
        S2 Aspect-Lock: Breite automatisch anpassen (Breite = Hoehe)

        NEW v0.8.2.4: Analog zu S1, aber mit 1:1 Verhältnis

        Wird aufgerufen wenn:
        - check_s2_aspect_locked geaendert wird
        - spin_s2_zeichen_hoehe geaendert wird
        """
        if not self.check_s2_aspect_locked.isChecked():
            # Aspect-Lock deaktiviert - nichts tun
            return

        # Berechne Breite = Hoehe (1:1 Verhältnis)
        hoehe = self.spin_s2_zeichen_hoehe.value()
        breite_berechnet = hoehe

        # Setze Breite (blockiere Signale um Endlos-Schleife zu verhindern)
        self.spin_s2_zeichen_breite.blockSignals(True)
        self.spin_s2_zeichen_breite.setValue(breite_berechnet)
        self.spin_s2_zeichen_breite.blockSignals(False)

        self.logger.debug(f"S2 Aspect-Lock: Breite = {breite_berechnet}mm (1:1)")

    def _on_save_settings_clicked(self):
        """
        Speichert aktuelle Einstellungen in RuntimeConfig und settings.json

        NEW: Ermöglicht User, Einstellungen manuell zu persistieren
        """
        try:
            # 1. RuntimeConfig mit aktuellen GUI-Werten synchronisieren
            self._sync_runtime_config_from_gui()

            # 2. RuntimeConfig zurück in AppSettings schreiben
            config = get_config()
            config.save_to_settings(self.settings)

            # 3. Settings in Datei speichern
            self.settings_mgr.save_settings(self.settings)

            # 4. Feedback
            self._update_statusbar("Einstellungen gespeichert")
            QMessageBox.information(
                self,
                "Gespeichert",
                "Einstellungen wurden erfolgreich gespeichert."
            )

            self.logger.info("Einstellungen gespeichert via Speichern-Button")

        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Einstellungen konnten nicht gespeichert werden:\n{e}"
            )

    # v7.1: Grafik-Validierungsmethoden entfernt (keine per-Item-Größen mehr)

    def _validate_all_text_lengths(self):
        """
        Validiert alle Textlängen im Tree und markiert zu lange Texte ROT

        Diese Methode wird aufgerufen wenn:
        - Zeichengröße geändert wird
        - Modus für Kategorie/Unterkategorie geändert wird (propagiert zu Kindern)

        Zeigt EINE Warnung für alle ungültigen Texte.
        Nur AKTIVIERTE (gecheckte) Zeichen werden validiert.

        FIXED: Läuft NUR wenn Initialisierung abgeschlossen UND mindestens ein Zeichen aktiviert
        """
        # FIXED: Validierung überspringen wenn Initialisierung noch läuft
        if not self._initialization_complete:
            return

        # FIXED: Validierung überspringen wenn keine Zeichen aktiviert sind
        if not self._has_any_checked_zeichen():
            return

        invalid_items = []
        affected_categories = set()  # NEW: Kategorien mit ungültigen Zeichen

        # Alle Items durchgehen
        for i in range(self.tree_zeichen.topLevelItemCount()):
            top_item = self.tree_zeichen.topLevelItem(i)
            if isinstance(top_item, ZeichenTreeItem):
                invalid, categories = self._validate_text_lengths_recursive(top_item, top_item.name)
                invalid_items.extend(invalid)
                affected_categories.update(categories)

        # Sammel-Warnung ausgeben wenn ungültige Texte gefunden
        if invalid_items:
            self.logger.warning(
                f"Text-Validierung: {len(invalid_items)} Zeichen haben zu lange Texte"
            )
            # NEW: Kategorien/Unterkategorien rot hervorheben
            self._highlight_categories(affected_categories)

            self.validation_mgr.show_batch_text_length_warning(self, invalid_items)
        else:
            self.logger.info("Text-Validierung: Alle Texte gültig")

    def _validate_font_size_for_zeichen(self):
        """
        Validiert ob die aktuelle Schriftgröße für die Zeichengröße geeignet ist

        Diese Methode wird aufgerufen wenn:
        - Schriftgröße geändert wird
        - Zeichengröße geändert wird
        - Sicherheitsabstand geändert wird

        Bei ungültiger Schriftgröße:
        - Warnung anzeigen
        - Schriftgröße auf empfohlenen Wert setzen
        """
        # FIXED: Validierung überspringen wenn Initialisierung noch läuft
        if not self._initialization_complete:
            return

        # Rekursions-Schutz: Verhindert Endlosschleife wenn wir die Spinbox setzen
        if hasattr(self, '_validating_font_size') and self._validating_font_size:
            return

        # Aktuelle Werte aus GUI
        # CHANGED: S2-Widgets verwenden
        font_size = self.spin_font_size.value()
        zeichen_hoehe_mm = self.spin_s2_zeichen_hoehe.value()
        sicherheitsabstand_mm = self.spin_s2_abstand_rand.value()

        # Validierung durchführen
        is_valid, error_msg = self.validation_mgr.validate_font_size(
            font_size=font_size,
            zeichen_hoehe_mm=zeichen_hoehe_mm,
            abstand_rand_mm=sicherheitsabstand_mm
        )

        if not is_valid:
            # Warnung anzeigen
            self.validation_mgr.show_validation_warning(
                parent=self,
                title="Schriftgröße zu groß",
                message=error_msg
            )

            # Schriftgröße auf empfohlenen Wert setzen
            recommended = self._calculate_recommended_font_size()

            # Rekursions-Schutz aktivieren
            self._validating_font_size = True
            try:
                self.spin_font_size.setValue(recommended)
                self.logger.warning(
                    f"Schriftgröße {font_size}pt ungültig, "
                    f"auf Empfehlung {recommended}pt gesetzt"
                )
            finally:
                # Rekursions-Schutz deaktivieren
                self._validating_font_size = False
        else:
            self.logger.debug(f"Schriftgröße {font_size}pt ist gültig")

    def _has_any_checked_zeichen(self) -> bool:
        """
        Prüft ob mindestens ein Zeichen aktiviert ist

        Returns:
            bool: True wenn mindestens ein Zeichen gecheckt ist
        """
        for i in range(self.tree_zeichen.topLevelItemCount()):
            top_item = self.tree_zeichen.topLevelItem(i)
            if isinstance(top_item, ZeichenTreeItem):
                if self._has_checked_zeichen_recursive(top_item):
                    return True
        return False

    def _has_checked_zeichen_recursive(self, item: ZeichenTreeItem) -> bool:
        """
        Prüft rekursiv ob mindestens ein Zeichen gecheckt ist

        Args:
            item: Tree-Item

        Returns:
            bool: True wenn mindestens ein gecheckte Zeichen gefunden
        """
        # Wenn Zeichen: Prüfe Checkbox-Status
        if item.item_type == ZeichenTreeItem.TYPE_ZEICHEN:
            return item.checkState(0) == Qt.CheckState.Checked

        # Für Kategorien: Rekursiv Kinder prüfen
        for i in range(item.childCount()):
            child = item.child(i)
            if isinstance(child, ZeichenTreeItem):
                if self._has_checked_zeichen_recursive(child):
                    return True

        return False

    def _validate_text_lengths_recursive(
        self,
        item: ZeichenTreeItem,
        category_path: str = ""
    ) -> tuple[list[str], set[str]]:
        """
        Validiert Textlängen rekursiv (nur GECHECKTE Zeichen)

        Diese Methode durchläuft den Tree rekursiv und prüft für jedes
        AKTIVE (gecheckte) Zeichen, ob der Text in den sicheren Bereich passt.
        Fehlerhafte Zeilen werden rot markiert, betroffene Kategorien werden
        zur Rückgabe-Liste hinzugefügt.

        Args:
            item: Tree-Item (Kategorie, Unterkategorie oder Zeichen)
            category_path: Pfad der PARENT-Kategorie (ohne aktuelles Item).
                          Beispiel: "Gefahren" oder "Gefahren > Akute"
                          NICHT erweitert mit Zeichen-Namen!

        Returns:
            tuple:
                - list[str]: Namen von Items mit zu langen Texten
                - set[str]: Betroffene Kategorie-Pfade (für Hervorhebung)

        Example:
            invalid, categories = self._validate_text_lengths_recursive(
                top_item, "Gefahren"
            )
        """
        invalid_items = []
        affected_categories = set()

        # FIXED: Nur GECHECKTE Zeichen validieren (nicht alle wie vorher)
        if (item.item_type == ZeichenTreeItem.TYPE_ZEICHEN and
            item.checkState(0) == Qt.CheckState.Checked and  # FIXED: Checkbox-Prüfung hinzugefügt
            item.params.modus in self.TEXT_MODES and
            item.params.text and
            item.widgets):

            # FIXED: font_size aus RuntimeConfig verwenden
            from runtime_config import get_config
            runtime_cfg = get_config()

            # Validiere Text
            is_valid, error_msg = self.validation_mgr.validate_text_length(
                text=item.params.text,
                modus=item.params.modus,
                zeichen_hoehe_mm=self.settings.zeichen.zeichen_hoehe_mm,
                zeichen_breite_mm=self.settings.zeichen.zeichen_breite_mm,
                sicherheitsabstand_mm=self.settings.zeichen.sicherheitsabstand_mm,
                font_size=runtime_cfg.font_size,  # FIXED: Aus RuntimeConfig statt DEFAULT_FONT_SIZE
                item_name=item.name
            )

            if not is_valid:
                # FIXED: GANZE ZEILE rot hinterlegen (nicht nur Text-Widget)
                self._highlight_row(item, error=True)

                # FIXED: Text-Widget mit Farb-Konstanten stylen (statt Magic Values)
                if 'text' in item.widgets:
                    item.widgets['text'].setStyleSheet(
                        f"background-color: {VALIDATION_ERROR_BG}; "
                        f"color: {VALIDATION_ERROR_FG}; "
                        f"font-weight: bold;"
                    )

                # Zur Warnliste hinzufügen (sind bereits alle gecheckt durch obige Prüfung)
                invalid_items.append(item.name)
                # FIXED: Nur Parent-Kategorie hinzufügen (ohne Zeichen-Name)
                if category_path:
                    affected_categories.add(category_path)
            else:
                # FIXED: Normale Farbe zurücksetzen (Zeile + Text)
                self._highlight_row(item, error=False)
                if 'text' in item.widgets:
                    item.widgets['text'].setStyleSheet("")

        # Rekursiv für Kinder
        for i in range(item.childCount()):
            child = item.child(i)
            if isinstance(child, ZeichenTreeItem):
                # FIXED: Pfad nur für Kategorien erweitern, NICHT für Zeichen
                # Grund: category_path soll nur Kategorie-Namen enthalten, nicht Zeichen
                if child.item_type == ZeichenTreeItem.TYPE_ZEICHEN:
                    # Für Zeichen: Aktuellen Kategorie-Pfad beibehalten (nicht erweitern)
                    child_path = category_path
                else:
                    # Für Kategorien/Unterkategorien: Pfad erweitern
                    child_path = f"{category_path} > {child.name}" if category_path else child.name

                invalid, categories = self._validate_text_lengths_recursive(child, child_path)
                invalid_items.extend(invalid)
                affected_categories.update(categories)

        return invalid_items, affected_categories

    def _highlight_row(self, item: ZeichenTreeItem, error: bool):
        """
        Hebt GANZE Zeile eines Zeichens farblich hervor

        WICHTIG: Styles alle Widgets (QComboBox, QSpinBox, QDoubleSpinBox)
        inklusive Sub-Controls (up-button, down-button, drop-down), da
        setBackground() nicht für Widget-Spalten funktioniert.

        Args:
            item: Zeichen-Item das hervorgehoben werden soll
            error: True = Rot hinterlegen (Fehler), False = Normal (weiß)

        Example:
            # Zeile rot markieren bei Validierungsfehler
            self._highlight_row(zeichen_item, error=True)

            # Zeile zurücksetzen bei gültigem Text
            self._highlight_row(zeichen_item, error=False)
        """
        # FIXED: Farb-Konstanten verwenden statt Magic Values
        if error:
            bg_color = VALIDATION_ERROR_BG  # Helles Rot für Fehler
            bg_brush = QBrush(QColor(bg_color))
        else:
            bg_color = VALIDATION_NORMAL_BG  # Normaler Hintergrund (weiß)
            bg_brush = QBrush(QColor(Qt.GlobalColor.white))

        # Spalten mit setBackground() färben (funktioniert für Spalten OHNE Widgets)
        for col in range(self.tree_zeichen.columnCount()):
            item.setBackground(col, bg_brush)

        # FIXED: Zeichenname (Spalte 0) auch rot + fett machen
        if error:
            item.setForeground(0, QBrush(QColor(VALIDATION_ERROR_FG)))  # Rot
            # Fettschrift für Zeichenname
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        else:
            item.setForeground(0, QBrush(QColor(Qt.GlobalColor.black)))  # Normal schwarz
            # Normale Schrift
            font = item.font(0)
            font.setBold(False)
            item.setFont(0, font)

        # FIXED: Widgets direkt stylen (setBackground funktioniert nicht für Widget-Spalten)
        # Alle Sub-Controls müssen explizit gestylt werden (up/down buttons, drop-down)
        if item.widgets:
            # FIXED: Kopien-SpinBox mit allen Sub-Controls stylen
            if 'kopien' in item.widgets:
                if error:
                    item.widgets['kopien'].setStyleSheet(
                        f"QSpinBox {{ background-color: {bg_color}; }} "
                        f"QSpinBox::up-button {{ background-color: {bg_color}; }} "
                        f"QSpinBox::down-button {{ background-color: {bg_color}; }}"
                    )
                else:
                    item.widgets['kopien'].setStyleSheet("")  # Reset auf Default

            # FIXED: Modus-ComboBox mit Drop-Down-Button stylen
            if 'modus' in item.widgets:
                if error:
                    item.widgets['modus'].setStyleSheet(
                        f"QComboBox {{ background-color: {bg_color}; }} "
                        f"QComboBox::drop-down {{ background-color: {bg_color}; }}"
                    )
                else:
                    item.widgets['modus'].setStyleSheet("")  # Reset auf Default

            # NOTE: Text-Widget behält seine eigene Farbe (rot/fett bei Fehler)
            # Wird separat in Validierung gesetzt (_validate_text_lengths_recursive)

            # v7.1: Grafik-Widget-Styling entfernt (keine per-Item-Grafik-Widgets mehr)

    def _highlight_categories(self, category_paths: set[str]):
        """
        Hebt Kategorien/Unterkategorien rot hervor (GANZE Zeile + Name)

        Diese Methode färbt die Kategorie-Zeilen UND Namen rot + fett,
        wenn mindestens ein Kind-Zeichen einen Validierungsfehler hat.
        ACHTUNG: Jetzt wird die GANZE Zeile rot hinterlegt, nicht nur der Name!

        FIXED: Aktualisiert NUR die betroffenen Kategorien statt ALLE zurückzusetzen.
        Kategorien die NICHT betroffen sind, werden zurückgesetzt.

        Args:
            category_paths: Set von Kategorie-Pfaden.
                           Beispiel: {"Gefahren", "Gefahren > Akute"}
                           Format: "TopLevel" oder "TopLevel > SubLevel"

        Example:
            affected = {"Gefahren", "Fahrzeuge > Einsatzfahrzeuge"}
            self._highlight_categories(affected)  # Färbt Zeilen + Namen rot
        """
        # FIXED: Intelligentes Update statt komplettes Reset
        # Gehe durch ALLE Kategorien und aktualisiere gezielt
        for i in range(self.tree_zeichen.topLevelItemCount()):
            top_item = self.tree_zeichen.topLevelItem(i)
            if isinstance(top_item, ZeichenTreeItem):
                self._update_category_highlight_recursive(top_item, "", category_paths)

    def _update_category_highlight_recursive(
        self,
        item: ZeichenTreeItem,
        parent_path: str,
        affected_paths: set[str]
    ):
        """
        Aktualisiert Kategorie-Hervorhebung rekursiv und intelligent

        Prüft für jede Kategorie, ob sie betroffen ist (im affected_paths Set).
        Wenn ja: rot färben. Wenn nein: zurücksetzen.

        FIXED: Verhindert fälschliches Zurücksetzen von Kategorien die noch
        invalide Zeichen haben.

        Args:
            item: Aktuelles Tree-Item
            parent_path: Pfad des Parents (z.B. "Gefahren")
            affected_paths: Set der betroffenen Kategorie-Pfade

        Example:
            affected = {"Gefahren", "Fahrzeuge > Einsatzfahrzeuge"}
            self._update_category_highlight_recursive(top_item, "", affected)
        """
        # Nur Kategorien/Unterkategorien behandeln (keine Zeichen)
        if item.item_type == ZeichenTreeItem.TYPE_ZEICHEN:
            return

        # Aktuellen Pfad bauen
        current_path = f"{parent_path} > {item.name}" if parent_path else item.name

        # Prüfen ob diese Kategorie betroffen ist
        if current_path in affected_paths:
            # ROT färben
            item.setForeground(0, QBrush(QColor(VALIDATION_ERROR_FG)))
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

            # Ganze Zeile rot hinterlegen
            bg_brush = QBrush(QColor(VALIDATION_ERROR_BG))
            for col in range(self.tree_zeichen.columnCount()):
                item.setBackground(col, bg_brush)
        else:
            # ZURÜCKSETZEN (normale Farbe)
            item.setForeground(0, QBrush(QColor(Qt.GlobalColor.black)))
            font = item.font(0)
            font.setBold(False)
            item.setFont(0, font)

            # Ganze Zeile weiß hinterlegen
            for col in range(self.tree_zeichen.columnCount()):
                item.setBackground(col, QBrush(QColor(Qt.GlobalColor.white)))

        # Rekursiv für Kinder
        for i in range(item.childCount()):
            child = item.child(i)
            if isinstance(child, ZeichenTreeItem):
                self._update_category_highlight_recursive(child, current_path, affected_paths)

    def _reset_all_category_highlights(self):
        """Setzt Hervorhebung aller Kategorien/Unterkategorien zurück"""
        for i in range(self.tree_zeichen.topLevelItemCount()):
            top_item = self.tree_zeichen.topLevelItem(i)
            if isinstance(top_item, ZeichenTreeItem):
                self._reset_category_highlight_recursive(top_item)

    def _reset_category_highlight_recursive(self, item: ZeichenTreeItem):
        """Setzt Hervorhebung rekursiv zurück (Zeile + Name)"""
        # Nur Kategorien/Unterkategorien
        if item.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
            # FIXED: Name zurücksetzen (schwarz, normale Schrift)
            item.setForeground(0, QBrush(QColor(Qt.GlobalColor.black)))
            font = item.font(0)
            font.setBold(False)
            item.setFont(0, font)

            # FIXED: Ganze Zeile zurücksetzen (weiße Hintergrundfarbe)
            for col in range(item.treeWidget().columnCount()):
                item.setBackground(col, QBrush(QColor(Qt.GlobalColor.white)))

        # Rekursiv
        for i in range(item.childCount()):
            child = item.child(i)
            if isinstance(child, ZeichenTreeItem):
                self._reset_category_highlight_recursive(child)

    def _highlight_category_by_path(self, path: str):
        """
        Hebt Kategorie anhand Pfad rot hervor

        Sucht die Kategorie anhand des Pfades und färbt sie rot.
        Unterstützt verschachtelte Pfade (TopLevel > SubLevel).

        Args:
            path: Kategorie-Pfad mit ">" als Trenner.
                 Beispiel: "Gefahren" oder "Gefahren > Akute"

        Example:
            self._highlight_category_by_path("Gefahren > Akute")
        """
        parts = [p.strip() for p in path.split(">")]
        if not parts:
            return

        # Erste Ebene suchen (Top-Level Kategorie)
        for i in range(self.tree_zeichen.topLevelItemCount()):
            top_item = self.tree_zeichen.topLevelItem(i)
            if isinstance(top_item, ZeichenTreeItem) and top_item.name == parts[0]:
                # FIXED: Kategorie-Name rot + fett
                top_item.setForeground(0, QBrush(QColor(VALIDATION_ERROR_FG)))
                font = top_item.font(0)
                font.setBold(True)
                top_item.setFont(0, font)

                # FIXED: Ganze Kategorie-Zeile rot hinterlegen
                bg_brush = QBrush(QColor(VALIDATION_ERROR_BG))
                for col in range(self.tree_zeichen.columnCount()):
                    top_item.setBackground(col, bg_brush)

                # Wenn Pfad länger, rekursiv in Kinder gehen
                if len(parts) > 1:
                    self._highlight_child_by_path(top_item, parts[1:])
                break

    def _highlight_child_by_path(self, parent: ZeichenTreeItem, parts: list[str]):
        """
        Rekursive Suche und Hervorhebung in Kindern

        Helper-Methode für _highlight_category_by_path. Durchsucht
        Kinder rekursiv und färbt gefundene Kategorien rot.

        Args:
            parent: Parent-Item in dem gesucht wird
            parts: Restliche Pfad-Teile als Liste

        Example:
            self._highlight_child_by_path(top_item, ["Akute", "Explosiv"])
        """
        if not parts:
            return

        for i in range(parent.childCount()):
            child = parent.child(i)
            if isinstance(child, ZeichenTreeItem) and child.name == parts[0]:
                # FIXED: Unterkategorie-Name rot + fett
                child.setForeground(0, QBrush(QColor(VALIDATION_ERROR_FG)))
                font = child.font(0)
                font.setBold(True)
                child.setFont(0, font)

                # FIXED: Ganze Unterkategorie-Zeile rot hinterlegen
                bg_brush = QBrush(QColor(VALIDATION_ERROR_BG))
                tree_widget = child.treeWidget()
                if tree_widget:
                    for col in range(tree_widget.columnCount()):
                        child.setBackground(col, bg_brush)

                # Wenn noch mehr Teile, weiter rekursiv
                if len(parts) > 1:
                    self._highlight_child_by_path(child, parts[1:])
                break

    def _validate_single_zeichen(self, item: ZeichenTreeItem):
        """
        Validiert einzelnes Zeichen und hebt Kategorien hervor

        Diese Methode wird aufgerufen wenn ein EINZELNES Zeichen aktiviert wird.
        Sie validiert das Zeichen, markiert es rot falls invalid, hebt die
        Kategorie-Hierarchie hervor und zeigt EINE Warnung.

        Args:
            item: Zeichen-Item das validiert werden soll
        """
        # FIXED: Validierung überspringen wenn Initialisierung noch läuft
        if not self._initialization_complete:
            return

        # Nur validieren wenn Text-Modus und Text vorhanden
        if item.params.modus not in self.TEXT_MODES or not item.params.text:
            return

        # FIXED: font_size aus RuntimeConfig verwenden
        from runtime_config import get_config
        runtime_cfg = get_config()

        # Validierung durchführen
        is_valid, error_msg = self.validation_mgr.validate_text_length(
            text=item.params.text,
            modus=item.params.modus,
            zeichen_hoehe_mm=self.settings.zeichen.zeichen_hoehe_mm,
            zeichen_breite_mm=self.settings.zeichen.zeichen_breite_mm,
            sicherheitsabstand_mm=self.settings.zeichen.sicherheitsabstand_mm,
            font_size=runtime_cfg.font_size,  # FIXED: Aus RuntimeConfig statt DEFAULT_FONT_SIZE
            item_name=item.name
        )

        if not is_valid:
            self.logger.warning(f"Einzelzeichen-Validierung: '{item.name}' hat zu langen Text")

            # Zeile rot hervorheben
            self._highlight_row(item, error=True)
            if 'text' in item.widgets:
                item.widgets['text'].setStyleSheet(
                    f"background-color: {VALIDATION_ERROR_BG}; "
                    f"color: {VALIDATION_ERROR_FG}; "
                    f"font-weight: bold;"
                )

            # FIXED: Kategorie-Pfad ermitteln und ALLE Ebenen hervorheben
            category_path = self._get_category_path_for_zeichen(item)
            if category_path:
                # FIXED: Alle Ebenen im Pfad hervorheben (z.B. "A", "A > B", "A > B > C")
                all_category_paths = self._get_all_category_levels(category_path)
                self._highlight_categories(all_category_paths)

            # FIXED: NUR EINE Warnung zeigen (Flag verhindert weitere)
            if not self._validation_warning_shown:
                self._validation_warning_shown = True
                self.validation_mgr.show_validation_warning(
                    self,
                    "Text überschreitet Canvas",
                    error_msg + "\n\nDer Text wurde ROT markiert.\nBitte kürze den Text!"
                )
                # FIXED: Flag mit Timer zurücksetzen (500ms Debounce)
                self._reset_validation_warning_flag_delayed()
        else:
            self.logger.info(f"Einzelzeichen-Validierung: '{item.name}' Text ist gültig")
            # Zeile zurücksetzen
            self._highlight_row(item, error=False)
            if 'text' in item.widgets:
                item.widgets['text'].setStyleSheet("")

            # FIXED: Kategorien-Hervorhebung neu berechnen OHNE Warnung
            # (Falls andere Zeichen in dieser Kategorie noch invalid sind)
            category_path = self._get_category_path_for_zeichen(item)
            if category_path:
                # Prüfe ob noch andere invalide Zeichen in dieser Kategorie existieren
                has_invalid = self._has_invalid_zeichen_in_category(category_path)
                if not has_invalid:
                    # Keine invaliden Zeichen mehr -> Kategorie zurücksetzen
                    self._highlight_categories(set())

    def _get_category_path_for_zeichen(self, item: ZeichenTreeItem) -> str:
        """
        Ermittelt Kategorie-Pfad für ein Zeichen

        Args:
            item: Zeichen-Item

        Returns:
            str: Kategorie-Pfad (z.B. "Gefahren > Akute" oder "Gefahren")
                 Leerer String wenn keine Kategorie
        """
        parts = []
        current = item.parent()

        while current is not None:
            if isinstance(current, ZeichenTreeItem):
                parts.insert(0, current.name)
            current = current.parent()

        return " > ".join(parts) if parts else ""

    def _get_all_category_levels(self, category_path: str) -> set[str]:
        """
        Ermittelt ALLE Kategorie-Ebenen für einen Pfad

        Beispiel:
            Input:  "Jonas Köritz > Einrichtungen > Feuerwehr"
            Output: {"Jonas Köritz",
                     "Jonas Köritz > Einrichtungen",
                     "Jonas Köritz > Einrichtungen > Feuerwehr"}

        Args:
            category_path: Vollständiger Kategorie-Pfad

        Returns:
            set[str]: Set aller Kategorie-Ebenen (inkl. aller Parent-Ebenen)
        """
        if not category_path:
            return set()

        parts = [p.strip() for p in category_path.split(">")]
        all_levels = set()

        # Baue alle Ebenen auf
        current_path = ""
        for i, part in enumerate(parts):
            if i == 0:
                current_path = part
            else:
                current_path += f" > {part}"
            all_levels.add(current_path)

        return all_levels

    def _has_invalid_zeichen_in_category(self, category_path: str) -> bool:
        """
        Prüft ob in einer Kategorie noch invalide Zeichen existieren

        Args:
            category_path: Kategorie-Pfad (z.B. "Gefahren > Akute")

        Returns:
            bool: True wenn mindestens ein invalides Zeichen existiert
        """
        # Alle Top-Level Items durchgehen
        for i in range(self.tree_zeichen.topLevelItemCount()):
            top_item = self.tree_zeichen.topLevelItem(i)
            if isinstance(top_item, ZeichenTreeItem):
                if self._has_invalid_zeichen_recursive(top_item, top_item.name, category_path):
                    return True
        return False

    def _has_invalid_zeichen_recursive(
        self,
        item: ZeichenTreeItem,
        current_path: str,
        target_path: str
    ) -> bool:
        """
        Rekursive Suche nach invaliden Zeichen in Kategorie

        Args:
            item: Aktuelles Item
            current_path: Aktueller Pfad
            target_path: Gesuchter Kategorie-Pfad

        Returns:
            bool: True wenn invalides Zeichen gefunden
        """
        # Wenn Zeichen: Prüfe ob invalid und in der richtigen Kategorie
        if item.item_type == ZeichenTreeItem.TYPE_ZEICHEN:
            # Kategorie des Zeichens ermitteln
            zeichen_category = self._get_category_path_for_zeichen(item)
            if zeichen_category == target_path:
                # Prüfe ob Zeichen aktiviert und invalid
                if (item.checkState(0) == Qt.CheckState.Checked and
                    item.params.modus in self.TEXT_MODES and
                    item.params.text):
                    # FIXED: font_size aus RuntimeConfig verwenden
                    from runtime_config import get_config
                    runtime_cfg = get_config()

                    # Validiere
                    is_valid, _ = self.validation_mgr.validate_text_length(
                        text=item.params.text,
                        modus=item.params.modus,
                        zeichen_hoehe_mm=self.settings.zeichen.zeichen_hoehe_mm,
                        zeichen_breite_mm=self.settings.zeichen.zeichen_breite_mm,
                        sicherheitsabstand_mm=self.settings.zeichen.sicherheitsabstand_mm,
                        font_size=runtime_cfg.font_size,  # FIXED: Aus RuntimeConfig statt DEFAULT_FONT_SIZE
                        item_name=item.name
                    )
                    if not is_valid:
                        return True
            return False

        # Für Kategorien: Rekursiv in Kinder gehen
        for i in range(item.childCount()):
            child = item.child(i)
            if isinstance(child, ZeichenTreeItem):
                child_path = f"{current_path} > {child.name}" if child.item_type != ZeichenTreeItem.TYPE_ZEICHEN else current_path
                if self._has_invalid_zeichen_recursive(child, child_path, target_path):
                    return True

        return False

    def _reset_validation_warning_flag_delayed(self):
        """
        Setzt das Warnungs-Flag mit Verzögerung zurück

        Verhindert mehrfache Warnungen wenn mehrere Events fast gleichzeitig kommen.
        Das Flag wird nach 500ms zurückgesetzt.
        """
        # Stoppe bestehenden Timer falls vorhanden
        if self._validation_warning_timer is not None:
            self._validation_warning_timer.stop()
            self._validation_warning_timer = None

        # Starte neuen Timer (500ms)
        self._validation_warning_timer = QTimer()
        self._validation_warning_timer.setSingleShot(True)
        self._validation_warning_timer.timeout.connect(self._reset_validation_warning_flag)
        self._validation_warning_timer.start(500)  # 500ms Debounce

    def _reset_validation_warning_flag(self):
        """Setzt das Warnungs-Flag zurück (wird von Timer aufgerufen)"""
        self._validation_warning_shown = False
        self._validation_warning_timer = None

    def _reset_validation_highlight(self, item: ZeichenTreeItem):
        """
        Setzt Validierungs-Hervorhebung für ein Zeichen zurück

        Args:
            item: Zeichen-Item
        """
        # Zeilen-Hintergrund zurücksetzen
        self._highlight_row(item, error=False)

        # Text-Widget zurücksetzen
        if 'text' in item.widgets:
            item.widgets['text'].setStyleSheet("")

    def _apply_dateiname_to_children(self, item: ZeichenTreeItem):
        """
        Befüllt rekursiv alle Kinder mit Dateiname-Modus mit Text aus Dateinamen

        Args:
            item: Tree-Item (Kategorie oder Unterkategorie)
        """
        for i in range(item.childCount()):
            child = item.child(i)
            if isinstance(child, ZeichenTreeItem):
                # Für Zeichen: Text aus Dateiname setzen
                if (child.item_type == ZeichenTreeItem.TYPE_ZEICHEN and
                    child.params.modus == "dateiname"):

                    # Dateiname als Text
                    filename = child.svg_path.stem if hasattr(child, 'svg_path') and child.svg_path else child.name
                    if filename.endswith('.svg'):
                        filename = filename[:-4]
                    text = filename.replace("_", " ")

                    # Text setzen (OHNE Einzelvalidierung - das passiert später in Batch)
                    child.params.text = text
                    if 'text' in child.widgets:
                        # FIXED: Signale blockieren um Einzel-Validierung zu vermeiden
                        child.widgets['text'].blockSignals(True)
                        child.widgets['text'].setText(text)
                        child.widgets['text'].blockSignals(False)

                # Rekursiv für Unterkategorien
                if child.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
                    self._apply_dateiname_to_children(child)

    def _on_vorlagen_ordner_oeffnen(self):
        """Vorlagen-Ordner oeffnen Dialog"""
        # CHANGED: Umbenannt von _on_ordner_oeffnen
        # Start-Verzeichnis: Zuletzt ausgewählter Ordner oder DEFAULT_ZEICHEN_DIR
        start_dir = self.settings.zeichen_ordner if self.settings.zeichen_ordner else str(DEFAULT_ZEICHEN_DIR)

        folder = QFileDialog.getExistingDirectory(
            self,
            "Vorlagen-Ordner waehlen",
            start_dir
        )

        if folder:
            self._update_statusbar(f"Öffne Ordner: {folder}")
            self.svg_loader = SVGLoaderLocal(Path(folder))
            self.settings.zeichen_ordner = folder
            self.settings_mgr.save_settings(self.settings)
            self._on_neu_laden()
        else:
            self._update_statusbar("Ordner-Auswahl abgebrochen")

    def _on_ausgabe_ordner_oeffnen(self):
        """Oeffnet Ausgabe-Ordner im Dateimanager"""
        # NEW: Ausgabe-Ordner im Dateimanager öffnen
        import subprocess
        from constants import EXPORT_DIR

        if not EXPORT_DIR.exists():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle("Ordner existiert nicht")
            msg_box.setText(f"Der Ausgabe-Ordner existiert nicht:\n{EXPORT_DIR}\n\nSoll er erstellt werden?")
            btn_ja = msg_box.addButton("Ja", QMessageBox.ButtonRole.YesRole)
            btn_nein = msg_box.addButton("Nein", QMessageBox.ButtonRole.NoRole)
            msg_box.setDefaultButton(btn_ja)
            msg_box.exec()

            if msg_box.clickedButton() == btn_ja:
                try:
                    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Fehler",
                        f"Der Ordner konnte nicht erstellt werden:\n{e}"
                    )
                    return
            else:
                return

        try:
            # Dateimanager öffnen
            subprocess.run([filemanager(), str(EXPORT_DIR)])
            self.logger.info(f"Ausgabe-Ordner geöffnet: {EXPORT_DIR}")
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Ausgabe-Ordners: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Der Ausgabe-Ordner konnte nicht geöffnet werden:\n{e}"
            )

    def _check_font_availability(self):
        """
        Prüft Verfügbarkeit der Standard-Schriftart

        Zeigt Warnung an, wenn konfigurierte Schriftart nicht verfügbar ist
        """
        from font_manager import FontManager

        # FIXED: font_family aus RuntimeConfig verwenden
        runtime_cfg = get_config()

        font_mgr = FontManager()
        actual_font, needs_warning = font_mgr.check_and_get_font(runtime_cfg.font_family)

        if needs_warning:
            self.logger.warning(f"Schriftart '{runtime_cfg.font_family}' nicht verfügbar! Verwende '{actual_font}'")

            # Warnung anzeigen (nach GUI-Initialisierung)
            QTimer.singleShot(500, lambda: self._show_font_warning(runtime_cfg.font_family, font_mgr))
        else:
            self.logger.info(f"Schriftart '{runtime_cfg.font_family}' verfügbar")

    def _show_font_warning(self, font_name: str, font_mgr):
        """
        Zeigt Font-Warnung als MessageBox

        Args:
            font_name: Name der fehlenden Schriftart
            font_mgr: FontManager-Instanz
        """
        warning_text = font_mgr.get_font_warning_message(font_name)

        QMessageBox.warning(
            self,
            "Schriftart fehlt",
            warning_text
        )

    def _on_neu_laden_delayed(self):
        """
        Verzögertes Laden der Kategorien (für bessere UX beim Programmstart)
        Zeigt animierte Statusmeldung während des Ladens
        """
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        # Animierte Statusmeldung
        self._loading_dots = 0
        self._loading_timer = QTimer()
        self._loading_timer.timeout.connect(self._update_loading_status)
        self._loading_timer.start(500)  # Alle 500ms aktualisieren

        # Status anzeigen
        self._update_statusbar("Lade Kategorien")
        QApplication.processEvents()

        # Kurze Verzögerung, damit Status sichtbar wird
        QTimer.singleShot(50, self._on_neu_laden)

    def _update_loading_status(self):
        """Aktualisiert animierte Lade-Statusmeldung"""
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        self._update_statusbar(f"Lade Kategorien{dots}")

    def _on_neu_laden(self):
        """Laedt Kategorien/Zeichen neu"""
        from PyQt6.QtWidgets import QApplication

        # Loading-Animation stoppen falls aktiv
        if hasattr(self, '_loading_timer') and self._loading_timer.isActive():
            self._loading_timer.stop()

        self.logger.info("Lade Kategorien neu...")
        self._update_statusbar("Lade Kategorien...")
        QApplication.processEvents()  # BUGFIX: UI aktualisieren
        self.tree_zeichen.clear()

        try:
            # CHANGED: scan_all_fast() - Kategorien UND SVGs in einem Durchlauf
            self._update_statusbar("Scanne Kategorien und SVGs...")
            QApplication.processEvents()  # BUGFIX: UI aktualisieren
            all_data = self.svg_loader.scan_all_fast()

            if not all_data:
                self.statusbar.showMessage(
                    f"Keine Kategorien in: {self.svg_loader.zeichen_dir}"
                )
                return

            # Hierarchie aufbauen (mit bereits geladenen SVG-Daten)
            self._update_statusbar(f"Baue Hierarchie auf ({len(all_data)} Kategorien)...")
            QApplication.processEvents()  # BUGFIX: UI aktualisieren
            self._build_tree_fast(all_data)

            # Statusbar aktualisieren
            total_svgs = sum(len(svgs) for svgs in all_data.values())
            self._update_statusbar("Kategorien erfolgreich geladen")
            QApplication.processEvents()  # BUGFIX: UI aktualisieren
            self.logger.info("{} Kategorien mit {} SVGs geladen".format(len(all_data), total_svgs))

            # Export-Button aktivieren
            self.btn_export.setEnabled(True)

            # FIXED: Initialisierung abgeschlossen - Validierung ab jetzt erlaubt
            self._initialization_complete = True
            self.logger.info("Initialisierung abgeschlossen - Validierung aktiviert")

            # Nach kurzer Zeit Standard-Status anzeigen
            QTimer.singleShot(2000, self._update_statusbar)

        except Exception as e:
            self.logger.error(f"Fehler beim Laden: {e}")
            self._update_statusbar(f"Fehler beim Laden: {e}")
            QMessageBox.critical(self, "Fehler", f"Beim Laden ist ein Fehler aufgetreten:\n{e}")
            return  # NEU: Verhindert weitere Ausführung bei Fehler

    def _build_tree(self, categories: list):
        """
        Baut Baum-Struktur auf

        Args:
            categories: Liste von Kategorie-Pfaden (z.B. ["Einheiten", "Formationen/Gruppen"])
        """
        # Hierarchie-Dict: {kategorie: {unterkategorie: [...], zeichen: [...]}}
        hierarchy = {}

        for category in categories:
            parts = category.split('/')
            current_dict = hierarchy

            # Hierarchie aufbauen
            for part in parts:
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]

        # Tree aufbauen
        self._add_hierarchy_to_tree(hierarchy, None)

    def _get_display_name_for_zeichen(self, svg_path: Path) -> str:
        """
        Gibt den Display-Namen für ein Zeichen zurück

        Für Blankozeichen werden die schönen Namen aus constants.py verwendet.
        Für normale Zeichen wird der Dateiname ohne Extension verwendet.

        Args:
            svg_path: Pfad zur SVG-Datei (oder virtueller Blanko-Pfad)

        Returns:
            Display-Name für TreeView
        """
        # Prüfe ob es ein Blanko-Zeichen ist
        if SVGLoaderLocal.is_blanko_zeichen(svg_path):
            # Verwende schönen Namen aus constants.py
            return SVGLoaderLocal.get_blanko_display_name(svg_path)
        else:
            # Normales Zeichen: Dateiname ohne Extension
            return svg_path.stem

    def _build_tree_fast(self, all_data: dict):
        """
        Baut Baum-Struktur schnell auf (mit bereits geladenen SVG-Daten)

        CHANGED: Nutzt scan_all_fast() Ergebnis - keine separaten get_svgs_in_category() Calls!

        Args:
            all_data: Dict[str, List[Path]] - Kategorien mit ihren SVG-Pfaden
        """
        from PyQt6.QtWidgets import QApplication
        from datetime import datetime

        # LOGGING: Start des GUI-Aufbaus
        start_time = datetime.now()
        total_items = sum(len(svgs) for svgs in all_data.values())
        self.logger.info("Starte GUI-Aufbau: {} Kategorien, {} Zeichen".format(
            len(all_data), total_items
        ))

        # Hierarchie-Dict mit SVG-Pfaden: {kategorie: {unterkategorie: {...}, svgs: [...]}}
        hierarchy = {}

        for category, svg_paths in all_data.items():
            parts = category.split('/')
            current_dict = hierarchy

            # Hierarchie aufbauen
            for part in parts:
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]

            # SVG-Pfade am Endpunkt speichern
            current_dict['__svgs__'] = svg_paths

        # PERFORMANCE: Updates deaktivieren während Tree-Aufbau
        self.tree_zeichen.setUpdatesEnabled(False)

        # PERFORMANCE: Signals blockieren während Initialisierung
        old_block_state = self.tree_zeichen.signalsBlocked()
        self.tree_zeichen.blockSignals(True)

        try:
            # Item-Counter für Batch-Processing
            self._item_counter = 0

            # Tree aufbauen (mit SVG-Daten)
            self._add_hierarchy_to_tree_fast(hierarchy, None, total_items)

        finally:
            # PERFORMANCE: Signals wieder aktivieren
            self.tree_zeichen.blockSignals(old_block_state)

            # PERFORMANCE: Updates wieder aktivieren -> Einmaliges Render
            self.tree_zeichen.setUpdatesEnabled(True)

            # LOGGING: Ende des GUI-Aufbaus
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.info("GUI-Aufbau abgeschlossen in {:.2f}s".format(elapsed))

    def _add_hierarchy_to_tree_fast(self, hierarchy_dict: dict, parent_item: Optional[QTreeWidgetItem], total_items: int = 0):
        """
        Fuegt Hierarchie rekursiv zum Tree hinzu (mit bereits geladenen SVG-Daten)

        CHANGED: SVG-Daten sind bereits vorhanden - kein _load_zeichen_for_item() mehr noetig!

        Args:
            hierarchy_dict: Hierarchie-Dictionary mit '__svgs__' keys
            parent_item: Parent-Item (None = Root)
            total_items: Gesamt-Anzahl Items für Fortschrittsanzeige
        """
        from PyQt6.QtWidgets import QApplication

        for name, sub_dict in sorted(hierarchy_dict.items()):
            # __svgs__ ueberspringen (wird separat verarbeitet)
            if name == '__svgs__':
                continue

            # Item erstellen
            if parent_item is None:
                # Top-Level Kategorie
                item = create_category_item(name)
                self.tree_zeichen.addTopLevelItem(item)
            else:
                # Unterkategorie
                item = create_subcategory_item(name, parent_item)

            # Widgets in Spalten erstellen
            self._create_item_widgets(item)

            # Rekursiv Kinder hinzufuegen
            if sub_dict:
                self._add_hierarchy_to_tree_fast(sub_dict, item, total_items)

            # CHANGED: Zeichen direkt aus Hierarchie laden (nicht mehr scannen!)
            if '__svgs__' in sub_dict:
                for svg_path in sub_dict['__svgs__']:
                    # Verwende schönen Display-Namen (für Blankozeichen aus constants.py)
                    display_name = self._get_display_name_for_zeichen(svg_path)
                    zeichen_item = create_zeichen_item(display_name, svg_path, item)
                    self._create_item_widgets(zeichen_item)

                    # PERFORMANCE: Batch-Processing - UI-Update alle 100 Items
                    self._item_counter += 1
                    if self._item_counter % GUI_BATCH_UPDATE_INTERVAL == 0:
                        # Fortschritt anzeigen
                        progress_pct = int((self._item_counter / total_items) * 100)
                        self._update_statusbar("Baue Hierarchie auf... {}% ({}/{})".format(
                            progress_pct, self._item_counter, total_items
                        ))
                        QApplication.processEvents()  # UI responsive halten

            # Anzahl aktualisieren
            item.update_anzahl()

    def _add_hierarchy_to_tree(self, hierarchy_dict: dict, parent_item: Optional[QTreeWidgetItem]):
        """
        Fuegt Hierarchie rekursiv zum Tree hinzu

        Args:
            hierarchy_dict: Hierarchie-Dictionary
            parent_item: Parent-Item (None = Root)
        """
        for name, sub_dict in sorted(hierarchy_dict.items()):
            # Item erstellen
            if parent_item is None:
                # Top-Level Kategorie
                item = create_category_item(name)
                self.tree_zeichen.addTopLevelItem(item)
            else:
                # Unterkategorie oder Zeichen
                # Pruefen ob Zeichen oder Unterkategorie
                # (Zeichen = .svg Datei, Unterkategorie = Ordner)
                if name.endswith('.svg'):
                    # Zeichen
                    category_path = self._get_category_path(parent_item)
                    svg_path = self.svg_loader.zeichen_dir / category_path / name
                    # Verwende schönen Display-Namen (für Blankozeichen aus constants.py)
                    display_name = self._get_display_name_for_zeichen(svg_path)
                    item = create_zeichen_item(display_name, svg_path, parent_item)
                else:
                    # Unterkategorie
                    item = create_subcategory_item(name, parent_item)

            # Widgets in Spalten erstellen
            self._create_item_widgets(item)

            # Rekursiv Kinder hinzufuegen
            if sub_dict:
                self._add_hierarchy_to_tree(sub_dict, item)

            # Zeichen laden (falls Kategorie/Unterkategorie)
            if item.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
                self._load_zeichen_for_item(item)

            # Anzahl aktualisieren
            item.update_anzahl()

    def _load_zeichen_for_item(self, item: ZeichenTreeItem):
        """
        Laedt Zeichen fuer Kategorie/Unterkategorie

        Args:
            item: Kategorie/Unterkategorie-Item
        """
        category_path = self._get_category_path(item)
        zeichen_paths = self.svg_loader.get_svgs_in_category(category_path)

        for svg_path in zeichen_paths:
            # Verwende schönen Display-Namen (für Blankozeichen aus constants.py)
            display_name = self._get_display_name_for_zeichen(svg_path)
            zeichen_item = create_zeichen_item(display_name, svg_path, item)
            self._create_item_widgets(zeichen_item)

    def _get_category_path(self, item: QTreeWidgetItem) -> str:
        """
        Gibt Kategorie-Pfad fuer Item zurueck

        Args:
            item: Tree-Item

        Returns:
            str: Kategorie-Pfad (z.B. "Formationen/Gruppen")
        """
        parts = []
        current = item

        while current is not None:
            if isinstance(current, ZeichenTreeItem):
                parts.insert(0, current.name)
            current = current.parent()

        return '/'.join(parts)

    def _create_item_widgets(self, item: ZeichenTreeItem):
        """
        Erstellt Widgets fuer Item-Spalten

        Args:
            item: Tree-Item
        """
        # CHANGED: Kopien-SpinBox (Spalte 1) - Jetzt auch für Kategorien!
        from PyQt6.QtWidgets import QSpinBox
        spin_kopien = QSpinBox()
        spin_kopien.setMinimum(1)
        spin_kopien.setMaximum(999)
        spin_kopien.setValue(1)

        # FIXED: EventFilter installieren (blockiert Scrollrad + Cursortasten)
        spin_kopien.installEventFilter(self.no_scroll_filter)

        # Bei Zeichen: Initial deaktiviert bis ausgewählt
        # Bei Kategorien: Immer aktiviert
        if item.item_type == ZeichenTreeItem.TYPE_ZEICHEN:
            spin_kopien.setEnabled(False)

        # PERFORMANCE: Signal erst NACH setValue verbinden (vermeidet Signal-Emission)
        spin_kopien.valueChanged.connect(
            lambda val, i=item: self._on_kopien_changed(i, val)
        )
        self.tree_zeichen.setItemWidget(item, ZeichenTreeItem.COL_ANZAHL, spin_kopien)

        # Modus-ComboBox (Spalte 2)
        # Labels werden aus modus_config.py geladen (Master-Definitionen)
        combo_modus = QComboBox()
        combo_modus.addItems(get_modus_gui_labels())

        # FIXED: EventFilter installieren (blockiert Scrollrad + Cursortasten)
        combo_modus.installEventFilter(self.no_scroll_filter)

        # v7.1.1: Standard-Modus aus RuntimeConfig setzen (für alle Zeichen)
        config = get_config()
        default_modus = config.standard_modus

        # NEW: Bei Blanko-Zeichen den passenden Modus vorauswählen (überschreibt Standard)
        if item.item_type == ZeichenTreeItem.TYPE_ZEICHEN and item.svg_path:
            blanko_modus = self.svg_loader.get_blanko_modus(item.svg_path)
            if blanko_modus:
                default_modus = blanko_modus  # Blanko-Modus hat Vorrang

        # Modus setzen (entweder Blanko-Modus oder Standard aus RuntimeConfig)
        gui_label = internal_to_gui(default_modus)
        index = combo_modus.findText(gui_label)
        if index >= 0:
            combo_modus.setCurrentIndex(index)
            # Auch im Item-Params speichern
            item.params.modus = default_modus

        # PERFORMANCE: Signal erst NACH setCurrentIndex verbinden
        combo_modus.currentTextChanged.connect(
            lambda text, i=item: self._on_modus_changed(i, text)
        )
        self.tree_zeichen.setItemWidget(item, ZeichenTreeItem.COL_MODUS, combo_modus)

        # Text-Eingabe (Spalte 3)
        line_text = QLineEdit()
        line_text.setPlaceholderText("OV-Name")  # Default: OV+Staerke
        line_text.textChanged.connect(
            lambda text, i=item: self._on_text_changed(i, text)
        )
        self.tree_zeichen.setItemWidget(item, ZeichenTreeItem.COL_TEXT, line_text)

        # v7.1: Grafik-Parameter sind jetzt global, keine per-Item-Widgets mehr
        # Widgets im Item speichern (ohne Grafik-Widgets)
        item.widgets = {
            'modus': combo_modus,
            'text': line_text,
            'kopien': spin_kopien
        }

    def _on_kopien_changed(self, item: ZeichenTreeItem, anzahl: int):
        """
        Kopien-Anzahl wurde geaendert

        Args:
            item: Tree-Item
            anzahl: Neue Anzahl
        """
        item.anzahl_kopien = anzahl
        self.logger.debug(f"Kopien-Anzahl fuer {item.name}: {anzahl}")

        # NEW: Bei Kategorie: An Kinder propagieren
        if item.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
            self._propagate_kopien_to_children(item, anzahl)

        # FIXED: Statusleiste aktualisieren
        self._update_statusbar()

    def _on_modus_changed(self, item: ZeichenTreeItem, modus_text: str):
        """
        Modus wurde geaendert

        Args:
            item: Tree-Item
            modus_text: Neuer Modus-Text
        """
        self.logger.debug(f"_on_modus_changed: item={item.name}, modus={modus_text}, is_category={item.item_type != ZeichenTreeItem.TYPE_ZEICHEN}")

        # CRITICAL FIX: Disconnect itemChanged während Modus-Wechsel
        # _highlight_row() und _highlight_categories() ändern Items was itemChanged triggert!
        # Das würde fälschlicherweise alle Checkboxen löschen
        self.tree_zeichen.itemChanged.disconnect(self._on_item_changed)
        try:
            # Modus-Text -> Internal (aus modus_config.py)
            modus = gui_to_internal(modus_text)

            # Parameter setzen
            item.params.modus = modus
            item.params.inherited = False

            # NEW: Bei Modus-Wechsel auf DATEI-Ebene Text leeren (wird bei dateiname-Modus gleich wieder gesetzt)
            if item.item_type == ZeichenTreeItem.TYPE_ZEICHEN:
                item.params.text = ""
                if 'text' in item.widgets:
                    item.widgets['text'].blockSignals(True)
                    item.widgets['text'].setText("")
                    item.widgets['text'].blockSignals(False)

            # FIXED: Validierung überspringen wenn Initialisierung noch läuft
            if not self._initialization_complete:
                # Textfeld-Platzhalter anpassen (ohne Validierung)
                self._update_text_placeholder(item, modus)
                # Grafik-Felder aktivieren/deaktivieren
                self._update_grafik_fields_state(item, modus == "ohne_text")
                # Grafik-Spalten ein-/ausblenden
                self._update_grafik_columns_visibility()
                return

            # FIXED: Validierung NUR bei aktivierten Zeichen durchführen
            is_checked = item.checkState(0) == Qt.CheckState.Checked if item.item_type == ZeichenTreeItem.TYPE_ZEICHEN else False

            # SPECIAL: Bei Dateiname-Modus automatisch Text aus Dateiname setzen
            if modus == "dateiname" and item.item_type == ZeichenTreeItem.TYPE_ZEICHEN:
                # Dateiname als Text: "Datei_Name.svg" → "Datei Name"
                filename = item.svg_path.stem if hasattr(item, 'svg_path') and item.svg_path else item.name
                if filename.endswith('.svg'):
                    filename = filename[:-4]
                text = filename.replace("_", " ")

                # Text setzen (OHNE Validierung hier - wird von _on_text_changed() übernommen)
                item.params.text = text
                if 'text' in item.widgets:
                    # FIXED: Signale blockieren um doppelte Validierung zu vermeiden
                    item.widgets['text'].blockSignals(True)
                    item.widgets['text'].setText(text)
                    item.widgets['text'].blockSignals(False)

                # FIXED: Validierung nur wenn Zeichen AKTIVIERT ist
                if is_checked:
                    # FIXED: font_size aus RuntimeConfig verwenden
                    from runtime_config import get_config
                    runtime_cfg = get_config()

                    # Validierung durchführen
                    is_valid, error_msg = self.validation_mgr.validate_text_length(
                        text=text,
                        modus=modus,
                        zeichen_hoehe_mm=self.settings.zeichen.zeichen_hoehe_mm,
                        zeichen_breite_mm=self.settings.zeichen.zeichen_breite_mm,
                        sicherheitsabstand_mm=self.settings.zeichen.sicherheitsabstand_mm,
                        font_size=runtime_cfg.font_size,  # FIXED: Aus RuntimeConfig statt DEFAULT_FONT_SIZE
                        item_name=item.name
                    )

                    if is_valid:
                        # Text ist gueltig -> Zeile zurücksetzen
                        self._highlight_row(item, error=False)
                        if 'text' in item.widgets:
                            item.widgets['text'].setStyleSheet("")
                    else:
                        # Text ist zu lang -> ROT einfaerben
                        self._highlight_row(item, error=True)
                        if 'text' in item.widgets:
                            item.widgets['text'].setStyleSheet(
                                f"background-color: {VALIDATION_ERROR_BG}; "
                                f"color: {VALIDATION_ERROR_FG}; "
                                f"font-weight: bold;"
                            )

                        # FIXED: Kategorie-Hervorhebung auch bei Dateiname-Modus
                        category_path = self._get_category_path_for_zeichen(item)
                        if category_path:
                            # FIXED: Alle Ebenen im Pfad hervorheben
                            all_category_paths = self._get_all_category_levels(category_path)
                            self._highlight_categories(all_category_paths)

                        # Warnung NUR anzeigen wenn nicht bereits eine gezeigt wird
                        if not self._batch_operation_active and not self._validation_warning_shown:
                            self._validation_warning_shown = True
                            self.validation_mgr.show_validation_warning(
                                self,
                                "Dateiname zu lang",
                                error_msg + "\n\nDer Text wurde ROT markiert.\nBitte kürze den Text manuell!"
                            )
                            # FIXED: Flag mit Timer zurücksetzen (500ms Debounce)
                            self._reset_validation_warning_flag_delayed()

            # Textfeld-Platzhalter anpassen
            self._update_text_placeholder(item, modus)

            # FIXED: Bei Modus-Wechsel Hervorhebung zurücksetzen (außer gerade bei Dateiname-Validierung)
            # Nur wenn NICHT gerade Dateiname-Modus gesetzt wurde (dann wurde Farbe oben schon gesetzt)
            if modus != "dateiname":
                self._highlight_row(item, error=False)
                if 'text' in item.widgets:
                    item.widgets['text'].setStyleSheet("")

            # v7.1: Grafik-Felder-Verwaltung entfernt (keine per-Item-Grafik-Widgets mehr)

            # Bei Kategorie: Propagieren
            if item.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
                # NEW: Batch-Modus aktivieren (unterdrückt Einzelwarnungen)
                self._batch_operation_active = True

                item.propagate_params_to_children()
                self._update_children_widgets(item)

                # NEW: Nach Modus-Propagierung Batch-Validierung für Text-Modi
                if modus == "dateiname":
                    # Spezial: Bei Dateiname-Modus erstmal alle Kinder mit Text befüllen
                    self._apply_dateiname_to_children(item)

                # NEW: Batch-Validierung für alle Kinder mit Text-Modi
                if modus in self.TEXT_MODES:
                    self._validate_all_text_lengths()

                # NEW: Batch-Modus deaktivieren
                self._batch_operation_active = False

        finally:
            # CRITICAL: Signal immer wieder verbinden, auch bei Fehlern
            self.tree_zeichen.itemChanged.connect(self._on_item_changed)

    def _on_text_changed(self, item: ZeichenTreeItem, text: str):
        """Text wurde geaendert"""
        # FIXED: Validierung überspringen wenn Initialisierung noch läuft
        if not self._initialization_complete:
            item.params.text = text
            item.params.inherited = False
            return

        # VALIDATION: Prüfe ob Text in Canvas passt (nur bei Text-Modi)
        if text and item.params.modus in self.TEXT_MODES:  # FIXED: Alle Text-Modi validieren
            # FIXED: font_size aus RuntimeConfig verwenden
            from runtime_config import get_config
            runtime_cfg = get_config()

            is_valid, error_msg = self.validation_mgr.validate_text_length(
                text=text,
                modus=item.params.modus,
                zeichen_hoehe_mm=self.settings.zeichen.zeichen_hoehe_mm,
                zeichen_breite_mm=self.settings.zeichen.zeichen_breite_mm,
                sicherheitsabstand_mm=self.settings.zeichen.sicherheitsabstand_mm,
                font_size=runtime_cfg.font_size,  # FIXED: Aus RuntimeConfig statt DEFAULT_FONT_SIZE
                item_name=item.name
            )

            if not is_valid:
                # FIXED: GANZE ZEILE rot hinterlegen (nicht nur Text-Widget)
                self._highlight_row(item, error=True)
                # FIXED: Textfeld ROT einfaerben mit Farb-Konstanten
                if 'text' in item.widgets:
                    item.widgets['text'].setStyleSheet(
                        f"background-color: {VALIDATION_ERROR_BG}; "
                        f"color: {VALIDATION_ERROR_FG}; "
                        f"font-weight: bold;"
                    )
                # FIXED: Warnung nur wenn NICHT im Batch-Modus UND noch keine Warnung gezeigt
                if not self._batch_operation_active and not self._validation_warning_shown:
                    self._validation_warning_shown = True
                    self.validation_mgr.show_validation_warning(
                        self, "Text überschreitet Canvas",
                        error_msg + "\n\nDer Text wurde ROT markiert.\nBitte kürze den Text!"
                    )
                    # FIXED: Flag mit Timer zurücksetzen (500ms Debounce)
                    self._reset_validation_warning_flag_delayed()
            else:
                # FIXED: GANZE ZEILE zurücksetzen (nicht nur Text-Widget)
                self._highlight_row(item, error=False)
                # FIXED: Text gueltig -> Normale Farbe
                if 'text' in item.widgets:
                    item.widgets['text'].setStyleSheet("")
        else:
            # FIXED: GANZE ZEILE zurücksetzen (nicht nur Text-Widget)
            self._highlight_row(item, error=False)
            # FIXED: Kein Text oder kein Text-Modus -> Normale Farbe
            if 'text' in item.widgets:
                item.widgets['text'].setStyleSheet("")

        item.params.text = text
        item.params.inherited = False

        # Propagieren
        if item.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
            item.propagate_params_to_children()
            self._update_children_widgets(item)

    # v7.1: Grafik-Parameter Event-Handler entfernt (Grafik-Größe ist jetzt global)

    def _update_text_placeholder(self, item: ZeichenTreeItem, modus: str):
        """
        Aktualisiert Platzhalter-Text des Textfelds basierend auf Modus

        Args:
            item: Tree-Item
            modus: Aktueller Modus
        """
        if not item.widgets:
            return

        # Platzhalter-Text aus modus_config.py laden
        placeholder = get_placeholder_text(modus)
        item.widgets['text'].setPlaceholderText(placeholder)

        # Bei "Nur Grafik" und "Schreiblinie" Textfeld deaktivieren
        # Bei "Dateiname" bleibt Textfeld aktiviert (manuell editierbar)
        item.widgets['text'].setEnabled(modus not in ["ohne_text", "schreiblinie_staerke"])  # CHANGED: "nur_grafik" -> "ohne_text"

    # v7.1: Grafik-Widget-Visibility-Methoden entfernt (keine per-Item-Widgets mehr)

    def _update_children_widgets(self, parent_item: ZeichenTreeItem):
        """
        Aktualisiert Widgets aller Kinder (nach Propagierung)

        Args:
            parent_item: Parent-Item
        """
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if isinstance(child, ZeichenTreeItem) and child.widgets:
                # v7.1: Nur Modus und Text-Widgets (Grafik-Widgets entfernt)
                child.widgets['modus'].blockSignals(True)
                child.widgets['text'].blockSignals(True)

                # Modus (Internal -> GUI aus modus_config.py)
                gui_label = internal_to_gui(child.params.modus)
                child.widgets['modus'].setCurrentText(gui_label)

                # Text-Platzhalter
                self._update_text_placeholder(child, child.params.modus)

                # Text
                child.widgets['text'].setText(child.params.text)

                # Signale wieder aktivieren
                child.widgets['modus'].blockSignals(False)
                child.widgets['text'].blockSignals(False)

                # Rekursiv
                if child.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
                    self._update_children_widgets(child)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Item wurde geändert (z.B. Checkbox)"""
        if column != ZeichenTreeItem.COL_NAME:
            return

        if not isinstance(item, ZeichenTreeItem):
            return

        # Bei Kategorie/Unterkategorie: Alle Kinder auch an/abhaken
        if item.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
            checked = item.is_checked()
            self.logger.debug(f"_on_item_changed: Category {item.name} checkbox changed to {checked}")

            # NEW: Wenn Checkbox aktiviert wird, propagiere ALLE Werte an Kinder
            if checked and hasattr(item, '_was_unchecked'):
                self._propagate_all_values_to_children(item)
                delattr(item, '_was_unchecked')
            elif not checked:
                # Merken, dass es deaktiviert wurde
                item._was_unchecked = True

            # FIXED: Batch-Modus aktivieren bevor Kinder aktiviert werden
            self._batch_operation_active = True

            # EXPERIMENTAL: Disconnect itemChanged statt blockSignals()
            # blockSignals() auf TreeWidget löscht Selection - disconnect nur das Event
            self.tree_zeichen.itemChanged.disconnect(self._on_item_changed)
            try:
                self._set_children_checked(item, checked)
            finally:
                self.tree_zeichen.itemChanged.connect(self._on_item_changed)

            # FIXED: Nach Aktivierung Batch-Validierung durchführen
            if checked:
                self._validate_all_text_lengths()

            # FIXED: Batch-Modus deaktivieren
            self._batch_operation_active = False
        else:
            # Bei Zeichen: Kopien-SpinBox aktivieren/deaktivieren
            if 'kopien' in item.widgets:
                item.widgets['kopien'].setEnabled(item.is_checked())

            # FIXED: Einzelzeichen-Validierung mit Kategorie-Hervorhebung
            # Verwende zentrale Validierung statt separate Einzelvalidierung
            if not self._batch_operation_active:
                if item.is_checked():
                    # AKTIVIERT: Validierung über zentralen Mechanismus
                    self._validate_single_zeichen(item)
                else:
                    # DEAKTIVIERT: Warnung zurücksetzen
                    self._reset_validation_highlight(item)
                    # FIXED: Auch Kategorien-Hervorhebung neu berechnen
                    self._validate_all_text_lengths()

        # Statusbar aktualisieren
        self._update_statusbar()

    def _set_children_checked(self, parent_item: ZeichenTreeItem, checked: bool):
        """
        Setzt Checkbox aller Kinder

        EXPERIMENTAL: Signal wird vom Aufrufer disconnected, nicht hier
        """
        self.logger.debug(f"_set_children_checked: parent={parent_item.name}, checked={checked}")
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if isinstance(child, ZeichenTreeItem):
                # Checkbox setzen (itemChanged Signal ist disconnected vom Aufrufer)
                self.logger.debug(f"  Setting child checkbox: {child.name} -> {checked}")
                child.set_checked(checked)

                # Bei Zeichen: Kopien-SpinBox aktivieren/deaktivieren
                if child.item_type == ZeichenTreeItem.TYPE_ZEICHEN and 'kopien' in child.widgets:
                    child.widgets['kopien'].setEnabled(checked)

                # Rekursiv
                if child.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
                    self._set_children_checked(child, checked)

    def _propagate_kopien_to_children(self, parent_item: ZeichenTreeItem, anzahl: int):
        """
        Propagiert Kopien-Anzahl an alle Kinder

        Args:
            parent_item: Parent-Item
            anzahl: Kopien-Anzahl
        """
        # NEW: Propagiere Kopien-Anzahl an alle Kinder
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if isinstance(child, ZeichenTreeItem):
                child.anzahl_kopien = anzahl
                if 'kopien' in child.widgets:
                    # FIXED: Signale blockieren um valueChanged-Kaskade zu verhindern
                    child.widgets['kopien'].blockSignals(True)
                    child.widgets['kopien'].setValue(anzahl)
                    child.widgets['kopien'].blockSignals(False)

                # Rekursiv
                if child.item_type != ZeichenTreeItem.TYPE_ZEICHEN:
                    self._propagate_kopien_to_children(child, anzahl)

    def _propagate_all_values_to_children(self, parent_item: ZeichenTreeItem):
        """
        Propagiert ALLE Werte (Modus, Text, Grafik-Einstellungen, Kopien) an alle Kinder

        Args:
            parent_item: Parent-Item
        """
        # NEW: Überschreibe alle Werte der Kinder mit den Werten des Parents
        self.logger.info(f"Propagiere alle Werte von {parent_item.name} an Kinder")

        # Parameter propagieren
        parent_item.propagate_params_to_children()

        # Kopien propagieren
        if 'kopien' in parent_item.widgets:
            anzahl = parent_item.widgets['kopien'].value()
            self._propagate_kopien_to_children(parent_item, anzahl)

        # Widgets aktualisieren
        self._update_children_widgets(parent_item)

    def _on_vorlagen_ordner_explorer_oeffnen(self):
        """Öffnet Vorlagen-Ordner im Dateimanager"""
        import subprocess
        from pathlib import Path

        vorlagen_ordner = Path(self.settings.zeichen_ordner)

        if not vorlagen_ordner.exists():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle("Ordner existiert nicht")
            msg_box.setText(f"Der Vorlagen-Ordner existiert nicht:\n{vorlagen_ordner}\n\nSoll er erstellt werden?")
            btn_ja = msg_box.addButton("Ja", QMessageBox.ButtonRole.YesRole)
            btn_nein = msg_box.addButton("Nein", QMessageBox.ButtonRole.NoRole)
            msg_box.setDefaultButton(btn_ja)
            msg_box.exec()

            if msg_box.clickedButton() == btn_ja:
                try:
                    vorlagen_ordner.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Fehler",
                        f"Der Ordner konnte nicht erstellt werden:\n{e}"
                    )
                    return
            else:
                return

        try:
            # Dateimanager öffnen
            subprocess.run([filemanager(), str(vorlagen_ordner)])
            self.logger.info(f"Vorlagen-Ordner geöffnet: {vorlagen_ordner}")
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Vorlagen-Ordners: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Der Vorlagen-Ordner konnte nicht geöffnet werden:\n{e}"
            )

    def _on_export(self):
        """Export-Funktion"""
        # NEW: Export-Dialog öffnen
        self.logger.info("Starte Export...")
        self._update_statusbar("Starte Export...")

        # Angehakte Zeichen sammeln
        checked_zeichen = self._get_all_checked_zeichen()

        if not checked_zeichen:
            self._update_statusbar("Keine Zeichen für Export ausgewählt")
            QMessageBox.warning(
                self,
                "Keine Auswahl",
                "Bitte wähle mindestens ein Zeichen aus!"
            )
            return

        # Kopienanzahl berechnen
        total_kopien = sum(item.anzahl_kopien for item in checked_zeichen)

        self.logger.info(f"{len(checked_zeichen)} Zeichen für Export ausgewählt ({total_kopien} Kopien)")
        self._update_statusbar(f"Export: {len(checked_zeichen)} Zeichen ({total_kopien} Kopien)")

        # IMPORTANT: RuntimeConfig mit aktuellen GUI-Werten synchronisieren
        # (damit Export die richtigen Werte verwendet, auch ohne vorheriges Speichern)
        self._sync_runtime_config_from_gui()

        # NEW: Ermittle aktives Layout (S1 oder S2)
        active_layout = self._get_active_layout()
        self.logger.info(f"Aktives Layout für Export: {active_layout.upper()}")

        # NEW: Export-Dialog öffnen
        from gui.dialogs.export_dialog import ExportDialog

        dialog = ExportDialog(checked_zeichen, self.settings, active_layout, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            self.logger.info("Export erfolgreich abgeschlossen")
            self._update_statusbar(f"Export erfolgreich: {len(checked_zeichen)} Zeichen ({total_kopien} Kopien)")
        else:
            self.logger.info("Export abgebrochen")
            self._update_statusbar("Export abgebrochen")

        # Nach kurzer Zeit Standard-Status anzeigen
        QTimer.singleShot(2000, self._update_statusbar)

    def _get_all_checked_zeichen(self) ->list[ZeichenTreeItem]:
        """Sammelt alle angehakten Zeichen"""
        checked = []

        # Alle Top-Level Items durchgehen
        for i in range(self.tree_zeichen.topLevelItemCount()):
            item = self.tree_zeichen.topLevelItem(i)
            if isinstance(item, ZeichenTreeItem):
                checked.extend(item.get_checked_zeichen())

        return checked

    def _on_einstellungen(self):
        """
        Einstellungen-Dialog öffnen

        NEW (v7.3): Settings Dialog implementiert
        """
        from gui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.settings_mgr, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Settings wurden gespeichert, UI aktualisieren
            self._load_settings_to_ui()
            self.logger.info("Einstellungen wurden aktualisiert")

            # RuntimeConfig aktualisieren
            from runtime_config import RuntimeConfig
            RuntimeConfig.get_instance().reload_from_settings()

    def _on_benutzerhandbuch(self):
        """Oeffnet Benutzerhandbuch (PDF bevorzugt, sonst Markdown)"""
        import subprocess
        import platform
        from pathlib import Path

        # Basis-Verzeichnis ermitteln
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent

        # Suche nach Benutzerhandbuch
        pdf_path = base_dir / "User-documentation" / "BENUTZERHANDBUCH.pdf"
        md_path = base_dir / "BENUTZERHANDBUCH.md"

        # Versuche PDF zu öffnen (bevorzugt)
        if pdf_path.exists():
            try:
                system = platform.system()
                if system == 'Windows':
                    # Windows: Standard-PDF-Reader (primär unterstützt)
                    subprocess.run(['start', '', str(pdf_path)], shell=True)
                elif system == 'Linux':
                    # Linux: xdg-open (Experimentell - wird getestet)
                    subprocess.run(['xdg-open', str(pdf_path)])
                else:
                    # Nicht unterstütztes System (z.B. macOS)
                    self.logger.warning(f"Nicht unterstütztes Betriebssystem: {system}")
                    QMessageBox.warning(
                        self,
                        "Nicht unterstützt",
                        f"Das Öffnen von Dateien wird auf {system} nicht unterstützt.\n\n"
                        f"Bitte öffne die Datei manuell:\n{pdf_path}"
                    )
                    return

                self.logger.info(f"Benutzerhandbuch geöffnet: {pdf_path}")
                return
            except Exception as e:
                self.logger.error(f"Fehler beim Öffnen der PDF: {e}")
                # Fallback zu Markdown

        # Fallback: Markdown im Browser öffnen
        if md_path.exists():
            try:
                system = platform.system()
                if system == 'Windows':
                    # Windows: Standard-Browser (primär unterstützt)
                    subprocess.run(['start', '', str(md_path)], shell=True)
                elif system == 'Linux':
                    # Linux: xdg-open (Experimentell - wird getestet)
                    subprocess.run(['xdg-open', str(md_path)])
                else:
                    # Nicht unterstütztes System (z.B. macOS)
                    self.logger.warning(f"Nicht unterstütztes Betriebssystem: {system}")
                    QMessageBox.warning(
                        self,
                        "Nicht unterstützt",
                        f"Das Öffnen von Dateien wird auf {system} nicht unterstützt.\n\n"
                        f"Bitte öffne die Datei manuell:\n{md_path}"
                    )
                    return

                self.logger.info(f"Benutzerhandbuch geöffnet: {md_path}")
                return
            except Exception as e:
                self.logger.error(f"Fehler beim Öffnen der Markdown-Datei: {e}")

        # Keine Datei gefunden
        QMessageBox.warning(
            self,
            "Benutzerhandbuch nicht gefunden",
            f"Das Benutzerhandbuch konnte nicht gefunden werden.\n\n"
            f"Erwartet in:\n"
            f"- {pdf_path}\n"
            f"- {md_path}"
        )
        self.logger.warning("Benutzerhandbuch nicht gefunden")

    def _on_logs_oeffnen(self):
        """Oeffnet Log-Ordner im Dateimanager"""
        # NEW: Log-Ordner im Dateimanager öffnen
        import subprocess
        from constants import LOGS_DIR

        if not LOGS_DIR.exists():
            QMessageBox.warning(
                self,
                "Log-Ordner nicht gefunden",
                f"Der Log-Ordner existiert nicht:\n{LOGS_DIR}"
            )
            return

        try:
            # Dateimanager öffnen
            subprocess.run([filemanager(), str(LOGS_DIR)])
            self.logger.info(f"Log-Ordner geöffnet: {LOGS_DIR}")
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Log-Ordners: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Der Log-Ordner konnte nicht geöffnet werden:\n{e}"
            )

    def _on_ueber(self):
        """Ueber-Dialog mit Logo"""
        # Custom About-Dialog mit Logo erstellen
        about_box = QMessageBox(self)
        about_box.setWindowTitle(f"Über {PROGRAM_NAME}")
        about_box.setTextFormat(Qt.TextFormat.RichText)

        # Logo setzen (falls vorhanden)
        if LOGO_PATH.exists():
            logo_pixmap = QPixmap(str(LOGO_PATH))
            if not logo_pixmap.isNull():
                # Logo auf 128px Hoehe skalieren
                logo_pixmap = logo_pixmap.scaledToHeight(
                    128,
                    Qt.TransformationMode.SmoothTransformation
                )
                about_box.setIconPixmap(logo_pixmap)

        # Text setzen
        about_box.setText(
            f"<h2>{PROGRAM_NAME}</h2>"
            f"<p>Version: {PROGRAM_VERSION}</p>"
        )
        about_box.setInformativeText(
            f"<p>{PROGRAM_DESCRIPTION}</p>"
            f"<p></p>"
            f"<p><b>Zweck:</b> Dieses Programm wurde speziell für die ehrenamtliche und hauptamtliche "
            f"Arbeit im Zivil- und Katastrophenschutz entwickelt. Es soll Hilfsorganisationen "
            f"eine kostenlose Open-Source-Lösung bieten.</p>"
            f"<p></p>"
            f"<p><b>Lizenz:</b> GPL v3 - Kostenlos für alle Zwecke (auch kommerzielle Nutzung)</p>"
            f"<p></p>"
            f"<p><b>Freundliche Bitte an kommerzielle Nutzer:</b><br>"
            f"Falls Sie dieses Tool kommerziell einsetzen, würden wir uns über eine kurze "
            f"Mitteilung freuen. Dies ist keine rechtliche Verpflichtung, sondern hilft uns, "
            f"die Verbreitung des Programms nachzuvollziehen.</p>"
            f"<p></p>"
            f"<p>{PROGRAM_AUTHOR}</p>"
            f"<p>{PROGRAM_AUTHOR_EMAIL}</p>"
        )

        about_box.exec()

    def _on_search_text_changed(self, search_text: str):
        """
        Filtert Tree-Items basierend auf Suchtext

        Args:
            search_text: Suchtext vom Benutzer
        """
        search_text = search_text.strip().lower()

        # Wenn Suchfeld leer: Alle Items anzeigen
        if not search_text:
            self._show_all_items()
            return

        # Alle Items durchsuchen und filtern
        root = self.tree_zeichen.invisibleRootItem()
        self._filter_tree_items(root, search_text)

    def _show_all_items(self):
        """Zeigt alle Tree-Items an"""
        root = self.tree_zeichen.invisibleRootItem()
        self._set_item_visibility_recursive(root, True)

    def _set_item_visibility_recursive(self, item: QTreeWidgetItem, visible: bool):
        """
        Setzt Sichtbarkeit eines Items und aller Kinder rekursiv

        Args:
            item: Tree-Item
            visible: True = sichtbar, False = versteckt
        """
        for i in range(item.childCount()):
            child = item.child(i)
            # Verwende setRowHidden() für bessere Widget-Behandlung
            index = self.tree_zeichen.indexFromItem(child)
            self.tree_zeichen.setRowHidden(index.row(), index.parent(), not visible)
            self._set_item_visibility_recursive(child, visible)

    def _filter_tree_items(self, parent_item: QTreeWidgetItem, search_text: str) -> bool:
        """
        Filtert Tree-Items rekursiv basierend auf Suchtext

        Ein Item wird angezeigt, wenn:
        - Der Name des Items den Suchtext enthält ODER
        - Mindestens ein Kind-Item den Suchtext enthält

        Args:
            parent_item: Eltern-Item
            search_text: Suchtext (lowercase)

        Returns:
            True wenn dieses Item oder ein Kind den Suchtext enthält
        """
        has_visible_child = False

        # Alle Kinder durchgehen
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)

            # Rekursiv Kinder filtern
            child_matches = self._filter_tree_items(child, search_text)

            # Prüfen ob der Name des Items den Suchtext enthält
            item_name = child.text(ZeichenTreeItem.COL_NAME).lower()
            name_matches = search_text in item_name

            # Item anzeigen wenn Name matched ODER ein Kind matched
            should_show = name_matches or child_matches

            # Verwende setRowHidden() statt setHidden() für bessere Widget-Behandlung
            index = self.tree_zeichen.indexFromItem(child)
            self.tree_zeichen.setRowHidden(index.row(), index.parent(), not should_show)

            # Parent soll angezeigt werden wenn mindestens ein Kind sichtbar ist
            if should_show:
                has_visible_child = True

                # Item expandieren wenn es Kinder hat und eines davon matched
                if child.childCount() > 0 and child_matches:
                    child.setExpanded(True)

        return has_visible_child

    # =============================================================================================
    # S1-LAYOUT HELPER-METHODEN (v0.9)
    # =============================================================================================

    def _on_s1_aspect_locked_changed(self):
        """
        Seitenverhältnis-Lock wurde geändert (S1-Layout)

        Wenn aktiviert: Breite = 2 x Höhe automatisch setzen
        """
        if self.check_s1_aspect_locked.isChecked():
            # Aspect-Lock aktiviert: Breite automatisch setzen
            # CHANGED: S1-Widgets verwenden
            hoehe = self.spin_s1_zeichen_hoehe.value()
            breite_berechnet = hoehe * 2.0

            # Breite-SpinBox aktualisieren
            self.spin_s1_zeichen_breite.blockSignals(True)
            self.spin_s1_zeichen_breite.setValue(breite_berechnet)
            self.spin_s1_zeichen_breite.blockSignals(False)

            # Breite-SpinBox deaktivieren
            self.spin_s1_zeichen_breite.setEnabled(False)

            self.logger.debug(f"S1 Aspect-Lock aktiviert: Breite = {breite_berechnet:.1f}mm (2 x {hoehe:.1f}mm)")
        else:
            # Aspect-Lock deaktiviert: Breite manuell änderbar
            self.spin_s1_zeichen_breite.setEnabled(True)

            self.logger.debug("S1 Aspect-Lock deaktiviert: Breite manuell änderbar")

    def _on_s2_aspect_locked_changed(self):
        """
        Seitenverhältnis-Lock wurde geändert (S2-Layout)

        NEW v0.8.2.4: Analog zu S1, aber mit 1:1 Verhältnis

        Wenn aktiviert: Breite = Höhe automatisch setzen
        """
        if self.check_s2_aspect_locked.isChecked():
            # Aspect-Lock aktiviert: Breite automatisch setzen
            hoehe = self.spin_s2_zeichen_hoehe.value()
            breite_berechnet = hoehe

            # Breite-SpinBox aktualisieren
            self.spin_s2_zeichen_breite.blockSignals(True)
            self.spin_s2_zeichen_breite.setValue(breite_berechnet)
            self.spin_s2_zeichen_breite.blockSignals(False)

            # Breite-SpinBox deaktivieren
            self.spin_s2_zeichen_breite.setEnabled(False)

            self.logger.debug(f"S2 Aspect-Lock aktiviert: Breite = {breite_berechnet:.1f}mm (1:1)")
        else:
            # Aspect-Lock deaktiviert: Breite manuell änderbar
            self.spin_s2_zeichen_breite.setEnabled(True)

            self.logger.debug("S2 Aspect-Lock deaktiviert: Breite manuell änderbar")

    def _on_s1_links_prozent_changed(self):
        """
        Links-Prozent wurde geändert (S1-Layout)

        Aktualisiert automatisch Rechts-Prozent Label
        """
        self._update_s1_rechts_prozent()

    def _on_s1_anzahl_schreiblinien_changed(self):
        """
        Anzahl Schreiblinien wurde geändert (S1-Layout)

        Aktualisiert automatisch Zeilenhöhe und Schriftgröße
        """
        self._update_s1_line_metrics()

    def _update_s1_rechts_prozent(self):
        """
        Berechnet und aktualisiert Rechts-Prozent Label (S1-Layout)

        Formel: Rechts-Prozent = 100 - Links-Prozent
        CHANGED: Zeigt auch mm-Wert an (fuer beide Seiten)
        """
        links_prozent = self.spin_s1_links_prozent.value()
        rechts_prozent = 100 - links_prozent

        # CHANGED: Berechne mm-Werte fuer beide Seiten (NACH Sicherheitsabstand!)
        hoehe = self.spin_s1_zeichen_hoehe.value()

        # FIXED: Wenn Aspect-Lock aktiviert, Breite berechnen
        if self.check_s1_aspect_locked.isChecked():
            breite = hoehe * 2.0
        else:
            breite = self.spin_s1_zeichen_breite.value()

        abstand = self.spin_s1_abstand_rand.value()

        # Verfuegbare Breite nach Sicherheitsabstand
        verfuegbar_breite = breite - 2 * abstand  # z.B. 90 - 6 = 84mm

        # Aufteilung innerhalb des verfuegbaren Bereichs
        links_breite_mm = verfuegbar_breite * (links_prozent / 100.0)  # z.B. 84 * 0.5 = 42mm
        rechts_breite_mm = verfuegbar_breite * (rechts_prozent / 100.0)  # z.B. 84 * 0.5 = 42mm

        # NEW: Linke Breite in mm anzeigen
        if hasattr(self, 'label_s1_links_breite_mm'):
            self.label_s1_links_breite_mm.setText(f"= {links_breite_mm:.1f} mm")

        # Label aktualisieren mit Prozent und mm
        self.label_s1_rechts_prozent_value.setText(f"{rechts_prozent}% = {rechts_breite_mm:.1f} mm")

        self.logger.debug(f"S1 Aufteilung: Links {links_prozent}% ({links_breite_mm:.1f}mm) | Rechts {rechts_prozent}% ({rechts_breite_mm:.1f}mm)")

    def _update_s1_max_grafik_labels(self):
        """
        Berechnet und aktualisiert die Labels für maximale Grafikabmessungen (S1-Layout)

        Zeigt an:
        - Text-Modi: Max. Grafik bei 1 Textzeile
        - Nur-Grafik: Max. Grafik bei vollem Platz
        """
        from constants import LINE_HEIGHT_FACTOR, POINTS_PER_INCH, mm_to_pixels, pixels_to_mm

        # Aktuelle Werte holen
        hoehe = self.spin_s1_zeichen_hoehe.value()

        # FIXED: Wenn Aspect-Lock aktiviert, Breite berechnen
        if self.check_s1_aspect_locked.isChecked():
            breite = hoehe * 2.0
        else:
            breite = self.spin_s1_zeichen_breite.value()

        abstand = self.spin_s1_abstand_rand.value()
        links_prozent = self.spin_s1_links_prozent.value()

        # Verfügbarer Bereich nach Sicherheitsabstand
        verfuegbar_hoehe = hoehe - 2 * abstand
        verfuegbar_breite = breite - 2 * abstand

        # Linke Breite (für Grafik)
        linke_breite_mm = verfuegbar_breite * (links_prozent / 100.0)

        # Text-Höhe für 1 Zeile berechnen (S1-Layout)
        font_size = self.spin_s1_font_size.value()
        dpi = 300  # Standard-DPI für Berechnung
        font_size_px = int((font_size / POINTS_PER_INCH) * dpi)

        # Maximale Font-Metrics (vereinfachte Berechnung)
        max_ascent = int(font_size_px * 0.8)  # Näherungswert
        max_descent = int(font_size_px * 0.2)  # Näherungswert
        text_bottom_offset_mm = self.spin_s1_text_bottom_offset.value()
        bottom_offset_px = mm_to_pixels(text_bottom_offset_mm, dpi)

        # Text-Höhe für 1 Zeile (S1-Layout)
        text_height_px = max_ascent + max_descent + bottom_offset_px
        text_height_mm = pixels_to_mm(text_height_px, dpi)

        # Abstand Grafik-Text
        abstand_grafik_text_mm = self.spin_s1_abstand_grafik_text.value()

        # Text-Modi: Verfügbare Höhe - Texthöhe - Abstand
        max_grafik_text_hoehe = verfuegbar_hoehe - text_height_mm - abstand_grafik_text_mm
        max_grafik_text_breite = linke_breite_mm

        # Nur-Grafik: Voller verfügbarer Bereich
        max_grafik_nur_hoehe = verfuegbar_hoehe
        max_grafik_nur_breite = linke_breite_mm

        # Labels aktualisieren
        if hasattr(self, 'label_s1_max_grafik_text_modi'):
            self.label_s1_max_grafik_text_modi.setText(
                f"Text-Modi: Max. {max_grafik_text_hoehe:.1f} x {max_grafik_text_breite:.1f} mm"
            )

        if hasattr(self, 'label_s1_max_grafik_nur_grafik'):
            self.label_s1_max_grafik_nur_grafik.setText(
                f"Nur-Grafik: Max. {max_grafik_nur_hoehe:.1f} x {max_grafik_nur_breite:.1f} mm"
            )

        self.logger.debug(
            f"S1 Max-Grafik: Text-Modi {max_grafik_text_hoehe:.1f}x{max_grafik_text_breite:.1f}mm, "
            f"Nur-Grafik {max_grafik_nur_hoehe:.1f}x{max_grafik_nur_breite:.1f}mm"
        )

    def _update_s1_line_metrics(self):
        """
        Berechnet und aktualisiert Zeilenhöhe + Schriftgröße (S1-Layout)

        NEUE LOGIK: Anzahl Zeilen → Zeilenhöhe → Schriftgröße

        Formel:
        - Zeilenhöhe (mm) = verfügbare_höhe / anzahl_zeilen
        - Schriftgröße (mm) = Zeilenhöhe / LINE_HEIGHT_FACTOR
        - Schriftgröße (pt) = (font_size_mm * 72) / 25.4
        """
        from constants import LINE_HEIGHT_FACTOR, SYSTEM_POINTS_PER_INCH

        # Anzahl Schreiblinien (INPUT vom User)
        anzahl_zeilen = self.spin_s1_anzahl_schreiblinien.value()

        # Verfügbare Höhe für Schreiblinien (Zeichenhöhe - 2 x Sicherheitsabstand)
        zeichen_hoehe = self.spin_s1_zeichen_hoehe.value()
        sicherheitsabstand = self.spin_s1_abstand_rand.value()
        verfuegbare_hoehe_mm = zeichen_hoehe - (2 * sicherheitsabstand)

        # Zeilenhöhe berechnen (verfügbare Höhe / Anzahl Zeilen)
        line_height_mm = verfuegbare_hoehe_mm / anzahl_zeilen

        # Schriftgröße berechnen (Zeilenhöhe / LINE_HEIGHT_FACTOR)
        font_size_mm = line_height_mm / LINE_HEIGHT_FACTOR

        # Schriftgröße in Punkten berechnen (mm -> pt)
        # 1 pt = 1/72 inch, 1 inch = 25.4 mm
        font_size_pt = (font_size_mm * SYSTEM_POINTS_PER_INCH) / 25.4

        # Labels aktualisieren
        self.label_s1_zeilenhoehe.setText(f"-> Zeilenhöhe: {line_height_mm:.1f} mm")
        self.label_s1_schriftgroesse.setText(f"Schriftgröße: {font_size_pt:.1f} pt")

        self.logger.debug(
            f"S1 Schreiblinien: {anzahl_zeilen} Zeilen -> {line_height_mm:.1f}mm/Zeile, "
            f"{font_size_pt:.1f}pt bei {verfuegbare_hoehe_mm:.1f}mm Höhe"
        )


# ================================================================================================
# TESTING
# ================================================================================================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
