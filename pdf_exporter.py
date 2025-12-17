#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_exporter.py - PDF-Export für taktische Zeichen

Zwei Export-Varianten:
1. Einzelzeichen: Jedes Zeichen auf eigener Seite (51x51mm bei 600 DPI)
2. Schnittbogen: Mehrere Zeichen auf DIN A4 (45x45mm pro Zeichen)

Version: 1.0.0
"""

from pathlib import Path
from typing import List, Optional
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from io import BytesIO
from datetime import datetime
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from logging_manager import LoggingManager
from runtime_config import get_config
from settings_manager import SettingsManager
from constants import (
    PROGRAM_NAME,
    PROGRAM_VERSION,
    DEFAULT_ZEICHEN_HOEHE_MM,
    DEFAULT_ZEICHEN_BREITE_MM,
    DEFAULT_BESCHNITTZUGABE_MM,
    DEFAULT_SICHERHEITSABSTAND_MM,
    DEFAULT_PDF_CHUNK_SIZE,
    DEFAULT_PDF_CHUNK_SIZE_SCHNITTBOGEN,
    DEFAULT_S1_LINKS_PROZENT,
    DEFAULT_S1_ANZAHL_SCHREIBLINIEN,
    DEFAULT_S1_STAERKE_ANZEIGEN,
    DIN_A4_WIDTH_MM,
    DIN_A4_HEIGHT_MM,
    MIN_PDF_LAST_CHUNK_SIZE,
    EXPORT_TIMESTAMP_FORMAT,
    create_pdf_filename
)


def set_no_print_scaling(canvas_obj):
    """
    Setzt ViewerPreferences um Auto-Skalierung in Adobe Acrobat zu verhindern.

    Verhindert, dass Adobe Acrobat PDFs automatisch auf 97% skaliert
    (Fit to printable area). Benutzer sehen nun standardmäßig 100%
    ("Tatsächliche Größe").

    NEW v0.8.2: Fix für Adobe PDF 97%-Skalierungsproblem
    FIXED v0.8.2.1: Korrekte ReportLab API für ViewerPreferences

    Args:
        canvas_obj: ReportLab Canvas Objekt

    Returns:
        None
    """
    logger = LoggingManager().get_logger(__name__)
    try:
        # Zugriff auf internes PDF-Dokument
        from reportlab.pdfbase.pdfdoc import PDFDictionary, PDFName

        if hasattr(canvas_obj, '_doc') and hasattr(canvas_obj._doc, 'Catalog'):
            # ViewerPreferences Dictionary korrekt erstellen mit ReportLab API
            # /PrintScaling /None verhindert Auto-Skalierung beim Drucken
            vp = PDFDictionary()
            vp['PrintScaling'] = PDFName('None')
            canvas_obj._doc.Catalog.ViewerPreferences = vp
            logger.debug("ViewerPreferences erfolgreich gesetzt: PrintScaling=None")
    except ImportError as e:
        # ReportLab-Version unterstützt PDFDictionary/PDFName nicht
        logger.debug(f"ViewerPreferences nicht verfügbar (alte ReportLab-Version): {e}")
    except Exception as e:
        # Andere Fehler - einfach ignorieren
        logger.debug(f"ViewerPreferences konnten nicht gesetzt werden: {e}")


class PDFExporter:
    """
    Erstellt PDF-Dokumente mit taktischen Zeichen

    Features:
    - Variante 1: Einzelzeichen (jedes Zeichen auf eigener Seite)
    - Variante 2: Schnittbogen (mehrere Zeichen auf A4)
    - Schnittlinien-Support
    - Metadaten
    """

    def __init__(self):
        """Initialisiert PDFExporter"""
        self.logger = LoggingManager().get_logger(__name__)
        self.logger.info("PDFExporter v1.0 initialisiert")

    def create_einzelzeichen_pdf(
        self,
        images: List[Image.Image],
        output_path: Path,
        dpi: int = 600,
        draw_cut_lines: bool = False,
        progress_callback: Optional[callable] = None,
        zeichen_hoehe_mm: float = None,
        zeichen_breite_mm: float = None,
        beschnittzugabe_mm: float = None
    ) -> Path:
        """
        Erstellt PDF mit Einzelzeichen (jedes Zeichen auf eigener Seite)

        Seitengröße entspricht der Druckgröße (z.B. 51x51mm bei 45mm Zeichen + 3mm Beschnitt)

        Args:
            images: Liste von PIL Images (bereits druckfertig mit Beschnitt)
            output_path: Ausgabe-PDF-Datei
            dpi: Auflösung (für Metadaten)
            draw_cut_lines: Schnittlinien anzeigen (alle 3 Linien)
            progress_callback: Optional callback(current, total, status)
            zeichen_hoehe_mm: Höhe des fertigen Zeichens (NACH Zuschnitt)
            zeichen_breite_mm: Breite des fertigen Zeichens (NACH Zuschnitt)
            beschnittzugabe_mm: Beschnittzugabe (wird auf allen Seiten hinzugefügt)

        Returns:
            Path zur erstellten PDF-Datei
        """
        # RuntimeConfig-Defaults laden falls nicht angegeben
        from runtime_config import get_config
        config = get_config()
        if zeichen_hoehe_mm is None:
            zeichen_hoehe_mm = config.zeichen_hoehe_mm
        if zeichen_breite_mm is None:
            zeichen_breite_mm = config.zeichen_breite_mm
        if beschnittzugabe_mm is None:
            beschnittzugabe_mm = config.beschnittzugabe_mm

        self.logger.info("Erstelle Einzelzeichen-PDF: {} Zeichen".format(len(images)))

        # PDF-Canvas erstellen
        # Seitengröße = Zeichengröße + 2×Beschnitt (z.B. 45mm + 2×3mm = 51mm)
        datei_hoehe_mm = zeichen_hoehe_mm + 2 * beschnittzugabe_mm
        datei_breite_mm = zeichen_breite_mm + 2 * beschnittzugabe_mm
        page_size = (datei_breite_mm * mm, datei_hoehe_mm * mm)
        c = canvas.Canvas(str(output_path), pagesize=page_size)

        # Metadaten
        c.setTitle("Taktische Zeichen - Einzelzeichen")
        c.setAuthor(f"{PROGRAM_NAME}")
        c.setSubject("{} taktische Zeichen".format(len(images)))
        c.setCreator( "{} {}".format(PROGRAM_NAME, PROGRAM_VERSION))

        # NEW v0.8.2: ViewerPreferences setzen (verhindert Adobe Auto-Skalierung)
        set_no_print_scaling(c)

        # Jedes Zeichen auf eigener Seite
        for idx, img in enumerate(images):
            if progress_callback:
                progress_callback(
                    idx + 1,
                    len(images),
                    "Erstelle PDF-Seite {}/{}".format(idx + 1, len(images))
                )

            # Image zu ImageReader konvertieren (für ReportLab)
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_reader = ImageReader(img_buffer)

            # Image auf Seite platzieren (linksbündig, bottom-up Koordinaten)
            # ReportLab: (0,0) ist links-unten
            c.drawImage(
                img_reader,
                0, 0,
                width=datei_breite_mm * mm,
                height=datei_hoehe_mm * mm,
                preserveAspectRatio=True
            )

            # Nächste Seite (außer bei letztem Zeichen)
            if idx < len(images) - 1:
                c.showPage()

        # PDF speichern
        c.save()

        self.logger.info("Einzelzeichen-PDF erstellt: {}".format(output_path))
        return output_path

    def create_schnittbogen_pdf(
        self,
        images: List[Image.Image],
        output_path: Path,
        dpi: int = 600,
        draw_cut_lines: bool = False,
        progress_callback: Optional[callable] = None,
        zeichen_hoehe_mm: float = None,
        zeichen_breite_mm: float = None,
        beschnittzugabe_mm: float = None,
        sicherheitsabstand_mm: float = None
    ) -> Path:
        """
        Erstellt PDF mit Schnittbogen (mehrere Zeichen auf A4)

        Zeichen werden in optimaler Anzahl auf DIN A4 angeordnet.
        Größe pro Zeichen: fertige Größe ohne Beschnitt (z.B. 45x45mm)

        Args:
            images: Liste von PIL Images (bereits druckfertig mit Beschnitt)
            output_path: Ausgabe-PDF-Datei
            dpi: Auflösung
            draw_cut_lines: Schnittlinien anzeigen
                            False: Nur Schnittlinie (fertige Größe - blau)
                            True: Schnittlinie + Canvas-Linie (grün)
            progress_callback: Optional callback(current, total, status)
            zeichen_hoehe_mm: Höhe des fertigen Zeichens (NACH Zuschnitt)
            zeichen_breite_mm: Breite des fertigen Zeichens (NACH Zuschnitt)
            beschnittzugabe_mm: Beschnittzugabe (wird beim Croppen entfernt)
            sicherheitsabstand_mm: Sicherheitsabstand (für Canvas-Linie)

        Returns:
            Path zur erstellten PDF-Datei
        """
        # RuntimeConfig-Defaults laden falls nicht angegeben
        from runtime_config import get_config
        config = get_config()
        if zeichen_hoehe_mm is None:
            zeichen_hoehe_mm = config.zeichen_hoehe_mm
        if zeichen_breite_mm is None:
            zeichen_breite_mm = config.zeichen_breite_mm
        if beschnittzugabe_mm is None:
            beschnittzugabe_mm = config.beschnittzugabe_mm
        if sicherheitsabstand_mm is None:
            sicherheitsabstand_mm = config.sicherheitsabstand_mm

        self.logger.info("Erstelle Schnittbogen-PDF: {} Zeichen".format(len(images)))

        # A4-Seitengröße
        page_width, page_height = A4

        # Seitenränder aus Settings laden (NEW v0.8.2)
        from settings_manager import SettingsManager
        settings = SettingsManager().load_settings()

        if hasattr(settings, 'pdf_margin_horizontal_mm'):
            margin_h = settings.pdf_margin_horizontal_mm * mm  # Links/Rechts
        else:
            margin_h = 10 * mm  # Fallback

        if hasattr(settings, 'pdf_margin_vertical_mm'):
            margin_v = settings.pdf_margin_vertical_mm * mm  # Oben/Unten
        else:
            margin_v = 10 * mm  # Fallback

        # NEW v0.8.2: Automatische Hoch/Quer-Erkennung
        # Berechne für beide Orientierungen, wie viele Zeichen passen
        # Portrait: 210x297mm
        portrait_width = DIN_A4_WIDTH_MM * mm
        portrait_height = DIN_A4_HEIGHT_MM * mm
        portrait_avail_w = portrait_width - 2 * margin_h
        portrait_avail_h = portrait_height - 2 * margin_v
        portrait_cols = int(portrait_avail_w / (zeichen_breite_mm * mm))
        portrait_rows = int(portrait_avail_h / (zeichen_hoehe_mm * mm))
        portrait_per_page = portrait_cols * portrait_rows

        # Landscape: 297x210mm
        landscape_width = DIN_A4_HEIGHT_MM * mm
        landscape_height = DIN_A4_WIDTH_MM * mm
        landscape_avail_w = landscape_width - 2 * margin_h
        landscape_avail_h = landscape_height - 2 * margin_v
        landscape_cols = int(landscape_avail_w / (zeichen_breite_mm * mm))
        landscape_rows = int(landscape_avail_h / (zeichen_hoehe_mm * mm))
        landscape_per_page = landscape_cols * landscape_rows

        # Wähle die Orientierung mit mehr Zeichen/Seite
        if landscape_per_page > portrait_per_page:
            # Querformat ist besser
            page_width = landscape_width
            page_height = landscape_height
            pagesize = landscape(A4)
            orientation = "Querformat"
            self.logger.info(
                "Automatische Orientierung: Querformat gewählt "
                f"({landscape_per_page} Zeichen/Seite vs {portrait_per_page} im Hochformat)"
            )
        else:
            # Hochformat ist besser (oder gleich)
            page_width = portrait_width
            page_height = portrait_height
            pagesize = A4
            orientation = "Hochformat"
            self.logger.info(
                "Automatische Orientierung: Hochformat gewählt "
                f"({portrait_per_page} Zeichen/Seite vs {landscape_per_page} im Querformat)"
            )

        # Verfügbare Fläche (mit horizontalen und vertikalen Rändern)
        available_width = page_width - 2 * margin_h
        available_height = page_height - 2 * margin_v

        # Zeichen-Größe: fertige Größe (z.B. 45mm oder 56×96mm)
        zeichen_hoehe = zeichen_hoehe_mm * mm
        zeichen_breite = zeichen_breite_mm * mm

        # Optimale Anzahl Spalten/Zeilen berechnen (RECHTECKIG!)
        # v7.1 FIX: Verwende tatsächliche Dimensionen statt max()
        # Spalten = Breite des Zeichens, Zeilen = Höhe des Zeichens
        cols = int(available_width / zeichen_breite)
        rows = int(available_height / zeichen_hoehe)

        zeichen_per_page = cols * rows

        # NEW v0.8.2.1: Grid zentrieren (horizontal und vertikal)
        # Tatsächlich genutzte Grid-Größe
        grid_width = cols * zeichen_breite
        grid_height = rows * zeichen_hoehe

        # Überschüssiger Platz
        excess_width = available_width - grid_width
        excess_height = available_height - grid_height

        # Grid-Offset für Zentrierung
        grid_offset_x = margin_h + (excess_width / 2)
        grid_offset_y = margin_v + (excess_height / 2)

        self.logger.info(
            "Schnittbogen-Layout: {}x{} = {} Zeichen/Seite (A4 {} mit {}mm h / {}mm v Rand, zentriert)".format(
                cols, rows, zeichen_per_page, orientation, margin_h / mm, margin_v / mm
            )
        )

        # PDF-Canvas erstellen
        c = canvas.Canvas(str(output_path), pagesize=pagesize)

        # Metadaten
        c.setTitle("Taktische Zeichen - Schnittbogen")
        c.setAuthor(f"{PROGRAM_NAME}")
        c.setSubject("{} taktische Zeichen".format(len(images)))
        c.setCreator( "{} {}".format(PROGRAM_NAME, PROGRAM_VERSION))

        # NEW v0.8.2: ViewerPreferences setzen (verhindert Adobe Auto-Skalierung)
        set_no_print_scaling(c)

        # NEW v0.8.2.1: Hinweistext für Druckeinstellungen (falls ViewerPreferences nicht greifen)
        def draw_print_hint(canvas_obj, pagesize):
            """Zeichnet Hinweistext für korrekte Druckeinstellungen (oben UND unten)"""
            w, h = pagesize
            canvas_obj.saveState()
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.setFillColorRGB(0.5, 0.5, 0.5)  # Grau
            hint_text = "WICHTIG: In Druckeinstellungen 'Tatsächliche Größe' (100%) wählen - NICHT skalieren!"
            text_width = canvas_obj.stringWidth(hint_text, "Helvetica", 8)
            # Zentriert am oberen Rand, knapp unterhalb
            canvas_obj.drawString((w - text_width) / 2, h - 8 * mm, hint_text)
            # Zentriert am unteren Rand, knapp oberhalb
            canvas_obj.drawString((w - text_width) / 2, 8 * mm, hint_text)
            canvas_obj.restoreState()

        # Zeichen auf Seiten verteilen
        page_num = 0

        # Hinweistext auf erste Seite zeichnen
        draw_print_hint(c, pagesize)

        for idx, img in enumerate(images):
            if progress_callback and idx % 10 == 0:
                progress_callback(
                    idx + 1,
                    len(images),
                    "Platziere Zeichen {}/{}".format(idx + 1, len(images))
                )

            # Position auf aktueller Seite
            pos_on_page = idx % zeichen_per_page
            col = pos_on_page % cols
            row = pos_on_page // cols

            # Neue Seite wenn nötig
            if idx > 0 and pos_on_page == 0:
                c.showPage()
                page_num += 1
                # Hinweistext auf neue Seite zeichnen
                draw_print_hint(c, pagesize)

            # Zeichen muss auf fertige Größe skaliert werden (Beschnitt abschneiden)
            # FIXED: Übergebe alle Parameter für rechteckige Zeichen
            img_cropped = self._crop_to_final_size(
                img, dpi, zeichen_hoehe_mm, zeichen_breite_mm, beschnittzugabe_mm
            )

            # X, Y Position berechnen (zentriert)
            # ReportLab: (0,0) ist links-unten
            # FIXED: Verwende tatsächliche Dimensionen für Grid-Layout (rechteckig!)
            # NEW v0.8.2.1: Zentriertes Grid mit Offset
            x = grid_offset_x + col * zeichen_breite
            # Y von oben zählen, mit Zentrierung
            y = page_height - grid_offset_y - (row + 1) * zeichen_hoehe

            # Image zu ImageReader konvertieren
            img_buffer = BytesIO()
            img_cropped.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_reader = ImageReader(img_buffer)

            # Image auf Seite platzieren
            # FIXED: Verwende tatsächliche Zeichen-Dimensionen (rechteckig!)
            c.drawImage(
                img_reader,
                x, y,
                width=zeichen_breite,
                height=zeichen_hoehe,
                preserveAspectRatio=True
            )

            # Schnittlinien zeichnen (optional)
            if draw_cut_lines:
                self._draw_schnittbogen_cut_lines(
                    c, x, y, zeichen_breite, zeichen_hoehe,
                    sicherheitsabstand_mm, draw_canvas_line=True
                )
            else:
                # Nur Schnittlinie (fertige Größe - blau)
                self._draw_schnittbogen_cut_lines(
                    c, x, y, zeichen_breite, zeichen_hoehe,
                    sicherheitsabstand_mm, draw_canvas_line=False
                )

        # PDF speichern
        c.save()

        total_pages = (len(images) - 1) // zeichen_per_page + 1
        self.logger.info(
            "Schnittbogen-PDF erstellt: {} Seiten, {} Zeichen".format(
                total_pages, len(images)
            )
        )
        return output_path

    def _crop_to_final_size(
        self,
        img: Image.Image,
        dpi: int,
        zeichen_hoehe_mm: float,
        zeichen_breite_mm: float,
        beschnittzugabe_mm: float
    ) -> Image.Image:
        """
        Schneidet Beschnittzugabe ab (z.B. 51mm -> 45mm)

        Args:
            img: PIL Image (mit Beschnitt, z.B. 51x51mm)
            dpi: Auflösung
            zeichen_hoehe_mm: Fertige Höhe NACH Zuschnitt
            zeichen_breite_mm: Fertige Breite NACH Zuschnitt
            beschnittzugabe_mm: Beschnittzugabe auf jeder Seite

        Returns:
            PIL Image (fertige Größe, z.B. 45x45mm)
        """
        # Beschnitt in Pixel umrechnen
        beschnitt_px = int((beschnittzugabe_mm / 25.4) * dpi)

        # Crop-Box: Beschnitt auf allen Seiten abschneiden
        left = beschnitt_px
        top = beschnitt_px
        right = img.width - beschnitt_px
        bottom = img.height - beschnitt_px

        cropped = img.crop((left, top, right, bottom))

        return cropped

    def _draw_schnittbogen_cut_lines(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        breite: float,
        hoehe: float,
        sicherheitsabstand_mm: float,
        draw_canvas_line: bool = False
    ):
        """
        Zeichnet Schnittlinien für Schnittbogen (RECHTECKIGE Zeichen unterstützt!)

        Args:
            c: ReportLab Canvas
            x: X-Position (links-unten)
            y: Y-Position (links-unten)
            breite: Zeichen-Breite in mm (z.B. 45mm)
            hoehe: Zeichen-Höhe in mm (z.B. 45mm)
            sicherheitsabstand_mm: Sicherheitsabstand in mm (z.B. 3mm)
            draw_canvas_line: Canvas-Linie auch zeichnen
        """
        # Linienstärke
        line_width = 0.5

        # BLAU: Schnittlinie (fertige Größe - äußerer Rand)
        c.setStrokeColorRGB(0, 0, 1)  # Blau
        c.setLineWidth(line_width)
        c.rect(x, y, breite, hoehe, stroke=1, fill=0)

        # GRÜN: Canvas-Linie (zur Kontrolle)
        if draw_canvas_line:
            # Sicherheitsrand in mm konvertieren
            sicherheit_mm = sicherheitsabstand_mm * mm

            c.setStrokeColorRGB(0, 1, 0)  # Grün
            c.setLineWidth(line_width)
            c.rect(
                x + sicherheit_mm,
                y + sicherheit_mm,
                breite - 2 * sicherheit_mm,
                hoehe - 2 * sicherheit_mm,
                stroke=1,
                fill=0
            )


def _create_test_pdf_filename(
    variant: str,
    count: int,
    dpi: int,
    output_dir: Path
) -> Path:
    """
    Erstellt PDF-Dateinamen fuer Test-Sektion (INTERNAL)

    HINWEIS: Diese Funktion wird nur in __main__ Test-Sektion verwendet.
    Fuer Production-Code verwende create_pdf_filename() aus constants.py!

    Args:
        variant: 'Einzelzeichen' oder 'Schnittbogen'
        count: Anzahl Zeichen
        dpi: Aufloesung
        output_dir: Ausgabe-Ordner

    Returns:
        Path: Vollstaendiger Dateipfad
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = "{}_{}_{}Zeichen_{}dpi.pdf".format(
        timestamp,
        variant,
        count,
        dpi
    )
    return output_dir / filename


# REMOVED (v0.6.0): Funktion nach constants.py verschoben als create_pdf_filename()
# Verwende stattdessen: from constants import create_pdf_filename


def create_einzelzeichen_pdf_streaming(
    generator,
    tasks: List,
    output_path: Path,
    dpi: int,
    draw_cut_lines: bool = False,
    progress_callback: Optional[callable] = None,
    chunk_start: int = 0,
    total_zeichen: int = None,
    zeichen_hoehe_mm: float = None,
    zeichen_breite_mm: float = None,
    beschnittzugabe_mm: float = None,
    s1_links_prozent: int = DEFAULT_S1_LINKS_PROZENT,
    s1_anzahl_schreiblinien: int = DEFAULT_S1_ANZAHL_SCHREIBLINIEN,
    s1_staerke_anzeigen: bool = DEFAULT_S1_STAERKE_ANZEIGEN
) -> Path:
    """
    Erstellt Einzelzeichen-PDF mit Streaming (RAM-effizient)

    STREAMING: Rendert Zeichen einzeln, fügt sie sofort zur PDF hinzu
    und gibt RAM frei. Keine Liste von Images im RAM!

    Args:
        generator: TaktischeZeichenGenerator Instanz
        tasks: Liste von (svg_path, config) Tupeln
        output_path: Ausgabe-PDF-Datei
        dpi: Auflösung
        draw_cut_lines: Schnittlinien zeichnen
        progress_callback: Optional callback(current, total, zeichen_name, status)
        chunk_start: Start-Index für Progress-Callback
        total_zeichen: Gesamtzahl Zeichen für Progress-Callback
        zeichen_hoehe_mm: Höhe des fertigen Zeichens
        zeichen_breite_mm: Breite des fertigen Zeichens
        beschnittzugabe_mm: Beschnittzugabe

    Returns:
        Path zur erstellten PDF-Datei
    """
    logger = LoggingManager().get_logger(__name__)

    # RuntimeConfig-Defaults laden falls nicht angegeben
    config = get_config()
    if zeichen_hoehe_mm is None:
        zeichen_hoehe_mm = config.zeichen_hoehe_mm
    if zeichen_breite_mm is None:
        zeichen_breite_mm = config.zeichen_breite_mm
    if beschnittzugabe_mm is None:
        beschnittzugabe_mm = config.beschnittzugabe_mm

    if total_zeichen is None:
        total_zeichen = len(tasks)

    logger.info(f"Erstelle Einzelzeichen-PDF (Streaming): {len(tasks)} Zeichen")

    # PDF-Canvas erstellen
    datei_hoehe_mm = zeichen_hoehe_mm + 2 * beschnittzugabe_mm
    datei_breite_mm = zeichen_breite_mm + 2 * beschnittzugabe_mm
    page_size = (datei_breite_mm * mm, datei_hoehe_mm * mm)
    c = canvas.Canvas(str(output_path), pagesize=page_size)

    # Metadaten
    c.setTitle("Taktische Zeichen - Einzelzeichen")
    c.setAuthor(f"{PROGRAM_NAME}")
    c.setSubject(f"{len(tasks)} taktische Zeichen")
    c.setCreator(f"{PROGRAM_NAME} {PROGRAM_VERSION}")

    # NEW v0.8.2: ViewerPreferences setzen (verhindert Adobe Auto-Skalierung)
    set_no_print_scaling(c)

    # STREAMING: Zeichen einzeln rendern und direkt zur PDF hinzufügen
    for idx, (svg_path, config) in enumerate(tasks):
        try:
            # Progress Callback
            if progress_callback:
                progress_callback(
                    chunk_start + idx + 1,
                    total_zeichen,
                    svg_path.stem,
                    "Erstelle PDF-Seite"
                )

            # CRITICAL: S1-Layout erkennen (2:1 Aspect Ratio)
            is_s1_layout = False
            expected_breite = config.zeichen_hoehe_mm * 2.0
            if abs(config.zeichen_breite_mm - expected_breite) < 0.1:  # Toleranz 0.1mm
                is_s1_layout = True

            # Zeichen als Image rendern (nur 1 im RAM!)
            # NEW: Layout-spezifische Methode aufrufen
            if is_s1_layout:
                img = generator.create_zeichen_s1(
                    svg_path=svg_path,
                    config=config,
                    s1_links_prozent=s1_links_prozent,
                    s1_anzahl_schreiblinien=s1_anzahl_schreiblinien,
                    s1_staerke_anzeigen=s1_staerke_anzeigen,
                    draw_cut_lines=draw_cut_lines,
                    return_image=True
                )
            else:
                img = generator.create_zeichen(
                    svg_path=svg_path,
                    config=config,
                    draw_cut_lines=draw_cut_lines,
                    return_image=True
                )

            # Image zu ImageReader konvertieren
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_reader = ImageReader(img_buffer)

            # Image auf Seite platzieren
            c.drawImage(
                img_reader,
                0, 0,
                width=datei_breite_mm * mm,
                height=datei_hoehe_mm * mm,
                preserveAspectRatio=True
            )

            # Nächste Seite (außer bei letztem Zeichen)
            if idx < len(tasks) - 1:
                c.showPage()

            # RAM SOFORT freigeben!
            del img
            del img_buffer
            del img_reader

            # Alle 5 Zeichen: Garbage Collection
            if (idx + 1) % 5 == 0:
                gc.collect()

        except Exception as e:
            logger.error(f"Fehler bei {svg_path.stem}: {e}")
            # Weitermachen mit nächstem Zeichen

    # PDF speichern
    c.save()

    # Finale GC
    gc.collect()

    logger.info(f"Einzelzeichen-PDF erstellt (Streaming): {output_path}")
    return output_path


def create_schnittbogen_pdf_streaming(
    generator,
    tasks: List,
    output_path: Path,
    dpi: int,
    draw_cut_lines: bool = False,
    progress_callback: Optional[callable] = None,
    chunk_start: int = 0,
    total_zeichen: int = None,
    zeichen_hoehe_mm: float = None,
    zeichen_breite_mm: float = None,
    beschnittzugabe_mm: float = None,
    sicherheitsabstand_mm: float = None,
    s1_links_prozent: int = DEFAULT_S1_LINKS_PROZENT,
    s1_anzahl_schreiblinien: int = DEFAULT_S1_ANZAHL_SCHREIBLINIEN,
    s1_staerke_anzeigen: bool = DEFAULT_S1_STAERKE_ANZEIGEN
) -> Path:
    """
    Erstellt Schnittbogen-PDF mit Streaming (RAM-effizient)

    STREAMING: Rendert Zeichen einzeln, platziert sie direkt auf A4-Seiten.
    Keine Liste von Images im RAM!

    Args:
        generator: TaktischeZeichenGenerator Instanz
        tasks: Liste von (svg_path, config) Tupeln
        output_path: Ausgabe-PDF-Datei
        dpi: Auflösung
        draw_cut_lines: Schnittlinien zeichnen
        progress_callback: Optional callback(current, total, zeichen_name, status)
        chunk_start: Start-Index für Progress-Callback
        total_zeichen: Gesamtzahl Zeichen für Progress-Callback
        zeichen_hoehe_mm: Höhe des fertigen Zeichens
        zeichen_breite_mm: Breite des fertigen Zeichens
        beschnittzugabe_mm: Beschnittzugabe
        sicherheitsabstand_mm: Sicherheitsabstand

    Returns:
        Path zur erstellten PDF-Datei
    """
    logger = LoggingManager().get_logger(__name__)

    # RuntimeConfig-Defaults laden falls nicht angegeben
    config = get_config()
    if zeichen_hoehe_mm is None:
        zeichen_hoehe_mm = config.zeichen_hoehe_mm
    if zeichen_breite_mm is None:
        zeichen_breite_mm = config.zeichen_breite_mm
    if beschnittzugabe_mm is None:
        beschnittzugabe_mm = config.beschnittzugabe_mm
    if sicherheitsabstand_mm is None:
        sicherheitsabstand_mm = config.sicherheitsabstand_mm

    if total_zeichen is None:
        total_zeichen = len(tasks)

    logger.info(f"Erstelle Schnittbogen-PDF (Streaming): {len(tasks)} Zeichen")

    # Seitenränder aus Settings laden (NEW v0.8.2)
    settings = SettingsManager().load_settings()

    if hasattr(settings, 'pdf_margin_horizontal_mm'):
        margin_h = settings.pdf_margin_horizontal_mm * mm  # Links/Rechts
    else:
        margin_h = 10 * mm  # Fallback

    if hasattr(settings, 'pdf_margin_vertical_mm'):
        margin_v = settings.pdf_margin_vertical_mm * mm  # Oben/Unten
    else:
        margin_v = 10 * mm  # Fallback

    # NEW v0.8.2: Automatische Hoch/Quer-Erkennung
    # Berechne für beide Orientierungen, wie viele Zeichen passen
    # Portrait: 210x297mm
    portrait_width = DIN_A4_WIDTH_MM * mm
    portrait_height = DIN_A4_HEIGHT_MM * mm
    portrait_avail_w = portrait_width - 2 * margin_h
    portrait_avail_h = portrait_height - 2 * margin_v
    portrait_cols = int(portrait_avail_w / (zeichen_breite_mm * mm))
    portrait_rows = int(portrait_avail_h / (zeichen_hoehe_mm * mm))
    portrait_per_page = portrait_cols * portrait_rows

    # Landscape: 297x210mm
    landscape_width = DIN_A4_HEIGHT_MM * mm
    landscape_height = DIN_A4_WIDTH_MM * mm
    landscape_avail_w = landscape_width - 2 * margin_h
    landscape_avail_h = landscape_height - 2 * margin_v
    landscape_cols = int(landscape_avail_w / (zeichen_breite_mm * mm))
    landscape_rows = int(landscape_avail_h / (zeichen_hoehe_mm * mm))
    landscape_per_page = landscape_cols * landscape_rows

    # Wähle die Orientierung mit mehr Zeichen/Seite
    if landscape_per_page > portrait_per_page:
        # Querformat ist besser
        pagesize = landscape(A4)
        orientation = "Querformat"
        logger.info(
            "Automatische Orientierung: Querformat gewählt "
            f"({landscape_per_page} Zeichen/Seite vs {portrait_per_page} im Hochformat)"
        )
    else:
        # Hochformat ist besser (oder gleich)
        pagesize = A4
        orientation = "Hochformat"
        logger.info(
            "Automatische Orientierung: Hochformat gewählt "
            f"({portrait_per_page} Zeichen/Seite vs {landscape_per_page} im Querformat)"
        )

    # A4-Canvas erstellen mit optimaler Orientierung
    c = canvas.Canvas(str(output_path), pagesize=pagesize)
    page_width, page_height = pagesize

    # Metadaten
    c.setTitle("Taktische Zeichen - Schnittbogen")
    c.setAuthor(f"{PROGRAM_NAME}")
    c.setSubject(f"{len(tasks)} taktische Zeichen")
    c.setCreator(f"{PROGRAM_NAME} {PROGRAM_VERSION}")

    # NEW v0.8.2: ViewerPreferences setzen (verhindert Adobe Auto-Skalierung)
    set_no_print_scaling(c)

    # Verfügbare Fläche (mit horizontalen und vertikalen Rändern)
    available_width = page_width - 2 * margin_h
    available_height = page_height - 2 * margin_v

    # Zeichen-Größe: fertige Größe (z.B. 45x45mm oder 45x90mm)
    zeichen_hoehe = zeichen_hoehe_mm * mm
    zeichen_breite = zeichen_breite_mm * mm

    # CRITICAL FIX: Grid IMMER auf finale Größe berechnen!
    # Schnittlinien dürfen Layout NICHT ändern (User-Anforderung)
    # Grid-Zellen-Größe = Fertige Zeichengröße (NACH Zuschnitt)
    grid_cell_width = zeichen_breite
    grid_cell_height = zeichen_hoehe

    # Optimale Anzahl Spalten/Zeilen berechnen (basierend auf finaler Zeichengröße!)
    cols = int(available_width / zeichen_breite)
    rows = int(available_height / zeichen_hoehe)
    zeichen_per_page = cols * rows

    # NEW v0.8.2.1: Grid zentrieren (horizontal und vertikal)
    # Tatsächlich genutzte Grid-Größe
    grid_width = cols * zeichen_breite
    grid_height = rows * zeichen_hoehe

    # Überschüssiger Platz
    excess_width = available_width - grid_width
    excess_height = available_height - grid_height

    # Grid-Offset für Zentrierung
    grid_offset_x = margin_h + (excess_width / 2)
    grid_offset_y = margin_v + (excess_height / 2)

    logger.info(
        "Schnittbogen-Layout: {}x{} = {} Zeichen/Seite ({:.1f}x{:.1f}mm Zeichen, A4 {} mit {:.0f}mm h / {:.0f}mm v Rand)".format(
            cols, rows, zeichen_per_page, zeichen_breite_mm, zeichen_hoehe_mm,
            orientation, margin_h / mm, margin_v / mm
        )
    )

    # NEW v0.8.2.1: Hinweistext für Druckeinstellungen (falls ViewerPreferences nicht greifen)
    def draw_print_hint(canvas_obj, pagesize_tuple):
        """Zeichnet Hinweistext für korrekte Druckeinstellungen (oben UND unten)"""
        w, h = pagesize_tuple
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColorRGB(0.5, 0.5, 0.5)  # Grau
        hint_text = "WICHTIG: In Druckeinstellungen 'Tatsächliche Größe' (100%) wählen - NICHT skalieren!"
        text_width = canvas_obj.stringWidth(hint_text, "Helvetica", 8)
        # Zentriert am oberen Rand, knapp unterhalb
        canvas_obj.drawString((w - text_width) / 2, h - 8 * mm, hint_text)
        # Zentriert am unteren Rand, knapp oberhalb
        canvas_obj.drawString((w - text_width) / 2, 8 * mm, hint_text)
        canvas_obj.restoreState()

    # Hinweistext auf erste Seite zeichnen
    draw_print_hint(c, pagesize)

    # STREAMING: Zeichen einzeln rendern und direkt platzieren
    for idx, (svg_path, config) in enumerate(tasks):
        try:
            # Progress Callback
            if progress_callback:
                progress_callback(
                    chunk_start + idx + 1,
                    total_zeichen,
                    svg_path.stem,
                    "Platziere Zeichen"
                )

            # Position auf aktueller Seite
            pos_on_page = idx % zeichen_per_page
            col = pos_on_page % cols
            row = pos_on_page // cols

            # Neue Seite wenn nötig
            if idx > 0 and pos_on_page == 0:
                c.showPage()
                # Hinweistext auf neue Seite zeichnen
                draw_print_hint(c, pagesize)

            # CRITICAL: S1-Layout erkennen (2:1 Aspect Ratio)
            is_s1_layout = False
            expected_breite = config.zeichen_hoehe_mm * 2.0
            if abs(config.zeichen_breite_mm - expected_breite) < 0.1:  # Toleranz 0.1mm
                is_s1_layout = True

            # Zeichen als Image rendern (nur 1 im RAM!)
            # NEW: Layout-spezifische Methode aufrufen
            if is_s1_layout:
                img = generator.create_zeichen_s1(
                    svg_path=svg_path,
                    config=config,
                    s1_links_prozent=s1_links_prozent,
                    s1_anzahl_schreiblinien=s1_anzahl_schreiblinien,
                    s1_staerke_anzeigen=s1_staerke_anzeigen,
                    draw_cut_lines=draw_cut_lines,
                    return_image=True
                )
            else:
                img = generator.create_zeichen(
                    svg_path=svg_path,
                    config=config,
                    draw_cut_lines=draw_cut_lines,
                    return_image=True
                )

            logger.debug(f"Schnittbogen: draw_cut_lines={draw_cut_lines}, img_size={img.size}")

            # CRITICAL FIX: IMMER auf finale Größe croppen (auch mit Schnittlinien!)
            # Beschnittzugabe wird abgeschnitten - rote Linie liegt außerhalb (User-Anforderung)
            # Layout muss IDENTISCH sein mit/ohne Schnittlinien
            beschnitt_px = int((beschnittzugabe_mm / 25.4) * dpi)
            final_width_px = int((zeichen_breite_mm / 25.4) * dpi)
            final_height_px = int((zeichen_hoehe_mm / 25.4) * dpi)

            img_cropped = img.crop((
                beschnitt_px,
                beschnitt_px,
                beschnitt_px + final_width_px,
                beschnitt_px + final_height_px
            ))

            # Zeichen IMMER in finaler Größe (Layout-konstant!)
            display_width_mm = zeichen_breite_mm
            display_height_mm = zeichen_hoehe_mm

            # Position berechnen (zentriert mit grid_offset)
            # ReportLab: (0,0) ist links-unten
            # Grid basiert auf finaler Zeichengröße (IMMER gleich!)
            # X-Position: von links nach rechts
            x = grid_offset_x + (col * grid_cell_width)
            # Y-Position: von oben nach unten (Y von oben zählen)
            y = page_height - grid_offset_y - ((row + 1) * grid_cell_height)

            # Image zu ImageReader konvertieren
            img_buffer = BytesIO()
            img_cropped.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_reader = ImageReader(img_buffer)

            # Image platzieren (Größe abhängig von Schnittlinien)
            c.drawImage(
                img_reader,
                x, y,
                width=display_width_mm * mm,
                height=display_height_mm * mm,
                preserveAspectRatio=True
            )

            # IMMER schwarzen Rahmen zeichnen (Schnittlinie)
            # Zeigt dem User wo geschnitten werden muss
            from reportlab.lib.colors import black
            c.setStrokeColor(black)
            c.setLineWidth(0.5)  # 0.5pt dünne Linie
            c.rect(x, y, display_width_mm * mm, display_height_mm * mm, stroke=1, fill=0)

            # RAM SOFORT freigeben!
            del img
            del img_cropped
            del img_buffer
            del img_reader

            # Alle 5 Zeichen: Garbage Collection
            if (idx + 1) % 5 == 0:
                gc.collect()

        except Exception as e:
            logger.error(f"Fehler bei {svg_path.stem}: {e}")
            # Weitermachen mit nächstem Zeichen

    # PDF speichern
    c.save()

    # Finale GC
    gc.collect()

    logger.info(f"Schnittbogen-PDF erstellt (Streaming): {output_path}")
    return output_path


def _generate_images_parallel(
    generator,
    tasks: List,
    draw_cut_lines: bool,
    num_threads: int,
    progress_callback: Optional[callable] = None,
    chunk_start: int = 0,
    total_zeichen: int = None
) -> List[Image.Image]:
    """
    Generiert Images parallel mit Multithreading (Hilfsfunktion für PDF-Export)

    NEW (v7.2): Fügt Multithreading zum PDF-Export hinzu

    Args:
        generator: TaktischeZeichenGenerator Instanz
        tasks: Liste von (svg_path, config) Tupeln
        draw_cut_lines: Schnittlinien zeichnen
        num_threads: Anzahl paralleler Threads
        progress_callback: Optional callback(current, total, zeichen_name, status)
        chunk_start: Start-Index für Progress-Callback (für stapelbasierte Verarbeitung)
        total_zeichen: Gesamtzahl Zeichen für Progress-Callback

    Returns:
        List[Image.Image]: Liste der generierten PIL Images
    """
    logger = LoggingManager().get_logger(__name__)

    if total_zeichen is None:
        total_zeichen = len(tasks)

    images = []
    completed = 0
    stats_lock = Lock()

    def worker(idx: int, svg_path, config):
        """Worker-Funktion für Thread-Pool"""
        try:
            # Zeichen als Image erstellen (NICHT speichern!)
            img = generator.create_zeichen(
                svg_path=svg_path,
                config=config,
                draw_cut_lines=draw_cut_lines,
                return_image=True  # WICHTIG: Gibt PIL Image zurück
            )
            return (idx, img, None)
        except Exception as e:
            logger.error("Fehler bei {}: {}".format(svg_path.stem, str(e)))
            return (idx, None, str(e))

    # ThreadPoolExecutor für parallele Verarbeitung
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Tasks submiten
        futures = {}
        for idx, (svg_path, config) in enumerate(tasks):
            future = executor.submit(worker, idx, svg_path, config)
            futures[future] = (idx, svg_path)

        # Images in richtiger Reihenfolge sammeln (wichtig für PDF!)
        results = {}
        for future in as_completed(futures):
            idx, svg_path = futures[future]
            task_idx, img, error = future.result()

            # Thread-safe Update
            with stats_lock:
                completed += 1

                if img is not None:
                    results[task_idx] = img

                # Progress Callback (bei jedem Zeichen, nicht nur alle 5)
                if progress_callback:
                    progress_callback(
                        chunk_start + completed,
                        total_zeichen,
                        svg_path.stem,
                        "Generiere Zeichen"
                    )

    # Images in richtiger Reihenfolge zurückgeben
    images = [results[i] for i in range(len(tasks)) if i in results]

    logger.info("Parallel-Generierung abgeschlossen: {} Images mit {} Threads".format(
        len(images), num_threads))

    return images


def create_einzelzeichen_pdf_chunked(
    generator,
    tasks: List,
    output_dir: Path,
    dpi: int,
    draw_cut_lines: bool = False,
    progress_callback: Optional[callable] = None,
    chunk_size: int = DEFAULT_PDF_CHUNK_SIZE,
    export_format: str = "Einzelzeichen",  # NEW (v0.6.0)
    zeichen_hoehe_mm: float = None,  # NEW (v7.1): Aus Settings
    zeichen_breite_mm: float = None,  # NEW (v7.1): Aus Settings
    beschnittzugabe_mm: float = None,  # NEW (v7.1): Aus Settings
    num_threads: int = 6,  # Erhöht von 4 auf 6 (moderne CPUs)
    s1_links_prozent: int = DEFAULT_S1_LINKS_PROZENT,
    s1_anzahl_schreiblinien: int = DEFAULT_S1_ANZAHL_SCHREIBLINIEN,
    s1_staerke_anzeigen: bool = DEFAULT_S1_STAERKE_ANZEIGEN
) -> List[Path]:
    """
    Erstellt mehrere Einzelzeichen-PDFs mit Stapelbasierter Verarbeitung

    NEW (v0.6.0): Reduziert RAM-Verbrauch von ~12,5 GB auf ~2,5 GB
    NEW (v7.1): Unterstützt dynamische Zeichengrößen aus Settings
    NEW (v7.2): Multithreading für deutlich schnellere PDF-Generierung

    Args:
        generator: TaktischeZeichenGenerator Instanz
        tasks: Liste von (svg_path, config) Tupeln
        output_dir: Ausgabe-Ordner (wird erstellt falls nicht vorhanden)
        dpi: Auflösung
        draw_cut_lines: Schnittlinien zeichnen
        progress_callback: Optional callback(current, total, status)
        chunk_size: Anzahl Seiten pro PDF-Datei (default: 100)
        export_format: Exportformat für Dateinamen (default: "Einzelzeichen")
        zeichen_hoehe_mm: Höhe des fertigen Zeichens (aus Settings)
        zeichen_breite_mm: Breite des fertigen Zeichens (aus Settings)
        beschnittzugabe_mm: Beschnittzugabe (aus Settings)
        num_threads: Anzahl paralleler Threads (default: 4)

    Returns:
        List[Path]: Liste aller erstellten PDF-Dateien

    Example:
        pdf_files = create_einzelzeichen_pdf_chunked(
            generator, tasks, output_dir, dpi=600, chunk_size=100,
            export_format="Einzelzeichen",
            zeichen_hoehe_mm=45.0, zeichen_breite_mm=45.0, beschnittzugabe_mm=3.0,
            num_threads=6
        )
    """
    # RuntimeConfig-Defaults laden falls nicht angegeben
    config = get_config()
    if zeichen_hoehe_mm is None:
        zeichen_hoehe_mm = config.zeichen_hoehe_mm
    if zeichen_breite_mm is None:
        zeichen_breite_mm = config.zeichen_breite_mm
    if beschnittzugabe_mm is None:
        beschnittzugabe_mm = config.beschnittzugabe_mm

    total_zeichen = len(tasks)
    logger = LoggingManager().get_logger(__name__)

    # Output-Ordner erstellen
    output_dir.mkdir(parents=True, exist_ok=True)

    # Zeitstempel für alle PDFs gleich (aus constants.py)
    timestamp = datetime.now().strftime(EXPORT_TIMESTAMP_FORMAT)

    # Stapel-Berechnung mit Merge-Logik
    num_chunks_raw = (total_zeichen + chunk_size - 1) // chunk_size
    last_chunk_size = total_zeichen % chunk_size if total_zeichen % chunk_size != 0 else chunk_size

    # NEW: Wenn letzte Datei < MIN_PDF_LAST_CHUNK_SIZE Seiten: In vorletzte integrieren
    if num_chunks_raw > 1 and last_chunk_size < MIN_PDF_LAST_CHUNK_SIZE:
        num_chunks = num_chunks_raw - 1  # Eine Datei weniger
        logger.info("Letzte Datei hätte nur {} Seiten -> Merge in vorletzte Datei".format(last_chunk_size))
    else:
        num_chunks = num_chunks_raw

    logger.info("Erstelle {} PDF-Dateien (Stapelgröße: {})".format(num_chunks, chunk_size))

    pdf_files = []

    for chunk_idx in range(num_chunks):
        # Stapel-Grenzen berechnen
        start = chunk_idx * chunk_size
        if chunk_idx == num_chunks - 1 and num_chunks < num_chunks_raw:
            # LETZTE Datei bei Merge: Nimm Rest
            end = total_zeichen
        else:
            end = min(start + chunk_size, total_zeichen)

        chunk_tasks = tasks[start:end]

        logger.info("PDF {}/{}: Zeichen {} bis {} ({} Seiten)".format(
            chunk_idx + 1, num_chunks,
            start + 1, end,
            len(chunk_tasks)
        ))

        # PDF für Stapel erstellen (CHANGED v0.6.0: Neue Namenskonvention)
        pdf_filename = create_pdf_filename(
            timestamp=timestamp,
            export_format=export_format,
            start_idx=start + 1,
            end_idx=end,
            file_idx=chunk_idx + 1,
            total_files=num_chunks
        )
        pdf_path = output_dir / pdf_filename

        # STREAMING (v7.3): Zeichen einzeln rendern statt alle im RAM
        # Spart massiv RAM bei großen Zeichen!
        create_einzelzeichen_pdf_streaming(
            generator=generator,
            tasks=chunk_tasks,
            output_path=pdf_path,
            dpi=dpi,
            draw_cut_lines=draw_cut_lines,
            progress_callback=progress_callback,
            chunk_start=start,
            total_zeichen=total_zeichen,
            zeichen_hoehe_mm=zeichen_hoehe_mm,
            zeichen_breite_mm=zeichen_breite_mm,
            beschnittzugabe_mm=beschnittzugabe_mm,
            s1_links_prozent=s1_links_prozent,
            s1_anzahl_schreiblinien=s1_anzahl_schreiblinien,
            s1_staerke_anzeigen=s1_staerke_anzeigen
        )

        pdf_files.append(pdf_path)
        logger.info("PDF erstellt: {}".format(pdf_filename))

        # GC nach jedem Stapel (zusätzlich zu GC in Streaming-Funktion)
        gc.collect()

    logger.info("Alle {} PDF-Dateien erstellt".format(len(pdf_files)))
    return pdf_files


def create_schnittbogen_pdf_chunked(
    generator,
    tasks: List,
    output_dir: Path,
    dpi: int,
    draw_cut_lines: bool = False,
    progress_callback: Optional[callable] = None,
    chunk_size: int = DEFAULT_PDF_CHUNK_SIZE_SCHNITTBOGEN,
    export_format: str = "Schnittbogen",  # NEW (v0.6.0)
    zeichen_hoehe_mm: float = None,  # NEW (v7.1): Aus Settings
    zeichen_breite_mm: float = None,  # NEW (v7.1): Aus Settings
    beschnittzugabe_mm: float = None,
    sicherheitsabstand_mm: float = None,  # NEW (v7.1): Aus Settings
    num_threads: int = 6,  # Erhöht von 4 auf 6 (moderne CPUs)
    s1_links_prozent: int = DEFAULT_S1_LINKS_PROZENT,
    s1_anzahl_schreiblinien: int = DEFAULT_S1_ANZAHL_SCHREIBLINIEN,
    s1_staerke_anzeigen: bool = DEFAULT_S1_STAERKE_ANZEIGEN
) -> List[Path]:
    """
    Erstellt mehrere Schnittbogen-PDFs mit Stapelbasierter Verarbeitung

    NEW (v0.6.0): Reduziert RAM-Verbrauch bei großen Schnittbögen
    NEW (v7.1): Unterstützt dynamische Zeichengrößen aus Settings
    NEW (v7.2): Multithreading für deutlich schnellere PDF-Generierung

    HINWEIS: Stapelgröße ist in SEITEN (nicht Zeichen!)
    Bei 24 Zeichen/Seite: 50 Seiten = 1200 Zeichen

    Args:
        generator: TaktischeZeichenGenerator Instanz
        tasks: Liste von (svg_path, config) Tupeln
        output_dir: Ausgabe-Ordner
        dpi: Auflösung
        draw_cut_lines: Schnittlinien zeichnen
        progress_callback: Optional callback(current, total, status)
        chunk_size: Anzahl SEITEN pro PDF-Datei (default: 50)
        export_format: Exportformat für Dateinamen (default: "Schnittbogen")
        zeichen_hoehe_mm: Höhe des fertigen Zeichens (aus Settings)
        zeichen_breite_mm: Breite des fertigen Zeichens (aus Settings)
        beschnittzugabe_mm: Beschnittzugabe (aus Settings)
        sicherheitsabstand_mm: Sicherheitsabstand (aus Settings)
        num_threads: Anzahl paralleler Threads (default: 4)

    Returns:
        List[Path]: Liste aller erstellten PDF-Dateien
    """
    # RuntimeConfig-Defaults laden falls nicht angegeben
    config = get_config()
    if zeichen_hoehe_mm is None:
        zeichen_hoehe_mm = config.zeichen_hoehe_mm
    if zeichen_breite_mm is None:
        zeichen_breite_mm = config.zeichen_breite_mm
    if beschnittzugabe_mm is None:
        beschnittzugabe_mm = config.beschnittzugabe_mm
    if sicherheitsabstand_mm is None:
        sicherheitsabstand_mm = config.sicherheitsabstand_mm

    total_zeichen = len(tasks)
    logger = LoggingManager().get_logger(__name__)

    # Output-Ordner erstellen
    output_dir.mkdir(parents=True, exist_ok=True)

    # Zeitstempel für alle PDFs gleich (aus constants.py)
    timestamp = datetime.now().strftime(EXPORT_TIMESTAMP_FORMAT)

    # Berechne Zeichen pro Seite (A4, 45mm Zeichen)
    # Optimale Anzahl: 4 Spalten x 6 Zeilen = 24 Zeichen/Seite
    zeichen_per_page = 24

    # Zeichen pro Chunk (nicht Seiten!)
    zeichen_per_chunk = chunk_size * zeichen_per_page

    # Stapel-Berechnung
    num_chunks_raw = (total_zeichen + zeichen_per_chunk - 1) // zeichen_per_chunk
    last_chunk_zeichen = total_zeichen % zeichen_per_chunk if total_zeichen % zeichen_per_chunk != 0 else zeichen_per_chunk
    last_chunk_pages = (last_chunk_zeichen + zeichen_per_page - 1) // zeichen_per_page

    # NEW: Merge-Logik (analog zu Einzelzeichen)
    if num_chunks_raw > 1 and last_chunk_pages < MIN_PDF_LAST_CHUNK_SIZE:
        num_chunks = num_chunks_raw - 1
        logger.info("Letzte Datei hätte nur {} Seiten -> Merge in vorletzte Datei".format(last_chunk_pages))
    else:
        num_chunks = num_chunks_raw

    logger.info("Erstelle {} Schnittbogen-PDFs (Stapelgröße: {} Seiten)".format(num_chunks, chunk_size))

    pdf_files = []

    for chunk_idx in range(num_chunks):
        # Stapel-Grenzen berechnen
        start = chunk_idx * zeichen_per_chunk
        if chunk_idx == num_chunks - 1 and num_chunks < num_chunks_raw:
            # LETZTE Datei bei Merge: Nimm Rest
            end = total_zeichen
        else:
            end = min(start + zeichen_per_chunk, total_zeichen)

        chunk_tasks = tasks[start:end]

        logger.info("PDF {}/{}: Zeichen {} bis {} ({} Zeichen, ~{} Seiten)".format(
            chunk_idx + 1, num_chunks,
            start + 1, end,
            len(chunk_tasks),
            (len(chunk_tasks) + zeichen_per_page - 1) // zeichen_per_page
        ))

        # PDF für Stapel erstellen (CHANGED v0.6.0: Neue Namenskonvention)
        pdf_filename = create_pdf_filename(
            timestamp=timestamp,
            export_format=export_format,
            start_idx=start + 1,
            end_idx=end,
            file_idx=chunk_idx + 1,
            total_files=num_chunks
        )
        pdf_path = output_dir / pdf_filename

        # STREAMING (v7.3): Zeichen einzeln rendern statt alle im RAM
        # Spart massiv RAM bei großen Zeichen!
        create_schnittbogen_pdf_streaming(
            generator=generator,
            tasks=chunk_tasks,
            output_path=pdf_path,
            dpi=dpi,
            draw_cut_lines=draw_cut_lines,
            progress_callback=progress_callback,
            chunk_start=start,
            total_zeichen=total_zeichen,
            zeichen_hoehe_mm=zeichen_hoehe_mm,
            zeichen_breite_mm=zeichen_breite_mm,
            beschnittzugabe_mm=beschnittzugabe_mm,
            sicherheitsabstand_mm=sicherheitsabstand_mm,
            s1_links_prozent=s1_links_prozent,
            s1_anzahl_schreiblinien=s1_anzahl_schreiblinien,
            s1_staerke_anzeigen=s1_staerke_anzeigen
        )

        pdf_files.append(pdf_path)
        logger.info("PDF erstellt: {}".format(pdf_filename))

        # GC nach jedem Stapel (zusätzlich zu GC in Streaming-Funktion)
        gc.collect()

    logger.info("Alle {} PDF-Dateien erstellt".format(len(pdf_files)))
    return pdf_files


# ================================================================================================
# TESTING
# ================================================================================================

if __name__ == "__main__":
    import sys
    from PIL import Image, ImageDraw
    from constants import ORGANIZATIONAL_BLUE, COLOR_SCHWARZ

    print("=" * 80)
    print("PDFExporter Test")
    print("=" * 80)

    # Logging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )

    # Test-Images erstellen (51x51mm @ 600 DPI)
    dpi = 600
    datei_groesse_mm = DEFAULT_ZEICHEN_HOEHE_MM + (2 * DEFAULT_BESCHNITTZUGABE_MM)  # 45mm + 2×3mm = 51mm
    size_px = int((datei_groesse_mm / 25.4) * dpi)

    print("\n[TEST-IMAGES]")
    print("Erstelle 10 Test-Zeichen: {}x{}px ({}mm @ {} DPI)".format(
        size_px, size_px, datei_groesse_mm, dpi
    ))

    images = []
    for i in range(10):
        img = Image.new('RGB', (size_px, size_px), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Blaues Quadrat mit Nummer
        margin = 50
        draw.rectangle(
            [(margin, margin), (size_px - margin, size_px - margin)],
            fill=ORGANIZATIONAL_BLUE,
            outline=COLOR_SCHWARZ,
            width=5
        )

        # Nummer
        from PIL import ImageFont
        try:
            font = ImageFont.truetype("arial.ttf", 100)
        except:
            font = ImageFont.load_default()

        draw.text(
            (size_px // 2, size_px // 2),
            str(i + 1),
            fill=(255, 255, 255),
            font=font,
            anchor="mm"
        )

        images.append(img)

    print("Test-Images erstellt: {} Zeichen".format(len(images)))

    # PDFExporter
    exporter = PDFExporter()
    output_dir = Path(".")

    # Test 1: Einzelzeichen-PDF
    print("\n[TEST 1: EINZELZEICHEN-PDF]")
    print("-" * 80)

    pdf_einzelzeichen = _create_test_pdf_filename('Einzelzeichen', len(images), dpi, output_dir)
    exporter.create_einzelzeichen_pdf(
        images=images,
        output_path=pdf_einzelzeichen,
        dpi=dpi,
        draw_cut_lines=False
    )
    print("[OK] Einzelzeichen-PDF: {}".format(pdf_einzelzeichen))

    # Test 2: Schnittbogen-PDF
    print("\n[TEST 2: SCHNITTBOGEN-PDF]")
    print("-" * 80)

    pdf_schnittbogen = _create_test_pdf_filename('Schnittbogen', len(images), dpi, output_dir)
    exporter.create_schnittbogen_pdf(
        images=images,
        output_path=pdf_schnittbogen,
        dpi=dpi,
        draw_cut_lines=True
    )
    print("[OK] Schnittbogen-PDF: {}".format(pdf_schnittbogen))

    print("\n" + "=" * 80)
    print("[FERTIG] Beide PDF-Varianten erstellt!")
    print("=" * 80)