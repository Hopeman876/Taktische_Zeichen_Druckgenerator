//! `tzdg` - Kommandozeile fuer den Taktische Zeichen Druckgenerator.
//!
//! ```text
//! tzdg export  <auftrag.json>                 Export laut Auftrag (siehe job::ExportAuftrag)
//! tzdg vorschau <zeichen.json> <aus.png> [px] Vorschau eines Zeichens (ZeichenSpec + optional config)
//! tzdg scan    <vorlagenordner>               Katalog als JSON ausgeben
//! tzdg pruefen <vorlagenordner>               Alle Vorlagen laden, Fehler/fehlende Schriften melden
//! tzdg config                                 Werkseinstellungen als JSON ausgeben
//! ```

use std::path::PathBuf;
use std::process::ExitCode;

use tz_core::compose::{ComposeOptionen, ZeichenSpec};
use tz_core::config::DruckConfig;
use tz_core::export::raster;
use tz_core::fonts::Fonts;
use tz_core::job::{exportiere, komponiere, ExportAuftrag, Fortschritt, GrafikCache};

struct Konsole;

impl Fortschritt for Konsole {
    fn melde(&self, fertig: usize, gesamt: usize, schritt: &str) {
        eprintln!("[{fertig}/{gesamt}] {schritt}");
    }
}

#[derive(serde::Deserialize)]
struct VorschauDatei {
    #[serde(flatten)]
    zeichen: ZeichenSpec,
    #[serde(default)]
    config: DruckConfig,
    #[serde(default)]
    schnittlinien: bool,
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match run(&args) {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("Fehler: {e}");
            ExitCode::FAILURE
        }
    }
}

fn lies_json<T: serde::de::DeserializeOwned>(pfad: &str) -> Result<T, String> {
    let text = std::fs::read_to_string(pfad).map_err(|e| format!("{pfad}: {e}"))?;
    serde_json::from_str(&text).map_err(|e| format!("{pfad}: {e}"))
}

fn run(args: &[String]) -> Result<(), String> {
    let fonts = Fonts::system();
    match args.first().map(String::as_str) {
        Some("export") => {
            let pfad = args.get(1).ok_or("Auftragsdatei fehlt")?;
            let auftrag: ExportAuftrag = lies_json(pfad)?;
            let bericht = exportiere(&auftrag, &fonts, &GrafikCache::new(), &Konsole).map_err(|e| e.to_string())?;
            println!("{}", serde_json::to_string_pretty(&bericht).map_err(|e| e.to_string())?);
            Ok(())
        }
        Some("vorschau") => {
            let ein = args.get(1).ok_or("Zeichendatei fehlt")?;
            let aus = PathBuf::from(args.get(2).ok_or("Ausgabedatei fehlt")?);
            let px: u32 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(800);
            let v: VorschauDatei = lies_json(ein)?;
            let k = komponiere(
                &v.zeichen,
                &v.config,
                &fonts,
                &GrafikCache::new(),
                ComposeOptionen { schnittlinien: v.schnittlinien },
            )
            .map_err(|e| e.to_string())?;
            for h in &k.hinweise {
                eprintln!("Hinweis: {}", h.text);
            }
            let png = raster::vorschau(&k, &fonts, px).map_err(|e| e.to_string())?;
            std::fs::write(&aus, png).map_err(|e| format!("{}: {e}", aus.display()))?;
            Ok(())
        }
        Some("scan") => {
            let dir = PathBuf::from(args.get(1).ok_or("Ordner fehlt")?);
            let k = tz_core::katalog::scan(&dir).map_err(|e| e.to_string())?;
            println!("{}", serde_json::to_string_pretty(&k).map_err(|e| e.to_string())?);
            Ok(())
        }
        Some("pruefen") => {
            // Laedt jede Vorlage des Ordners und meldet Lesefehler und fehlende Schriften.
            let dir = PathBuf::from(args.get(1).ok_or("Ordner fehlt")?);
            let k = tz_core::katalog::scan(&dir).map_err(|e| e.to_string())?;
            let mut pfade = Vec::new();
            fn sammle(k: &tz_core::katalog::Kategorie, out: &mut Vec<PathBuf>) {
                for v in &k.vorlagen {
                    if let tz_core::katalog::VorlageRef::Datei { pfad } = &v.vorlage {
                        out.push(pfad.clone());
                    }
                }
                k.unterkategorien.iter().for_each(|u| sammle(u, out));
            }
            sammle(&k, &mut pfade);
            let (mut fehler, mut schriften) = (0, 0);
            for p in &pfade {
                match tz_core::grafik::lade(p, &fonts) {
                    Err(e) => {
                        fehler += 1;
                        println!("FEHLER  {e}");
                    }
                    Ok(g) if !g.fehlende_schriften.is_empty() => {
                        schriften += 1;
                        println!("SCHRIFT {}: {}", p.display(), g.fehlende_schriften.join(", "));
                    }
                    Ok(_) => {}
                }
            }
            println!("{} Vorlagen, {fehler} nicht lesbar, {schriften} mit fehlenden Schriften", pfade.len());
            Ok(())
        }
        Some("config") => {
            println!("{}", serde_json::to_string_pretty(&DruckConfig::default()).map_err(|e| e.to_string())?);
            Ok(())
        }
        _ => Err("Verwendung: tzdg export <auftrag.json> | vorschau <zeichen.json> <aus.png> [px] | scan <ordner> | config".into()),
    }
}
