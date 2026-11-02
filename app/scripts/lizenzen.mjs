// Erzeugt app/src-tauri/LIZENZEN-DRITTANBIETER.txt mit den Lizenztexten aller Komponenten,
// die in der Windows-Anwendung enthalten sind (Rust-Abhaengigkeiten der App + Laufzeit-Pakete
// der Oberflaeche). MIT/Apache/BSD verlangen, dass diese Texte mitgeliefert werden.
//
// Aufruf: node scripts/lizenzen.mjs   (laeuft automatisch vor jedem `tauri build`)

import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const APP = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const ZIEL = join(APP, "src-tauri", "LIZENZEN-DRITTANBIETER.txt");
const ZIEL_PLATTFORM = "x86_64-pc-windows-msvc";
const APP_PAKET = "tz-app";
const EIGENE_PAKETE = new Set(["tz-app", "tz-core", "tz-cli"]);
const LIZENZ_DATEI = /^(licen[cs]e|copying|notice)/i;
const TRENNER = "=".repeat(78);

/** Lizenzdateien eines Paketordners (LICENSE, LICENSE-MIT, COPYING, NOTICE ...). */
function lizenzDateien(ordner) {
  if (!existsSync(ordner)) return [];
  return readdirSync(ordner)
    .filter((f) => LIZENZ_DATEI.test(f))
    .sort()
    .map((f) => ({ name: f, text: readFileSync(join(ordner, f), "utf8").trim() }));
}

function abschnitt(titel, lizenz, quelle, dateien) {
  const kopf = [TRENNER, titel, `Lizenz: ${lizenz || "siehe unten"}`];
  if (quelle) kopf.push(`Quelle: ${quelle}`);
  kopf.push(TRENNER);
  const texte = dateien.length
    ? dateien.map((d) => `--- ${d.name} ---\n${d.text}`).join("\n\n")
    : `(Das Paket enthaelt keine eigene Lizenzdatei; es gilt die SPDX-Lizenz "${lizenz}", ` +
      `Volltext: https://spdx.org/licenses/)`;
  return `${kopf.join("\n")}\n\n${texte}\n`;
}

// --- Rust: alle normalen (nicht Build-/Test-)Abhaengigkeiten der App fuer Windows ----------
const meta = JSON.parse(
  execFileSync("cargo", ["metadata", "--format-version", "1", "--filter-platform", ZIEL_PLATTFORM], {
    cwd: APP,
    maxBuffer: 256 * 1024 * 1024,
  }).toString(),
);
const pakete = new Map(meta.packages.map((p) => [p.id, p]));
const knoten = new Map(meta.resolve.nodes.map((n) => [n.id, n]));
const start = meta.packages.find((p) => p.name === APP_PAKET);
const besucht = new Set();
const stapel = [start.id];
while (stapel.length) {
  const id = stapel.pop();
  if (besucht.has(id)) continue;
  besucht.add(id);
  for (const dep of knoten.get(id)?.deps ?? []) {
    if (dep.dep_kinds.some((k) => k.kind === null)) stapel.push(dep.pkg);
  }
}
const rust = [...besucht]
  .map((id) => pakete.get(id))
  .filter((p) => !EIGENE_PAKETE.has(p.name))
  .sort((a, b) => a.name.localeCompare(b.name) || a.version.localeCompare(b.version));

// --- Oberflaeche: Laufzeit-Pakete (inkl. Svelte, das in das Bundle kompiliert wird) --------
const pkg = JSON.parse(readFileSync(join(APP, "package.json"), "utf8"));
const npmNamen = new Set([...Object.keys(pkg.dependencies ?? {}), "svelte"]);
const npm = [];
const offen = [...npmNamen];
while (offen.length) {
  const name = offen.pop();
  const ordner = join(APP, "node_modules", name);
  if (!existsSync(join(ordner, "package.json"))) continue;
  const p = JSON.parse(readFileSync(join(ordner, "package.json"), "utf8"));
  npm.push({ name, version: p.version, lizenz: p.license, quelle: p.repository?.url ?? p.homepage, ordner });
  // Svelte-Laufzeit bindet eigene Abhaengigkeiten ein -> mit aufnehmen
  if (name === "svelte") {
    for (const d of Object.keys(p.dependencies ?? {})) if (!npmNamen.has(d)) (npmNamen.add(d), offen.push(d));
  }
}
npm.sort((a, b) => a.name.localeCompare(b.name));

// --- Ausgabe --------------------------------------------------------------------------------
const teile = [
  "Taktische Zeichen Druckgenerator - Lizenzen der verwendeten Komponenten",
  "",
  "Das Programm selbst steht unter der GNU General Public License v3.0 (oder spaeter), siehe LICENSE.",
  "Im Folgenden die Lizenztexte aller enthaltenen Fremdkomponenten.",
  `Rust-Komponenten: ${rust.length}, Oberflaechen-Komponenten: ${npm.length}`,
  "",
];
for (const p of rust) {
  teile.push(abschnitt(`${p.name} ${p.version} (Rust)`, p.license, p.repository, lizenzDateien(dirname(p.manifest_path))));
}
for (const p of npm) {
  teile.push(abschnitt(`${p.name} ${p.version} (JavaScript)`, p.lizenz, p.quelle, lizenzDateien(p.ordner)));
}
writeFileSync(ZIEL, teile.join("\n"));
const ohneText = [...rust.filter((p) => !lizenzDateien(dirname(p.manifest_path)).length).map((p) => p.name)];
console.log(`${ZIEL}: ${rust.length} Rust- und ${npm.length} JS-Komponenten`);
if (ohneText.length) console.log(`Ohne eigene Lizenzdatei (SPDX-Verweis): ${ohneText.join(", ")}`);
