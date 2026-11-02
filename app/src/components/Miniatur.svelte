<script lang="ts">
  import { api } from "../lib/api";
  import type { VorlageInfo } from "../lib/types";

  const cache = new Map<string, Promise<string>>();

  /** `px` = gewuenschte Kantenlaenge (wird auf Stufen gerundet, damit der Cache greift). */
  let { vorlage, px = 160 }: { vorlage: VorlageInfo; px?: number } = $props();

  const STUFEN = [96, 160, 256, 384];
  const stufe = $derived(STUFEN.find((s) => s >= px * (window.devicePixelRatio || 1)) ?? STUFEN[STUFEN.length - 1]);

  let element: HTMLDivElement | undefined = $state();
  let sichtbar = $state(false);
  let bild = $state<string | null>(null);
  let fehler = $state(false);

  $effect(() => {
    if (!element) return;
    const obs = new IntersectionObserver((e) => {
      if (e.some((x) => x.isIntersecting)) {
        sichtbar = true;
        obs.disconnect();
      }
    });
    obs.observe(element);
    return () => obs.disconnect();
  });

  $effect(() => {
    const v = vorlage.vorlage;
    if (!sichtbar || v.art !== "datei") return;
    const schluessel = `${stufe}|${v.pfad}`;
    let p = cache.get(schluessel);
    if (!p) {
      p = api.miniatur(v.pfad, stufe);
      cache.set(schluessel, p);
      p.catch(() => cache.delete(schluessel));
    }
    p.then((b) => (bild = b)).catch(() => (fehler = true));
  });
</script>

<div class="mini" bind:this={element}>
  {#if vorlage.vorlage.art === "blanko"}
    <span class="blanko">Blanko</span>
  {:else if bild}
    <img src={bild} alt={vorlage.name} />
  {:else if fehler}
    <span class="fehler" title="Vorlage nicht lesbar">!</span>
  {/if}
</div>

<style>
  .mini {
    width: 100%;
    aspect-ratio: 1;
    display: grid;
    place-items: center;
    background: #fff;
    border-radius: 4px;
    overflow: hidden;
  }
  img {
    max-width: 92%;
    max-height: 92%;
  }
  .blanko {
    font-size: 11px;
    color: #667;
    border: 1px dashed #99a;
    padding: 18% 10%;
  }
  .fehler {
    color: #b42318;
    font-weight: 700;
    font-size: 20px;
  }
</style>
