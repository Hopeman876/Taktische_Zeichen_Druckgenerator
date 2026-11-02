//! Export-Auftraege: Grafiken laden, komponieren, Dateien schreiben.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::{Instant, SystemTime};

use rayon::prelude::*;
use serde::{Deserialize, Serialize};

use crate::compose::{compose, ComposeOptionen, Hinweis, Komposition, ZeichenSpec};
use crate::config::DruckConfig;
use crate::error::{Error, Result};
use crate::export::bogen::BogenLayout;
use crate::export::pdf::{PdfDokument, PdfOptionen, SeitenElement};
use crate::export::raster;
use crate::fonts::Fonts;
use crate::grafik::{self, Grafik};
use crate::katalog::VorlageRef;
use crate::svg::{Anker, Rgb, SvgBuilder};
use crate::units::pt_to_mm;

/// Programmname fuer PDF-Metadaten.
pub const PROGRAMM: &str = "Taktische Zeichen Druckgenerator";
/// Programmversion.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Hinweistext auf Schnittboegen.
const DRUCKHINWEIS: &str =
    "WICHTIG: In den Druckeinstellungen \"Tatsächliche Größe\" (100 %) wählen - NICHT skalieren!";
const HINWEIS_PT: f64 = 8.0;
const HINWEIS_RAND_MM: f64 = 2.0;
const HINWEIS_ZEILE_MM: f64 = 3.0;
const BOGEN_LINIE_PT: f32 = 0.5;

/// Ausgabeformat.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExportFormat {
    /// Ein PNG pro Zeichen (mit Beschnitt).
    Png,
    /// PDF, eine Seite pro Zeichen (mit Beschnitt, TrimBox = Endformat).
    PdfEinzel,
    /// PDF-Schnittbogen auf A4 (Zeichen in Endgroesse im Raster).
    PdfBogen,
}

impl ExportFormat {
    fn ordner_teile(self) -> (&'static str, &'static str) {
        match self {
            ExportFormat::Png => ("PNG", "Einzelzeichen"),
            ExportFormat::PdfEinzel => ("PDF", "Einzelzeichen"),
            ExportFormat::PdfBogen => ("PDF", "Schnittbogen"),
        }
    }
}

fn eins() -> u32 {
    1
}

/// Ein Zeichen im Auftrag inkl. Anzahl Kopien.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportPosten {
    #[serde(flatten)]
    pub zeichen: ZeichenSpec,
    #[serde(default = "eins")]
    pub kopien: u32,
}

/// Kompletter Export-Auftrag (auch als JSON fuer die CLI).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportAuftrag {
    pub posten: Vec<ExportPosten>,
    #[serde(default)]
    pub config: DruckConfig,
    pub format: ExportFormat,
    /// Basisordner; darin wird ein Unterordner mit Zeitstempel angelegt.
    pub ziel_ordner: PathBuf,
    /// Ueberschreibt `config.export.schnittlinien`.
    #[serde(default)]
    pub schnittlinien: Option<bool>,
    /// PDF auf mehrere Dateien aufteilen (Zeichen pro Datei). `None` = eine Datei.
    #[serde(default)]
    pub zeichen_pro_datei: Option<usize>,
}

/// Hinweis mit Zuordnung zum Zeichen.
#[derive(Debug, Clone, Serialize)]
pub struct ZeichenHinweis {
    pub position: usize,
    pub zeichen: String,
    pub hinweis: Hinweis,
}

/// Ergebnis eines Exports.
#[derive(Debug, Clone, Serialize)]
pub struct ExportBericht {
    pub ordner: PathBuf,
    pub dateien: Vec<PathBuf>,
    pub anzahl_zeichen: usize,
    pub anzahl_seiten: usize,
    pub hinweise: Vec<ZeichenHinweis>,
    /// Textdatei mit allen Hinweisen im Ausgabeordner (nur wenn es Hinweise gibt).
    pub bericht_datei: Option<PathBuf>,
    pub dauer_ms: u128,
}

/// Name der Hinweis-Datei im Ausgabeordner.
pub const BERICHT_DATEINAME: &str = "Hinweise.txt";

/// Fehlende Schriften einer Vorlage (Vorab-Pruefung vor dem Export).
#[derive(Debug, Clone, Serialize)]
pub struct SchriftProblem {
    pub vorlage: String,
    pub pfad: PathBuf,
    pub schriften: Vec<String>,
}

/// Ergebnis der Pruefung eines Auftragspostens (fuer Markierungen in der Oberflaeche).
#[derive(Debug, Clone, Serialize)]
pub struct PostenPruefung {
    /// Vorlage nicht lesbar o.ae. -> Export nicht moeglich.
    pub fehler: Option<String>,
    /// Hinweise zum Zeichen (ohne den fuer alle gleichen Schrift-Fallback).
    pub hinweise: Vec<Hinweis>,
}

/// Komponiert alle Zeichen probeweise und sammelt Fehler und Hinweise je Posten.
pub fn pruefe_auftrag(
    zeichen: &[ZeichenSpec],
    cfg: &DruckConfig,
    fonts: &Fonts,
    cache: &GrafikCache,
) -> Vec<PostenPruefung> {
    zeichen
        .par_iter()
        .map(|z| match komponiere(z, cfg, fonts, cache, ComposeOptionen::default()) {
            Ok(k) => PostenPruefung {
                fehler: None,
                hinweise: k
                    .hinweise
                    .into_iter()
                    .filter(|h| h.art != crate::compose::HinweisArt::SchriftFallback)
                    .collect(),
            },
            Err(e) => PostenPruefung { fehler: Some(e.to_string()), hinweise: Vec::new() },
        })
        .collect()
}

/// Prueft alle Datei-Vorlagen auf fehlende Schriften (jede Vorlage einmal).
/// Nicht ladbare Vorlagen werden hier uebersprungen; der Export meldet sie als Fehler.
pub fn pruefe_schriften(vorlagen: &[VorlageRef], fonts: &Fonts, cache: &GrafikCache) -> Vec<SchriftProblem> {
    let mut pfade: Vec<&PathBuf> = vorlagen
        .iter()
        .filter_map(|v| match v {
            VorlageRef::Datei { pfad } => Some(pfad),
            VorlageRef::Blanko { .. } => None,
        })
        .collect();
    pfade.sort();
    pfade.dedup();
    pfade
        .par_iter()
        .filter_map(|pfad| {
            let g = cache.hole(pfad, fonts).ok()?;
            if g.fehlende_schriften.is_empty() {
                return None;
            }
            Some(SchriftProblem {
                vorlage: VorlageRef::Datei { pfad: (*pfad).clone() }.name(),
                pfad: (*pfad).clone(),
                schriften: g.fehlende_schriften.clone(),
            })
        })
        .collect()
}

/// Schreibt die Hinweise als lesbare Textdatei.
fn schreibe_bericht(ordner: &Path, hinweise: &[ZeichenHinweis], zeitpunkt: &str) -> Result<PathBuf> {
    use std::fmt::Write;
    let mut text = String::new();
    let _ = writeln!(text, "{PROGRAMM} {VERSION} - Hinweise zum Export vom {zeitpunkt}");
    let _ = writeln!(text, "Position = Zeile im Auftrag\n");
    for h in hinweise {
        let _ = writeln!(text, "#{:<4} {:<40} {}", h.position, h.zeichen, h.hinweis.text);
    }
    let pfad = ordner.join(BERICHT_DATEINAME);
    std::fs::write(&pfad, text).map_err(|e| Error::io(&pfad, e))?;
    Ok(pfad)
}

/// Fortschrittsmeldung und Abbruch.
pub trait Fortschritt: Sync {
    fn melde(&self, _fertig: usize, _gesamt: usize, _schritt: &str) {}
    fn abgebrochen(&self) -> bool {
        false
    }
}

/// Ohne Rueckmeldung.
pub struct KeinFortschritt;
impl Fortschritt for KeinFortschritt {}

/// Aenderungszeit der Datei + geladene Grafik.
type CacheEintrag = (Option<SystemTime>, Arc<Grafik>);

/// Cache geladener Vorlagen (Schluessel: Pfad + Aenderungszeit).
#[derive(Default)]
pub struct GrafikCache {
    map: Mutex<HashMap<PathBuf, CacheEintrag>>,
}

impl GrafikCache {
    pub fn new() -> Self {
        Self::default()
    }

    /// Laedt die Vorlage oder liefert sie aus dem Cache.
    pub fn hole(&self, pfad: &Path, fonts: &Fonts) -> Result<Arc<Grafik>> {
        let mtime = std::fs::metadata(pfad).and_then(|m| m.modified()).ok();
        if let Some((t, g)) = self.map.lock().expect("Cache-Lock").get(pfad) {
            if *t == mtime {
                return Ok(g.clone());
            }
        }
        let g = grafik::lade(pfad, fonts)?;
        self.map.lock().expect("Cache-Lock").insert(pfad.to_path_buf(), (mtime, g.clone()));
        Ok(g)
    }

    pub fn leeren(&self) {
        self.map.lock().expect("Cache-Lock").clear();
    }
}

/// Komponiert ein einzelnes Zeichen (laedt die Grafik bei Bedarf).
pub fn komponiere(
    spec: &ZeichenSpec,
    cfg: &DruckConfig,
    fonts: &Fonts,
    cache: &GrafikCache,
    opt: ComposeOptionen,
) -> Result<Komposition> {
    let grafik = match &spec.vorlage {
        VorlageRef::Datei { pfad } => Some(cache.hole(pfad, fonts)?),
        VorlageRef::Blanko { .. } => None,
    };
    compose(spec, grafik, cfg, fonts, opt)
}

/// Fuehrt einen Export aus.
pub fn exportiere(
    auftrag: &ExportAuftrag,
    fonts: &Fonts,
    cache: &GrafikCache,
    fortschritt: &dyn Fortschritt,
) -> Result<ExportBericht> {
    let start = Instant::now();
    log::info!(
        "Export gestartet: {:?}, {} Positionen, Ziel {}",
        auftrag.format,
        auftrag.posten.len(),
        auftrag.ziel_ordner.display()
    );
    let cfg = &auftrag.config;
    cfg.validiert()?;
    if auftrag.posten.is_empty() {
        return Err(Error::Config("Keine Zeichen ausgewaehlt".into()));
    }
    let schnittlinien = auftrag.schnittlinien.unwrap_or(cfg.export.schnittlinien);
    let anzahl_zeichen: usize = auftrag.posten.iter().map(|p| p.kopien.max(1) as usize).sum();
    let gesamt_schritte = auftrag.posten.len() * 2;

    // 1) Komponieren (parallel). Auf Schnittboegen keine Einzelzeichen-Schnittlinien.
    let opt = ComposeOptionen { schnittlinien: schnittlinien && auftrag.format != ExportFormat::PdfBogen };
    let fertig = std::sync::atomic::AtomicUsize::new(0);
    let ergebnisse: Vec<Result<Komposition>> = auftrag
        .posten
        .par_iter()
        .map(|p| {
            if fortschritt.abgebrochen() {
                return Err(Error::Cancelled);
            }
            let k = komponiere(&p.zeichen, cfg, fonts, cache, opt);
            let n = fertig.fetch_add(1, std::sync::atomic::Ordering::Relaxed) + 1;
            fortschritt.melde(
                n,
                gesamt_schritte,
                &format!("Zeichen vorbereitet: {}", p.zeichen.vorlage.name()),
            );
            k
        })
        .collect();
    // Alle nicht lesbaren Vorlagen auf einmal melden (nicht nur die erste)
    let mut kompositionen = Vec::with_capacity(ergebnisse.len());
    let mut probleme = Vec::new();
    for (i, r) in ergebnisse.into_iter().enumerate() {
        match r {
            Ok(k) => kompositionen.push(k),
            Err(Error::Cancelled) => return Err(Error::Cancelled),
            Err(e) => probleme.push(format!("#{} {}: {e}", i + 1, auftrag.posten[i].zeichen.vorlage.name())),
        }
    }
    if !probleme.is_empty() {
        return Err(Error::Vorlagen(probleme));
    }

    let hinweise: Vec<ZeichenHinweis> = kompositionen
        .iter()
        .zip(&auftrag.posten)
        .enumerate()
        .flat_map(|(i, (k, p))| {
            k.hinweise.iter().map(move |h| ZeichenHinweis {
                position: i + 1,
                zeichen: p.zeichen.vorlage.name(),
                hinweis: h.clone(),
            })
        })
        .collect();
    // Schrift-Fallback betrifft alle Zeichen gleich -> nur einmal melden
    let mut fallback_gemeldet = false;
    let hinweise: Vec<ZeichenHinweis> = hinweise
        .into_iter()
        .filter(|h| {
            if h.hinweis.art != crate::compose::HinweisArt::SchriftFallback {
                return true;
            }
            !std::mem::replace(&mut fallback_gemeldet, true)
        })
        .collect();

    // 2) Zielordner
    let jetzt = chrono::Local::now();
    let zeitstempel = jetzt.format("%Y-%m-%d_%H-%M").to_string();
    let (dateiformat, exportformat) = auftrag.format.ordner_teile();
    let aufloesung = match auftrag.format {
        ExportFormat::Png => format!("{}_dpi", cfg.export.png_dpi),
        _ => "Vektor".to_string(),
    };
    let ordner = eindeutiger_ordner(
        &auftrag.ziel_ordner,
        &format!("{zeitstempel}_{dateiformat}_{exportformat}_{anzahl_zeichen}_Zeichen_{aufloesung}"),
    );
    std::fs::create_dir_all(&ordner).map_err(|e| Error::io(&ordner, e))?;

    // 3) Schreiben
    let basis = auftrag.posten.len();
    let melde_schreiben = |n: usize, text: &str| fortschritt.melde(basis + n, gesamt_schritte, text);
    let (dateien, anzahl_seiten) = match auftrag.format {
        ExportFormat::Png => {
            let dpi = cfg.export.png_dpi as f64;
            let fertig = std::sync::atomic::AtomicUsize::new(0);
            let dateien: Vec<PathBuf> = kompositionen
                .par_iter()
                .zip(&auftrag.posten)
                .enumerate()
                .map(|(i, (k, p))| {
                    if fortschritt.abgebrochen() {
                        return Err(Error::Cancelled);
                    }
                    let hintergrund = cfg.export.png_hintergrund_weiss.then_some([255, 255, 255]);
                    let pixmap = raster::rendere(k, fonts, dpi, hintergrund)?;
                    let bytes = raster::png_bytes(&pixmap, dpi)?;
                    // Jede Kopie als eigene Datei; bei mehreren Kopien mit Zaehler
                    let kopien = p.kopien.max(1);
                    let basis = format!("{:03}_{}", i + 1, dateiname(&p.zeichen.vorlage.name()));
                    let mut pfade = Vec::with_capacity(kopien as usize);
                    for nr in 1..=kopien {
                        let name =
                            if kopien == 1 { format!("{basis}.png") } else { format!("{basis}_{nr}.png") };
                        let pfad = ordner.join(name);
                        std::fs::write(&pfad, &bytes).map_err(|e| Error::io(&pfad, e))?;
                        pfade.push(pfad);
                    }
                    let n = fertig.fetch_add(1, std::sync::atomic::Ordering::Relaxed) + 1;
                    melde_schreiben(n, "PNG geschrieben");
                    Ok(pfade)
                })
                .collect::<Result<Vec<Vec<PathBuf>>>>()?
                .into_iter()
                .flatten()
                .collect();
            let n = dateien.len();
            (dateien, n)
        }
        ExportFormat::PdfEinzel | ExportFormat::PdfBogen => {
            // Kopien ausmultiplizieren (jede Seite referenziert dieselben XObjects)
            let liste: Vec<&Komposition> = kompositionen
                .iter()
                .zip(&auftrag.posten)
                .flat_map(|(k, p)| std::iter::repeat_n(k, p.kopien.max(1) as usize))
                .collect();
            let pro_datei = auftrag.zeichen_pro_datei.filter(|n| *n > 0).unwrap_or(liste.len());
            let teile: Vec<&[&Komposition]> = liste.chunks(pro_datei).collect();
            let mut dateien = Vec::new();
            let mut seiten = 0;
            for (idx, teil) in teile.iter().enumerate() {
                if fortschritt.abgebrochen() {
                    return Err(Error::Cancelled);
                }
                let von = idx * pro_datei + 1;
                let bis = von + teil.len() - 1;
                let titel = format!("Taktische Zeichen - {exportformat} ({von} bis {bis})");
                let mut doc = PdfDokument::new(
                    fonts,
                    PdfOptionen {
                        titel,
                        ersteller: format!("{PROGRAMM} {VERSION}"),
                        text_als_pfade: cfg.export.text_als_pfade,
                    },
                );
                if auftrag.format == ExportFormat::PdfEinzel {
                    schreibe_einzel(&mut doc, teil)?;
                } else {
                    schreibe_bogen(&mut doc, teil, cfg, fonts, schnittlinien)?;
                }
                seiten += doc.anzahl_seiten();
                let name = format!(
                    "{zeitstempel}_{exportformat}_Zeichen_{von}_bis_{bis}_Datei_{}_von_{}.pdf",
                    idx + 1,
                    teile.len()
                );
                let pfad = ordner.join(name);
                std::fs::write(&pfad, doc.finish()).map_err(|e| Error::io(&pfad, e))?;
                melde_schreiben(
                    (idx + 1) * basis / teile.len(),
                    &format!("PDF {} von {} geschrieben", idx + 1, teile.len()),
                );
                dateien.push(pfad);
            }
            (dateien, seiten)
        }
    };

    let bericht_datei = if hinweise.is_empty() {
        None
    } else {
        Some(schreibe_bericht(&ordner, &hinweise, &jetzt.format("%d.%m.%Y %H:%M").to_string())?)
    };
    let dauer_ms = start.elapsed().as_millis();
    log::info!(
        "Export fertig: {anzahl_zeichen} Zeichen, {anzahl_seiten} Seiten/Dateien, {} Hinweise, {dauer_ms} ms -> {}",
        hinweise.len(),
        ordner.display()
    );
    Ok(ExportBericht { ordner, dateien, anzahl_zeichen, anzahl_seiten, hinweise, bericht_datei, dauer_ms })
}

fn schreibe_einzel(doc: &mut PdfDokument, liste: &[&Komposition]) -> Result<()> {
    // Alle Quellen einmal parallel umwandeln, danach Seiten anhaengen.
    let elemente: Vec<SeitenElement> =
        liste.iter().map(|k| SeitenElement::Zeichen { k, x: 0.0, y: 0.0, zuschnitt: None }).collect();
    doc.vorbereiten(elemente.iter())?;
    for k in liste {
        let d = k.geometrie.datei;
        doc.seite(
            d.w,
            d.h,
            Some(k.geometrie.schnitt),
            &[SeitenElement::Zeichen { k, x: 0.0, y: 0.0, zuschnitt: None }],
        )?;
    }
    Ok(())
}

fn schreibe_bogen(
    doc: &mut PdfDokument,
    liste: &[&Komposition],
    cfg: &DruckConfig,
    fonts: &Fonts,
    schnittlinien: bool,
) -> Result<()> {
    let layout = BogenLayout::berechne(cfg)?;
    let hinweis_svg = if cfg.export.druckhinweis {
        Some(druckhinweis_svg(layout.seite_w_mm, layout.seite_h_mm, cfg, fonts)?)
    } else {
        None
    };
    let alle: Vec<SeitenElement> =
        liste.iter().map(|k| SeitenElement::Zeichen { k, x: 0.0, y: 0.0, zuschnitt: None }).collect();
    doc.vorbereiten(alle.iter())?;

    for seite in liste.chunks(layout.pro_seite()) {
        let mut elemente = Vec::new();
        if let Some(svg) = &hinweis_svg {
            elemente.push(SeitenElement::SvgSeite { svg });
        }
        for (i, k) in seite.iter().enumerate() {
            let (px, py) = layout.position(i);
            let s = k.geometrie.schnitt;
            // Datei so verschieben, dass der Schnittbereich auf dem Rasterplatz liegt
            elemente.push(SeitenElement::Zeichen { k, x: px - s.x, y: py - s.y, zuschnitt: Some(s) });
            let platz = crate::geometry::Rect::new(px, py, s.w, s.h);
            elemente.push(SeitenElement::Rahmen { r: platz, rgb: [0.0, 0.0, 1.0], dicke_pt: BOGEN_LINIE_PT });
            if schnittlinien {
                let g = cfg.groesse();
                elemente.push(SeitenElement::Rahmen {
                    r: platz.inset(g.sicherheitsabstand_mm),
                    rgb: [0.0, 0.67, 0.0],
                    dicke_pt: BOGEN_LINIE_PT,
                });
            }
        }
        doc.seite(layout.seite_w_mm, layout.seite_h_mm, None, &elemente)?;
    }
    Ok(())
}

/// Hinweistext oben und unten auf der Seite (im nicht bedruckten Randbereich).
fn druckhinweis_svg(w: f64, h: f64, cfg: &DruckConfig, fonts: &Fonts) -> Result<String> {
    let face = fonts.resolve(&cfg.text.font_family)?;
    let size = pt_to_mm(HINWEIS_PT);
    let version = format!("Erstellt mit dem {PROGRAMM} v{VERSION}");
    let mut b = SvgBuilder::new(w, h);
    let oben1 = HINWEIS_RAND_MM + face.ascender * size;
    let unten2 = h - HINWEIS_RAND_MM;
    for (y, text) in [
        (oben1, DRUCKHINWEIS),
        (oben1 + HINWEIS_ZEILE_MM, version.as_str()),
        (unten2 - HINWEIS_ZEILE_MM, DRUCKHINWEIS),
        (unten2, version.as_str()),
    ] {
        b.text(w / 2.0, y, text, &face.family, size, Rgb::HINWEIS, Anker::Mitte, None);
    }
    Ok(b.finish())
}

/// Dateiname ohne problematische Zeichen.
fn dateiname(name: &str) -> String {
    let s: String =
        name.chars().map(|c| if c.is_alphanumeric() || c == '-' || c == '_' { c } else { '_' }).collect();
    if s.is_empty() {
        "Zeichen".into()
    } else {
        s
    }
}

fn eindeutiger_ordner(basis: &Path, name: &str) -> PathBuf {
    let mut pfad = basis.join(name);
    let mut n = 2;
    while pfad.exists() {
        pfad = basis.join(format!("{name}_{n}"));
        n += 1;
    }
    pfad
}
