#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text_overlay.py - Text-Overlay mit Platzhaltern

Version: 1.2.1 (v7.3 - 1-Zeilen-Modi in unterer Position)

WICHTIG - Offset-Handling:
- TEXT_GRAFIK_OFFSET_MM: Abstand zwischen Grafik (unten) und Text (oben)
- TEXT_BOTTOM_OFFSET_MM: Abstand zwischen Text (unten) und Sicherheitsrand (grüne Linie)
- calculate_text_height_mm() gibt IMMER: Text-Höhe (für 2 Zeilen!) + TEXT_BOTTOM_OFFSET_MM zurück
- TEXT_GRAFIK_OFFSET_MM wird separat im Generator abgezogen!

NEU v7.1 - Einheitliches Layout:
- ALLE Text-Modi reservieren IMMER Platz für 2 Zeilen
- Dadurch konsistente Grafik-Position über alle Modi hinweg
- Vereinfachte Berechnung und Template-Verwaltung
- Variable Schriftgrößen werden unterstützt (font_size Parameter)

NEU v7.3 - Text-Positionierung für bessere UX:
- 2-Zeilen-Modi (OV+Stärke, Ort+Stärke, Schreiblinie+Stärke): Text in Zeile 1 + 2
- 1-Zeilen-Modi (Ruf, Freitext, Dateiname): Text NUR in Zeile 2 (unten)
- Dadurch direkter Bezug zum Parameter "Abstand Text-Unterkante" für den User
- Grafik-Position bleibt weiterhin konsistent über alle Modi
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import logging
from dataclasses import dataclass
from typing import Optional, List, Union

from runtime_config import get_config
from font_manager import FontManager
from constants import (
    MODUS_OV_STAERKE,
    MODUS_ORT_STAERKE,
    MODUS_SCHREIBLINIE_STAERKE,
    MODUS_RUF,
    MODUS_OHNE_TEXT,
    MODUS_FREITEXT,
    MODUS_DATEINAME,
    GRAFIK_POSITION_CENTER,
    TEXT_COLOR,
    DEFAULT_FONT_SIZE,
    DEFAULT_ABSTAND_GRAFIK_TEXT_MM,  # NEW: User-konfigurierbare Version
    DEFAULT_TEXT_BOTTOM_OFFSET_MM,  # NEW: User-konfigurierbare Version
    LINE_HEIGHT_FACTOR,
    PLACEHOLDER_OV_LENGTH,
    PLACEHOLDER_RUF_LENGTH,
    PLACEHOLDER_STAERKE_DIGITS,
    DEFAULT_SICHERHEITSABSTAND_MM,
    DEFAULT_ZEICHEN_HOEHE_MM,
    DEFAULT_ZEICHEN_BREITE_MM,
    DEFAULT_BESCHNITTZUGABE_MM,
    POINTS_PER_INCH,
    TEMP_IMAGE_SIZE_PX,  # NEW: Für präzisere Textmessungen
    create_placeholder_text,
    create_staerke_placeholder,
    mm_to_pixels,
    pixels_to_mm
)


@dataclass
class ZeichenConfig:
    """
    Konfiguration fuer ein taktisches Zeichen

    NOTE (v7.3): font_size und font_family werden aus RuntimeConfig geladen (User-Settings)
    """
    zeichen_id: str
    svg_path: Path

    modus: str = MODUS_OV_STAERKE

    placeholder_ov_length: int = PLACEHOLDER_OV_LENGTH
    placeholder_ruf_length: int = PLACEHOLDER_RUF_LENGTH
    placeholder_staerke_format: Optional[List[int]] = None

    font_size: int = None  # Wird aus RuntimeConfig geladen (v7.3)
    font_family: str = None  # Wird aus RuntimeConfig geladen (v7.3)
    dpi: int = 600

    # NEW: Zeichenabmessungen aus GUI-Settings (für flexible Druckgröße)
    zeichen_hoehe_mm: float = None  # Wird aus RuntimeConfig geladen
    zeichen_breite_mm: float = None  # Wird aus RuntimeConfig geladen
    sicherheitsabstand_mm: float = None  # Wird aus RuntimeConfig geladen
    beschnittzugabe_mm: float = None  # Wird aus RuntimeConfig geladen

    # NEW: Text-Offset-Parameter (User-konfigurierbar)
    abstand_grafik_text_mm: float = None  # Wird aus RuntimeConfig geladen
    text_bottom_offset_mm: float = None  # Wird aus RuntimeConfig geladen

    def __post_init__(self):
        """Lädt Werte aus RuntimeConfig falls nicht gesetzt"""
        config = get_config()

        # Font-Parameter
        if self.font_size is None:
            self.font_size = config.font_size
        if self.font_family is None:
            self.font_family = config.font_family

        # Zeichenabmessungen
        if self.zeichen_hoehe_mm is None:
            self.zeichen_hoehe_mm = config.zeichen_hoehe_mm
        if self.zeichen_breite_mm is None:
            self.zeichen_breite_mm = config.zeichen_breite_mm
        if self.sicherheitsabstand_mm is None:
            self.sicherheitsabstand_mm = config.sicherheitsabstand_mm
        if self.beschnittzugabe_mm is None:
            self.beschnittzugabe_mm = config.beschnittzugabe_mm

        # Text-Offset-Parameter
        if self.abstand_grafik_text_mm is None:
            self.abstand_grafik_text_mm = config.abstand_grafik_text_mm
        if self.text_bottom_offset_mm is None:
            self.text_bottom_offset_mm = config.text_bottom_offset_mm

    # NEU: Phase 2 - Erweiterte Modi-Optionen
    # Für MODUS_OV_STAERKE: Echter OV-Name statt Platzhalter
    ov_name: Optional[str] = None  # None = Platzhalter verwenden

    # Für MODUS_ORT_STAERKE: Echter Ort-Name statt Platzhalter
    ort_name: Optional[str] = None  # None = Platzhalter verwenden

    # Für MODUS_FREITEXT: Freitext-Zeile
    freitext: Optional[str] = None

    # Für MODUS_OHNE_TEXT: Grafik-Positionierung
    grafik_position: str = GRAFIK_POSITION_CENTER  # "top", "center", "bottom"

    # v7.1: Für MODUS_OHNE_TEXT: Benutzerdefinierte Grafikgröße in mm (None = Maximum verwenden)
    custom_grafik_hoehe_mm: Optional[float] = None  # Höhe der Grafik
    custom_grafik_breite_mm: Optional[float] = None  # Breite der Grafik

    # v7.1 Phase 2: Render-Scale für Performance-Optimierung
    render_scale: float = 1.0  # Skalierungsfaktor für SVG-Rendering (1.0 = keine Skalierung)

    # NEW: Output-Verzeichnis (None = EXPORT_DIR verwenden)
    output_dir: Optional[Path] = None


class TextOverlayPlaceholder:
    """
    Fuegt Platzhalter-Text zu taktischen Zeichen hinzu
    
    WICHTIG (v2.3): Text wird DIREKT auf Canvas gezeichnet!
    """
    
    def __init__(self):
        """Initialisiert TextOverlay"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("TextOverlayPlaceholder v2.3 (OFFSET KORRIGIERT) initialisiert")
    
    def calculate_text_height_mm(self, config: ZeichenConfig) -> float:
        """
        Berechnet Text-Hoehe in mm (OHNE Text zu zeichnen)

        WICHTIG v7.1: Reserviert IMMER Platz für 2 Zeilen, unabhängig vom Modus!
        - Einheitliches Layout über alle Text-Modi
        - Konsistente Grafik-Position
        - Schriftgröße aus config.font_size wird berücksichtigt (variabel!)

        Rückgabe enthält IMMER: Text-Höhe (für 2 Zeilen) + TEXT_BOTTOM_OFFSET_MM
        TEXT_GRAFIK_OFFSET_MM wird NICHT zur Text-Höhe addiert, sondern separat
        im Generator von der Grafik-Höhe abgezogen.

        Beispiel (10pt Font @ 200 DPI):
        - 2 Zeilen Text (IMMER!): ~11.5mm
        - TEXT_BOTTOM_OFFSET_MM: 0.0mm (Abstand Text→Sicherheitsrand)
        - GESAMT: 11.5mm + 0.0mm = 11.5mm (wird zurückgegeben!)

        Args:
            config: Zeichen-Konfiguration (inkl. font_size!)

        Returns:
            Text-Hoehe in mm (IMMER für 2 Zeilen + Offset!)
        """
        if config.modus == MODUS_OHNE_TEXT:
            return 0.0

        if config.modus == MODUS_OV_STAERKE:
            text_lines = self._generate_ov_staerke_placeholders(config)
        elif config.modus == MODUS_ORT_STAERKE:  # NEW
            text_lines = self._generate_ort_staerke_placeholders(config)
        elif config.modus == MODUS_SCHREIBLINIE_STAERKE:  # NEW
            text_lines = self._generate_schreiblinie_staerke_placeholders(config)
        elif config.modus == MODUS_RUF:
            text_lines = self._generate_ruf_placeholders(config)
        elif config.modus == MODUS_FREITEXT:
            text_lines = self._generate_freitext_placeholders(config)
        elif config.modus == MODUS_DATEINAME:  # NEW
            text_lines = self._generate_dateiname_placeholders(config)
        else:
            # Fallback: Ruf
            text_lines = self._generate_ruf_placeholders(config)
        
        text_height_px = self._calculate_text_height_px(
            text_lines,
            config.font_size,
            config.dpi,
            config.text_bottom_offset_mm,
            config.zeichen_hoehe_mm,
            config.zeichen_breite_mm
        )
        
        text_height_mm = pixels_to_mm(text_height_px, config.dpi)
        
        self.logger.debug(
            "Text-Hoehe: {:.2f}mm ({}px) @ {} DPI".format(
                text_height_mm, text_height_px, config.dpi
            )
        )
        
        return text_height_mm

    def calculate_text_width_mm(self, config: ZeichenConfig) -> float:
        """
        Berechnet Text-Breite in mm (WICHTIG für Validierung!)

        Diese Methode berechnet die tatsächliche Breite des Textes,
        um zu prüfen, ob er in den sicheren Bereich passt.

        Args:
            config: Zeichen-Konfiguration

        Returns:
            float: Text-Breite in mm
        """
        # Font laden
        font = self._load_font(config.font_size, config.dpi, config.font_family)

        # Text-Zeilen generieren
        if config.modus == MODUS_OV_STAERKE:
            lines = self._generate_ov_staerke_placeholders(config)
        elif config.modus == MODUS_ORT_STAERKE:
            lines = self._generate_ort_staerke_placeholders(config)
        elif config.modus == MODUS_SCHREIBLINIE_STAERKE:
            lines = self._generate_schreiblinie_staerke_placeholders(config)
        elif config.modus == MODUS_RUF:
            lines = self._generate_ruf_placeholders(config)
        elif config.modus == MODUS_FREITEXT:
            lines = self._generate_freitext_placeholders(config)
        elif config.modus == MODUS_DATEINAME:
            lines = self._generate_dateiname_placeholders(config)
        else:
            # Kein Text-Modus
            return 0.0

        # Temp-Canvas für Breiten-Messung
        temp_img = Image.new('RGB', (TEMP_IMAGE_SIZE_PX, TEMP_IMAGE_SIZE_PX))
        temp_draw = ImageDraw.Draw(temp_img)

        # Breiteste Zeile finden
        max_width_px = 0
        for line in lines:
            bbox = temp_draw.textbbox((0, 0), line, font=font)
            text_width_px = bbox[2] - bbox[0]
            if text_width_px > max_width_px:
                max_width_px = text_width_px

        # In mm umrechnen
        text_width_mm = pixels_to_mm(max_width_px, config.dpi)

        self.logger.debug("Text-Breite: {:.2f}mm ({}px) @ {} DPI".format(
            text_width_mm, max_width_px, config.dpi))

        return text_width_mm

    def draw_text_on_canvas(
        self,
        canvas: Image.Image,
        config: ZeichenConfig
    ) -> None:
        """
        Zeichnet Text DIREKT auf Canvas (nicht auf Grafik!)
        
        WICHTIG: Text wird am UNTEREN Rand des Canvas positioniert!
        
        Canvas-Groesse: 39x39mm (921x921px @ 600 DPI)
        Text-Position: Y = canvas_height - text_height (AM UNTEREN RAND!)
        
        Args:
            canvas: 39mm Canvas (bereits mit Grafik)
            config: Zeichen-Konfiguration
        """
        if config.modus == MODUS_OHNE_TEXT:
            self.logger.debug("Modus OHNE_TEXT: Kein Text")
            return

        if config.modus == MODUS_OV_STAERKE:
            text_lines = self._generate_ov_staerke_placeholders(config)
        elif config.modus == MODUS_ORT_STAERKE:  # NEW
            text_lines = self._generate_ort_staerke_placeholders(config)
        elif config.modus == MODUS_SCHREIBLINIE_STAERKE:  # NEW
            text_lines = self._generate_schreiblinie_staerke_placeholders(config)
        elif config.modus == MODUS_RUF:
            text_lines = self._generate_ruf_placeholders(config)
        elif config.modus == MODUS_FREITEXT:
            text_lines = self._generate_freitext_placeholders(config)
        elif config.modus == MODUS_DATEINAME:  # NEW
            text_lines = self._generate_dateiname_placeholders(config)
        else:
            # Fallback: Ruf
            text_lines = self._generate_ruf_placeholders(config)
        
        self.logger.debug("Text-Zeilen: {}".format(text_lines))

        text_height_px = self._calculate_text_height_px(
            text_lines,
            config.font_size,
            config.dpi,
            config.text_bottom_offset_mm,
            config.zeichen_hoehe_mm,
            config.zeichen_breite_mm
        )

        # Y-Position: AM UNTEREN RAND!
        # WICHTIG: text_height_px enthaelt bereits den Offset!
        y_start = canvas.height - text_height_px

        self.logger.info(
            "Text am UNTEREN Rand: Y={}px (Canvas: {}px, Text: {}px)".format(
                y_start, canvas.height, text_height_px
            )
        )

        # NEW v0.8.2.1: MODUS_SCHREIBLINIE_STAERKE - Zeichne echte Linie statt Unterstriche
        if config.modus == MODUS_SCHREIBLINIE_STAERKE:
            from constants import S1_LINE_COLOR, S1_LINE_WIDTH, S1_LINE_MARGIN_MM, mm_to_pixels
            draw = ImageDraw.Draw(canvas)

            # FIXED v0.8.2.2: Margin und Breite wie rechte Seite
            # Nutze die volle config.zeichen_breite_mm (= Breite des linken Bereichs im S1-Layout)
            margin_px = mm_to_pixels(S1_LINE_MARGIN_MM, config.dpi)

            # FIXED v0.8.2.2: Berechne Linienbreite aus config statt canvas.width
            # Dies stellt sicher, dass die Linie immer die volle verfügbare Breite nutzt
            canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
            canvas_breite_px = mm_to_pixels(canvas_breite_mm, config.dpi)

            line_x_start = margin_px
            line_x_end = canvas_breite_px - margin_px

            self.logger.debug(
                f"S1-Schreiblinie: Canvas={canvas.width}px, Berechnet={canvas_breite_px}px, "
                f"Linie={line_x_start}px bis {line_x_end}px (Breite: {line_x_end - line_x_start}px)"
            )

            # Y-Position der Schreiblinie (erste Zeile)
            font = self._load_font(config.font_size, config.dpi)
            max_ascent, max_descent = self._get_max_font_metrics(config.font_size, config.dpi)
            y_baseline = y_start + max_ascent

            # Linie wie auf rechter Seite zeichnen
            draw.line(
                [(line_x_start, y_baseline), (line_x_end, y_baseline)],
                fill=S1_LINE_COLOR,
                width=S1_LINE_WIDTH
            )

            # Nur zweite Zeile (Stärke) als Text zeichnen (eine Zeile tiefer)
            if len(text_lines) > 1:
                from constants import LINE_HEIGHT_FACTOR, POINTS_PER_INCH
                font_size_px = int((config.font_size / POINTS_PER_INCH) * config.dpi)
                line_height_px = int(font_size_px * LINE_HEIGHT_FACTOR)

                self._draw_text_at_position(
                    canvas,
                    [text_lines[1]],  # Nur Stärke-Zeile
                    y_start + line_height_px,  # Eine Zeile tiefer
                    config.font_size,
                    config.dpi
                )

            self.logger.info(
                "Schreiblinie als echte Linie gezeichnet: {}px breit, Y={}px (volle Breite des linken Bereichs)".format(
                    line_x_end - line_x_start, y_baseline
                )
            )
        else:
            # Alle anderen Modi: Normale Text-Darstellung
            self._draw_text_at_position(
                canvas,
                text_lines,
                y_start,
                config.font_size,
                config.dpi
            )
    
    def _generate_ov_staerke_placeholders(self, config: ZeichenConfig) -> list:
        """
        Generiert Platzhalter fuer OV + Staerke Modus
        
        WICHTIG: Beide Zeilen muessen PIXEL-GLEICH breit sein!
        
        Strategie:
        1. Staerke-Zeile generieren
        2. OV-Zeile mit Unterstrichen fuellen (fast so breit wie Staerke)
        3. Beide Zeilen mit Leerzeichen auf GLEICHE Breite bringen
        """
        lines = []
        
        # Staerke-Zeile generieren
        if config.placeholder_staerke_format is not None:
            staerke_line = create_staerke_placeholder(config.placeholder_staerke_format)
        else:
            staerke_line = create_staerke_placeholder(PLACEHOLDER_STAERKE_DIGITS)
        
        # Font laden
        font = self._load_font(config.font_size, config.dpi, config.font_family)

        # Temporaeres Draw-Objekt
        temp_img = Image.new('RGB', (TEMP_IMAGE_SIZE_PX, TEMP_IMAGE_SIZE_PX))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Breite der Staerke-Zeile
        staerke_bbox = temp_draw.textbbox((0, 0), staerke_line, font=font)
        staerke_width_px = staerke_bbox[2] - staerke_bbox[0]
        
        self.logger.debug("Staerke: '{}' = {}px".format(staerke_line, staerke_width_px))
        
        # NEU: Phase 2 - Echter OV-Name oder Platzhalter
        ov_prefix = "OV: "
        if config.ov_name:
            # Echter OV-Name verwenden
            ov_text = ov_prefix + config.ov_name

            # NEU v0.8.1: Prüfe ob OV-Name zu lang ist
            ov_bbox = temp_draw.textbbox((0, 0), ov_text, font=font)
            ov_width = ov_bbox[2] - ov_bbox[0]

            # Wenn OV-Name breiter als Stärke-Zeile → prüfe Umbruch
            canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
            max_width_px = mm_to_pixels(canvas_breite_mm, config.dpi)

            if ov_width > max_width_px:
                # OV-Name zu lang → versuche Umbruch
                self.logger.warning(
                    "OV-Name '{}' zu lang ({}px > {}px) für OV+Stärke Modus - Text wird ggf. verkleinert".format(
                        ov_text, ov_width, max_width_px
                    )
                )

            ov_line = ov_text
        else:
            # OV-Zeile mit Unterstrichen fuellen (KNAPP unter Staerke-Breite)
            ov_line = ov_prefix

            # CHANGED: Stoppe BEVOR wir Staerke-Breite erreichen!
            while True:
                test_line = ov_line + "_"
                test_bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                test_width_px = test_bbox[2] - test_bbox[0]

                # Wenn mit einem weiteren "_" die Breite UEBER Staerke waere, stoppen!
                if test_width_px > staerke_width_px:
                    break

                ov_line = test_line

                # Sicherheits-Check
                if len(ov_line) > 200:
                    self.logger.warning("OV-Zeile zu lang (>200)!")
                    break
        
        # Aktuelle Breiten messen
        ov_bbox = temp_draw.textbbox((0, 0), ov_line, font=font)
        ov_width_px = ov_bbox[2] - ov_bbox[0]
        
        self.logger.debug("OV: '{}' = {}px".format(ov_line, ov_width_px))
        
        # CHANGED: Beide auf die LAENGERE Breite bringen mit Leerzeichen!
        target_width = max(ov_width_px, staerke_width_px)
        
        self.logger.debug("Ziel-Breite: {}px".format(target_width))
        
        # OV-Zeile auffuellen
        # FIXED: Wenn Leerzeichen zu weit überschießt, entfernen und akzeptieren
        prev_ov_line = ov_line
        prev_ov_width = ov_width_px
        while ov_width_px < target_width:
            prev_ov_line = ov_line
            prev_ov_width = ov_width_px
            ov_line += " "
            ov_bbox = temp_draw.textbbox((0, 0), ov_line, font=font)
            ov_width_px = ov_bbox[2] - ov_bbox[0]

            # FIXED: Wenn wir zu weit überschießen (>10px), nutze vorherige Version
            if ov_width_px > target_width + 10:
                ov_line = prev_ov_line
                ov_width_px = prev_ov_width
                self.logger.debug("OV: Leerzeichen überschießt zu weit, verwende vorherige Version")
                break

            # Sicherheit
            if len(ov_line) > 250:
                break

        # Staerke-Zeile auffuellen
        # FIXED: Wenn Leerzeichen zu weit überschießt, entfernen und akzeptieren
        prev_staerke_line = staerke_line
        prev_staerke_width = staerke_width_px
        while staerke_width_px < target_width:
            prev_staerke_line = staerke_line
            prev_staerke_width = staerke_width_px
            staerke_line += " "
            staerke_bbox = temp_draw.textbbox((0, 0), staerke_line, font=font)
            staerke_width_px = staerke_bbox[2] - staerke_bbox[0]

            # FIXED: Wenn wir zu weit überschießen (>10px), nutze vorherige Version
            if staerke_width_px > target_width + 10:
                staerke_line = prev_staerke_line
                staerke_width_px = prev_staerke_width
                self.logger.debug("Stärke: Leerzeichen überschießt zu weit, verwende vorherige Version")
                break

            # Sicherheit
            if len(staerke_line) > 250:
                break
        
        # Finale Breiten
        ov_bbox = temp_draw.textbbox((0, 0), ov_line, font=font)
        ov_width_px = ov_bbox[2] - ov_bbox[0]
        
        staerke_bbox = temp_draw.textbbox((0, 0), staerke_line, font=font)
        staerke_width_px = staerke_bbox[2] - staerke_bbox[0]
        
        diff = abs(ov_width_px - staerke_width_px)
        
        self.logger.debug("OV FINAL: {}px, Staerke FINAL: {}px, Diff: {}px".format(
            ov_width_px, staerke_width_px, diff
        ))

        # CHANGED: Toleranz von 3px auf 5px erhöht (Leerzeichen-Breite variiert)
        if diff > 5:  # Toleranz: 5px
            self.logger.warning("OV/Staerke immer noch {}px unterschiedlich!".format(diff))
        else:
            self.logger.debug("OV+Staerke OK: Differenz nur {}px".format(diff))  # CHANGED: INFO -> DEBUG
        
        lines.append(ov_line)
        lines.append(staerke_line)

        return lines

    def _generate_ort_staerke_placeholders(self, config: ZeichenConfig) -> list:
        """
        Generiert Platzhalter fuer Ort + Staerke Modus

        NEW: Wie OV + Staerke, aber "OV:" wird durch "Ort:" ersetzt
        """
        lines = []

        # Staerke-Zeile generieren
        if config.placeholder_staerke_format is not None:
            staerke_line = create_staerke_placeholder(config.placeholder_staerke_format)
        else:
            staerke_line = create_staerke_placeholder(PLACEHOLDER_STAERKE_DIGITS)

        # Font laden
        font = self._load_font(config.font_size, config.dpi, config.font_family)

        # Temporaeres Draw-Objekt
        temp_img = Image.new('RGB', (TEMP_IMAGE_SIZE_PX, TEMP_IMAGE_SIZE_PX))
        temp_draw = ImageDraw.Draw(temp_img)

        # Breite der Staerke-Zeile
        staerke_bbox = temp_draw.textbbox((0, 0), staerke_line, font=font)
        staerke_width_px = staerke_bbox[2] - staerke_bbox[0]

        # Ort-Zeile (analog zu OV-Zeile)
        ort_prefix = "Ort: "
        if config.ort_name:  # FIXED: Verwende ort_name statt ov_name
            ort_line = ort_prefix + config.ort_name
        else:
            ort_line = ort_prefix

            while True:
                test_line = ort_line + "_"
                test_bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                test_width_px = test_bbox[2] - test_bbox[0]

                if test_width_px > staerke_width_px:
                    break

                ort_line = test_line

                if len(ort_line) > 200:
                    break

        # Breiten angleichen (wie bei OV)
        ort_bbox = temp_draw.textbbox((0, 0), ort_line, font=font)
        ort_width_px = ort_bbox[2] - ort_bbox[0]

        if ort_width_px < staerke_width_px:
            while ort_width_px < staerke_width_px:
                test_line = ort_line + " "
                test_bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                test_width_px = test_bbox[2] - test_bbox[0]

                if test_width_px > staerke_width_px:
                    break

                ort_line = test_line
                ort_width_px = test_width_px

        lines.append(ort_line)
        lines.append(staerke_line)

        return lines

    def _generate_schreiblinie_staerke_placeholders(self, config: ZeichenConfig) -> list:
        """
        Generiert Platzhalter fuer Schreiblinie + Staerke Modus

        NEW: Wie OV + Staerke, aber statt "OV: ___" nur eine durchgehende Linie
        """
        lines = []

        # Staerke-Zeile generieren
        if config.placeholder_staerke_format is not None:
            staerke_line = create_staerke_placeholder(config.placeholder_staerke_format)
        else:
            staerke_line = create_staerke_placeholder(PLACEHOLDER_STAERKE_DIGITS)

        # Font laden
        font = self._load_font(config.font_size, config.dpi, config.font_family)

        # Temporaeres Draw-Objekt
        temp_img = Image.new('RGB', (TEMP_IMAGE_SIZE_PX, TEMP_IMAGE_SIZE_PX))
        temp_draw = ImageDraw.Draw(temp_img)

        # Breite der Staerke-Zeile
        staerke_bbox = temp_draw.textbbox((0, 0), staerke_line, font=font)
        staerke_width_px = staerke_bbox[2] - staerke_bbox[0]

        # Schreiblinie: Nur Unterstriche (kein Präfix)
        schreiblinie = ""

        while True:
            test_line = schreiblinie + "_"
            test_bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            test_width_px = test_bbox[2] - test_bbox[0]

            if test_width_px > staerke_width_px:
                break

            schreiblinie = test_line

            if len(schreiblinie) > 200:
                break

        # Breiten angleichen
        schreib_bbox = temp_draw.textbbox((0, 0), schreiblinie, font=font)
        schreib_width_px = schreib_bbox[2] - schreib_bbox[0]

        if schreib_width_px < staerke_width_px:
            while schreib_width_px < staerke_width_px:
                test_line = schreiblinie + " "
                test_bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                test_width_px = test_bbox[2] - test_bbox[0]

                if test_width_px > staerke_width_px:
                    break

                schreiblinie = test_line
                schreib_width_px = test_width_px

        lines.append(schreiblinie)
        lines.append(staerke_line)

        return lines

    def _wrap_text_to_two_lines(
        self,
        text: str,
        max_width_px: int,
        font_size: int,
        dpi: int,
        font_family: str = None
    ) -> list:
        """
        Bricht Text intelligent auf zwei Zeilen um wenn er zu lang ist

        Strategie:
        1. Prüfen ob Text auf eine Zeile passt → [zeile1_leer, text]
        2. Sonst: Text an Leerzeichen umbrechen → [text_teil1, text_teil2]
        3. Falls kein Leerzeichen: Hart umbrechen

        Args:
            text: Text zum Umbrechen
            max_width_px: Maximale Breite in Pixel (Canvas-Breite)
            font_size: Schriftgröße in Punkt
            dpi: Auflösung
            font_family: Optional Schriftart

        Returns:
            Liste mit 2 Zeilen [zeile1, zeile2]
        """
        font = self._load_font(font_size, dpi, font_family)

        # Temporäres Draw-Objekt für Breitenmessung
        temp_img = Image.new('RGB', (TEMP_IMAGE_SIZE_PX, TEMP_IMAGE_SIZE_PX))
        temp_draw = ImageDraw.Draw(temp_img)

        # Test: Passt der Text auf eine Zeile?
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width_px:
            # Text passt auf eine Zeile → in Zeile 2 (unten)
            return ["", text]

        self.logger.debug(
            "Text zu lang ({}px > {}px): '{}' - Umbrechen...".format(
                text_width, max_width_px, text
            )
        )

        # Text muss umgebrochen werden
        # Strategie: An Leerzeichen oder Bindestrichen trennen
        words = text.replace("-", "- ").split()  # Bindestriche werden zu Trennstellen

        if len(words) <= 1:
            # Kein Leerzeichen → Harter Umbruch
            mid = len(text) // 2
            return [text[:mid], text[mid:]]

        # Versuche intelligenten Umbruch: Suche optimale Trennstelle
        # Strategie: So viele Woerter wie moeglich in Zeile 1 packen
        best_line1 = ""
        best_line2 = text

        for i in range(1, len(words)):
            line1_candidate = " ".join(words[:i])
            line2_candidate = " ".join(words[i:])

            # Pruefe zuerst line1 - wenn diese zu lang ist, koennen wir abbrechen
            bbox1 = temp_draw.textbbox((0, 0), line1_candidate, font=font)
            width1 = bbox1[2] - bbox1[0]

            if width1 > max_width_px:
                # line1 zu lang -> keine weiteren Worte mehr moeglich
                break

            # Pruefe line2
            bbox2 = temp_draw.textbbox((0, 0), line2_candidate, font=font)
            width2 = bbox2[2] - bbox2[0]

            # Wenn beide passen, speichern und weitermachen (versuche mehr in line1 zu packen)
            if width2 <= max_width_px:
                best_line1 = line1_candidate
                best_line2 = line2_candidate
                # Weiter iterieren, um mehr Woerter in line1 zu packen
            # Sonst: line2 zu lang, aber line1 passt noch -> weiter versuchen

        if best_line1:
            self.logger.debug(
                "Text umgebrochen: '{}' | '{}'".format(best_line1, best_line2)
            )
            return [best_line1, best_line2]
        else:
            # Fallback: Harter Umbruch in der Mitte
            mid = len(text) // 2
            self.logger.warning(
                "Kein guter Umbruch gefunden, harter Umbruch bei Position {}".format(mid)
            )
            return [text[:mid], text[mid:]]

    def validate_text_fits(
        self,
        text: str,
        config: ZeichenConfig,
        max_lines: int = 2
    ) -> tuple:
        """
        Validiert ob Text auf das Zeichen passt (Stufe 1: focusOut-Validierung)

        Prueft ob der eingegebene Text mit der konfigurierten Schriftgroesse
        auf das Zeichen passt ohne Text-Wrapping zu beruecksichtigen.

        Args:
            text: Zu pruefender Text
            config: ZeichenConfig mit Dimensionen und Schrifteinstellungen
            max_lines: Maximale Anzahl verfuegbarer Zeilen (1 fuer S1, 2 fuer S2)

        Returns:
            tuple: (fits: bool, warning: Optional[str], estimated_lines: int)
                - fits: True wenn Text passt, False wenn zu lang
                - warning: Warnmeldung falls Text zu lang, None sonst
                - estimated_lines: Geschaetzte Anzahl benoetigter Zeilen
        """
        if not text or not text.strip():
            # Leerer Text passt immer
            return (True, None, 0)

        # Berechne verfuegbare Breite (Canvas-Breite abzueglich Sicherheitsabstaende)
        canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
        max_width_px = mm_to_pixels(canvas_breite_mm, config.dpi)

        # Font laden
        font = self._load_font(config.font_size, config.dpi, config.font_family)

        # Temporaeres Draw-Objekt fuer Breitenmessung
        temp_img = Image.new('RGB', (TEMP_IMAGE_SIZE_PX, TEMP_IMAGE_SIZE_PX))
        temp_draw = ImageDraw.Draw(temp_img)

        # Messe Text-Breite
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width_px = bbox[2] - bbox[0]

        # Pruefe ob Text auf eine Zeile passt
        if text_width_px <= max_width_px:
            return (True, None, 1)

        # Text passt nicht auf eine Zeile
        self.logger.debug(
            "Text-Validierung: '{}' zu lang ({}px > {}px)".format(
                text, text_width_px, max_width_px
            )
        )

        # Wenn nur 1 Zeile verfuegbar ist (S1-Layout)
        if max_lines == 1:
            warning = (
                "Text zu lang! Maximale Breite: {:.1f}mm. "
                "Reduziere die Textlaenge oder verkleinere die Schriftgroesse.".format(
                    canvas_breite_mm
                )
            )
            return (False, warning, 2)  # Schaetzung: 2 Zeilen benoetigt

        # Pruefe ob Text auf 2 Zeilen passt (S2-Layout)
        # Strategie: Versuche Text an Leerzeichen zu trennen
        words = text.replace("-", "- ").split()

        if len(words) <= 1:
            # Kein Leerzeichen → Harter Umbruch noetig
            mid = len(text) // 2
            line1 = text[:mid]
            line2 = text[mid:]

            bbox1 = temp_draw.textbbox((0, 0), line1, font=font)
            bbox2 = temp_draw.textbbox((0, 0), line2, font=font)
            width1 = bbox1[2] - bbox1[0]
            width2 = bbox2[2] - bbox2[0]

            if width1 <= max_width_px and width2 <= max_width_px:
                return (True, None, 2)
            else:
                warning = (
                    "Text zu lang! Auch mit 2 Zeilen passt der Text nicht. "
                    "Reduziere die Textlaenge oder verkleinere die Schriftgroesse.".format()
                )
                return (False, warning, 3)  # Schaetzung: 3+ Zeilen benoetigt

        # Versuche intelligenten Umbruch (gleiche Logik wie _wrap_text_to_two_lines)
        found_valid_split = False
        for i in range(1, len(words)):
            line1_candidate = " ".join(words[:i])
            line2_candidate = " ".join(words[i:])

            # Pruefe zuerst line1
            bbox1 = temp_draw.textbbox((0, 0), line1_candidate, font=font)
            width1 = bbox1[2] - bbox1[0]

            if width1 > max_width_px:
                # line1 zu lang -> abbrechen
                break

            # Pruefe line2
            bbox2 = temp_draw.textbbox((0, 0), line2_candidate, font=font)
            width2 = bbox2[2] - bbox2[0]

            if width2 <= max_width_px:
                # Text passt auf 2 Zeilen
                found_valid_split = True
                # Weiter versuchen, optimale Trennstelle zu finden

        if found_valid_split:
            return (True, None, 2)

        # Kein gueter Umbruch gefunden → Text passt nicht auf 2 Zeilen
        warning = (
            "Text zu lang! Auch mit 2 Zeilen passt der Text nicht. "
            "Reduziere die Textlaenge oder verkleinere die Schriftgroesse.".format()
        )
        return (False, warning, 3)  # Schaetzung: 3+ Zeilen benoetigt

    def _generate_ruf_placeholders(self, config: ZeichenConfig) -> list:
        """
        Generiert Platzhalter fuer Ruf-Modus

        NEU v0.8.1: Wenn config.freitext (= echter Rufname) gesetzt ist und zu lang:
        Automatischer Umbruch auf 2 Zeilen!

        WICHTIG: Gibt IMMER 2 Zeilen zurück
        """
        if config.freitext:
            # Echter Rufname → mit Umbruch wenn nötig
            canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
            max_width_px = mm_to_pixels(canvas_breite_mm, config.dpi)

            return self._wrap_text_to_two_lines(
                config.freitext,
                max_width_px,
                config.font_size,
                config.dpi,
                config.font_family
            )
        else:
            # Platzhalter → wie bisher
            ruf_placeholder = create_placeholder_text(config.placeholder_ruf_length)
            ruf_line = "Ruf: {}".format(ruf_placeholder)
            return ["", ruf_line]  # Leere Zeile 1, Text in Zeile 2

    def _generate_freitext_placeholders(self, config: ZeichenConfig) -> list:
        """
        Generiert Freitext-Zeile (NEU: Phase 2)

        Wenn config.freitext gesetzt ist: Diesen Text verwenden
        Sonst: Platzhalter verwenden

        NEU v0.8.1: Wenn Freitext zu lang → automatischer Umbruch auf 2 Zeilen!

        WICHTIG: Gibt IMMER 2 Zeilen zurück
        """
        if config.freitext:
            # Echten Freitext verwenden → mit Umbruch wenn nötig
            canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
            max_width_px = mm_to_pixels(canvas_breite_mm, config.dpi)

            return self._wrap_text_to_two_lines(
                config.freitext,
                max_width_px,
                config.font_size,
                config.dpi,
                config.font_family
            )
        else:
            # Platzhalter verwenden (gleiche Länge wie OV)
            freitext_placeholder = create_placeholder_text(config.placeholder_ov_length)
            return ["", freitext_placeholder]  # Leere Zeile 1, Text in Zeile 2

    def _generate_dateiname_placeholders(self, config: ZeichenConfig) -> list:
        """
        Generiert Text aus Dateiname (NEU)

        Verhält sich wie Freitext-Modus:
        - Wenn config.freitext gesetzt ist: Diesen Text verwenden (manuell bearbeitet)
        - Sonst: Dateiname verwenden (Unterstriche → Leerzeichen, ohne .svg)

        NEU v0.8.1: Wenn Text zu lang → automatischer Umbruch auf 2 Zeilen!

        WICHTIG: Gibt IMMER 2 Zeilen zurück
        """
        canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
        max_width_px = mm_to_pixels(canvas_breite_mm, config.dpi)

        if config.freitext:
            # Manuell bearbeiteter Text verwenden → mit Umbruch wenn nötig
            return self._wrap_text_to_two_lines(
                config.freitext,
                max_width_px,
                config.font_size,
                config.dpi,
                config.font_family
            )
        else:
            # Dateiname als Text: "Datei_Name.svg" → "Datei Name"
            filename = config.svg_path.stem  # Ohne Extension
            text = filename.replace("_", " ")  # Unterstriche → Leerzeichen

            # Mit Umbruch wenn nötig
            return self._wrap_text_to_two_lines(
                text,
                max_width_px,
                config.font_size,
                config.dpi,
                config.font_family
            )

    def _get_max_font_metrics(self, font_size: int, dpi: int) -> tuple:
        """
        Berechnet MAXIMALE Ascent/Descent für eine Schriftart/Schriftgröße.

        Dies stellt sicher, dass alle Zeichen auf der gleichen Höhe ausgerichtet sind,
        unabhängig vom tatsächlichen Inhalt. Sorgt für konsistentes, professionelles Layout.

        WICHTIG: Diese Funktion sollte EINMAL pro Schriftart/Schriftgröße-Kombination
        aufgerufen werden, nicht für jedes einzelne Zeichen!

        Returns:
            (max_ascent, max_descent) - Maximale Werte in Pixel
        """
        font = self._load_font(font_size, dpi)

        # Temporäres Draw-Objekt
        temp_img = Image.new('RGB', (TEMP_IMAGE_SIZE_PX, TEMP_IMAGE_SIZE_PX))
        temp_draw = ImageDraw.Draw(temp_img)

        # Test-String mit allen relevanten Zeichen:
        # - Hohe Buchstaben: T, l, d, f, h, k (maximaler Ascent)
        # - Tiefe Buchstaben: g, y, p, q, j, _ (maximaler Descent)
        # - Zahlen und Sonderzeichen: 0-9, /, =, - (für Stärke-Zeile)
        test_string = "Tlfhk_gyqj0123456789/=-:OV"

        bbox = temp_draw.textbbox((0, 0), test_string, font=font)

        max_ascent = bbox[1]    # Abstand Baseline -> Oberkante
        max_descent = bbox[3]   # Abstand Baseline -> Unterkante

        self.logger.debug(
            "Max Font-Metrics für {}pt @ {}dpi: ascent={}px, descent={}px".format(
                font_size, dpi, max_ascent, max_descent
            )
        )

        return (max_ascent, max_descent)

    def _calculate_text_height_px(
        self,
        lines: list,
        font_size: int,
        dpi: int,
        text_bottom_offset_mm: float,
        zeichen_hoehe_mm: float = None,
        zeichen_breite_mm: float = None
    ) -> int:
        """
        Berechnet Text-Hoehe in Pixel mit KONSISTENTEN Font-Metrics!

        WICHTIG v7.1: IMMER 2 Zeilen Platz reservieren für einheitliches Layout!
        - S2-Layout: 2 Zeilen (konsistentes Layout)
        - S1-Layout (2:1 Aspect Ratio): 1 Zeile (platzsparend)
        - Konsistente Darstellung unabhängig vom Modus
        - Vereinfachte Template-Verwaltung (nur 1 Text-Template pro DPI/Größe/Layout)

        Verwendet _get_max_font_metrics() für konsistente Ausrichtung!
        Dadurch sind alle Zeichen auf der gleichen Baseline-Höhe, unabhängig vom Inhalt.

        Formel:
        - max_ascent: Maximaler Ascent für diese Schriftart/Größe
        - line_height * (num_lines-1): Abstand zwischen Baselines
        - max_descent: Maximaler Descent für diese Schriftart/Größe
        - text_bottom_offset_mm: Abstand Text->Sicherheitsrand (user-konfigurierbar)

        Args:
            lines: Text-Zeilen (wird ignoriert - Layout-abhängig!)
            font_size: Schriftgröße in pt (variabel!)
            dpi: Auflösung
            text_bottom_offset_mm: Unterer Offset in mm
            zeichen_hoehe_mm: Zeichenhöhe (optional, für S1-Erkennung)
            zeichen_breite_mm: Zeichenbreite (optional, für S1-Erkennung)

        Returns:
            Text-Höhe in Pixel (2 Zeilen für S2, 1 Zeile für S1!)
        """
        if len(lines) == 0:
            # Kein Text: Nur Offset zurückgeben
            return mm_to_pixels(text_bottom_offset_mm, dpi)

        # CRITICAL: S1-Layout erkennen (2:1 Aspect Ratio)
        is_s1_layout = False
        if zeichen_hoehe_mm is not None and zeichen_breite_mm is not None:
            expected_breite = zeichen_hoehe_mm * 2.0
            if abs(zeichen_breite_mm - expected_breite) < 0.1:  # Toleranz 0.1mm
                is_s1_layout = True

        # v7.1: 2 Zeilen für S2, 1 Zeile für S1
        num_lines = 1 if is_s1_layout else 2

        # CHANGED: Verwende maximale Font-Metrics für Konsistenz!
        max_ascent, max_descent = self._get_max_font_metrics(font_size, dpi)

        # Zeilenabstand (abhängig von Schriftgröße!)
        font_size_px = int((font_size / POINTS_PER_INCH) * dpi)
        line_height_px = int(font_size_px * LINE_HEIGHT_FACTOR)

        # Offsets
        bottom_offset_px = mm_to_pixels(text_bottom_offset_mm, dpi)

        # GESAMT-HÖHE: IMMER für 2 Zeilen (konsistent für alle Modi!)
        # Enthält NUR Text + TEXT_BOTTOM_OFFSET_MM (nicht TEXT_GRAFIK_OFFSET_MM!)
        total_height = max_ascent + (line_height_px * (num_lines - 1)) + max_descent + bottom_offset_px

        layout_type = "S1" if is_s1_layout else "S2"
        self.logger.debug(
            "Text-Hoehe: {}px = max_ascent({}px) + {}x line_height({}px) + max_descent({}px) + bottom_offset({}px) [{} ZEILEN, {} Layout]".format(
                total_height, max_ascent, num_lines - 1, line_height_px, max_descent, bottom_offset_px, num_lines, layout_type
            )
        )

        return total_height
    
    def _draw_text_at_position(
        self,
        canvas: Image.Image,
        lines: list,
        y_start: int,
        font_size: int,
        dpi: int
    ) -> None:
        """
        Zeichnet Text auf Canvas
        
        WICHTIG (ZENTRIERUNG):
        - OV und Staerke sind linksbündig ZUEINANDER
        - ABER: Beide Zeilen sind horizontal ZENTRIERT im Canvas!
        
        Vorgehensweise:
        1. Breite der längsten Zeile (Stärke) messen
        2. Diese Zeile im Canvas zentrieren
        3. OV-Zeile an gleicher X-Position beginnen
        
        Args:
            canvas: Canvas (39mm)
            lines: Text-Zeilen
            y_start: Y-Position
            font_size: Schriftgroesse
            dpi: Aufloesung
        """
        draw = ImageDraw.Draw(canvas)
        font = self._load_font(font_size, dpi)

        # WICHTIG: draw.text() verwendet die Y-Position als BASELINE, nicht als Oberkante!
        # CHANGED: Verwende maximale Font-Metrics für konsistente Ausrichtung!

        # Hole maximale Metrics (gleiche wie in _calculate_text_height_px!)
        max_ascent, max_descent = self._get_max_font_metrics(font_size, dpi)

        # y_start ist die gewünschte OBERKANTE
        # Baseline = Oberkante + max_ascent (konsistent für alle Zeichen!)
        y_pos = y_start + max_ascent

        self.logger.debug(
            "Text-Start: y_start={}px (Oberkante), max_ascent={}px, y_pos={}px (Baseline)".format(
                y_start, max_ascent, y_pos
            )
        )
        
        font_size_px = int((font_size / POINTS_PER_INCH) * dpi)
        line_height_px = int(font_size_px * LINE_HEIGHT_FACTOR)
        
        # CHANGED: X-Position berechnen durch Zentrierung der längsten Zeile!
        # Die längste Zeile ist immer die letzte (Stärke oder Ruf)
        longest_line = lines[-1]  # Letzte Zeile ist immer die längste
        
        bbox = draw.textbbox((0, 0), longest_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        # Zentriere die längste Zeile im Canvas
        x_start = (canvas.width - text_width) // 2
        
        self.logger.debug(
            "Text ZENTRIERT: X={}px (Canvas: {}px, Text: {}px)".format(
                x_start, canvas.width, text_width
            )
        )
        
        # Alle Zeilen an dieser X-Position beginnen (linksbündig zueinander!)
        for line in lines:
            draw.text((x_start, y_pos), line, fill=TEXT_COLOR, font=font)
            
            self.logger.debug("Zeile '{}' bei ({}, {})".format(line, x_start, y_pos))
            
            y_pos += line_height_px
    
    def _load_font(self, font_size: int, dpi: int, font_family: str = None) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
        """
        Laedt Font mit Fallback-Mechanismus

            WICHTIG: Testet mehrere Varianten um Encoding-Probleme zu vermeiden

        Args:
            font_size: Schriftgröße in Punkten
            dpi: Auflösung
            font_family: Optional: Schriftart (falls None: aus RuntimeConfig)

        Returns:
            FreeTypeFont bei Erfolg, ImageFont.ImageFont als Fallback
        """
        # Font-Family: Nutze Parameter, sonst RuntimeConfig
        if font_family is None:
            runtime_cfg = get_config()
            font_family = runtime_cfg.font_family

        font_size_px = int((font_size / POINTS_PER_INCH) * dpi)

        # FontManager für Fallback verwenden
        font_mgr = FontManager()
        actual_font, _ = font_mgr.check_and_get_font(font_family)

        # Versuche Schriftart zu laden. Mehrere Varianten testen (mit und ohne .lower())
        font_paths = [
            # Variante 1: Original-Name (Case-Sensitive)
            f"{actual_font}.ttf",
            
            # Variante 2: Windows Fonts mit Original-Name
            f"C:/Windows/Fonts/{actual_font}.ttf",
            
            # Variante 3: Lowercase (für Standard-Fonts wie "arial")
            f"{actual_font.lower()}.ttf",
            
            # Variante 4: Windows Fonts mit Lowercase
            f"C:/Windows/Fonts/{actual_font.lower()}.ttf",
            
            # Variante 5: Vollständiger Name als Fallback
            actual_font
        ]
        
        # Alle Varianten durchprobieren
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size_px)
                self.logger.debug(f"Font geladen: {actual_font} ({font_size_px}px) via '{font_path}'")
                return font
            except Exception:
                # Nächste Variante probieren
                continue

        # Fallback: System-Default
        self.logger.warning(
            f"Schriftart '{actual_font}' konnte nicht geladen werden. "
            f"Verwende Default-Font. Alle Pfade getestet: {len(font_paths)}"
        )
        return ImageFont.load_default()


if __name__ == "__main__":
    import logging
    from PIL import Image
    from constants import ORGANIZATIONAL_BLUE, COLOR_WEISS
    
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)-8s | %(message)s')
    
    print("=" * 80)
    print("TEXT-OVERLAY v2.3 TEST (OFFSET KORRIGIERT)")
    print("=" * 80)
    
    # 39mm Canvas (45mm - 2×3mm Sicherheitsabstand = 39mm)
    canvas_hoehe_mm = DEFAULT_ZEICHEN_HOEHE_MM - (2 * DEFAULT_SICHERHEITSABSTAND_MM)
    canvas_size = mm_to_pixels(canvas_hoehe_mm, 600)
    canvas = Image.new('RGB', (canvas_size, canvas_size), COLOR_WEISS)
    
    # Test-Grafik oben
    test_grafik = Image.new('RGB', (500, 300), ORGANIZATIONAL_BLUE)
    canvas.paste(test_grafik, ((canvas_size - 500) // 2, 0))
    
    print("\nCanvas: {}x{}px".format(canvas.width, canvas.height))
    
    # Config
    config = ZeichenConfig(
        zeichen_id="TEST",
        svg_path=Path("test.svg"),
        modus=MODUS_OV_STAERKE,
        font_size=8,
        dpi=600
    )
    
    # Text zeichnen
    overlay = TextOverlayPlaceholder()
    text_height = overlay.calculate_text_height_mm(config)
    print("Text-Hoehe: {:.2f}mm".format(text_height))
    
    overlay.draw_text_on_canvas(canvas, config)
    
    # Speichern
    output = Path("test_canvas_v23_offset_fix.png")
    canvas.save(output, dpi=(600, 600))
    print("\n[OK] Gespeichert: {}".format(output))
    print("=" * 80)
