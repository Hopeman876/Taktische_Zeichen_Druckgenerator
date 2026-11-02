<script lang="ts">
  // Einfuehrungstour: hebt nacheinander Bereiche hervor (data-tour="...") und erklaert sie.
  import { TOUR_SCHRITTE } from "../lib/tour";

  let { ende, ersterStart = false }: { ende: (nichtMehrZeigen: boolean) => void; ersterStart?: boolean } = $props();

  const ABSTAND_PX = 12;
  const KARTE_BREITE_PX = 340;
  const RAND_PX = 8;

  let index = $state(0);
  let nichtMehrZeigen = $state(true);
  let rechteck = $state<DOMRect | null>(null);
  let karteEl: HTMLDivElement | undefined = $state();
  let kartePos = $state({ links: 0, oben: 0 });

  const schritt = $derived(TOUR_SCHRITTE[index]);
  const letzter = $derived(index === TOUR_SCHRITTE.length - 1);

  function messen(): void {
    const el = schritt.ziel ? document.querySelector(`[data-tour="${schritt.ziel}"]`) : null;
    rechteck = el ? el.getBoundingClientRect() : null;
    // Karte neben das Ziel setzen (rechts, sonst links, sonst darunter), im Fenster halten
    const kh = karteEl?.offsetHeight ?? 200;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    if (!rechteck) {
      kartePos = { links: (vw - KARTE_BREITE_PX) / 2, oben: (vh - kh) / 2 };
      return;
    }
    let links: number;
    if (rechteck.right + ABSTAND_PX + KARTE_BREITE_PX < vw) links = rechteck.right + ABSTAND_PX;
    else if (rechteck.left - ABSTAND_PX - KARTE_BREITE_PX > 0) links = rechteck.left - ABSTAND_PX - KARTE_BREITE_PX;
    else links = Math.min(Math.max(rechteck.left, RAND_PX), vw - KARTE_BREITE_PX - RAND_PX);
    let oben = rechteck.top;
    if (links >= rechteck.left && links < rechteck.right) oben = rechteck.bottom + ABSTAND_PX;
    oben = Math.min(Math.max(oben, RAND_PX), vh - kh - RAND_PX);
    kartePos = { links, oben };
  }

  $effect(() => {
    void index;
    void karteEl;
    // nach dem Rendern messen
    requestAnimationFrame(messen);
  });

  function beenden(): void {
    ende(ersterStart ? nichtMehrZeigen : true);
  }

  function taste(e: KeyboardEvent): void {
    if (e.key === "Escape") beenden();
    else if (e.key === "ArrowRight" && !letzter) index++;
    else if (e.key === "ArrowLeft" && index > 0) index--;
  }
</script>

<svelte:window onresize={messen} onkeydown={taste} />

<div class="tour" role="dialog" aria-modal="true" aria-labelledby="tour-titel">
  {#if rechteck}
    <div
      class="spot"
      style:left="{rechteck.left - 4}px"
      style:top="{rechteck.top - 4}px"
      style:width="{rechteck.width + 8}px"
      style:height="{rechteck.height + 8}px"
    ></div>
  {:else}
    <div class="abdunkeln"></div>
  {/if}
  <div class="karte" bind:this={karteEl} style:left="{kartePos.links}px" style:top="{kartePos.oben}px" style:width="{KARTE_BREITE_PX}px">
    <div class="schritt muted">Schritt {index + 1} von {TOUR_SCHRITTE.length}</div>
    <h3 id="tour-titel">{schritt.titel}</h3>
    <p>{schritt.text}</p>
    {#if ersterStart}
      <label class="check"><input type="checkbox" bind:checked={nichtMehrZeigen} /> Beim Start nicht mehr anzeigen</label>
    {/if}
    <div class="knoepfe">
      <button class="ghost" onclick={beenden}>{letzter ? "Schließen" : "Tour beenden"}</button>
      <span class="spacer"></span>
      <button onclick={() => index--} disabled={index === 0}>Zurück</button>
      {#if letzter}
        <button class="primary" onclick={beenden}>Fertig</button>
      {:else}
        <!-- svelte-ignore a11y_autofocus -->
        <button class="primary" onclick={() => index++} autofocus>Weiter</button>
      {/if}
    </div>
  </div>
</div>

<style>
  .tour {
    position: fixed;
    inset: 0;
    z-index: 40;
  }
  .abdunkeln {
    position: absolute;
    inset: 0;
    background: rgba(10, 16, 24, 0.55);
  }
  /* Hervorhebung: alles ausser dem Ziel wird abgedunkelt */
  .spot {
    position: absolute;
    border-radius: 8px;
    box-shadow:
      0 0 0 3px var(--accent),
      0 0 0 9999px rgba(10, 16, 24, 0.55);
    transition: all 0.25s ease;
    pointer-events: none;
  }
  .karte {
    position: absolute;
    background: var(--panel);
    border-radius: 10px;
    box-shadow: var(--shadow);
    padding: 14px 16px 12px;
    transition: left 0.25s ease, top 0.25s ease;
  }
  @media (prefers-reduced-motion: reduce) {
    .spot,
    .karte {
      transition: none;
    }
  }
  .schritt {
    font-size: 11px;
  }
  h3 {
    margin: 2px 0 6px;
    font-size: 16px;
  }
  p {
    margin: 0 0 10px;
    line-height: 1.45;
    font-size: 13px;
  }
  .check {
    display: flex;
    gap: 6px;
    align-items: center;
    font-size: 12px;
    margin-bottom: 8px;
  }
  .knoepfe {
    display: flex;
    gap: 6px;
    align-items: center;
  }
</style>
