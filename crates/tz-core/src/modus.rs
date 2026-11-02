//! Text-Modi (Single Source of Truth fuer Labels, Platzhalter und interne Namen).
//!
//! Die Oberflaeche holt die Liste ueber das Tauri-Kommando `modi` und haelt
//! selbst keine Labels vor.

use serde::{Deserialize, Serialize};

/// Text-Modus eines Zeichens. Die serde-Namen entsprechen den internen Werten
/// der Python-Version, damit alte Sessions importiert werden koennen.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Modus {
    OvStaerke,
    OrtStaerke,
    SchreiblinieStaerke,
    #[default]
    Freitext,
    Ruf,
    Dateiname,
    #[serde(alias = "nur_grafik")]
    OhneText,
}

/// Beschreibung eines Modus fuer die Oberflaeche.
#[derive(Debug, Clone, Serialize)]
pub struct ModusInfo {
    pub id: Modus,
    pub label: &'static str,
    pub platzhalter: &'static str,
    /// Ob der Modus ein Texteingabefeld hat.
    pub hat_text: bool,
}

impl Modus {
    /// Alle Modi in Anzeige-Reihenfolge.
    pub const ALLE: [Modus; 7] = [
        Modus::OvStaerke,
        Modus::OrtStaerke,
        Modus::SchreiblinieStaerke,
        Modus::Freitext,
        Modus::Ruf,
        Modus::Dateiname,
        Modus::OhneText,
    ];

    /// Anzeige-Label (Umlaute erlaubt, da UI-Text).
    pub fn label(self) -> &'static str {
        match self {
            Modus::OvStaerke => "OV + Stärke",
            Modus::OrtStaerke => "Ort + Stärke",
            Modus::SchreiblinieStaerke => "Schreiblinie + Stärke",
            Modus::Freitext => "Schreiblinie oder Freitext",
            Modus::Ruf => "Ruf",
            Modus::Dateiname => "Dateiname",
            Modus::OhneText => "Nur Grafik",
        }
    }

    /// Platzhalter fuer das Texteingabefeld.
    pub fn platzhalter(self) -> &'static str {
        match self {
            Modus::OvStaerke => "OV-Name",
            Modus::OrtStaerke => "Ortsname",
            Modus::SchreiblinieStaerke => "",
            Modus::Freitext => "Freitext (leer = Schreiblinie)",
            Modus::Ruf => "Rufname",
            Modus::Dateiname => "Dateiname (automatisch)",
            Modus::OhneText => "",
        }
    }

    /// Ob der Modus einen frei eingebbaren Text verwendet.
    pub fn hat_text(self) -> bool {
        !matches!(self, Modus::SchreiblinieStaerke | Modus::OhneText)
    }

    /// Ob der Modus eine Staerke-Zeile enthaelt.
    pub fn hat_staerke(self) -> bool {
        matches!(self, Modus::OvStaerke | Modus::OrtStaerke | Modus::SchreiblinieStaerke)
    }

    /// Beschreibung fuer die Oberflaeche.
    pub fn info(self) -> ModusInfo {
        ModusInfo {
            id: self,
            label: self.label(),
            platzhalter: self.platzhalter(),
            hat_text: self.hat_text(),
        }
    }
}

/// Vertikale Position der Grafik im Modus "Nur Grafik".
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum GrafikPosition {
    #[serde(alias = "top", alias = "oben")]
    Oben,
    #[default]
    #[serde(alias = "center", alias = "mittig")]
    Mittig,
    #[serde(alias = "bottom", alias = "unten")]
    Unten,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn serde_names_match_python_version() {
        let m: Modus = serde_json::from_str("\"ov_staerke\"").unwrap();
        assert_eq!(m, Modus::OvStaerke);
        let m: Modus = serde_json::from_str("\"ohne_text\"").unwrap();
        assert_eq!(m, Modus::OhneText);
        let p: GrafikPosition = serde_json::from_str("\"top\"").unwrap();
        assert_eq!(p, GrafikPosition::Oben);
    }
}
