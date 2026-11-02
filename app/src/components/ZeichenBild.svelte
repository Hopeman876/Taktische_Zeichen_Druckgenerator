<script lang="ts">
  // Gerendertes Zeichen (Vorschau-Bild) mit Massen und Hinweisen.
  // Rendert bei jeder Aenderung von Zeichen oder Druckeinstellungen neu (verzoegert).
  import { api, fehlerText } from "../lib/api";
  import { store } from "../lib/store.svelte";
  import type { DruckConfig, Hinweis, VorschauAntwort, ZeichenSpec } from "../lib/types";

  const VORSCHAU_PX = 900;
  const VERZOEGERUNG_MS = 120;

  let {
    spec,
    schnittlinien,
    maxHoehe = "42vh",
    ergebnis,
  }: {
    spec: ZeichenSpec | null;
    schnittlinien: boolean;
    maxHoehe?: string;
    /** Rueckmeldung nach jedem Rendern (z.B. ob eine 3. Zeile moeglich ist). */
    ergebnis?: (r: VorschauAntwort | null) => void;
  } = $props();

  let bild = $state<string | null>(null);
  let hinweise = $state<Hinweis[]>([]);
  let fehler = $state<string | null>(null);
  let masse = $state("");
  let laeuft = 0;

  $effect(() => {
    if (!spec || !store.einstellungen) {
      bild = null;
      hinweise = [];
      fehler = null;
      masse = "";
      ergebnis?.(null);
      return;
    }
    // Snapshots lesen alle Felder -> jede Aenderung loest ein neues Rendern aus
    const s = $state.snapshot(spec) as ZeichenSpec;
    const config = $state.snapshot(store.config) as DruckConfig;
    const schnitt = schnittlinien;
    const nr = ++laeuft;
    const t = setTimeout(async () => {
      try {
        const r = await api.vorschau(s, config, schnitt, VORSCHAU_PX);
        if (nr !== laeuft) return;
        bild = r.bild;
        hinweise = r.hinweise;
        masse = `${r.breite_mm.toFixed(1)} × ${r.hoehe_mm.toFixed(1)} mm (inkl. Beschnitt)`;
        fehler = null;
        ergebnis?.(r);
      } catch (e) {
        if (nr === laeuft) fehler = fehlerText(e);
      }
    }, VERZOEGERUNG_MS);
    return () => clearTimeout(t);
  });
</script>

<div class="buehne">
  {#if bild}<img src={bild} alt="Vorschau" style="max-height: {maxHoehe}" />{/if}
</div>
<p class="muted masse">{masse}</p>
{#if fehler}<div class="hinweis fehler">{fehler}</div>{/if}
{#each hinweise as h, i (i)}
  <div class="hinweis">{h.text}</div>
{/each}

<style>
  .buehne {
    background: repeating-conic-gradient(var(--panel-2) 0% 25%, var(--bg) 0% 50%) 50% / 16px 16px;
    border-radius: var(--radius);
    padding: 12px;
    display: grid;
    place-items: center;
    min-height: 160px;
  }
  img {
    max-width: 100%;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.25);
    background: #fff;
  }
  .masse {
    margin: 0;
    font-size: 12px;
    text-align: center;
  }
</style>
