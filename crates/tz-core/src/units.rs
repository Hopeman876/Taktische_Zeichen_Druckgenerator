//! Einheiten und unveraenderliche System-Konstanten (entspricht `SYSTEM_*` der Python-Version).

/// Millimeter pro Zoll.
pub const MM_PER_INCH: f64 = 25.4;
/// PostScript-Punkte pro Zoll.
pub const PT_PER_INCH: f64 = 72.0;
/// CSS/usvg-Pixel pro Zoll (usvg rechnet `mm` mit 96 DPI in Pixel um).
pub const CSS_PX_PER_INCH: f64 = 96.0;

/// Millimeter -> PDF-Punkte.
pub fn mm_to_pt(mm: f64) -> f64 {
    mm / MM_PER_INCH * PT_PER_INCH
}

/// Schriftgroesse in Punkt -> Millimeter.
pub fn pt_to_mm(pt: f64) -> f64 {
    pt / PT_PER_INCH * MM_PER_INCH
}

/// Millimeter -> Pixel bei gegebener Aufloesung.
pub fn mm_to_px(mm: f64, dpi: f64) -> f64 {
    mm / MM_PER_INCH * dpi
}

/// Millimeter -> CSS-Pixel (Einheit, in der usvg-Baeume vermessen sind).
pub fn mm_to_css_px(mm: f64) -> f64 {
    mm_to_px(mm, CSS_PX_PER_INCH)
}

/// CSS-Pixel -> Millimeter.
pub fn css_px_to_mm(px: f64) -> f64 {
    px / CSS_PX_PER_INCH * MM_PER_INCH
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn conversions_roundtrip() {
        assert!((mm_to_pt(25.4) - 72.0).abs() < 1e-9);
        assert!((pt_to_mm(72.0) - 25.4).abs() < 1e-9);
        assert!((mm_to_px(45.0, 600.0).round() - 1063.0).abs() < 1e-9);
        assert!((css_px_to_mm(mm_to_css_px(12.3)) - 12.3).abs() < 1e-9);
    }
}
