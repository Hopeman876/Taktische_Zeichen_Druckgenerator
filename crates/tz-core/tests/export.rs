//! Ende-zu-Ende-Tests: Vorlagen -> PNG / PDF-Einzelzeichen / PDF-Schnittbogen.

use std::path::Path;

use tz_core::compose::ZeichenSpec;
use tz_core::config::{DruckConfig, Layout};
use tz_core::fonts::Fonts;
use tz_core::job::{exportiere, ExportAuftrag, ExportFormat, ExportPosten, GrafikCache, KeinFortschritt};
use tz_core::katalog::{BlankoArt, VorlageRef};
use tz_core::modus::Modus;

const SVG_VORLAGE: &str = r##"<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <rect width="200" height="200" fill="#ffffff"/>
  <path d="M20 40 H180 V160 H20 Z" fill="none" stroke="#00467f" stroke-width="8"/>
  <path d="M20 40 L180 160 M180 40 L20 160" stroke="#00467f" stroke-width="6"/>
</svg>"##;

fn vorlagen(dir: &Path) -> (VorlageRef, VorlageRef) {
    let svg = dir.join("Einheit.svg");
    std::fs::write(&svg, SVG_VORLAGE).unwrap();
    let png = dir.join("Foto.png");
    let mut img = image::RgbaImage::new(400, 300);
    for (x, y, p) in img.enumerate_pixels_mut() {
        if (50..350).contains(&x) && (50..250).contains(&y) {
            *p = image::Rgba([220, 30, 30, 255]);
        }
    }
    img.save(&png).unwrap();
    (VorlageRef::Datei { pfad: svg }, VorlageRef::Datei { pfad: png })
}

fn posten(vorlage: VorlageRef, modus: Modus, text: Option<&str>, kopien: u32) -> ExportPosten {
    ExportPosten {
        zeichen: ZeichenSpec { vorlage, modus, text: text.map(String::from), ..Default::default() },
        kopien,
    }
}

fn auftrag(dir: &Path, format: ExportFormat, layout: Layout) -> ExportAuftrag {
    let (svg, png) = vorlagen(dir);
    ExportAuftrag {
        posten: vec![
            posten(svg.clone(), Modus::OvStaerke, Some("Musterstadt"), 3),
            posten(svg, Modus::Freitext, None, 1),
            posten(png, Modus::Ruf, Some("Heros Musterstadt 23/1"), 2),
            posten(VorlageRef::Blanko { blanko: BlankoArt::Leer }, Modus::SchreiblinieStaerke, None, 1),
        ],
        config: DruckConfig { layout, ..Default::default() },
        format,
        ziel_ordner: dir.join("out"),
        schnittlinien: Some(true),
        zeichen_pro_datei: None,
    }
}

fn count(hay: &[u8], needle: &[u8]) -> usize {
    hay.windows(needle.len()).filter(|w| *w == needle).count()
}

#[test]
fn pdf_einzel_is_vector_and_deduplicated() {
    let dir = tempfile::tempdir().unwrap();
    let fonts = Fonts::system();
    let a = auftrag(dir.path(), ExportFormat::PdfEinzel, Layout::S2);
    let bericht = exportiere(&a, &fonts, &GrafikCache::new(), &KeinFortschritt).unwrap();
    assert_eq!(bericht.anzahl_zeichen, 7);
    assert_eq!(bericht.anzahl_seiten, 7);
    assert_eq!(bericht.dateien.len(), 1);
    let pdf = std::fs::read(&bericht.dateien[0]).unwrap();
    assert!(pdf.starts_with(b"%PDF-"));
    // Nur die PNG-Vorlage ist ein Rasterbild, und sie wird trotz 2 Kopien nur einmal eingebettet.
    // Rasterbild + Alpha-Maske (SMask), trotz 2 Kopien nur einmal eingebettet
    assert_eq!(count(&pdf, b"/Subtype /Image"), 2, "genau ein Rasterbild");
    assert_eq!(count(&pdf, b"/TrimBox"), 7);
    assert!(count(&pdf, b"/PrintScaling /None") == 1);
}

#[test]
fn pdf_bogen_fits_pages() {
    let dir = tempfile::tempdir().unwrap();
    let fonts = Fonts::system();
    let mut a = auftrag(dir.path(), ExportFormat::PdfBogen, Layout::S2);
    a.posten[0].kopien = 30; // 30 + 1 + 2 + 1 = 34 Zeichen, 24 pro Seite -> 2 Seiten
    let bericht = exportiere(&a, &fonts, &GrafikCache::new(), &KeinFortschritt).unwrap();
    assert_eq!(bericht.anzahl_seiten, 2);
    let pdf = std::fs::read(&bericht.dateien[0]).unwrap();
    assert_eq!(count(&pdf, b"/Subtype /Image"), 2);
}

#[test]
fn png_export_has_correct_size_and_dpi() {
    let dir = tempfile::tempdir().unwrap();
    let fonts = Fonts::system();
    let a = auftrag(dir.path(), ExportFormat::Png, Layout::S1);
    let bericht = exportiere(&a, &fonts, &GrafikCache::new(), &KeinFortschritt).unwrap();
    // Kopien laut auftrag(): 3 + 1 + 2 + 1 = 7 Dateien, Kopien mit Zaehler im Namen
    assert_eq!(bericht.dateien.len(), 7);
    let namen: Vec<String> =
        bericht.dateien.iter().map(|p| p.file_name().unwrap().to_string_lossy().into_owned()).collect();
    assert!(namen.iter().any(|n| n.ends_with("_3.png")), "{namen:?}");
    assert!(namen.iter().any(|n| n == "002_Einheit.png"), "{namen:?}");
    let img = image::open(&bericht.dateien[0]).unwrap();
    // S1: 90 + 2*2 mm breit, 47.5 + 2*2 mm hoch bei 300 DPI
    let erwartet_w = ((94.0 / 25.4) * 300.0_f64).round() as u32;
    let erwartet_h = ((51.5 / 25.4) * 300.0_f64).round() as u32;
    assert_eq!((img.width(), img.height()), (erwartet_w, erwartet_h));
    // PNG-Vorlage mit 300 px Inhalt ist zu klein fuer 300 DPI -> Warnung
    assert!(bericht.hinweise.iter().any(|h| h.position == 3));
    // ... und landet im Hinweis-Bericht im Ausgabeordner
    let datei = bericht.bericht_datei.expect("Hinweis-Bericht");
    let text = std::fs::read_to_string(datei).unwrap();
    assert!(text.contains("DPI"), "{text}");
}

#[test]
fn unreadable_templates_block_export_and_are_all_listed() {
    let dir = tempfile::tempdir().unwrap();
    let fonts = Fonts::system();
    let mut a = auftrag(dir.path(), ExportFormat::PdfEinzel, Layout::S2);
    for (i, name) in ["kaputt1.svg", "kaputt2.svg"].iter().enumerate() {
        let p = dir.path().join(name);
        std::fs::write(&p, "<svg kein xml").unwrap();
        a.posten.insert(i, posten(VorlageRef::Datei { pfad: p }, Modus::Freitext, None, 1));
    }
    let fehler = exportiere(&a, &fonts, &GrafikCache::new(), &KeinFortschritt).unwrap_err().to_string();
    assert!(fehler.contains("#1 kaputt1") && fehler.contains("#2 kaputt2"), "{fehler}");
}
