<script lang="ts">
  import { open, save } from "@tauri-apps/plugin-dialog";
  import AuftragListe from "./components/AuftragListe.svelte";
  import EinstellungenDialog from "./components/EinstellungenDialog.svelte";
  import ExportDialog from "./components/ExportDialog.svelte";
  import HilfeMenu from "./components/HilfeMenu.svelte";
  import KategorieBaum from "./components/KategorieBaum.svelte";
  import Rueckfrage from "./components/Rueckfrage.svelte";
  import Splash from "./components/Splash.svelte";
  import Tour from "./components/Tour.svelte";
  import UeberDialog from "./components/UeberDialog.svelte";
  import Trenner from "./components/Trenner.svelte";
  import VorlagenGrid from "./components/VorlagenGrid.svelte";
  import Vorschau from "./components/Vorschau.svelte";
  import { api, fehlerText } from "./lib/api";
  import { store } from "./lib/store.svelte";
  import type { Layout, Session } from "./lib/types";

  const SESSION_FILTER = [{ name: "Druckgenerator-Session", extensions: ["tzdg.json", "json"] }];

  let dialog = $state<"einstellungen" | "export" | "ueber" | null>(null);

  // ---------------------------------------------------------------------------------------------
  // Splash-Screen: bleibt sichtbar, bis alles geladen ist - mindestens SPLASH_MIN_MS.
  // Die Mindestdauer kann hier angepasst werden (Millisekunden).
  // ---------------------------------------------------------------------------------------------
  const SPLASH_MIN_MS = 2500;
  let splash = $state(true);
  let tour = $state<{ ersterStart: boolean } | null>(null);

  async function starten(): Promise<void> {
    const beginn = performance.now();
    await store.start();
    const rest = SPLASH_MIN_MS - (performance.now() - beginn);
    if (rest > 0) await new Promise((r) => setTimeout(r, rest));
    splash = false;
    // Einfuehrungstour beim ersten Start
    if (store.einstellungen && !store.einstellungen.tour_gesehen) tour = { ersterStart: true };
  }

  function tourEnde(nichtMehrZeigen: boolean): void {
    tour = null;
    if (store.einstellungen && nichtMehrZeigen) {
      store.einstellungen.tour_gesehen = true;
      store.speichern();
    }
  }

  // Ziehbare Bereichsgroessen (gespeichert in settings.json -> oberflaeche)
  const GRENZEN = {
    kategorienMin: 160,
    vorschauMin: 300,
    mitteMin: 380,
    trenner: 8,
    anteilMin: 0.15,
    anteilMax: 0.85,
  };
  let hauptEl: HTMLElement | undefined = $state();
  let mitteEl: HTMLElement | undefined = $state();

  const ob = $derived(store.einstellungen?.oberflaeche ?? store.info?.standard_oberflaeche ?? null);

  function begrenze(v: number, min: number, max: number): number {
    return Math.min(Math.max(v, min), Math.max(min, max));
  }

  /** Platz, der fuer Kategorien + Vorschau maximal zur Verfuegung steht. */
  function seitenPlatz(): number {
    const breite = hauptEl?.clientWidth ?? 1400;
    return breite - GRENZEN.mitteMin - 2 * GRENZEN.trenner;
  }

  function kategorienZiehen(d: number): void {
    if (!ob) return;
    ob.kategorien_px = begrenze(ob.kategorien_px + d, GRENZEN.kategorienMin, seitenPlatz() - ob.vorschau_px);
  }

  function vorschauZiehen(d: number): void {
    if (!ob) return;
    ob.vorschau_px = begrenze(ob.vorschau_px - d, GRENZEN.vorschauMin, seitenPlatz() - ob.kategorien_px);
  }

  function anteilZiehen(d: number): void {
    if (!ob) return;
    const hoehe = mitteEl?.clientHeight ?? 800;
    ob.vorlagen_anteil = begrenze(ob.vorlagen_anteil + d / hoehe, GRENZEN.anteilMin, GRENZEN.anteilMax);
  }

  function standard(): NonNullable<typeof ob> | null {
    return store.info?.standard_oberflaeche ?? null;
  }

  starten();

  // Auftrag nach jeder Aenderung (Posten oder Druckeinstellungen) verzoegert pruefen
  const PRUEF_VERZOEGERUNG_MS = 300;
  $effect(() => {
    if (!store.einstellungen) return;
    // Snapshots lesen -> jede Aenderung an Posten/Konfiguration loest die Pruefung aus
    $state.snapshot(store.posten);
    $state.snapshot(store.config);
    const t = setTimeout(() => store.pruefen(), PRUEF_VERZOEGERUNG_MS);
    return () => clearTimeout(t);
  });

  async function ordnerWaehlen(): Promise<void> {
    const o = await open({ directory: true, defaultPath: store.vorlagenOrdner, title: "Vorlagenordner wählen" });
    if (typeof o === "string" && store.einstellungen) {
      store.einstellungen.vorlagen_ordner = o;
      store.kategoriePfad = "";
      store.speichern();
      await store.katalogNeuLaden();
    }
  }

  function layoutSetzen(l: Layout): void {
    if (!store.einstellungen) return;
    store.einstellungen.config.layout = l;
    store.speichern();
    void store.schriftAnpassen();
  }

  async function exportOeffnen(): Promise<void> {
    if (await store.darfWechseln()) dialog = "export";
  }

  async function sessionSpeichern(): Promise<void> {
    if (!(await store.darfWechseln())) return;
    const pfad = await save({ filters: SESSION_FILTER, defaultPath: "Auftrag.tzdg.json" });
    if (!pfad) return;
    try {
      await api.jsonSpeichern(pfad, store.session());
      store.hinweis(`Session gespeichert: ${pfad}`);
    } catch (e) {
      store.fehler(fehlerText(e));
    }
  }

  async function sessionLaden(): Promise<void> {
    if (!(await store.darfWechseln())) return;
    if (
      store.posten.length > 0 &&
      !(await store.bestaetigen("Session öffnen", "Der aktuelle Auftrag wird ersetzt.", "Weiter"))
    )
      return;
    const pfad = await open({ filters: SESSION_FILTER, multiple: false });
    if (typeof pfad !== "string") return;
    try {
      const s = await api.jsonLaden<Session>(pfad);
      const mitConfig = await store.bestaetigen(
        "Druckeinstellungen",
        "Auch die Druckeinstellungen (Größen, Schrift, …) aus der Session übernehmen?",
        "Übernehmen",
      );
      store.sessionUebernehmen(s, mitConfig);
      store.hinweis(`Session geladen: ${s.posten.length} Positionen`);
    } catch (e) {
      store.fehler(`Session nicht lesbar: ${fehlerText(e)}`);
    }
  }
</script>

{#if splash}
  <Splash />
{:else if !store.einstellungen}
  <div class="laden">
    {#if store.meldung?.art === "fehler"}
      <div class="hinweis fehler">{store.meldung.text}</div>
    {:else}
      <span class="muted">Lade …</span>
    {/if}
  </div>
{:else}
  <div class="app">
    <header class="leiste">
      <strong class="titel">Taktische Zeichen Druckgenerator</strong>
      <span class="muted version">v{store.info?.version}</span>
      <div class="gruppe">
        <button onclick={ordnerWaehlen} title={store.vorlagenOrdner}>Vorlagenordner…</button>
        <button onclick={() => store.katalogNeuLaden()} title="Vorlagen neu einlesen (F5)">Neu laden</button>
      </div>
      <div class="gruppe" data-tour="layout">
      <div class="gruppe segment" role="group" aria-label="Layout">
        <button class:aktiv={store.config.layout === "s2"} onclick={() => layoutSetzen("s2")} title="Einzelschild">S2</button>
        <button class:aktiv={store.config.layout === "s1"} onclick={() => layoutSetzen("s1")} title="Doppelschild mit Schreiblinien">S1</button>
      </div>
      <label class="gruppe">
        <span class="muted">Standard-Modus</span>
        <select bind:value={store.einstellungen.standard_modus} onchange={() => store.speichern()}>
          {#each store.info?.modi ?? [] as m (m.id)}<option value={m.id}>{m.label}</option>{/each}
        </select>
      </label>
      </div>
      <span class="spacer"></span>
      <div class="gruppe">
        <button onclick={sessionLaden}>Session öffnen…</button>
        <button onclick={sessionSpeichern} disabled={store.posten.length === 0}>Session speichern…</button>
        <button
          onclick={() => api.ordnerOeffnen(store.ausgabeOrdner).catch((e) => store.fehler(fehlerText(e)))}
          title="Ordner mit allen Exporten öffnen: {store.ausgabeOrdner}"
        >
          Ausgabeordner
        </button>
        <button onclick={() => (dialog = "einstellungen")} data-tour="einstellungen">Einstellungen</button>
        <button class="primary" onclick={exportOeffnen} disabled={store.posten.length === 0} data-tour="export">
          Exportieren ({store.anzahlZeichen})
        </button>
        <HilfeMenu tourStarten={() => (tour = { ersterStart: false })} ueberZeigen={() => (dialog = "ueber")} />
      </div>
    </header>

    {#if store.meldung}
      <div class="meldung hinweis" class:fehler={store.meldung.art === "fehler"} class:info={store.meldung.art === "info"}>
        {store.meldung.text}
        <button class="ghost icon" onclick={() => (store.meldung = null)} aria-label="Meldung schließen">✕</button>
      </div>
    {/if}

    <main
      bind:this={hauptEl}
      style:grid-template-columns="{ob?.kategorien_px ?? 240}px {GRENZEN.trenner}px minmax({GRENZEN.mitteMin}px, 1fr) {GRENZEN.trenner}px {ob?.vorschau_px ?? 400}px"
    >
      <aside class="panel kategorien" data-tour="kategorien">
        <div class="panel-head"><h2>Kategorien</h2></div>
        <div class="panel-body baum">
          {#if store.katalog}
            <KategorieBaum kategorie={store.katalog} gewaehlt={store.kategoriePfad} waehle={(p) => (store.kategoriePfad = p)} />
          {:else if store.katalogFehler}
            <div class="hinweis fehler">{store.katalogFehler}</div>
            <button onclick={ordnerWaehlen}>Ordner wählen…</button>
          {/if}
          {#if store.katalogHinweis}
            <div class="hinweis">{store.katalogHinweis}</div>
          {/if}
          {#if store.info}
            <div class="linie"></div>
            <button class="ghost blanko" class:aktiv={store.kategoriePfad === "#blanko"} onclick={() => (store.kategoriePfad = "#blanko")}>
              {store.info.blanko.name}
            </button>
          {/if}
        </div>
      </aside>
      <Trenner
        richtung="spalte"
        ziehen={kategorienZiehen}
        ende={() => store.speichern()}
        zuruecksetzen={() => ob && standard() && (ob.kategorien_px = standard()!.kategorien_px)}
      />
      <div
        class="mitte"
        bind:this={mitteEl}
        style:grid-template-rows="minmax(120px, {ob?.vorlagen_anteil ?? 0.5}fr) {GRENZEN.trenner}px minmax(120px, {1 -
          (ob?.vorlagen_anteil ?? 0.5)}fr)"
      >
        <div class="oben" data-tour="vorlagen"><VorlagenGrid /></div>
        <Trenner
          richtung="zeile"
          ziehen={anteilZiehen}
          ende={() => store.speichern()}
          zuruecksetzen={() => ob && standard() && (ob.vorlagen_anteil = standard()!.vorlagen_anteil)}
        />
        <div class="unten" data-tour="auftrag"><AuftragListe /></div>
      </div>
      <Trenner
        richtung="spalte"
        ziehen={vorschauZiehen}
        ende={() => store.speichern()}
        zuruecksetzen={() => ob && standard() && (ob.vorschau_px = standard()!.vorschau_px)}
      />
      <aside class="rechts" data-tour="vorschau"><Vorschau /></aside>
    </main>
  </div>
{/if}

{#if dialog === "einstellungen"}
  <EinstellungenDialog schliessen={() => (dialog = null)} />
{:else if dialog === "export"}
  <ExportDialog schliessen={() => (dialog = null)} />
{:else if dialog === "ueber"}
  <UeberDialog schliessen={() => (dialog = null)} />
{/if}

{#if tour && !splash}
  <Tour ersterStart={tour.ersterStart} ende={tourEnde} />
{/if}

<Rueckfrage />

<svelte:window onkeydown={(e) => e.key === "F5" && (e.preventDefault(), store.katalogNeuLaden())} />

<style>
  .laden {
    height: 100%;
    display: grid;
    place-items: center;
  }
  .app {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 8px;
  }
  .leiste {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }
  .titel {
    font-size: 15px;
  }
  .version {
    font-size: 12px;
    margin-left: -6px;
  }
  .gruppe {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .segment button {
    border-radius: 0;
    margin-left: -1px;
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
  /* Schwebend, damit sich das Layout nicht verschiebt */
  .meldung {
    position: fixed;
    left: 50%;
    bottom: 20px;
    transform: translateX(-50%);
    z-index: 20;
    max-width: min(720px, calc(100vw - 32px));
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: var(--shadow);
    font-size: 13px;
    padding: 8px 12px;
  }
  .meldung.info {
    background: var(--accent-soft);
    color: var(--text);
  }
  .meldung button {
    margin-left: auto;
  }
  main {
    flex: 1;
    min-height: 0;
    display: grid;
  }
  .baum {
    padding: 4px;
  }
  .linie {
    border-top: 1px solid var(--border);
    margin: 6px 0;
  }
  .blanko {
    width: 100%;
    text-align: left;
  }
  .blanko.aktiv {
    background: var(--accent-soft);
  }
  .mitte {
    display: grid;
    min-height: 0;
    min-width: 0;
  }
  .oben,
  .unten,
  .rechts {
    min-height: 0;
    min-width: 0;
  }
</style>
