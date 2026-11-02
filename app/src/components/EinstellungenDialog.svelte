<script lang="ts">
  import { api } from "../lib/api";
  import { store } from "../lib/store.svelte";
  import type { DruckConfig } from "../lib/types";
  import ZeichenBild from "./ZeichenBild.svelte";
  import Zahl from "./Zahl.svelte";

  const STANDARD_GRAFIK_MAX_MM: [number, number] = [30, 25];

  /** mm-Zahl im deutschen Format. */
  function mm(v: number): string {
    return Number.isFinite(v) ? v.toLocaleString("de-DE", { maximumFractionDigits: 1 }) : "–";
  }

  let { schliessen }: { schliessen: () => void } = $props();

  type Tab = "groesse" | "text" | "export";
  let tab = $state<Tab>("groesse");
  let fehler = $state<string[]>([]);
  let schriften = $state<string[]>([]);

  const cfg = $derived(store.config);
  const beispiel = $derived(store.beispielZeichen);
  let vorschauSchnitt = $state(true);

  // Abgeleitete Masse (Inhaltsbereich = Endformat minus 2 x Sicherheitsabstand)
  const s2Inhalt = $derived({
    w: cfg.s2.breite_mm - 2 * cfg.s2.sicherheitsabstand_mm,
    h: cfg.s2.hoehe_mm - 2 * cfg.s2.sicherheitsabstand_mm,
  });
  const s1InhaltW = $derived(cfg.s1.groesse.breite_mm - 2 * cfg.s1.groesse.sicherheitsabstand_mm);
  const s1Links = $derived((s1InhaltW * cfg.s1.links_prozent) / 100);

  function layoutSetzen(l: "s2" | "s1"): void {
    cfg.layout = l;
    void hoeheGeaendert();
  }

  /** Nach Aenderung einer Zeichenhoehe: ggf. Schriftgroesse mitwachsen lassen. */
  async function hoeheGeaendert(): Promise<void> {
    await store.schriftAnpassen();
    await geaendert();
  }

  function grafikMaxUmschalten(an: boolean): void {
    cfg.grafik_max_mm = an ? [...STANDARD_GRAFIK_MAX_MM] : null;
    geaendert();
  }

  api.schriften().then((s) => (schriften = s)).catch(() => {});

  async function geaendert(): Promise<void> {
    store.speichern();
    fehler = await api.configPruefen($state.snapshot(store.config) as DruckConfig);
  }

  async function zuruecksetzen(): Promise<void> {
    if (!store.einstellungen || !store.info) return;
    const ok = await store.bestaetigen(
      "Werkseinstellungen",
      "Alle Druckeinstellungen auf Werkseinstellungen zurücksetzen?",
      "Zurücksetzen",
    );
    if (!ok) return;
    store.einstellungen.config = $state.snapshot(store.info.werkseinstellungen) as DruckConfig;
    geaendert();
  }

  function taste(e: KeyboardEvent): void {
    if (e.key === "Escape" && !store.rueckfrage) schliessen();
  }
</script>

<svelte:window onkeydown={taste} />

<div class="overlay" role="presentation" onclick={(e) => e.target === e.currentTarget && schliessen()}>
  <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="einst-titel">
    <header>
      <h3 id="einst-titel">Einstellungen</h3>
      <span class="spacer"></span>
      <button class="ghost" onclick={schliessen} aria-label="Schließen">✕</button>
    </header>
    <nav>
      <button class:aktiv={tab === "groesse"} onclick={() => (tab = "groesse")}>Größe & Layout</button>
      <button class:aktiv={tab === "text"} onclick={() => (tab = "text")}>Text & Linien</button>
      <button class:aktiv={tab === "export"} onclick={() => (tab = "export")}>Export</button>
    </nav>
    <div class="koerper">
    <div class="inhalt">
      {#if tab === "groesse"}
        <div class="spalten">
          <fieldset class:aktiv={cfg.layout === "s2"}>
            <legend>S2 – Einzelschild</legend>
            <Zahl label="Höhe" einheit="mm" bind:wert={cfg.s2.hoehe_mm} onchange={hoeheGeaendert} />
            <Zahl label="Breite" einheit="mm" bind:wert={cfg.s2.breite_mm} onchange={geaendert} />
            <Zahl label="Beschnittzugabe" einheit="mm" bind:wert={cfg.s2.beschnitt_mm} onchange={geaendert} />
            <Zahl label="Sicherheitsabstand" einheit="mm" bind:wert={cfg.s2.sicherheitsabstand_mm} onchange={geaendert} />
            <p class="masse">Inhaltsbereich (Grafik + Text): {mm(s2Inhalt.w)} × {mm(s2Inhalt.h)} mm</p>
          </fieldset>
          <fieldset class:aktiv={cfg.layout === "s1"}>
            <legend>S1 – Doppelschild</legend>
            <Zahl label="Höhe" einheit="mm" bind:wert={cfg.s1.groesse.hoehe_mm} onchange={hoeheGeaendert} />
            <Zahl label="Breite" einheit="mm" bind:wert={cfg.s1.groesse.breite_mm} onchange={geaendert} />
            <Zahl label="Beschnittzugabe" einheit="mm" bind:wert={cfg.s1.groesse.beschnitt_mm} onchange={geaendert} />
            <Zahl label="Sicherheitsabstand" einheit="mm" bind:wert={cfg.s1.groesse.sicherheitsabstand_mm} onchange={geaendert} />
            <Zahl label="Anteil links (Grafik + Text)" einheit="%" schritt={1} bind:wert={cfg.s1.links_prozent} onchange={geaendert} />
            <p class="masse">
              Links (Grafik + Text): <strong>{mm(s1Links)} mm</strong> · Rechts (Schreiblinien):
              <strong>{mm(s1InhaltW - s1Links)} mm</strong><br />
              <span class="muted">Bezogen auf den Inhaltsbereich von {mm(s1InhaltW)} mm (Breite minus 2 × Sicherheitsabstand)</span>
            </p>
            <Zahl label="Schreiblinien" schritt={1} min={1} max={15} bind:wert={cfg.s1.anzahl_schreiblinien} onchange={geaendert} />
            <label class="feld">Stärke in oberster Linie<input type="checkbox" bind:checked={cfg.s1.staerke_anzeigen} onchange={geaendert} /></label>
          </fieldset>
          <fieldset>
            <legend>Max. Grafikgröße (alle Zeichen)</legend>
            <label class="feld">
              Grafikgröße begrenzen
              <input type="checkbox" checked={cfg.grafik_max_mm !== null} onchange={(e) => grafikMaxUmschalten(e.currentTarget.checked)} />
            </label>
            {#if cfg.grafik_max_mm}
              <Zahl label="Max. Breite" einheit="mm" bind:wert={cfg.grafik_max_mm[0]} onchange={geaendert} />
              <Zahl label="Max. Höhe" einheit="mm" bind:wert={cfg.grafik_max_mm[1]} onchange={geaendert} />
            {/if}
            <p class="muted klein">
              Damit werden alle Grafiken höchstens so groß – für ein einheitliches Bild. Einzelne Zeichen
              können in der Vorschau abweichen („Max. Grafikgröße abweichend“).
            </p>
          </fieldset>
        </div>
      {:else if tab === "text"}
        <div class="spalten">
          <fieldset>
            <legend>Schrift</legend>
            <label class="feld">
              Schriftart
              <input type="text" list="schriften" bind:value={cfg.text.font_family} onchange={geaendert} />
            </label>
            <datalist id="schriften">
              {#each schriften as s (s)}<option value={s}></option>{/each}
            </datalist>
            <Zahl label="Schriftgröße" einheit="pt" schritt={1} min={8} bind:wert={cfg.text.font_size_pt} onchange={geaendert} />
            <label class="feld" title="45–48 mm → 10 pt, sonst proportional zur Höhe (mind. 8 pt)">
              Schriftgröße mit Zeichenhöhe anpassen
              <input
                type="checkbox"
                bind:checked={cfg.text.schrift_mitwachsen}
                onchange={() => (cfg.text.schrift_mitwachsen ? hoeheGeaendert() : geaendert())}
              />
            </label>
            <p class="muted klein">
              Beim Ändern der Zeichenhöhe oder Wechsel S1/S2 wird die Schriftgröße automatisch gesetzt
              (45–48 mm → 10 pt, sonst proportional). Danach kann sie weiter angepasst werden.
            </p>
            <Zahl label="Zeilenabstand" einheit="× Schriftgröße" schritt={0.1} bind:wert={cfg.text.zeilenabstand_faktor} onchange={geaendert} />
            <Zahl label="Mindest-Schriftgröße bei langem Text" einheit="pt" bind:wert={cfg.text.min_schrift_pt} onchange={geaendert} />
            <Zahl label="Abstand Grafik → Text" einheit="mm" bind:wert={cfg.text.abstand_grafik_text_mm} onchange={geaendert} />
            <Zahl label="Abstand Text → unten" einheit="mm" bind:wert={cfg.text.text_unten_mm} onchange={geaendert} />
          </fieldset>
          <fieldset>
            <legend>Stärke-Felder (Stellen)</legend>
            <Zahl label="Führer" schritt={1} bind:wert={cfg.text.staerke_stellen[0]} onchange={geaendert} />
            <Zahl label="Unterführer" schritt={1} bind:wert={cfg.text.staerke_stellen[1]} onchange={geaendert} />
            <Zahl label="Helfer" schritt={1} bind:wert={cfg.text.staerke_stellen[2]} onchange={geaendert} />
            <Zahl label="Gesamt" schritt={1} bind:wert={cfg.text.staerke_stellen[3]} onchange={geaendert} />
            <div class="zweite">Linien</div>
            <Zahl label="Schreiblinie" einheit="mm" schritt={0.05} bind:wert={cfg.linien.schreiblinie_mm} onchange={geaendert} />
            <Zahl label="Schreiblinie Rand" einheit="mm" bind:wert={cfg.linien.schreiblinie_rand_mm} onchange={geaendert} />
            <Zahl label="Schnittlinie" einheit="mm" schritt={0.05} bind:wert={cfg.linien.schnittlinie_mm} onchange={geaendert} />
          </fieldset>
        </div>
      {:else}
        <div class="spalten">
          <fieldset>
            <legend>PDF</legend>
            <label class="feld">Text in Pfade umwandeln<input type="checkbox" bind:checked={cfg.export.text_als_pfade} onchange={geaendert} /></label>
            <p class="muted klein">Empfohlen für Druckereien. Aus = Schrift wird eingebettet (Text bleibt auswählbar).</p>
            <label class="feld">Schnittlinien standardmäßig<input type="checkbox" bind:checked={cfg.export.schnittlinien} onchange={geaendert} /></label>
            <label class="feld">Druckhinweis auf Schnittbogen<input type="checkbox" bind:checked={cfg.export.druckhinweis} onchange={geaendert} /></label>
            <Zahl label="Bogenrand links/rechts" einheit="mm" bind:wert={cfg.export.bogen_rand_horizontal_mm} onchange={geaendert} />
            <Zahl label="Bogenrand oben/unten" einheit="mm" bind:wert={cfg.export.bogen_rand_vertikal_mm} onchange={geaendert} />
          </fieldset>
          <fieldset>
            <legend>PNG</legend>
            <Zahl label="Auflösung" einheit="DPI" schritt={50} min={72} max={1200} bind:wert={cfg.export.png_dpi} onchange={geaendert} />
            <label class="feld">
              Weißer statt transparenter Hintergrund
              <input type="checkbox" bind:checked={cfg.export.png_hintergrund_weiss} onchange={geaendert} />
            </label>
            <p class="muted klein">
              Transparent eignet sich zum Weiterverwenden (z.B. in Dokumenten). Weiß, wenn ein Programm oder
              Druckdienst transparente Bereiche falsch (z.B. schwarz) darstellt. PDFs haben nie einen Hintergrund.
            </p>
          </fieldset>
        </div>
      {/if}
      {#each fehler as f (f)}<div class="hinweis fehler">{f}</div>{/each}
    </div>
    <aside class="live">
      <div class="live-kopf">
        <strong>Live-Vorschau</strong>
        <div class="segment" role="group" aria-label="Layout der Vorschau">
          <button class:aktiv={cfg.layout === "s2"} onclick={() => layoutSetzen("s2")} title="Einzelschild (aktiviert S2)">S2</button>
          <button class:aktiv={cfg.layout === "s1"} onclick={() => layoutSetzen("s1")} title="Doppelschild (aktiviert S1)">S1</button>
        </div>
      </div>
      <div class="muted klein" title={beispiel.titel}>{beispiel.titel}</div>
      <label class="check klein"><input type="checkbox" bind:checked={vorschauSchnitt} /> Schnitt- und Hilfslinien</label>
      <ZeichenBild spec={beispiel.spec} schnittlinien={vorschauSchnitt} maxHoehe="46vh" />
    </aside>
    </div>
    <footer>
      <button onclick={zuruecksetzen}>Werkseinstellungen</button>
      <button
        onclick={() => api.pfadOeffnen(store.info?.daten_ordner ?? "")}
        title="Ordner mit settings.json und Logs: {store.info?.daten_ordner ?? ''}"
      >
        Daten- und Log-Ordner
      </button>
      <button
        onclick={() => {
          if (store.einstellungen && store.info) {
            store.einstellungen.oberflaeche = { ...store.info.standard_oberflaeche };
            store.speichern();
          }
        }}
        title="Größen von Kategorien, Vorlagen, Auftrag und Vorschau zurücksetzen"
      >
        Ansicht zurücksetzen
      </button>
      <span class="spacer"></span>
      <button class="primary" onclick={schliessen}>Fertig</button>
    </footer>
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(10, 16, 24, 0.45);
    display: grid;
    place-items: center;
    z-index: 10;
  }
  .dialog {
    background: var(--panel);
    border-radius: 10px;
    box-shadow: var(--shadow);
    width: min(1240px, calc(100vw - 32px));
    /* Feste Hoehe: der Dialog springt nicht, wenn Meldungen erscheinen */
    height: min(820px, calc(100vh - 48px));
    display: flex;
    flex-direction: column;
  }
  header,
  footer {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
  }
  header {
    border-bottom: 1px solid var(--border);
  }
  footer {
    border-top: 1px solid var(--border);
  }
  h3 {
    margin: 0;
    font-size: 16px;
  }
  nav {
    display: flex;
    gap: 4px;
    padding: 8px 16px 0;
  }
  nav button.aktiv {
    background: var(--accent-soft);
    border-color: var(--accent);
  }
  .koerper {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(300px, 400px);
    min-height: 0;
    flex: 1;
  }
  .inhalt {
    padding: 12px 16px;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .live {
    border-left: 1px solid var(--border);
    padding: 12px 16px;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .live-kopf {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .segment {
    display: flex;
  }
  .segment button {
    border-radius: 0;
    margin-left: -1px;
    padding: 2px 10px;
  }
  .segment button:first-child {
    border-radius: var(--radius) 0 0 var(--radius);
  }
  .segment button:last-child {
    border-radius: 0 var(--radius) var(--radius) 0;
  }
  .segment button.aktiv {
    background: var(--accent);
    color: var(--accent-text);
    border-color: var(--accent);
  }
  .check {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  fieldset.aktiv {
    border-color: var(--accent);
  }
  .masse {
    font-size: 12px;
    margin: 6px 0 0;
    line-height: 1.5;
  }
  .spalten {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 12px;
  }
  fieldset {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 8px 12px 10px;
    margin: 0;
  }
  legend {
    font-weight: 600;
    padding: 0 4px;
  }
  .zweite {
    margin-top: 10px;
    font-weight: 600;
  }
  .klein {
    font-size: 12px;
    margin: 0 0 6px;
  }
  .feld input[type="text"] {
    width: 180px;
  }
</style>
