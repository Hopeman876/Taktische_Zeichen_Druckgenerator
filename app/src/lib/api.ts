// Typisierte Wrapper um die Tauri-Kommandos (src-tauri/src/lib.rs).

import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import type {
  AppEinstellungen,
  AppInfo,
  BogenLayout,
  DruckConfig,
  ExportAuftrag,
  ExportBericht,
  Fortschritt,
  Kategorie,
  PostenPruefung,
  SchriftProblem,
  VorlageRef,
  VorschauAntwort,
  ZeichenSpec,
} from "./types";

export const api = {
  appInfo: () => invoke<AppInfo>("app_info"),
  einstellungenLaden: () => invoke<AppEinstellungen>("einstellungen_laden"),
  einstellungenSpeichern: (einstellungen: AppEinstellungen) =>
    invoke<void>("einstellungen_speichern", { einstellungen }),
  configPruefen: (config: DruckConfig) => invoke<string[]>("config_pruefen", { config }),
  bogenLayout: (config: DruckConfig) => invoke<BogenLayout>("bogen_layout", { config }),
  katalogLaden: (ordner: string) => invoke<Kategorie>("katalog_laden", { ordner }),
  schriften: () => invoke<string[]>("schriften"),
  vorschau: (zeichen: ZeichenSpec, config: DruckConfig, schnittlinien: boolean, maxPx: number) =>
    invoke<VorschauAntwort>("vorschau", { zeichen, config, schnittlinien, maxPx }),
  miniatur: (pfad: string, maxPx: number) => invoke<string>("miniatur", { pfad, maxPx }),
  exportieren: (auftrag: ExportAuftrag) => invoke<ExportBericht>("exportieren", { auftrag }),
  auftragPruefen: (zeichen: ZeichenSpec[], config: DruckConfig) =>
    invoke<PostenPruefung[]>("auftrag_pruefen", { zeichen, config }),
  schriftenPruefen: (vorlagen: VorlageRef[]) => invoke<SchriftProblem[]>("schriften_pruefen", { vorlagen }),
  exportAbbrechen: () => invoke<void>("export_abbrechen"),
  cacheLeeren: () => invoke<void>("cache_leeren"),
  pfadOeffnen: (pfad: string) => invoke<void>("pfad_oeffnen", { pfad }),
  ordnerOeffnen: (pfad: string) => invoke<void>("ordner_oeffnen", { pfad }),
  schriftEmpfehlung: (hoeheMm: number) => invoke<number>("schrift_empfehlung", { hoeheMm }),
  jsonSpeichern: (pfad: string, daten: unknown) => invoke<void>("json_speichern", { pfad, daten }),
  jsonLaden: <T>(pfad: string) => invoke<T>("json_laden", { pfad }),
  ordnerExistiert: (pfad: string) => invoke<boolean>("ordner_existiert", { pfad }),
  aufFortschritt: (cb: (f: Fortschritt) => void): Promise<UnlistenFn> =>
    listen<Fortschritt>("export-fortschritt", (e) => cb(e.payload)),
};

/** Fehlertext aus einer Tauri-Exception. */
export function fehlerText(e: unknown): string {
  return typeof e === "string" ? e : e instanceof Error ? e.message : JSON.stringify(e);
}
