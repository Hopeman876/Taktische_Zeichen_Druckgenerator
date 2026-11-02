<script lang="ts">
  import { store } from "../lib/store.svelte";
  import type { FeldName, ZeichenSpec } from "../lib/types";
  import ZeichenBild from "./ZeichenBild.svelte";

  const STANDARD_GRAFIK_MAX_MM: [number, number] = [30, 25];

  /** Aus der letzten Vorschau: Text passt nicht in 2 Zeilen, eine 3. Zeile haette Platz. */
  let dritteMoeglich = $state(false);

  const ansicht = $derived(store.ansicht);
  const posten = $derived(store.aktiverPosten);
  const mehrfach = $derived(ansicht?.art === "mehrfach" ? ansicht : null);
  const titel = $derived.by(() => {
    if (!ansicht) return "";
    if (ansicht.art === "vorlage") return ansicht.vorlage.name;
    if (ansicht.art === "posten") return posten?.name ?? "";
    return `Mehrfachauswahl: ${ansicht.ids.length} Zeichen`;
  });
  const vorlage = $derived(
    ansicht?.art === "vorlage" ? ansicht.vorlage.vorlage : ansicht?.art === "posten" ? posten?.vorlage : null,
  );
  /** Textfeld zeigen? In der Mehrfachauswahl, sobald ein beteiligter Modus Text hat. */
  const textSichtbar = $derived.by(() => {
    if (!ansicht) return false;
    if (store.modusHatText(ansicht.entwurf.modus)) return true;
    if (ansicht.art !== "mehrfach") return false;
    return store.posten.some((p) => ansicht.ids.includes(p.id) && store.modusHatText(p.modus));
  });
  const positionSichtbar = $derived(
    ansicht?.entwurf.modus === "ohne_text" ||
      (mehrfach !== null && store.posten.some((p) => mehrfach.ids.includes(p.id) && p.modus === "ohne_text")),
  );
  const platzhalter = $derived(store.info?.modi.find((m) => m.id === ansicht?.entwurf.modus)?.platzhalter ?? "");

  // Vorschaubild (nicht bei Mehrfachauswahl)
  const spec = $derived.by((): ZeichenSpec | null => {
    const a = ansicht;
    if (!a || a.art === "mehrfach" || !vorlage) return null;
    return {
      vorlage,
      modus: a.entwurf.modus,
      text: a.entwurf.text,
      grafik_position: a.entwurf.grafik_position,
      grafik_max_mm: a.entwurf.grafik_max_mm,
      drei_zeilen: a.entwurf.drei_zeilen,
    };
  });

  /** Feld ist in der Mehrfachauswahl unterschiedlich und noch nicht bearbeitet. */
  function gemischt(f: FeldName): boolean {
    return mehrfach?.gemischt[f] ?? false;
  }

  function geaendert(f: FeldName): void {
    store.feldGeaendert(f);
  }
</script>

<section class="panel">
  <div class="panel-head">
    <h2>Vorschau</h2>
    {#if ansicht}
      <span class="art" class:mehr={ansicht.art === "mehrfach"}>
        {ansicht.art === "vorlage" ? "Vorlage" : ansicht.art === "posten" ? "Auftrag" : "Mehrfachauswahl"}
      </span>
    {/if}
    <span class="spacer"></span>
    <label class="check">
      <input type="checkbox" bind:checked={store.vorschauSchnittlinien} /> Schnittlinien
    </label>
  </div>
  <div class="panel-body inhalt">
    {#if !ansicht}
      <p class="muted">Vorlage im Katalog oder Zeile im Auftrag anklicken.</p>
    {:else}
      <div class="titel" title={titel}>{titel}</div>
      {#if ansicht.art === "mehrfach"}
        <div class="mehrfach-info">
          <strong>{ansicht.ids.length} Zeichen ausgewählt</strong>
          <span class="muted">
            Grau dargestellte Felder haben unterschiedliche Werte. Ein geändertes Feld gilt nach „Änderung
            speichern“ für alle ausgewählten Zeichen.
          </span>
        </div>
      {:else}
        <ZeichenBild
          {spec}
          schnittlinien={store.vorschauSchnittlinien}
          ergebnis={(r) => (dritteMoeglich = r?.dritte_zeile_moeglich ?? false)}
        />
      {/if}

      <div class="parameter">
        <label class="feld" class:gemischt={gemischt("modus")}>
          Modus
          <select bind:value={ansicht.entwurf.modus} onchange={() => geaendert("modus")}>
            {#each store.info?.modi ?? [] as m (m.id)}
              <option value={m.id}>{m.label}</option>
            {/each}
          </select>
        </label>
        {#if textSichtbar}
          <label class="feld spalte" class:gemischt={gemischt("text")}>
            Text
            <input
              type="text"
              value={gemischt("text") ? "" : (ansicht.entwurf.text ?? "")}
              placeholder={gemischt("text") ? "(unterschiedlich)" : platzhalter}
              oninput={(e) => {
                ansicht.entwurf.text = e.currentTarget.value || null;
                geaendert("text");
              }}
            />
          </label>
        {/if}
        {#if ansicht.art !== "mehrfach" && (dritteMoeglich || ansicht.entwurf.drei_zeilen)}
          <label
            class="feld"
            title="Nur möglich, wenn der Text in zwei Zeilen nicht passt und über dem Text genug Platz ist – die Grafik wird nicht verkleinert."
          >
            <span>3. Textzeile verwenden <span class="muted klein">(Text passt nicht in 2 Zeilen)</span></span>
            <input type="checkbox" bind:checked={ansicht.entwurf.drei_zeilen} />
          </label>
        {/if}
        <label class="feld" class:gemischt={gemischt("kopien")}>
          Anzahl
          <input
            type="number"
            min="1"
            max="999"
            bind:value={ansicht.entwurf.kopien}
            oninput={() => geaendert("kopien")}
          />
        </label>
        {#if positionSichtbar}
          <label class="feld" class:gemischt={gemischt("grafik_position")}>
            Grafik-Position (Nur Grafik)
            <select bind:value={ansicht.entwurf.grafik_position} onchange={() => geaendert("grafik_position")}>
              <option value="oben">oben</option>
              <option value="mittig">mittig</option>
              <option value="unten">unten</option>
            </select>
          </label>
        {/if}
        {#if ansicht.art !== "mehrfach"}
          <label
            class="feld"
            title="Weicht für dieses Zeichen von der max. Grafikgröße in den Einstellungen ab"
          >
            <span>
              Max. Grafikgröße abweichend
              {#if store.config.grafik_max_mm && !ansicht.entwurf.grafik_max_mm}
                <span class="muted klein">(Standard: {store.config.grafik_max_mm[0]} × {store.config.grafik_max_mm[1]} mm)</span>
              {/if}
            </span>
            <input
              type="checkbox"
              checked={ansicht.entwurf.grafik_max_mm !== null}
              onchange={(e) =>
                (ansicht.entwurf.grafik_max_mm = e.currentTarget.checked
                  ? (store.config.grafik_max_mm ? [...store.config.grafik_max_mm] : [...STANDARD_GRAFIK_MAX_MM])
                  : null)}
            />
          </label>
          {#if ansicht.entwurf.grafik_max_mm}
            <label class="feld">
              Max. Breite (mm)<input type="number" min="1" step="0.5" bind:value={ansicht.entwurf.grafik_max_mm[0]} />
            </label>
            <label class="feld">
              Max. Höhe (mm)<input type="number" min="1" step="0.5" bind:value={ansicht.entwurf.grafik_max_mm[1]} />
            </label>
          {/if}
        {/if}
      </div>
    {/if}
  </div>
  {#if ansicht}
    <div class="leiste">
      <button
        onclick={() => store.hinzufuegen()}
        disabled={ansicht.art === "mehrfach"}
        class:primary={ansicht.art === "vorlage"}
        title={ansicht.art === "posten"
          ? "Als zusätzlichen Eintrag mit diesen Parametern zum Auftrag hinzufügen"
          : "Mit diesen Parametern zum Auftrag hinzufügen"}
      >
        {ansicht.art === "posten" ? "Als neu hinzufügen" : "Hinzufügen"}
      </button>
      <button onclick={() => store.entfernen()} disabled={ansicht.art === "vorlage"}>
        Entfernen{ansicht.art === "mehrfach" ? ` (${ansicht.ids.length})` : ""}
      </button>
      <span class="spacer"></span>
      {#if store.ungespeichert}
        <button class="ghost" onclick={() => store.aenderungVerwerfen()}>Verwerfen</button>
      {/if}
      <button
        class:primary={store.ungespeichert}
        onclick={() => store.aenderungSpeichern()}
        disabled={!store.ungespeichert}
      >
        Änderung speichern
      </button>
    </div>
  {/if}
</section>

<style>
  section {
    height: 100%;
  }
  .inhalt {
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .art {
    font-size: 11px;
    border-radius: 10px;
    padding: 1px 8px;
    background: var(--accent-soft);
  }
  .art.mehr {
    background: var(--accent);
    color: var(--accent-text);
  }
  .check {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
  }
  .titel {
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .mehrfach-info {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 18px 14px;
    border: 1px dashed var(--border);
    border-radius: var(--radius);
    background: var(--panel-2);
    text-align: center;
    font-size: 13px;
  }
  .klein {
    font-size: 11px;
  }
  .parameter {
    border-top: 1px solid var(--border);
    padding-top: 8px;
  }
  .spalte {
    grid-template-columns: auto 1fr;
  }
  /* Unterschiedliche Werte in der Mehrfachauswahl: ausgegraut, bis bearbeitet */
  .gemischt {
    color: var(--muted);
  }
  .gemischt select,
  .gemischt input {
    background: var(--panel-2);
    color: var(--muted);
    border-style: dashed;
  }
  .leiste {
    display: flex;
    gap: 6px;
    align-items: center;
    padding: 8px 10px;
    border-top: 1px solid var(--border);
    flex-wrap: wrap;
  }
</style>
