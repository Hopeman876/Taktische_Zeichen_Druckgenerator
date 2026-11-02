//! Schnittbogen-Layout: Raster fertiger Zeichen (ohne Beschnitt) auf DIN A4.

use serde::Serialize;

use crate::config::DruckConfig;
use crate::error::{Error, Result};

pub const A4_KURZ_MM: f64 = 210.0;
pub const A4_LANG_MM: f64 = 297.0;

/// Berechnetes Raster.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct BogenLayout {
    pub seite_w_mm: f64,
    pub seite_h_mm: f64,
    pub querformat: bool,
    pub spalten: usize,
    pub zeilen: usize,
    /// Linke obere Ecke des Rasters (Raster ist auf der Seite zentriert).
    pub offset_x_mm: f64,
    pub offset_y_mm: f64,
    pub zeichen_w_mm: f64,
    pub zeichen_h_mm: f64,
}

impl BogenLayout {
    pub fn pro_seite(&self) -> usize {
        self.spalten * self.zeilen
    }

    /// Linke obere Ecke von Platz `i` auf der Seite.
    pub fn position(&self, i: usize) -> (f64, f64) {
        let col = i % self.spalten;
        let row = i / self.spalten;
        (self.offset_x_mm + col as f64 * self.zeichen_w_mm, self.offset_y_mm + row as f64 * self.zeichen_h_mm)
    }

    /// Hoch- oder Querformat - je nachdem, wo mehr Zeichen passen.
    pub fn berechne(cfg: &DruckConfig) -> Result<Self> {
        let g = cfg.groesse();
        let (mh, mv) = (cfg.export.bogen_rand_horizontal_mm, cfg.export.bogen_rand_vertikal_mm);
        let raster = |seite_w: f64, seite_h: f64| {
            let cols = ((seite_w - 2.0 * mh) / g.breite_mm + 1e-9).floor().max(0.0) as usize;
            let rows = ((seite_h - 2.0 * mv) / g.hoehe_mm + 1e-9).floor().max(0.0) as usize;
            (cols, rows)
        };
        let hoch = raster(A4_KURZ_MM, A4_LANG_MM);
        let quer = raster(A4_LANG_MM, A4_KURZ_MM);
        let querformat = quer.0 * quer.1 > hoch.0 * hoch.1;
        let ((spalten, zeilen), (seite_w, seite_h)) =
            if querformat { (quer, (A4_LANG_MM, A4_KURZ_MM)) } else { (hoch, (A4_KURZ_MM, A4_LANG_MM)) };
        if spalten * zeilen == 0 {
            return Err(Error::Config(format!(
                "Zeichen ({:.1} x {:.1} mm) passt mit den Seitenraendern nicht auf A4",
                g.breite_mm, g.hoehe_mm
            )));
        }
        Ok(Self {
            seite_w_mm: seite_w,
            seite_h_mm: seite_h,
            querformat,
            spalten,
            zeilen,
            offset_x_mm: (seite_w - spalten as f64 * g.breite_mm) / 2.0,
            offset_y_mm: (seite_h - zeilen as f64 * g.hoehe_mm) / 2.0,
            zeichen_w_mm: g.breite_mm,
            zeichen_h_mm: g.hoehe_mm,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::Layout;

    #[test]
    fn default_s2_grid() {
        let l = BogenLayout::berechne(&DruckConfig::default()).unwrap();
        // 45 x 47.5 mm, 8 mm Rand: hoch 4x5=20, quer 6x4=24 -> quer
        assert!(l.querformat);
        assert_eq!((l.spalten, l.zeilen), (6, 4));
        assert!((l.offset_x_mm - (297.0 - 270.0) / 2.0).abs() < 1e-9);
    }

    #[test]
    fn s1_grid_and_too_large() {
        let mut cfg = DruckConfig { layout: Layout::S1, ..Default::default() };
        let l = BogenLayout::berechne(&cfg).unwrap();
        // 90 x 47.5 mm: hoch 2x5=10, quer 3x4=12
        assert_eq!(l.pro_seite(), 12);
        cfg.s1.groesse.breite_mm = 280.0;
        cfg.s1.groesse.hoehe_mm = 280.0;
        assert!(BogenLayout::berechne(&cfg).is_err());
    }
}
