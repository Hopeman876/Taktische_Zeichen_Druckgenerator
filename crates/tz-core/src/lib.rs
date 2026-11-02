//! Rendering-Kern des Taktische Zeichen Druckgenerators.
//!
//! Pipeline (alles vektoriell, Raster nur beim PNG-Export):
//!
//! ```text
//! Vorlage (SVG / Pseudo-SVG / PNG / Blanko)
//!     -> grafik::Grafik          (usvg-Baum + Inhalts-Bounding-Box, Whitespace getrimmt)
//! Zeichen-Parameter + DruckConfig
//!     -> compose::compose()      (Geometrie, Text-Layout -> Overlay-SVG)
//!     -> export::pdf / png       (svg2pdf-Vektor-PDF, resvg-PNG)
//! ```
//!
//! Die Grafik und die Beschriftung bleiben getrennte Ebenen. Dadurch funktionieren
//! auch Vorlagen, die selbst Rasterbilder enthalten (usvg verbietet Bilder in
//! verschachtelten SVG-Bildern), und identische Grafiken werden im PDF nur einmal
//! eingebettet.

pub mod compose;
pub mod config;
pub mod error;
pub mod export;
pub mod fonts;
pub mod geometry;
pub mod grafik;
pub mod job;
pub mod katalog;
pub mod modus;
pub mod svg;
pub mod units;

pub use config::DruckConfig;
pub use error::{Error, Result};
pub use modus::Modus;
