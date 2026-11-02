# Entwicklung – Taktische Zeichen Druckgenerator

Technische Informationen für Mitwirkende. Die Beschreibung für Anwender steht in der [README](README.md).

Version 0.9 / 2.0 ist eine Neuentwicklung in **Rust + Tauri**. Die frühere Python-Version (bis v0.8.x)
liegt weiterhin in der Git-Historie (letzter Stand: Commit `5499f7a`).

## Kernidee: alles bleibt Vektor

Die Vorlage (SVG, Pseudo-SVG oder PNG/JPG) und die Beschriftung werden als getrennte Ebenen direkt
ins PDF geschrieben. Rasterbilder entstehen nur beim PNG-Export und für die Vorschau. Daraus folgt:

- Text, Linien und SVG-Grafiken sind im PDF gestochen scharf. Wahlweise wird der Text in Pfade
  umgewandelt (Standard) oder die Schrift eingebettet.
- Kopien kosten fast nichts: Jede Grafik und jedes Overlay wird einmal eingebettet und beliebig oft
  platziert.
- Ein Export mit 8 Zeichen dauert ca. 0,2 s. ImageMagick, Multiprocessing und Template-Caching der
  Python-Version sind nicht mehr nötig.
- PDF-Einzelzeichen haben eine TrimBox (Endformat) und eine BleedBox (mit Beschnitt), so wie
  Druckereien es erwarten.

## Aufbau

```
.
├── crates/
│   ├── tz-core/      Rendering-Kern (reines Rust, ohne GUI, vollständig getestet)
│   └── tz-cli/       Kommandozeile `tzdg` (Tests, Automatisierung, Batch)
├── app/
│   ├── src/          Oberfläche (Svelte 5 + TypeScript)
│   ├── src-tauri/    Desktop-Hülle (Tauri 2), dünne Schicht über tz-core
│   └── scripts/      Build-Hilfen (z.B. Lizenztexte erzeugen)
└── docs/             Architektur, Roadmap, Bilder für die README
```

Details: [docs/ARCHITEKTUR.md](docs/ARCHITEKTUR.md) · offene Punkte: [docs/ROADMAP.md](docs/ROADMAP.md) ·
Hinweise für KI-Assistenten: [CLAUDE.md](CLAUDE.md)

## Entwickeln

Voraussetzungen: Rust (stable), Node.js 22. Unter Linux zusätzlich die WebKitGTK-Pakete
(`libwebkit2gtk-4.1-dev`, `librsvg2-dev`).

```bash
cargo test                      # Kern + CLI testen (ohne GUI-Abhängigkeiten)

cd app
npm install
npx tauri dev                   # App mit Hot-Reload starten
npx tauri build                 # Release-Build (Windows: NSIS-Installer)
```

Vor jedem Commit müssen grün sein: `cargo fmt --all --check`,
`cargo clippy -p tz-core -p tz-cli --all-targets -- -D warnings`, `cargo test` und in `app/`
`npm run check`.

## Kommandozeile `tzdg`

```bash
cargo run -p tz-cli -- config                    # Werkseinstellungen als JSON
cargo run -p tz-cli -- scan <vorlagenordner>     # Katalog als JSON
cargo run -p tz-cli -- pruefen <vorlagenordner>  # alle Vorlagen laden: Lesefehler, fehlende Schriften
cargo run -p tz-cli -- export auftrag.json       # Export laut Auftrag
cargo run -p tz-cli -- vorschau zeichen.json vorschau.png 800
```

Beispiel `auftrag.json`:

```json
{
  "format": "pdf_bogen",
  "ziel_ordner": "C:/Ausgabe",
  "config": { "layout": "s2", "s2": { "hoehe_mm": 47.5, "breite_mm": 45 } },
  "posten": [
    { "vorlage": { "art": "datei", "pfad": "C:/Vorlagen/THW_Fahrzeuge/MzKW.svg" },
      "modus": "ov_staerke", "text": "Musterstadt", "kopien": 4 },
    { "vorlage": { "art": "blanko", "blanko": "leer" }, "modus": "freitext" }
  ]
}
```

## Build und Release per GitHub Actions

Der Workflow `.github/workflows/build.yml` prüft bei jedem Push und Pull Request (Tests, Clippy,
Oberfläche; bei PRs aus diesem Repository nicht doppelt). Der Windows-Build (Installer + portable
EXE) läuft nur manuell über **Actions → „Test, Build und Release“ → „Run workflow“**.

**Nur bauen:** Feld „version“ leer lassen. ZIP-Inhalt und Installer liegen danach als Artefakte am
Workflow-Lauf.

**Release:** Branch (normalerweise `main`) wählen, im Feld „version“ die Version ohne `v` eintragen,
z.B. `2.0.0-pre-release` oder `2.0.0`, und starten. Der Workflow

1. prüft die Version (gültige SemVer: `X.Y.Z` oder `X.Y.Z-zusatz`) und dass der Tag `vX.Y.Z` noch
   nicht existiert,
2. übernimmt sie in `Cargo.toml`, `app/package.json` und `app/src-tauri/tauri.conf.json` (die Werte
   im Repository bleiben unverändert),
3. baut, legt das Release als Entwurf mit ZIP und Installer an und veröffentlicht es erst danach.
   Dabei entsteht der Tag auf dem gebauten Commit.

Versionen mit Bindestrich (`2.0.0-pre-release`, `2.0.0-rc.1`) werden als **Vorabversion**
veröffentlicht, Versionen ohne (`2.0.0`) als „Latest“-Release. Die Beschreibung wird aus den
Commits erzeugt und kann auf der Website jederzeit bearbeitet werden. Wer sie vor dem
Veröffentlichen schreiben möchte, setzt beim Start den Haken „entwurf“ und veröffentlicht den
Entwurf anschließend selbst unter „Releases“.

> **Wichtig:** Kein Release vorab auf der Website anlegen. GitHub-Releases sind nach dem
> Veröffentlichen unveränderlich; danach lassen sich keine Dateien mehr anhängen.

## Lizenzen der Komponenten

`app/scripts/lizenzen.mjs` erzeugt vor jedem `tauri build` die Datei `LIZENZEN-DRITTANBIETER.txt` mit
den Lizenztexten aller in der Windows-Anwendung enthaltenen Komponenten (Rust-Abhängigkeiten laut
`cargo metadata` + Laufzeit-Pakete der Oberfläche). Sie wird Installer und portabler ZIP beigelegt.
Übersicht: [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md).

## Dateien neben der EXE (portable Nutzung)

| Pfad | Inhalt |
|------|--------|
| `Taktische_Zeichen_Grafikvorlagen/` | Standard-Vorlagenordner (in der App änderbar) |
| `Taktische_Zeichen_Ausgabe/` | Standard-Ausgabeordner (änderbar) |
| `fonts/` | zusätzliche Schriften (TTF/OTF), die nicht installiert sein müssen |
| `settings.json` | Einstellungen |
| `Logs/JJJJ-MM-TT.log` | Protokolle (die letzten 30 Tage) |
| `LIZENZEN-DRITTANBIETER.txt` | Lizenztexte aller Fremdkomponenten |

Ist der Ordner der EXE schreibgeschützt (z.B. nach Installation unter `C:\Programme`), legt die App
`settings.json` und `Logs/` unter `%APPDATA%\de.thw.taktische-zeichen-druckgenerator\` ab.
