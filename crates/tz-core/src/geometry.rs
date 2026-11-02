//! Geometrie eines Zeichens: Datei (mit Beschnitt) -> Schnitt -> Sicherheitsbereich.

use serde::Serialize;

use crate::config::Groesse;

/// Achsparalleles Rechteck in mm (Ursprung oben links, y nach unten).
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct Rect {
    pub x: f64,
    pub y: f64,
    pub w: f64,
    pub h: f64,
}

impl Rect {
    pub const fn new(x: f64, y: f64, w: f64, h: f64) -> Self {
        Self { x, y, w, h }
    }

    pub fn right(&self) -> f64 {
        self.x + self.w
    }

    pub fn bottom(&self) -> f64 {
        self.y + self.h
    }

    /// Um `d` nach innen verkleinert.
    pub fn inset(&self, d: f64) -> Rect {
        Rect::new(self.x + d, self.y + d, (self.w - 2.0 * d).max(0.0), (self.h - 2.0 * d).max(0.0))
    }

    pub fn is_empty(&self) -> bool {
        self.w <= 0.0 || self.h <= 0.0
    }
}

/// Die drei verschachtelten Bereiche eines Zeichens.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct ZeichenGeometrie {
    /// Gesamte Datei inkl. Beschnittzugabe.
    pub datei: Rect,
    /// Fertiges Zeichen nach dem Zuschnitt.
    pub schnitt: Rect,
    /// Bereich fuer Grafik und Text (Schnitt minus Sicherheitsabstand).
    pub inhalt: Rect,
}

impl ZeichenGeometrie {
    pub fn aus(g: &Groesse) -> Self {
        let datei =
            Rect::new(0.0, 0.0, g.breite_mm + 2.0 * g.beschnitt_mm, g.hoehe_mm + 2.0 * g.beschnitt_mm);
        let schnitt = datei.inset(g.beschnitt_mm);
        let inhalt = schnitt.inset(g.sicherheitsabstand_mm);
        Self { datei, schnitt, inhalt }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn nested_areas() {
        let g = Groesse { hoehe_mm: 45.0, breite_mm: 45.0, beschnitt_mm: 3.0, sicherheitsabstand_mm: 3.0 };
        let geo = ZeichenGeometrie::aus(&g);
        assert_eq!(geo.datei, Rect::new(0.0, 0.0, 51.0, 51.0));
        assert_eq!(geo.schnitt, Rect::new(3.0, 3.0, 45.0, 45.0));
        assert_eq!(geo.inhalt, Rect::new(6.0, 6.0, 39.0, 39.0));
    }
}
