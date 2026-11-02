//! Vektor-PDF mit svg2pdf + pdf-writer.
//!
//! Jede Grafik und jedes Overlay wird genau einmal als Form-XObject eingebettet
//! und dann beliebig oft platziert (Kopien kosten fast keinen Speicherplatz).
//! Die Umwandlung SVG -> PDF-Chunk laeuft parallel.

use std::collections::HashMap;
use std::sync::Arc;

use pdf_writer::{Chunk, Content, Finish, Name, Pdf, Rect as PdfRect, Ref, TextStr};
use rayon::prelude::*;

use crate::compose::Komposition;
use crate::error::{Error, Result};
use crate::fonts::Fonts;
use crate::geometry::Rect;
use crate::grafik::{usvg_options, Grafik};
use crate::units::mm_to_pt;

/// Optionen fuer das PDF.
#[derive(Debug, Clone)]
pub struct PdfOptionen {
    pub titel: String,
    pub ersteller: String,
    /// Text in Pfade umwandeln statt Schriften einzubetten.
    pub text_als_pfade: bool,
}

/// Ergebnis einer parallelen Umwandlung: Quelle, ggf. Grafik, PDF-Chunk mit Wurzel-Referenz.
type ChunkErgebnis = (Quelle, Option<Arc<Grafik>>, Result<(Chunk, Ref)>);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum Quelle {
    Grafik(usize),
    Svg(String),
}

/// PDF im Aufbau.
pub struct PdfDokument {
    pdf: Pdf,
    next: i32,
    catalog: Ref,
    page_tree: Ref,
    pages: Vec<Ref>,
    xobjects: HashMap<Quelle, Ref>,
    /// Haelt Grafiken am Leben, solange ihr Zeiger als Schluessel dient.
    grafiken: Vec<Arc<Grafik>>,
    fonts: Fonts,
    opt: PdfOptionen,
}

/// Ein Element auf einer Seite (Koordinaten in mm, y nach unten).
pub enum SeitenElement<'a> {
    /// Komposition mit linker oberer Ecke der *Datei* bei (x, y). Optional auf ein
    /// Rechteck der Komposition zugeschnitten (z.B. Schnittbereich im Bogen).
    Zeichen { k: &'a Komposition, x: f64, y: f64, zuschnitt: Option<Rect> },
    /// Beliebiges SVG gleicher Groesse wie die Seite (Hinweistexte).
    SvgSeite { svg: &'a str },
    /// Rechteck-Umriss in RGB (0..1) und Strichstaerke in pt.
    Rahmen { r: Rect, rgb: [f32; 3], dicke_pt: f32 },
}

impl PdfDokument {
    pub fn new(fonts: &Fonts, opt: PdfOptionen) -> Self {
        let mut doc = Self {
            pdf: Pdf::new(),
            next: 1,
            catalog: Ref::new(1),
            page_tree: Ref::new(2),
            pages: Vec::new(),
            xobjects: HashMap::new(),
            grafiken: Vec::new(),
            fonts: fonts.clone(),
            opt,
        };
        doc.catalog = doc.alloc();
        doc.page_tree = doc.alloc();
        doc
    }

    fn alloc(&mut self) -> Ref {
        let r = Ref::new(self.next);
        self.next += 1;
        r
    }

    fn conversion(&self) -> svg2pdf::ConversionOptions {
        svg2pdf::ConversionOptions { embed_text: !self.opt.text_als_pfade, ..Default::default() }
    }

    /// Wandelt alle noch unbekannten Grafiken/Overlays parallel in XObjects um.
    pub fn vorbereiten<'a>(
        &mut self,
        elemente: impl IntoIterator<Item = &'a SeitenElement<'a>>,
    ) -> Result<()> {
        enum Job<'b> {
            Grafik(Arc<Grafik>),
            Svg(&'b str),
        }
        let mut jobs: Vec<(Quelle, Job)> = Vec::new();
        let mut gesehen = std::collections::HashSet::new();
        for e in elemente {
            let mut push = |q: Quelle, j: Job<'a>| {
                if !self.xobjects.contains_key(&q) && gesehen.insert(q.clone()) {
                    jobs.push((q, j));
                }
            };
            match e {
                SeitenElement::Zeichen { k, .. } => {
                    if let Some(p) = &k.grafik {
                        push(Quelle::Grafik(Arc::as_ptr(&p.grafik) as usize), Job::Grafik(p.grafik.clone()));
                    }
                    push(Quelle::Svg(k.overlay_svg.clone()), Job::Svg(&k.overlay_svg));
                }
                SeitenElement::SvgSeite { svg } => push(Quelle::Svg(svg.to_string()), Job::Svg(svg)),
                SeitenElement::Rahmen { .. } => {}
            }
        }
        let conv = self.conversion();
        let fonts = &self.fonts;
        let chunks: Vec<ChunkErgebnis> = jobs
            .into_par_iter()
            .map(|(q, job)| match job {
                Job::Grafik(g) => {
                    let r = svg2pdf::to_chunk(&g.tree, conv).map_err(|e| Error::Pdf(e.to_string()));
                    (q, Some(g), r)
                }
                Job::Svg(svg) => {
                    let r = usvg::Tree::from_str(svg, &usvg_options(fonts))
                        .map_err(|e| Error::InternalSvg(e.to_string()))
                        .and_then(|t| svg2pdf::to_chunk(&t, conv).map_err(|e| Error::Pdf(e.to_string())));
                    (q, None, r)
                }
            })
            .collect();
        for (q, g, r) in chunks {
            let (chunk, root) = r?;
            let mut map = HashMap::new();
            let mut next = self.next;
            let renumbered = chunk.renumber(|old| {
                *map.entry(old).or_insert_with(|| {
                    let r = Ref::new(next);
                    next += 1;
                    r
                })
            });
            self.next = next;
            let neu = *map.get(&root).ok_or_else(|| Error::Pdf("XObject-Referenz fehlt".into()))?;
            self.pdf.extend(&renumbered);
            self.xobjects.insert(q, neu);
            if let Some(g) = g {
                self.grafiken.push(g);
            }
        }
        Ok(())
    }

    /// Fuegt eine Seite hinzu. `trim` = Endformat (TrimBox) bei Einzelzeichen.
    pub fn seite(
        &mut self,
        w_mm: f64,
        h_mm: f64,
        trim: Option<Rect>,
        elemente: &[SeitenElement],
    ) -> Result<()> {
        self.vorbereiten(elemente.iter())?;
        let page_id = self.alloc();
        let content_id = self.alloc();
        let hp = h_mm;
        let pt = |v: f64| mm_to_pt(v) as f32;
        let mut content = Content::new();
        let mut namen: Vec<(String, Ref)> = Vec::new();
        let name_fuer = |r: Ref, namen: &mut Vec<(String, Ref)>| -> String {
            if let Some((n, _)) = namen.iter().find(|(_, rr)| *rr == r) {
                return n.clone();
            }
            let n = format!("X{}", namen.len());
            namen.push((n.clone(), r));
            n
        };
        // XObject (Einheitsquadrat) auf Rechteck (mm, y nach unten) abbilden.
        let platziere = |content: &mut Content, name: &str, x: f64, y: f64, w: f64, h: f64| {
            content.save_state();
            content.transform([pt(w), 0.0, 0.0, pt(h), pt(x), pt(hp - y - h)]);
            content.x_object(Name(name.as_bytes()));
            content.restore_state();
        };
        let clip = |content: &mut Content, r: &Rect| {
            content.rect(pt(r.x), pt(hp - r.bottom()), pt(r.w), pt(r.h));
            content.clip_nonzero();
            content.end_path();
        };

        for e in elemente {
            match e {
                SeitenElement::Zeichen { k, x, y, zuschnitt } => {
                    content.save_state();
                    if let Some(z) = zuschnitt {
                        clip(&mut content, &Rect::new(x + z.x, y + z.y, z.w, z.h));
                    }
                    if let Some(p) = &k.grafik {
                        let r = self.xobjects[&Quelle::Grafik(Arc::as_ptr(&p.grafik) as usize)];
                        let n = name_fuer(r, &mut namen);
                        let ib = p.grafik.inhalt;
                        let s = p.ziel.w / ib.w; // mm pro Baum-Einheit
                        let size = p.grafik.tree.size();
                        content.save_state();
                        clip(&mut content, &Rect::new(x + p.ziel.x, y + p.ziel.y, p.ziel.w, p.ziel.h));
                        platziere(
                            &mut content,
                            &n,
                            x + p.ziel.x - ib.x * s,
                            y + p.ziel.y - ib.y * s,
                            size.width() as f64 * s,
                            size.height() as f64 * s,
                        );
                        content.restore_state();
                    }
                    let r = self.xobjects[&Quelle::Svg(k.overlay_svg.clone())];
                    let n = name_fuer(r, &mut namen);
                    platziere(&mut content, &n, *x, *y, k.geometrie.datei.w, k.geometrie.datei.h);
                    content.restore_state();
                }
                SeitenElement::SvgSeite { svg } => {
                    let r = self.xobjects[&Quelle::Svg(svg.to_string())];
                    let n = name_fuer(r, &mut namen);
                    platziere(&mut content, &n, 0.0, 0.0, w_mm, h_mm);
                }
                SeitenElement::Rahmen { r, rgb, dicke_pt } => {
                    content.save_state();
                    content.set_stroke_rgb(rgb[0], rgb[1], rgb[2]);
                    content.set_line_width(*dicke_pt);
                    content.rect(pt(r.x), pt(hp - r.bottom()), pt(r.w), pt(r.h));
                    content.stroke();
                    content.restore_state();
                }
            }
        }

        let media = PdfRect::new(0.0, 0.0, pt(w_mm), pt(h_mm));
        let mut page = self.pdf.page(page_id);
        page.media_box(media);
        if let Some(t) = trim {
            page.bleed_box(media);
            page.trim_box(PdfRect::new(pt(t.x), pt(hp - t.bottom()), pt(t.right()), pt(hp - t.y)));
        }
        page.parent(self.page_tree);
        page.contents(content_id);
        let mut res = page.resources();
        let mut xo = res.x_objects();
        for (n, r) in &namen {
            xo.pair(Name(n.as_bytes()), *r);
        }
        xo.finish();
        res.finish();
        page.finish();
        self.pdf.stream(content_id, &content.finish());
        self.pages.push(page_id);
        Ok(())
    }

    pub fn anzahl_seiten(&self) -> usize {
        self.pages.len()
    }

    /// Schliesst das Dokument ab.
    pub fn finish(mut self) -> Vec<u8> {
        let info = self.alloc();
        let mut catalog = self.pdf.catalog(self.catalog);
        catalog.pages(self.page_tree);
        // Druckdialog: "Tatsaechliche Groesse" vorschlagen
        catalog.insert(Name(b"ViewerPreferences")).dict().pair(Name(b"PrintScaling"), Name(b"None"));
        catalog.finish();
        let count = self.pages.len() as i32;
        self.pdf.pages(self.page_tree).kids(self.pages.iter().copied()).count(count);
        self.pdf
            .document_info(info)
            .title(TextStr(&self.opt.titel))
            .creator(TextStr(&self.opt.ersteller))
            .producer(TextStr(&self.opt.ersteller));
        self.pdf.finish()
    }
}
