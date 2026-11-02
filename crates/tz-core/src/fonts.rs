//! Schriftverwaltung und Textmessung.
//!
//! Gemessen wird mit rustybuzz (derselbe Shaper, den usvg beim Rendern nutzt),
//! damit Layout-Berechnung und Ausgabe exakt uebereinstimmen.

use std::collections::BTreeSet;
use std::path::Path;
use std::sync::Arc;

use usvg::fontdb::{self, Database, Family, Query};

use crate::error::{Error, Result};

/// Fallback-Kette, falls die gewuenschte Schrift fehlt.
const FALLBACK_FAMILIEN: [&str; 4] = ["Arial", "Liberation Sans", "Helvetica", "DejaVu Sans"];

/// Gemeinsam genutzte Schriftdatenbank.
#[derive(Clone)]
pub struct Fonts {
    db: Arc<Database>,
}

/// Eine aufgeloeste Schrift mit Metriken (Werte relativ zur Schriftgroesse = 1).
#[derive(Clone)]
pub struct FontFace {
    /// Tatsaechlich gefundene Familie (wird so ins SVG geschrieben).
    pub family: String,
    /// `true`, wenn nicht die gewuenschte Familie, sondern ein Fallback genutzt wird.
    pub ist_fallback: bool,
    pub ascender: f64,
    pub descender: f64,
    pub underline_position: f64,
    pub underline_dicke: f64,
    data: Arc<Vec<u8>>,
    index: u32,
}

impl Fonts {
    /// Laedt alle Systemschriften.
    pub fn system() -> Self {
        let mut db = Database::new();
        db.load_system_fonts();
        Self::from_db(db)
    }

    /// Laedt Systemschriften plus alle Schriften aus `dir` (z.B. `fonts/` neben der EXE).
    pub fn system_mit_ordner(dir: &Path) -> Self {
        let mut db = Database::new();
        db.load_system_fonts();
        if dir.is_dir() {
            db.load_fonts_dir(dir);
        }
        Self::from_db(db)
    }

    /// Verwendet eine vorbereitete Datenbank.
    pub fn from_db(mut db: Database) -> Self {
        for fam in FALLBACK_FAMILIEN {
            if has_family(&db, fam) {
                db.set_sans_serif_family(fam);
                break;
            }
        }
        Self { db: Arc::new(db) }
    }

    /// Datenbank fuer usvg-Optionen.
    pub fn db(&self) -> Arc<Database> {
        self.db.clone()
    }

    /// Alle verfuegbaren Familiennamen (sortiert, fuer Auswahllisten).
    pub fn familien(&self) -> Vec<String> {
        let mut set = BTreeSet::new();
        for face in self.db.faces() {
            if let Some((name, _)) = face.families.first() {
                set.insert(name.clone());
            }
        }
        set.into_iter().collect()
    }

    /// Ob die Familie installiert ist.
    pub fn hat_familie(&self, family: &str) -> bool {
        has_family(&self.db, family)
    }

    /// Loest eine Familie (regulaerer Schnitt) inkl. Fallback-Kette auf.
    pub fn resolve(&self, family: &str) -> Result<FontFace> {
        let mut kandidaten: Vec<(&str, bool)> = vec![(family, false)];
        kandidaten.extend(FALLBACK_FAMILIEN.iter().map(|f| (*f, true)));
        for (name, fallback) in kandidaten {
            let query = Query { families: &[Family::Name(name)], ..Query::default() };
            if let Some(id) = self.db.query(&query) {
                if let Some(face) = self.load_face(id, fallback && name != family) {
                    return Ok(face);
                }
            }
        }
        let query = Query { families: &[Family::SansSerif], ..Query::default() };
        let id = self
            .db
            .query(&query)
            .or_else(|| self.db.faces().next().map(|f| f.id))
            .ok_or_else(|| Error::FontMissing(family.to_string()))?;
        self.load_face(id, true).ok_or_else(|| Error::FontMissing(family.to_string()))
    }

    fn load_face(&self, id: fontdb::ID, ist_fallback: bool) -> Option<FontFace> {
        let family = self.db.face(id)?.families.first()?.0.clone();
        self.db.with_face_data(id, |data, index| {
            let face = rustybuzz::ttf_parser::Face::parse(data, index).ok()?;
            let upem = face.units_per_em() as f64;
            let (ul_pos, ul_dicke) = face
                .underline_metrics()
                .map(|m| (m.position as f64 / upem, m.thickness as f64 / upem))
                .unwrap_or((-0.1, 0.05));
            Some(FontFace {
                family: family.clone(),
                ist_fallback,
                ascender: face.ascender() as f64 / upem,
                descender: -(face.descender() as f64) / upem,
                underline_position: -ul_pos,
                underline_dicke: ul_dicke.max(0.03),
                data: Arc::new(data.to_vec()),
                index,
            })
        })?
    }
}

impl FontFace {
    /// Laufweite eines Textes in derselben Einheit wie `size`.
    pub fn breite(&self, text: &str, size: f64) -> f64 {
        if text.is_empty() {
            return 0.0;
        }
        let Some(face) = rustybuzz::Face::from_slice(&self.data, self.index) else {
            return 0.0;
        };
        let mut buffer = rustybuzz::UnicodeBuffer::new();
        buffer.push_str(text);
        let glyphs = rustybuzz::shape(&face, &[], buffer);
        let advance: i64 = glyphs.glyph_positions().iter().map(|p| p.x_advance as i64).sum();
        advance as f64 / face.units_per_em() as f64 * size
    }
}

fn has_family(db: &Database, family: &str) -> bool {
    db.faces().any(|f| f.families.iter().any(|(n, _)| n.eq_ignore_ascii_case(family)))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn resolves_with_fallback_and_measures() {
        let fonts = Fonts::system();
        let face = fonts.resolve("Gibt-Es-Nicht-Font").expect("irgendeine Schrift");
        assert!(face.ist_fallback);
        let w1 = face.breite("OV: ", 10.0);
        let w2 = face.breite("OV: OV", 10.0);
        assert!(w1 > 0.0 && w2 > w1);
        assert!(face.ascender > 0.5 && face.descender > 0.0);
        // Laufweite skaliert linear
        assert!((face.breite("Test", 20.0) - 2.0 * face.breite("Test", 10.0)).abs() < 1e-9);
    }
}
