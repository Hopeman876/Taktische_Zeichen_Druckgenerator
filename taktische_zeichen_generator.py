#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poc_main_v2.py - v3.5 (Template-Optimierung)

TEMPLATE-OPTIMIERUNG v3.5:
- _get_template_key() generiert eindeutige Template-Keys
- _create_text_template() erstellt wiederverwendbare Text-Templates
- create_zeichen() unterstützt optionale Templates
- create_zeichen_batch() nutzt Templates (use_templates=True)
- Speicher-Effizienz: Text nur 1x generieren pro Modus
- Konsistenz: Identische Modi = identisches Layout

MULTITHREADING v3.4:
- create_zeichen_batch() Methode mit ThreadPoolExecutor
- Parallele Verarbeitung mehrerer Zeichen
- Thread-safe mit Lock fuer Statistiken
- Progress-Callback Support
- run_comprehensive() nutzt Multithreading (default: 4 Threads)

PERFORMANCE v3.2:
- render_scale: 3 -> 2 (50% schneller!)
- ~2.3s statt 5.2s pro Zeichen
- Grafik nutzt volle Canvas-Breite (39mm)
- TEXT_OFFSET_MM = 2.0mm (reduziert)

OPTIMIERUNG v3.1:
- ImageMagick: ERST bei hoher Aufloesung rendern (2x DPI)
- DANN trimmen bei hoher Aufloesung (praeziser!)
- Dann auf Zielgroesse skalieren
- Ergebnis: Groessere Grafiken, besseres Trimming

ERFOLG v3.0:
- SVG wird mit ImageMagick gerendert (svglib entfernt)
- Whitespace-Trimming NACH Rendering mit Wand trim()
- Skalierung mit Wand resize()
- Grafik wird korrekt gerendert (Layout OK, Position OK)

Version: 0.3.5-templates
"""

from pathlib import Path
from PIL import Image, ImageDraw
from wand.image import Image as WandImage
import re
import base64
from io import BytesIO
import sys
import math
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time

from logging_manager import LoggingManager

from constants import (
    EXPORT_DIR,
    DEFAULT_ZEICHEN_DIR,
    MODUS_OV_STAERKE,
    MODUS_ORT_STAERKE,
    MODUS_RUF,
    MODUS_OHNE_TEXT,
    MODUS_FREITEXT,
    MODUS_DATEINAME,
    DEFAULT_DPI,
    DEFAULT_ZEICHEN_HOEHE_MM,
    DEFAULT_SICHERHEITSABSTAND_MM,
    PLACEHOLDER_STAERKE_DIGITS,
    PLACEHOLDER_RUF_LENGTH,
    DEFAULT_FONT_SIZE,
    RESAMPLING_FILTER,
    EXPORT_PNG_COMPRESS_LEVEL,
    RESAMPLING_RENDER_SCALE_BIG_SVG,
    RESAMPLING_RENDER_SCALE_MED_SVG,
    RESAMPLING_RENDER_SCALE_SMALL_SVG,
    RESAMPLING_MAX_PX_SIZE_BIG,
    RESAMPLING_MAX_PX_SIZE_MED,
    PNG_COLOR_MODE,  # NEW: Farbmodus (RGBA fuer Transparenz)
    PNG_COLOR_MODE_RGBA,  # NEW: RGBA-Konstante
    PNG_BACKGROUND_COLOR_TRANSPARENT,  # NEW: Transparente Hintergrundfarbe
    PNG_BACKGROUND_COLOR_WHITE,  # NEW: Weisse Hintergrundfarbe
    S1_LINE_COLOR,  # NEW: Farbe der Schreiblinien (S1-Layout)
    S1_LINE_WIDTH,  # NEW: Linienstärke (S1-Layout)
    S1_LINE_MARGIN_MM,  # NEW: Abstand der Schreiblinien vom Rand (S1-Layout)
    S1_STAERKE_SLASH_ANGLE_DEG,  # NEW: Winkel der Schrägstriche (Stärkeangabe)
    S1_STAERKE_HEIGHT_FACTOR,  # NEW: Höhenfaktor für Stärkeangabe
    S1_STAERKE_UNDERSCORE_WIDTH_FACTOR,  # NEW: Unterstrich-Breite (Stärkeangabe)
    S1_STAERKE_LEFT_MARGIN_FACTOR,  # NEW: Linker Rand für handschriftliche Zahlen (Stärkeangabe)
    S1_STAERKE_GAP_FACTOR,  # NEW: Gap zwischen letztem Slash und Unterstrich (Stärkeangabe)
    S1_STAERKE_SLASH_COUNT,  # NEW: Anzahl Schrägstriche (Stärkeangabe)
    LINE_HEIGHT_FACTOR,  # NEW: Zeilenabstand-Faktor (S1-Layout)
    SYSTEM_POINTS_PER_INCH,  # NEW: Points per Inch (S1-Layout)
    DEFAULT_S1_LINKS_PROZENT,  # NEW: S1 Layout Links/Rechts Aufteilung
    DEFAULT_S1_ANZAHL_SCHREIBLINIEN,  # NEW: S1 Layout Anzahl Schreiblinien
    DEFAULT_S1_STAERKE_ANZEIGEN,  # NEW: S1 Layout Stärke anzeigen
    create_staerke_placeholder,  # NEW: Stärke-Platzhalter generieren (S1-Layout)
    mm_to_pixels,
    ZEICHEN_SIZE_THRESHOLD_VERY_LARGE_MM,  # Schwellwert für sehr große Zeichen
    ZEICHEN_SIZE_THRESHOLD_LARGE_MM  # Schwellwert für große Zeichen
)
from svg_loader_local import SVGLoaderLocal
from text_overlay import TextOverlayPlaceholder, ZeichenConfig
from print_preparer import PrintPreparer


class TaktischeZeichenGenerator:
    """
    Proof-of-Concept v3.2 - ImageMagick-basierte Loesung

    FUNKTIONIERT:
    - SVG-Rendering mit ImageMagick/Wand
    - Wand trim() fuer Whitespace-Trimming
    - Wand-basiertes Scaling mit hoher Aufloesung
    - Korrekte Grafik-Darstellung
    """

    def __init__(self, zeichen_dir: Path = None):
        """Initialisiert"""
        self.logger = LoggingManager().get_logger(__name__)

        # RuntimeConfig-Default laden falls nicht angegeben
        if zeichen_dir is None:
            from runtime_config import get_config
            zeichen_dir = get_config().zeichen_dir

        self.svg_loader = SVGLoaderLocal(zeichen_dir)
        self.text_overlay = TextOverlayPlaceholder()
        self.print_preparer = PrintPreparer()

        EXPORT_DIR.mkdir(parents=True, exist_ok=True)

        self.logger.info("TaktischeZeichenGenerator initialisiert")

    def _get_max_grafik_groesse_mm(self) -> float:
        """
        Berechnet maximale Grafikgröße aus RuntimeConfig

        Returns:
            float: Canvas-Höhe in mm (Zeichen-Höhe - 2×Sicherheitsabstand)
        """
        try:
            from runtime_config import get_config
            config = get_config()
            return config.zeichen_hoehe_mm - (2 * config.sicherheitsabstand_mm)
        except Exception:
            # Fallback auf Defaults
            return DEFAULT_ZEICHEN_HOEHE_MM - (2 * DEFAULT_SICHERHEITSABSTAND_MM)

    def validate_custom_grafik_size(self, size_mm: float) -> Tuple[bool, str]:
        """
        Validiert benutzerdefinierte Grafikgröße

        Returns:
            (is_valid, message) - Tuple mit Validierungsergebnis und Nachricht
        """
        if size_mm <= 0:
            return False, "Größe muss positiv sein (größer als 0mm)"

        max_grafik_groesse_mm = self._get_max_grafik_groesse_mm()
        if size_mm > max_grafik_groesse_mm:
            return False, "Größe darf {} mm nicht überschreiten (Maximum: {}mm)".format(
                size_mm, max_grafik_groesse_mm)

        # Warnung bei sehr kleinen Größen (unter 10mm)
        if size_mm < 10:
            return True, "WARNUNG: Sehr kleine Grafik ({}mm). Empfohlen: mindestens 10mm".format(size_mm)

        return True, "Größe {}x{}mm ist gültig".format(size_mm, size_mm)

    def _is_pseudo_svg(self, svg_path: Path) -> bool:
        """Prueft ob SVG ein Pseudo-SVG ist (nur PNG-Wrapper)"""
        try:
            # FIXED: Blanko-Zeichen koennen keine Pseudo-SVGs sein (virtueller Pfad)
            if SVGLoaderLocal.is_blanko_zeichen(svg_path):
                return False

            # Datei muss existieren
            if not svg_path.exists():
                return False

            content = svg_path.read_text(encoding='utf-8')

            has_png = 'data:image/png;base64,' in content
            vector_elements = ['<path', '<circle', '<rect', '<polygon', '<polyline', '<line', '<ellipse']
            has_vector = any(elem in content for elem in vector_elements)

            return has_png and not has_vector

        except Exception as e:
            self.logger.warning("Konnte SVG nicht pruefen: {}".format(e))
            return False

    def _extract_png_from_svg(self, svg_path: Path) -> Image.Image:
        """Extrahiert PNG aus Pseudo-SVG"""
        self.logger.info("Pseudo-SVG erkannt - extrahiere PNG")
        
        content = svg_path.read_text(encoding='utf-8')
        match = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', content)
        
        if not match:
            raise ValueError("Kein eingebettetes PNG gefunden")
        
        png_data = base64.b64decode(match.group(1))
        pil_image = Image.open(BytesIO(png_data))

        # CHANGED: RGBA beibehalten statt RGB-Konvertierung
        if pil_image.mode != PNG_COLOR_MODE:
            pil_image = pil_image.convert(PNG_COLOR_MODE)

        return pil_image

    def _draw_staerke_indicator(
        self,
        draw: ImageDraw.ImageDraw,
        y_pos: int,
        line_x_start: int,
        line_x_end: int,
        line_height_px: int
    ) -> None:
        """
        Zeichnet Staerkeangabe als geometrische Linien (nicht als Text)

        Layout: /   /   /   GAP  ________
                ←   70%   → 5% ← 25% →

        Args:
            draw: ImageDraw-Objekt
            y_pos: Y-Position der Schreiblinie (Baseline)
            line_x_start: Linke Grenze (mit Margin)
            line_x_end: Rechte Grenze (mit Margin)
            line_height_px: Zeilenhöhe in Pixeln
        """
        # Verfügbare Breite berechnen
        available_width_px = line_x_end - line_x_start

        # Höhe der Stärkeangabe (90% der Zeilenhöhe)
        staerke_height_px = line_height_px * S1_STAERKE_HEIGHT_FACTOR

        # 1. Unterstrich-Breite und -Position (rechtsbündig)
        underscore_width_px = available_width_px * S1_STAERKE_UNDERSCORE_WIDTH_FACTOR
        underscore_x_start = int(line_x_end - underscore_width_px)
        underscore_x_end = line_x_end

        # 2. Linker Rand (Platz für handschriftliche Zahlen)
        left_margin_width_px = available_width_px * S1_STAERKE_LEFT_MARGIN_FACTOR

        # 3. Gap-Breite (optische Trennung zwischen Slashes und Unterstrich)
        gap_width_px = available_width_px * S1_STAERKE_GAP_FACTOR

        # 4. Slash-Bereich: Mit unterschiedlichen Abständen links (Margin) und rechts (Gap)
        slash_area_x_start = int(line_x_start + left_margin_width_px)  # Linker Rand (groß, für Schreiben)
        slash_area_x_end = int(underscore_x_start - gap_width_px)      # Rechter Gap (klein, optisch)
        slash_area_width_px = slash_area_x_end - slash_area_x_start

        # Winkel in Radiant konvertieren
        angle_rad = math.radians(S1_STAERKE_SLASH_ANGLE_DEG)

        # Breite eines Schrägstrichs berechnen (aus Höhe und Winkel)
        # tan(angle) = Höhe / Breite → Breite = Höhe / tan(angle)
        slash_width_px = staerke_height_px / math.tan(angle_rad)

        # Abstand zwischen Schrägstrichen berechnen
        # KORRIGIERT: Nur N-1 Spacings ZWISCHEN den Slashes (nicht vor/nach)
        # Bei 3 Slashes: 2 Spacings zwischen ihnen
        # Dadurch endet letzter Slash DIREKT am slash_area_x_end (Gap wird korrekt respektiert)
        slash_spacing_px = (slash_area_width_px - (S1_STAERKE_SLASH_COUNT * slash_width_px)) / (S1_STAERKE_SLASH_COUNT - 1)

        # Y-Positionen für Slashes (AN der Baseline beginnend, nach OBEN)
        slash_y_bottom = y_pos                             # Beginnt an Baseline (gleiche Höhe wie Unterstrich)
        slash_y_top = int(y_pos - staerke_height_px)      # Geht nach oben (in vorherige Zeile hinein)

        # Schrägstriche zeichnen (von links nach rechts)
        # Start OHNE initiales Spacing (direkt bei slash_area_x_start)
        current_x = slash_area_x_start
        for i in range(S1_STAERKE_SLASH_COUNT):
            # Slash von unten-links nach oben-rechts
            x1 = int(current_x)
            y1 = slash_y_bottom
            x2 = int(current_x + slash_width_px)
            y2 = slash_y_top

            draw.line([(x1, y1), (x2, y2)], fill=S1_LINE_COLOR, width=S1_LINE_WIDTH)

            # Nächste Position
            current_x += slash_width_px + slash_spacing_px

        # Unterstrich zeichnen (bereits berechnet)
        draw.line(
            [(underscore_x_start, y_pos), (underscore_x_end, y_pos)],
            fill=S1_LINE_COLOR,
            width=S1_LINE_WIDTH
        )

        self.logger.debug(
            "Staerke gezeichnet: Margin links ({:.0f}px) + 3 Slashes ({:.1f}px hoch, {:.1f}° Winkel) + Gap rechts ({:.0f}px) + Unterstrich ({:.0f}px breit)".format(
                left_margin_width_px, staerke_height_px, S1_STAERKE_SLASH_ANGLE_DEG, gap_width_px, underscore_width_px
            )
        )

    def _sanitize_svg_content(self, svg_path: Path) -> Path:
        """
        Bereinigt SVG-Inhalt von ungültigen UTF-8-Zeichen

        Dies verhindert Warnungen wie:
        "Invalid UTF-8 string passed to pango_layout_set_text()"

        Args:
            svg_path: Pfad zur SVG-Datei

        Returns:
            Path zur bereinigten temporären SVG-Datei
        """
        try:
            # FIXED: Blanko-Zeichen sind virtuelle Pfade, keine echten Dateien
            if SVGLoaderLocal.is_blanko_zeichen(svg_path):
                return svg_path

            # FIXED: Datei muss existieren
            if not svg_path.exists():
                return svg_path

            # Lese SVG mit error='ignore' um ungueltige UTF-8 Zeichen zu ueberspringen
            with open(svg_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Schreibe bereinigten Inhalt in temporaere Datei
            import tempfile
            temp_fd, temp_path = tempfile.mkstemp(suffix='.svg', prefix='sanitized_')
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Schliesse den File Descriptor
            import os
            os.close(temp_fd)

            return Path(temp_path)
        except Exception as e:
            self.logger.debug(f"SVG-Bereinigung fehlgeschlagen, verwende Original: {e}")
            return svg_path

    def _svg_to_image_imagemagick(
        self,
        svg_path: Path,
        max_height_mm: float,
        max_width_mm: float,
        dpi: int,
        render_scale: float = 1.0  # v7.1 Phase 2: Übergeben aus ZeichenConfig
    ) -> Image.Image:
        """
        Konvertiert SVG mit ImageMagick (Fallback)

        OPTIMIERT: ERST hochskalieren, DANN trimmen!

        Workflow:
        1. SVG bei hoher Aufloesung rendern (3x Zielgroesse fuer Praezision)
        2. Bei hoher Aufloesung trimmen (praezise!)
        3. Auf Zielgroesse skalieren

        Vorteil: Trimming bei hoher Aufloesung ist viel genauer

        Args:
            render_scale: Skalierungsfaktor (v7.1 Phase 2: aus RenderProfile)
        """
        self.logger.info("Konvertiere mit ImageMagick (Fallback)")

        max_width_px = mm_to_pixels(max_width_mm, dpi)
        max_height_px = mm_to_pixels(max_height_mm, dpi)

        # v7.1 Phase 2: render_scale wird aus ZeichenConfig.render_scale übergeben
        # Fallback auf altes Verhalten wenn render_scale == 1.0
        if render_scale == 1.0:
            # LEGACY: Smart Render Scale basierend auf Zeichengröße (Fallback)
            self.logger.debug(f"Datei: {svg_path}")
            if max_width_px > RESAMPLING_MAX_PX_SIZE_BIG or max_height_px > RESAMPLING_MAX_PX_SIZE_BIG:
                render_scale = RESAMPLING_RENDER_SCALE_BIG_SVG  # Sehr große Zeichen
                self.logger.debug("Sehr großes Zeichen: render_scale={}".format(render_scale))
            elif max_width_px > RESAMPLING_MAX_PX_SIZE_MED or max_height_px > 1000:
                render_scale = RESAMPLING_RENDER_SCALE_MED_SVG  # Große Zeichen
                self.logger.debug("Großes Zeichen: render_scale={}".format(render_scale))
            else:
                render_scale = RESAMPLING_RENDER_SCALE_SMALL_SVG
                self.logger.debug("Kleines Zeichen: render_scale={}".format(render_scale))
        else:
            self.logger.debug(f"Verwende render_scale aus Profil: {render_scale}")

        # Bereinige SVG vor dem Rendern (verhindert Pango UTF-8 Warnungen)
        sanitized_svg_path = self._sanitize_svg_content(svg_path)
        temp_file_created = (sanitized_svg_path != svg_path)

        try:
            with WandImage(filename=str(sanitized_svg_path), resolution=int(dpi * render_scale)) as img:
                # SCHRITT 1: SVG bei hoher Aufloesung rendern
                orig_w = img.width
                orig_h = img.height

                self.logger.info(
                    "SVG gerendert @ {}x DPI: {}x{}px".format(
                        render_scale, orig_w, orig_h
                    )
                )

                # SCHRITT 2: Bei HOHER Aufloesung trimmen (praezise!)
                img.trim(fuzz=0)

                trimmed_width = img.width
                trimmed_height = img.height

                if trimmed_width != orig_w or trimmed_height != orig_h:
                    self.logger.info(
                        "SVG getrimmt @ high-res: {}x{} -> {}x{}px".format(
                            orig_w, orig_h,
                            trimmed_width, trimmed_height
                        )
                    )

                # SCHRITT 3: Skalierung auf Zielgroesse berechnen
                # Grafik soll so gross wie moeglich werden:
                # - Nicht breiter als max_width_px
                # - Nicht hoeher als max_height_px
                # - Seitenverhaeltnis beibehalten

                # Berechne was die Grafik bei 1x Aufloesung waere
                current_width_1x = trimmed_width / render_scale
                current_height_1x = trimmed_height / render_scale

                # Berechne Skalierungsfaktoren
                scale_w = max_width_px / current_width_1x
                scale_h = max_height_px / current_height_1x

                # Nimm den KLEINEREN Faktor (damit nichts ueber Limits geht)
                scale = min(scale_w, scale_h)

                # Finale Groesse
                final_width = int(current_width_1x * scale)
                final_height = int(current_height_1x * scale)

                self.logger.info(
                    "Skalierung: {}x{} @ 1x -> {}x{}px (Faktor: {:.3f})".format(
                        int(current_width_1x), int(current_height_1x),
                        final_width, final_height, scale
                    )
                )

                # SCHRITT 4: Auf Zielgroesse skalieren
                # OPTIMIZED: 'catrom' Filter ist schneller als 'lanczos' bei guter Qualität
                img.resize(final_width, final_height, filter=RESAMPLING_FILTER)

                # CHANGED: Alpha-Kanal beibehalten fuer Transparenz (fuer Druck auf farbigem Untergrund)
                # REMOVED: img.alpha_channel = 'remove'
                # Transparenz bleibt erhalten -> PNG mit RGBA statt RGB

                png_blob = img.make_blob('png')

            pil_image = Image.open(BytesIO(png_blob))

            # CHANGED: RGBA beibehalten statt RGB-Konvertierung
            if pil_image.mode != PNG_COLOR_MODE:
                pil_image = pil_image.convert(PNG_COLOR_MODE)

            return pil_image
        finally:
            # Cleanup: Temporäre Datei löschen falls erstellt
            if temp_file_created:
                try:
                    import os
                    os.unlink(sanitized_svg_path)
                    self.logger.debug(f"Temporäre SVG-Datei gelöscht: {sanitized_svg_path}")
                except Exception as e:
                    self.logger.debug(f"Fehler beim Löschen der temporären SVG: {e}")

    def _svg_to_image(
        self,
        svg_path: Path,
        max_height_mm: float,
        max_width_mm: float,
        dpi: int,
        render_scale: float = 1.0  # v7.1 Phase 2: Übergeben aus ZeichenConfig
    ) -> Image.Image:
        """
        Konvertiert SVG zu PIL Image (2-Stufen-Strategie)

        1. Pseudo-SVG Check (PNG-in-SVG-Wrapper)
        2. ImageMagick Rendering

        Args:
            render_scale: Skalierungsfaktor (v7.1 Phase 2: aus RenderProfile)
        """
        try:
            # SCHRITT 1: Pseudo-SVG Check
            if self._is_pseudo_svg(svg_path):
                pil_image = self._extract_png_from_svg(svg_path)

                max_width_px = mm_to_pixels(max_width_mm, dpi)
                max_height_px = mm_to_pixels(max_height_mm, dpi)

                scale_w = max_width_px / pil_image.width
                scale_h = max_height_px / pil_image.height
                scale = min(scale_w, scale_h)

                new_width = int(pil_image.width * scale)
                new_height = int(pil_image.height * scale)

                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                return pil_image

            # SCHRITT 2: ImageMagick Rendering
            return self._svg_to_image_imagemagick(svg_path, max_height_mm, max_width_mm, dpi, render_scale)

        except Exception as e:
            self.logger.error("Fehler bei SVG-Konvertierung: {}".format(e))
            raise

    def calculate_max_grafik_size_mm(self) -> float:
        """Berechnet maximale Grafik-Groesse fuer alle Modi"""
        sicherer_bereich_mm = self._get_max_grafik_groesse_mm()

        config_ov = ZeichenConfig(
            zeichen_id="temp",
            svg_path=Path("temp.svg"),
            modus=MODUS_OV_STAERKE,
            placeholder_staerke_format=PLACEHOLDER_STAERKE_DIGITS
            # font_size und dpi werden aus RuntimeConfig geladen (__post_init__)
        )
        text_hoehe_ov = self.text_overlay.calculate_text_height_mm(config_ov)

        config_ruf = ZeichenConfig(
            zeichen_id="temp",
            svg_path=Path("temp.svg"),
            modus=MODUS_RUF,
            placeholder_ruf_length=PLACEHOLDER_RUF_LENGTH
            # font_size und dpi werden aus RuntimeConfig geladen (__post_init__)
        )
        text_hoehe_ruf = self.text_overlay.calculate_text_height_mm(config_ruf)

        max_text_hoehe = max(text_hoehe_ov, text_hoehe_ruf, 0.0)

        # CHANGED: text_hoehe enthält bereits TEXT_GRAFIK_OFFSET_MM + TEXT_BOTTOM_OFFSET_MM!
        max_grafik_groesse = sicherer_bereich_mm - max_text_hoehe

        self.logger.info(
            "Max. Grafik-Groesse: {:.2f}mm (Bereich: {}mm - Text mit Offsets: {:.2f}mm)".format(
                max_grafik_groesse, sicherer_bereich_mm, max_text_hoehe
            )
        )

        return max_grafik_groesse
    
    def create_zeichen(
        self,
        svg_path: Path,
        config: ZeichenConfig,
        draw_cut_lines: bool = False,
        text_template: Optional[Image.Image] = None,
        svg_template: Optional[Image.Image] = None,
        return_image: bool = False,
        track_timing: bool = False
    ):
        """
        Erstellt druckfertiges Zeichen

        Args:
            svg_path: Pfad zur SVG-Datei
            config: Zeichen-Konfiguration
            draw_cut_lines: Schnittlinien zeichnen
            text_template: Optional vorbereitetes Text-Template (Batch-Optimierung)
            svg_template: Optional vorbereitete SVG-Grafik (PERFORMANCE BOOST!)
            return_image: True = PIL Image zurückgeben, False = Datei speichern (default)
            track_timing: True = Zeitmessung pro Schritt zurückgeben (für Statistik)

        Returns:
            Path: Pfad zur gespeicherten Datei (wenn return_image=False und track_timing=False)
            Image: PIL Image (wenn return_image=True und track_timing=False)
            Tuple[Path/Image, dict]: (output, timings) wenn track_timing=True
        """
        import time

        # NEW: Zeitmessung initialisieren
        timings = {
            'render': 0.0,      # SVG-Rendering
            'generate': 0.0,    # Canvas + Text + Grafik-Komposition
            'export': 0.0       # Datei-Export / Print-Vorbereitung
        }

        self.logger.info("=" * 80)
        self.logger.info("Erstelle Zeichen: {}".format(config.zeichen_id))
        self.logger.info("=" * 80)

        # NEW: Blanko-Zeichen erkennen
        is_blanko = SVGLoaderLocal.is_blanko_zeichen(svg_path)

        if not is_blanko and not self.svg_loader.validate_svg(svg_path):
            raise ValueError("Ungueltige SVG: {}".format(svg_path))

        # SVG-Grafik holen (entweder aus Template oder neu rendern)
        # NEW: Bei Blanko-Zeichen wird KEINE Grafik gerendert!
        zeichen_image = None

        # NEW: Zeitmessung Rendering initialisieren (wird nur bei tatsächlichem Rendering gefüllt)
        render_start_time = None

        if svg_template is not None:
            # Template klonen (PERFORMANCE BOOST!)
            try:
                # FIXED: PIL Image.copy() kann bei korrupten PNGs fehlschlagen
                zeichen_image = svg_template.copy()
                self.logger.debug("Verwende SVG-Template (optimiert)")
            except (AssertionError, OSError) as e:
                # Fallback: SVG neu rendern
                self.logger.warning("SVG-Template konnte nicht kopiert werden ({}), rendere neu".format(str(e)))

        if zeichen_image is None and not is_blanko:
            # Traditionell: SVG neu rendern (NUR wenn NICHT Blanko!)
            # NEW: Debug-Logging für Rendering-Start
            self.logger.debug("START: SVG-Rendering von {}".format(svg_path.name))

            # NEW: Zeitmessung Rendering starten
            render_start_time = time.time()

            # NEU: Phase 2 - Bei OHNE_TEXT volle 39x39mm nutzen (oder benutzerdefinierte Größe)!
            if config.modus == MODUS_OHNE_TEXT:
                # OHNE Text: Voller Canvas verfügbar (rechteckig möglich!)
                if config.custom_grafik_hoehe_mm is not None and config.custom_grafik_breite_mm is not None:
                    # v7.1: Benutzerdefinierte Größe verwenden (Höhe und Breite separat)
                    max_grafik_height_mm = config.custom_grafik_hoehe_mm
                    max_grafik_width_mm = config.custom_grafik_breite_mm
                    self.logger.info("OHNE_TEXT: Benutzerdefinierte Grafikgröße {}x{}mm".format(
                        config.custom_grafik_breite_mm, config.custom_grafik_hoehe_mm))
                else:
                    # CHANGED: Canvas-Abmessungen berechnen (rechteckig!)
                    canvas_hoehe_mm = config.zeichen_hoehe_mm - (2 * config.sicherheitsabstand_mm)
                    canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)

                    max_grafik_height_mm = canvas_hoehe_mm  # FIXED: Volle Canvas-Höhe
                    max_grafik_width_mm = canvas_breite_mm  # FIXED: Volle Canvas-Breite
                    self.logger.info("OHNE_TEXT: Volle Grafikgröße {}x{}mm".format(
                        canvas_breite_mm, canvas_hoehe_mm))
            else:
                # MIT Text: Höhe muss IMMER Text + Offsets berücksichtigen!
                # custom_grafik_* sind nur MAXIMUM-Werte

                # Text-Höhe berechnen (enthält Text + TEXT_BOTTOM_OFFSET_MM)
                text_height_mm = self.text_overlay.calculate_text_height_mm(config)

                # Canvas-Abmessungen berechnen (rechteckig!)
                canvas_hoehe_mm = config.zeichen_hoehe_mm - (2 * config.sicherheitsabstand_mm)
                canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)

                # Verfügbare Höhe für Grafik nach Abzug von Text + Abständen
                # text_height_mm enthält bereits: Text + TEXT_BOTTOM_OFFSET_MM
                # Zusätzlich abziehen: TEXT_GRAFIK_OFFSET_MM (Abstand Grafik->Text)
                verfuegbare_hoehe = canvas_hoehe_mm - text_height_mm - config.abstand_grafik_text_mm

                # v7.1: Wenn custom_grafik_* gesetzt, als MAXIMUM verwenden
                if config.custom_grafik_hoehe_mm is not None and config.custom_grafik_breite_mm is not None:
                    # Verwende das KLEINERE von custom und verfügbar (damit Text nicht überdeckt wird!)
                    max_grafik_height_mm = min(config.custom_grafik_hoehe_mm, verfuegbare_hoehe)
                    max_grafik_width_mm = min(config.custom_grafik_breite_mm, canvas_breite_mm)
                    self.logger.info("MIT_TEXT: Grafik begrenzt auf {}x{}mm (custom: {}x{}mm, verfügbar mit Text: {}mm Höhe)".format(
                        max_grafik_width_mm, max_grafik_height_mm,
                        config.custom_grafik_breite_mm, config.custom_grafik_hoehe_mm,
                        verfuegbare_hoehe))
                else:
                    # Fallback: Verwende verfügbare Größe
                    max_grafik_height_mm = verfuegbare_hoehe
                    max_grafik_width_mm = canvas_breite_mm
                    self.logger.info("MIT_TEXT: Berechnete Grafikgröße {}x{}mm (verfügbar nach Text)".format(
                        max_grafik_width_mm, max_grafik_height_mm))

            zeichen_image = self._svg_to_image(
                svg_path,
                max_height_mm=max_grafik_height_mm,  # ~21.8mm (begrenzt durch Text)
                max_width_mm=max_grafik_width_mm,     # 39mm (volle Breite!)
                dpi=config.dpi,
                render_scale=config.render_scale  # v7.1 Phase 2
            )

            # NEW: Zeitmessung Rendering stoppen
            if render_start_time is not None:
                timings['render'] = time.time() - render_start_time
                self.logger.debug("Rendering-Zeit: {:.3f}s".format(timings['render']))

            # NEW: Debug-Logging für Rendering-Ende
            self.logger.debug("ENDE: SVG-Rendering von {} abgeschlossen".format(svg_path.name))
        else:
            # NEW: Kein Rendering (Template oder Blanko)
            if svg_template is not None:
                self.logger.debug("Kein Rendering (SVG-Template verwendet)")
            if is_blanko:
                self.logger.debug("Kein Rendering (Blanko-Zeichen)")

        # NEW: Zeitmessung Generierung starten
        generate_start = time.time()

        # CHANGED: Rechteckiger Canvas (Höhe × Breite)
        canvas_hoehe_mm = config.zeichen_hoehe_mm - (2 * config.sicherheitsabstand_mm)
        canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
        canvas_hoehe_px = mm_to_pixels(canvas_hoehe_mm, config.dpi)
        canvas_breite_px = mm_to_pixels(canvas_breite_mm, config.dpi)

        # NEU: Template-Optimierung
        if text_template is not None:
            # Template klonen (schnell!)
            canvas = text_template.copy()
            self.logger.debug("Verwende Text-Template (optimiert)")
        else:
            # Traditionell: Neues Canvas + Text zeichnen
            # CHANGED: RGBA-Canvas mit transparentem Hintergrund (rechteckig)
            bg_color = PNG_BACKGROUND_COLOR_TRANSPARENT if PNG_COLOR_MODE == PNG_COLOR_MODE_RGBA else PNG_BACKGROUND_COLOR_WHITE
            canvas = Image.new(PNG_COLOR_MODE, (canvas_breite_px, canvas_hoehe_px), bg_color)

            if config.modus != MODUS_OHNE_TEXT:
                self.text_overlay.draw_text_on_canvas(canvas, config)

        # NEW: Grafik nur einfügen wenn NICHT Blanko!
        if not is_blanko:
            # CHANGED: Horizontal zentriert (rechteckig!)
            x_offset = (canvas_breite_px - zeichen_image.width) // 2

            # NEU: Phase 2 - Vertikale Positionierung für MODUS_OHNE_TEXT
            if config.modus == MODUS_OHNE_TEXT:
                # Grafik-Position je nach Einstellung
                if config.grafik_position == "top":
                    y_offset = 0  # Oben
                elif config.grafik_position == "bottom":
                    # CHANGED: canvas_hoehe_px statt canvas_size_px
                    y_offset = canvas_hoehe_px - zeichen_image.height  # Unten
                else:  # "center" oder default
                    # CHANGED: canvas_hoehe_px statt canvas_size_px
                    y_offset = (canvas_hoehe_px - zeichen_image.height) // 2  # Mittig
            else:
                # Mit Text: Grafik immer oben
                y_offset = 0

            # CHANGED: Bei RGBA Alpha-Kanal als Maske verwenden
            # Dies erhält die glatten Konturen (Anti-Aliasing) und verhindert schwarze Flächen
            if zeichen_image.mode == 'RGBA':
                canvas.paste(zeichen_image, (x_offset, y_offset), mask=zeichen_image)
            else:
                canvas.paste(zeichen_image, (x_offset, y_offset))
        else:
            # Blanko-Zeichen: Keine Grafik, nur weißer Canvas + Text
            self.logger.info("BLANKO-Zeichen: Keine Grafik gerendert")

        # NEW: Zeitmessung Generierung stoppen
        timings['generate'] = time.time() - generate_start
        self.logger.debug("Generierungs-Zeit: {:.3f}s".format(timings['generate']))

        # NEW: Zeitmessung Export starten
        export_start = time.time()

        # CHANGED: Config-Werte an prepare_for_print übergeben (mit Breite & Beschnitt)
        print_ready_image = self.print_preparer.prepare_for_print(
            canvas,
            config.dpi,
            draw_cut_lines=draw_cut_lines,
            zeichen_hoehe_mm=config.zeichen_hoehe_mm,
            zeichen_breite_mm=config.zeichen_breite_mm,
            sicherheitsabstand_mm=config.sicherheitsabstand_mm,
            beschnittzugabe_mm=config.beschnittzugabe_mm
        )

        # NEU: return_image Parameter
        if return_image:
            # Für PDF-Export: Image zurückgeben statt speichern
            # NEW: Zeitmessung Export stoppen
            timings['export'] = time.time() - export_start
            self.logger.debug("Export-Zeit: {:.3f}s".format(timings['export']))

            self.logger.info("ERFOLGREICH (Image zurückgegeben)")

            # NEW: Timings zurückgeben wenn gewünscht
            if track_timing:
                return (print_ready_image, timings)
            else:
                return print_ready_image
        else:
            # Standard: Datei speichern
            output_file = self._export_image(
                print_ready_image,
                config.zeichen_id,
                config.modus,
                config.dpi,
                draw_cut_lines,
                config.output_dir  # NEW: Output-Verzeichnis aus Config
            )

            # NEW: Zeitmessung Export stoppen
            timings['export'] = time.time() - export_start
            self.logger.debug("Export-Zeit: {:.3f}s".format(timings['export']))

            self.logger.info("ERFOLGREICH: {}".format(output_file.name))

            # NEW: Timings zurückgeben wenn gewünscht
            if track_timing:
                return (output_file, timings)
            else:
                return output_file

    def create_zeichen_s1(
        self,
        svg_path: Path,
        config: ZeichenConfig,
        s1_links_prozent: int = DEFAULT_S1_LINKS_PROZENT,
        s1_anzahl_schreiblinien: int = DEFAULT_S1_ANZAHL_SCHREIBLINIEN,
        s1_staerke_anzeigen: bool = DEFAULT_S1_STAERKE_ANZEIGEN,
        draw_cut_lines: bool = False,
        text_template: Optional[Image.Image] = None,
        svg_template: Optional[Image.Image] = None,
        return_image: bool = False,
        track_timing: bool = False
    ):
        """
        Erstellt druckfertiges S1-Layout Zeichen (Doppelschild)

        S1-Layout: Rechteckiges Zeichen (Breite = 2 × Höhe) mit zwei Bereichen:
        - Links: Grafik + Freitext (wie S2-Layout)
        - Rechts: Schreiblinien + optionaler Stärke-Platzhalter

        Args:
            svg_path: Pfad zur SVG-Datei (für linken Bereich)
            config: Zeichen-Konfiguration (Größe, DPI, Modus für linken Bereich)
            s1_links_prozent: Aufteilung Links/Rechts in Prozent (20-80, default: 40)
            s1_anzahl_schreiblinien: Anzahl gewünschter Schreiblinien (3-10, default: 5, Zeilenhöhe wird berechnet)
            s1_staerke_anzeigen: Stärke-Platzhalter in erster Zeile anzeigen (default: True)
            draw_cut_lines: Schnittlinien zeichnen
            text_template: Optional vorbereitetes Text-Template (Batch-Optimierung)
            svg_template: Optional vorbereitete SVG-Grafik (PERFORMANCE BOOST!)
            return_image: True = PIL Image zurückgeben, False = Datei speichern (default)
            track_timing: True = Zeitmessung pro Schritt zurückgeben (für Statistik)

        Returns:
            Path: Pfad zur gespeicherten Datei (wenn return_image=False und track_timing=False)
            Image: PIL Image (wenn return_image=True und track_timing=False)
            Tuple[Path/Image, dict]: (output, timings) wenn track_timing=True
        """
        import time

        # NEW: Zeitmessung initialisieren
        timings = {
            'render': 0.0,      # SVG-Rendering
            'generate': 0.0,    # Canvas + Text + Schreiblinien-Komposition
            'export': 0.0       # Datei-Export / Print-Vorbereitung
        }

        self.logger.info("=" * 80)
        self.logger.info("Erstelle S1-Layout Zeichen: {}".format(config.zeichen_id))
        self.logger.info("=" * 80)

        # NEW: Zeitmessung Generate-Phase starten
        generate_start_time = time.time()

        # VALIDIERUNG: Aspect Ratio muss 2:1 sein
        expected_breite = config.zeichen_hoehe_mm * 2.0
        if abs(config.zeichen_breite_mm - expected_breite) > 0.1:  # Toleranz 0.1mm
            self.logger.warning(
                "S1-Layout: Seitenverhältnis nicht 2:1! Erwartet: {}mm, Ist: {}mm".format(
                    expected_breite, config.zeichen_breite_mm
                )
            )

        # Canvas-Abmessungen berechnen (rechteckig, 2:1)
        canvas_hoehe_mm = config.zeichen_hoehe_mm - (2 * config.sicherheitsabstand_mm)
        canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
        canvas_hoehe_px = mm_to_pixels(canvas_hoehe_mm, config.dpi)
        canvas_breite_px = mm_to_pixels(canvas_breite_mm, config.dpi)

        # CHANGED: RGBA-Canvas mit transparentem Hintergrund
        bg_color = PNG_BACKGROUND_COLOR_TRANSPARENT if PNG_COLOR_MODE == PNG_COLOR_MODE_RGBA else PNG_BACKGROUND_COLOR_WHITE
        canvas = Image.new(PNG_COLOR_MODE, (canvas_breite_px, canvas_hoehe_px), bg_color)

        # SCHRITT 1: Linker Bereich - Grafik + Text (wie S2-Layout)
        links_breite_px = int(canvas_breite_px * (s1_links_prozent / 100.0))
        links_bereich = Image.new(PNG_COLOR_MODE, (links_breite_px, canvas_hoehe_px), bg_color)

        # Blanko-Zeichen erkennen
        is_blanko = SVGLoaderLocal.is_blanko_zeichen(svg_path)
        # NEW: S1-Blanko mit beidseitigen Schreiblinien erkennen
        is_blanko_s1_both = SVGLoaderLocal.is_blanko_s1_both(svg_path)

        # CHANGED v0.8.2.2: Stärkeangabe aus Blanko-Zeichen ermitteln
        # Überschreibt s1_staerke_anzeigen Parameter für die neuen Blanko-Varianten
        if is_blanko and SVGLoaderLocal.has_staerke_anzeige(svg_path):
            s1_staerke_anzeigen = True
            self.logger.debug(f"Blanko-Zeichen {svg_path.stem} → Stärkeangabe aktiviert")
        elif is_blanko and not SVGLoaderLocal.has_staerke_anzeige(svg_path):
            s1_staerke_anzeigen = False
            self.logger.debug(f"Blanko-Zeichen {svg_path.stem} → Stärkeangabe deaktiviert")

        # NEW: SVG-Grafik holen (entweder aus Template oder neu rendern)
        zeichen_image = None
        render_start_time = None

        if svg_template is not None and not is_blanko:
            # Template klonen (PERFORMANCE BOOST!)
            try:
                zeichen_image = svg_template.copy()
                self.logger.debug("Verwende SVG-Template (optimiert)")
            except (AssertionError, OSError) as e:
                # Fallback: SVG neu rendern
                self.logger.warning("SVG-Template konnte nicht kopiert werden ({}), rendere neu".format(str(e)))

        if zeichen_image is None and not is_blanko:
            # SVG-Grafik rendern (mit angepasster Breite für linken Bereich)
            self.logger.debug("START: SVG-Rendering von {}".format(svg_path.name))
            render_start_time = time.time()

            links_breite_mm = canvas_breite_mm * (s1_links_prozent / 100.0)

            # Text-Höhe berechnen (wenn Text vorhanden)
            if config.modus != MODUS_OHNE_TEXT:
                # CRITICAL: Temporäre Config für Textberechnung (linker Bereich)
                from dataclasses import replace
                temp_config = replace(
                    config,
                    zeichen_breite_mm=links_breite_mm,  # Nur linke Breite
                    zeichen_hoehe_mm=canvas_hoehe_mm  # Verfügbare Höhe
                )
                text_height_mm = self.text_overlay.calculate_text_height_mm(temp_config)
                verfuegbare_hoehe_mm = canvas_hoehe_mm - text_height_mm - config.abstand_grafik_text_mm
            else:
                verfuegbare_hoehe_mm = canvas_hoehe_mm

            # Grafik rendern (mit Breite des linken Bereichs)
            zeichen_image = self._svg_to_image(
                svg_path,
                max_height_mm=verfuegbare_hoehe_mm,
                max_width_mm=links_breite_mm,
                dpi=config.dpi,
                render_scale=config.render_scale
            )

            # NEW: Zeitmessung Rendering beenden
            if render_start_time:
                timings['render'] = time.time() - render_start_time
                self.logger.debug("ENDE: SVG-Rendering ({:.3f}s)".format(timings['render']))

        # Grafik einfügen (falls vorhanden - nicht bei Blanko)
        # CHANGED v0.8.2.3: Auch nicht bei BLANKO_S1_LEER (komplett leer)
        is_blanko_leer_gfx = (str(svg_path.stem) == "BLANKO_S1_LEER")
        if zeichen_image is not None and not is_blanko_leer_gfx:
            # Grafik horizontal zentriert im linken Bereich
            x_offset = (links_breite_px - zeichen_image.width) // 2
            y_offset = 0  # Grafik oben

            # Grafik einfügen (mit Alpha-Maske für glatte Kanten)
            if zeichen_image.mode == 'RGBA':
                links_bereich.paste(zeichen_image, (x_offset, y_offset), mask=zeichen_image)
            else:
                links_bereich.paste(zeichen_image, (x_offset, y_offset))

        # Text zeichnen (falls Modus != OHNE_TEXT UND NICHT S1-Blanko beidseitig)
        # NEW: Bei S1-Blanko beidseitig sollen beide Seiten Schreiblinien haben (kein Text)
        # CHANGED v0.8.2.3: Auch BLANKO_S1_LEER ausschließen (komplett leer)
        is_blanko_leer = (str(svg_path.stem) == "BLANKO_S1_LEER")
        if config.modus != MODUS_OHNE_TEXT and not is_blanko_s1_both and not is_blanko_leer:
            # CRITICAL: Temporäre Config für linken Bereich erstellen
            # Der links_bereich ist schmaler als das volle Zeichen!
            from dataclasses import replace
            links_config = replace(
                config,
                zeichen_breite_mm=canvas_breite_mm * (s1_links_prozent / 100.0),  # Nur linke Breite
                zeichen_hoehe_mm=canvas_hoehe_mm  # Verfügbare Höhe (nach Sicherheitsabstand)
            )
            self.text_overlay.draw_text_on_canvas(links_bereich, links_config)

        # NEW: Bei S1-Blanko beidseitig Schreiblinien auch auf linker Seite zeichnen
        # CHANGED v0.8.2.2: Aber nicht für BLANKO_S1_LEER (komplett leer)
        if is_blanko_s1_both and str(svg_path.stem) != "BLANKO_S1_LEER":
            # Schreiblinien-Parameter berechnen (NEUE LOGIK: Anzahl → Zeilenhöhe → Schriftgröße)
            anzahl_zeilen = s1_anzahl_schreiblinien  # INPUT vom User (3-10)

            bottom_offset_mm = config.text_bottom_offset_mm
            bottom_offset_px = mm_to_pixels(bottom_offset_mm, config.dpi)

            verfuegbare_hoehe_mm = canvas_hoehe_mm - bottom_offset_mm

            # Zeilenhöhe berechnen (verfügbare Höhe / Anzahl Zeilen)
            line_height_mm = verfuegbare_hoehe_mm / anzahl_zeilen
            line_height_px = mm_to_pixels(line_height_mm, config.dpi)

            # Horizontale Grenzen für Schreiblinien
            # CRITICAL: Linien sollen an der Trennlinie durchgängig sein (kein Margin am Rand rechts)
            margin_px = mm_to_pixels(S1_LINE_MARGIN_MM, config.dpi)
            line_x_start_links = margin_px
            line_x_end_links = links_breite_px  # Bis zur Trennlinie (kein Margin rechts)

            # ImageDraw für linke Seite
            draw_links = ImageDraw.Draw(links_bereich)

            # Schreiblinien zeichnen (GLEICHE Y-Positionen wie rechte Seite!)
            # Erste Linie GENAU am bottom_offset (wie Text auf linker Seite)
            # CHANGED v0.8.2.3: Stärkeangabe NUR auf rechter Seite, nicht auf linker!
            # CHANGED v0.8.2.3: Sicherheitsüberprüfung für Canvas-Rand (wie rechte Seite)
            CANVAS_EDGE_SAFETY_PX = 2
            for i in range(anzahl_zeilen):
                y_from_bottom = bottom_offset_px + (i * line_height_px)
                y_pos = int(canvas_hoehe_px - y_from_bottom)

                # CRITICAL: Sicherstellen dass Linie innerhalb Canvas liegt (mindestens 2px vom Rand)
                if y_pos >= (canvas_hoehe_px - CANVAS_EDGE_SAFETY_PX):
                    y_pos = canvas_hoehe_px - CANVAS_EDGE_SAFETY_PX
                    self.logger.debug("Linke Seite: Linie {} zu nah am Rand, korrigiert auf y={}px".format(i, y_pos))

                # Normale Schreiblinie (KEINE Stärkeangabe auf linker Seite!)
                draw_links.line(
                    [(line_x_start_links, y_pos), (line_x_end_links, y_pos)],
                    fill=S1_LINE_COLOR,
                    width=S1_LINE_WIDTH
                )

            self.logger.info(
                "S1-Blanko beidseitig: {} Schreiblinien auf BEIDEN Seiten (durchgaengig an Trennlinie)".format(
                    anzahl_zeilen
                )
            )

        # Linken Bereich auf Haupt-Canvas einfügen
        canvas.paste(links_bereich, (0, 0))

        # SCHRITT 2: Rechter Bereich - Schreiblinien
        # CHANGED v0.8.2.2: Überspringen für BLANKO_S1_LEER (komplett leer)
        if str(svg_path.stem) != "BLANKO_S1_LEER":
            rechts_start_px = links_breite_px
            rechts_breite_px = canvas_breite_px - links_breite_px
            rechts_breite_mm = canvas_breite_mm * ((100 - s1_links_prozent) / 100.0)

            # ImageDraw für Linien
            draw = ImageDraw.Draw(canvas)

            # Schreiblinien-Parameter berechnen (NEUE LOGIK: Anzahl → Zeilenhöhe → Schriftgröße)
            anzahl_zeilen = s1_anzahl_schreiblinien  # INPUT vom User (3-10)

            # CRITICAL: Gleiche Referenz wie linke Seite - text_bottom_offset berücksichtigen
            bottom_offset_mm = config.text_bottom_offset_mm
            bottom_offset_px = mm_to_pixels(bottom_offset_mm, config.dpi)

            # Verfügbare Höhe für Schreiblinien (ohne bottom_offset)
            verfuegbare_hoehe_mm = canvas_hoehe_mm - bottom_offset_mm

            # Zeilenhöhe berechnen (verfügbare Höhe / Anzahl Zeilen)
            line_height_mm = verfuegbare_hoehe_mm / anzahl_zeilen
            line_height_px = mm_to_pixels(line_height_mm, config.dpi)

            # Horizontale Grenzen für Schreiblinien (mit Margin)
            # NEW: Bei S1-Blanko beidseitig kein Margin links (Linien treffen sich an Trennlinie)
            margin_px = mm_to_pixels(S1_LINE_MARGIN_MM, config.dpi)
            if is_blanko_s1_both:
                line_x_start = rechts_start_px  # Kein Margin links - direkt an Trennlinie
            else:
                line_x_start = rechts_start_px + margin_px
            line_x_end = canvas_breite_px - margin_px

            self.logger.info(
                "S1-Layout: {} Schreiblinien (Höhe: {:.1f}mm, Bottom-Offset: {:.1f}mm)".format(
                    anzahl_zeilen, line_height_mm, bottom_offset_mm
                )
            )

            # Schreiblinien zeichnen mit Stärkeangabe in erster Zeile
            # CRITICAL: Von unten nach oben (wie linke Seite mit text_bottom_offset)
            # FIXED: Minimaler Sicherheitsabstand (2px) vom Canvas-Rand, damit Linie sichtbar
            CANVAS_EDGE_SAFETY_PX = 2
            for i in range(anzahl_zeilen):
                # Zeile 0 = unterste Zeile, von unten nach oben
                y_from_bottom = bottom_offset_px + (i * line_height_px)
                y_pos = int(canvas_hoehe_px - y_from_bottom)

                # CRITICAL: Sicherstellen dass Linie innerhalb Canvas liegt (mindestens 2px vom Rand)
                if y_pos >= (canvas_hoehe_px - CANVAS_EDGE_SAFETY_PX):
                    y_pos = canvas_hoehe_px - CANVAS_EDGE_SAFETY_PX
                    self.logger.debug("Linie {} zu nah am Rand, korrigiert auf y={}px".format(i, y_pos))

                # CHANGED: ERSTE (oberste) Zeile mit Stärkeangabe (falls aktiviert)
                # CRITICAL: i == anzahl_zeilen - 1 ist die OBERSTE Zeile!
                # NEW: Stärkeangabe als gezeichnete Linien (nicht als Text!)
                if i == (anzahl_zeilen - 1) and s1_staerke_anzeigen:
                    self._draw_staerke_indicator(
                        draw,
                        y_pos,
                        line_x_start,
                        line_x_end,
                        int(line_height_px)
                    )
                    # Keine Schreiblinie - Stärkeangabe ersetzt sie komplett
                else:
                    # Normale Schreiblinie
                    draw.line(
                        [(line_x_start, y_pos), (line_x_end, y_pos)],
                        fill=S1_LINE_COLOR,
                        width=S1_LINE_WIDTH
                    )

            # SCHRITT 3.5: Orange Trennlinie zwischen Links/Rechts (nur bei Hilfslinien)
            if draw_cut_lines:
                from constants import CUT_LINE_COLOR_S1_BORDER, CUT_LINE_WIDTH_PX
                # Vertikale Linie bei rechts_start_px (Grenze zwischen Links und Rechts)
                draw.line(
                    [(rechts_start_px, 0), (rechts_start_px, canvas_hoehe_px)],
                    fill=CUT_LINE_COLOR_S1_BORDER,
                    width=CUT_LINE_WIDTH_PX
                )
                self.logger.debug(
                    "S1-Trennlinie (orange) gezeichnet bei x={}px ({:.1f}%)".format(
                        rechts_start_px, s1_links_prozent
                    )
                )
        else:
            self.logger.info("BLANKO_S1_LEER erkannt - keine Schreiblinien auf rechter Seite")

        # NEW: Zeitmessung Generate-Phase beenden
        timings['generate'] = time.time() - generate_start_time

        # SCHRITT 4: Print-Vorbereitung (Beschnittzugabe + Schnittlinien)
        # NEW: Export-Zeitmessung starten
        export_start_time = time.time()

        print_ready_image = self.print_preparer.prepare_for_print(
            canvas,
            config.dpi,
            draw_cut_lines=draw_cut_lines,
            zeichen_hoehe_mm=config.zeichen_hoehe_mm,
            zeichen_breite_mm=config.zeichen_breite_mm,
            sicherheitsabstand_mm=config.sicherheitsabstand_mm,
            beschnittzugabe_mm=config.beschnittzugabe_mm
        )

        # NEW: Zeitmessung Export-Phase beenden
        timings['export'] = time.time() - export_start_time

        # SCHRITT 5: Export oder Return
        if return_image:
            self.logger.info("ERFOLGREICH (S1-Layout Image zurückgegeben)")
            if track_timing:
                return (print_ready_image, timings)
            else:
                return print_ready_image
        else:
            output_file = self._export_image(
                print_ready_image,
                config.zeichen_id,
                "s1_layout",  # Modus-Suffix
                config.dpi,
                draw_cut_lines,
                config.output_dir
            )
            self.logger.info("ERFOLGREICH (S1-Layout): {}".format(output_file.name))
            if track_timing:
                return (output_file, timings)
            else:
                return output_file

    def create_zeichen_s1_batch(
        self,
        tasks: List[Tuple[Path, ZeichenConfig]],
        s1_links_prozent: int,
        s1_anzahl_schreiblinien: int,
        s1_staerke_anzeigen: bool,
        draw_cut_lines: bool = False,
        num_threads: int = 4,
        progress_callback: Optional[callable] = None,
        preparing_callback: Optional[callable] = None,
        use_templates: bool = True,
        chunk_size: Optional[int] = None
    ) -> Tuple[List[Path], List[Tuple[str, str]]]:
        """
        Erstellt mehrere S1-Layout Zeichen parallel mit Multithreading

        NEUE RESSOURCEN-OPTIMIERUNG (v0.8.1):
        - Stapelbasierte Verarbeitung: Templates werden nur für Teilmengen erstellt
        - Template-System für Text und SVG (wie S2)
        - Reduziert RAM-Verbrauch massiv
        - Templates werden nach jedem Chunk explizit freigegeben
        - Aggressive Garbage Collection
        - Detailliertes Performance-Tracking

        Args:
            tasks: Liste von (svg_path, config) Tupeln
            s1_links_prozent: Aufteilung Links/Rechts in Prozent
            s1_anzahl_schreiblinien: Anzahl gewünschter Schreiblinien (3-10, Zeilenhöhe wird berechnet)
            s1_staerke_anzeigen: Stärke-Platzhalter anzeigen
            draw_cut_lines: Schnittlinien zeichnen
            num_threads: Anzahl paralleler Threads (default: 4)
            progress_callback: Optional callback(current, total, svg_name, status)
            preparing_callback: Optional callback(status_text) für Vorbereitungsphase
            use_templates: Template-Optimierung nutzen (default: True)
            chunk_size: Anzahl Zeichen pro Chunk (default: num_threads * 4)

        Returns:
            Tuple: (successful_files, errors)
                - successful_files: Liste von erfolgreich erstellten Dateipfaden
                - errors: Liste von (zeichen_id, error_message) Tupeln
        """
        if not tasks:
            return ([], [])

        # NEW: Stapelgröße berechnen (falls nicht angegeben)
        if chunk_size is None:
            from constants import DEFAULT_PNG_CHUNK_MULTIPLIER

            # Zeichengröße aus erstem Task ermitteln
            if tasks:
                first_config = tasks[0][1]
                max_dimension = max(first_config.zeichen_hoehe_mm, first_config.zeichen_breite_mm)

                # Dynamische Stapelgröße basierend auf Zeichengröße
                if max_dimension > ZEICHEN_SIZE_THRESHOLD_VERY_LARGE_MM:
                    multiplier = 1
                    self.logger.info(f"Sehr große Zeichen ({max_dimension}mm): Reduzierte Stapelgröße für häufige GC")
                elif max_dimension > ZEICHEN_SIZE_THRESHOLD_LARGE_MM:
                    multiplier = 2
                    self.logger.info(f"Große Zeichen ({max_dimension}mm): Reduzierte Stapelgröße für häufige GC")
                else:
                    multiplier = DEFAULT_PNG_CHUNK_MULTIPLIER

                chunk_size = num_threads * multiplier
            else:
                chunk_size = num_threads * DEFAULT_PNG_CHUNK_MULTIPLIER

        self.logger.info("Stapelbasierte Verarbeitung: Stapelgröße = {} Zeichen".format(chunk_size))

        # NEW: Zeit-Messung für Export
        import time
        import gc
        start_time = time.time()

        # NEW: Debug-Logging für Export-Start
        total_kopien = len(tasks)

        # NEW: Eindeutige Zeichen zählen (ohne Kopien)
        unique_zeichen = set()
        for svg_path, config in tasks:
            zeichen_base = config.zeichen_id.rsplit('_', 1)[0] if '_' in config.zeichen_id else config.zeichen_id
            unique_zeichen.add(zeichen_base)
        anzahl_eindeutige_zeichen = len(unique_zeichen)

        self.logger.debug("=" * 80)
        self.logger.debug("START: S1-Batch-Export von {} Zeichen ({} Kopien gesamt)".format(
            anzahl_eindeutige_zeichen, total_kopien))
        self.logger.debug("=" * 80)

        # NEW: Stapelbasierte Verarbeitung - globale Statistiken
        successful_files = []
        errors = []
        completed = 0
        all_timings = []
        stats_lock = Lock()

        # NEW: Tasks in Stapel aufteilen
        num_chunks = (len(tasks) + chunk_size - 1) // chunk_size
        self.logger.info("Verarbeite {} Tasks in {} Stapel (S1-Layout)".format(len(tasks), num_chunks))

        # NEW: Chunk-Loop
        for chunk_idx in range(num_chunks):
            chunk_start = chunk_idx * chunk_size
            chunk_end = min(chunk_start + chunk_size, len(tasks))
            chunk_tasks = tasks[chunk_start:chunk_end]

            self.logger.info("=" * 80)
            self.logger.info("CHUNK {}/{}: Zeichen {} bis {} ({} Zeichen)".format(
                chunk_idx + 1, num_chunks,
                chunk_start + 1, chunk_end,
                len(chunk_tasks)
            ))
            self.logger.info("=" * 80)

            # NEW: Templates NUR für aktuellen Chunk erstellen
            text_templates = {}
            svg_templates = {}

            if use_templates:
                self.logger.info("Erstelle Templates für Stapel {}/{}...".format(chunk_idx + 1, num_chunks))

                # NEW: Status-Callback für Vorbereitungsphase
                if preparing_callback:
                    preparing_callback("Stapel {}/{}: Erstelle Text-Templates...".format(chunk_idx + 1, num_chunks))

                # Text-Templates (nur für chunk_tasks!)
                text_template_keys_seen = set()
                for i, (svg_path, config) in enumerate(chunk_tasks):
                    template_key = self._get_template_key(config)
                    if template_key not in text_template_keys_seen:
                        text_templates[template_key] = self._create_text_template(config)
                        text_template_keys_seen.add(template_key)

                # NEW: Status-Callback für SVG-Templates
                if preparing_callback:
                    preparing_callback("Stapel {}/{}: Erstelle SVG-Templates...".format(chunk_idx + 1, num_chunks))

                # SVG-Templates (nur für chunk_tasks!)
                # CRITICAL: Für S1 müssen wir die linke Bereich-Breite berücksichtigen
                svg_template_keys_seen = set()
                for svg_path, config in chunk_tasks:
                    # CRITICAL: S1 SVG-Templates brauchen s1_links_prozent im Key
                    svg_template_key = self._get_svg_template_key(svg_path, config) + f"_s1_{s1_links_prozent}"
                    if svg_template_key not in svg_template_keys_seen:
                        try:
                            # FIXED: Blanko-Zeichen haben keine Grafik, kein Template noetig
                            if SVGLoaderLocal.is_blanko_zeichen(svg_path):
                                svg_template_keys_seen.add(svg_template_key)
                                continue

                            if preparing_callback:
                                preparing_callback("Stapel {}/{}: Rendere SVG-Template {}/{} ({})...".format(
                                    chunk_idx + 1, num_chunks,
                                    len(svg_template_keys_seen) + 1,
                                    len(chunk_tasks),
                                    svg_path.stem))

                            # S1-spezifisches SVG-Template erstellen (linke Bereich-Breite)
                            canvas_hoehe_mm = config.zeichen_hoehe_mm - (2 * config.sicherheitsabstand_mm)
                            canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
                            links_breite_mm = canvas_breite_mm * (s1_links_prozent / 100.0)

                            # Text-Hoehe berechnen (falls Text-Modus)
                            if config.modus != "nur_grafik":
                                from dataclasses import replace
                                temp_config = replace(
                                    config,
                                    zeichen_breite_mm=links_breite_mm,
                                    zeichen_hoehe_mm=canvas_hoehe_mm
                                )
                                text_height_mm = self.text_overlay.calculate_text_height_mm(temp_config)
                                verfuegbare_hoehe_mm = canvas_hoehe_mm - text_height_mm - config.abstand_grafik_text_mm
                            else:
                                verfuegbare_hoehe_mm = canvas_hoehe_mm

                            # SVG rendern fuer linken Bereich
                            svg_templates[svg_template_key] = self._svg_to_image(
                                svg_path,
                                max_height_mm=verfuegbare_hoehe_mm,
                                max_width_mm=links_breite_mm,
                                dpi=config.dpi,
                                render_scale=config.render_scale
                            )
                            svg_template_keys_seen.add(svg_template_key)
                        except Exception as e:
                            self.logger.warning("SVG-Template für {} konnte nicht erstellt werden: {}".format(
                                svg_path.stem, str(e)))
                            self.logger.debug("Fallback: Zeichen werden ohne SVG-Template gerendert")

                self.logger.info("Templates erstellt: {} Text-Templates, {} SVG-Templates".format(
                    len(text_templates), len(svg_templates)))

                if preparing_callback:
                    preparing_callback("Stapel {}/{}: Starte Verarbeitung...".format(chunk_idx + 1, num_chunks))

            # NEW: Worker-Funktion (innerhalb Chunk, hat Zugriff auf text_templates/svg_templates)
            def worker(svg_path: Path, config: ZeichenConfig):
                """Worker-Funktion für einen Thread"""
                try:
                    # Templates holen (falls aktiviert)
                    text_template = None
                    svg_template = None

                    if use_templates:
                        # Text-Template
                        template_key = self._get_template_key(config)
                        text_template = text_templates.get(template_key)

                        # SVG-Template (PERFORMANCE BOOST!)
                        svg_template_key = self._get_svg_template_key(svg_path, config) + f"_s1_{s1_links_prozent}"
                        svg_template = svg_templates.get(svg_template_key)

                    # NEW: Zeichen mit Zeitmessung erstellen
                    result = self.create_zeichen_s1(
                        svg_path, config,
                        s1_links_prozent, s1_anzahl_schreiblinien, s1_staerke_anzeigen,
                        draw_cut_lines,
                        text_template, svg_template,
                        track_timing=True  # NEW: Zeitmessung aktivieren
                    )

                    # Ergebnis entpacken
                    output_file, timings = result

                    return (True, output_file, None, timings)
                except Exception as e:
                    import traceback
                    error_msg = str(e)
                    self.logger.error("FEHLER bei {}: {}".format(config.zeichen_id, error_msg))
                    self.logger.debug("Traceback:\n{}".format(traceback.format_exc()))
                    return (False, None, error_msg, None)

            try:
                # NEW: ThreadPoolExecutor für aktuellen Chunk
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    # Nur chunk_tasks submiten (nicht alle tasks!)
                    futures = {}
                    for svg_path, config in chunk_tasks:
                        future = executor.submit(worker, svg_path, config)
                        futures[future] = (svg_path, config)

                    # Ergebnisse einsammeln
                    for future in as_completed(futures):
                        svg_path, config = futures[future]
                        success, output_file, error_msg, timings = future.result()

                        # Thread-safe Update
                        with stats_lock:
                            completed += 1

                            if success:
                                successful_files.append(output_file)
                                # NEW: Zeitmessungen sammeln
                                if timings:
                                    all_timings.append(timings)
                            else:
                                errors.append((config.zeichen_id, error_msg))

                            # Progress Callback (mit globaler Position!)
                            if progress_callback:
                                status = "OK" if success else "FEHLER"
                                progress_callback(completed, total_kopien, svg_path.stem, status)

            except Exception as e:
                self.logger.error(f"Fehler in Stapel {chunk_idx + 1}: {e}")
                raise

            finally:
                # NEW: Template-Cleanup nach Chunk (WICHTIG für Ressourcen-Freigabe!)
                self.logger.info("Stapel {}/{} abgeschlossen, gebe Templates frei...".format(chunk_idx + 1, num_chunks))
                text_templates.clear()
                svg_templates.clear()

                # Doppelte GC für bessere Speicherfreigabe
                gc.collect()
                gc.collect()

                self.logger.debug("Templates freigegeben und Garbage Collection durchgeführt (2x)")

        # END Chunk-Loop

        # NEW: Zeit-Messung Ende und Statistik-Ausgabe
        end_time = time.time()
        elapsed_time = end_time - start_time

        self.logger.debug("=" * 80)
        self.logger.debug("ENDE: S1-Batch-Export abgeschlossen")
        self.logger.debug("=" * 80)

        # NEW: Detaillierte Statistik-Berechnung
        if all_timings:
            render_times = [t['render'] for t in all_timings]
            generate_times = [t['generate'] for t in all_timings]
            export_times = [t['export'] for t in all_timings]

            total_times_per_zeichen = [
                t['render'] + t['generate'] + t['export']
                for t in all_timings
            ]

            def calc_stats(times):
                if not times:
                    return {'min': 0, 'max': 0, 'avg': 0}
                return {
                    'min': min(times),
                    'max': max(times),
                    'avg': sum(times) / len(times)
                }

            render_stats = calc_stats(render_times)
            generate_stats = calc_stats(generate_times)
            export_stats = calc_stats(export_times)
            total_stats = calc_stats(total_times_per_zeichen)

        # NEW: Formattierte Zeit-Ausgabe
        if elapsed_time < 60:
            time_str = "{:.1f} Sekunden".format(elapsed_time)
        else:
            minutes = int(elapsed_time / 60)
            seconds = elapsed_time % 60
            time_str = "{} Minute(n) {:.1f} Sekunden".format(minutes, seconds)

        avg_time_per_zeichen = elapsed_time / total_kopien if total_kopien > 0 else 0

        # NEW: Detaillierte Ausgabe auf INFO-Level
        self.logger.info("=" * 80)
        self.logger.info("S1-EXPORT-STATISTIK")
        self.logger.info("=" * 80)
        self.logger.info("Eindeutige Zeichen: {}".format(anzahl_eindeutige_zeichen))
        self.logger.info("Kopien exportiert: {}".format(len(successful_files)))
        self.logger.info("Fehler: {}".format(len(errors)))
        self.logger.info("Gesamtzeit: {}".format(time_str))
        self.logger.info("-" * 80)

        if all_timings:
            self.logger.info("ZEITSTATISTIK PRO SCHRITT (pro Kopie):")
            self.logger.info("  Rendern (SVG → Bild):")
            self.logger.info("    Min: {:.3f}s | Max: {:.3f}s | Durchschnitt: {:.3f}s".format(
                render_stats['min'], render_stats['max'], render_stats['avg']))
            self.logger.info("  Generieren (Canvas + Text + Schreiblinien):")
            self.logger.info("    Min: {:.3f}s | Max: {:.3f}s | Durchschnitt: {:.3f}s".format(
                generate_stats['min'], generate_stats['max'], generate_stats['avg']))
            self.logger.info("  Ausgeben (Print-Prep + Export):")
            self.logger.info("    Min: {:.3f}s | Max: {:.3f}s | Durchschnitt: {:.3f}s".format(
                export_stats['min'], export_stats['max'], export_stats['avg']))
            self.logger.info("-" * 80)
            self.logger.info("ZEITSTATISTIK PRO KOPIE (alle Schritte):")
            self.logger.info("  Min: {:.3f}s | Max: {:.3f}s | Durchschnitt: {:.3f}s".format(
                total_stats['min'], total_stats['max'], total_stats['avg']))
        else:
            self.logger.info("Durchschnitt: {:.2f}s pro Kopie".format(avg_time_per_zeichen))

        self.logger.info("=" * 80)

        return (successful_files, errors)

    def estimate_batch_time(
        self,
        num_tasks: int,
        num_threads: int = 4,
        avg_time_per_task: float = 10
    ) -> dict:
        """
        Schätzt die Dauer für Batch-Verarbeitung

        Args:
            num_tasks: Anzahl zu verarbeitender Zeichen
            num_threads: Anzahl paralleler Threads
            avg_time_per_task: Durchschnittliche Zeit pro Zeichen in Sekunden (default: 1.5s)

        Returns:
            Dict mit Zeitschätzung:
                - total_seconds: Geschätzte Gesamtzeit in Sekunden
                - minutes: Minuten
                - seconds: Sekunden (Rest)
                - formatted: Formatierter String "Xm Ys"
                - per_task: Zeit pro Zeichen
                - speedup: Beschleunigung durch Multithreading
        """
        # Sequenzielle Zeit
        sequential_time = num_tasks * avg_time_per_task

        # Mit Multithreading (mit Overhead-Faktor)
        overhead_factor = 1.1  # 10% Overhead für Thread-Management
        parallel_time = (sequential_time / num_threads) * overhead_factor

        minutes = int(parallel_time // 60)
        seconds = int(parallel_time % 60)
        formatted = "{}m {}s".format(minutes, seconds) if minutes > 0 else "{}s".format(seconds)

        speedup = sequential_time / parallel_time

        return {
            "total_seconds": parallel_time,
            "minutes": minutes,
            "seconds": seconds,
            "formatted": formatted,
            "per_task": avg_time_per_task,
            "speedup": speedup,
            "num_threads": num_threads,
            "num_tasks": num_tasks
        }

    def create_zeichen_batch(
        self,
        tasks: List[Tuple[Path, ZeichenConfig]],
        draw_cut_lines: bool = False,
        num_threads: int = 4,
        progress_callback: Optional[callable] = None,
        preparing_callback: Optional[callable] = None,
        use_templates: bool = True,
        chunk_size: Optional[int] = None  # NEW: Stapelgröße für Ressourcen-Optimierung
    ) -> Tuple[List[Path], List[Tuple[str, str]]]:
        """
        Erstellt mehrere Zeichen parallel mit Multithreading

        NEUE RESSOURCEN-OPTIMIERUNG (v0.6.0):
        - Stapelbasierte Verarbeitung: Templates werden nur für Teilmengen erstellt
        - Reduziert RAM-Verbrauch von ~2,5 GB auf ~250 MB (bei 100 Zeichen)
        - Templates werden nach jedem Chunk explizit freigegeben

        Args:
            tasks: Liste von (svg_path, config) Tupeln
            draw_cut_lines: Schnittlinien zeichnen
            num_threads: Anzahl paralleler Threads (default: 4)
            progress_callback: Optional callback(current, total, svg_name, status)
            preparing_callback: Optional callback(status_text) für Vorbereitungsphase
            use_templates: Template-Optimierung nutzen (default: True)
            chunk_size: Anzahl Zeichen pro Chunk (default: num_threads * 4)

        Returns:
            Tuple: (successful_files, errors)
                - successful_files: Liste von erfolgreich erstellten Dateipfaden
                - errors: Liste von (zeichen_id, error_message) Tupeln

        Example:
            tasks = [
                (svg_path1, config1),
                (svg_path2, config2),
                ...
            ]
            files, errors = poc.create_zeichen_batch(tasks, num_threads=4)
        """
        if not tasks:
            return ([], [])

        # NEW: Stapelgröße berechnen (falls nicht angegeben)
        # Bei großen Zeichen: Kleinere Stapel für häufigere Garbage Collection
        if chunk_size is None:
            from constants import DEFAULT_PNG_CHUNK_MULTIPLIER

            # Zeichengröße aus erstem Task ermitteln
            if tasks:
                first_config = tasks[0][1]
                max_dimension = max(first_config.zeichen_hoehe_mm, first_config.zeichen_breite_mm)

                # Dynamische Stapelgröße basierend auf Zeichengröße
                if max_dimension > ZEICHEN_SIZE_THRESHOLD_VERY_LARGE_MM:
                    # Sehr große Zeichen: Sehr kleine Stapel (häufige GC!)
                    multiplier = 1  # z.B. 6 Threads × 1 = 6 Zeichen/Stapel
                    self.logger.info(f"Sehr große Zeichen ({max_dimension}mm): Reduzierte Stapelgröße für häufige GC")
                elif max_dimension > ZEICHEN_SIZE_THRESHOLD_LARGE_MM:
                    # Große Zeichen: Kleine Stapel
                    multiplier = 2  # z.B. 6 Threads × 2 = 12 Zeichen/Stapel
                    self.logger.info(f"Große Zeichen ({max_dimension}mm): Reduzierte Stapelgröße für häufige GC")
                else:
                    # Normale Zeichen: Standard-Stapelgröße
                    multiplier = DEFAULT_PNG_CHUNK_MULTIPLIER

                chunk_size = num_threads * multiplier
            else:
                chunk_size = num_threads * DEFAULT_PNG_CHUNK_MULTIPLIER

        self.logger.info("Stapelbasierte Verarbeitung: Stapelgröße = {} Zeichen".format(chunk_size))

        # NEW: Zeit-Messung für Export
        import time
        import gc
        start_time = time.time()

        # NEW: Debug-Logging für Export-Start
        total_kopien = len(tasks)

        # NEW: Eindeutige Zeichen zählen (ohne Kopien)
        unique_zeichen = set()
        for svg_path, config in tasks:
            # Zeichen-ID ohne Kopiernummer (alles vor "_001", "_002" etc.)
            zeichen_base = config.zeichen_id.rsplit('_', 1)[0] if '_' in config.zeichen_id else config.zeichen_id
            unique_zeichen.add(zeichen_base)
        anzahl_eindeutige_zeichen = len(unique_zeichen)

        self.logger.debug("=" * 80)
        self.logger.debug("START: Batch-Export von {} Zeichen ({} Kopien gesamt)".format(
            anzahl_eindeutige_zeichen, total_kopien))
        self.logger.debug("=" * 80)

        # NEW: Stapelbasierte Verarbeitung - globale Statistiken
        successful_files = []
        errors = []
        completed = 0
        all_timings = []
        stats_lock = Lock()

        # NEW: Tasks in Stapel aufteilen
        num_chunks = (len(tasks) + chunk_size - 1) // chunk_size
        self.logger.info("Verarbeite {} Tasks in {} Stapel".format(len(tasks), num_chunks))

        # NEW: Chunk-Loop
        for chunk_idx in range(num_chunks):
            chunk_start = chunk_idx * chunk_size
            chunk_end = min(chunk_start + chunk_size, len(tasks))
            chunk_tasks = tasks[chunk_start:chunk_end]

            self.logger.info("=" * 80)
            self.logger.info("CHUNK {}/{}: Zeichen {} bis {} ({} Zeichen)".format(
                chunk_idx + 1, num_chunks,
                chunk_start + 1, chunk_end,
                len(chunk_tasks)
            ))
            self.logger.info("=" * 80)

            # NEW: Templates NUR für aktuellen Chunk erstellen
            text_templates = {}
            svg_templates = {}

            if use_templates:
                self.logger.info("Erstelle Templates für Stapel {}/{}...".format(chunk_idx + 1, num_chunks))

                # NEW: Status-Callback für Vorbereitungsphase
                if preparing_callback:
                    preparing_callback("Stapel {}/{}: Erstelle Text-Templates...".format(chunk_idx + 1, num_chunks))

                # Text-Templates (nur für chunk_tasks!)
                text_template_keys_seen = set()
                for i, (svg_path, config) in enumerate(chunk_tasks):
                    template_key = self._get_template_key(config)
                    if template_key not in text_template_keys_seen:
                        text_templates[template_key] = self._create_text_template(config)
                        text_template_keys_seen.add(template_key)

                # NEW: Status-Callback für SVG-Templates
                if preparing_callback:
                    preparing_callback("Stapel {}/{}: Erstelle SVG-Templates...".format(chunk_idx + 1, num_chunks))

                # SVG-Templates (nur fuer chunk_tasks!)
                svg_template_keys_seen = set()
                for svg_path, config in chunk_tasks:
                    svg_template_key = self._get_svg_template_key(svg_path, config)
                    if svg_template_key not in svg_template_keys_seen:
                        try:
                            # FIXED: Blanko-Zeichen haben keine Grafik, kein Template noetig
                            if SVGLoaderLocal.is_blanko_zeichen(svg_path):
                                svg_template_keys_seen.add(svg_template_key)
                                continue

                            # NEW: Status-Update pro SVG-Template (mit Dateinamen)
                            if preparing_callback:
                                preparing_callback("Stapel {}/{}: Rendere SVG-Template {}/{} ({})...".format(
                                    chunk_idx + 1, num_chunks,
                                    len(svg_template_keys_seen) + 1,
                                    len(chunk_tasks),
                                    svg_path.stem))

                            svg_templates[svg_template_key] = self._create_svg_template(svg_path, config)
                            svg_template_keys_seen.add(svg_template_key)
                        except Exception as e:
                            # FIXED: Template-Fehler loggen, aber Export fortsetzen
                            self.logger.warning("SVG-Template für {} konnte nicht erstellt werden: {}".format(
                                svg_path.stem, str(e)))
                            self.logger.debug("Fallback: Zeichen werden ohne SVG-Template gerendert")

                self.logger.info("Templates erstellt: {} Text-Templates, {} SVG-Templates".format(
                    len(text_templates), len(svg_templates)))

                # NEW: Status-Callback für Start der Verarbeitung
                if preparing_callback:
                    preparing_callback("Stapel {}/{}: Starte Verarbeitung...".format(chunk_idx + 1, num_chunks))

            # NEW: Worker-Funktion (innerhalb Chunk, hat Zugriff auf text_templates/svg_templates)
            def worker(svg_path: Path, config: ZeichenConfig):
                """Worker-Funktion für einen Thread"""
                try:
                    # Templates holen (falls aktiviert)
                    text_template = None
                    svg_template = None

                    if use_templates:
                        # Text-Template
                        template_key = self._get_template_key(config)
                        text_template = text_templates.get(template_key)

                        # SVG-Template (PERFORMANCE BOOST!)
                        svg_template_key = self._get_svg_template_key(svg_path, config)
                        svg_template = svg_templates.get(svg_template_key)

                    # NEW: Zeichen mit Zeitmessung erstellen
                    result = self.create_zeichen(
                        svg_path, config, draw_cut_lines,
                        text_template, svg_template,
                        track_timing=True  # NEW: Zeitmessung aktivieren
                    )

                    # Ergebnis entpacken
                    output_file, timings = result

                    return (True, output_file, None, timings)
                except Exception as e:
                    # FIXED: Fehler loggen!
                    import traceback
                    error_msg = str(e)
                    self.logger.error("FEHLER bei {}: {}".format(config.zeichen_id, error_msg))
                    self.logger.debug("Traceback:\n{}".format(traceback.format_exc()))
                    return (False, None, error_msg, None)

            try:
                # NEW: ThreadPoolExecutor für aktuellen Chunk
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    # Nur chunk_tasks submiten (nicht alle tasks!)
                    futures = {}
                    for svg_path, config in chunk_tasks:
                        future = executor.submit(worker, svg_path, config)
                        futures[future] = (svg_path, config)

                    # Ergebnisse einsammeln
                    for future in as_completed(futures):
                        svg_path, config = futures[future]
                        success, output_file, error_msg, timings = future.result()

                        # Thread-safe Update
                        with stats_lock:
                            completed += 1

                            if success:
                                successful_files.append(output_file)
                                # NEW: Zeitmessungen sammeln
                                if timings:
                                    all_timings.append(timings)
                            else:
                                errors.append((config.zeichen_id, error_msg))

                            # Progress Callback (mit globaler Position!)
                            if progress_callback:
                                status = "OK" if success else "FEHLER"
                                progress_callback(completed, total_kopien, svg_path.stem, status)
                        pass

            except Exception as e:
                # Explizites Exception-Logging
                self.logger.error(f"Fehler in Stapel {chunk_idx + 1}: {e}")
                raise  # Re-raise für äußere Fehlerbehandlung

            finally:
                # NEW: Template-Cleanup nach Chunk (WICHTIG für Ressourcen-Freigabe!)
                # v7.1 Phase 2: Aggressivere Garbage Collection für große Zeichen
                self.logger.info("Stapel {}/{} abgeschlossen, gebe Templates frei...".format(chunk_idx + 1, num_chunks))
                text_templates.clear()
                svg_templates.clear()

                # v7.1 Phase 2: Doppelte GC für bessere Speicherfreigabe
                gc.collect()  # Generation 0-2
                gc.collect()  # Nochmals für zirkuläre Referenzen

                self.logger.debug("Templates freigegeben und Garbage Collection durchgeführt (2x)")

        # END Chunk-Loop

        # NEW: Zeit-Messung Ende und Statistik-Ausgabe
        end_time = time.time()
        elapsed_time = end_time - start_time

        # NEW: Debug-Logging für Export-Ende
        self.logger.debug("=" * 80)
        self.logger.debug("ENDE: Batch-Export abgeschlossen")
        self.logger.debug("=" * 80)

        # NEW: Detaillierte Statistik-Berechnung
        if all_timings:
            # Pro Schritt: render, generate, export
            render_times = [t['render'] for t in all_timings]
            generate_times = [t['generate'] for t in all_timings]
            export_times = [t['export'] for t in all_timings]

            # Pro Zeichen: Gesamt-Zeit (alle Schritte)
            total_times_per_zeichen = [
                t['render'] + t['generate'] + t['export']
                for t in all_timings
            ]

            # Statistik-Funktionen
            def calc_stats(times):
                if not times:
                    return {'min': 0, 'max': 0, 'avg': 0}
                return {
                    'min': min(times),
                    'max': max(times),
                    'avg': sum(times) / len(times)
                }

            render_stats = calc_stats(render_times)
            generate_stats = calc_stats(generate_times)
            export_stats = calc_stats(export_times)
            total_stats = calc_stats(total_times_per_zeichen)

        # NEW: Formattierte Zeit-Ausgabe
        if elapsed_time < 60:
            time_str = "{:.1f} Sekunden".format(elapsed_time)
        else:
            minutes = int(elapsed_time / 60)
            seconds = elapsed_time % 60
            time_str = "{} Minute(n) {:.1f} Sekunden".format(minutes, seconds)

        avg_time_per_zeichen = elapsed_time / total_kopien if total_kopien > 0 else 0

        # NEW: Detaillierte Ausgabe auf INFO-Level
        self.logger.info("=" * 80)
        self.logger.info("EXPORT-STATISTIK")
        self.logger.info("=" * 80)
        self.logger.info("Eindeutige Zeichen: {}".format(anzahl_eindeutige_zeichen))
        self.logger.info("Kopien exportiert: {}".format(len(successful_files)))
        self.logger.info("Fehler: {}".format(len(errors)))
        self.logger.info("Gesamtzeit: {}".format(time_str))
        self.logger.info("-" * 80)

        if all_timings:
            # Pro Schritt
            self.logger.info("ZEITSTATISTIK PRO SCHRITT (pro Kopie):")
            self.logger.info("  Rendern (SVG → Bild):")
            self.logger.info("    Min: {:.3f}s | Max: {:.3f}s | Durchschnitt: {:.3f}s".format(
                render_stats['min'], render_stats['max'], render_stats['avg']))
            self.logger.info("  Generieren (Canvas + Text + Grafik):")
            self.logger.info("    Min: {:.3f}s | Max: {:.3f}s | Durchschnitt: {:.3f}s".format(
                generate_stats['min'], generate_stats['max'], generate_stats['avg']))
            self.logger.info("  Ausgeben (Print-Prep + Export):")
            self.logger.info("    Min: {:.3f}s | Max: {:.3f}s | Durchschnitt: {:.3f}s".format(
                export_stats['min'], export_stats['max'], export_stats['avg']))
            self.logger.info("-" * 80)
            self.logger.info("ZEITSTATISTIK PRO KOPIE (alle Schritte):")
            self.logger.info("  Min: {:.3f}s | Max: {:.3f}s | Durchschnitt: {:.3f}s".format(
                total_stats['min'], total_stats['max'], total_stats['avg']))
        else:
            self.logger.info("Durchschnitt: {:.2f}s pro Kopie".format(avg_time_per_zeichen))

        self.logger.info("=" * 80)

        return (successful_files, errors)

    def _export_image(
        self,
        image: Image.Image,
        zeichen_id: str,
        modus: str,
        dpi: int,
        with_cut_lines: bool = False,
        output_dir: Path = None
    ) -> Path:
        """
        Exportiert Image als PNG

        Überschreibt existierende Dateien ohne Fehler.
        """
        # CHANGED: output_dir Parameter hinzugefügt
        if output_dir is None:
            output_dir = EXPORT_DIR

        suffix = "_mit_linien" if with_cut_lines else "_druckfertig"
        filename = "{}_{}{}.png".format(zeichen_id, modus, suffix)
        output_file = output_dir.resolve() / filename
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Info wenn Datei überschrieben wird
        if output_file.exists():
            self.logger.debug("Überschreibe existierende Datei: {}".format(filename))


        image.save(str(output_file), dpi=(dpi, dpi), compress_level=EXPORT_PNG_COMPRESS_LEVEL)

        return output_file

    def _get_template_key(self, config: ZeichenConfig) -> str:
        """
        Generiert eindeutigen Template-Key für Config

        Template-Key Komponenten:
        - Modus
        - Font-Size
        - DPI
        - Modus-spezifische Parameter (OV-Name, Freitext, Grafik-Position)

        Returns:
            Template-Key String (z.B. "ov_staerke_8pt_600dpi_OV_Musterstadt")
        """
        key_parts = [
            config.modus,
            "{}pt".format(config.font_size),
            "{}dpi".format(config.dpi)
        ]

        # Modus-spezifische Parameter
        if config.modus == MODUS_OV_STAERKE:
            if config.ov_name:
                key_parts.append("ov_{}".format(config.ov_name.replace(" ", "_")))
            else:
                key_parts.append("platzhalter")
        elif config.modus == MODUS_ORT_STAERKE:  # NEW: Ort+Stärke mit eigenem ort_name
            if config.ort_name:
                key_parts.append("ort_{}".format(config.ort_name.replace(" ", "_")))
            else:
                key_parts.append("platzhalter")
        elif config.modus == MODUS_FREITEXT:
            if config.freitext:
                key_parts.append("txt_{}".format(config.freitext.replace(" ", "_")[:20]))
            else:
                key_parts.append("platzhalter")
        elif config.modus == MODUS_DATEINAME:
            # FIXED: Dateiname muss eindeutig sein!
            if config.freitext:
                # Dateiname ist im freitext-Feld gespeichert
                key_parts.append("fname_{}".format(config.freitext.replace(" ", "_")))
            else:
                key_parts.append("platzhalter")
        elif config.modus == MODUS_OHNE_TEXT:
            key_parts.append("pos_{}".format(config.grafik_position))

        return "_".join(key_parts)

    def _create_text_template(self, config: ZeichenConfig) -> Image.Image:
        """
        Erstellt Text-Template ohne Grafik (nur für Batch-Optimierung)

        Template = Canvas mit Text, OHNE Grafik
        Kann wiederverwendet werden für alle Zeichen mit identischen Text-Parametern

        Returns:
            PIL Image mit Text (Canvas-Größe = Endgröße - Rand, rechteckig)
        """
        # CHANGED: Rechteckiger Canvas
        canvas_hoehe_mm = config.zeichen_hoehe_mm - (2 * config.sicherheitsabstand_mm)
        canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)
        canvas_hoehe_px = mm_to_pixels(canvas_hoehe_mm, config.dpi)
        canvas_breite_px = mm_to_pixels(canvas_breite_mm, config.dpi)
        # CHANGED: RGBA-Canvas mit transparentem Hintergrund (rechteckig)
        bg_color = PNG_BACKGROUND_COLOR_TRANSPARENT if PNG_COLOR_MODE == PNG_COLOR_MODE_RGBA else PNG_BACKGROUND_COLOR_WHITE
        template = Image.new(PNG_COLOR_MODE, (canvas_breite_px, canvas_hoehe_px), bg_color)

        # Text zeichnen (wenn nicht OHNE_TEXT)
        if config.modus != MODUS_OHNE_TEXT:
            self.text_overlay.draw_text_on_canvas(template, config)

        self.logger.debug("Template erstellt: {}".format(self._get_template_key(config)))
        return template

    def _get_svg_template_key(self, svg_path: Path, config: ZeichenConfig) -> str:
        """
        Generiert eindeutigen SVG-Template-Key

        PERFORMANCE: SVG-Grafiken mit gleichen Parametern werden nur 1x gerendert!

        SVG-Template-Key Komponenten:
        - SVG-Pfad (welche Grafik)
        - DPI (Auflösung)
        - Modus (bestimmt Grafik-Größe)
        - Custom Grafik-Größe (falls vorhanden)

        Returns:
            SVG-Template-Key String (z.B. "einheit_001_600dpi_ov_staerke_39mm")
        """
        key_parts = [
            svg_path.stem,  # Dateiname ohne Extension
            "{}dpi".format(config.dpi)
        ]

        # Modus beeinflusst Grafik-Größe
        key_parts.append(config.modus)

        # v7.1: Custom Grafik-Größe (Höhe und Breite separat)
        if config.custom_grafik_hoehe_mm is not None and config.custom_grafik_breite_mm is not None:
            key_parts.append("{}x{}mm".format(config.custom_grafik_breite_mm, config.custom_grafik_hoehe_mm))

        return "_".join(key_parts)

    def _create_svg_template(self, svg_path: Path, config: ZeichenConfig) -> Image.Image:
        """
        Rendert SVG-Grafik als wiederverwendbares Template

        PERFORMANCE-BOOST: Bei 10 Kopien wird SVG nur 1x gerendert statt 10x!

        Args:
            svg_path: Pfad zur SVG-Datei
            config: Zeichen-Konfiguration (für Größen-Berechnung)

        Returns:
            PIL Image der gerenderten SVG-Grafik (ohne Canvas/Text)
        """
        # Grafik-Größe berechnen (analog zu create_zeichen)
        if config.modus == MODUS_OHNE_TEXT:
            if config.custom_grafik_hoehe_mm is not None and config.custom_grafik_breite_mm is not None:
                max_grafik_height_mm = config.custom_grafik_hoehe_mm
                max_grafik_width_mm = config.custom_grafik_breite_mm
            else:
                max_grafik_groesse_mm = self._get_max_grafik_groesse_mm()
                max_grafik_height_mm = max_grafik_groesse_mm
                max_grafik_width_mm = max_grafik_groesse_mm
        else:
            # MIT Text: Höhe muss IMMER Text + Offsets berücksichtigen!
            # custom_grafik_* sind nur MAXIMUM-Werte

            # Text-Höhe berechnen (enthält Text + TEXT_BOTTOM_OFFSET_MM)
            text_height_mm = self.text_overlay.calculate_text_height_mm(config)

            # Canvas-Abmessungen berechnen (rechteckig!)
            canvas_hoehe_mm = config.zeichen_hoehe_mm - (2 * config.sicherheitsabstand_mm)
            canvas_breite_mm = config.zeichen_breite_mm - (2 * config.sicherheitsabstand_mm)

            # Verfügbare Höhe für Grafik nach Abzug von Text + Abständen
            verfuegbare_hoehe = canvas_hoehe_mm - text_height_mm - config.abstand_grafik_text_mm

            # v7.1: Wenn custom_grafik_* gesetzt, als MAXIMUM verwenden
            if config.custom_grafik_hoehe_mm is not None and config.custom_grafik_breite_mm is not None:
                # Verwende das KLEINERE von custom und verfügbar (damit Text nicht überdeckt wird!)
                max_grafik_height_mm = min(config.custom_grafik_hoehe_mm, verfuegbare_hoehe)
                max_grafik_width_mm = min(config.custom_grafik_breite_mm, canvas_breite_mm)
            else:
                # Fallback: Verwende verfügbare Größe
                max_grafik_height_mm = verfuegbare_hoehe
                max_grafik_width_mm = canvas_breite_mm

        # SVG rendern
        zeichen_image = self._svg_to_image(
            svg_path,
            max_height_mm=max_grafik_height_mm,
            max_width_mm=max_grafik_width_mm,
            dpi=config.dpi,
            render_scale=config.render_scale  # v7.1 Phase 2
        )

        self.logger.debug("SVG-Template erstellt: {}".format(self._get_svg_template_key(svg_path, config)))
        return zeichen_image

    def scan_available_zeichen(self) -> dict:
        """Scannt verfuegbare Zeichen"""
        all_svgs = self.svg_loader.get_all_svgs()
        result = {}
        for category, svg_paths in all_svgs.items():
            result[category] = [
                self.svg_loader.get_svg_info(svg_path)
                for svg_path in svg_paths
            ]
        return result

    def ask_custom_grafik_size(self) -> Optional[float]:
        """
        Interaktive Abfrage der benutzerdefinierten Grafikgröße für OHNE_TEXT Modus

        Returns:
            float: Benutzerdefinierte Größe in mm, oder None für Maximum (39mm)
        """
        print("")
        print("=" * 60)
        print("GRAFIKGRÖSSE FÜR MODUS 'OHNE TEXT'")
        print("=" * 60)
        max_grafik_groesse_mm = self._get_max_grafik_groesse_mm()
        print("Standard: Maximale Größe ({}mm × {}mm)".format(
            max_grafik_groesse_mm, max_grafik_groesse_mm))
        print("")
        print("Möchten Sie eine benutzerdefinierte Größe festlegen?")
        print("  [ENTER] = Maximum verwenden ({}mm)".format(max_grafik_groesse_mm))
        print("  [Zahl]  = Benutzerdefinierte Größe in mm (quadratisch)")
        print("")

        while True:
            user_input = input("Größe (in mm) oder ENTER für Maximum: ").strip()

            # ENTER = Maximum verwenden
            if not user_input:
                print("→ Verwende maximale Größe: {}mm".format(max_grafik_groesse_mm))
                return None

            # Versuche Zahl zu parsen
            try:
                size_mm = float(user_input)

                # Validierung
                is_valid, message = self.validate_custom_grafik_size(size_mm)

                if not is_valid:
                    print("✗ FEHLER: {}".format(message))
                    print("  Bitte erneut versuchen.")
                    continue

                # Warnung anzeigen (falls vorhanden)
                if "WARNUNG" in message:
                    print("⚠ {}".format(message))
                    confirm = input("  Trotzdem verwenden? [j/N]: ").strip().lower()
                    if confirm != 'j':
                        continue

                print("✓ {}".format(message))
                return size_mm

            except ValueError:
                print("✗ FEHLER: Ungültige Eingabe. Bitte eine Zahl eingeben.")
                continue


def run_comprehensive(max_per_category: int = 6, num_threads: int = 4):
    """
    Comprehensive Test mit Multithreading

    Args:
        max_per_category: Max. Zeichen pro Kategorie
        num_threads: Anzahl paralleler Threads (default: 4)
    """
    print("=" * 80)
    print("COMPREHENSIVE TEST MIT MULTITHREADING")
    print("=" * 80)
    print("Threads: {}".format(num_threads))
    print("")

    logging_mgr = LoggingManager(log_level="WARNING", log_to_console=False)
    generator = TaktischeZeichenGenerator()

    available_zeichen = generator.scan_available_zeichen()

    if not available_zeichen:
        print("\n[FEHLER] Keine Zeichen gefunden!")
        return

    # Sammle alle Tasks
    all_tasks = []

    for category_name, zeichen_list in available_zeichen.items():
        zeichen_to_process = zeichen_list[:max_per_category]

        for zeichen_info in zeichen_to_process:
            svg_path = zeichen_info['path']

            # Alle 3 Modi für jedes Zeichen
            for modus_name, modus in [
                ("OV", MODUS_OV_STAERKE),
                ("Ruf", MODUS_RUF),
                ("Ohne", MODUS_OHNE_TEXT)
            ]:
                zeichen_id = "{}_{}_{}".format(
                    category_name.replace(" ", "_"),
                    svg_path.stem,
                    modus_name
                )

                config = ZeichenConfig(
                    zeichen_id=zeichen_id,
                    svg_path=svg_path,
                    modus=modus
                    # font_size und dpi werden aus RuntimeConfig geladen
                )

                all_tasks.append((svg_path, config))

    total_tasks = len(all_tasks)
    print("Zeichen gesamt: {}".format(total_tasks))

    # Zeitschätzung anzeigen
    estimation = generator.estimate_batch_time(total_tasks, num_threads)
    print("")
    print("[ZEITSCHÄTZUNG]")
    print("  Geschätzte Dauer: {}".format(estimation['formatted']))
    print("  Zeit pro Zeichen: {:.2f}s (Durchschnitt)".format(estimation['per_task']))
    print("  Speedup durch Multithreading: {:.1f}x".format(estimation['speedup']))
    print("")

    # Progress Callback
    def progress(current, total, svg_name, status):
        percent = (current / total * 100) if total > 0 else 0
        print("  [{:3d}/{:3d}] {:3.0f}%  {:<30} [{}]".format(
            current, total, percent, svg_name[:30], status
        ))

    # Batch-Verarbeitung mit Multithreading
    start_time = time.time()

    successful_files, errors = generator.create_zeichen_batch(
        all_tasks,
        draw_cut_lines=True,
        num_threads=num_threads,
        progress_callback=progress
    )

    elapsed = time.time() - start_time

    # Zusammenfassung
    print("")
    print("=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print("Erfolgreich:  {}".format(len(successful_files)))
    print("Fehler:       {}".format(len(errors)))
    print("Gesamtzeit:   {:.1f}s".format(elapsed))
    print("Durchschnitt: {:.2f}s pro Zeichen".format(elapsed / total_tasks if total_tasks > 0 else 0))
    print("")

    if errors:
        print("FEHLER:")
        for zeichen_id, error_msg in errors[:10]:  # Max 10 Fehler anzeigen
            print("  - {}: {}".format(zeichen_id, error_msg[:60]))
        if len(errors) > 10:
            print("  ... und {} weitere Fehler".format(len(errors) - 10))
        print("")


if __name__ == "__main__":
    # Usage: python taktische_zeichen_generator.py comprehensive [max_per_category] [num_threads]
    # Example: python taktische_zeichen_generator.py comprehensive 6 4
    if len(sys.argv) > 1 and sys.argv[1] == "comprehensive":
        max_per_cat = int(sys.argv[2]) if len(sys.argv) > 2 else 6
        num_threads = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        run_comprehensive(max_per_cat, num_threads)
    else:
        print("TaktischeZeichenGenerator - Verwenden Sie als Modul")
        print("")
        print("Comprehensive Test:")
        print("  python taktische_zeichen_generator.py comprehensive [max_per_category] [num_threads]")
        print("")
        print("Beispiel:")
        print("  python taktische_zeichen_generator.py comprehensive 6 4")

# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PATCH 2: taktische_zeichen_generator.py - ÄNDERUNGEN")
    print("=" * 80)
    print("\n[PROBLEM]")
    print("  Templates werden bei Exception nicht freigegeben")
    print("  → Memory-Leak bei Fehler während Batch-Verarbeitung")
    
    print("\n[LÖSUNG]")
    print("  Template-Cleanup in finally-Block verschoben")
    print("  → Wird IMMER ausgeführt (auch bei Exception)")
    
    print("\n[VORTEILE]")
    print("  ✅ Keine Memory-Leaks mehr")
    print("  ✅ Robustere Fehlerbehandlung")
    print("  ✅ Sauberes Ressourcen-Management")
    
    print("\n" + "=" * 80)
    print("STATUS: Patch bereit zum Anwenden")
    print("=" * 80)
