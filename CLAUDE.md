# Taktische Zeichen Druckgenerator - AI Guide

**Version:** v0.9.0 (Rust/Tauri rewrite) | **Updated:** 2026-11-01

## What Is This Project?

Desktop application (Windows first, portable) that prepares tactical signs (SVG/PNG templates)
with text overlays for printing: vector PDF (single signs with bleed, or A4 cutting sheets)
and PNG. The former Python/PyQt version (up to v0.8.x) lives in git history (last commit `5499f7a`).

**Tech Stack:** Rust (tz-core: usvg/resvg, svg2pdf, pdf-writer, rustybuzz) | Tauri 2 | Svelte 5 + TypeScript

## Structure

```
crates/tz-core/   Rendering core, no GUI, fully tested (start here for any print/layout logic)
crates/tz-cli/    CLI `tzdg` (export from JSON job, preview, catalog)
app/src/          UI (Svelte 5 runes): lib/store.svelte.ts (state), lib/api.ts, lib/types.ts
app/src-tauri/    Thin Tauri command layer over tz-core (settings, dialogs, threads, progress)
docs/             ARCHITEKTUR.md (architecture, layout rules), ROADMAP.md (open items), bilder/ (README images)
README.md         user-facing project page (German, with screenshots) - keep technical details in ENTWICKLUNG.md
ENTWICKLUNG.md    developer docs: build, CLI, release via tag, licenses, portable files
.github/workflows/build.yml   tests, clippy, frontend check, Windows build, release on tag v*
```

**Read `docs/ARCHITEKTUR.md` before changing layout or export code.**

## Critical Rules

1. **Single sources of truth**
   - Factory defaults ONLY in `DruckConfig::default()` (`crates/tz-core/src/config.rs`).
     New setting = field + default + check in `pruefe()` + input in `EinstellungenDialog.svelte`.
   - Mode labels/placeholders ONLY in `crates/tz-core/src/modus.rs` (UI gets them via `app_info`).
   - Serde names of modes must stay compatible with the Python version (`ov_staerke`, `ohne_text`, ...).
2. **Keep the pipeline vector.** Templates and overlay are separate layers; never rasterize for PDF.
3. **Quality gates (must pass before commit):**
   `cargo fmt --all --check`, `cargo clippy -p tz-core -p tz-cli --all-targets -- -D warnings`,
   `cargo test`, and in `app/`: `npm run check`.
4. **Code style:** German domain terms and doc comments (as in existing code), English Rust/TS idioms.
   No magic numbers: named `const` in the module. No `unwrap()` on user data; return `tz_core::Error`.
   Typed TS (no `any`); UI texts may contain umlauts.
5. **Git:** NO automatic commits - only commit/push when the user explicitly asks.
   Commit messages: `<Typ>: <Kurzbeschreibung>` (Feature/Fix/Refactor/Docs/Test/Chore), imperative.
   Work on the `claude/*` branch named in the task; push with `git push -u origin <branch>`,
   retry up to 4 times with exponential backoff on network errors.

## Quick Commands

```bash
cargo test                                # core + CLI tests (no GUI deps needed)
cargo run -p tz-cli -- export job.json    # headless export
cd app && npm install && npx tauri dev    # run the app (Linux needs libwebkit2gtk-4.1-dev)
cd app && npx tauri build                 # release build (Windows: NSIS installer + exe)
```

## Text Modes (internal id -> label)

`ov_staerke` OV + Stärke · `ort_staerke` Ort + Stärke · `schreiblinie_staerke` Schreiblinie + Stärke ·
`freitext` Schreiblinie oder Freitext (default) · `ruf` Ruf · `dateiname` Dateiname · `ohne_text` Nur Grafik.
Layouts: S2 (single sign) and S1 (double sign with writing lines on the right).
