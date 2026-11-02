<script lang="ts">
  // ?-Menue: Benutzerhandbuch (folgt), Einfuehrungstour, Ueber.
  let { tourStarten, ueberZeigen }: { tourStarten: () => void; ueberZeigen: () => void } = $props();

  let offen = $state(false);
  let wurzel: HTMLElement | undefined = $state();

  function waehle(aktion: () => void): void {
    offen = false;
    aktion();
  }

  function aussen(e: MouseEvent): void {
    if (offen && wurzel && !wurzel.contains(e.target as Node)) offen = false;
  }
</script>

<svelte:window onclick={aussen} onkeydown={(e) => e.key === "Escape" && (offen = false)} />

<div class="hilfe" bind:this={wurzel} data-tour="hilfe">
  <button class="frage" onclick={() => (offen = !offen)} aria-haspopup="menu" aria-expanded={offen} title="Hilfe">?</button>
  {#if offen}
    <div class="menue" role="menu">
      <button role="menuitem" disabled title="Das Benutzerhandbuch folgt in einer späteren Version">
        Benutzerhandbuch <span class="muted">(folgt)</span>
      </button>
      <button role="menuitem" onclick={() => waehle(tourStarten)}>Einführungstour</button>
      <div class="trenn"></div>
      <button role="menuitem" onclick={() => waehle(ueberZeigen)}>Über …</button>
    </div>
  {/if}
</div>

<style>
  .hilfe {
    position: relative;
  }
  .frage {
    font-weight: 700;
    width: 32px;
    padding: 5px 0;
  }
  .menue {
    position: absolute;
    right: 0;
    top: calc(100% + 4px);
    z-index: 15;
    min-width: 220px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: 4px;
    display: flex;
    flex-direction: column;
  }
  .menue button {
    border: none;
    text-align: left;
    padding: 7px 10px;
    background: transparent;
  }
  .menue button:hover:not(:disabled) {
    background: var(--accent-soft);
  }
  .trenn {
    border-top: 1px solid var(--border);
    margin: 4px 0;
  }
</style>
