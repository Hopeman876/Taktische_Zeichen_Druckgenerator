//! Tauri-Backend: duenne Schicht zwischen Oberflaeche (Svelte) und `tz-core`.
//!
//! Alle rechenintensiven Kommandos laufen ueber `spawn_blocking`, damit die
//! Oberflaeche nie blockiert.

mod protokoll;

use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, OnceLock};

use base64::Engine;
use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Emitter, Manager, State};

use tz_core::compose::{ComposeOptionen, Hinweis, ZeichenSpec};
use tz_core::config::DruckConfig;
use tz_core::export::bogen::BogenLayout;
use tz_core::export::raster;
use tz_core::fonts::Fonts;
use tz_core::job::{
    self, ExportAuftrag, ExportBericht, ExportFormat, Fortschritt, GrafikCache, PostenPruefung,
    SchriftProblem,
};
use tz_core::katalog::{self, Kategorie, VorlageRef};
use tz_core::modus::{Modus, ModusInfo};

/// Standard-Ordnernamen (kompatibel zur portablen Python-Version).
const VORLAGEN_ORDNER: &str = "Taktische_Zeichen_Grafikvorlagen";
const AUSGABE_ORDNER: &str = "Taktische_Zeichen_Ausgabe";
const SCHRIFTEN_ORDNER: &str = "fonts";
const EINSTELLUNGEN_DATEI: &str = "settings.json";
const FORTSCHRITT_EVENT: &str = "export-fortschritt";

/// Gemeinsamer Zustand.
struct AppState {
    basis: PathBuf,
    /// Ablage fuer settings.json und Logs (neben der EXE oder Fallback), gesetzt in `setup`.
    daten: OnceLock<PathBuf>,
    fonts: Arc<OnceLock<Fonts>>,
    cache: Arc<GrafikCache>,
    abbruch: Arc<AtomicBool>,
}

impl AppState {
    fn daten(&self) -> PathBuf {
        self.daten.get().cloned().unwrap_or_else(|| self.basis.clone())
    }

    fn fonts(&self) -> Fonts {
        let basis = self.basis.clone();
        self.fonts.get_or_init(|| Fonts::system_mit_ordner(&basis.join(SCHRIFTEN_ORDNER))).clone()
    }
}

/// Persistente App-Einstellungen.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(default)]
struct AppEinstellungen {
    config: DruckConfig,
    vorlagen_ordner: Option<PathBuf>,
    ausgabe_ordner: Option<PathBuf>,
    export_format: Option<ExportFormat>,
    standard_modus: Modus,
    oberflaeche: Oberflaeche,
    /// Einfuehrungstour wurde gesehen (startet dann nicht mehr automatisch).
    tour_gesehen: bool,
}

/// Vom Benutzer gezogene Bereichsgroessen (Werte werden in der Oberflaeche begrenzt).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
struct Oberflaeche {
    /// Breite der Kategorienspalte in px.
    kategorien_px: f64,
    /// Breite der Vorschau in px.
    vorschau_px: f64,
    /// Anteil der Vorlagen an der Hoehe der Mitte (0..1).
    vorlagen_anteil: f64,
    /// Kachelbreite der Vorlagen-Miniaturen in px (Zoom).
    vorlagen_zoom: f64,
}

impl Default for Oberflaeche {
    fn default() -> Self {
        Self { kategorien_px: 240.0, vorschau_px: 400.0, vorlagen_anteil: 0.5, vorlagen_zoom: 104.0 }
    }
}

#[derive(Serialize)]
struct AppInfo {
    version: &'static str,
    programm: &'static str,
    autoren: &'static str,
    lizenz: &'static str,
    modi: Vec<ModusInfo>,
    blanko: Kategorie,
    standard_vorlagen_ordner: PathBuf,
    standard_ausgabe_ordner: PathBuf,
    werkseinstellungen: DruckConfig,
    /// Ordner mit settings.json und Logs.
    daten_ordner: PathBuf,
    /// Standard-Bereichsgroessen (fuer "Ansicht zuruecksetzen").
    standard_oberflaeche: Oberflaeche,
}

#[derive(Serialize)]
struct VorschauAntwort {
    /// PNG als Data-URL.
    bild: String,
    hinweise: Vec<Hinweis>,
    breite_mm: f64,
    hoehe_mm: f64,
    /// Text passt nicht in 2 Zeilen, eine 3. Zeile waere moeglich.
    dritte_zeile_moeglich: bool,
}

type CmdResult<T> = Result<T, String>;

fn fehler(e: impl std::fmt::Display) -> String {
    let text = e.to_string();
    log::error!("{text}");
    text
}

fn data_url(png: &[u8]) -> String {
    format!("data:image/png;base64,{}", base64::engine::general_purpose::STANDARD.encode(png))
}

async fn blocking<T: Send + 'static>(f: impl FnOnce() -> CmdResult<T> + Send + 'static) -> CmdResult<T> {
    tauri::async_runtime::spawn_blocking(f).await.map_err(fehler)?
}

fn einstellungen_pfad(state: &AppState) -> PathBuf {
    state.daten().join(EINSTELLUNGEN_DATEI)
}

// ---------------------------------------------------------------------------------------------
// Kommandos
// ---------------------------------------------------------------------------------------------

#[tauri::command]
fn app_info(state: State<'_, AppState>) -> AppInfo {
    AppInfo {
        version: job::VERSION,
        programm: job::PROGRAMM,
        autoren: env!("CARGO_PKG_AUTHORS"),
        lizenz: env!("CARGO_PKG_LICENSE"),
        modi: Modus::ALLE.iter().map(|m| m.info()).collect(),
        blanko: katalog::blanko_kategorie(),
        standard_vorlagen_ordner: state.basis.join(VORLAGEN_ORDNER),
        standard_ausgabe_ordner: state.basis.join(AUSGABE_ORDNER),
        werkseinstellungen: DruckConfig::default(),
        daten_ordner: state.daten(),
        standard_oberflaeche: Oberflaeche::default(),
    }
}

#[tauri::command]
fn einstellungen_laden(state: State<'_, AppState>) -> CmdResult<AppEinstellungen> {
    let pfad = einstellungen_pfad(&state);
    match std::fs::read_to_string(&pfad) {
        Ok(text) => Ok(serde_json::from_str(&text).unwrap_or_else(|e| {
            log::warn!("settings.json unlesbar ({e}), verwende Werkseinstellungen");
            AppEinstellungen::default()
        })),
        Err(_) => Ok(AppEinstellungen::default()),
    }
}

#[tauri::command]
fn einstellungen_speichern(state: State<'_, AppState>, einstellungen: AppEinstellungen) -> CmdResult<()> {
    let pfad = einstellungen_pfad(&state);
    if let Some(dir) = pfad.parent() {
        std::fs::create_dir_all(dir).map_err(fehler)?;
    }
    let text = serde_json::to_string_pretty(&einstellungen).map_err(fehler)?;
    std::fs::write(&pfad, text).map_err(fehler)
}

#[tauri::command]
fn config_pruefen(config: DruckConfig) -> Vec<String> {
    config.pruefe()
}

#[tauri::command]
fn bogen_layout(config: DruckConfig) -> CmdResult<BogenLayout> {
    BogenLayout::berechne(&config).map_err(fehler)
}

#[tauri::command]
async fn katalog_laden(ordner: PathBuf) -> CmdResult<Kategorie> {
    blocking(move || katalog::scan(&ordner).map_err(fehler)).await
}

#[tauri::command]
async fn schriften(state: State<'_, AppState>) -> CmdResult<Vec<String>> {
    let fonts_lock = state.fonts.clone();
    let basis = state.basis.clone();
    blocking(move || {
        Ok(fonts_lock.get_or_init(|| Fonts::system_mit_ordner(&basis.join(SCHRIFTEN_ORDNER))).familien())
    })
    .await
}

#[tauri::command]
async fn vorschau(
    state: State<'_, AppState>,
    zeichen: ZeichenSpec,
    config: DruckConfig,
    schnittlinien: bool,
    max_px: u32,
) -> CmdResult<VorschauAntwort> {
    let fonts = state.fonts();
    let cache = state.cache.clone();
    blocking(move || {
        let k = job::komponiere(&zeichen, &config, &fonts, &cache, ComposeOptionen { schnittlinien })
            .map_err(fehler)?;
        let png = raster::vorschau(&k, &fonts, max_px.clamp(64, 2400)).map_err(fehler)?;
        Ok(VorschauAntwort {
            bild: data_url(&png),
            hinweise: k.hinweise,
            breite_mm: k.geometrie.datei.w,
            hoehe_mm: k.geometrie.datei.h,
            dritte_zeile_moeglich: k.dritte_zeile_moeglich,
        })
    })
    .await
}

#[tauri::command]
async fn miniatur(state: State<'_, AppState>, pfad: PathBuf, max_px: u32) -> CmdResult<String> {
    let fonts = state.fonts();
    let cache = state.cache.clone();
    blocking(move || {
        let g = cache.hole(&pfad, &fonts).map_err(fehler)?;
        raster::miniatur(&g, max_px.clamp(16, 512)).map(|p| data_url(&p)).map_err(fehler)
    })
    .await
}

/// Meldet den Export-Fortschritt als Event an die Oberflaeche.
struct EventFortschritt {
    app: AppHandle,
    abbruch: Arc<AtomicBool>,
}

#[derive(Clone, Serialize)]
struct FortschrittEvent {
    fertig: usize,
    gesamt: usize,
    schritt: String,
}

impl Fortschritt for EventFortschritt {
    fn melde(&self, fertig: usize, gesamt: usize, schritt: &str) {
        let _ =
            self.app.emit(FORTSCHRITT_EVENT, FortschrittEvent { fertig, gesamt, schritt: schritt.into() });
    }

    fn abgebrochen(&self) -> bool {
        self.abbruch.load(Ordering::Relaxed)
    }
}

#[tauri::command]
async fn exportieren(
    app: AppHandle,
    state: State<'_, AppState>,
    auftrag: ExportAuftrag,
) -> CmdResult<ExportBericht> {
    let fonts = state.fonts();
    let cache = state.cache.clone();
    let abbruch = state.abbruch.clone();
    abbruch.store(false, Ordering::Relaxed);
    blocking(move || {
        let fortschritt = EventFortschritt { app, abbruch };
        job::exportiere(&auftrag, &fonts, &cache, &fortschritt).map_err(fehler)
    })
    .await
}

/// Prueft alle Zeichen des Auftrags (lesbar? Hinweise?) fuer die Markierungen in der Liste.
#[tauri::command]
async fn auftrag_pruefen(
    state: State<'_, AppState>,
    zeichen: Vec<ZeichenSpec>,
    config: DruckConfig,
) -> CmdResult<Vec<PostenPruefung>> {
    let fonts = state.fonts();
    let cache = state.cache.clone();
    blocking(move || Ok(job::pruefe_auftrag(&zeichen, &config, &fonts, &cache))).await
}

/// Vorab-Pruefung: Welche Vorlagen verwenden nicht installierte Schriften?
#[tauri::command]
async fn schriften_pruefen(
    state: State<'_, AppState>,
    vorlagen: Vec<VorlageRef>,
) -> CmdResult<Vec<SchriftProblem>> {
    let fonts = state.fonts();
    let cache = state.cache.clone();
    blocking(move || Ok(job::pruefe_schriften(&vorlagen, &fonts, &cache))).await
}

#[tauri::command]
fn export_abbrechen(state: State<'_, AppState>) {
    state.abbruch.store(true, Ordering::Relaxed);
}

#[tauri::command]
fn cache_leeren(state: State<'_, AppState>) {
    state.cache.leeren();
}

#[tauri::command]
fn pfad_oeffnen(pfad: PathBuf) -> CmdResult<()> {
    tauri_plugin_opener::open_path(&pfad, None::<&str>).map_err(fehler)
}

/// Oeffnet einen Ordner im Explorer und legt ihn vorher an, falls er noch fehlt
/// (z.B. der Ausgabeordner vor dem ersten Export).
#[tauri::command]
fn ordner_oeffnen(pfad: PathBuf) -> CmdResult<()> {
    std::fs::create_dir_all(&pfad).map_err(fehler)?;
    tauri_plugin_opener::open_path(&pfad, None::<&str>).map_err(fehler)
}

/// Empfohlene Schriftgroesse fuer eine Zeichenhoehe ("Schrift mitwachsen").
#[tauri::command]
fn schrift_empfehlung(hoehe_mm: f64) -> f64 {
    tz_core::config::empfohlene_schrift_pt(hoehe_mm)
}

#[tauri::command]
fn json_speichern(pfad: PathBuf, daten: serde_json::Value) -> CmdResult<()> {
    let text = serde_json::to_string_pretty(&daten).map_err(fehler)?;
    std::fs::write(&pfad, text).map_err(fehler)
}

#[tauri::command]
fn json_laden(pfad: PathBuf) -> CmdResult<serde_json::Value> {
    let text = std::fs::read_to_string(&pfad).map_err(fehler)?;
    serde_json::from_str(&text).map_err(fehler)
}

#[tauri::command]
fn ordner_existiert(pfad: PathBuf) -> bool {
    pfad.is_dir()
}

/// Ordner der ausfuehrbaren Datei (portable Nutzung wie bei der Python-Version).
fn basis_ordner() -> PathBuf {
    std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(Path::to_path_buf))
        .unwrap_or_else(|| PathBuf::from("."))
}

pub fn run() {
    let state = AppState {
        basis: basis_ordner(),
        daten: OnceLock::new(),
        fonts: Arc::new(OnceLock::new()),
        cache: Arc::new(GrafikCache::new()),
        abbruch: Arc::new(AtomicBool::new(false)),
    };
    // Schriften im Hintergrund vorladen (unter Windows einige 100 ms)
    {
        let fonts = state.fonts.clone();
        let basis = state.basis.clone();
        std::thread::spawn(move || {
            fonts.get_or_init(|| Fonts::system_mit_ordner(&basis.join(SCHRIFTEN_ORDNER)));
        });
    }

    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .manage(state)
        .setup(|app| {
            let state = app.state::<AppState>();
            let daten = protokoll::daten_ordner(&state.basis, app.path().app_config_dir().ok());
            match protokoll::starte(&daten) {
                Ok(ordner) => log::info!(
                    "Start {} {} - Daten: {}, Logs: {}",
                    job::PROGRAMM,
                    job::VERSION,
                    daten.display(),
                    ordner.display()
                ),
                Err(e) => eprintln!("Log-Datei nicht anlegbar: {e}"),
            }
            let _ = state.daten.set(daten);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            app_info,
            einstellungen_laden,
            einstellungen_speichern,
            config_pruefen,
            bogen_layout,
            katalog_laden,
            schriften,
            vorschau,
            miniatur,
            exportieren,
            schriften_pruefen,
            auftrag_pruefen,
            export_abbrechen,
            cache_leeren,
            pfad_oeffnen,
            ordner_oeffnen,
            schrift_empfehlung,
            json_speichern,
            json_laden,
            ordner_existiert,
        ])
        .run(tauri::generate_context!())
        .expect("Fehler beim Start der Anwendung");
}
