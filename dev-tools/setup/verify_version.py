#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_version.py - Prüft welche Version von poc_main_v2.py installiert ist
"""

from pathlib import Path
import re

def check_version():
    """Prüft Version der poc_main_v2.py"""
    
    poc_file = Path("poc_main_v2.py")
    
    if not poc_file.exists():
        print("[FEHLER] poc_main_v2.py nicht gefunden!")
        return
    
    content = poc_file.read_text(encoding='utf-8')
    
    print("=" * 80)
    print("VERSION CHECK - poc_main_v2.py")
    print("=" * 80)
    print()
    
    # Prüfe auf neue Features
    checks = {
        "run_comprehensive Funktion": "def run_comprehensive(" in content,
        "FIXED v2 Kommentar": "FIXED v2:" in content,
        "Sicherheitscheck Resize": "Sicherheitscheck - falls Größe nicht stimmt" in content,
        "target_width_pt_for_dpi": "target_width_pt_for_dpi" in content,
        "comprehensive Mode": 'sys.argv[1] == "comprehensive"' in content,
    }
    
    all_present = True
    for feature, present in checks.items():
        status = "[OK]" if present else "[FEHLT]"
        print(f"{status} {feature}")
        if not present:
            all_present = False
    
    print()
    print("=" * 80)
    
    if all_present:
        print("✅ ALLE FIXES VORHANDEN - Version ist aktuell (v2.7-fixed)")
        print()
        print("Du kannst jetzt starten:")
        print("  python poc_main_v2.py                    # Demo")
        print("  python poc_main_v2.py comprehensive      # Alle Zeichen")
    else:
        print("❌ ALTE VERSION INSTALLIERT - Bitte aktualisieren!")
        print()
        print("So aktualisierst du:")
        print("  1. Öffne das Artifact 'poc_main_v2.py (v2.7 - Fixed)'")
        print("  2. Kopiere den KOMPLETTEN Code")
        print("  3. Ersetze deine aktuelle poc_main_v2.py Datei")
        print("  4. Speichern und dieses Script nochmal ausführen")
    
    print("=" * 80)
    
    # Zeige ersten Teil der Datei
    print()
    print("Erste Zeilen der Datei:")
    print("-" * 80)
    lines = content.split('\n')[:15]
    for line in lines:
        print(line)

if __name__ == "__main__":
    check_version()
