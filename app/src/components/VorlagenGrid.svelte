<script lang="ts">
  import { findeKategorie, store } from "../lib/store.svelte";
  import type { Kategorie, VorlageInfo } from "../lib/types";
  import Miniatur from "./Miniatur.svelte";

  let suche = $state("");

  // Zoom der Kacheln (gespeichert in settings.json -> oberflaeche.vorlagen_zoom)
  const ZOOM_MIN = 64;
  const ZOOM_MAX = 260;
  const ZOOM_SCHRITT = 16;
  const zoom = $derived(store.einstellungen?.oberflaeche.vorlagen_zoom ?? 104);

  function zoomSetzen(v: number): void {
    if (!store.einstellungen) return;
    store.einstellungen.oberflaeche.vorlagen_zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(v)));
    store.speichern();
  }

  /** Strg + Mausrad zoomt die Kacheln. */
  function rad(e: WheelEvent): void {
    if (!e.ctrlKey) return;
    e.preventDefault();
    zoomSetzen(zoom + (e.deltaY < 0 ? ZOOM_SCHRITT : -ZOOM_SCHRITT));
  }

  /** Vorlagen der gewaehlten Kategorie inkl. Unterkategorien. */
  function sammle(k: Kategorie | null): VorlageInfo[] {
    if (!k) return [];
    return [...k.vorlagen, ...k.unterkategorien.flatMap(sammle)];
  }

  const kategorie = $derived(
    store.kategoriePfad === "#blanko" ? (store.info?.blanko ?? null) : findeKategorie(store.katalog, store.kategoriePfad),
  );
  const vorlagen = $derived.by(() => {
    const alle = sammle(kategorie);
    const s = suche.trim().toLowerCase();
    return s ? alle.filter((v) => v.name.toLowerCase().includes(s)) : alle;
  });

  function schluessel(v: VorlageInfo): string {
    return v.vorlage.art === "datei" ? v.vorlage.pfad : `#${v.vorlage.blanko}`;
  }

  const gewaehlt = $derived(store.ansicht?.art === "vorlage" ? schluessel(store.ansicht.vorlage) : null);
</script>

<section class="panel">
  <div class="panel-head">
    <h2>Vorlagen</h2>
    <span class="muted">{kategorie?.name ?? ""} · {vorlagen.length}</span>
    <span class="spacer"></span>
    <label class="zoom" title="Größe der Vorschaubilder (auch Strg + Mausrad)">
      <span aria-hidden="true">🔍</span>
      <input
        type="range"
        min={ZOOM_MIN}
        max={ZOOM_MAX}
        step="8"
        value={zoom}
        oninput={(e) => zoomSetzen(Number(e.currentTarget.value))}
        aria-label="Größe der Vorschaubilder"
      />
    </label>
    <input type="text" placeholder="Suchen…" bind:value={suche} aria-label="Vorlagen durchsuchen" />
    <button
      onclick={() => store.alleHinzufuegen(vorlagen)}
      disabled={vorlagen.length === 0}
      title="Alle angezeigten Vorlagen mit Standard-Parametern zum Auftrag hinzufügen"
    >
      Alle hinzufügen
    </button>
  </div>
  <div
    class="panel-body"
    {@attach (el) => {
      // nicht passiv, damit preventDefault das Seiten-Zoom des WebViews verhindert
      el.addEventListener("wheel", rad, { passive: false });
      return () => el.removeEventListener("wheel", rad);
    }}
  >
    {#if vorlagen.length === 0}
      <p class="muted leer">Keine Vorlagen in dieser Kategorie.</p>
    {:else}
      <div class="grid" style:grid-template-columns="repeat(auto-fill, minmax({zoom}px, 1fr))">
        {#each vorlagen as v (schluessel(v))}
          <button
            class="karte"
            class:gewaehlt={gewaehlt === schluessel(v)}
            onclick={() => store.vorlageAnsehen(v)}
            title="{v.name} – Klick zeigt die Vorlage in der Vorschau"
          >
            <Miniatur vorlage={v} px={zoom} />
            <span class="name">{v.name}</span>
            {#if v.format === "png" || v.format === "jpg"}<span class="format">{v.format.toUpperCase()}</span>{/if}
          </button>
        {/each}
      </div>
    {/if}
  </div>
</section>

<style>
  section {
    height: 100%;
  }
  input {
    width: 160px;
  }
  .leer {
    padding: 16px;
  }
  .zoom {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
  }
  .zoom input {
    width: 90px;
  }
  .grid {
    display: grid;
    gap: 8px;
    padding: 10px;
  }
  .karte {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 6px;
    background: var(--panel-2);
    white-space: normal;
  }
  .karte.gewaehlt {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent);
  }
  .name {
    font-size: 12px;
    line-height: 1.25;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    word-break: break-word;
  }
  .format {
    position: absolute;
    top: 8px;
    right: 8px;
    font-size: 10px;
    background: var(--accent);
    color: var(--accent-text);
    border-radius: 3px;
    padding: 0 4px;
  }
</style>
