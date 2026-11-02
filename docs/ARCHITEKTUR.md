# Architektur

## Schichten

```
Svelte-Oberfläche (app/src)          Zustand: lib/store.svelte.ts, Typen: lib/types.ts
        │  invoke() / Events          (keine Fachlogik, keine Modus-Labels im Code)
Tauri-Kommandos (app/src-tauri)       Einstellungen, Dateidialoge, Threads, Fortschritt
        │
tz-core (crates/tz-core)              gesamte Fachlogik, ohne GUI, testbar
  ├── config.rs     DruckConfig = Werkseinstellungen + Validierung (ersetzt DEFAULT_* + RuntimeConfig)
  ├── modus.rs      7 Modi, Labels, Platzhalter (Single Source of Truth, ersetzt modus_config.py)
  ├── katalog.rs    Vorlagenordner rekursiv einlesen, Blanko-Vorlagen
  ├── grafik.rs     Vorlage -> usvg-Baum + sichtbarer Inhalt (Trimmen weißer/transparenter Ränder)
  ├── fonts.rs      Schriftdatenbank, Fallback-Kette, Textmessung mit rustybuzz
  ├── compose.rs    Layout S2/S1, Text-Modi, Umbruch, Auto-Verkleinerung -> Overlay-SVG
  ├── export/
  │   ├── pdf.rs    svg2pdf-Chunks als Form-XObjects, Seiten mit pdf-writer
  │   ├── raster.rs PNG-Export, Vorschau, Miniaturen (resvg)
  │   └── bogen.rs  A4-Raster für Schnittbögen (Hoch-/Querformat automatisch)
  └── job.rs        Export-Auftrag: parallel komponieren, Dateien schreiben, Bericht
```

## Datenfluss eines Zeichens

1. **Vorlage laden** (`grafik::lade`): SVG direkt mit usvg parsen. PNG/JPG wird in ein
   minimales SVG mit `<image>` verpackt. Pseudo-SVGs (PNG in SVG) funktionieren ohne
   Sonderfall. Ein Hilfsraster mit 1024 px ermittelt den sichtbaren Inhalt. Der Baum wird
   im `GrafikCache` (Pfad + Änderungszeit) gehalten.
2. **Komponieren** (`compose::compose`): Aus `DruckConfig` + `ZeichenSpec` (Vorlage, Modus,
   Text, Position) entstehen
   - die **Platzierung** der Grafik (Inhaltsbox -> Zielrechteck in mm) und
   - ein **Overlay-SVG** in Dateigröße (Text, Platzhalter-Linien, Schreiblinien, Schnittlinien).
3. **Ausgeben**:
   - PDF: Grafik und Overlay werden je einmal mit `svg2pdf::to_chunk` umgewandelt (parallel)
     und als XObject platziert. Die Grafik wird auf ihr Zielrechteck beschnitten, damit weiße
     Hintergrundflächen der Vorlage den Text nicht überdecken.
   - PNG/Vorschau: resvg rendert die Grafik in ein Teilbild (gleicher Zuschnitt) und das
     Overlay darüber.

Warum zwei Ebenen statt eines zusammengesetzten SVG? usvg verbietet Bilder in verschachtelten
SVG-Bildern. Vorlagen mit eingebetteten PNGs würden sonst leer bleiben. Außerdem lassen sich
die Grafiken so zwischen Kopien und Zeichen teilen.

## Layout-Regeln (aus v0.8.x übernommen)

- Bereiche: Datei (mit Beschnitt) ⊃ Schnitt (Endformat) ⊃ Inhalt (minus Sicherheitsabstand)
- Der Textblock reserviert **immer 2 Zeilen** am unteren Rand des Inhalts:
  `Ascender + Zeilenabstand + Descender + Abstand unten`
- Die Zeilen stehen linksbündig untereinander, der Block ist horizontal zentriert (an der längsten Zeile ausgerichtet)
- Einzeiliger Text steht in Zeile 2 (unten)
- Die Grafik sitzt oben und horizontal zentriert im Restbereich (`Höhe - Text - Abstand Grafik/Text`),
  höchstens `grafik_max_mm` groß (Zeichen-Wert vor `DruckConfig::grafik_max_mm`).
  Im Modus "Nur Grafik" nutzt sie den ganzen Inhalt, Position oben/mittig/unten
- Platzhalter: Stärke `     /      /      / ___` (Stellen konfigurierbar). Die Unterstriche sind
  echte Linien in Unterstrich-Position und -Stärke der Schrift
- Zu lange Texte werden ausgewogen auf 2 Zeilen umgebrochen (Trennung an Leerzeichen und
  Bindestrichen; gewählt wird die Trennstelle mit der schmalsten längeren Zeile) und in 0,5-pt-Schritten
  bis `min_schrift_pt` (mind. 8 pt) verkleinert. Passt es dann noch nicht: Hinweis `text_zu_lang`, Zeile im
  Auftrag rot, und – falls über dem Textblock Platz ist – `dritte_zeile_moeglich`. Mit `drei_zeilen` am
  Zeichen wird eine 3. Zeile oberhalb des Blocks gesetzt; die Grafik bleibt für 2 Zeilen eingepasst, und die
  Oberkante der 3. Zeile darf nicht über der Unterkante der platzierten Grafik liegen
- S1: links `links_prozent` % wie S2, rechts `anzahl_schreiblinien` Linien. Die oberste Linie ist
  optional die geometrische Stärke-Anzeige (3 Schrägstriche à 75° + Unterstrich 25 %)
- Schnittbogen: Zeichen in Endgröße, ohne Lücke, Raster zentriert, blaue Schnittkanten,
  optional grüne Inhaltslinien, Druckhinweis oben und unten

## Konventionen

- Rust: `cargo fmt` (rustfmt.toml), `cargo clippy -D warnings`, deutsche Fachbegriffe in Namen
  wie in der Python-Version (`zeichen`, `vorlage`, `beschnitt` …), Doku-Kommentare auf Deutsch
- Werkseinstellungen stehen **nur** in `DruckConfig::default()`. Neue Einstellung: Feld +
  Default + Prüfung in `pruefe()` + Eingabefeld im Einstellungsdialog
- Die Oberfläche hält keine Modus-Labels vor, sie kommen aus `Modus::info()` über `app_info`
- Systemkonstanten (Einheiten, Trim-Schwellen, Faktoren) liegen als `const` im jeweiligen Modul
- Tests: Unit-Tests je Modul, Ende-zu-Ende-Tests in `crates/tz-core/tests/export.rs`

## Bedienkonzept der Oberfläche

Zustand in `app/src/lib/store.svelte.ts`. Die Vorschau zeigt genau eine `Ansicht`:

- `vorlage`: Katalog-Vorlage mit Entwurfs-Parametern (Standard-Modus, Anzahl 1). „Hinzufügen“ legt
  einen Posten an; die Ansicht bleibt, damit dieselbe Vorlage erneut mit anderem Text folgen kann.
- `posten`: ein Auftragseintrag. Bearbeitet wird ein Entwurf; erst „Änderung speichern“ schreibt ihn
  zurück. „Als neu hinzufügen“ legt eine Kopie mit dem Entwurf an.
- `mehrfach`: ab zwei angehakten Posten („Checkbox gewinnt“). Je Feld `gemischt` (unterschiedliche
  Werte, grau) und `geaendert`; gespeichert werden nur geänderte Felder.

Jeder Wechsel läuft über `darfWechseln()` (Rückfrage Speichern/Verwerfen/Zurück). Der Auftrag wird über
`gruppiere()` als Kategorienbaum angezeigt; `postenSortiert` (Anzeige-Reihenfolge) ist auch die
Export-Reihenfolge und die Nummerierung in `Hinweise.txt`.

## Einstellungen und Sessions

- `settings.json` neben der EXE (Fallback: App-Konfigurationsordner, siehe `app/src-tauri/src/protokoll.rs`): `{ config, vorlagen_ordner, ausgabe_ordner,
  export_format, standard_modus }`. Fehlende Felder werden mit Werkseinstellungen gefüllt
  (`#[serde(default)]`). Alte Dateien bleiben dadurch lesbar
- Session-Datei (`*.tzdg.json`): `{ format: "tzdg-session", version: 1, config, posten[] }`
- Die Modus-Namen sind identisch zur Python-Version (`ov_staerke`, `ohne_text`, …)
