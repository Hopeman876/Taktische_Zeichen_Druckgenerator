//! Minimaler SVG-Builder fuer das Beschriftungs-Overlay.
//!
//! Alle Koordinaten sind Millimeter (`viewBox` in mm, `width/height` mit Einheit mm).
//! Stile werden als `style`-Attribut geschrieben, damit CSS aus Vorlagen sie nicht
//! ueberschreiben kann.

use std::fmt::Write;

/// RGB-Farbe.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Rgb(pub u8, pub u8, pub u8);

impl Rgb {
    pub const SCHWARZ: Rgb = Rgb(0, 0, 0);
    pub const WEISS: Rgb = Rgb(255, 255, 255);
    pub const SCHREIBLINIE: Rgb = Rgb(80, 80, 80);
    pub const BESCHNITT: Rgb = Rgb(255, 0, 0);
    pub const SCHNITT: Rgb = Rgb(0, 0, 255);
    pub const SICHERHEIT: Rgb = Rgb(0, 170, 0);
    pub const S1_TRENNLINIE: Rgb = Rgb(255, 140, 0);
    pub const HINWEIS: Rgb = Rgb(128, 128, 128);

    fn css(self) -> String {
        format!("#{:02x}{:02x}{:02x}", self.0, self.1, self.2)
    }
}

/// Textanker.
#[derive(Debug, Clone, Copy)]
pub enum Anker {
    Start,
    Mitte,
}

/// SVG-Dokument im Aufbau.
pub struct SvgBuilder {
    out: String,
}

/// Zahl kompakt formatieren (max. 4 Nachkommastellen).
pub fn num(v: f64) -> String {
    let s = format!("{:.4}", v);
    let s = s.trim_end_matches('0').trim_end_matches('.');
    if s == "-0" {
        "0".into()
    } else {
        s.into()
    }
}

/// XML-Escaping fuer Text und Attribute.
pub fn escape(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    for c in text.chars() {
        match c {
            '&' => out.push_str("&amp;"),
            '<' => out.push_str("&lt;"),
            '>' => out.push_str("&gt;"),
            '"' => out.push_str("&quot;"),
            '\'' => out.push_str("&apos;"),
            c if (c as u32) < 0x20 && c != '\t' => {}
            c => out.push(c),
        }
    }
    out
}

impl SvgBuilder {
    /// Neues Dokument mit Groesse in mm.
    pub fn new(breite_mm: f64, hoehe_mm: f64) -> Self {
        let mut out = String::with_capacity(4096);
        let _ = write!(
            out,
            r#"<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">"#,
            w = num(breite_mm),
            h = num(hoehe_mm)
        );
        Self { out }
    }

    /// Gefuelltes Rechteck.
    pub fn rect_fill(&mut self, x: f64, y: f64, w: f64, h: f64, farbe: Rgb) {
        if w <= 0.0 || h <= 0.0 {
            return;
        }
        let _ = write!(
            self.out,
            r#"<rect x="{}" y="{}" width="{}" height="{}" style="fill:{};stroke:none"/>"#,
            num(x),
            num(y),
            num(w),
            num(h),
            farbe.css()
        );
    }

    /// Rechteck-Umriss (Linie mittig auf der Kante).
    pub fn rect_stroke(&mut self, x: f64, y: f64, w: f64, h: f64, farbe: Rgb, dicke: f64) {
        let _ = write!(
            self.out,
            r#"<rect x="{}" y="{}" width="{}" height="{}" style="fill:none;stroke:{};stroke-width:{}"/>"#,
            num(x),
            num(y),
            num(w),
            num(h),
            farbe.css(),
            num(dicke)
        );
    }

    /// Gerade Linie.
    pub fn line(&mut self, x1: f64, y1: f64, x2: f64, y2: f64, farbe: Rgb, dicke: f64) {
        let _ = write!(
            self.out,
            r#"<line x1="{}" y1="{}" x2="{}" y2="{}" style="stroke:{};stroke-width:{};stroke-linecap:butt"/>"#,
            num(x1),
            num(y1),
            num(x2),
            num(y2),
            farbe.css(),
            num(dicke)
        );
    }

    /// Einzeiliger Text an der Grundlinie `y`.
    #[allow(clippy::too_many_arguments)]
    pub fn text(
        &mut self,
        x: f64,
        y: f64,
        text: &str,
        family: &str,
        size_mm: f64,
        farbe: Rgb,
        anker: Anker,
        halo: Option<Rgb>,
    ) {
        if text.is_empty() {
            return;
        }
        let anchor = match anker {
            Anker::Start => "start",
            Anker::Mitte => "middle",
        };
        let halo_css = halo
            .map(|h| format!(";stroke:{};stroke-width:{};paint-order:stroke", h.css(), num(size_mm * 0.15)))
            .unwrap_or_default();
        let _ = write!(
            self.out,
            r#"<text x="{}" y="{}" xml:space="preserve" style="font-family:'{}';font-size:{}px;fill:{};text-anchor:{}{}">{}</text>"#,
            num(x),
            num(y),
            escape(family).replace('\'', ""),
            num(size_mm),
            farbe.css(),
            anchor,
            halo_css,
            escape(text)
        );
    }

    /// Fertiges Dokument.
    pub fn finish(mut self) -> String {
        self.out.push_str("</svg>");
        self.out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn number_formatting() {
        assert_eq!(num(1.0), "1");
        assert_eq!(num(1.25), "1.25");
        assert_eq!(num(-0.00001), "0");
        assert_eq!(num(1.234_567), "1.2346");
    }

    #[test]
    fn escaping() {
        assert_eq!(escape("A&B <C> \"d\""), "A&amp;B &lt;C&gt; &quot;d&quot;");
    }

    #[test]
    fn builder_produces_parsable_svg() {
        let mut b = SvgBuilder::new(45.0, 47.5);
        b.rect_fill(0.0, 0.0, 45.0, 47.5, Rgb::WEISS);
        b.text(1.0, 40.0, "OV: Musterstadt & Co", "Arial", 3.5, Rgb::SCHWARZ, Anker::Start, None);
        let svg = b.finish();
        let tree = usvg::Tree::from_str(&svg, &usvg::Options::default()).unwrap();
        assert!((tree.size().width() - crate::units::mm_to_css_px(45.0) as f32).abs() < 0.01);
    }
}
