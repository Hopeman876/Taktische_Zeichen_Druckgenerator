<script lang="ts">
  // Startbildschirm: Logo, Name, Version und aktueller Ladeschritt.
  import logo from "../../src-tauri/icons/Logo.png";
  import { store } from "../lib/store.svelte";
</script>

<div class="splash" role="status" aria-live="polite">
  <div class="karte">
    <img src={logo} alt="" />
    <h1>{store.info?.programm ?? "Taktische Zeichen Druckgenerator"}</h1>
    <p class="version">{store.info ? `Version ${store.info.version}` : " "}</p>
    <div class="balken"><div class="lauf"></div></div>
    <p class="status">{store.ladeStatus}</p>
  </div>
</div>

<style>
  .splash {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: grid;
    place-items: center;
    background: var(--bg);
  }
  .karte {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 32px 48px;
    border-radius: 14px;
    background: var(--panel);
    box-shadow: var(--shadow);
    min-width: 360px;
  }
  img {
    width: 120px;
    height: auto;
    margin-bottom: 8px;
  }
  h1 {
    font-size: 20px;
    margin: 0;
  }
  .version {
    margin: 0;
    color: var(--muted);
    font-size: 13px;
  }
  .balken {
    width: 220px;
    height: 4px;
    border-radius: 2px;
    background: var(--panel-2);
    overflow: hidden;
    margin-top: 14px;
  }
  .lauf {
    width: 40%;
    height: 100%;
    background: var(--accent);
    border-radius: 2px;
    animation: lauf 1.2s ease-in-out infinite;
  }
  @keyframes lauf {
    from {
      transform: translateX(-100%);
    }
    to {
      transform: translateX(250%);
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .lauf {
      animation: none;
      width: 100%;
    }
  }
  .status {
    margin: 6px 0 0;
    font-size: 12px;
    color: var(--muted);
  }
</style>
