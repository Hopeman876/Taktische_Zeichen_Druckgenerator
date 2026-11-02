//! Datenordner (portable Ablage) und Log-Datei.
//!
//! Einstellungen und Logs liegen neben der EXE, damit die App portabel bleibt
//! (z.B. auf einem USB-Stick). Ist der Ordner schreibgeschuetzt (z.B. unter
//! "C:\Programme" nach einer Installation), wird der App-Datenordner des Benutzers genutzt.

use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

use log::{Level, LevelFilter, Log, Metadata, Record};

/// Unterordner fuer Log-Dateien.
pub const LOG_ORDNER: &str = "Logs";
/// So viele Tages-Logdateien werden aufbewahrt.
const MAX_LOG_DATEIEN: usize = 30;
/// Name der Testdatei fuer die Schreibpruefung.
const SCHREIBTEST_DATEI: &str = ".schreibtest";
/// Eigene Module (alles andere wird erst ab WARN protokolliert).
const EIGENE_MODULE: [&str; 2] = ["tz_core", "tz_app_lib"];

/// Waehlt den Datenordner: Ordner der EXE, falls beschreibbar, sonst `fallback`.
pub fn daten_ordner(basis: &Path, fallback: Option<PathBuf>) -> PathBuf {
    if ist_beschreibbar(basis) {
        return basis.to_path_buf();
    }
    match fallback {
        Some(f) if std::fs::create_dir_all(&f).is_ok() => f,
        _ => basis.to_path_buf(),
    }
}

fn ist_beschreibbar(ordner: &Path) -> bool {
    let test = ordner.join(SCHREIBTEST_DATEI);
    match File::create(&test) {
        Ok(_) => {
            let _ = std::fs::remove_file(&test);
            true
        }
        Err(_) => false,
    }
}

struct DateiLogger {
    datei: Mutex<File>,
}

impl Log for DateiLogger {
    fn enabled(&self, m: &Metadata) -> bool {
        let eigen = EIGENE_MODULE.iter().any(|p| m.target().starts_with(p));
        if eigen {
            m.level() <= Level::Info || cfg!(debug_assertions)
        } else {
            m.level() <= Level::Warn
        }
    }

    fn log(&self, r: &Record) {
        if !self.enabled(r.metadata()) {
            return;
        }
        let zeile = format!(
            "{} {:<5} {}: {}\n",
            chrono::Local::now().format("%Y-%m-%d %H:%M:%S"),
            r.level(),
            r.target(),
            r.args()
        );
        if let Ok(mut f) = self.datei.lock() {
            let _ = f.write_all(zeile.as_bytes());
        }
        if cfg!(debug_assertions) {
            eprint!("{zeile}");
        }
    }

    fn flush(&self) {
        if let Ok(mut f) = self.datei.lock() {
            let _ = f.flush();
        }
    }
}

/// Startet das Logging in `<daten>/Logs/JJJJ-MM-TT.log` und raeumt alte Dateien auf.
/// Gibt den Log-Ordner zurueck.
pub fn starte(daten: &Path) -> std::io::Result<PathBuf> {
    let ordner = daten.join(LOG_ORDNER);
    std::fs::create_dir_all(&ordner)?;
    let datei_pfad = ordner.join(format!("{}.log", chrono::Local::now().format("%Y-%m-%d")));
    let datei = OpenOptions::new().create(true).append(true).open(&datei_pfad)?;
    aufraeumen(&ordner);

    let logger = Box::new(DateiLogger { datei: Mutex::new(datei) });
    if log::set_boxed_logger(logger).is_ok() {
        log::set_max_level(LevelFilter::Debug);
    }
    // Abstuerze ebenfalls protokollieren
    let vorher = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        log::error!("Absturz: {info}");
        log::logger().flush();
        vorher(info);
    }));
    Ok(ordner)
}

/// Loescht die aeltesten Log-Dateien ueber `MAX_LOG_DATEIEN`.
fn aufraeumen(ordner: &Path) {
    let Ok(eintraege) = std::fs::read_dir(ordner) else {
        return;
    };
    let mut logs: Vec<PathBuf> = eintraege
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.extension().is_some_and(|e| e == "log"))
        .collect();
    // Dateinamen sind Datumsangaben -> alphabetisch = chronologisch
    logs.sort();
    let zu_viele = logs.len().saturating_sub(MAX_LOG_DATEIEN);
    for alt in logs.into_iter().take(zu_viele) {
        let _ = std::fs::remove_file(alt);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn writable_dir_is_preferred() {
        let dir = std::env::temp_dir().join("tz_protokoll_test");
        std::fs::create_dir_all(&dir).unwrap();
        assert_eq!(daten_ordner(&dir, Some(PathBuf::from("/gibt/es/nicht"))), dir);
    }
}
