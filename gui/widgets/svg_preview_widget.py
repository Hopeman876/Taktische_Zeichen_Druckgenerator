#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
svg_preview_widget.py - SVG-Vorschau-Widget mit ImageMagick-Rendering

Custom Widget für SVG-Darstellung in Qt
"""

from pathlib import Path
from typing import Optional
from io import BytesIO

from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage

from wand.image import Image as WandImage

from logging_manager import LoggingManager


class SVGPreviewWidget(QLabel):
    """
    Custom Widget für SVG-Vorschau

    Features:
    - Rendert SVG mit Wand/ImageMagick
    - Automatische Größenanpassung
    - Cache für Performance
    - Fehlerbehandlung

    Example:
        preview = SVGPreviewWidget(parent)
        preview.load_svg(Path("zeichen.svg"))
        preview.set_preview_size(400, 400)
    """

    def __init__(self, parent=None):
        """Initialisiert SVG-Vorschau-Widget"""
        super().__init__(parent)

        self.logger = LoggingManager().get_logger(__name__)

        # Aktuelles SVG
        self.current_svg_path: Optional[Path] = None
        self.current_pixmap: Optional[QPixmap] = None

        # Vorschau-Größe (Standard: 400x400)
        self.preview_width = 400
        self.preview_height = 400

        # Widget-Konfiguration
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # Styling
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                background-color: #f5f5f5;
                padding: 10px;
            }
        """)

        # Platzhalter anzeigen
        self._show_placeholder("Kein Zeichen gewählt")

    def load_svg(self, svg_path: Path) -> bool:
        """
        Lädt SVG-Datei und rendert Vorschau

        Args:
            svg_path: Pfad zur SVG-Datei

        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        if not svg_path or not svg_path.exists():
            self.logger.error(f"SVG-Datei nicht gefunden: {svg_path}")
            self._show_error(f"Datei nicht gefunden:\n{svg_path}")
            return False

        try:
            self.logger.debug(f"Lade SVG: {svg_path.name}")

            # SVG mit Wand rendern
            pixmap = self._render_svg_to_pixmap(svg_path)

            if pixmap:
                self.current_svg_path = svg_path
                self.current_pixmap = pixmap
                self._display_pixmap(pixmap)
                self.logger.info(f"SVG geladen: {svg_path.name}")
                return True
            else:
                self._show_error("Fehler beim Rendern")
                return False

        except Exception as e:
            self.logger.error(f"Fehler beim Laden von {svg_path.name}: {e}")
            self._show_error(f"Fehler:\n{str(e)}")
            return False

    def _render_svg_to_pixmap(self, svg_path: Path) -> Optional[QPixmap]:
        """
        Rendert SVG zu QPixmap mit Wand/ImageMagick

        Args:
            svg_path: Pfad zur SVG-Datei

        Returns:
            QPixmap oder None bei Fehler
        """
        try:
            # SVG mit Wand öffnen und rendern
            with WandImage(filename=str(svg_path)) as img:
                # Auf Vorschau-Größe skalieren (Aspect Ratio beibehalten)
                img.transform(resize=f"{self.preview_width}x{self.preview_height}")

                # Format: PNG für beste Qualität
                img.format = 'png'

                # Zu Bytes konvertieren
                blob = img.make_blob()

                # QImage aus Bytes erstellen
                qimage = QImage.fromData(blob)

                # QPixmap aus QImage
                pixmap = QPixmap.fromImage(qimage)

                return pixmap

        except Exception as e:
            self.logger.error(f"Fehler beim Rendern: {e}")
            return None

    def _display_pixmap(self, pixmap: QPixmap):
        """
        Zeigt Pixmap im Label an (skaliert auf Widget-Größe)

        Args:
            pixmap: Anzuzeigendes Pixmap
        """
        if pixmap:
            # Auf Label-Größe skalieren (Aspect Ratio beibehalten)
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)

    def set_preview_size(self, width: int, height: int):
        """
        Setzt Vorschau-Größe (für Rendering)

        Args:
            width: Breite in Pixel
            height: Höhe in Pixel
        """
        self.preview_width = width
        self.preview_height = height

        # Aktuelles SVG neu rendern
        if self.current_svg_path:
            self.load_svg(self.current_svg_path)

    def clear(self):
        """Löscht Vorschau"""
        self.current_svg_path = None
        self.current_pixmap = None
        # CHANGED: Direkt Platzhalter setzen ohne clear() aufzurufen
        self.setText("Kein Zeichen gewählt")
        self.setPixmap(QPixmap())  # Leeres Pixmap
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                background-color: #f5f5f5;
                padding: 20px;
                color: #888;
                font-size: 14pt;
            }
        """)

    def reload(self):
        """Lädt aktuelles SVG neu"""
        if self.current_svg_path:
            self.load_svg(self.current_svg_path)

    def _show_placeholder(self, text: str):
        """
        Zeigt Platzhalter-Text

        Args:
            text: Anzuzeigender Text
        """
        # CHANGED: Nicht mehr clear() aufrufen (Rekursion vermeiden)
        self.current_svg_path = None
        self.current_pixmap = None
        self.setText(text)
        self.setPixmap(QPixmap())  # Leeres Pixmap
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                background-color: #f5f5f5;
                padding: 20px;
                color: #888;
                font-size: 14pt;
            }
        """)

    def _show_error(self, error_msg: str):
        """
        Zeigt Fehlermeldung

        Args:
            error_msg: Fehlermeldung
        """
        self.setText(f"Fehler beim Laden:\n{error_msg}")
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #f00;
                background-color: #ffe0e0;
                padding: 20px;
                color: #c00;
                font-size: 12pt;
            }
        """)

    def resizeEvent(self, event):
        """Qt Event: Widget wurde vergrößert/verkleinert"""
        super().resizeEvent(event)

        # Pixmap neu skalieren
        if self.current_pixmap:
            self._display_pixmap(self.current_pixmap)

    def sizeHint(self) -> QSize:
        """Gibt bevorzugte Widget-Größe zurück"""
        return QSize(self.preview_width, self.preview_height)


# ================================================================================================
# TESTING
# ================================================================================================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    from constants import DEFAULT_ZEICHEN_DIR

    print("=" * 80)
    print("SVG-VORSCHAU-WIDGET TEST")
    print("=" * 80)

    app = QApplication(sys.argv)

    # Test-Fenster
    window = QMainWindow()
    window.setWindowTitle("SVG Preview Widget Test")
    window.setMinimumSize(600, 600)

    # Central Widget
    central = QWidget()
    layout = QVBoxLayout()
    central.setLayout(layout)
    window.setCentralWidget(central)

    # Preview Widget
    preview = SVGPreviewWidget()
    layout.addWidget(preview)

    # Test: SVG laden (falls vorhanden)
    test_dir = DEFAULT_ZEICHEN_DIR
    if test_dir.exists():
        svg_files = list(test_dir.rglob("*.svg"))
        if svg_files:
            test_svg = svg_files[0]
            print(f"\n[TEST] Lade Test-SVG: {test_svg}")
            success = preview.load_svg(test_svg)
            print(f"[TEST] Erfolgreich: {success}")
        else:
            print(f"\n[INFO] Keine SVG-Dateien in {test_dir}")
    else:
        print(f"\n[INFO] Test-Verzeichnis nicht gefunden: {test_dir}")

    window.show()

    print("\n" + "=" * 80)
    print("[OK] Test-Fenster geöffnet")
    print("=" * 80)

    sys.exit(app.exec())
