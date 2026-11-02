import { mount } from "svelte";
import "./app.css";
import App from "./App.svelte";

// Das Standard-Kontextmenue des WebViews (Edge: "Teilen", "Weitere Tools" ...) gehoert nicht in
// die App. In Eingabefeldern bleibt es fuer Ausschneiden/Kopieren/Einfuegen erhalten.
document.addEventListener("contextmenu", (e) => {
  const ziel = e.target as HTMLElement | null;
  const eingabe = ziel?.closest("input, textarea, [contenteditable='true']");
  if (!eingabe) e.preventDefault();
});

const app = mount(App, { target: document.getElementById("app")! });

export default app;
