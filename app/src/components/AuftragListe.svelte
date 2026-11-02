<script lang="ts">
  import { gruppenIds, gruppiere, store } from "../lib/store.svelte";
  import AuftragGruppe from "./AuftragGruppe.svelte";

  let suche = $state("");

  /** Treffer in Name, Text, Kategorie oder Modus (Gross-/Kleinschreibung egal). */
  const gefiltert = $derived.by(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return store.posten;
    return store.posten.filter((p) =>
      [p.name, p.text ?? "", p.kategorie, store.modusLabel(p.modus)].some((t) => t.toLowerCase().includes(s)),
    );
  });
  const gruppen = $derived(gruppiere(gefiltert, "Hauptordner"));
  const sichtbar = $derived(gruppenIds(gruppen));
  const nummern = $derived(new Map(store.postenSortiert.map((p, i) => [p.id, i + 1])));
  const anzahlMarkiert = $derived(store.markiert.length);
  const anzahlRot = $derived(store.posten.filter((p) => store.istRot(p.id)).length);
  // "Alle" bezieht sich auf die sichtbaren (gefilterten) Zeichen
  const alle = $derived(sichtbar.length > 0 && sichtbar.every((id) => store.markiert.includes(id)));
  const teilweise = $derived(!alle && sichtbar.some((id) => store.markiert.includes(id)));

  async function alleUmschalten(e: Event): Promise<void> {
    const el = e.currentTarget as HTMLInputElement;
    await store.umschalten(sichtbar, !alle);
    el.checked = alle;
    el.indeterminate = teilweise;
  }
</script>

<section class="panel">
  <div class="panel-head">
    <h2>Auftrag</h2>
    <span class="muted">{store.posten.length} Positionen · {store.anzahlZeichen} Zeichen</span>
    {#if anzahlMarkiert > 0}<span class="markiert">{anzahlMarkiert} ausgewählt</span>{/if}
    {#if anzahlRot > 0}
      <span class="rot" title="Rot markierte Zeichen: Vorlage nicht lesbar oder Text passt nicht">{anzahlRot} mit Problemen</span>
    {/if}
    <span class="spacer"></span>
    <input type="text" class="suche" placeholder="Auftrag durchsuchen…" bind:value={suche} aria-label="Auftrag durchsuchen" />
    <button onclick={() => store.leeren()} disabled={store.posten.length === 0}>Leeren</button>
  </div>
  <div class="panel-body">
    {#if store.posten.length === 0}
      <p class="muted leer">
        Noch keine Zeichen im Auftrag. Vorlage oben anklicken, in der Vorschau einstellen und „Zum Auftrag
        hinzufügen“.
      </p>
    {:else}
      <div class="tabelle">
        <div class="zeile titel">
          <span class="zelle check">
            <input
              type="checkbox"
              {@attach (el) => {
                el.checked = alle;
                el.indeterminate = teilweise;
              }}
              onchange={alleUmschalten}
              aria-label="Alle Zeichen auswählen"
              title="Alle an-/abwählen"
            />
          </span>
          <span class="zelle nr">#</span>
          <span class="zelle">Vorlage</span>
          <span class="zelle">Modus</span>
          <span class="zelle">Text</span>
          <span class="zelle anz">Anz.</span>
        </div>
        {#if sichtbar.length === 0}
          <p class="muted leer">Keine Treffer für „{suche}“.</p>
        {/if}
        {#if gruppen.posten.length > 0}
          <AuftragGruppe gruppe={{ ...gruppen, untergruppen: [] }} nummer={(id) => nummern.get(id) ?? 0} />
        {/if}
        {#each gruppen.untergruppen as g (g.pfad)}
          <AuftragGruppe gruppe={g} nummer={(id) => nummern.get(id) ?? 0} />
        {/each}
      </div>
    {/if}
  </div>
</section>

<style>
  section {
    height: 100%;
  }
  .leer {
    padding: 16px;
  }
  .tabelle {
    --auftrag-spalten: 32px 36px minmax(120px, 1.2fr) minmax(110px, 0.9fr) minmax(100px, 1.2fr) 64px;
  }
  .zeile {
    display: grid;
    grid-template-columns: var(--auftrag-spalten);
    align-items: center;
    border-bottom: 1px solid var(--border);
    min-height: 32px;
  }
  .titel {
    position: sticky;
    top: 0;
    z-index: 1;
    background: var(--panel);
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
  }
  .zelle {
    padding: 0 6px;
  }
  .check {
    display: grid;
    place-items: center;
  }
  .nr,
  .anz {
    text-align: right;
  }
  /* Abstand zum (ggf. ueberlagernden) Scrollbalken */
  .anz {
    padding-right: 14px;
  }
  .suche {
    width: 180px;
  }
  .rot {
    font-size: 12px;
    background: var(--danger);
    color: #fff;
    border-radius: 10px;
    padding: 1px 8px;
  }
  .markiert {
    font-size: 12px;
    background: var(--accent);
    color: var(--accent-text);
    border-radius: 10px;
    padding: 1px 8px;
  }
</style>
