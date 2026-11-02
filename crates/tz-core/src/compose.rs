//! Komposition eines Zeichens: Geometrie, Text-Layout und Overlay-SVG.
//!
//! Ergebnis ist eine [`Komposition`]: die platzierte Grafik (eigener usvg-Baum)
//! plus ein Overlay-SVG mit Text, Platzhaltern, Schreiblinien und optionalen
//! Schnittlinien. Beide Ebenen liegen im selben mm-Koordinatensystem
//! (Ursprung = linke obere Ecke der Datei inkl. Beschnitt).
//!
//! Die Layout-Regeln entsprechen der Python-Version v0.8.x:
//! - Text am unteren Rand des Inhaltsbereichs, Platz fuer IMMER 2 Zeilen
//! - Zeilen untereinander linksbuendig, als Block horizontal zentriert
//! - Grafik oben, horizontal zentriert, im verbleibenden Platz eingepasst
//! - Zu lange Texte werden ausgewogen auf zwei Zeilen umgebrochen und bei Bedarf
//!   schrittweise bis `min_schrift_pt` verkleinert

use std::sync::Arc;

use serde::{Deserialize, Serialize};

use crate::config::{DruckConfig, Layout};
use crate::error::{Error, Result};
use crate::fonts::{FontFace, Fonts};
use crate::geometry::{Rect, ZeichenGeometrie};
use crate::grafik::Grafik;
use crate::katalog::{BlankoArt, VorlageRef};
use crate::modus::{GrafikPosition, Modus};
use crate::svg::{Anker, Rgb, SvgBuilder};
use crate::units::pt_to_mm;

/// Schrittweite der automatischen Textverkleinerung in Punkt.
const VERKLEINERUNG_SCHRITT_PT: f64 = 0.5;
/// Mindest-DPI fuer Rasterbilder, darunter gibt es eine Warnung.
pub const MIN_RASTER_DPI: f64 = 300.0;
/// Schriftgroesse der Schnittlinien-Beschriftung in mm.
const SCHNITT_LABEL_MM: f64 = 1.2;

// Staerke-Anzeige im S1-Layout (geometrisch gezeichnet), Faktoren der Python-Version.
const S1_STAERKE_WINKEL_GRAD: f64 = 75.0;
const S1_STAERKE_HOEHE_FAKTOR: f64 = 0.9;
const S1_STAERKE_UNTERSTRICH_FAKTOR: f64 = 0.25;
const S1_STAERKE_RAND_LINKS_FAKTOR: f64 = 0.12;
const S1_STAERKE_LUECKE_FAKTOR: f64 = 0.01;
const S1_STAERKE_SCHRAEGSTRICHE: usize = 3;

/// Was auf ein Zeichen gedruckt werden soll.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct ZeichenSpec {
    pub vorlage: VorlageRef,
    pub modus: Modus,
    /// OV-Name / Ortsname / Rufname / Freitext / Dateiname-Ueberschreibung.
    /// `None` oder leer = Platzhalter.
    pub text: Option<String>,
    /// Position der Grafik im Modus "Nur Grafik".
    pub grafik_position: GrafikPosition,
    /// Abweichende maximale Grafikgroesse [Breite, Hoehe] in mm fuer dieses Zeichen
    /// (`None` = Einstellung `DruckConfig::grafik_max_mm` gilt).
    pub grafik_max_mm: Option<[f64; 2]>,
    /// Dritte Textzeile erlauben, falls der Text in zwei Zeilen nicht passt (nur wenn
    /// Platz ist: Grafik wird nicht verkleinert, Text beruehrt die Grafik nicht).
    pub drei_zeilen: bool,
}

impl Default for ZeichenSpec {
    fn default() -> Self {
        Self {
            vorlage: VorlageRef::Blanko { blanko: BlankoArt::Leer },
            modus: Modus::default(),
            text: None,
            grafik_position: GrafikPosition::default(),
            grafik_max_mm: None,
            drei_zeilen: false,
        }
    }
}

/// Art eines Hinweises.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum HinweisArt {
    TextVerkleinert,
    TextZuLang,
    SchriftFallback,
    GrafikKeinPlatz,
    RasterAufloesungNiedrig,
    SchriftInVorlageFehlt,
}

/// Hinweis zur Komposition (fuer Bericht und Oberflaeche).
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct Hinweis {
    pub art: HinweisArt,
    pub text: String,
}

/// Grafik und ihr Zielrechteck (mm). Die Inhaltsbox der Grafik wird exakt
/// auf `ziel` abgebildet (Seitenverhaeltnis bleibt erhalten).
#[derive(Debug, Clone)]
pub struct Platzierung {
    pub grafik: Arc<Grafik>,
    pub ziel: Rect,
}

/// Fertig komponiertes Zeichen.
#[derive(Debug, Clone)]
pub struct Komposition {
    pub geometrie: ZeichenGeometrie,
    pub grafik: Option<Platzierung>,
    /// Overlay in Dateigroesse (inkl. Beschnitt), transparenter Hintergrund.
    pub overlay_svg: String,
    pub hinweise: Vec<Hinweis>,
    /// Text passt nicht in zwei Zeilen, aber in drei, und der Platz reicht dafuer.
    pub dritte_zeile_moeglich: bool,
}

/// Optionen fuer die Komposition.
#[derive(Debug, Clone, Copy, Default)]
pub struct ComposeOptionen {
    /// Rote/blaue/gruene Schnitt- und Hilfslinien einzeichnen.
    pub schnittlinien: bool,
}

/// Komponiert ein Zeichen. `grafik` muss fuer Datei-Vorlagen geladen sein.
pub fn compose(
    spec: &ZeichenSpec,
    grafik: Option<Arc<Grafik>>,
    cfg: &DruckConfig,
    fonts: &Fonts,
    opt: ComposeOptionen,
) -> Result<Komposition> {
    let groesse = cfg.groesse();
    let geo = ZeichenGeometrie::aus(&groesse);
    let face = fonts.resolve(&cfg.text.font_family)?;
    let mut ctx = Ctx {
        cfg,
        face: &face,
        svg: SvgBuilder::new(geo.datei.w, geo.datei.h),
        hinweise: Vec::new(),
        name: spec.vorlage.name(),
        dritte_zeile_moeglich: false,
    };
    if face.ist_fallback {
        ctx.hinweis(
            HinweisArt::SchriftFallback,
            format!("Schrift '{}' nicht gefunden, verwende '{}'", cfg.text.font_family, face.family),
        );
    }

    let blanko = match &spec.vorlage {
        VorlageRef::Blanko { blanko } => Some(*blanko),
        VorlageRef::Datei { .. } => {
            if grafik.is_none() {
                return Err(Error::Config("Grafik fuer Datei-Vorlage nicht geladen".into()));
            }
            None
        }
    };

    let platzierung = match cfg.layout {
        // Leeres Blankoschild: weder Grafik noch Text noch Linien
        _ if blanko == Some(BlankoArt::Leer) => None,
        Layout::S2 => ctx.text_und_grafik(geo.inhalt, spec, grafik),
        Layout::S1 => ctx.s1(geo.inhalt, spec, grafik, blanko),
    };

    if let Some(p) = &platzierung {
        if !p.grafik.fehlende_schriften.is_empty() {
            ctx.hinweis(
                HinweisArt::SchriftInVorlageFehlt,
                format!(
                    "Vorlage verwendet nicht installierte Schrift(en): {} (wird ersetzt)",
                    p.grafik.fehlende_schriften.join(", ")
                ),
            );
        }
        if let Some(dpi) = p.grafik.effektive_dpi(p.ziel.w) {
            if dpi < MIN_RASTER_DPI {
                ctx.hinweis(
                    HinweisArt::RasterAufloesungNiedrig,
                    format!("Rasterbild hat nur ca. {:.0} DPI (empfohlen: mind. {:.0})", dpi, MIN_RASTER_DPI),
                );
            }
        }
    }

    if opt.schnittlinien {
        ctx.schnittlinien(&geo);
    }

    let Ctx { svg, hinweise, dritte_zeile_moeglich, .. } = ctx;
    Ok(Komposition {
        geometrie: geo,
        grafik: platzierung,
        overlay_svg: svg.finish(),
        hinweise,
        dritte_zeile_moeglich,
    })
}

// ---------------------------------------------------------------------------------------------
// Text-Zeilen
// ---------------------------------------------------------------------------------------------

/// Teilstueck einer Zeile. Breiten in mm.
#[derive(Debug, Clone)]
enum Seg {
    Text(String),
    /// Unsichtbarer Abstand (zum handschriftlichen Ausfuellen).
    Luecke(f64),
    /// Schreiblinie in Hoehe eines Unterstrichs.
    Linie(f64),
}

#[derive(Debug, Clone, Default)]
struct Zeile {
    segs: Vec<Seg>,
    /// Zeile besteht nur aus automatisch erzeugten Platzhaltern (nie verkleinern).
    nur_platzhalter: bool,
    /// Durchgehende Schreiblinie ueber die ganze Bereichsbreite.
    volle_linie: bool,
}

impl Zeile {
    fn text(t: impl Into<String>) -> Self {
        Self { segs: vec![Seg::Text(t.into())], ..Default::default() }
    }

    fn leer() -> Self {
        Self::default()
    }

    fn ist_leer(&self) -> bool {
        self.segs.is_empty() && !self.volle_linie
    }

    fn breite(&self, face: &FontFace, size: f64) -> f64 {
        self.segs
            .iter()
            .map(|s| match s {
                Seg::Text(t) => face.breite(t, size),
                Seg::Luecke(w) | Seg::Linie(w) => *w,
            })
            .sum()
    }
}

struct Ctx<'a> {
    cfg: &'a DruckConfig,
    face: &'a FontFace,
    svg: SvgBuilder,
    hinweise: Vec<Hinweis>,
    name: String,
    dritte_zeile_moeglich: bool,
}

impl Ctx<'_> {
    fn hinweis(&mut self, art: HinweisArt, text: String) {
        self.hinweise.push(Hinweis { art, text });
    }

    /// Staerke-Zeile: "     /      /      / ___" (Felder 1-3 frei, Gesamt als Linie).
    fn staerke_zeile(&self, size: f64) -> Zeile {
        let sp = self.face.breite(" ", size);
        let us = self.face.breite("_", size);
        let [a, b, c, d] = self.cfg.text.staerke_stellen.map(|v| v as f64);
        Zeile {
            segs: vec![
                Seg::Luecke(sp * (a + 1.0)),
                Seg::Text("/".into()),
                Seg::Luecke(sp * (b + 2.0)),
                Seg::Text("/".into()),
                Seg::Luecke(sp * (c + 2.0)),
                Seg::Text("/".into()),
                Seg::Luecke(sp),
                Seg::Linie(us * d),
            ],
            nur_platzhalter: true,
            volle_linie: false,
        }
    }

    /// Praefix + Name, oder Praefix + Linie bis `ziel_breite`.
    fn praefix_zeile(&self, praefix: &str, name: Option<&str>, ziel_breite: f64, size: f64) -> Zeile {
        match name {
            Some(n) => Zeile::text(format!("{praefix}{n}")),
            None => {
                let rest = (ziel_breite - self.face.breite(praefix, size)).max(0.0);
                Zeile {
                    segs: vec![Seg::Text(praefix.into()), Seg::Linie(rest)],
                    nur_platzhalter: true,
                    volle_linie: false,
                }
            }
        }
    }

    /// Bricht Text auf maximal zwei Zeilen um. Passt er in eine Zeile, steht er unten.
    fn umbruch(&self, text: &str, max_w: f64, size: f64) -> [Zeile; 2] {
        let w = |t: &str| self.face.breite(t, size);
        if w(text) <= max_w {
            return [Zeile::leer(), Zeile::text(text)];
        }
        // Trennstellen: Leerzeichen und nach Bindestrichen
        let woerter: Vec<String> =
            text.replace('-', "- ").split_whitespace().map(|s| s.to_string()).collect();
        let zusammen = |ws: &[String]| ws.join(" ").replace("- ", "-");
        if woerter.len() > 1 {
            // Ausgewogen umbrechen: Trennstelle mit der schmalsten laengeren Zeile.
            // Passt keine Variante, wird trotzdem die ausgewogenste genommen; die
            // Schriftgroesse wird dann vom Aufrufer weiter verkleinert.
            let (l1, l2) = (1..woerter.len())
                .map(|i| (zusammen(&woerter[..i]), zusammen(&woerter[i..])))
                .min_by(|a, b| {
                    let wa = w(&a.0).max(w(&a.1));
                    let wb = w(&b.0).max(w(&b.1));
                    wa.total_cmp(&wb)
                })
                .unwrap_or_default();
            return [Zeile::text(l1), Zeile::text(l2)];
        }
        // Ein einziges langes Wort: hart in der Mitte trennen
        let chars: Vec<char> = text.chars().collect();
        let mid = chars.len() / 2;
        [
            Zeile::text(chars[..mid].iter().collect::<String>()),
            Zeile::text(chars[mid..].iter().collect::<String>()),
        ]
    }

    /// Bricht Text ausgewogen auf genau drei Zeilen um (fuer die optionale 3. Zeile).
    fn umbruch3(&self, text: &str, size: f64) -> Option<[Zeile; 3]> {
        let w = |t: &str| self.face.breite(t, size);
        let woerter: Vec<String> =
            text.replace('-', "- ").split_whitespace().map(|s| s.to_string()).collect();
        if woerter.len() < 3 {
            return None;
        }
        let zusammen = |ws: &[String]| ws.join(" ").replace("- ", "-");
        let mut best: Option<(f64, [String; 3])> = None;
        for i in 1..woerter.len() - 1 {
            for j in i + 1..woerter.len() {
                let teile = [zusammen(&woerter[..i]), zusammen(&woerter[i..j]), zusammen(&woerter[j..])];
                let breite = teile.iter().map(|t| w(t)).fold(0.0, f64::max);
                if best.as_ref().is_none_or(|(b, _)| breite < *b) {
                    best = Some((breite, teile));
                }
            }
        }
        best.map(|(_, [a, b, c])| [Zeile::text(a), Zeile::text(b), Zeile::text(c)])
    }

    /// Dreizeilige Variante eines Modus (falls es eine gibt).
    fn zeilen3(&self, spec: &ZeichenSpec, size: f64) -> Option<Vec<Zeile>> {
        let text = spec.text.as_deref().map(str::trim).filter(|t| !t.is_empty());
        match spec.modus {
            Modus::Freitext => self.umbruch3(text?, size).map(Vec::from),
            Modus::Ruf => self.umbruch3(&format!("Ruf: {}", text?), size).map(Vec::from),
            Modus::Dateiname => {
                let auto = self.name.replace('_', " ");
                self.umbruch3(text.unwrap_or(&auto), size).map(Vec::from)
            }
            Modus::OvStaerke | Modus::OrtStaerke => {
                // Name auf zwei Zeilen, darunter die Staerke-Zeile
                let praefix = if spec.modus == Modus::OvStaerke { "OV: " } else { "Ort: " };
                let voll = format!("{praefix}{}", text?);
                let woerter: Vec<&str> = voll.split_whitespace().collect();
                if woerter.len() < 3 {
                    return None;
                }
                let [a, b] = self.umbruch(&voll, 0.0, size);
                if a.ist_leer() {
                    return None;
                }
                Some(vec![a, b, self.staerke_zeile(size)])
            }
            _ => None,
        }
    }

    /// Erzeugt die zwei Textzeilen eines Modus bei Schriftgroesse `size` (mm).
    fn zeilen(&self, spec: &ZeichenSpec, bereich_w: f64, size: f64) -> [Zeile; 2] {
        let text = spec.text.as_deref().map(str::trim).filter(|t| !t.is_empty());
        match spec.modus {
            Modus::OhneText => [Zeile::leer(), Zeile::leer()],
            Modus::OvStaerke | Modus::OrtStaerke => {
                let praefix = if spec.modus == Modus::OvStaerke { "OV: " } else { "Ort: " };
                let staerke = self.staerke_zeile(size);
                let sw = staerke.breite(self.face, size);
                [self.praefix_zeile(praefix, text, sw, size), staerke]
            }
            Modus::SchreiblinieStaerke => {
                let linie = Zeile { volle_linie: true, nur_platzhalter: true, ..Default::default() };
                [linie, self.staerke_zeile(size)]
            }
            Modus::Ruf => match text {
                Some(t) => self.umbruch(&format!("Ruf: {t}"), bereich_w, size),
                None => [Zeile::leer(), self.praefix_zeile("Ruf: ", None, bereich_w, size)],
            },
            Modus::Freitext => match text {
                Some(t) => self.umbruch(t, bereich_w, size),
                None => [
                    Zeile::leer(),
                    Zeile { segs: vec![Seg::Linie(bereich_w)], nur_platzhalter: true, volle_linie: false },
                ],
            },
            Modus::Dateiname => {
                let auto = self.name.replace('_', " ");
                self.umbruch(text.unwrap_or(&auto), bereich_w, size)
            }
        }
    }

    /// Hoehe des Textblocks (immer 2 Zeilen) inkl. Abstand nach unten, in mm.
    fn textblock_hoehe(&self, size: f64) -> f64 {
        let lh = size * self.cfg.text.zeilenabstand_faktor;
        self.face.ascender * size + lh + self.face.descender * size + self.cfg.text.text_unten_mm
    }

    /// Sucht die groesste Schriftgroesse (ab `size0` abwaerts bis Mindestgroesse), bei der alle
    /// echten Texte in die Breite passen. Liefert Zeilen, Groesse und ob es passt.
    fn plane(
        &self,
        breite: f64,
        erzeuge: &dyn Fn(f64) -> Option<Vec<Zeile>>,
    ) -> Option<(Vec<Zeile>, f64, bool)> {
        let passt = |zeilen: &[Zeile], size: f64| {
            zeilen.iter().all(|z| z.nur_platzhalter || z.breite(self.face, size) <= breite + 1e-9)
        };
        let size0 = pt_to_mm(self.cfg.text.font_size_pt);
        let min_size = pt_to_mm(self.cfg.text.min_schrift_pt.min(self.cfg.text.font_size_pt));
        let mut size = size0;
        let mut zeilen = erzeuge(size)?;
        while !passt(&zeilen, size) && size - pt_to_mm(VERKLEINERUNG_SCHRITT_PT) >= min_size - 1e-9 {
            size -= pt_to_mm(VERKLEINERUNG_SCHRITT_PT);
            zeilen = erzeuge(size)?;
        }
        let ok = passt(&zeilen, size);
        Some((zeilen, size, ok))
    }

    /// Text am unteren Rand von `bereich`, Grafik im Rest darueber. Reicht die Breite fuer zwei
    /// Zeilen nicht, wird (falls vom Zeichen erlaubt und Platz vorhanden) eine dritte Zeile
    /// oberhalb des Textblocks verwendet - ohne die Grafik zu verkleinern oder zu beruehren.
    fn text_und_grafik(
        &mut self,
        bereich: Rect,
        spec: &ZeichenSpec,
        grafik: Option<Arc<Grafik>>,
    ) -> Option<Platzierung> {
        if spec.modus == Modus::OhneText {
            return grafik.and_then(|g| self.platziere(g, bereich, spec));
        }
        let size0 = pt_to_mm(self.cfg.text.font_size_pt);
        let lh = size0 * self.cfg.text.zeilenabstand_faktor;
        let baseline2 = bereich.bottom() - self.cfg.text.text_unten_mm - self.face.descender * size0;
        let baseline1 = baseline2 - lh;
        let baseline0 = baseline1 - lh;

        // Grafik immer fuer zwei Textzeilen einpassen (wird durch eine 3. Zeile nicht kleiner)
        let block_h = self.textblock_hoehe(size0);
        let grafik_bereich = Rect::new(
            bereich.x,
            bereich.y,
            bereich.w,
            (bereich.h - block_h - self.cfg.text.abstand_grafik_text_mm).max(0.0),
        );
        let platzierung = grafik.and_then(|g| self.platziere(g, grafik_bereich, spec));

        let (zeilen2, size2, passt2) = self
            .plane(bereich.w, &|size| Some(Vec::from(self.zeilen(spec, bereich.w, size))))
            .expect("zwei Zeilen gibt es immer");

        // 3. Zeile: nur wenn zwei Zeilen nicht reichen, drei passen und die Oberkante der
        // obersten Zeile unterhalb der Grafik liegt.
        let mut drei: Option<(Vec<Zeile>, f64)> = None;
        if !passt2 {
            if let Some((zeilen3, size3, true)) = self.plane(bereich.w, &|size| self.zeilen3(spec, size)) {
                let oberkante = baseline0 - self.face.ascender * size0;
                let grafik_unten = platzierung.as_ref().map_or(bereich.y, |p| p.ziel.bottom());
                if oberkante >= grafik_unten - 1e-9 {
                    self.dritte_zeile_moeglich = true;
                    drei = Some((zeilen3, size3));
                }
            }
        }

        let min_pt = self.cfg.text.min_schrift_pt.min(self.cfg.text.font_size_pt);
        match (spec.drei_zeilen, drei) {
            (true, Some((zeilen3, size3))) => {
                self.hinweis(
                    HinweisArt::TextVerkleinert,
                    format!("Text dreizeilig gesetzt ({:.1} pt)", size3 / pt_to_mm(1.0)),
                );
                self.zeichne_block(&zeilen3, &[baseline0, baseline1, baseline2], size3, bereich);
            }
            (wunsch, drei) => {
                if !passt2 {
                    let zusatz = if drei.is_some() {
                        " - 3. Zeile in der Vorschau zuschaltbar"
                    } else if wunsch {
                        " - 3. Zeile nicht moeglich (kein Platz neben der Grafik oder Text zu lang)"
                    } else {
                        ""
                    };
                    self.hinweis(
                        HinweisArt::TextZuLang,
                        format!("Text passt bei {min_pt:.0} pt nicht in {:.1} mm Breite{zusatz}", bereich.w),
                    );
                } else if (size2 - size0).abs() > 1e-9 {
                    self.hinweis(
                        HinweisArt::TextVerkleinert,
                        format!(
                            "Schrift von {:.1} pt auf {:.1} pt verkleinert",
                            self.cfg.text.font_size_pt,
                            size2 / pt_to_mm(1.0)
                        ),
                    );
                }
                self.zeichne_block(&zeilen2, &[baseline1, baseline2], size2, bereich);
            }
        }
        platzierung
    }

    /// Zeichnet Zeilen an den Grundlinien: als Block zentriert, Zeilen linksbuendig zueinander.
    fn zeichne_block(&mut self, zeilen: &[Zeile], baselines: &[f64], size: f64, bereich: Rect) {
        let echte = zeilen.iter().filter(|z| !z.ist_leer() && !z.volle_linie).count();
        let blockbreite = zeilen
            .iter()
            .filter(|z| !z.ist_leer() && !z.volle_linie)
            .map(|z| z.breite(self.face, size))
            .fold(0.0_f64, f64::max);
        let x0 = bereich.x + (bereich.w - blockbreite) / 2.0;
        for (zeile, baseline) in zeilen.iter().zip(baselines.iter().copied()) {
            if zeile.volle_linie {
                let rand = self.cfg.linien.schreiblinie_rand_mm;
                self.svg.line(
                    bereich.x + rand,
                    baseline,
                    bereich.right() - rand,
                    baseline,
                    Rgb::SCHREIBLINIE,
                    self.cfg.linien.schreiblinie_mm,
                );
                continue;
            }
            // Einzelne Zeile (z.B. Staerke ohne Partnerzeile) fuer sich zentrieren
            let x_start =
                if echte == 1 { bereich.x + (bereich.w - zeile.breite(self.face, size)) / 2.0 } else { x0 };
            self.zeichne_zeile(zeile, x_start, baseline, size);
        }
    }

    fn zeichne_zeile(&mut self, zeile: &Zeile, x: f64, baseline: f64, size: f64) {
        let mut x = x;
        let family = self.face.family.clone();
        for seg in &zeile.segs {
            match seg {
                Seg::Text(t) => {
                    self.svg.text(x, baseline, t, &family, size, Rgb::SCHWARZ, Anker::Start, None);
                    x += self.face.breite(t, size);
                }
                Seg::Luecke(w) => x += w,
                Seg::Linie(w) => {
                    let dicke = self.face.underline_dicke * size;
                    let y = baseline + self.face.underline_position * size - dicke / 2.0;
                    self.svg.rect_fill(x, y, *w, dicke, Rgb::SCHWARZ);
                    x += w;
                }
            }
        }
    }

    /// Passt die Grafik in den Bereich ein.
    fn platziere(&mut self, grafik: Arc<Grafik>, bereich: Rect, spec: &ZeichenSpec) -> Option<Platzierung> {
        let mut r = bereich;
        // Abweichung am Zeichen hat Vorrang vor der Einstellung fuer alle Zeichen
        if let Some([max_w, max_h]) = spec.grafik_max_mm.or(self.cfg.grafik_max_mm) {
            let w = max_w.clamp(0.0, r.w);
            let h = max_h.clamp(0.0, r.h);
            let y = match (spec.modus, spec.grafik_position) {
                (Modus::OhneText, GrafikPosition::Mittig) => r.y + (r.h - h) / 2.0,
                (Modus::OhneText, GrafikPosition::Unten) => r.bottom() - h,
                _ => r.y,
            };
            r = Rect::new(r.x + (r.w - w) / 2.0, y, w, h);
        }
        if r.w < 0.5 || r.h < 0.5 {
            self.hinweis(
                HinweisArt::GrafikKeinPlatz,
                "Kein Platz fuer die Grafik (Text oder Abstaende zu gross)".into(),
            );
            return None;
        }
        let ib = grafik.inhalt;
        let s = (r.w / ib.w).min(r.h / ib.h);
        let (w, h) = (ib.w * s, ib.h * s);
        let x = r.x + (r.w - w) / 2.0;
        let y = match (spec.modus, spec.grafik_position) {
            (Modus::OhneText, GrafikPosition::Mittig) => r.y + (r.h - h) / 2.0,
            (Modus::OhneText, GrafikPosition::Unten) => r.bottom() - h,
            _ => r.y,
        };
        Some(Platzierung { grafik, ziel: Rect::new(x, y, w, h) })
    }

    // -----------------------------------------------------------------------------------------
    // S1 (Doppelschild)
    // -----------------------------------------------------------------------------------------

    fn s1(
        &mut self,
        inhalt: Rect,
        spec: &ZeichenSpec,
        grafik: Option<Arc<Grafik>>,
        blanko: Option<BlankoArt>,
    ) -> Option<Platzierung> {
        let s1 = self.cfg.s1;
        let links_w = inhalt.w * s1.links_prozent / 100.0;
        let links = Rect::new(inhalt.x, inhalt.y, links_w, inhalt.h);
        let rechts = Rect::new(inhalt.x + links_w, inhalt.y, inhalt.w - links_w, inhalt.h);

        let (links_linien, staerke) = match blanko {
            Some(BlankoArt::S1Leer | BlankoArt::Leer) => return None,
            Some(BlankoArt::S1Linien) => (true, false),
            Some(BlankoArt::S1LinienStaerke) => (true, true),
            _ => (false, s1.staerke_anzeigen),
        };

        let mut platzierung = None;
        if links_linien {
            self.schreiblinien(links, s1.anzahl_schreiblinien, false, true, false);
        } else {
            platzierung = self.text_und_grafik(links, spec, grafik);
        }
        self.schreiblinien(rechts, s1.anzahl_schreiblinien, staerke, !links_linien, true);
        platzierung
    }

    /// Schreiblinien von unten nach oben. Oberste Linie optional als Staerke-Anzeige.
    fn schreiblinien(
        &mut self,
        bereich: Rect,
        anzahl: u32,
        staerke: bool,
        rand_links: bool,
        rand_rechts: bool,
    ) {
        let anzahl = anzahl.max(1);
        let unten = self.cfg.text.text_unten_mm;
        let lh = (bereich.h - unten) / anzahl as f64;
        let rand = self.cfg.linien.schreiblinie_rand_mm;
        let dicke = self.cfg.linien.schreiblinie_mm;
        let x0 = bereich.x + if rand_links { rand } else { 0.0 };
        let x1 = bereich.right() - if rand_rechts { rand } else { 0.0 };
        for i in 0..anzahl {
            // Linie vollstaendig im Bereich halten
            let y = (bereich.bottom() - unten - i as f64 * lh).min(bereich.bottom() - dicke / 2.0);
            if staerke && i == anzahl - 1 {
                self.staerke_anzeige(y, x0, x1, lh);
            } else {
                self.svg.line(x0, y, x1, y, Rgb::SCHREIBLINIE, dicke);
            }
        }
    }

    /// Staerke als Geometrie: Rand | / / / | Luecke | Unterstrich (25 %).
    fn staerke_anzeige(&mut self, y: f64, x0: f64, x1: f64, lh: f64) {
        let dicke = self.cfg.linien.schreiblinie_mm;
        let verfuegbar = x1 - x0;
        let hoehe = lh * S1_STAERKE_HOEHE_FAKTOR;
        let us_start = x1 - verfuegbar * S1_STAERKE_UNTERSTRICH_FAKTOR;
        let bereich_start = x0 + verfuegbar * S1_STAERKE_RAND_LINKS_FAKTOR;
        let bereich_ende = us_start - verfuegbar * S1_STAERKE_LUECKE_FAKTOR;
        let strich_w = hoehe / S1_STAERKE_WINKEL_GRAD.to_radians().tan();
        let n = S1_STAERKE_SCHRAEGSTRICHE as f64;
        let abstand = ((bereich_ende - bereich_start) - n * strich_w) / (n - 1.0);
        let mut x = bereich_start;
        for _ in 0..S1_STAERKE_SCHRAEGSTRICHE {
            self.svg.line(x, y, x + strich_w, y - hoehe, Rgb::SCHREIBLINIE, dicke);
            x += strich_w + abstand;
        }
        self.svg.line(us_start, y, x1, y, Rgb::SCHREIBLINIE, dicke);
    }

    // -----------------------------------------------------------------------------------------
    // Schnittlinien (Einzelzeichen)
    // -----------------------------------------------------------------------------------------

    fn schnittlinien(&mut self, geo: &ZeichenGeometrie) {
        let d = self.cfg.linien.schnittlinie_mm;
        let family = self.face.family.clone();
        let label = |b: &mut SvgBuilder, x: f64, y: f64, text: String, farbe: Rgb| {
            b.text(x, y, &text, &family, SCHNITT_LABEL_MM, farbe, Anker::Start, Some(Rgb::WEISS));
        };
        let g = self.cfg.groesse();
        let datei = geo.datei.inset(d / 2.0);
        self.svg.rect_stroke(datei.x, datei.y, datei.w, datei.h, Rgb::BESCHNITT, d);
        let s = geo.schnitt;
        self.svg.rect_stroke(s.x, s.y, s.w, s.h, Rgb::SCHNITT, d);
        let i = geo.inhalt;
        self.svg.rect_stroke(i.x, i.y, i.w, i.h, Rgb::SICHERHEIT, d);
        if self.cfg.layout == Layout::S1 {
            let x = i.x + i.w * self.cfg.s1.links_prozent / 100.0;
            self.svg.line(x, i.y, x, i.bottom(), Rgb::S1_TRENNLINIE, d);
        }
        let off = SCHNITT_LABEL_MM * 0.5;
        label(
            &mut self.svg,
            off,
            off + SCHNITT_LABEL_MM,
            format!("BESCHNITT ({:.1}x{:.1}mm)", geo.datei.w, geo.datei.h),
            Rgb::BESCHNITT,
        );
        label(
            &mut self.svg,
            s.x + off,
            s.y + off + SCHNITT_LABEL_MM,
            format!("SCHNITT ({:.1}x{:.1}mm)", g.breite_mm, g.hoehe_mm),
            Rgb::SCHNITT,
        );
        label(
            &mut self.svg,
            i.x + off,
            i.y + off + SCHNITT_LABEL_MM,
            format!("INHALT ({:.1}x{:.1}mm)", i.w, i.h),
            Rgb::SICHERHEIT,
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::DruckConfig;

    /// Zeichen ohne Grafik, aber mit Text (Blanko-Variante, die im S2-Layout Text traegt).
    fn spec(modus: Modus, text: Option<&str>) -> ZeichenSpec {
        ZeichenSpec {
            vorlage: VorlageRef::Blanko { blanko: BlankoArt::S1Linien },
            modus,
            text: text.map(String::from),
            ..Default::default()
        }
    }

    #[test]
    fn blank_s2_sign_is_completely_empty() {
        let fonts = Fonts::system();
        for layout in [Layout::S2, Layout::S1] {
            let cfg = DruckConfig { layout, ..Default::default() };
            let s = ZeichenSpec { modus: Modus::OvStaerke, text: Some("Text".into()), ..Default::default() };
            let k = compose(&s, None, &cfg, &fonts, ComposeOptionen::default()).unwrap();
            assert!(k.overlay_svg.ends_with("\"></svg>"), "{layout:?}: {}", k.overlay_svg);
            assert!(k.grafik.is_none());
        }
    }

    #[test]
    fn long_text_offers_third_line_and_uses_it_when_enabled() {
        let fonts = Fonts::system();
        // S2-Zeichen mit derselben Inhaltsbreite wie der linke S1-Bereich (34,4 mm)
        let mut cfg = DruckConfig::default();
        cfg.s2.breite_mm = 34.4 + 2.0 * cfg.s2.sicherheitsabstand_mm;
        let text = "FGr Führung-Kommunikation Führungs und Kommunikationstrupp";

        // Ohne 3. Zeile: passt bei 8 pt nicht -> Warnung, 3. Zeile wird angeboten (keine Grafik)
        let k = compose(&spec(Modus::Freitext, Some(text)), None, &cfg, &fonts, ComposeOptionen::default())
            .unwrap();
        assert!(k.dritte_zeile_moeglich);
        assert!(k.hinweise.iter().any(|h| h.art == HinweisArt::TextZuLang), "{:?}", k.hinweise);

        // Mit 3. Zeile: passt, bleibt im Inhaltsbereich
        let s = ZeichenSpec { drei_zeilen: true, ..spec(Modus::Freitext, Some(text)) };
        let k = compose(&s, None, &cfg, &fonts, ComposeOptionen::default()).unwrap();
        assert!(!k.hinweise.iter().any(|h| h.art == HinweisArt::TextZuLang), "{:?}", k.hinweise);
        assert_eq!(k.overlay_svg.matches("<text").count(), 3, "{}", k.overlay_svg);
        let tree = parse(&k.overlay_svg, &fonts);
        let bb = tree.root().abs_stroke_bounding_box();
        let mm = |px: f32| crate::units::css_px_to_mm(px as f64);
        assert!(mm(bb.left()) >= k.geometrie.inhalt.x - 0.01, "links {}", mm(bb.left()));
        assert!(mm(bb.right()) <= k.geometrie.inhalt.right() + 0.01, "rechts {}", mm(bb.right()));
    }

    #[test]
    fn third_line_is_refused_when_graphic_would_collide() {
        let fonts = Fonts::system();
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("hoch.svg");
        // Hohe, schmale Grafik fuellt den Grafikbereich bis unten
        std::fs::write(&p, r#"<svg xmlns="http://www.w3.org/2000/svg" width="10" height="40"><rect width="10" height="40"/></svg>"#)
            .unwrap();
        let g = crate::grafik::lade(&p, &fonts).unwrap();
        let mut cfg = DruckConfig::default();
        cfg.s2.breite_mm = 34.4 + 2.0 * cfg.s2.sicherheitsabstand_mm;
        let s = ZeichenSpec {
            vorlage: VorlageRef::Datei { pfad: p },
            modus: Modus::Freitext,
            text: Some("FGr Führung-Kommunikation Führungs und Kommunikationstrupp".into()),
            drei_zeilen: true,
            ..Default::default()
        };
        let k = compose(&s, Some(g), &cfg, &fonts, ComposeOptionen::default()).unwrap();
        assert!(!k.dritte_zeile_moeglich);
        assert_eq!(k.overlay_svg.matches("<text").count(), 2);
        assert!(k.hinweise.iter().any(|h| h.text.contains("3. Zeile nicht moeglich")), "{:?}", k.hinweise);
    }

    fn parse(svg: &str, fonts: &Fonts) -> usvg::Tree {
        usvg::Tree::from_str(svg, &crate::grafik::usvg_options(fonts)).expect("Overlay parsebar")
    }

    #[test]
    fn all_modes_compose_and_parse() {
        let fonts = Fonts::system();
        for layout in [Layout::S2, Layout::S1] {
            let cfg = DruckConfig { layout, ..Default::default() };
            for modus in Modus::ALLE {
                for text in [None, Some("Musterstadt-Nord")] {
                    let k = compose(
                        &spec(modus, text),
                        None,
                        &cfg,
                        &fonts,
                        ComposeOptionen { schnittlinien: true },
                    )
                    .unwrap();
                    let tree = parse(&k.overlay_svg, &fonts);
                    if modus != Modus::OhneText {
                        assert!(tree.root().has_children(), "{modus:?} {layout:?} ohne Inhalt");
                    }
                }
            }
        }
    }

    #[test]
    fn long_text_is_wrapped_into_two_lines() {
        let fonts = Fonts::system();
        let cfg = DruckConfig::default();
        let k = compose(
            &spec(Modus::Freitext, Some("Technische Einsatzleitung Abschnitt Nord-West Erweiterung")),
            None,
            &cfg,
            &fonts,
            ComposeOptionen::default(),
        )
        .unwrap();
        assert_eq!(k.overlay_svg.matches("<text").count(), 2, "{}", k.overlay_svg);
    }

    #[test]
    fn text_stays_inside_content_area() {
        let fonts = Fonts::system();
        let cfg = DruckConfig::default();
        let k = compose(
            &spec(Modus::OvStaerke, Some("Musterstadt")),
            None,
            &cfg,
            &fonts,
            ComposeOptionen::default(),
        )
        .unwrap();
        let tree = parse(&k.overlay_svg, &fonts);
        let bb = tree.root().abs_stroke_bounding_box();
        let mm = |px: f32| crate::units::css_px_to_mm(px as f64);
        let inhalt = k.geometrie.inhalt;
        assert!(mm(bb.left()) >= inhalt.x - 0.01, "links {}", mm(bb.left()));
        assert!(mm(bb.right()) <= inhalt.right() + 0.01, "rechts {}", mm(bb.right()));
        assert!(mm(bb.bottom()) <= inhalt.bottom() + 0.3, "unten {}", mm(bb.bottom()));
    }

    #[test]
    fn global_max_graphic_size_and_override() {
        let fonts = Fonts::system();
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("q.svg");
        std::fs::write(&p, r#"<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>"#)
            .unwrap();
        let g = crate::grafik::lade(&p, &fonts).unwrap();
        let cfg = DruckConfig { grafik_max_mm: Some([20.0, 20.0]), ..Default::default() };
        let s = ZeichenSpec {
            vorlage: VorlageRef::Datei { pfad: p },
            modus: Modus::OvStaerke,
            ..Default::default()
        };
        let k = compose(&s, Some(g.clone()), &cfg, &fonts, ComposeOptionen::default()).unwrap();
        let ziel = k.grafik.unwrap().ziel;
        assert!(ziel.w <= 20.0 + 1e-6 && ziel.h <= 20.0 + 1e-6, "{ziel:?}");
        assert!((ziel.w - 20.0).abs() < 0.5, "global begrenzt: {ziel:?}");

        let s2 = ZeichenSpec { grafik_max_mm: Some([10.0, 10.0]), ..s };
        let k2 = compose(&s2, Some(g), &cfg, &fonts, ComposeOptionen::default()).unwrap();
        let z2 = k2.grafik.unwrap().ziel;
        assert!((z2.w - 10.0).abs() < 0.5, "Zeichen ueberschreibt: {z2:?}");
    }

    #[test]
    fn graphic_area_leaves_room_for_text() {
        let fonts = Fonts::system();
        let dir = tempfile::tempdir().unwrap();
        let p = dir.path().join("q.svg");
        std::fs::write(&p, r#"<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>"#)
            .unwrap();
        let g = crate::grafik::lade(&p, &fonts).unwrap();
        let cfg = DruckConfig::default();
        let s = ZeichenSpec {
            vorlage: VorlageRef::Datei { pfad: p },
            modus: Modus::OvStaerke,
            ..Default::default()
        };
        let k = compose(&s, Some(g.clone()), &cfg, &fonts, ComposeOptionen::default()).unwrap();
        let ziel = k.grafik.unwrap().ziel;
        let inhalt = k.geometrie.inhalt;
        assert!((ziel.y - inhalt.y).abs() < 1e-9, "Grafik oben");
        assert!(ziel.bottom() < inhalt.bottom() - 8.0, "Platz fuer 2 Textzeilen");
        assert!(((ziel.x + ziel.w / 2.0) - (inhalt.x + inhalt.w / 2.0)).abs() < 1e-9, "zentriert");

        // Nur Grafik, unten
        let s2 = ZeichenSpec { modus: Modus::OhneText, grafik_position: GrafikPosition::Unten, ..s };
        let k2 = compose(&s2, Some(g), &cfg, &fonts, ComposeOptionen::default()).unwrap();
        let z2 = k2.grafik.unwrap().ziel;
        assert!((z2.bottom() - inhalt.bottom()).abs() < 1e-9);
    }
}
