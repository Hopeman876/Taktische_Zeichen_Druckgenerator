<script lang="ts">
  import { gruppenIds, store, type Gruppe } from "../lib/store.svelte";
  import AuftragGruppe from "./AuftragGruppe.svelte";

  let {
    gruppe,
    tiefe = 0,
    nummer,
    kopfZeigen = true,
  }: { gruppe: Gruppe; tiefe?: number; nummer: (id: number) => number; kopfZeigen?: boolean } = $props();

  let offen = $state(true);

  const ids = $derived(gruppenIds(gruppe));
  const anzahlMarkiert = $derived(ids.filter((id) => store.markiert.includes(id)).length);
  const alle = $derived(ids.length > 0 && anzahlMarkiert === ids.length);
  const teilweise = $derived(anzahlMarkiert > 0 && !alle);
  const aktivId = $derived(store.ansicht?.art === "posten" ? store.ansicht.id : null);
  const einrueckung = $derived(`padding-left: ${8 + tiefe * 16}px`);

  // Der Browser hakt sofort an; nach der (evtl. abgelehnten) Rueckfrage wird der
  // sichtbare Zustand explizit an den tatsaechlichen Zustand angeglichen.
  async function gruppeUmschalten(e: Event): Promise<void> {
    const el = e.currentTarget as HTMLInputElement;
    await store.umschalten(ids, !alle);
    el.checked = alle;
    el.indeterminate = teilweise;
  }

  async function zeileUmschalten(e: Event, id: number): Promise<void> {
    const el = e.currentTarget as HTMLInputElement;
    await store.umschalten([id], !store.markiert.includes(id));
    el.checked = store.markiert.includes(id);
  }

  /** Tooltip mit Fehler und Hinweisen des Zeichens. */
  function problemText(id: number): string {
    const r = store.pruefung[id];
    if (!r) return "";
    return [r.fehler, ...r.hinweise.map((h) => h.text)].filter(Boolean).join("\n");
  }

  function textAnzeige(text: string | null, modus: string): string {
    if (modus === "ohne_text" || modus === "schreiblinie_staerke") return "–";
    return text ?? "";
  }
</script>

{#if kopfZeigen}
  <div class="zeile kopf">
    <span class="zelle check">
      <input
        type="checkbox"
        {@attach (el) => {
          el.checked = alle;
          el.indeterminate = teilweise;
        }}
        onchange={gruppeUmschalten}
        aria-label="Alle Zeichen in {gruppe.name} auswählen"
      />
    </span>
    <button class="ghost gruppe" style={einrueckung} onclick={() => (offen = !offen)} aria-expanded={offen}>
      <span class="pfeil">{offen ? "▾" : "▸"}</span>
      {gruppe.name}
      <span class="muted anzahl">{ids.length}</span>
    </button>
  </div>
{/if}

{#if offen || !kopfZeigen}
  {#each gruppe.posten as p (p.id)}
    <div
      class="zeile posten"
      class:aktiv={aktivId === p.id}
      class:markiert={store.markiert.includes(p.id)}
      class:rot={store.istRot(p.id)}
      title={problemText(p.id)}
      role="button"
      tabindex="0"
      onclick={() => store.postenAnsehen(p.id)}
      onkeydown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), store.postenAnsehen(p.id))}
    >
      <span class="zelle check">
        <input
          type="checkbox"
          {@attach (el) => {
            el.checked = store.markiert.includes(p.id);
          }}
          onclick={(e) => e.stopPropagation()}
          onchange={(e) => zeileUmschalten(e, p.id)}
          aria-label="{p.name} auswählen"
        />
      </span>
      <span class="zelle nr muted">{nummer(p.id)}</span>
      <span class="zelle name" style="padding-left: {tiefe * 16 + (kopfZeigen ? 16 : 0)}px" title={p.vorlage.art === "datei" ? p.vorlage.pfad : p.name}>{p.name}</span>
      <span class="zelle modus">{store.modusLabel(p.modus)}</span>
      <span class="zelle text" title={p.text ?? ""}>{textAnzeige(p.text, p.modus)}</span>
      <span class="zelle anz">
        {#if store.istRot(p.id)}<span class="symbol fehler" aria-label="Problem">✖</span>
        {:else if problemText(p.id)}<span class="symbol warn" aria-label="Hinweis">⚠</span>{/if}
        {p.kopien}
      </span>
    </div>
  {/each}
  {#each gruppe.untergruppen as u (u.pfad)}
    <AuftragGruppe gruppe={u} tiefe={tiefe + 1} {nummer} />
  {/each}
{/if}

<style>
  .zeile {
    display: grid;
    grid-template-columns: var(--auftrag-spalten);
    align-items: center;
    border-bottom: 1px solid var(--border);
    min-height: 32px;
  }
  .zelle {
    padding: 0 6px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .check {
    display: grid;
    place-items: center;
  }
  .kopf {
    background: var(--panel-2);
    grid-template-columns: 32px 1fr;
  }
  .gruppe {
    text-align: left;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
    border-radius: 0;
    padding-top: 6px;
    padding-bottom: 6px;
  }
  .pfeil {
    width: 12px;
    display: inline-block;
  }
  .anzahl {
    font-weight: 400;
    font-size: 12px;
  }
  .posten {
    cursor: pointer;
  }
  .posten:hover {
    background: var(--panel-2);
  }
  .posten.markiert {
    background: var(--accent-soft);
  }
  .posten.aktiv {
    box-shadow: inset 3px 0 0 var(--accent);
    background: var(--accent-soft);
  }
  /* Problemzeilen: Vorlage nicht lesbar oder Text passt nicht */
  .posten.rot {
    background: var(--danger-soft);
    color: var(--danger);
    box-shadow: inset 3px 0 0 var(--danger);
  }
  .posten.rot.aktiv,
  .posten.rot.markiert {
    background: var(--danger-soft);
  }
  .symbol {
    font-size: 11px;
    margin-right: 4px;
  }
  .symbol.fehler {
    color: var(--danger);
  }
  .symbol.warn {
    color: var(--warn);
  }
  .nr {
    font-size: 12px;
    text-align: right;
  }
  .anz {
    text-align: right;
    /* Abstand zum (ggf. ueberlagernden) Scrollbalken */
    padding-right: 14px;
  }
</style>
