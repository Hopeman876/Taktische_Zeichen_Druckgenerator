<script lang="ts">
  import type { Kategorie } from "../lib/types";
  import KategorieBaum from "./KategorieBaum.svelte";

  let {
    kategorie,
    gewaehlt,
    waehle,
    tiefe = 0,
  }: { kategorie: Kategorie; gewaehlt: string; waehle: (pfad: string) => void; tiefe?: number } = $props();

  let offen = $state(true);
</script>

<div class="knoten">
  <div class="zeile" class:aktiv={gewaehlt === kategorie.pfad} style="padding-left: {6 + tiefe * 14}px">
    {#if kategorie.unterkategorien.length > 0}
      <button class="ghost icon pfeil" onclick={() => (offen = !offen)} aria-label={offen ? "Zuklappen" : "Aufklappen"}>
        {offen ? "▾" : "▸"}
      </button>
    {:else}
      <span class="pfeil-platz"></span>
    {/if}
    <button class="ghost name" onclick={() => waehle(kategorie.pfad)} title={kategorie.pfad || kategorie.name}>
      {kategorie.name}
      <span class="anzahl">{kategorie.anzahl_gesamt}</span>
    </button>
  </div>
  {#if offen}
    {#each kategorie.unterkategorien as u (u.pfad)}
      <KategorieBaum kategorie={u} {gewaehlt} {waehle} tiefe={tiefe + 1} />
    {/each}
  {/if}
</div>

<style>
  .zeile {
    display: flex;
    align-items: center;
    border-radius: var(--radius);
  }
  .zeile.aktiv {
    background: var(--accent-soft);
  }
  .pfeil,
  .pfeil-platz {
    width: 22px;
    flex: none;
    padding: 2px 0;
  }
  .name {
    flex: 1;
    text-align: left;
    display: flex;
    gap: 6px;
    align-items: center;
    padding: 4px 6px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .anzahl {
    margin-left: auto;
    font-size: 11px;
    color: var(--muted);
  }
</style>
