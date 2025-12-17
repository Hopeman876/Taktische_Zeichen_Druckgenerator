#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
find_pseudo_svgs.py - Findet alle Pseudo-SVGs (PNG-Wrapper)

Scannt alle SVGs und identifiziert solche, die nur eingebettete PNGs sind.
Bietet dann Batch-Extraktion an.

Verwendung:
  python find_pseudo_svgs.py
  python find_pseudo_svgs.py --extract  # Extrahiert alle PNGs
"""

from pathlib import Path
import re
import base64
import sys
import unicodedata


DEFAULT_ZEICHEN_DIR = Path(__file__).parent / "Taktische_Zeichen"


def is_pseudo_svg(svg_path: Path) -> dict:
    """
    Prüft ob SVG ein Pseudo-SVG ist (nur PNG-Wrapper)
    
    Args:
        svg_path: Pfad zur SVG
        
    Returns:
        Dict mit Analyse-Ergebnis
    """
    result = {
        "path": svg_path,
        "is_pseudo": False,
        "has_embedded_png": False,
        "has_vector_elements": False,
        "png_size_bytes": 0,
        "png_dimensions": None
    }
    
    try:
        content = svg_path.read_text(encoding='utf-8')
        
        # Suche nach eingebettetem PNG
        png_match = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', content)
        
        if png_match:
            result["has_embedded_png"] = True
            
            # Versuche PNG-Größe zu ermitteln
            try:
                base64_data = png_match.group(1)
                png_data = base64.b64decode(base64_data)
                result["png_size_bytes"] = len(png_data)
            except:
                pass
            
            # Versuche Dimensionen aus <image> Tag zu lesen
            dim_match = re.search(r'<image[^>]*width="(\d+)"[^>]*height="(\d+)"', content)
            if dim_match:
                result["png_dimensions"] = (int(dim_match.group(1)), int(dim_match.group(2)))
        
        # Prüfe auf echte Vektor-Elemente
        vector_elements = ['<path', '<circle', '<rect', '<polygon', '<polyline', '<line', '<ellipse']
        for element in vector_elements:
            if element in content:
                result["has_vector_elements"] = True
                break
        
        # Ist es ein Pseudo-SVG?
        # = Hat eingebettetes PNG ABER keine Vektor-Elemente
        if result["has_embedded_png"] and not result["has_vector_elements"]:
            result["is_pseudo"] = True
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def extract_png_from_pseudo_svg(svg_path: Path, output_dir: Path = None) -> Path:
    """
    Extrahiert PNG aus Pseudo-SVG
    
    Args:
        svg_path: SVG-Datei
        output_dir: Ausgabe-Verzeichnis (None = gleicher Ordner)
        
    Returns:
        Path zur PNG-Datei
    """
    if output_dir is None:
        output_dir = svg_path.parent
    
    # Normalisiere Dateinamen (entferne Umlaute)
    stem = svg_path.stem
    stem = stem.replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe')
    stem = stem.replace('Ü', 'Ue').replace('Ä', 'Ae').replace('Ö', 'Oe')
    stem = stem.replace('ß', 'ss')
    
    # Normalisiere auch Unicode (NFD -> NFC)
    stem = unicodedata.normalize('NFC', stem)
    
    output_path = output_dir / (stem + ".png")
    
    # Lese und dekodiere
    content = svg_path.read_text(encoding='utf-8')
    match = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', content)
    
    if not match:
        raise ValueError("Kein PNG gefunden")
    
    base64_data = match.group(1)
    png_data = base64.b64decode(base64_data)
    
    # Speichere
    output_path.write_bytes(png_data)
    
    return output_path


def scan_directory(zeichen_dir: Path = DEFAULT_ZEICHEN_DIR):
    """
    Scannt Verzeichnis nach Pseudo-SVGs
    
    Args:
        zeichen_dir: Zeichen-Verzeichnis
    """
    print("=" * 80)
    print("PSEUDO-SVG SCANNER")
    print("=" * 80)
    print("\nScanne: {}".format(zeichen_dir))
    print("Suche nach SVGs, die nur PNG-Wrapper sind...\n")
    
    pseudo_svgs = []
    real_svgs = []
    mixed_svgs = []
    error_svgs = []
    
    # Scanne alle SVGs
    all_svgs = list(zeichen_dir.rglob("*.svg"))
    
    print("Gefunden: {} SVG-Dateien".format(len(all_svgs)))
    print("Analysiere...\n")
    
    for svg_path in all_svgs:
        result = is_pseudo_svg(svg_path)
        
        if "error" in result:
            error_svgs.append((svg_path, result))
        elif result["is_pseudo"]:
            pseudo_svgs.append((svg_path, result))
        elif result["has_embedded_png"] and result["has_vector_elements"]:
            mixed_svgs.append((svg_path, result))
        else:
            real_svgs.append((svg_path, result))
    
    # Ausgabe
    print("=" * 80)
    print("ERGEBNISSE")
    print("=" * 80)
    
    print("\n[PSEUDO-SVGs] {} Dateien (nur PNG-Wrapper)".format(len(pseudo_svgs)))
    if pseudo_svgs:
        print("-" * 80)
        for svg_path, result in pseudo_svgs[:10]:  # Zeige erste 10
            dims = result.get("png_dimensions", (0, 0))
            size_kb = result.get("png_size_bytes", 0) / 1024
            category = svg_path.parent.name
            print("  {} ({})".format(svg_path.name, category))
            print("    PNG: {}x{}px, {:.1f} KB".format(dims[0], dims[1], size_kb))
        
        if len(pseudo_svgs) > 10:
            print("  ... und {} weitere".format(len(pseudo_svgs) - 10))
    
    print("\n[ECHTE SVGs] {} Dateien (Vektor-Grafiken)".format(len(real_svgs)))
    
    print("\n[MIXED SVGs] {} Dateien (PNG + Vektor)".format(len(mixed_svgs)))
    if mixed_svgs:
        print("-" * 80)
        for svg_path, result in mixed_svgs[:5]:
            print("  {} ({})".format(svg_path.name, svg_path.parent.name))
        
        if len(mixed_svgs) > 5:
            print("  ... und {} weitere".format(len(mixed_svgs) - 5))
    
    if error_svgs:
        print("\n[FEHLER] {} Dateien konnten nicht analysiert werden".format(len(error_svgs)))
    
    print("\n" + "=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print("Gesamt:       {} SVGs".format(len(all_svgs)))
    print("Pseudo-SVGs:  {} ({:.1f}%)".format(
        len(pseudo_svgs), 
        len(pseudo_svgs) / len(all_svgs) * 100 if all_svgs else 0
    ))
    print("Echte SVGs:   {} ({:.1f}%)".format(
        len(real_svgs),
        len(real_svgs) / len(all_svgs) * 100 if all_svgs else 0
    ))
    print("Mixed SVGs:   {} ({:.1f}%)".format(
        len(mixed_svgs),
        len(mixed_svgs) / len(all_svgs) * 100 if all_svgs else 0
    ))
    
    return pseudo_svgs, real_svgs, mixed_svgs, error_svgs


def extract_all_pseudo_svgs(pseudo_svgs: list):
    """
    Extrahiert alle Pseudo-SVGs zu PNGs
    
    Args:
        pseudo_svgs: Liste von (path, result) Tupeln
    """
    print("\n" + "=" * 80)
    print("BATCH-EXTRAKTION")
    print("=" * 80)
    print("\nExtrahiere {} Pseudo-SVGs zu PNGs...\n".format(len(pseudo_svgs)))
    
    try:
        response = input("Fortfahren? (j/n): ").lower()
        if response not in ['j', 'ja', 'y', 'yes']:
            print("\n[ABGEBROCHEN]")
            return
    except KeyboardInterrupt:
        print("\n\n[ABGEBROCHEN]")
        return
    
    success = 0
    failed = 0
    
    for i, (svg_path, result) in enumerate(pseudo_svgs, 1):
        try:
            png_path = extract_png_from_pseudo_svg(svg_path)
            print("[{}/{}] OK: {} -> {}".format(
                i, len(pseudo_svgs), svg_path.name, png_path.name
            ))
            success += 1
        except Exception as e:
            print("[{}/{}] FEHLER: {} - {}".format(
                i, len(pseudo_svgs), svg_path.name, str(e)
            ))
            failed += 1
    
    print("\n" + "=" * 80)
    print("EXTRAKTION ABGESCHLOSSEN")
    print("=" * 80)
    print("Erfolgreich: {}".format(success))
    print("Fehlgeschlagen: {}".format(failed))
    print("\n[INFO] Die PNG-Dateien wurden neben den SVGs gespeichert.")
    print("[INFO] Sie haben keine Umlaute mehr im Dateinamen!")


if __name__ == "__main__":
    extract_mode = "--extract" in sys.argv
    
    # Scanne
    pseudo_svgs, real_svgs, mixed_svgs, error_svgs = scan_directory()
    
    # Extrahiere wenn gewünscht
    if extract_mode and pseudo_svgs:
        extract_all_pseudo_svgs(pseudo_svgs)
    elif pseudo_svgs and not extract_mode:
        print("\n[INFO] Um alle PNGs zu extrahieren:")
        print("       python find_pseudo_svgs.py --extract")
