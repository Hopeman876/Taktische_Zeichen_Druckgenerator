//! Vorlagen-Katalog: rekursives Einlesen des Vorlagenordners.
//!
//! Ordner = Kategorie, Unterordner = Unterkategorie. Erlaubt sind SVG, PNG und JPG.
//! Zusaetzlich gibt es die virtuelle Kategorie "Blanko-Zeichen".

use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Error, Result};

/// Erlaubte Dateiendungen (klein geschrieben).
pub const ERLAUBTE_ENDUNGEN: [&str; 4] = ["svg", "png", "jpg", "jpeg"];

/// Name der virtuellen Blanko-Kategorie.
pub const BLANKO_KATEGORIE: &str = "Blanko-Zeichen";

/// Varianten ohne Grafikvorlage.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BlankoArt {
    /// Leeres Schild (S2): keine Grafik, kein Text, keine Linien. Serde-Name "leer".
    Leer,
    /// S1: komplett leer (weder Text noch Linien).
    S1Leer,
    /// S1: beidseitig Schreiblinien, ohne Staerke.
    S1Linien,
    /// S1: beidseitig Schreiblinien, rechts mit Staerke.
    S1LinienStaerke,
}

impl BlankoArt {
    pub const ALLE: [BlankoArt; 4] =
        [BlankoArt::Leer, BlankoArt::S1Leer, BlankoArt::S1Linien, BlankoArt::S1LinienStaerke];

    pub fn label(self) -> &'static str {
        match self {
            BlankoArt::Leer => "S2 leer (Blankoschild)",
            BlankoArt::S1Leer => "S1 leer",
            BlankoArt::S1Linien => "S1 mit Linien",
            BlankoArt::S1LinienStaerke => "S1 mit Linien + Stärke",
        }
    }
}

/// Verweis auf eine Vorlage.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(tag = "art", rename_all = "snake_case")]
pub enum VorlageRef {
    /// Datei (absoluter Pfad).
    Datei { pfad: PathBuf },
    /// Virtuelle Blanko-Vorlage.
    Blanko { blanko: BlankoArt },
}

impl VorlageRef {
    /// Anzeigename bzw. Dateiname ohne Endung (fuer Modus "Dateiname").
    pub fn name(&self) -> String {
        match self {
            VorlageRef::Datei { pfad } => {
                pfad.file_stem().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default()
            }
            VorlageRef::Blanko { blanko } => blanko.label().to_string(),
        }
    }
}

/// Dateiformat einer Vorlage.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum VorlageFormat {
    Svg,
    Png,
    Jpg,
    Blanko,
}

/// Eintrag in der Vorlagenliste.
#[derive(Debug, Clone, Serialize)]
pub struct VorlageInfo {
    pub name: String,
    pub format: VorlageFormat,
    pub vorlage: VorlageRef,
}

/// Kategorie mit Unterkategorien.
#[derive(Debug, Clone, Serialize)]
pub struct Kategorie {
    pub name: String,
    /// Pfad relativ zum Vorlagenordner ("/"-getrennt), leer fuer die Wurzel.
    pub pfad: String,
    pub vorlagen: Vec<VorlageInfo>,
    pub unterkategorien: Vec<Kategorie>,
    /// Anzahl Vorlagen inkl. aller Unterkategorien.
    pub anzahl_gesamt: usize,
}

/// Liest den Vorlagenordner rekursiv ein. Versteckte Dateien/Ordner werden ignoriert.
pub fn scan(wurzel: &Path) -> Result<Kategorie> {
    if !wurzel.is_dir() {
        return Err(Error::io(
            wurzel,
            std::io::Error::new(std::io::ErrorKind::NotFound, "Vorlagenordner nicht gefunden"),
        ));
    }
    let name = wurzel.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
    scan_ordner(wurzel, wurzel, name)
}

fn scan_ordner(wurzel: &Path, ordner: &Path, name: String) -> Result<Kategorie> {
    let mut eintraege: Vec<_> = std::fs::read_dir(ordner)
        .map_err(|e| Error::io(ordner, e))?
        .filter_map(|e| e.ok())
        .filter(|e| !e.file_name().to_string_lossy().starts_with('.'))
        .collect();
    eintraege.sort_by_key(|e| e.file_name().to_string_lossy().to_lowercase());

    let mut vorlagen = Vec::new();
    let mut unterkategorien = Vec::new();
    for e in eintraege {
        let pfad = e.path();
        if pfad.is_dir() {
            let sub_name = e.file_name().to_string_lossy().into_owned();
            let sub = scan_ordner(wurzel, &pfad, sub_name)?;
            if sub.anzahl_gesamt > 0 {
                unterkategorien.push(sub);
            }
        } else if let Some(format) = format_von(&pfad) {
            vorlagen.push(VorlageInfo {
                name: pfad.file_stem().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default(),
                format,
                vorlage: VorlageRef::Datei { pfad: pfad.clone() },
            });
        }
    }
    let anzahl_gesamt = vorlagen.len() + unterkategorien.iter().map(|k| k.anzahl_gesamt).sum::<usize>();
    let rel = ordner.strip_prefix(wurzel).map(|p| p.to_string_lossy().replace('\\', "/")).unwrap_or_default();
    Ok(Kategorie { name, pfad: rel, vorlagen, unterkategorien, anzahl_gesamt })
}

/// Virtuelle Blanko-Kategorie.
pub fn blanko_kategorie() -> Kategorie {
    let vorlagen: Vec<_> = BlankoArt::ALLE
        .iter()
        .map(|b| VorlageInfo {
            name: b.label().to_string(),
            format: VorlageFormat::Blanko,
            vorlage: VorlageRef::Blanko { blanko: *b },
        })
        .collect();
    Kategorie {
        name: BLANKO_KATEGORIE.into(),
        pfad: String::new(),
        anzahl_gesamt: vorlagen.len(),
        vorlagen,
        unterkategorien: Vec::new(),
    }
}

/// Ermittelt das Format anhand der Endung.
pub fn format_von(pfad: &Path) -> Option<VorlageFormat> {
    let ext = pfad.extension()?.to_string_lossy().to_lowercase();
    match ext.as_str() {
        "svg" => Some(VorlageFormat::Svg),
        "png" => Some(VorlageFormat::Png),
        "jpg" | "jpeg" => Some(VorlageFormat::Jpg),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn scans_recursively_and_skips_empty() {
        let dir = tempfile::tempdir().unwrap();
        let root = dir.path();
        std::fs::create_dir_all(root.join("Einheiten/Trupps")).unwrap();
        std::fs::create_dir_all(root.join("Leer")).unwrap();
        std::fs::write(root.join("Einheiten/B.svg"), "<svg/>").unwrap();
        std::fs::write(root.join("Einheiten/a.png"), [0u8]).unwrap();
        std::fs::write(root.join("Einheiten/Trupps/T.svg"), "<svg/>").unwrap();
        std::fs::write(root.join("Einheiten/notiz.txt"), "x").unwrap();

        let k = scan(root).unwrap();
        assert_eq!(k.anzahl_gesamt, 3);
        assert_eq!(k.unterkategorien.len(), 1);
        let einheiten = &k.unterkategorien[0];
        assert_eq!(einheiten.name, "Einheiten");
        assert_eq!(einheiten.vorlagen.iter().map(|v| v.name.as_str()).collect::<Vec<_>>(), ["a", "B"]);
        assert_eq!(einheiten.unterkategorien[0].pfad, "Einheiten/Trupps");
    }
}
