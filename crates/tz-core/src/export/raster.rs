//! Raster-Ausgabe (PNG-Export und Vorschau) mit resvg.

use resvg::tiny_skia::{self, Pixmap, PixmapPaint, Transform};

use crate::compose::Komposition;
use crate::error::{Error, Result};
use crate::fonts::Fonts;
use crate::grafik::usvg_options;
use crate::units::{mm_to_px, CSS_PX_PER_INCH, MM_PER_INCH};

/// Rendert eine Komposition (Dateigroesse inkl. Beschnitt) bei `dpi`.
/// Hintergrund transparent, ausser `hintergrund` ist gesetzt.
pub fn rendere(k: &Komposition, fonts: &Fonts, dpi: f64, hintergrund: Option<[u8; 3]>) -> Result<Pixmap> {
    let w = mm_to_px(k.geometrie.datei.w, dpi).round().max(1.0) as u32;
    let h = mm_to_px(k.geometrie.datei.h, dpi).round().max(1.0) as u32;
    let mut pixmap = Pixmap::new(w, h).ok_or_else(|| Error::Png(format!("Bild {w}x{h} zu gross")))?;
    if let Some([r, g, b]) = hintergrund {
        pixmap.fill(tiny_skia::Color::from_rgba8(r, g, b, 255));
    }
    let ppm = dpi / MM_PER_INCH;

    if let Some(p) = &k.grafik {
        // Grafik in eigenes Teilbild rendern = Zuschnitt auf die Inhaltsbox, damit z.B.
        // weisse Hintergrundflaechen der Vorlage den Text nicht ueberdecken.
        let x0 = (p.ziel.x * ppm).floor();
        let y0 = (p.ziel.y * ppm).floor();
        let x1 = (p.ziel.right() * ppm).ceil();
        let y1 = (p.ziel.bottom() * ppm).ceil();
        if let Some(mut teil) = Pixmap::new((x1 - x0).max(1.0) as u32, (y1 - y0).max(1.0) as u32) {
            let ib = p.grafik.inhalt;
            let s = p.ziel.w * ppm / ib.w;
            let t = Transform::from_translate((p.ziel.x * ppm - x0) as f32, (p.ziel.y * ppm - y0) as f32)
                .pre_scale(s as f32, s as f32)
                .pre_translate(-ib.x as f32, -ib.y as f32);
            resvg::render(&p.grafik.tree, t, &mut teil.as_mut());
            pixmap.draw_pixmap(
                x0 as i32,
                y0 as i32,
                teil.as_ref(),
                &PixmapPaint::default(),
                Transform::identity(),
                None,
            );
        }
    }

    let overlay = usvg::Tree::from_str(&k.overlay_svg, &usvg_options(fonts))
        .map_err(|e| Error::InternalSvg(e.to_string()))?;
    let s = (dpi / CSS_PX_PER_INCH) as f32;
    resvg::render(&overlay, Transform::from_scale(s, s), &mut pixmap.as_mut());
    Ok(pixmap)
}

/// Vorschau: passt die Komposition in `max_px` ein (weisser Hintergrund).
pub fn vorschau(k: &Komposition, fonts: &Fonts, max_px: u32) -> Result<Vec<u8>> {
    let groesste = k.geometrie.datei.w.max(k.geometrie.datei.h);
    let dpi = max_px as f64 / (groesste / MM_PER_INCH);
    let pixmap = rendere(k, fonts, dpi, Some([255, 255, 255]))?;
    png_bytes(&pixmap, dpi)
}

/// Kodiert als PNG mit DPI-Angabe (pHYs), damit Druckprogramme die Groesse kennen.
pub fn png_bytes(pixmap: &Pixmap, dpi: f64) -> Result<Vec<u8>> {
    let mut out = Vec::new();
    {
        let mut enc = png::Encoder::new(&mut out, pixmap.width(), pixmap.height());
        enc.set_color(png::ColorType::Rgba);
        enc.set_depth(png::BitDepth::Eight);
        let ppm = (dpi / 0.0254).round() as u32;
        enc.set_pixel_dims(Some(png::PixelDimensions { xppu: ppm, yppu: ppm, unit: png::Unit::Meter }));
        let mut writer = enc.write_header().map_err(|e| Error::Png(e.to_string()))?;
        // tiny-skia speichert vormultipliziert -> fuer PNG demultiplizieren
        let mut data = Vec::with_capacity(pixmap.data().len());
        for p in pixmap.pixels() {
            let c = p.demultiply();
            data.extend_from_slice(&[c.red(), c.green(), c.blue(), c.alpha()]);
        }
        writer.write_image_data(&data).map_err(|e| Error::Png(e.to_string()))?;
    }
    Ok(out)
}

/// Vorschaubild einer Vorlage (nur sichtbarer Inhalt, eingepasst in `max_px`).
pub fn miniatur(g: &crate::grafik::Grafik, max_px: u32) -> Result<Vec<u8>> {
    let ib = g.inhalt;
    let s = max_px as f64 / ib.w.max(ib.h);
    let w = (ib.w * s).round().max(1.0) as u32;
    let h = (ib.h * s).round().max(1.0) as u32;
    let mut pixmap = Pixmap::new(w, h).ok_or_else(|| Error::Png("Miniatur zu gross".into()))?;
    let t = Transform::from_scale(s as f32, s as f32).pre_translate(-ib.x as f32, -ib.y as f32);
    resvg::render(&g.tree, t, &mut pixmap.as_mut());
    png_bytes(&pixmap, 96.0)
}
