#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
profile_performance.py - Performance-Profiling

Misst wo die Zeit verloren geht beim Rendering.
"""

import time
from pathlib import Path

from logging_manager import LoggingManager
from taktische_zeichen_generator import TaktischeZeichenGenerator
from text_overlay import ZeichenConfig
from constants import (
    MODUS_OV_STAERKE,
    DEFAULT_FONT_SIZE,
    DEFAULT_DPI
)


def profile_single_zeichen(svg_path: Path):
    """Profiliert ein einzelnes Zeichen"""

    print("=" * 80)
    print("PERFORMANCE-PROFILING")
    print("=" * 80)
    print("")
    print("SVG: {}".format(svg_path.name))
    print("")

    # Init
    logging_mgr = LoggingManager(log_level="WARNING", log_to_console=False)

    timings = {}

    # SCHRITT 1: Initialisieren
    t_start = time.time()
    generator = TaktischeZeichenGenerator()
    timings['init'] = time.time() - t_start

    # SCHRITT 2: Config erstellen
    t_start = time.time()
    config = ZeichenConfig(
        zeichen_id="Profile_Test",
        svg_path=svg_path,
        modus=MODUS_OV_STAERKE,
        font_size=DEFAULT_FONT_SIZE,
        dpi=DEFAULT_DPI
    )
    timings['config'] = time.time() - t_start

    # SCHRITT 3: SVG validieren
    t_start = time.time()
    is_valid = generator.svg_loader.validate_svg(svg_path)
    timings['validate'] = time.time() - t_start

    # SCHRITT 4: Text-Höhe berechnen
    t_start = time.time()
    text_height = generator.text_overlay.calculate_text_height_mm(config)
    timings['text_height'] = time.time() - t_start

    # SCHRITT 5: Max Grafik-Größe
    t_start = time.time()
    max_grafik = generator.calculate_max_grafik_size_mm()
    timings['max_grafik'] = time.time() - t_start

    # SCHRITT 6: SVG zu Image (KRITISCH!)
    from constants import DEFAULT_ZEICHEN_HOEHE_MM, DEFAULT_SICHERHEITSABSTAND_MM

    # Canvas-Größe berechnen (45mm - 2×3mm = 39mm)
    max_grafik_groesse_mm = DEFAULT_ZEICHEN_HOEHE_MM - (2 * DEFAULT_SICHERHEITSABSTAND_MM)

    t_start = time.time()
    zeichen_image = generator._svg_to_image(
        svg_path,
        max_height_mm=max_grafik,
        max_width_mm=max_grafik_groesse_mm,
        dpi=config.dpi
    )
    timings['svg_to_image'] = time.time() - t_start

    # SCHRITT 7: Canvas erstellen
    from constants import mm_to_pixels

    t_start = time.time()
    from PIL import Image
    canvas_size_px = mm_to_pixels(max_grafik_groesse_mm, config.dpi)
    canvas = Image.new('RGB', (canvas_size_px, canvas_size_px), (255, 255, 255))
    x_offset = (canvas_size_px - zeichen_image.width) // 2
    canvas.paste(zeichen_image, (x_offset, 0))
    timings['canvas'] = time.time() - t_start

    # SCHRITT 8: Text hinzufügen
    t_start = time.time()
    generator.text_overlay.draw_text_on_canvas(canvas, config)
    timings['text_overlay'] = time.time() - t_start

    # SCHRITT 9: Druckvorbereitung
    t_start = time.time()
    print_ready = generator.print_preparer.prepare_for_print(
        canvas, config.dpi, draw_cut_lines=True
    )
    timings['print_prep'] = time.time() - t_start

    # SCHRITT 10: Export
    t_start = time.time()
    output = generator._export_image(
        print_ready, "Profile_Test", config.modus, config.dpi, True
    )
    timings['export'] = time.time() - t_start

    # Gesamt
    total = sum(timings.values())

    # Ausgabe
    print("ZEITMESSUNG:")
    print("-" * 80)

    for step, duration in sorted(timings.items(), key=lambda x: x[1], reverse=True):
        percent = (duration / total * 100) if total > 0 else 0
        bar = "#" * int(percent / 2)

        print("  {:<20} {:>8.3f}s  {:>5.1f}%  {}".format(
            step, duration, percent, bar
        ))

    print("-" * 80)
    print("  {:<20} {:>8.3f}s  100.0%".format("GESAMT", total))
    print("")

    # Analyse
    print("ANALYSE:")
    print("-" * 80)

    svg_percent = (timings['svg_to_image'] / total * 100) if total > 0 else 0

    if svg_percent > 80:
        print("  [!] SVG-Rendering dominiert ({:.1f}%)".format(svg_percent))
        print("      -> ImageMagick Rendering ist CPU-intensiv")
        print("      -> Lösungen:")
        print("         1. render_scale reduzieren (aktuell: 2)")
        print("         2. Multithreading nutzen (test_batch_svgs_mt.py)")
        print("         3. Caching für identische SVGs")

    if timings['text_overlay'] > 0.5:
        print("  [!] Text-Overlay langsam ({:.3f}s)".format(timings['text_overlay']))
        print("      -> Font-Loading optimieren")

    if timings['print_prep'] > 0.5:
        print("  [!] Druckvorbereitung langsam ({:.3f}s)".format(timings['print_prep']))

    print("")
    print("=" * 80)


if __name__ == "__main__":
    # Test mit erstem SVG aus Liste
    test_list = Path("test_svgs.txt")

    if test_list.exists():
        with open(test_list, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    svg_path = Path(line)
                    if svg_path.exists():
                        profile_single_zeichen(svg_path)
                        break
    else:
        # Fallback: Erstes SVG finden
        from constants import DEFAULT_ZEICHEN_DIR
        svgs = list(DEFAULT_ZEICHEN_DIR.rglob("*.svg"))
        if svgs:
            profile_single_zeichen(svgs[0])
        else:
            print("Keine SVG gefunden!")
