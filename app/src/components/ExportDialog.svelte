<script lang="ts">
  import { open } from "@tauri-apps/plugin-dialog";
  import { onDestroy } from "svelte";
  import { api, fehlerText } from "../lib/api";
  import { store } from "../lib/store.svelte";
  import type {
    BogenLayout,
    DruckConfig,
    ExportAuftrag,
    ExportBericht,
    ExportFormat,
    Fortschritt,
    SchriftProblem,
    VorlageRef,
  } from "../lib/types";

  let { schliessen }: { schliessen: () => void } = $props();

  const FORMATE: { id: ExportFormat; label: string; info: string }[] = [
    { id: "pdf_einzel", label: "PDF – Einzelzeichen", info: "Eine Seite pro Zeichen mit Beschnittzugabe (für Druckereien)." },
    { id: "pdf_bogen", label: "PDF – Schnittbogen", info: "Zeichen in Endgröße im Raster auf DIN A4 (zum Selbstdrucken)." },
    { id: "png", label: "PNG – Einzeldateien", info: "Rasterbild pro Zeichen in der eingestellten Auflösung." },
  ];

  let format = $state<ExportFormat>(store.einstellungen?.export_format ?? "pdf_einzel");
  let schnittlinien = $state(store.config.export.schnittlinien);
  let aufteilen = $state(false);
  let proDatei = $state(100);
  let laeuft = $state(false);
  let fortschritt = $state<Fortschritt | null>(null);
  let bericht = $state<ExportBericht | null>(null);
  let fehler = $state<string | null>(null);
  let bogen = $state<BogenLayout | null>(null);
  let bogenFehler = $state<string | null>(null);

  const ziel = $derived(store.ausgabeOrdner);

  // Vorab-Pruefung: fehlende Schriften in Vorlagen
  let schriftProbleme = $state<SchriftProblem[]>([]);
  // Frische Pruefung beim Oeffnen: nicht lesbare Vorlagen blockieren den Export
  let geprueft = $state(false);
  store.pruefen().finally(() => (geprueft = true));
  const blockiert = $derived(store.fehlerhafte);
  api
    .schriftenPruefen(store.posten.map((p) => $state.snapshot(p.vorlage) as VorlageRef))
    .then((p) => (schriftProbleme = p))
    .catch(() => {});

  $effect(() => {
    if (format !== "pdf_bogen") return;
    api
      .bogenLayout($state.snapshot(store.config) as DruckConfig)
      .then((b) => ((bogen = b), (bogenFehler = null)))
      .catch((e) => ((bogen = null), (bogenFehler = fehlerText(e))));
  });

  let abmelden: (() => void) | null = null;
  api.aufFortschritt((f) => (fortschritt = f)).then((u) => (abmelden = u));
  onDestroy(() => abmelden?.());

  async function zielWaehlen(): Promise<void> {
    const o = await open({ directory: true, defaultPath: ziel, title: "Ausgabeordner wählen" });
    if (typeof o === "string" && store.einstellungen) {
      store.einstellungen.ausgabe_ordner = o;
      store.speichern();
    }
  }

  async function starten(): Promise<void> {
    if (!store.einstellungen) return;
    store.einstellungen.export_format = format;
    store.speichern();
    const auftrag: ExportAuftrag = {
      // Reihenfolge wie in der Auftragsliste angezeigt (nach Kategorien gruppiert)
      posten: store.postenSortiert.map((p) => ({
        vorlage: $state.snapshot(p.vorlage),
        modus: p.modus,
        text: p.text,
        grafik_position: p.grafik_position,
        grafik_max_mm: $state.snapshot(p.grafik_max_mm),
        drei_zeilen: p.drei_zeilen ?? false,
        kopien: Math.max(1, Math.round(p.kopien || 1)),
      })),
      config: $state.snapshot(store.config) as DruckConfig,
      format,
      ziel_ordner: ziel,
      schnittlinien,
      zeichen_pro_datei: aufteilen && format !== "png" ? proDatei : null,
    };
    laeuft = true;
    fehler = null;
    bericht = null;
    fortschritt = null;
    try {
      bericht = await api.exportieren(auftrag);
    } catch (e) {
      fehler = fehlerText(e);
    } finally {
      laeuft = false;
    }
  }

  function zu(): void {
    if (!laeuft) schliessen();
  }
</script>

<svelte:window onkeydown={(e) => e.key === "Escape" && !store.rueckfrage && zu()} />

<div class="overlay" role="presentation" onclick={(e) => e.target === e.currentTarget && zu()}>
  <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="export-titel">
    <header>
      <h3 id="export-titel">Exportieren</h3>
      <span class="muted">{store.anzahlZeichen} Zeichen</span>
      <span class="spacer"></span>
      <button class="ghost" onclick={zu} disabled={laeuft} aria-label="Schließen">✕</button>
    </header>
    <div class="inhalt">
      <div class="formate">
        {#each FORMATE as f (f.id)}
          <label class="format" class:aktiv={format === f.id}>
            <input type="radio" name="format" value={f.id} bind:group={format} disabled={laeuft} />
            <span><strong>{f.label}</strong><br /><span class="muted">{f.info}</span></span>
          </label>
        {/each}
      </div>

      {#if blockiert.length > 0}
        <div class="hinweis fehler">
          <strong>Export nicht möglich:</strong> {blockiert.length} Vorlage(n) sind nicht lesbar. Die Zeilen sind im
          Auftrag rot markiert – bitte entfernen oder die Vorlage reparieren.
          <ul>
            {#each blockiert as p (p.id)}
              <li>{p.name}: {store.pruefung[p.id]?.fehler}</li>
            {/each}
          </ul>
        </div>
      {/if}

      {#if schriftProbleme.length > 0}
        <div class="hinweis">
          <strong>Fehlende Schriften in Vorlagen</strong> – diese werden beim Export durch eine Ersatzschrift
          ersetzt. Schrift installieren oder in den Ordner <code>fonts</code> neben der EXE legen.
          <ul>
            {#each schriftProbleme as p (p.pfad)}
              <li>{p.vorlage}: {p.schriften.join(", ")}</li>
            {/each}
          </ul>
        </div>
      {/if}

      {#if format === "pdf_bogen"}
        {#if bogen}
          <p class="muted">
            {bogen.spalten} × {bogen.zeilen} = {bogen.spalten * bogen.zeilen} Zeichen pro Seite ({bogen.querformat ? "Querformat" : "Hochformat"}),
            {Math.ceil(store.anzahlZeichen / (bogen.spalten * bogen.zeilen))} Seite(n)
          </p>
        {:else if bogenFehler}
          <div class="hinweis fehler">{bogenFehler}</div>
        {/if}
      {/if}

      <label class="feld"><span>Schnittlinien einzeichnen</span><input type="checkbox" bind:checked={schnittlinien} disabled={laeuft} /></label>
      {#if format !== "png"}
        <label class="feld"><span>Auf mehrere PDF-Dateien aufteilen</span><input type="checkbox" bind:checked={aufteilen} disabled={laeuft} /></label>
        {#if aufteilen}
          <label class="feld"><span>Zeichen pro Datei</span><input type="number" min="1" bind:value={proDatei} disabled={laeuft} /></label>
        {/if}
      {/if}
      <div class="ziel">
        <span class="muted">Ziel:</span>
        <code title={ziel}>{ziel}</code>
        <button onclick={zielWaehlen} disabled={laeuft}>Ändern…</button>
      </div>

      {#if laeuft}
        <div class="fortschritt">
          <progress max={fortschritt?.gesamt ?? 1} value={fortschritt?.fertig ?? 0}></progress>
          <span class="muted">{fortschritt?.schritt ?? "Starte …"}</span>
        </div>
      {/if}
      {#if fehler}<div class="hinweis fehler">{fehler}</div>{/if}
      {#if bericht}
        <div class="ergebnis">
          <strong>Fertig:</strong> {bericht.anzahl_zeichen} Zeichen, {bericht.anzahl_seiten}
          {format === "png" ? "Datei(en)" : bericht.anzahl_seiten === 1 ? "Seite" : "Seiten"} in
          {(bericht.dauer_ms / 1000).toFixed(1)} s
          <button onclick={() => api.pfadOeffnen(bericht!.ordner)}>Ordner öffnen</button>
        </div>
        {#if bericht.hinweise.length > 0}
          <details open={bericht.hinweise.length <= 5}>
            <summary>
              {bericht.hinweise.length} Hinweis(e)
              {#if bericht.bericht_datei}
                – gespeichert in
                <button class="link" onclick={() => api.pfadOeffnen(bericht!.bericht_datei!)}>Hinweise.txt</button>
              {/if}
            </summary>
            {#each bericht.hinweise as h, i (i)}
              <div class="hinweis">#{h.position} {h.zeichen}: {h.hinweis.text}</div>
            {/each}
          </details>
        {/if}
      {/if}
    </div>
    <footer>
      {#if laeuft}
        <button onclick={() => api.exportAbbrechen()}>Abbrechen</button>
      {/if}
      <span class="spacer"></span>
      <button onclick={zu} disabled={laeuft}>Schließen</button>
      <button
        class="primary"
        onclick={starten}
        disabled={laeuft || store.posten.length === 0 || !geprueft || blockiert.length > 0}
      >
        Export starten
      </button>
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
    width: min(640px, calc(100vw - 32px));
    max-height: calc(100vh - 48px);
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
  .inhalt {
    padding: 12px 16px;
    overflow-x: hidden;
    overflow-y: auto;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .formate {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .format {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 8px 10px;
    cursor: pointer;
  }
  .format.aktiv {
    border-color: var(--accent);
    background: var(--accent-soft);
  }
  .ziel {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  code {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
  }
  .fortschritt {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  progress {
    width: 100%;
  }
  .ergebnis {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    color: var(--ok);
  }
  .ergebnis button {
    margin-left: auto;
  }
  .link {
    border: none;
    background: none;
    padding: 0;
    color: var(--accent);
    text-decoration: underline;
  }
  ul {
    margin: 4px 0 0;
    padding-left: 18px;
  }
</style>
