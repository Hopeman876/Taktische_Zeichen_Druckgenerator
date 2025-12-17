#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
print_preparer.py - Druckvorbereitung

Version: 1.0.0 (Produktionsversion)

FUNKTIONSWEISE:
- Canvas ist bereits 39x39mm (Grafik + Text fertig positioniert!)
- Hier werden nur noch Ränder hinzugefügt
- KEINE Positionierung mehr nötig!
"""

from PIL import Image, ImageDraw, ImageFont
import logging
from pathlib import Path

from constants import (
    DEFAULT_ZEICHEN_HOEHE_MM,
    DEFAULT_ZEICHEN_BREITE_MM,
    DEFAULT_SICHERHEITSABSTAND_MM,
    DEFAULT_BESCHNITTZUGABE_MM,
    DEFAULT_DPI,
    BG_COLOR,
    CUT_LINE_WIDTH_PX,
    CUT_LINE_LABEL_FONT_SIZE,
    CUT_LINE_LABEL_OFFSET_PX,
    CUT_LINE_LABEL_STROKE_WIDTH,
    CUT_LINE_LABEL_STROKE_COLOR,
    CUT_LINE_COLOR_BESCHNITT,
    CUT_LINE_COLOR_SCHNITT,
    CUT_LINE_COLOR_SICHERHEIT,
    PNG_COLOR_MODE,  # NEW: Farbmodus (RGBA fuer Transparenz)
    PNG_COLOR_MODE_RGBA,  # NEW: RGBA-Konstante
    PNG_BACKGROUND_COLOR_TRANSPARENT,  # NEW: Transparente Hintergrundfarbe
    PNG_BACKGROUND_COLOR_WHITE,  # NEW: Weisse Hintergrundfarbe
    mm_to_pixels,
    calculate_print_dimensions
)


class PrintPreparer:
    """
    Bereitet Images für Druck vor

    FUNKTIONSWEISE:
    - Input ist bereits 39x39mm Canvas (fertig!)
    - Hier werden nur Ränder hinzugefügt:
      1. Sicherheitsrand (3mm) -> 45x45mm
      2. Beschnittzugabe (3mm) -> 51x51mm
    - KEINE Positionierung mehr!
    """
    
    def __init__(self):
        """Initialisiert PrintPreparer"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("PrintPreparerV2 v2.3 (KORRIGIERT) initialisiert")
    
    def prepare_for_print(
        self,
        canvas: Image.Image,
        dpi: int = None,
        draw_cut_lines: bool = False,
        zeichen_hoehe_mm: float = None,
        zeichen_breite_mm: float = None,
        sicherheitsabstand_mm: float = None,
        beschnittzugabe_mm: float = None
    ) -> Image.Image:
        """
        Bereitet Canvas fuer Druck vor (RECHTECKIGE Zeichen unterstützt!)

        WICHTIG:
        - canvas kann rechteckig sein (Höhe != Breite)
        - Hier werden Rand und Beschnitt hinzugefügt

        Workflow:
        1. Pruefen: Canvas muss (zeichen_hoehe/breite - 2×sicherheitsabstand) sein
        2. Rand hinzufügen -> endgroesse (zeichen_hoehe/breite)
        3. Beschnittzugabe (3mm) -> datei_groesse
        4. Optional: Schneidelinien

        Args:
            canvas: PIL Image (Canvas = zeichen_hoehe/breite - 2×sicherheitsabstand)
            dpi: Aufloesung
            draw_cut_lines: Schneidelinien
            zeichen_hoehe_mm: Höhe des fertigen Zeichens (NACH Zuschnitt)
            zeichen_breite_mm: Breite des fertigen Zeichens (NACH Zuschnitt)
            sicherheitsabstand_mm: Sicherheitsabstand (Grafik/Text zum fertigen Rand)
            beschnittzugabe_mm: Beschnittzugabe (wird rund um das Zeichen hinzugefügt)

        Returns:
            PIL Image (druckfertig mit Beschnitt)

        Beispiel:
            zeichen_hoehe=45mm, zeichen_breite=45mm, rand=3mm
            → Canvas: 39×39mm (Input)
            → Mit Rand: 45×45mm (endgroesse)
            → Mit Beschnitt: 51×51mm (datei_groesse, Output)

            zeichen_hoehe=28mm, zeichen_breite=32mm, rand=0mm
            → Canvas: 28×32mm (Input)
            → Mit Rand: 28×32mm (endgroesse)
            → Mit Beschnitt: 34×38mm (datei_groesse, Output)
        """
        # RuntimeConfig-Defaults laden falls nicht angegeben
        from runtime_config import get_config
        config = get_config()
        if dpi is None:
            dpi = config.export_dpi
        if zeichen_hoehe_mm is None:
            zeichen_hoehe_mm = config.zeichen_hoehe_mm
        if zeichen_breite_mm is None:
            zeichen_breite_mm = config.zeichen_breite_mm
        if sicherheitsabstand_mm is None:
            sicherheitsabstand_mm = config.sicherheitsabstand_mm
        if beschnittzugabe_mm is None:
            beschnittzugabe_mm = config.beschnittzugabe_mm

        # FIXED: Mit Config-Werten berechnen (rechteckige Zeichen!)
        dims = calculate_print_dimensions(dpi, zeichen_hoehe_mm, zeichen_breite_mm, sicherheitsabstand_mm, beschnittzugabe_mm)
        
        self.logger.info("Druckvorbereitung @ {} DPI".format(dpi))
        self.logger.debug("Input Canvas: {}x{}px".format(canvas.width, canvas.height))

        # SCHRITT 1: Pruefen ob Canvas die erwartete Größe hat (RECHTECKIG!)
        # CHANGED: Separate Prüfung für Höhe und Breite
        expected_hoehe_px = dims['canvas_hoehe_px']
        expected_breite_px = dims['canvas_breite_px']
        if canvas.height != expected_hoehe_px or canvas.width != expected_breite_px:
            self.logger.warning(
                "WARNUNG: Canvas ist {}x{}px (B×H), erwartet {}x{}px ({}×{}mm)".format(
                    canvas.width, canvas.height,
                    expected_breite_px, expected_hoehe_px,
                    dims['canvas_breite_mm'], dims['canvas_hoehe_mm']
                )
            )
        
        # SCHRITT 2: Sicherheitsrand hinzufügen
        with_safety = self._add_safety_margin(canvas, dims)

        # SCHRITT 3: Beschnittzugabe hinzufügen
        with_bleed = self._add_bleed(with_safety, dims)

        # CHANGED: Log-Ausgabe für rechteckige Zeichen
        self.logger.info(
            "Druckvorbereitung fertig: {}x{}px ({}×{}mm)".format(
                with_bleed.width, with_bleed.height,
                dims['datei_breite_mm'], dims['datei_hoehe_mm']
            )
        )
        
        # SCHRITT 4: Schneidelinien (optional)
        if draw_cut_lines:
            with_bleed = self._draw_cut_lines(with_bleed, dims)
        
        # DPI-Metadaten
        with_bleed.info['dpi'] = (dpi, dpi)
        
        return with_bleed
    
    def _add_safety_margin(self, canvas: Image.Image, dims: dict) -> Image.Image:
        """
        Fuegt Sicherheitsrand hinzu (RECHTECKIGE Bilder unterstützt!)

        Beispiel quadratisch: 39×39mm -> 45×45mm
        Beispiel rechteckig: 28×32mm -> 28×32mm (mit rand=0)

        Args:
            canvas: Canvas (z.B. 39×39mm oder 28×32mm)
            dims: Dimensions-Dict (mit separaten Höhen/Breiten)

        Returns:
            Image mit Sicherheitsrand (z.B. 45×45mm oder 28×32mm)
        """
        margin_px = dims['sicherheitsrand_px']
        # CHANGED: Separate Werte für Höhe und Breite!
        target_breite_px = dims['endgroesse_breite_px']
        target_hoehe_px = dims['endgroesse_hoehe_px']

        # CHANGED: Neues Image mit gleichem Farbmodus wie Canvas (RGBA fuer Transparenz)
        bg_color = PNG_BACKGROUND_COLOR_TRANSPARENT if PNG_COLOR_MODE == PNG_COLOR_MODE_RGBA else BG_COLOR
        with_margin = Image.new(PNG_COLOR_MODE, (target_breite_px, target_hoehe_px), bg_color)

        # CHANGED: Canvas zentriert einfuegen mit Alpha-Maske bei RGBA
        # Dies erhält die glatten Konturen (Anti-Aliasing)
        if canvas.mode == 'RGBA':
            with_margin.paste(canvas, (margin_px, margin_px), mask=canvas)
        else:
            with_margin.paste(canvas, (margin_px, margin_px))

        self.logger.debug(
            "Sicherheitsrand: +{}mm ({}px) -> {}x{}px (B×H)".format(
                dims['SICHERHEITSABSTAND_MM'], margin_px,
                target_breite_px, target_hoehe_px
            )
        )

        return with_margin
    
    def _add_bleed(self, image: Image.Image, dims: dict) -> Image.Image:
        """
        Fuegt Beschnittzugabe hinzu (RECHTECKIGE Bilder unterstützt!)

        Beispiel quadratisch: 45×45mm -> 51×51mm
        Beispiel rechteckig: 28×32mm -> 34×38mm

        Args:
            image: Image mit Endgröße (z.B. 45×45mm oder 28×32mm)
            dims: Dimensions-Dict (mit separaten Höhen/Breiten)

        Returns:
            Image mit Beschnitt (z.B. 51×51mm oder 34×38mm)
        """
        bleed_px = dims['beschnitt_px']
        # CHANGED: Separate Werte für Höhe und Breite!
        target_breite_px = dims['datei_breite_px']
        target_hoehe_px = dims['datei_hoehe_px']

        # CHANGED: Neues Image mit gleichem Farbmodus wie Canvas (RGBA fuer Transparenz)
        bg_color = PNG_BACKGROUND_COLOR_TRANSPARENT if PNG_COLOR_MODE == PNG_COLOR_MODE_RGBA else BG_COLOR
        with_bleed = Image.new(PNG_COLOR_MODE, (target_breite_px, target_hoehe_px), bg_color)

        # CHANGED: Image zentriert einfuegen mit Alpha-Maske bei RGBA
        # Dies erhält die glatten Konturen (Anti-Aliasing)
        if image.mode == 'RGBA':
            with_bleed.paste(image, (bleed_px, bleed_px), mask=image)
        else:
            with_bleed.paste(image, (bleed_px, bleed_px))

        self.logger.debug(
            "Beschnittzugabe: +{}mm ({}px) -> {}x{}px (B×H)".format(
                dims['BESCHNITTZUGABE_MM'], bleed_px,
                target_breite_px, target_hoehe_px
            )
        )

        return with_bleed
    
    def _draw_cut_lines(self, image: Image.Image, dims: dict) -> Image.Image:
        """
        Zeichnet Schneidelinien (RECHTECKIGE Bilder unterstützt!)

        ROT: Beschnittkante (z.B. 51×51mm oder 34×38mm)
        BLAU: Schneidelinie (z.B. 45×45mm oder 28×32mm)
        GRUEN: Sicherheitsbereich (z.B. 39×39mm oder 28×32mm)

        Args:
            image: Image mit Beschnitt (rechteckig möglich!)
            dims: Dimensions-Dict (mit separaten Höhen/Breiten)

        Returns:
            Image mit Schneidelinien
        """
        img_with_lines = image.copy()
        draw = ImageDraw.Draw(img_with_lines)

        beschnitt_px = dims['beschnitt_px']
        sicherheit_px = dims['sicherheitsrand_px']

        self.logger.info("Zeichne Schneidelinien ({}px Breite)".format(CUT_LINE_WIDTH_PX))

        # Font - skaliert mit DPI für bessere Lesbarkeit bei niedrigen Auflösungen
        # Bei 600 DPI: 24pt (Standard)
        # Bei 100 DPI: 4pt (min: 8pt) → lesbar
        dpi = dims.get('dpi', 600)
        scaled_font_size = max(8, int(CUT_LINE_LABEL_FONT_SIZE * dpi / 600))
        try:
            label_font = ImageFont.truetype("arial.ttf", scaled_font_size)
        except Exception:
            try:
                label_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", scaled_font_size)
            except Exception:
                label_font = ImageFont.load_default()

        # ROT: Beschnittkante (aeusserster Rand)
        draw.rectangle(
            [(CUT_LINE_WIDTH_PX, CUT_LINE_WIDTH_PX),
             (image.width - CUT_LINE_WIDTH_PX, image.height - CUT_LINE_WIDTH_PX)],
            outline=CUT_LINE_COLOR_BESCHNITT,
            width=CUT_LINE_WIDTH_PX
        )
        # CHANGED: Label mit Breite×Höhe für rechteckige Zeichen
        # Label außen mit Standard-Offset
        draw.text(
            (CUT_LINE_LABEL_OFFSET_PX, CUT_LINE_LABEL_OFFSET_PX),
            "BESCHNITT ({:.1f}x{:.1f}mm)".format(
                dims['datei_breite_mm'], dims['datei_hoehe_mm']
            ),
            fill=CUT_LINE_COLOR_BESCHNITT,
            font=label_font,
            stroke_width=CUT_LINE_LABEL_STROKE_WIDTH,
            stroke_fill=CUT_LINE_LABEL_STROKE_COLOR
        )

        # BLAU: Schneidelinie (endgroesse)
        cut_offset = beschnitt_px
        draw.rectangle(
            [(cut_offset, cut_offset),
             (image.width - cut_offset, image.height - cut_offset)],
            outline=CUT_LINE_COLOR_SCHNITT,
            width=CUT_LINE_WIDTH_PX
        )
        # CHANGED: Label näher an blauer Linie (kleiner Offset)
        inner_label_offset = 10  # Kleinerer Offset für innere Labels
        draw.text(
            (cut_offset + inner_label_offset, cut_offset + inner_label_offset),
            "SCHNITT ({:.1f}x{:.1f}mm)".format(
                dims['endgroesse_breite_mm'], dims['endgroesse_hoehe_mm']
            ),
            fill=CUT_LINE_COLOR_SCHNITT,
            font=label_font,
            stroke_width=CUT_LINE_LABEL_STROKE_WIDTH,
            stroke_fill=CUT_LINE_LABEL_STROKE_COLOR
        )

        # GRUEN: Sicherheitsbereich (Canvas-Größe)
        safety_offset = beschnitt_px + sicherheit_px
        draw.rectangle(
            [(safety_offset, safety_offset),
             (image.width - safety_offset, image.height - safety_offset)],
            outline=CUT_LINE_COLOR_SICHERHEIT,
            width=CUT_LINE_WIDTH_PX
        )
        # CHANGED: Label näher an grüner Linie (kleiner Offset)
        draw.text(
            (safety_offset + inner_label_offset, safety_offset + inner_label_offset),
            "CANVAS ({:.1f}x{:.1f}mm)".format(
                dims['canvas_breite_mm'], dims['canvas_hoehe_mm']
            ),
            fill=CUT_LINE_COLOR_SICHERHEIT,
            font=label_font,
            stroke_width=CUT_LINE_LABEL_STROKE_WIDTH,
            stroke_fill=CUT_LINE_LABEL_STROKE_COLOR
        )

        self.logger.info("Alle Schneidelinien gezeichnet")

        return img_with_lines


# REMOVED: prepare_image_for_print() - ungenutzte Wrapper-Funktion (siehe cleanup)


if __name__ == "__main__":
    import logging
    from PIL import Image, ImageDraw
    from constants import ORGANIZATIONAL_BLUE, COLOR_SCHWARZ
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    print("=" * 80)
    print("PrintPreparer V2.3 Test (KORRIGIERT)")
    print("=" * 80)
    
    dims = calculate_print_dimensions(600)
    print("\n[DIMENSIONEN @ 600 DPI]")
    print("-" * 80)
    print("Grafik-Bereich:   {}mm ({}px)".format(dims['max_grafik_mm'], dims['max_grafik_px']))
    print("+ Sicherheit:     {}mm ({}px)".format(dims['SICHERHEITSABSTAND_MM'], dims['sicherheitsrand_px']))
    print("= Nach Zuschnitt: {}mm ({}px)".format(dims['endgroesse_mm'], dims['endgroesse_px']))
    print("+ Beschnitt:      {}mm ({}px)".format(dims['BESCHNITTZUGABE_MM'], dims['beschnitt_px']))
    print("= Datei-Groesse:  {}mm ({}px)".format(dims['datei_groesse_mm'], dims['datei_groesse_px']))
    
    # Test: 39mm Canvas erstellen
    canvas_size = dims['max_grafik_px']
    canvas = Image.new('RGB', (canvas_size, canvas_size), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    # Blaues Quadrat (Grafik simulieren)
    margin = 50
    draw.rectangle(
        [(margin, margin),
         (canvas_size - margin, canvas_size - margin)],
        fill=ORGANIZATIONAL_BLUE,
        outline=COLOR_SCHWARZ,
        width=5
    )
    
    canvas_hoehe_mm = DEFAULT_ZEICHEN_HOEHE_MM - (2 * DEFAULT_SICHERHEITSABSTAND_MM)
    print("\nTest-Canvas erstellt: {}x{}px ({}mm)".format(
        canvas.width, canvas.height, canvas_hoehe_mm
    ))

    # Druckvorbereitung
    print("\n[DRUCKVORBEREITUNG]")
    print("-" * 80)

    preparer = PrintPreparer()
    prepared = preparer.prepare_for_print(canvas, dpi=600, draw_cut_lines=True)

    # Speichern
    output_file = Path("test_print_v23_KORRIGIERT.png")
    prepared.save(output_file, dpi=(600, 600))

    datei_groesse_mm = DEFAULT_ZEICHEN_HOEHE_MM + (2 * DEFAULT_BESCHNITTZUGABE_MM)
    print("\n[OK] Gespeichert: {}".format(output_file))
    print("     Groesse: {}x{}px ({}mm)".format(
        prepared.width, prepared.height, datei_groesse_mm
    ))
    print("\n" + "=" * 80)