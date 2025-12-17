#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
markdown_to_pdf.py - Konvertiert Markdown-Dateien zu PDF für Releases

Verwendet: markdown + weasyprint
Installieren: pip install markdown weasyprint
"""

import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


def convert_markdown_to_pdf(md_file: Path, output_pdf: Path) -> bool:
    """
    Konvertiert eine Markdown-Datei zu PDF.

    Args:
        md_file: Pfad zur .md Datei
        output_pdf: Pfad zur Ausgabe-PDF

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    try:
        # Markdown lesen
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Markdown zu HTML konvertieren
        html_content = markdown.markdown(
            md_content,
            extensions=['extra', 'codehilite', 'tables', 'toc']
        )

        # HTML mit CSS für besseres Layout
        html_with_style = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 40px auto;
                    padding: 0 20px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    margin-top: 24px;
                    margin-bottom: 16px;
                    font-weight: bold;
                }}
                h1 {{ font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
                h3 {{ font-size: 1.25em; }}
                code {{
                    background-color: #f6f8fa;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
                pre {{
                    background-color: #f6f8fa;
                    padding: 16px;
                    border-radius: 6px;
                    overflow-x: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 16px 0;
                }}
                table th, table td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                table th {{
                    background-color: #f6f8fa;
                    font-weight: bold;
                }}
                ul, ol {{
                    padding-left: 30px;
                }}
                blockquote {{
                    border-left: 4px solid #ddd;
                    padding-left: 16px;
                    color: #666;
                    margin-left: 0;
                }}
                a {{
                    color: #0366d6;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Font-Konfiguration für bessere Schriftarten
        font_config = FontConfiguration()

        # HTML zu PDF konvertieren
        HTML(string=html_with_style).write_pdf(
            output_pdf,
            font_config=font_config
        )

        print(f"✓ Konvertiert: {md_file.name} -> {output_pdf.name}")
        return True

    except Exception as e:
        print(f"✗ Fehler bei {md_file.name}: {e}")
        return False


def main():
    """Konvertiert alle übergebenen Markdown-Dateien zu PDF"""
    if len(sys.argv) < 2:
        print("Usage: python markdown_to_pdf.py <file1.md> <file2.md> ...")
        print("Konvertiert Markdown-Dateien zu PDF (gleiches Verzeichnis)")
        return 1

    success_count = 0
    total_count = 0

    for md_path_str in sys.argv[1:]:
        md_path = Path(md_path_str)

        if not md_path.exists():
            print(f"✗ Datei nicht gefunden: {md_path}")
            continue

        if not md_path.suffix.lower() == '.md':
            print(f"✗ Keine Markdown-Datei: {md_path}")
            continue

        # PDF im gleichen Verzeichnis erstellen
        pdf_path = md_path.with_suffix('.pdf')

        total_count += 1
        if convert_markdown_to_pdf(md_path, pdf_path):
            success_count += 1

    print(f"\n{success_count}/{total_count} Dateien erfolgreich konvertiert")
    return 0 if success_count == total_count else 1


if __name__ == '__main__':
    sys.exit(main())
