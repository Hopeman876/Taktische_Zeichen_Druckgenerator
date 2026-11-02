//! Druck- und Layout-Konfiguration.
//!
//! `DruckConfig::default()` ist die einzige Stelle mit Werkseinstellungen
//! (entspricht den `DEFAULT_*`-Konstanten + RuntimeConfig der Python-Version).
//! Die App speichert die Struktur als JSON (`settings.json`); fehlende Felder
//! werden beim Laden durch `#[serde(default)]` mit Werkseinstellungen gefuellt.

use serde::{Deserialize, Serialize};

use crate::error::{Error, Result};

/// Welches Layout aktiv ist.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Layout {
    /// Einzelschild: Grafik oben, zwei Textzeilen unten.
    S2,
    /// Doppelschild: links Grafik + Text, rechts Schreiblinien.
    S1,
}

/// Abmessungen eines fertigen Zeichens.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Groesse {
    /// Hoehe des fertigen Zeichens (nach dem Zuschnitt) in mm.
    pub hoehe_mm: f64,
    /// Breite des fertigen Zeichens (nach dem Zuschnitt) in mm.
    pub breite_mm: f64,
    /// Beschnittzugabe rund um das Zeichen in mm (wird abgeschnitten).
    pub beschnitt_mm: f64,
    /// Abstand von Grafik/Text zum fertigen Rand in mm.
    pub sicherheitsabstand_mm: f64,
}

impl Default for Groesse {
    fn default() -> Self {
        Self { hoehe_mm: 47.5, breite_mm: 45.0, beschnitt_mm: 2.0, sicherheitsabstand_mm: 3.0 }
    }
}

/// S1-spezifische Optionen (Doppelschild).
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct S1Optionen {
    pub groesse: Groesse,
    /// Anteil des linken Bereichs (Grafik + Text) in Prozent.
    pub links_prozent: f64,
    /// Anzahl Schreiblinien im rechten Bereich.
    pub anzahl_schreiblinien: u32,
    /// Staerke-Platzhalter in der obersten Schreiblinie anzeigen.
    pub staerke_anzeigen: bool,
}

impl Default for S1Optionen {
    fn default() -> Self {
        Self {
            groesse: Groesse {
                hoehe_mm: 47.5,
                breite_mm: 90.0,
                beschnitt_mm: 2.0,
                sicherheitsabstand_mm: 2.0,
            },
            links_prozent: 40.0,
            anzahl_schreiblinien: 5,
            staerke_anzeigen: true,
        }
    }
}

/// Schrift- und Textabstaende.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct TextOptionen {
    /// Schriftfamilie (Systemschrift). Fallback: serifenlose Standardschrift.
    pub font_family: String,
    /// Schriftgroesse in Punkt.
    pub font_size_pt: f64,
    /// Schriftgroesse beim Aendern der Zeichenhoehe automatisch anpassen
    /// (siehe [`empfohlene_schrift_pt`]); die Oberflaeche setzt dann `font_size_pt`.
    pub schrift_mitwachsen: bool,
    /// Abstand zwischen zwei Grundlinien als Vielfaches der Schriftgroesse.
    pub zeilenabstand_faktor: f64,
    /// Abstand Grafik (unten) -> Text (oben) in mm.
    pub abstand_grafik_text_mm: f64,
    /// Abstand Text (unten) -> Sicherheitsrand in mm.
    pub text_unten_mm: f64,
    /// Stellen der Staerke-Felder: Fuehrer / Unterfuehrer / Helfer / Gesamt.
    pub staerke_stellen: [u32; 4],
    /// Untergrenze fuer die automatische Verkleinerung zu langer Texte in Punkt.
    pub min_schrift_pt: f64,
}

impl Default for TextOptionen {
    fn default() -> Self {
        Self {
            font_family: "Arial".into(),
            font_size_pt: 10.0,
            schrift_mitwachsen: true,
            zeilenabstand_faktor: 2.0,
            abstand_grafik_text_mm: 2.0,
            text_unten_mm: 0.0,
            staerke_stellen: [5, 6, 6, 3],
            min_schrift_pt: 8.0,
        }
    }
}

/// Linien (Schreiblinien, Platzhalter, Schnittlinien).
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct LinienOptionen {
    /// Strichstaerke der Schreiblinien in mm.
    pub schreiblinie_mm: f64,
    /// Abstand der Schreiblinien zum Bereichsrand in mm.
    pub schreiblinie_rand_mm: f64,
    /// Strichstaerke der Schnittlinien in mm.
    pub schnittlinie_mm: f64,
}

impl Default for LinienOptionen {
    fn default() -> Self {
        Self { schreiblinie_mm: 0.15, schreiblinie_rand_mm: 2.0, schnittlinie_mm: 0.15 }
    }
}

/// Optionen fuer Export-Formate.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct ExportOptionen {
    /// Aufloesung fuer PNG-Export.
    pub png_dpi: u32,
    /// PNG mit weissem statt transparentem Hintergrund.
    pub png_hintergrund_weiss: bool,
    /// Seitenrand Schnittbogen links/rechts in mm.
    pub bogen_rand_horizontal_mm: f64,
    /// Seitenrand Schnittbogen oben/unten in mm.
    pub bogen_rand_vertikal_mm: f64,
    /// Schnittlinien standardmaessig zeichnen.
    pub schnittlinien: bool,
    /// Text im PDF in Pfade umwandeln (true) oder Schrift einbetten (false).
    pub text_als_pfade: bool,
    /// Hinweistext "Tatsaechliche Groesse drucken" auf Schnittboegen.
    pub druckhinweis: bool,
}

impl Default for ExportOptionen {
    fn default() -> Self {
        Self {
            png_dpi: 300,
            png_hintergrund_weiss: false,
            bogen_rand_horizontal_mm: 8.0,
            bogen_rand_vertikal_mm: 8.0,
            schnittlinien: false,
            text_als_pfade: true,
            druckhinweis: true,
        }
    }
}

/// Gesamte Konfiguration eines Exports bzw. einer Vorschau.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct DruckConfig {
    pub layout: Layout,
    pub s2: Groesse,
    pub s1: S1Optionen,
    pub text: TextOptionen,
    pub linien: LinienOptionen,
    pub export: ExportOptionen,
    /// Maximale Grafikgroesse [Breite, Hoehe] in mm fuer alle Zeichen (`None` = so gross wie
    /// moeglich). Einzelne Zeichen koennen sie mit `ZeichenSpec::grafik_max_mm` ueberschreiben.
    pub grafik_max_mm: Option<[f64; 2]>,
}

impl Default for DruckConfig {
    fn default() -> Self {
        Self {
            layout: Layout::S2,
            s2: Groesse::default(),
            s1: S1Optionen::default(),
            text: TextOptionen::default(),
            linien: LinienOptionen::default(),
            export: ExportOptionen::default(),
            grafik_max_mm: None,
        }
    }
}

/// Grenzen fuer die Validierung (unveraenderlich).
pub mod grenzen {
    /// Zeichengroesse. Schnittboegen pruefen zusaetzlich, ob das Zeichen auf A4 passt.
    pub const GROESSE_MM: (f64, f64) = (10.0, 1000.0);
    pub const BESCHNITT_MM: (f64, f64) = (0.0, 10.0);
    pub const SICHERHEIT_MM: (f64, f64) = (0.0, 20.0);
    /// Schrift auf dem Zeichen: nie kleiner als 8 pt (Lesbarkeit).
    pub const FONT_PT: (f64, f64) = (8.0, 48.0);
    pub const LINKS_PROZENT: (f64, f64) = (20.0, 80.0);
    pub const SCHREIBLINIEN: (u32, u32) = (1, 15);
    pub const PNG_DPI: (u32, u32) = (72, 1200);
    pub const BOGEN_RAND_MM: (f64, f64) = (5.0, 40.0);
    pub const STAERKE_STELLEN: (u32, u32) = (1, 10);
    pub const GRAFIK_MAX_MM: (f64, f64) = (1.0, 280.0);
}

/// Bezugshoehe fuer die Schrift-Empfehlung: 47,5 mm -> 10 pt.
const SCHRIFT_BEZUG_HOEHE_MM: f64 = 47.5;
const SCHRIFT_BEZUG_PT: f64 = 10.0;
/// In diesem Hoehenbereich bleibt es bei 10 pt (uebliche Zeichengroessen 45-48 mm).
const SCHRIFT_STANDARD_BEREICH_MM: (f64, f64) = (45.0, 48.0);

/// Empfohlene Schriftgroesse fuer eine Zeichenhoehe (wie Version 0.8.x):
/// 45-48 mm -> 10 pt, sonst linear zu 47,5 mm, auf ganze pt gerundet, nie unter der Mindestschrift.
pub fn empfohlene_schrift_pt(hoehe_mm: f64) -> f64 {
    let (von, bis) = SCHRIFT_STANDARD_BEREICH_MM;
    let pt = if (von..=bis).contains(&hoehe_mm) {
        SCHRIFT_BEZUG_PT
    } else {
        (hoehe_mm / SCHRIFT_BEZUG_HOEHE_MM * SCHRIFT_BEZUG_PT).round()
    };
    pt.clamp(grenzen::FONT_PT.0, grenzen::FONT_PT.1)
}

impl DruckConfig {
    /// Aktive Zeichengroesse je nach Layout.
    pub fn groesse(&self) -> Groesse {
        match self.layout {
            Layout::S2 => self.s2,
            Layout::S1 => self.s1.groesse,
        }
    }

    /// Prueft alle Werte und liefert eine Liste lesbarer Fehlermeldungen.
    pub fn pruefe(&self) -> Vec<String> {
        let mut fehler = Vec::new();
        let mut bereich = |name: &str, wert: f64, (min, max): (f64, f64)| {
            if !(min..=max).contains(&wert) || wert.is_nan() {
                fehler.push(format!("{name}: {wert} liegt nicht zwischen {min} und {max}"));
            }
        };
        for (praefix, g) in [("S2", self.s2), ("S1", self.s1.groesse)] {
            bereich(&format!("{praefix} Hoehe (mm)"), g.hoehe_mm, grenzen::GROESSE_MM);
            bereich(&format!("{praefix} Breite (mm)"), g.breite_mm, grenzen::GROESSE_MM);
            bereich(&format!("{praefix} Beschnitt (mm)"), g.beschnitt_mm, grenzen::BESCHNITT_MM);
            bereich(
                &format!("{praefix} Sicherheitsabstand (mm)"),
                g.sicherheitsabstand_mm,
                grenzen::SICHERHEIT_MM,
            );
        }
        bereich("Schriftgroesse (pt)", self.text.font_size_pt, grenzen::FONT_PT);
        bereich("Mindest-Schriftgroesse (pt)", self.text.min_schrift_pt, grenzen::FONT_PT);
        bereich("S1 linker Anteil (%)", self.s1.links_prozent, grenzen::LINKS_PROZENT);
        bereich(
            "S1 Schreiblinien",
            self.s1.anzahl_schreiblinien as f64,
            (grenzen::SCHREIBLINIEN.0 as f64, grenzen::SCHREIBLINIEN.1 as f64),
        );
        bereich(
            "PNG-DPI",
            self.export.png_dpi as f64,
            (grenzen::PNG_DPI.0 as f64, grenzen::PNG_DPI.1 as f64),
        );
        bereich("Bogenrand horizontal (mm)", self.export.bogen_rand_horizontal_mm, grenzen::BOGEN_RAND_MM);
        bereich("Bogenrand vertikal (mm)", self.export.bogen_rand_vertikal_mm, grenzen::BOGEN_RAND_MM);
        for (i, stellen) in self.text.staerke_stellen.iter().enumerate() {
            bereich(
                &format!("Staerke-Feld {} (Stellen)", i + 1),
                *stellen as f64,
                (grenzen::STAERKE_STELLEN.0 as f64, grenzen::STAERKE_STELLEN.1 as f64),
            );
        }
        if let Some([w, h]) = self.grafik_max_mm {
            bereich("Max. Grafikbreite (mm)", w, grenzen::GRAFIK_MAX_MM);
            bereich("Max. Grafikhoehe (mm)", h, grenzen::GRAFIK_MAX_MM);
        }
        for (praefix, g) in [("S2", self.s2), ("S1", self.s1.groesse)] {
            if g.sicherheitsabstand_mm * 2.0 >= g.hoehe_mm.min(g.breite_mm) {
                fehler.push(format!("{praefix}: Sicherheitsabstand ist zu gross fuer die Zeichengroesse"));
            }
        }
        if self.text.font_family.trim().is_empty() {
            fehler.push("Schriftfamilie darf nicht leer sein".into());
        }
        fehler
    }

    /// Wie [`pruefe`](Self::pruefe), aber als `Result`.
    pub fn validiert(&self) -> Result<()> {
        let fehler = self.pruefe();
        if fehler.is_empty() {
            Ok(())
        } else {
            Err(Error::Config(fehler.join("; ")))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn recommended_font_size_like_legacy() {
        assert_eq!(empfohlene_schrift_pt(45.0), 10.0);
        assert_eq!(empfohlene_schrift_pt(48.0), 10.0);
        assert_eq!(empfohlene_schrift_pt(50.0), 11.0);
        assert_eq!(empfohlene_schrift_pt(60.0), 13.0);
        assert_eq!(empfohlene_schrift_pt(30.0), 8.0, "nie unter 8 pt");
        assert_eq!(empfohlene_schrift_pt(950.0), 48.0, "obere Grenze");
    }

    #[test]
    fn defaults_are_valid() {
        assert!(DruckConfig::default().pruefe().is_empty());
    }

    #[test]
    fn partial_json_uses_defaults() {
        let cfg: DruckConfig = serde_json::from_str(r#"{"s2": {"hoehe_mm": 60}}"#).unwrap();
        assert_eq!(cfg.s2.hoehe_mm, 60.0);
        assert_eq!(cfg.s2.breite_mm, 45.0);
        assert_eq!(cfg.text.font_size_pt, 10.0);
    }

    #[test]
    fn invalid_values_are_reported() {
        let mut cfg = DruckConfig::default();
        cfg.s2.hoehe_mm = 5.0;
        cfg.text.font_size_pt = 100.0;
        // Hoehe, Schriftgroesse und (Folgefehler) Sicherheitsabstand
        assert_eq!(cfg.pruefe().len(), 3);
    }
}
