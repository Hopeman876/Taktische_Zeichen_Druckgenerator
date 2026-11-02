<script lang="ts">
  // Ziehbarer Trennbalken zwischen zwei Bereichen. Doppelklick setzt zurueck.
  let {
    richtung,
    ziehen,
    ende,
    zuruecksetzen,
  }: {
    /** "spalte" = senkrechter Balken (zieht nach links/rechts), "zeile" = waagerecht. */
    richtung: "spalte" | "zeile";
    ziehen: (delta: number) => void;
    ende: () => void;
    zuruecksetzen: () => void;
  } = $props();

  const TASTATUR_SCHRITT_PX = 16;
  let start: number | null = null;

  function runter(e: PointerEvent): void {
    start = richtung === "spalte" ? e.clientX : e.clientY;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    e.preventDefault();
  }

  function bewegen(e: PointerEvent): void {
    if (start === null) return;
    const pos = richtung === "spalte" ? e.clientX : e.clientY;
    ziehen(pos - start);
    start = pos;
  }

  function hoch(e: PointerEvent): void {
    if (start === null) return;
    start = null;
    (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
    ende();
  }

  function taste(e: KeyboardEvent): void {
    const zurueck = richtung === "spalte" ? "ArrowLeft" : "ArrowUp";
    const vor = richtung === "spalte" ? "ArrowRight" : "ArrowDown";
    if (e.key === zurueck || e.key === vor) {
      e.preventDefault();
      ziehen(e.key === vor ? TASTATUR_SCHRITT_PX : -TASTATUR_SCHRITT_PX);
      ende();
    }
  }
</script>

<!-- Fokussierbarer Separator = interaktives ARIA-Muster "Window Splitter" (per Tastatur bedienbar) -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex, a11y_no_noninteractive_element_interactions -->
<div
  class="trenner {richtung}"
  role="separator"
  aria-orientation={richtung === "spalte" ? "vertical" : "horizontal"}
  tabindex="0"
  title="Ziehen zum Ändern der Größe, Doppelklick zum Zurücksetzen"
  onpointerdown={runter}
  onpointermove={bewegen}
  onpointerup={hoch}
  onpointercancel={hoch}
  ondblclick={() => (zuruecksetzen(), ende())}
  onkeydown={taste}
></div>

<style>
  .trenner {
    position: relative;
    touch-action: none;
  }
  .trenner::after {
    content: "";
    position: absolute;
    border-radius: 2px;
    background: transparent;
    transition: background 0.15s;
  }
  .trenner:hover::after,
  .trenner:focus-visible::after {
    background: var(--accent);
  }
  .spalte {
    cursor: col-resize;
  }
  .spalte::after {
    top: 0;
    bottom: 0;
    left: 2px;
    width: 3px;
  }
  .zeile {
    cursor: row-resize;
  }
  .zeile::after {
    left: 0;
    right: 0;
    top: 2px;
    height: 3px;
  }
  .trenner:focus-visible {
    outline: none;
  }
</style>
