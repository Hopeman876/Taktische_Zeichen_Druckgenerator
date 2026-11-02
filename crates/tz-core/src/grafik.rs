//! Laden von Grafikvorlagen (SVG, Pseudo-SVG mit eingebettetem PNG, PNG, JPG).
//!
//! Jede Vorlage wird zu einem eigenstaendigen usvg-Baum. Rasterdateien werden
//! dazu in ein minimales SVG mit `<image>` verpackt. Anschliessend wird der
//! sichtbare Inhalt ermittelt (weisse/transparente Raender werden ignoriert,
//! wie das Whitespace-Trimming der Python-Version).

use std::io::Cursor;
use std::path::Path;
use std::sync::Arc;

use base64::Engine;
use resvg::tiny_skia;
use serde::Serialize;
use usvg::{ImageKind, Node, Tree};

use crate::error::{Error, Result};
use crate::fonts::Fonts;
use crate::katalog::{format_von, VorlageFormat};

/// Kantenlaenge des Hilfsrasters fuer die Inhaltserkennung.
const TRIM_RASTER_PX: f32 = 1024.0;
/// Pixel gelten als "leer", wenn Alpha darunter liegt ...
const TRIM_ALPHA_SCHWELLE: u8 = 8;
/// ... oder alle Farbkanaele mindestens diesen Wert haben (nahezu weiss).
const TRIM_WEISS_SCHWELLE: u8 = 245;

/// Sichtbarer Inhaltsbereich in Baum-Einheiten (CSS-Pixel).
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct InhaltsBox {
    pub x: f64,
    pub y: f64,
    pub w: f64,
    pub h: f64,
}

/// Eine geladene Vorlage.
pub struct Grafik {
    pub tree: Tree,
    pub inhalt: InhaltsBox,
    pub format: VorlageFormat,
    /// Pixelgroesse des groessten eingebetteten Rasterbildes (fuer DPI-Warnungen).
    pub raster_px: Option<(u32, u32)>,
    /// Anteil, den das Rasterbild am Inhalt einnimmt (1.0 bei reinen PNG-Vorlagen).
    pub raster_anteil: f64,
    /// Schriften, die die Vorlage verwendet, die aber nicht installiert sind
    /// (usvg ersetzt sie still durch eine Ersatzschrift).
    pub fehlende_schriften: Vec<String>,
}

impl std::fmt::Debug for Grafik {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Grafik")
            .field("inhalt", &self.inhalt)
            .field("format", &self.format)
            .field("raster_px", &self.raster_px)
            .finish()
    }
}

impl Grafik {
    /// Effektive Aufloesung des Rasterbildes, wenn der Inhalt `breite_mm` breit gedruckt wird.
    pub fn effektive_dpi(&self, breite_mm: f64) -> Option<f64> {
        let (px_w, _) = self.raster_px?;
        if breite_mm <= 0.0 {
            return None;
        }
        Some(px_w as f64 * self.raster_anteil / (breite_mm / crate::units::MM_PER_INCH))
    }
}

/// usvg-Optionen mit gemeinsamer Schriftdatenbank.
pub fn usvg_options(fonts: &Fonts) -> usvg::Options<'static> {
    usvg::Options { fontdb: fonts.db(), ..usvg::Options::default() }
}

/// Laedt eine Vorlagendatei.
pub fn lade(pfad: &Path, fonts: &Fonts) -> Result<Arc<Grafik>> {
    let format = format_von(pfad).ok_or_else(|| Error::UnsupportedFormat(pfad.to_path_buf()))?;
    let data = std::fs::read(pfad).map_err(|e| Error::io(pfad, e))?;
    let mut opts = usvg_options(fonts);
    opts.resources_dir = pfad.parent().map(|p| p.to_path_buf());

    let (tree, raster_px) = match format {
        VorlageFormat::Svg => {
            let data = steuerzeichen_entfernen(data);
            let tree = Tree::from_data(&data, &opts)
                .map_err(|e| Error::Svg { path: pfad.to_path_buf(), message: e.to_string() })?;
            let px = groesstes_rasterbild(tree.root());
            (tree, px)
        }
        VorlageFormat::Png | VorlageFormat::Jpg => {
            let (svg, w, h) = raster_als_svg(&data, format)
                .map_err(|m| Error::Raster { path: pfad.to_path_buf(), message: m })?;
            let tree = Tree::from_str(&svg, &opts)
                .map_err(|e| Error::Raster { path: pfad.to_path_buf(), message: e.to_string() })?;
            (tree, Some((w, h)))
        }
        VorlageFormat::Blanko => return Err(Error::UnsupportedFormat(pfad.to_path_buf())),
    };

    let inhalt = inhalt_ermitteln(&tree);
    let fehlende_schriften = fehlende_schriften(tree.root(), fonts);
    if !fehlende_schriften.is_empty() {
        log::warn!("{}: fehlende Schriften {:?}", pfad.display(), fehlende_schriften);
    }
    let raster_anteil = match (raster_px, format) {
        (Some(_), VorlageFormat::Png | VorlageFormat::Jpg) => inhalt.w / tree.size().width() as f64,
        (Some(_), _) => 1.0,
        _ => 0.0,
    };
    Ok(Arc::new(Grafik { tree, inhalt, format, raster_px, raster_anteil, fehlende_schriften }))
}

/// Entfernt in XML unzulaessige Steuerzeichen (U+0000-U+001F ausser Tab, LF, CR).
///
/// Manche Programme schreiben z.B. bei kaputten Umlauten ein Backspace (U+0008) in
/// Attribute; XML-Parser lehnen die Datei dann komplett ab. Diese Bytes kommen in UTF-8
/// nie innerhalb von Mehrbyte-Zeichen vor und koennen daher byteweise entfernt werden.
/// Die Datei auf der Platte bleibt unveraendert.
fn steuerzeichen_entfernen(mut data: Vec<u8>) -> Vec<u8> {
    let unzulaessig = |b: &u8| *b < 0x20 && !matches!(*b, b'\t' | b'\n' | b'\r');
    if data.iter().any(unzulaessig) {
        log::warn!("Vorlage enthaelt unzulaessige Steuerzeichen - werden beim Laden ignoriert");
        data.retain(|b| !unzulaessig(b));
    }
    data
}

/// Verpackt PNG/JPG-Daten in ein SVG (1 Bildpixel = 1 Baum-Einheit).
fn raster_als_svg(data: &[u8], format: VorlageFormat) -> std::result::Result<(String, u32, u32), String> {
    let (w, h) = bildgroesse(data).ok_or_else(|| "Bildgroesse nicht lesbar".to_string())?;
    let mime = if format == VorlageFormat::Png { "image/png" } else { "image/jpeg" };
    let b64 = base64::engine::general_purpose::STANDARD.encode(data);
    let svg = format!(
        r#"<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><image width="{w}" height="{h}" xlink:href="data:{mime};base64,{b64}"/></svg>"#
    );
    Ok((svg, w, h))
}

fn bildgroesse(data: &[u8]) -> Option<(u32, u32)> {
    image::ImageReader::new(Cursor::new(data)).with_guessed_format().ok()?.into_dimensions().ok()
}

/// Sucht rekursiv das groesste eingebettete Rasterbild (z.B. Pseudo-SVG).
fn groesstes_rasterbild(group: &usvg::Group) -> Option<(u32, u32)> {
    let mut best: Option<(u32, u32)> = None;
    let mut nimm = |kandidat: Option<(u32, u32)>| {
        if let Some((w, h)) = kandidat {
            if best.is_none_or(|(bw, bh)| (w as u64 * h as u64) > (bw as u64 * bh as u64)) {
                best = Some((w, h));
            }
        }
    };
    for node in group.children() {
        match node {
            Node::Group(g) => nimm(groesstes_rasterbild(g)),
            Node::Image(img) => match img.kind() {
                ImageKind::PNG(d) | ImageKind::JPEG(d) | ImageKind::GIF(d) | ImageKind::WEBP(d) => {
                    nimm(bildgroesse(d))
                }
                ImageKind::SVG(t) => nimm(groesstes_rasterbild(t.root())),
            },
            _ => {}
        }
    }
    best
}

/// Sucht Text-Elemente, deren benannte Schriften alle fehlen. Generische Familien
/// (`sans-serif` ...) gelten als vorhanden; gemeldet wird die erste benannte Familie.
fn fehlende_schriften(group: &usvg::Group, fonts: &Fonts) -> Vec<String> {
    let mut fehlend = std::collections::BTreeSet::new();
    sammle_fehlende_schriften(group, fonts, &mut fehlend);
    fehlend.into_iter().collect()
}

fn sammle_fehlende_schriften(
    group: &usvg::Group,
    fonts: &Fonts,
    fehlend: &mut std::collections::BTreeSet<String>,
) {
    for node in group.children() {
        match node {
            Node::Group(g) => sammle_fehlende_schriften(g, fonts, fehlend),
            Node::Text(text) => {
                for span in text.chunks().iter().flat_map(|c| c.spans()) {
                    let benannt: Vec<&str> = span
                        .font()
                        .families()
                        .iter()
                        .filter_map(|f| match f {
                            usvg::FontFamily::Named(n) => Some(n.as_str()),
                            _ => None,
                        })
                        .collect();
                    if let Some(erste) = benannt.first() {
                        if !benannt.iter().any(|n| fonts.hat_familie(n)) {
                            fehlend.insert((*erste).to_string());
                        }
                    }
                }
            }
            _ => {}
        }
    }
}

/// Ermittelt den sichtbaren Bereich ueber ein Hilfsraster.
fn inhalt_ermitteln(tree: &Tree) -> InhaltsBox {
    let size = tree.size();
    let voll = InhaltsBox { x: 0.0, y: 0.0, w: size.width() as f64, h: size.height() as f64 };
    let scale = TRIM_RASTER_PX / size.width().max(size.height());
    let pw = (size.width() * scale).ceil().max(1.0) as u32;
    let ph = (size.height() * scale).ceil().max(1.0) as u32;
    let Some(mut pixmap) = tiny_skia::Pixmap::new(pw, ph) else {
        return voll;
    };
    resvg::render(tree, tiny_skia::Transform::from_scale(scale, scale), &mut pixmap.as_mut());

    let (mut min_x, mut min_y, mut max_x, mut max_y) = (u32::MAX, u32::MAX, 0u32, 0u32);
    for (i, px) in pixmap.pixels().iter().enumerate() {
        let c = px.demultiply();
        let leer = c.alpha() < TRIM_ALPHA_SCHWELLE
            || (c.red() >= TRIM_WEISS_SCHWELLE
                && c.green() >= TRIM_WEISS_SCHWELLE
                && c.blue() >= TRIM_WEISS_SCHWELLE);
        if !leer {
            let x = i as u32 % pw;
            let y = i as u32 / pw;
            min_x = min_x.min(x);
            min_y = min_y.min(y);
            max_x = max_x.max(x);
            max_y = max_y.max(y);
        }
    }
    if min_x > max_x || min_y > max_y {
        return voll;
    }
    // 1 Hilfspixel Rand, damit Antialiasing-Kanten nicht abgeschnitten werden.
    let s = scale as f64;
    let x0 = (min_x.saturating_sub(1)) as f64 / s;
    let y0 = (min_y.saturating_sub(1)) as f64 / s;
    let x1 = ((max_x + 2).min(pw)) as f64 / s;
    let y1 = ((max_y + 2).min(ph)) as f64 / s;
    InhaltsBox { x: x0, y: y0, w: (x1 - x0).min(voll.w), h: (y1 - y0).min(voll.h) }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fonts() -> Fonts {
        Fonts::system()
    }

    #[test]
    fn svg_whitespace_is_trimmed() {
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("t.svg");
        std::fs::write(
            &p,
            r#"<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
                <rect width="100" height="100" fill="white"/>
                <rect x="20" y="30" width="40" height="20" fill="blue"/></svg>"#,
        )
        .unwrap();
        let g = lade(&p, &fonts()).unwrap();
        assert!((g.inhalt.x - 20.0).abs() < 0.5, "{:?}", g.inhalt);
        assert!((g.inhalt.y - 30.0).abs() < 0.5);
        assert!((g.inhalt.w - 40.0).abs() < 0.6);
        assert!((g.inhalt.h - 20.0).abs() < 0.6);
        assert!(g.raster_px.is_none());
        assert!(g.fehlende_schriften.is_empty());
    }

    #[test]
    fn control_characters_are_removed() {
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("kaputt.svg");
        // Wie ETB-Fue.svg: Backspace statt Umlaut im id-Attribut
        std::fs::write(
            &p,
            b"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"10\" height=\"10\"><rect id=\"Fu\x08\" width=\"10\" height=\"10\"/></svg>",
        )
        .unwrap();
        assert!(lade(&p, &fonts()).is_ok());
    }

    #[test]
    fn missing_template_fonts_are_reported() {
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("t.svg");
        std::fs::write(
            &p,
            r#"<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">
                <text x="5" y="30" font-family="Gibt-Es-Nicht-Font, sans-serif">A</text>
                <text x="50" y="30" font-family="sans-serif">B</text></svg>"#,
        )
        .unwrap();
        let g = lade(&p, &fonts()).unwrap();
        assert_eq!(g.fehlende_schriften, vec!["Gibt-Es-Nicht-Font".to_string()]);
    }

    #[test]
    fn png_is_wrapped_and_trimmed() {
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("t.png");
        let mut img = image::RgbaImage::new(200, 100);
        for y in 10..60 {
            for x in 50..150 {
                img.put_pixel(x, y, image::Rgba([200, 0, 0, 255]));
            }
        }
        img.save(&p).unwrap();
        let g = lade(&p, &fonts()).unwrap();
        assert_eq!(g.raster_px, Some((200, 100)));
        assert!((g.inhalt.x - 50.0).abs() < 1.0, "{:?}", g.inhalt);
        // Bildglaettung beim Hochskalieren verbreitert die Kante um ca. 1 Quellpixel
        assert!((g.inhalt.w - 100.0).abs() < 3.0, "{:?}", g.inhalt);
        // 100 Inhaltspixel auf 25.4 mm gedruckt = 100 DPI
        let dpi = g.effektive_dpi(25.4).unwrap();
        assert!((dpi - 100.0).abs() < 4.0, "{dpi}");
    }

    #[test]
    fn pseudo_svg_with_embedded_png_is_detected() {
        let dir = tempfile::tempdir().unwrap();
        let png = dir.path().join("i.png");
        image::RgbaImage::from_pixel(64, 32, image::Rgba([0, 0, 0, 255])).save(&png).unwrap();
        let b64 = base64::engine::general_purpose::STANDARD.encode(std::fs::read(&png).unwrap());
        let p = dir.path().join("pseudo.svg");
        std::fs::write(
            &p,
            format!(
                r#"<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="64" height="32"><image width="64" height="32" xlink:href="data:image/png;base64,{b64}"/></svg>"#
            ),
        )
        .unwrap();
        let g = lade(&p, &fonts()).unwrap();
        assert_eq!(g.raster_px, Some((64, 32)));
    }
}
