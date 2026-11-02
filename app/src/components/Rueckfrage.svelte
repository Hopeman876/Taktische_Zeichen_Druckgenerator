<script lang="ts">
  import { store } from "../lib/store.svelte";

  const r = $derived(store.rueckfrage);

  /** Escape = erster (vorsichtigster) Knopf. */
  function taste(e: KeyboardEvent): void {
    if (r && e.key === "Escape") {
      e.preventDefault();
      r.antwort(r.knoepfe[0].id);
    }
  }
</script>

<svelte:window onkeydown={taste} />

{#if r}
  <div class="overlay" role="presentation">
    <div class="dialog" role="alertdialog" aria-modal="true" aria-labelledby="rf-titel" aria-describedby="rf-text">
      <h3 id="rf-titel">{r.titel}</h3>
      <p id="rf-text">{r.text}</p>
      <div class="knoepfe">
        {#each r.knoepfe as k (k.id)}
          <!-- svelte-ignore a11y_autofocus -->
          <button class:primary={k.primaer} autofocus={k.primaer} onclick={() => r.antwort(k.id)}>{k.label}</button>
        {/each}
      </div>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(10, 16, 24, 0.45);
    display: grid;
    place-items: center;
    z-index: 30;
  }
  .dialog {
    background: var(--panel);
    border-radius: 10px;
    box-shadow: var(--shadow);
    width: min(440px, calc(100vw - 32px));
    padding: 16px 18px 14px;
  }
  h3 {
    margin: 0 0 8px;
    font-size: 16px;
  }
  p {
    margin: 0 0 16px;
    line-height: 1.45;
  }
  .knoepfe {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
</style>
