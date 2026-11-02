//! Fehlertypen des Kerns.

use std::path::PathBuf;

/// Alle Fehler, die der Kern nach aussen gibt.
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("Datei konnte nicht gelesen werden: {path}: {source}")]
    Io {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },
    #[error("Ungueltige SVG-Vorlage {path}: {message}")]
    Svg { path: PathBuf, message: String },
    #[error("Ungueltiges Rasterbild {path}: {message}")]
    Raster { path: PathBuf, message: String },
    #[error("Nicht unterstuetztes Dateiformat: {0}")]
    UnsupportedFormat(PathBuf),
    #[error("Keine Schriftart gefunden fuer '{0}' (auch kein Fallback)")]
    FontMissing(String),
    #[error("Interner SVG-Fehler: {0}")]
    InternalSvg(String),
    #[error("PDF-Erzeugung fehlgeschlagen: {0}")]
    Pdf(String),
    #[error("PNG-Erzeugung fehlgeschlagen: {0}")]
    Png(String),
    #[error("Ungueltige Konfiguration: {0}")]
    Config(String),
    #[error("{} Vorlage(n) nicht lesbar - Export nicht moeglich:\n{}", .0.len(), .0.join("\n"))]
    Vorlagen(Vec<String>),
    #[error("Export abgebrochen")]
    Cancelled,
}

impl Error {
    pub(crate) fn io(path: impl Into<PathBuf>, source: std::io::Error) -> Self {
        Self::Io { path: path.into(), source }
    }
}

/// Kurzform fuer `Result<T, Error>`.
pub type Result<T> = std::result::Result<T, Error>;
