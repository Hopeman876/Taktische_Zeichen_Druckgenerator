# Third-Party Licenses

Der Taktische Zeichen Druckgenerator steht unter der GPL-3.0-or-later (siehe `LICENSE`).
Die wichtigsten verwendeten Open-Source-Komponenten:

| Komponente | Lizenz | Verwendung |
|------------|--------|------------|
| Tauri 2 (+ plugin-dialog, plugin-opener) | Apache-2.0 OR MIT | Desktop-Hülle |
| svg2pdf, pdf-writer (Typst-Projekt) | MIT OR Apache-2.0 | Vektor-PDF-Erzeugung |
| usvg, resvg, tiny-skia | Apache-2.0 OR MIT / BSD-3-Clause | SVG-Verarbeitung, Rendering |
| fontdb, rustybuzz, ttf-parser | MIT | Schriften, Textmessung |
| image, png | MIT OR Apache-2.0 | Rasterbilder |
| serde, serde_json, rayon, chrono, thiserror, base64 | MIT OR Apache-2.0 | Infrastruktur |
| Svelte 5 | MIT | Oberfläche |
| @tauri-apps/api, @tauri-apps/plugin-dialog | Apache-2.0 OR MIT | Oberfläche ↔ Backend |
| Microsoft Edge WebView2 (Windows, Systemkomponente) | Microsoft-Lizenz | Anzeige der Oberfläche |

Alle Lizenzen sind mit der GPL-3.0 vereinbar (geprüft: MIT, Apache-2.0, BSD-2/3-Clause, Zlib,
Unicode-3.0, MPL-2.0, Unlicense, CC0-1.0, BSL-1.0, 0BSD).

Die **vollständigen Lizenztexte** aller in der Anwendung enthaltenen Komponenten werden bei jedem
Build von `app/scripts/lizenzen.mjs` erzeugt (`LIZENZEN-DRITTANBIETER.txt`) und liegen dem Installer
sowie der portablen ZIP bei. Die vollständige Liste aller (auch indirekten)
Rust-Abhängigkeiten liefert `cargo tree`, die der Oberfläche `npm ls --all` in `app/`.
Schriften werden nicht mitgeliefert. Die App nutzt installierte Systemschriften bzw. den Ordner
`fonts/` neben der EXE, deren Lizenzen beim jeweiligen Anbieter liegen.
