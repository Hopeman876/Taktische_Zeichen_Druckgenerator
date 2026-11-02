// Schritte der Einfuehrungstour. `ziel` = Wert des Attributs data-tour im Layout.

export interface TourSchritt {
  ziel: string | null;
  titel: string;
  text: string;
}

export const TOUR_SCHRITTE: TourSchritt[] = [
  {
    ziel: null,
    titel: "Willkommen!",
    text:
      "Diese kurze Tour zeigt dir in einer Minute, wie du taktische Zeichen für den Druck vorbereitest. " +
      "Du kannst sie jederzeit über das ?-Menü erneut starten.",
  },
  {
    ziel: "kategorien",
    titel: "1. Kategorien",
    text:
      "Hier siehst du die Ordner deines Vorlagenordners. Jeder Ordner ist eine Kategorie. " +
      "Ganz unten findest du die Blanko-Zeichen ohne Grafik.",
  },
  {
    ziel: "vorlagen",
    titel: "2. Vorlagen",
    text:
      "Die Zeichen der gewählten Kategorie. Ein Klick zeigt eine Vorlage groß in der Vorschau – sie landet " +
      "dabei noch nicht im Auftrag. Mit dem Regler (oder Strg + Mausrad) änderst du die Größe der Bilder.",
  },
  {
    ziel: "vorschau",
    titel: "3. Vorschau und Parameter",
    text:
      "So sieht das fertige Zeichen aus. Stelle Modus, Text und Anzahl ein und klicke auf „Hinzufügen“. " +
      "Dieselbe Vorlage kannst du mehrfach mit anderem Text hinzufügen.",
  },
  {
    ziel: "auftrag",
    titel: "4. Auftrag",
    text:
      "Alle Zeichen, die exportiert werden – nach Kategorien gruppiert. Mit den Checkboxen wählst du mehrere " +
      "Zeichen aus und bearbeitest sie gemeinsam in der Vorschau. Rot markierte Zeilen haben ein Problem " +
      "(Tooltip zeigt Details). Änderungen übernimmst du mit „Änderung speichern“.",
  },
  {
    ziel: "layout",
    titel: "5. Schild-Typ und Standard-Modus",
    text:
      "S2 = Einzelschild, S1 = Doppelschild mit Schreiblinien. Der Standard-Modus wird für neu angeklickte " +
      "Vorlagen verwendet.",
  },
  {
    ziel: "einstellungen",
    titel: "6. Einstellungen",
    text:
      "Zeichengröße, Ränder, Schrift, Aufteilung des Doppelschilds und die maximale Grafikgröße – mit " +
      "Live-Vorschau.",
  },
  {
    ziel: "export",
    titel: "7. Exportieren",
    text:
      "Erzeugt PDF-Einzelzeichen (für Druckereien), einen PDF-Schnittbogen auf A4 oder PNG-Dateien. " +
      "Hinweise zum Export werden zusätzlich in „Hinweise.txt“ im Ausgabeordner gespeichert.",
  },
  {
    ziel: "hilfe",
    titel: "Fertig!",
    text: "Über das ?-Menü erreichst du diese Tour und die Programminformationen jederzeit wieder. Viel Erfolg!",
  },
];
