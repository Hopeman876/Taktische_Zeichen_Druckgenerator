<script lang="ts">
  import logo from "../../src-tauri/icons/Logo.png";
  import { api } from "../lib/api";
  import { store } from "../lib/store.svelte";

  let { schliessen }: { schliessen: () => void } = $props();
  const info = $derived(store.info);
</script>

<svelte:window onkeydown={(e) => e.key === "Escape" && schliessen()} />

<div class="overlay" role="presentation" onclick={(e) => e.target === e.currentTarget && schliessen()}>
  <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="ueber-titel">
    <img src={logo} alt="" />
    <h3 id="ueber-titel">{info?.programm}</h3>
    <p class="version">Version {info?.version}</p>
    <p>Bereitet taktische Zeichen (SVG/PNG-Vorlagen) mit Beschriftung als Vektor-PDF, Schnittbogen oder PNG für den Druck auf.</p>
    <dl>
      <dt>Autor</dt>
      <dd>{info?.autoren}</dd>
      <dt>Lizenz</dt>
      <dd>{info?.lizenz} – freie Software (GNU General Public License)</dd>
      <dt>Technik</dt>
      <dd>Rust (resvg, svg2pdf), Tauri, Svelte – Lizenztexte aller Komponenten in LIZENZEN-DRITTANBIETER.txt neben dem Programm</dd>
      <dt>Daten &amp; Logs</dt>
      <dd>
        <button class="link" onclick={() => api.pfadOeffnen(info?.daten_ordner ?? "")}>{info?.daten_ordner}</button>
      </dd>
    </dl>
    <div class="knoepfe"><button class="primary" onclick={schliessen}>Schließen</button></div>
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(10, 16, 24, 0.45);
    display: grid;
    place-items: center;
    z-index: 20;
  }
  .dialog {
    background: var(--panel);
    border-radius: 10px;
    box-shadow: var(--shadow);
    width: min(520px, calc(100vw - 32px));
    padding: 20px 24px 16px;
    text-align: center;
  }
  img {
    width: 84px;
  }
  h3 {
    margin: 8px 0 0;
    font-size: 18px;
  }
  .version {
    margin: 2px 0 10px;
    color: var(--muted);
  }
  dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 4px 12px;
    text-align: left;
    font-size: 13px;
  }
  dt {
    color: var(--muted);
  }
  dd {
    margin: 0;
    overflow-wrap: anywhere;
  }
  .link {
    border: none;
    background: none;
    padding: 0;
    color: var(--accent);
    text-decoration: underline;
    text-align: left;
  }
  .knoepfe {
    display: flex;
    justify-content: flex-end;
    margin-top: 12px;
  }
</style>
