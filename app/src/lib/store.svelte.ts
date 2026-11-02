// Zentraler Oberflaechen-Zustand (Svelte 5 Runes).
//
// Bedienkonzept:
// - Klick auf eine Vorlage im Katalog zeigt sie in der Vorschau (Ansicht "vorlage").
//   Erst "Zum Auftrag hinzufuegen" legt einen Posten an.
// - Klick auf eine Auftragszeile zeigt diesen Posten (Ansicht "posten").
// - Zwei oder mehr angehakte Posten -> Ansicht "mehrfach" (Checkbox gewinnt).
// - Aenderungen an Posten werden erst mit "Aenderung speichern" uebernommen;
//   beim Wechsel mit ungespeicherten Aenderungen gibt es eine Rueckfrage.

import { api, fehlerText } from "./api";
import type {
  Ansicht,
  AppEinstellungen,
  AppInfo,
  DruckConfig,
  FeldName,
  Kategorie,
  Knopf,
  ModusId,
  Parameter,
  Posten,
  PostenPruefung,
  Session,
  VorlageInfo,
  VorlageRef,
  ZeichenSpec,
} from "./types";

const SPEICHER_VERZOEGERUNG_MS = 400;
const MELDUNG_DAUER_MS = 4000;
const WARNUNG_DAUER_MS = 9000;
/** Hinweis-Arten, die eine Zeile im Auftrag rot markieren (Export moeglich, Ergebnis fehlerhaft). */
const ROTE_HINWEISE = ["text_zu_lang"];
/** Ab so vielen Zeichen fragt "Alle hinzufuegen" nach. */
const RUECKFRAGE_AB = 2;

export const FELDER: FeldName[] = ["modus", "text", "kopien", "grafik_position"];

let naechsteId = 1;

interface Rueckfrage {
  titel: string;
  text: string;
  knoepfe: Knopf[];
  antwort: (id: string) => void;
}

function gleich(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

function parameterVon(p: Posten): Parameter {
  return {
    modus: p.modus,
    text: p.text,
    kopien: p.kopien,
    grafik_position: p.grafik_position,
    grafik_max_mm: p.grafik_max_mm ? [p.grafik_max_mm[0], p.grafik_max_mm[1]] : null,
    drei_zeilen: p.drei_zeilen ?? false,
  };
}

function normiereText(t: string | null): string | null {
  return t && t.trim() !== "" ? t : null;
}

class Store {
  info = $state<AppInfo | null>(null);
  einstellungen = $state<AppEinstellungen | null>(null);
  katalog = $state<Kategorie | null>(null);
  katalogFehler = $state<string | null>(null);
  /** Hinweis zum Vorlagenordner (z.B. leer), keine Fehlermeldung. */
  katalogHinweis = $state<string | null>(null);
  /** Ladeschritt fuer den Splash-Screen. */
  ladeStatus = $state("Programm wird gestartet …");
  /** Pfad der gewaehlten Kategorie ("" = Wurzel, "#blanko" = Blanko). */
  kategoriePfad = $state<string>("");
  posten = $state<Posten[]>([]);
  /** Angehakte Posten (Ids). */
  markiert = $state<number[]>([]);
  ansicht = $state<Ansicht | null>(null);
  meldung = $state<{ text: string; art: "info" | "warnung" | "fehler" } | null>(null);
  /** Pruefergebnis je Posten-Id (lesbar? Hinweise?), aktualisiert bei jeder Aenderung. */
  pruefung = $state<Record<number, PostenPruefung>>({});
  #pruefLauf = 0;
  rueckfrage = $state<Rueckfrage | null>(null);
  vorschauSchnittlinien = $state(false);

  #speicherTimer: ReturnType<typeof setTimeout> | null = null;
  #meldungTimer: ReturnType<typeof setTimeout> | null = null;

  // -------------------------------------------------------------------------------------------
  // Abgeleitete Werte
  // -------------------------------------------------------------------------------------------

  get config(): DruckConfig {
    return this.einstellungen!.config;
  }

  get vorlagenOrdner(): string {
    return this.einstellungen?.vorlagen_ordner ?? this.info?.standard_vorlagen_ordner ?? "";
  }

  get ausgabeOrdner(): string {
    return this.einstellungen?.ausgabe_ordner ?? this.info?.standard_ausgabe_ordner ?? "";
  }

  /** Auftrag als Kategorienbaum (Anzeige und Export-Reihenfolge). */
  get gruppen(): Gruppe {
    return gruppiere(this.posten, "Hauptordner");
  }

  /** Posten in Anzeige-Reihenfolge = Reihenfolge im Export. */
  get postenSortiert(): Posten[] {
    return gruppenPosten(this.gruppen);
  }

  get anzahlZeichen(): number {
    return this.posten.reduce((s, p) => s + Math.max(1, p.kopien), 0);
  }

  /** Posten der aktuellen Einzelansicht. */
  get aktiverPosten(): Posten | null {
    const a = this.ansicht;
    return a?.art === "posten" ? (this.posten.find((p) => p.id === a.id) ?? null) : null;
  }

  /**
   * Zeichen fuer die Live-Vorschau im Einstellungsdialog: das aktuelle Zeichen der Vorschau,
   * bei Mehrfachauswahl das erste ausgewaehlte, sonst ein Beispiel (Blanko, OV + Staerke).
   */
  get beispielZeichen(): { titel: string; spec: ZeichenSpec } {
    const a = this.ansicht;
    const ausParametern = (vorlage: VorlageRef, p: Parameter): ZeichenSpec => ({
      vorlage,
      modus: p.modus,
      text: p.text,
      grafik_position: p.grafik_position,
      grafik_max_mm: p.grafik_max_mm,
      drei_zeilen: p.drei_zeilen ?? false,
    });
    if (a?.art === "vorlage") return { titel: a.vorlage.name, spec: ausParametern(a.vorlage.vorlage, a.entwurf) };
    if (a?.art === "posten" && this.aktiverPosten) {
      return { titel: this.aktiverPosten.name, spec: ausParametern(this.aktiverPosten.vorlage, a.entwurf) };
    }
    if (a?.art === "mehrfach") {
      const p = this.posten.find((x) => x.id === a.ids[0]);
      if (p) return { titel: `${p.name} (1. der Auswahl)`, spec: ausParametern(p.vorlage, parameterVon(p)) };
    }
    return {
      titel: "Beispiel (kein Zeichen ausgewählt)",
      spec: {
        // Blanko mit Platzhaltern (S2: "OV: ___" + Staerke, S1: Schreiblinien), "leer" waere leer
        vorlage: { art: "blanko", blanko: "s1_linien" },
        modus: "ov_staerke",
        text: null,
        grafik_position: "mittig",
        grafik_max_mm: null,
        drei_zeilen: false,
      },
    };
  }

  /** Posten, deren Vorlage nicht lesbar ist (Export blockiert). */
  get fehlerhafte(): Posten[] {
    return this.postenSortiert.filter((p) => this.pruefung[p.id]?.fehler);
  }

  /** Rot markieren: nicht lesbar oder Text passt nicht. */
  istRot(id: number): boolean {
    const r = this.pruefung[id];
    return !!r && (!!r.fehler || r.hinweise.some((h) => ROTE_HINWEISE.includes(h.art)));
  }

  /** Prueft alle Posten (Backend komponiert probeweise). Aeltere Laeufe werden verworfen. */
  async pruefen(): Promise<void> {
    if (!this.einstellungen) return;
    const nr = ++this.#pruefLauf;
    const liste = $state.snapshot(this.posten) as Posten[];
    const config = $state.snapshot(this.config) as DruckConfig;
    try {
      const ergebnis = await api.auftragPruefen(
        liste.map((p) => ({
          vorlage: p.vorlage,
          modus: p.modus,
          text: p.text,
          grafik_position: p.grafik_position,
          grafik_max_mm: p.grafik_max_mm,
          drei_zeilen: p.drei_zeilen ?? false,
        })),
        config,
      );
      if (nr !== this.#pruefLauf) return;
      const neu: Record<number, PostenPruefung> = {};
      liste.forEach((p, i) => (neu[p.id] = ergebnis[i]));
      this.pruefung = neu;
    } catch (e) {
      if (nr === this.#pruefLauf) this.fehler(`Prüfung fehlgeschlagen: ${fehlerText(e)}`);
    }
  }

  /** Warnt direkt beim Hinzufuegen, wenn Vorlagen nicht installierte Schriften verwenden. */
  async #schriftenWarnen(vorlagen: VorlageRef[]): Promise<void> {
    try {
      const probleme = await api.schriftenPruefen(vorlagen);
      if (probleme.length === 0) return;
      const schriften = [...new Set(probleme.flatMap((p) => p.schriften))].join(", ");
      const wer = probleme.length === 1 ? `„${probleme[0].vorlage}“ verwendet` : `${probleme.length} Vorlagen verwenden`;
      this.warnung(`${wer} nicht installierte Schrift(en): ${schriften} – wird beim Export ersetzt.`);
    } catch {
      // Pruefung ist nur ein Hinweis
    }
  }

  /** Gibt es ungespeicherte Aenderungen an Posten? */
  get ungespeichert(): boolean {
    const a = this.ansicht;
    if (!a) return false;
    if (a.art === "posten") {
      const p = this.aktiverPosten;
      return !!p && !gleich({ ...a.entwurf, text: normiereText(a.entwurf.text) }, parameterVon(p));
    }
    if (a.art === "mehrfach") return FELDER.some((f) => a.geaendert[f]);
    return false;
  }

  modusLabel(id: ModusId): string {
    return this.info?.modi.find((m) => m.id === id)?.label ?? id;
  }

  modusHatText(id: ModusId): boolean {
    return this.info?.modi.find((m) => m.id === id)?.hat_text ?? false;
  }

  /** Kategorie-Pfad einer Vorlage relativ zum Vorlagenordner. */
  kategorieVon(v: VorlageRef): string {
    if (v.art === "blanko") return this.info?.blanko.name ?? "Blanko-Zeichen";
    const norm = (s: string) => s.replace(/\\/g, "/").replace(/\/+$/, "");
    const datei = norm(v.pfad);
    const ordner = datei.slice(0, Math.max(0, datei.lastIndexOf("/")));
    const wurzel = norm(this.vorlagenOrdner);
    if (ordner.toLowerCase() === wurzel.toLowerCase()) return "";
    if (ordner.toLowerCase().startsWith(wurzel.toLowerCase() + "/")) return ordner.slice(wurzel.length + 1);
    return ordner.slice(ordner.lastIndexOf("/") + 1);
  }

  // -------------------------------------------------------------------------------------------
  // Start, Katalog, Einstellungen
  // -------------------------------------------------------------------------------------------

  async start(): Promise<void> {
    try {
      this.ladeStatus = "Einstellungen werden geladen …";
      this.info = await api.appInfo();
      // Fehlende Felder fuellt das Backend (serde default) mit Werkseinstellungen auf.
      this.einstellungen = await api.einstellungenLaden();
      this.ladeStatus = "Schriften werden geladen …";
      await api.schriften();
      this.ladeStatus = "Vorlagen werden eingelesen …";
      await this.katalogNeuLaden();
      this.ladeStatus = "Fertig";
    } catch (err) {
      this.fehler(`Start fehlgeschlagen: ${fehlerText(err)}`);
    }
  }

  async katalogNeuLaden(): Promise<void> {
    this.katalogFehler = null;
    this.katalogHinweis = null;
    await api.cacheLeeren();
    const ordner = this.vorlagenOrdner;
    if (!(await api.ordnerExistiert(ordner))) {
      this.katalog = null;
      this.katalogFehler = `Vorlagenordner nicht gefunden: ${ordner}`;
      return;
    }
    try {
      this.katalog = await api.katalogLaden(ordner);
      if (this.katalog.anzahl_gesamt === 0) {
        this.katalogHinweis =
          `Der Vorlagenordner ist leer: ${ordner}. Lege dort SVG-, PNG- oder JPG-Vorlagen ab ` +
          "(Unterordner = Kategorien) und klicke auf „Neu laden“.";
      }
    } catch (err) {
      this.katalog = null;
      this.katalogFehler = fehlerText(err);
    }
  }

  /**
   * "Schrift mitwachsen": setzt die Schriftgroesse passend zur Hoehe des aktiven Layouts
   * (nach Aenderung der Zeichenhoehe oder Wechsel S1/S2). Ohne Wirkung, wenn abgeschaltet.
   */
  async schriftAnpassen(): Promise<void> {
    if (!this.einstellungen || !this.config.text.schrift_mitwachsen) return;
    const c = this.config;
    const hoehe = c.layout === "s1" ? c.s1.groesse.hoehe_mm : c.s2.hoehe_mm;
    if (!Number.isFinite(hoehe)) return;
    try {
      const pt = await api.schriftEmpfehlung(hoehe);
      if (c.text.font_size_pt !== pt) {
        c.text.font_size_pt = pt;
        this.speichern();
      }
    } catch {
      // Empfehlung ist nur eine Komfortfunktion
    }
  }

  /** Einstellungen verzoegert speichern (bei jeder Aenderung aufrufen). */
  speichern(): void {
    if (this.#speicherTimer) clearTimeout(this.#speicherTimer);
    this.#speicherTimer = setTimeout(() => {
      if (this.einstellungen) {
        api
          .einstellungenSpeichern($state.snapshot(this.einstellungen) as AppEinstellungen)
          .catch((e) => this.fehler(`Einstellungen nicht gespeichert: ${fehlerText(e)}`));
      }
    }, SPEICHER_VERZOEGERUNG_MS);
  }

  // -------------------------------------------------------------------------------------------
  // Rueckfragen
  // -------------------------------------------------------------------------------------------

  /** Zeigt einen Dialog und liefert die Id des gedrueckten Knopfes. */
  fragen(titel: string, text: string, knoepfe: Knopf[]): Promise<string> {
    return new Promise((resolve) => {
      this.rueckfrage = {
        titel,
        text,
        knoepfe,
        antwort: (id) => {
          this.rueckfrage = null;
          resolve(id);
        },
      };
    });
  }

  async bestaetigen(titel: string, text: string, ok: string): Promise<boolean> {
    const a = await this.fragen(titel, text, [
      { id: "nein", label: "Abbrechen" },
      { id: "ja", label: ok, primaer: true },
    ]);
    return a === "ja";
  }

  /** Vor jedem Wechsel aufrufen. `false` = Benutzer will weiter bearbeiten. */
  async darfWechseln(): Promise<boolean> {
    if (!this.ungespeichert) return true;
    const a = await this.fragen(
      "Ungespeicherte Änderungen",
      "Die Änderungen an den Parametern wurden noch nicht gespeichert.",
      [
        { id: "zurueck", label: "Zurück" },
        { id: "verwerfen", label: "Verwerfen" },
        { id: "speichern", label: "Speichern", primaer: true },
      ],
    );
    if (a === "speichern") {
      this.aenderungSpeichern();
      return true;
    }
    if (a === "verwerfen") {
      this.aenderungVerwerfen();
      return true;
    }
    return false;
  }

  // -------------------------------------------------------------------------------------------
  // Ansicht wechseln
  // -------------------------------------------------------------------------------------------

  standardParameter(): Parameter {
    return {
      modus: this.einstellungen?.standard_modus ?? "freitext",
      text: null,
      kopien: 1,
      grafik_position: "mittig",
      grafik_max_mm: null,
      drei_zeilen: false,
    };
  }

  async vorlageAnsehen(v: VorlageInfo): Promise<void> {
    if (!(await this.darfWechseln())) return;
    this.markiert = [];
    this.ansicht = {
      art: "vorlage",
      vorlage: v,
      kategorie: this.kategorieVon(v.vorlage),
      entwurf: this.standardParameter(),
    };
  }

  async postenAnsehen(id: number): Promise<void> {
    const a = this.ansicht;
    if (a?.art === "posten" && a.id === id && this.markiert.length === 0) return;
    if (!(await this.darfWechseln())) return;
    this.markiert = [];
    this.#zeigePosten(id);
  }

  #zeigePosten(id: number): void {
    const p = this.posten.find((x) => x.id === id);
    this.ansicht = p ? { art: "posten", id, entwurf: parameterVon($state.snapshot(p) as Posten) } : null;
  }

  #zeigeMehrfach(ids: number[]): void {
    const liste = this.posten.filter((p) => ids.includes(p.id));
    const erster = parameterVon($state.snapshot(liste[0]) as Posten);
    const gemischt = {} as Record<FeldName, boolean>;
    const geaendert = {} as Record<FeldName, boolean>;
    for (const f of FELDER) {
      gemischt[f] = liste.some((p) => !gleich(p[f], liste[0][f]));
      geaendert[f] = false;
    }
    this.ansicht = { art: "mehrfach", ids, entwurf: { ...erster, grafik_max_mm: null }, gemischt, geaendert };
  }

  /** Setzt die Markierung (nach Rueckfrage) und passt die Ansicht an. */
  async markierungSetzen(ids: number[]): Promise<void> {
    if (!(await this.darfWechseln())) return;
    this.markiert = ids;
    if (ids.length >= 2) this.#zeigeMehrfach(ids);
    else if (ids.length === 1) this.#zeigePosten(ids[0]);
    else if (this.ansicht?.art === "mehrfach") this.ansicht = null;
  }

  async umschalten(ids: number[], an: boolean): Promise<void> {
    const rest = this.markiert.filter((m) => !ids.includes(m));
    await this.markierungSetzen(an ? [...rest, ...ids] : rest);
  }

  async alleMarkieren(an: boolean): Promise<void> {
    await this.markierungSetzen(an ? this.posten.map((p) => p.id) : []);
  }

  /** Feld in der Mehrfachansicht wurde bearbeitet. */
  feldGeaendert(f: FeldName): void {
    const a = this.ansicht;
    if (a?.art !== "mehrfach") return;
    a.gemischt[f] = false;
    a.geaendert[f] = true;
  }

  // -------------------------------------------------------------------------------------------
  // Aktionen der Vorschau-Leiste
  // -------------------------------------------------------------------------------------------

  /** Legt einen neuen Posten aus der aktuellen Vorlage bzw. dem aktuellen Posten an. */
  hinzufuegen(): void {
    const a = this.ansicht;
    let quelle: { vorlage: VorlageRef; name: string; kategorie: string } | null = null;
    if (a?.art === "vorlage") {
      quelle = { vorlage: a.vorlage.vorlage, name: a.vorlage.name, kategorie: a.kategorie };
    } else if (a?.art === "posten") {
      const p = this.aktiverPosten;
      if (p) quelle = { vorlage: $state.snapshot(p.vorlage) as VorlageRef, name: p.name, kategorie: p.kategorie };
    }
    if (!a || !quelle || a.art === "mehrfach") return;
    const neu: Posten = {
      id: naechsteId++,
      ...quelle,
      ...($state.snapshot(a.entwurf) as Parameter),
      text: normiereText(a.entwurf.text),
      kopien: Math.max(1, Math.round(a.entwurf.kopien || 1)),
    };
    this.posten.push(neu);
    if (a.art === "posten") {
      // Original bleibt unveraendert, der neue Eintrag wird angezeigt
      this.#zeigePosten(neu.id);
    }
    this.hinweis(`„${neu.name}“ zum Auftrag hinzugefügt (${this.posten.length} Positionen)`);
    void this.#schriftenWarnen([neu.vorlage]);
  }

  /** Mehrere Vorlagen auf einmal (mit Rueckfrage). */
  async alleHinzufuegen(vorlagen: VorlageInfo[]): Promise<void> {
    if (vorlagen.length >= RUECKFRAGE_AB) {
      const ok = await this.bestaetigen(
        "Alle hinzufügen",
        `${vorlagen.length} Zeichen mit Standard-Parametern zum Auftrag hinzufügen?`,
        "Hinzufügen",
      );
      if (!ok) return;
    }
    for (const v of vorlagen) {
      this.posten.push({
        id: naechsteId++,
        name: v.name,
        vorlage: v.vorlage,
        kategorie: this.kategorieVon(v.vorlage),
        ...this.standardParameter(),
      });
    }
    this.hinweis(`${vorlagen.length} Zeichen hinzugefügt`);
    void this.#schriftenWarnen(vorlagen.map((v) => v.vorlage));
  }

  aenderungSpeichern(): void {
    const a = this.ansicht;
    if (a?.art === "posten") {
      const p = this.aktiverPosten;
      if (!p) return;
      Object.assign(p, $state.snapshot(a.entwurf), {
        text: normiereText(a.entwurf.text),
        kopien: Math.max(1, Math.round(a.entwurf.kopien || 1)),
      });
      this.#zeigePosten(p.id);
    } else if (a?.art === "mehrfach") {
      const werte = $state.snapshot(a.entwurf) as Parameter;
      for (const p of this.posten) {
        if (!a.ids.includes(p.id)) continue;
        if (a.geaendert.modus) p.modus = werte.modus;
        if (a.geaendert.text) p.text = normiereText(werte.text);
        if (a.geaendert.kopien) p.kopien = Math.max(1, Math.round(werte.kopien || 1));
        if (a.geaendert.grafik_position) p.grafik_position = werte.grafik_position;
      }
      this.#zeigeMehrfach(a.ids);
    }
  }

  aenderungVerwerfen(): void {
    const a = this.ansicht;
    if (a?.art === "posten") this.#zeigePosten(a.id);
    else if (a?.art === "mehrfach") this.#zeigeMehrfach(a.ids);
  }

  async entfernen(): Promise<void> {
    const a = this.ansicht;
    let ids: number[] = [];
    if (a?.art === "posten") ids = [a.id];
    else if (a?.art === "mehrfach") {
      const ok = await this.bestaetigen(
        "Entfernen",
        `${a.ids.length} Zeichen aus dem Auftrag entfernen?`,
        "Entfernen",
      );
      if (!ok) return;
      ids = a.ids;
    }
    if (ids.length === 0) return;
    this.posten = this.posten.filter((p) => !ids.includes(p.id));
    this.markiert = this.markiert.filter((m) => !ids.includes(m));
    this.ansicht = null;
  }

  async leeren(): Promise<void> {
    const ok = await this.bestaetigen(
      "Auftrag leeren",
      `Alle ${this.posten.length} Positionen aus dem Auftrag entfernen?`,
      "Leeren",
    );
    if (!ok) return;
    this.posten = [];
    this.markiert = [];
    if (this.ansicht?.art !== "vorlage") this.ansicht = null;
  }

  // -------------------------------------------------------------------------------------------
  // Sessions
  // -------------------------------------------------------------------------------------------

  session(): Session {
    return {
      format: "tzdg-session",
      version: 1,
      config: $state.snapshot(this.config) as DruckConfig,
      posten: this.posten.map(({ id: _id, ...rest }) => $state.snapshot(rest) as Omit<Posten, "id">),
    };
  }

  sessionUebernehmen(s: Session, configUebernehmen: boolean): void {
    if (s.format !== "tzdg-session") throw new Error("Keine Session-Datei des Druckgenerators");
    this.posten = s.posten.map((p) => ({
      ...p,
      id: naechsteId++,
      kategorie: p.kategorie ?? this.kategorieVon(p.vorlage),
    }));
    this.markiert = [];
    this.ansicht = null;
    if (configUebernehmen && this.einstellungen) {
      this.einstellungen.config = s.config;
      this.speichern();
    }
  }

  // -------------------------------------------------------------------------------------------
  // Meldungen
  // -------------------------------------------------------------------------------------------

  /** Kurze Info, verschwindet automatisch. */
  hinweis(text: string): void {
    this.meldung = { text, art: "info" };
    if (this.#meldungTimer) clearTimeout(this.#meldungTimer);
    this.#meldungTimer = setTimeout(() => {
      if (this.meldung?.art === "info") this.meldung = null;
    }, MELDUNG_DAUER_MS);
  }

  /** Warnung, bleibt laenger stehen. */
  warnung(text: string): void {
    this.meldung = { text, art: "warnung" };
    if (this.#meldungTimer) clearTimeout(this.#meldungTimer);
    this.#meldungTimer = setTimeout(() => {
      if (this.meldung?.art === "warnung") this.meldung = null;
    }, WARNUNG_DAUER_MS);
  }

  fehler(text: string): void {
    this.meldung = { text, art: "fehler" };
  }
}

export const store = new Store();

/** Sucht eine Kategorie per Pfad im Baum. */
export function findeKategorie(k: Kategorie | null, pfad: string): Kategorie | null {
  if (!k) return null;
  if (k.pfad === pfad) return k;
  for (const u of k.unterkategorien) {
    const f = findeKategorie(u, pfad);
    if (f) return f;
  }
  return null;
}

/** Gruppe im Auftrag (Kategorie mit Unterkategorien). */
export interface Gruppe {
  name: string;
  pfad: string;
  posten: Posten[];
  untergruppen: Gruppe[];
}

/** Baut aus den Posten einen Kategorienbaum (Reihenfolge der Posten bleibt erhalten). */
export function gruppiere(posten: Posten[], wurzelName: string): Gruppe {
  const wurzel: Gruppe = { name: wurzelName, pfad: "", posten: [], untergruppen: [] };
  for (const p of posten) {
    let g = wurzel;
    let pfad = "";
    for (const teil of p.kategorie.split("/").filter(Boolean)) {
      pfad = pfad ? `${pfad}/${teil}` : teil;
      let u = g.untergruppen.find((x) => x.pfad === pfad);
      if (!u) {
        u = { name: teil, pfad, posten: [], untergruppen: [] };
        g.untergruppen.push(u);
      }
      g = u;
    }
    g.posten.push(p);
  }
  const sortiere = (g: Gruppe) => {
    g.untergruppen.sort((a, b) => a.name.localeCompare(b.name, "de"));
    g.untergruppen.forEach(sortiere);
  };
  sortiere(wurzel);
  return wurzel;
}

/** Alle Posten einer Gruppe in Anzeige-Reihenfolge (eigene Posten, dann Untergruppen). */
export function gruppenPosten(g: Gruppe): Posten[] {
  return [...g.posten, ...g.untergruppen.flatMap(gruppenPosten)];
}

/** Alle Posten-Ids einer Gruppe inkl. Untergruppen. */
export function gruppenIds(g: Gruppe): number[] {
  return gruppenPosten(g).map((p) => p.id);
}
