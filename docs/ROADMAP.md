# Roadmap

Stand: erster Meilenstein (Kern, Export, App-Grundgerüst).

## Erledigt

- [x] Rendering-Kern in Rust: S2/S1, alle 7 Modi, Blanko-Varianten, Umbruch, Auto-Verkleinerung
- [x] Vorlagen: SVG, Pseudo-SVG (PNG in SVG), PNG, JPG, mit Trimmen weißer/transparenter Ränder
- [x] Vektor-PDF Einzelzeichen (TrimBox/BleedBox) und Schnittbogen (A4, Hoch-/Querformat automatisch)
- [x] PNG-Export mit DPI-Metadaten
- [x] Hinweise: Schrift-Fallback, Text verkleinert/zu lang, kein Platz für Grafik, Raster-DPI zu niedrig
- [x] CLI `tzdg` (Export per JSON-Auftrag, Vorschau, Katalog)
- [x] Desktop-App: Kategorien, Vorlagen mit Miniaturen, Auftrag, Live-Vorschau, Einstellungen,
      Export mit Fortschritt/Abbruch, Sessions
- [x] GitHub Actions: Tests, Clippy, Frontend-Check, Windows-Installer + portable EXE, Release per „Run workflow“
- [x] Bedienkonzept: Katalog -> Vorschau -> Hinzufügen; Auftrag nach Kategorien gruppiert mit
      Checkboxen und Mehrfachauswahl; „Änderung speichern“ mit Rückfrage bei ungespeicherten Änderungen
- [x] Einstellungen und Logs neben der EXE (Fallback `%APPDATA%`), Log-Datei mit 30 Tagen Aufbewahrung
- [x] Prüfung fehlender Schriften in Vorlagen (Vorschau, Vorab-Prüfung im Export-Dialog, Bericht)
- [x] Hinweis-Bericht `Hinweise.txt` im Ausgabeordner (u.a. zu lange Texte)
- [x] Max. Grafikgröße für alle Zeichen (Einstellungen) mit Abweichung pro Zeichen
- [x] Live-Vorschau im Einstellungsdialog, mm-Anzeige für Inhaltsbereich und S1-Aufteilung
- [x] Bereichsgrößen per Trennbalken veränderbar und gespeichert
- [x] Erste Tests mit echten Vorlagen (1363 Dateien): unzulässige Steuerzeichen werden beim Laden
      ignoriert, ausgewogener Umbruch + Verkleinerung bis Mindestgröße, leeres S2-Blankoschild,
      PNG-Kopien als einzelne Dateien, Suche im Auftrag, Zoom der Vorlagen, rote Markierung und
      Export-Sperre bei nicht lesbaren Vorlagen, Prüf-Kommando `tzdg pruefen`
- [x] Mindestschrift 8 pt, optionale 3. Textzeile pro Zeichen (nur ohne Kollision mit der Grafik)
- [x] Splash-Screen (bis App bereit, mind. 2,5 s), ?-Menü mit Einführungstour und „Über“
- [x] Edge-Kontextmenü abgeschaltet, Warnung bei leerem Vorlagenordner
- [x] Release per „Run workflow“ mit Versionseingabe: Tag und Release entstehen im Workflow (Entwurf → Dateien → veröffentlichen), Vorabversion bei Bindestrich
- [x] Knopf „Ausgabeordner“, Schriftgröße wächst mit der Zeichenhöhe (abschaltbar), max. 1000 mm,
      PNG-Hintergrund weiß/transparent, vollständige Lizenztexte im Paket, Windows-Build nur manuell
- [x] Alte Python-Version entfernt (liegt in der Git-Historie, letzter Stand: Commit `5499f7a`)

## Als Nächstes (für Funktionsgleichheit mit v0.8.x)

- [ ] **Praxistest mit den echten Vorlagen** (Inkscape/Illustrator-SVGs, CSS, Masken, Verläufe)
      und Abgleich mit Ausdrucken der Python-Version
- [ ] Zeitschätzung vor dem Export (bei Vektor meist unnötig, ggf. nur für PNG)
- [ ] Benutzerhandbuch für die neue Version (Menüpunkt im ?-Menü ist vorbereitet und ausgegraut)

## Druckvorstufe (CMYK / PDF/X)

- [ ] Klären: Reicht **PDF/X-4** (Transparenz erlaubt, ICC-basiert) oder muss es **PDF/X-1a** sein?
- [ ] Umsetzung per Ghostscript als optionaler Nachschritt (`-dPDFX`, ICC ISO Coated v2 300 %).
      Ghostscript ist AGPL: als externes Programm aufrufen, nicht linken
- [ ] Alternativ prüfen, ob `krilla` (Typst-Projekt) PDF/X direkt kann

## Später

- [ ] Excel/CSV-Import für Massenaufträge (`calamine`)
- [ ] Import alter Python-Sessions (vorerst nicht benötigt)
- [ ] Ablage des Installers in der Release-Struktur klären (nur bei Bedarf ausführen, z.B. wegen WebView2)
- [ ] Code-Signing: vorerst nicht (kostenpflichtig) – EXE/Installer bleiben unsigniert
- [ ] Auto-Update über das Tauri-Updater-Plugin
- [ ] Optional: Web-Version (tz-core nach WebAssembly, ohne CMYK)
