#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
svg_analyzer.py - SVG Analyse & Reparatur Tool

Analysiert problematische SVG-Dateien und versucht sie zu reparieren.

Häufige Probleme:
1. Ungültige/fehlende XML-Deklaration
2. Encoding-Probleme (Umlaute im Dateinamen oder Inhalt)
3. Eingebettete Bilder mit falschen Pfaden
4. Unsupported SVG-Version
5. Korrupte/fehlerhafte SVG-Struktur
6. Policy-Einschränkungen (MVG/MSVG)

Version: 1.0
"""

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List
import re
import logging
import unicodedata


class SVGAnalyzer:
    """
    Analysiert SVG-Dateien auf potenzielle Probleme
    """
    
    def __init__(self):
        """Initialisiert Analyzer"""
        self.logger = logging.getLogger(__name__)
    
    def analyze_svg(self, svg_path: Path) -> Dict:
        """
        Analysiert SVG-Datei auf Probleme
        
        Args:
            svg_path: Pfad zur SVG-Datei
            
        Returns:
            Dict mit Analyse-Ergebnissen
        """
        result = {
            "path": svg_path,
            "filename": svg_path.name,
            "exists": svg_path.exists(),
            "problems": [],
            "warnings": [],
            "info": {},
            "can_be_fixed": False,
            "is_valid": True
        }
        
        if not svg_path.exists():
            result["problems"].append("Datei existiert nicht")
            result["is_valid"] = False
            return result
        
        # 1. Dateinamen-Analyse (Umlaute, Sonderzeichen)
        self._check_filename(svg_path, result)
        
        # 2. Datei-Größe prüfen
        self._check_filesize(svg_path, result)
        
        # 3. Encoding prüfen
        self._check_encoding(svg_path, result)
        
        # 4. XML-Struktur prüfen
        self._check_xml_structure(svg_path, result)
        
        # 5. SVG-spezifische Prüfungen
        self._check_svg_specifics(svg_path, result)
        
        # 6. Eingebettete Bilder prüfen
        self._check_embedded_images(svg_path, result)
        
        # Zusammenfassung
        if result["problems"]:
            result["is_valid"] = False
        
        # FIXED: XML-Parse-Fehler können auch repariert werden!
        if any("Encoding" in p or "Umlaut" in p or "XML-Deklaration" in p or "XML-Parse" in p
               for p in result["problems"]):
            result["can_be_fixed"] = True
        
        return result
    
    def _check_filename(self, svg_path: Path, result: Dict) -> None:
        """Prüft Dateinamen auf problematische Zeichen"""
        filename = svg_path.name
        
        # Umlaute im Dateinamen
        if any(c in filename for c in ['ä', 'ö', 'ü', 'Ä', 'Ö', 'Ü', 'ß']):
            result["warnings"].append(
                "Dateiname enthält Umlaute: {}".format(filename)
            )
            result["info"]["has_umlauts_in_filename"] = True
        
        # Sonderzeichen (außer Bindestrich, Unterstrich, Punkt)
        special_chars = re.findall(r'[^a-zA-Z0-9._-]', filename.replace('.svg', ''))
        if special_chars:
            result["warnings"].append(
                "Dateiname enthält Sonderzeichen: {}".format(set(special_chars))
            )
            result["info"]["special_chars_in_filename"] = list(set(special_chars))
    
    def _check_filesize(self, svg_path: Path, result: Dict) -> None:
        """Prüft Dateigröße"""
        size_bytes = svg_path.stat().st_size
        result["info"]["size_bytes"] = size_bytes
        
        if size_bytes == 0:
            result["problems"].append("Datei ist leer (0 Bytes)")
        elif size_bytes < 100:
            result["warnings"].append(
                "Datei sehr klein ({}B) - möglicherweise unvollständig".format(size_bytes)
            )
        elif size_bytes > 10 * 1024 * 1024:  # > 10MB
            result["warnings"].append(
                "Datei sehr groß ({:.1f}MB)".format(size_bytes / (1024 * 1024))
            )
    
    def _check_encoding(self, svg_path: Path, result: Dict) -> None:
        """Prüft Encoding der Datei"""
        try:
            # Versuche UTF-8
            content = svg_path.read_text(encoding='utf-8')
            result["info"]["encoding"] = "utf-8"
            result["info"]["content_length"] = len(content)
            
        except UnicodeDecodeError:
            result["problems"].append("Encoding-Problem: Nicht UTF-8")
            result["can_be_fixed"] = True
            
            # Versuche andere Encodings
            for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content = svg_path.read_text(encoding=enc)
                    result["info"]["encoding"] = enc
                    result["warnings"].append(
                        "Falsches Encoding: {} statt UTF-8".format(enc)
                    )
                    break
                except UnicodeDecodeError:
                    continue
            else:
                result["problems"].append("Encoding konnte nicht ermittelt werden")
                return
        
        # XML-Deklaration prüfen
        first_line = content.split('\n')[0].strip()
        if not first_line.startswith('<?xml'):
            result["warnings"].append("Fehlende XML-Deklaration")
            result["can_be_fixed"] = True
        else:
            result["info"]["xml_declaration"] = first_line
            
            # Encoding in XML-Deklaration prüfen
            if 'encoding=' in first_line:
                enc_match = re.search(r'encoding=["\']([^"\']+)["\']', first_line)
                if enc_match:
                    declared_enc = enc_match.group(1).lower()
                    result["info"]["declared_encoding"] = declared_enc
                    
                    if declared_enc != 'utf-8':
                        result["warnings"].append(
                            "Deklariertes Encoding ist {} statt UTF-8".format(declared_enc)
                        )
    
    def _check_xml_structure(self, svg_path: Path, result: Dict) -> None:
        """Prüft XML-Struktur"""
        try:
            content = svg_path.read_text(encoding=result["info"].get("encoding", "utf-8"))
            
            # Versuche XML zu parsen
            try:
                tree = ET.fromstring(content)
                result["info"]["xml_valid"] = True
                result["info"]["root_tag"] = tree.tag
                
            except ET.ParseError as e:
                result["problems"].append("XML-Parse-Fehler: {}".format(str(e)))
                result["info"]["xml_valid"] = False
                
        except Exception as e:
            result["problems"].append("Fehler beim Lesen: {}".format(str(e)))
    
    def _check_svg_specifics(self, svg_path: Path, result: Dict) -> None:
        """Prüft SVG-spezifische Eigenschaften"""
        try:
            content = svg_path.read_text(encoding=result["info"].get("encoding", "utf-8"))
            
            # SVG-Version prüfen
            version_match = re.search(r'<svg[^>]*version=["\']([^"\']+)["\']', content)
            if version_match:
                version = version_match.group(1)
                result["info"]["svg_version"] = version
                
                # Warnung bei alten Versionen
                if version not in ['1.1', '2.0', '1.2']:
                    result["warnings"].append(
                        "Ungewöhnliche SVG-Version: {}".format(version)
                    )
            else:
                result["warnings"].append("Keine SVG-Version gefunden")
            
            # Namespace prüfen
            if 'xmlns="http://www.w3.org/2000/svg"' in content:
                result["info"]["has_svg_namespace"] = True
            else:
                result["warnings"].append("Fehlender SVG-Namespace")
            
            # Viewbox prüfen
            if 'viewBox=' in content:
                viewbox_match = re.search(r'viewBox=["\']([^"\']+)["\']', content)
                if viewbox_match:
                    result["info"]["viewBox"] = viewbox_match.group(1)
            
            # Width/Height prüfen
            width_match = re.search(r'width=["\']([^"\']+)["\']', content)
            height_match = re.search(r'height=["\']([^"\']+)["\']', content)
            
            if width_match:
                result["info"]["width"] = width_match.group(1)
            if height_match:
                result["info"]["height"] = height_match.group(1)
                
        except Exception as e:
            result["warnings"].append("Fehler bei SVG-Analyse: {}".format(str(e)))
    
    def _check_embedded_images(self, svg_path: Path, result: Dict) -> None:
        """Prüft eingebettete Bilder"""
        try:
            content = svg_path.read_text(encoding=result["info"].get("encoding", "utf-8"))
            
            # xlink:href Bilder (externe Referenzen)
            href_matches = re.findall(r'xlink:href=["\']([^"\']+)["\']', content)
            if href_matches:
                result["info"]["embedded_images"] = href_matches
                
                # Prüfe ob externe Dateien (nicht base64)
                external_images = [h for h in href_matches if not h.startswith('data:')]
                if external_images:
                    result["warnings"].append(
                        "SVG referenziert externe Bilder: {}".format(len(external_images))
                    )
                    result["info"]["external_images"] = external_images
                    
        except Exception as e:
            result["warnings"].append(
                "Fehler bei Embedded-Image-Analyse: {}".format(str(e))
            )
    
    def repair_svg(self, svg_path: Path, output_path: Optional[Path] = None) -> bool:
        """
        Versucht SVG zu reparieren
        
        Args:
            svg_path: Pfad zur SVG-Datei
            output_path: Ausgabe-Pfad (None = überschreiben)
            
        Returns:
            True bei Erfolg
        """
        if output_path is None:
            output_path = svg_path.parent / (svg_path.stem + "_repaired.svg")
        
        try:
            # Lese Inhalt mit verschiedenen Encodings
            content = None
            used_encoding = None
            
            for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content = svg_path.read_text(encoding=enc)
                    used_encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                self.logger.error("Konnte Datei nicht lesen")
                return False
            
            # 1. XML-Deklaration hinzufügen falls fehlend
            if not content.strip().startswith('<?xml'):
                content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
                self.logger.info("XML-Deklaration hinzugefügt")
            
            # 2. Encoding in XML-Deklaration korrigieren
            content = re.sub(
                r'encoding=["\'][^"\']*["\']',
                'encoding="UTF-8"',
                content,
                count=1
            )
            
            # NEW: 3. Entferne problematische Zeichen aus Metadaten
            # Das Problem ist in Zeile 4 - wahrscheinlich in den XMP-Metadaten
            # Wir behalten nur den SVG-Teil
            try:
                # Finde SVG-Start
                svg_start = content.find('<svg')
                if svg_start > 0:
                    # Behalte alles ab <svg
                    content_before = content[:svg_start]
                    content_after = content[svg_start:]
                    
                    # Behalte nur XML-Deklaration
                    xml_decl = '<?xml version="1.0" encoding="UTF-8"?>\n'
                    content = xml_decl + content_after
                    
                    self.logger.info("XMP-Metadaten entfernt (wahrscheinlich korrupt)")
            except Exception as e:
                self.logger.warning("Konnte Metadaten nicht entfernen: {}".format(e))
            
            # 4. Speichere als UTF-8
            output_path.write_text(content, encoding='utf-8')
            
            self.logger.info("Reparierte SVG: {}".format(output_path))
            return True
            
        except Exception as e:
            self.logger.error("Fehler bei Reparatur: {}".format(e))
            return False


def analyze_problematic_svgs(svg_dir: Path, problem_names: List[str]) -> None:
    """
    Analysiert spezifische problematische SVGs
    
    Args:
        svg_dir: Zeichen-Verzeichnis
        problem_names: Liste von Dateinamen
    """
    print("=" * 80)
    print("SVG ANALYZER - PROBLEMATISCHE DATEIEN")
    print("=" * 80)
    
    analyzer = SVGAnalyzer()
    
    for problem_name in problem_names:
        print("\n" + "-" * 80)
        print("DATEI: {}".format(problem_name))
        print("-" * 80)
        
        # FIXED: Normalisiere Dateinamen (NFD und NFC)
        # NFD = decomposed (ü = u + ¨)
        # NFC = composed (ü = ü)
        problem_name_nfc = unicodedata.normalize('NFC', problem_name)
        problem_name_nfd = unicodedata.normalize('NFD', problem_name)
        
        # Suche mit beiden Normalisierungen
        svg_files = []
        for svg_path in svg_dir.rglob("*.svg"):
            # Normalisiere auch gefundene Dateinamen
            svg_name_nfc = unicodedata.normalize('NFC', svg_path.name)
            svg_name_nfd = unicodedata.normalize('NFD', svg_path.name)
            
            # Vergleiche beide Varianten
            if (svg_name_nfc == problem_name_nfc or 
                svg_name_nfd == problem_name_nfd or
                svg_name_nfc == problem_name_nfd or
                svg_name_nfd == problem_name_nfc):
                svg_files.append(svg_path)
                break
        
        if not svg_files:
            print("[FEHLER] Datei nicht gefunden: {}".format(problem_name))
            print("  Gesucht (NFC): {}".format(problem_name_nfc.encode('utf-8')))
            print("  Gesucht (NFD): {}".format(problem_name_nfd.encode('utf-8')))
            continue
        
        svg_path = svg_files[0]
        print("Pfad: {}".format(svg_path))
        print("Gefunden als: {}".format(svg_path.name.encode('utf-8')))
        
        # Analysiere
        result = analyzer.analyze_svg(svg_path)
        
        # Ausgabe
        print("\n[STATUS] {}".format(
            "GÜLTIG" if result["is_valid"] else "FEHLERHAFT"
        ))
        
        if result["info"]:
            print("\n[INFO]")
            for key, value in result["info"].items():
                print("  {}: {}".format(key, value))
        
        if result["warnings"]:
            print("\n[WARNUNGEN]")
            for warning in result["warnings"]:
                print("  - {}".format(warning))
        
        if result["problems"]:
            print("\n[PROBLEME]")
            for problem in result["problems"]:
                print("  - {}".format(problem))
        
        # Reparatur anbieten
        if result["can_be_fixed"]:
            print("\n[LÖSUNG] Diese Datei kann repariert werden!")
            try:
                response = input("Reparieren? (j/n): ").lower()
                if response in ['j', 'ja', 'y', 'yes']:
                    if analyzer.repair_svg(svg_path):
                        print("[OK] Repariert: {}_repaired.svg".format(svg_path.stem))
                    else:
                        print("[FEHLER] Reparatur fehlgeschlagen")
            except KeyboardInterrupt:
                print("\n[ABGEBROCHEN]")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    # Standard: Taktische_Zeichen Ordner
    zeichen_dir = Path(__file__).parent / "Taktische_Zeichen"
    
    if not zeichen_dir.exists():
        print("[FEHLER] Zeichen-Ordner nicht gefunden: {}".format(zeichen_dir))
        print("Aktuelles Verzeichnis: {}".format(Path.cwd()))
        print("\nVERSUCHE: python svg_analyzer.py [PFAD_ZUM_ZEICHEN_ORDNER]")
        sys.exit(1)
    
    # Zeichen-Ordner aus Kommandozeile übernehmen (optional)
    if len(sys.argv) > 1:
        zeichen_dir = Path(sys.argv[1])
        if not zeichen_dir.exists():
            print("[FEHLER] Angegebener Pfad existiert nicht: {}".format(zeichen_dir))
            sys.exit(1)
    
    print("\n[INFO] Zeichen-Ordner: {}".format(zeichen_dir))
    print("[INFO] Suche problematische Dateien rekursiv...")
    
    # DEBUG: Zeige alle SVGs im Personen_THW_invertiert Ordner
    personen_dir = zeichen_dir / "Personen_THW_invertiert"
    if personen_dir.exists():
        print("\n[DEBUG] Alle SVGs in Personen_THW_invertiert:")
        all_svgs = sorted(personen_dir.glob("*.svg"))
        for svg in all_svgs[:20]:  # Zeige erste 20
            print("  - {}".format(svg.name))
        if len(all_svgs) > 20:
            print("  ... und {} weitere".format(len(all_svgs) - 20))
        
        # Suche speziell nach ETB*
        etb_files = sorted(personen_dir.glob("ETB*.svg"))
        if etb_files:
            print("\n[DEBUG] ETB-Dateien gefunden:")
            for etb in etb_files:
                print("  - {}".format(etb.name))
                # Zeige Encoding des Dateinamens
                try:
                    print("    Bytes: {}".format(etb.name.encode('utf-8')))
                except:
                    print("    Encoding-Problem!")
    else:
        print("\n[WARNUNG] Personen_THW_invertiert Ordner nicht gefunden!")
    
    # Problematische Dateien aus deinem Test
    problematic_files = [
        "ETB-Fü.svg",
        "ETB-Fu.svg",  # Alternative ohne Umlaut
        # Weitere problematische Dateien hier hinzufügen
    ]
    
    # Prüfe ob Dateien existieren (mit Unicode-Normalisierung!)
    print("\n[SUCHE PROBLEMATISCHE DATEIEN]")
    found_files = []
    for fname in problematic_files:
        # FIXED: Normalisiere Suchstring
        fname_nfc = unicodedata.normalize('NFC', fname)
        fname_nfd = unicodedata.normalize('NFD', fname)
        
        # Suche mit Normalisierung
        found = False
        for svg_path in zeichen_dir.rglob("*.svg"):
            svg_name_nfc = unicodedata.normalize('NFC', svg_path.name)
            svg_name_nfd = unicodedata.normalize('NFD', svg_path.name)
            
            if (svg_name_nfc == fname_nfc or 
                svg_name_nfd == fname_nfd or
                svg_name_nfc == fname_nfd or
                svg_name_nfd == fname_nfc):
                print("  [OK] {} gefunden: {}".format(fname, svg_path.parent.name))
                found_files.append(fname)
                found = True
                break
        
        if not found:
            print("  [X] {} NICHT gefunden".format(fname))
    
    print("")
    
    if found_files:
        analyze_problematic_svgs(zeichen_dir, found_files)
    else:
        print("[INFO] Keine der angegebenen Dateien gefunden.")
        print("[INFO] Siehe DEBUG-Ausgabe oben für verfügbare ETB-Dateien.")
