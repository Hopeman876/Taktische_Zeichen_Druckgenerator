#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_schneidelinien.py - Test ob Schneidelinien gezeichnet werden

Dieses Script testet isoliert, ob die Schneidelinien-Funktion funktioniert
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import logging

# Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_schneidelinien():
    """Testet Schneidelinien auf einem Test-Bild"""
    
    print("=" * 80)
    print("TEST: SCHNEIDELINIEN ZEICHNEN")
    print("=" * 80)
    
    # Test-Image erstellen (1200x1200px = ca. 51mm @ 600 DPI)
    size = 1200
    test_image = Image.new('RGB', (size, size), (255, 255, 255))
    
    # Blaues Quadrat in der Mitte zeichnen
    draw = ImageDraw.Draw(test_image)
    margin = 200
    draw.rectangle(
        [(margin, margin), (size - margin, size - margin)],
        fill=(0, 70, 127), 
        outline=(0, 0, 0),
        width=5
    )
    
    print(f"\nTest-Image erstellt: {size}x{size}px")
    
    # Jetzt Schneidelinien zeichnen
    print("\nZeichne Schneidelinien...")
    
    # Dimensionen (simuliert)
    beschnitt_px = 71  # 3mm @ 600 DPI
    sicherheit_px = 71  # 3mm @ 600 DPI
    line_width = 15
    
    # Font
    try:
        label_font = ImageFont.truetype("arial.ttf", 60)
        print("Arial Font geladen")
    except:
        label_font = ImageFont.load_default()
        print("Default Font verwendet")
    
    # 1. ROTE LINIE (äußerster Rand)
    print("Zeichne ROTE Linie (Beschnitt)...")
    draw.rectangle(
        [(line_width, line_width), 
         (size - line_width, size - line_width)],
        outline=(255, 0, 0),  # Knallrot
        width=line_width
    )
    draw.text((30, 30), "ROT: BESCHNITT", fill=(255, 0, 0), font=label_font)
    
    # 2. BLAUE LINIE (Schneidelinie)
    print("Zeichne BLAUE Linie (Schnitt)...")
    cut_offset = beschnitt_px
    draw.rectangle(
        [(cut_offset, cut_offset), 
         (size - cut_offset, size - cut_offset)],
        outline=(0, 0, 255),  # Blau
        width=line_width
    )
    draw.text((cut_offset + 30, cut_offset + 30), "BLAU: SCHNITT", fill=(0, 0, 255), font=label_font)
    
    # 3. GRÜNE LINIE (Sicherheit)
    print("Zeichne GRÜNE Linie (Sicherheit)...")
    safety_offset = beschnitt_px + sicherheit_px
    draw.rectangle(
        [(safety_offset, safety_offset),
         (size - safety_offset, size - safety_offset)],
        outline=(0, 255, 0),  # Grün
        width=line_width
    )
    draw.text(
        (safety_offset + 30, safety_offset + 30),
        "GRUEN: SICHERHEIT",
        fill=(0, 255, 0),
        font=label_font
    )
    
    # 4. GELBE LINIEN (zum Testen - kreuzweise durch die Mitte)
    print("Zeichne GELBE Test-Linien...")
    draw.line([(0, size//2), (size, size//2)], fill=(255, 255, 0), width=20)
    draw.line([(size//2, 0), (size//2, size)], fill=(255, 255, 0), width=20)
    
    # Speichern
    output_file = Path("test_schneidelinien_DEBUG.png")
    test_image.save(output_file, dpi=(600, 600))
    
    print(f"\n✓ Test-Image gespeichert: {output_file}")
    print(f"  Größe: {test_image.width}x{test_image.height}px")
    print("\nPRÜFE DAS BILD:")
    print("  - ROTE Linie ganz außen sichtbar?")
    print("  - BLAUE Linie innen sichtbar?")
    print("  - GRÜNE Linie noch weiter innen sichtbar?")
    print("  - GELBE Kreuz-Linien durch die Mitte sichtbar?")
    print("\nWenn KEINE Linien sichtbar sind, liegt ein Problem mit PIL vor!")
    print("=" * 80)


if __name__ == "__main__":
    test_schneidelinien()
