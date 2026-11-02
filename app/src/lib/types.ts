// Typen spiegeln die serde-Strukturen aus tz-core / src-tauri wider.

export type ModusId =
  | "ov_staerke"
  | "ort_staerke"
  | "schreiblinie_staerke"
  | "freitext"
  | "ruf"
  | "dateiname"
  | "ohne_text";

export type GrafikPosition = "oben" | "mittig" | "unten";
export type Layout = "s2" | "s1";
export type BlankoArt = "leer" | "s1_leer" | "s1_linien" | "s1_linien_staerke";
export type ExportFormat = "png" | "pdf_einzel" | "pdf_bogen";
export type VorlageFormat = "svg" | "png" | "jpg" | "blanko";

export type VorlageRef = { art: "datei"; pfad: string } | { art: "blanko"; blanko: BlankoArt };

export interface ModusInfo {
  id: ModusId;
  label: string;
  platzhalter: string;
  hat_text: boolean;
}

export interface VorlageInfo {
  name: string;
  format: VorlageFormat;
  vorlage: VorlageRef;
}

export interface Kategorie {
  name: string;
  pfad: string;
  vorlagen: VorlageInfo[];
  unterkategorien: Kategorie[];
  anzahl_gesamt: number;
}

export interface Groesse {
  hoehe_mm: number;
  breite_mm: number;
  beschnitt_mm: number;
  sicherheitsabstand_mm: number;
}

export interface DruckConfig {
  layout: Layout;
  s2: Groesse;
  s1: {
    groesse: Groesse;
    links_prozent: number;
    anzahl_schreiblinien: number;
    staerke_anzeigen: boolean;
  };
  text: {
    font_family: string;
    font_size_pt: number;
    schrift_mitwachsen: boolean;
    zeilenabstand_faktor: number;
    abstand_grafik_text_mm: number;
    text_unten_mm: number;
    staerke_stellen: [number, number, number, number];
    min_schrift_pt: number;
  };
  linien: {
    schreiblinie_mm: number;
    schreiblinie_rand_mm: number;
    schnittlinie_mm: number;
  };
  export: {
    png_dpi: number;
    png_hintergrund_weiss: boolean;
    bogen_rand_horizontal_mm: number;
    bogen_rand_vertikal_mm: number;
    schnittlinien: boolean;
    text_als_pfade: boolean;
    druckhinweis: boolean;
  };
  grafik_max_mm: [number, number] | null;
}

export interface ZeichenSpec {
  vorlage: VorlageRef;
  modus: ModusId;
  text: string | null;
  grafik_position: GrafikPosition;
  grafik_max_mm: [number, number] | null;
  drei_zeilen: boolean;
}

/** Einstellbare Parameter eines Zeichens (Vorschau / Auftrag). */
export interface Parameter {
  modus: ModusId;
  text: string | null;
  kopien: number;
  grafik_position: GrafikPosition;
  grafik_max_mm: [number, number] | null;
  drei_zeilen: boolean;
}

/** In der Mehrfachauswahl gemeinsam bearbeitbare Felder. */
export type FeldName = "modus" | "text" | "kopien" | "grafik_position";

/** Eintrag im Auftrag (Oberflaeche). */
export interface Posten extends ZeichenSpec {
  id: number;
  name: string;
  kopien: number;
  /** Kategorie-Pfad relativ zum Vorlagenordner ("/"-getrennt), fuer die Gruppierung. */
  kategorie: string;
}

/** Was die Vorschau gerade zeigt. */
export type Ansicht =
  | { art: "vorlage"; vorlage: VorlageInfo; kategorie: string; entwurf: Parameter }
  | { art: "posten"; id: number; entwurf: Parameter }
  | {
      art: "mehrfach";
      ids: number[];
      entwurf: Parameter;
      /** Feld hat bei den gewaehlten Zeichen unterschiedliche Werte (und ist noch unveraendert). */
      gemischt: Record<FeldName, boolean>;
      geaendert: Record<FeldName, boolean>;
    };

export interface Knopf {
  id: string;
  label: string;
  primaer?: boolean;
}

export interface SchriftProblem {
  vorlage: string;
  pfad: string;
  schriften: string[];
}

export interface Hinweis {
  art: string;
  text: string;
}

export interface VorschauAntwort {
  bild: string;
  hinweise: Hinweis[];
  breite_mm: number;
  hoehe_mm: number;
  dritte_zeile_moeglich: boolean;
}

export interface BogenLayout {
  seite_w_mm: number;
  seite_h_mm: number;
  querformat: boolean;
  spalten: number;
  zeilen: number;
}

export interface ExportAuftrag {
  posten: (ZeichenSpec & { kopien: number })[];
  config: DruckConfig;
  format: ExportFormat;
  ziel_ordner: string;
  schnittlinien: boolean | null;
  zeichen_pro_datei: number | null;
}

export interface ExportBericht {
  ordner: string;
  dateien: string[];
  anzahl_zeichen: number;
  anzahl_seiten: number;
  hinweise: { position: number; zeichen: string; hinweis: Hinweis }[];
  bericht_datei: string | null;
  dauer_ms: number;
}

export interface AppInfo {
  version: string;
  programm: string;
  autoren: string;
  lizenz: string;
  modi: ModusInfo[];
  blanko: Kategorie;
  standard_vorlagen_ordner: string;
  standard_ausgabe_ordner: string;
  werkseinstellungen: DruckConfig;
  daten_ordner: string;
  standard_oberflaeche: Oberflaeche;
}

export interface AppEinstellungen {
  config: DruckConfig;
  vorlagen_ordner: string | null;
  ausgabe_ordner: string | null;
  export_format: ExportFormat | null;
  standard_modus: ModusId;
  oberflaeche: Oberflaeche;
  tour_gesehen: boolean;
}

/** Bereichsgroessen der Hauptansicht. */
export interface Oberflaeche {
  kategorien_px: number;
  vorschau_px: number;
  vorlagen_anteil: number;
  vorlagen_zoom: number;
}

/** Ergebnis der Pruefung eines Auftragseintrags. */
export interface PostenPruefung {
  fehler: string | null;
  hinweise: Hinweis[];
}

export interface Fortschritt {
  fertig: number;
  gesamt: number;
  schritt: string;
}

/** Gespeicherter Arbeitsstand (Session-Datei). */
export interface Session {
  format: "tzdg-session";
  version: 1;
  config: DruckConfig;
  posten: (Omit<Posten, "id" | "kategorie"> & { kategorie?: string })[];
}
