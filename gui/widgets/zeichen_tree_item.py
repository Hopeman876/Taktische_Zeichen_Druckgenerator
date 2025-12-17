#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zeichen_tree_item.py - Custom TreeWidget-Item fuer Zeichen-Hierarchie

Unterstuetzt:
- Kategorien
- Unterkategorien
- Einzelne Zeichen
- Parameter-Vererbung
- Checkboxen
"""

from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field

from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon


@dataclass
class ZeichenParameter:
    """
    Parameter fuer ein Zeichen/Kategorie (v7.1: Grafik-Parameter entfernt)

    Attributes:
        modus: Modus (ov_staerke, ruf, freitext, nur_grafik)
        text: Text fuer OV/Ruf/Freitext
        inherited: True wenn von Parent geerbt

    Note:
        grafik_position, grafik_max_hoehe, grafik_max_breite wurden in v7.1 entfernt
        → Grafik-Größe ist jetzt global in Settings/RuntimeConfig
    """
    modus: str = "ov_staerke"
    text: str = ""
    inherited: bool = False


class ZeichenTreeItem(QTreeWidgetItem):
    """
    Custom TreeWidgetItem fuer Zeichen-Hierarchie

    Typen:
    - CATEGORY: Kategorie (z.B. "Fahrzeuge")
    - SUBCATEGORY: Unterkategorie (z.B. "Anhaenger")
    - ZEICHEN: Einzelnes Zeichen (z.B. "zeichen.svg")

    Features:
    - Checkbox fuer Auswahl
    - Parameter (mit Vererbung)
    - Vorschaubild (optional)
    - Anzahl Kinder
    """

    # Item-Typen
    TYPE_CATEGORY = "category"
    TYPE_SUBCATEGORY = "subcategory"
    TYPE_ZEICHEN = "zeichen"

    # Spalten-Indizes
    COL_NAME = 0
    COL_ANZAHL = 1
    COL_MODUS = 2
    COL_TEXT = 3
    COL_GRAFIK_POS = 4
    COL_GRAFIK_HOEHE = 5
    COL_GRAFIK_BREITE = 6

    def __init__(
        self,
        item_type: str,
        name: str,
        svg_path: Optional[Path] = None,
        parent: Optional[QTreeWidgetItem] = None
    ):
        """
        Initialisiert Tree-Item

        Args:
            item_type: Typ (CATEGORY, SUBCATEGORY, ZEICHEN)
            name: Anzeige-Name
            svg_path: Pfad zur SVG-Datei (nur bei ZEICHEN)
            parent: Parent-Item (None = Root)
        """
        super().__init__(parent)

        self.item_type = item_type
        self.name = name
        self.svg_path = svg_path

        # Parameter (mit Defaults)
        self.params = ZeichenParameter()

        # Vorschaubild (wird spaeter geladen)
        self.preview_pixmap: Optional[QPixmap] = None

        # Widgets (werden spaeter gesetzt)
        self.widgets = {}

        # Anzahl Kopien (Standard: 1)
        self.anzahl_kopien: int = 1

        # UI initialisieren
        self._setup_ui()

    def _setup_ui(self):
        """Initialisiert UI-Elemente"""
        # Spalte 0: Name mit Checkbox
        self.setText(self.COL_NAME, self.name)
        self.setCheckState(self.COL_NAME, Qt.CheckState.Unchecked)

        # Spalte 1: Anzahl (wird spaeter gesetzt)
        self.setText(self.COL_ANZAHL, "")

        # Spalten 2-6 werden spaeter durch Widgets gesetzt
        # (ComboBox, LineEdit, SpinBox)

    def set_preview(self, pixmap: QPixmap):
        """
        Setzt Vorschaubild

        Args:
            pixmap: Vorschaubild
        """
        self.preview_pixmap = pixmap
        # Icon in Spalte 0 setzen
        icon = QIcon(pixmap)
        self.setIcon(self.COL_NAME, icon)

    def update_anzahl(self):
        """
        Aktualisiert Anzahl-Spalte

        Zeigt Anzahl Kopien an (nur bei Zeichen)
        """
        # Anzahl-Spalte wird durch SpinBox-Widget gesetzt
        # Diese Methode ist nur noch fuer Kompatibilitaet
        pass

    def _count_zeichen_recursive(self) -> int:
        """
        Zaehlt Zeichen rekursiv

        Returns:
            int: Anzahl Zeichen
        """
        count = 0

        for i in range(self.childCount()):
            child = self.child(i)
            if isinstance(child, ZeichenTreeItem):
                if child.item_type == self.TYPE_ZEICHEN:
                    count += 1
                else:
                    # Rekursiv in Unterkategorien
                    count += child._count_zeichen_recursive()

        return count

    def get_all_zeichen(self) -> List['ZeichenTreeItem']:
        """
        Gibt alle Zeichen rekursiv zurueck

        Returns:
            List[ZeichenTreeItem]: Liste aller Zeichen-Items
        """
        zeichen = []

        for i in range(self.childCount()):
            child = self.child(i)
            if isinstance(child, ZeichenTreeItem):
                if child.item_type == self.TYPE_ZEICHEN:
                    zeichen.append(child)
                else:
                    # Rekursiv
                    zeichen.extend(child.get_all_zeichen())

        return zeichen

    def get_checked_zeichen(self) -> List['ZeichenTreeItem']:
        """
        Gibt alle angehakten Zeichen rekursiv zurueck

        Returns:
            List[ZeichenTreeItem]: Liste angehakter Zeichen
        """
        zeichen = []

        # Wenn es ein Zeichen ist, pruefen ob angehakt
        if self.item_type == self.TYPE_ZEICHEN:
            if self.checkState(self.COL_NAME) == Qt.CheckState.Checked:
                return [self]
            else:
                return []

        # Fuer Kategorien/Unterkategorien: Rekursiv alle Kinder durchsuchen
        # (unabhaengig vom eigenen Checkbox-Status)
        for i in range(self.childCount()):
            child = self.child(i)
            if isinstance(child, ZeichenTreeItem):
                zeichen.extend(child.get_checked_zeichen())

        return zeichen

    def propagate_params_to_children(self):
        """
        Propagiert Parameter an alle Kinder

        Setzt bei Kindern inherited=True
        """
        if self.item_type == self.TYPE_ZEICHEN:
            return

        for i in range(self.childCount()):
            child = self.child(i)
            if isinstance(child, ZeichenTreeItem):
                # Parameter kopieren
                child.params.modus = self.params.modus
                child.params.text = self.params.text
                # v7.1: grafik_position, grafik_max_hoehe, grafik_max_breite entfernt (jetzt global)
                child.params.inherited = True

                # Rekursiv
                child.propagate_params_to_children()

    def get_effective_params(self) -> ZeichenParameter:
        """
        Gibt effektive Parameter zurueck (mit Vererbung)

        Returns:
            ZeichenParameter: Effektive Parameter
        """
        # Wenn eigene Parameter (nicht geerbt), verwende diese
        if not self.params.inherited:
            return self.params

        # Sonst Parent-Parameter holen
        parent = self.parent()
        if isinstance(parent, ZeichenTreeItem):
            return parent.get_effective_params()

        # Root: Eigene Parameter
        return self.params

    def is_checked(self) -> bool:
        """Gibt zurueck ob Item angehakt ist"""
        return self.checkState(self.COL_NAME) == Qt.CheckState.Checked

    def set_checked(self, checked: bool):
        """Setzt Checkbox-Status"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.setCheckState(self.COL_NAME, state)

    def __repr__(self) -> str:
        """String-Repraesentation fuer Debugging"""
        return f"ZeichenTreeItem(type={self.item_type}, name={self.name})"


# ================================================================================================
# HELPER-FUNKTIONEN
# ================================================================================================

def create_category_item(name: str, parent: Optional[QTreeWidgetItem] = None) -> ZeichenTreeItem:
    """
    Erstellt Kategorie-Item

    Args:
        name: Kategorie-Name
        parent: Parent-Item

    Returns:
        ZeichenTreeItem: Kategorie-Item
    """
    return ZeichenTreeItem(ZeichenTreeItem.TYPE_CATEGORY, name, parent=parent)


def create_subcategory_item(name: str, parent: QTreeWidgetItem) -> ZeichenTreeItem:
    """
    Erstellt Unterkategorie-Item

    Args:
        name: Unterkategorie-Name
        parent: Parent-Item

    Returns:
        ZeichenTreeItem: Unterkategorie-Item
    """
    return ZeichenTreeItem(ZeichenTreeItem.TYPE_SUBCATEGORY, name, parent=parent)


def create_zeichen_item(name: str, svg_path: Path, parent: QTreeWidgetItem) -> ZeichenTreeItem:
    """
    Erstellt Zeichen-Item

    Args:
        name: Zeichen-Name
        svg_path: Pfad zur SVG-Datei
        parent: Parent-Item

    Returns:
        ZeichenTreeItem: Zeichen-Item
    """
    return ZeichenTreeItem(ZeichenTreeItem.TYPE_ZEICHEN, name, svg_path, parent)
