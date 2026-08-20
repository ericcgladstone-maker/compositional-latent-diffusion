#!/usr/bin/env python3
"""Fold the 2026-07 comment-driven analyses (W1-W8) into the master docx.

Prose-rule compliant: no em dashes, no semicolons, no performative/banned terms.
Every table is built directly from the source CSVs (no hand transcription), so
all numbers are traceable to raw. Adds a "Follow-up analyses" section after the
confirmation subsections, with three grayscale figures, and appends a new
specification-details note. Also updates the transmissibility_mode options cell.
"""
import csv, glob, os, shutil
import docx
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.abspath(os.path.join(HERE, "..", "latent-adoption-build-review.docx"))
D1 = sorted(glob.glob(os.path.join(HERE, "results", "*-comments")))[-1]
D2 = sorted(glob.glob(os.path.join(HERE, "results", "*-comments2")))[-1]
S1 = os.path.basename(D1).split("-comments")[0]   # provenance stamp
S2 = os.path.basename(D2).split("-comments2")[0]

def rows(path):
    return list(csv.DictReader(open(path)))

w1 = rows(os.path.join(D1, "w1_capacity_x_k.csv"))
w2 = rows(os.path.join(D1, "w2_stab_x_enh.csv"))
w3 = rows(os.path.join(D1, "w3_carriers.csv"))
w8 = rows(os.path.join(D1, "w8_density_under_cap.csv"))
w4 = rows(os.path.join(D2, "w4_overlap_leakage.csv"))
w5 = rows(os.path.join(D2, "w5_ecology.csv"))
w6 = rows(os.path.join(D2, "w6_coupling_matrix.csv"))
w7 = rows(os.path.join(D2, "w7_cuegated.csv"))

FIG_W1 = os.path.join(D1, "fig_w1_capacity_ratio.png")
FIG_W2 = os.path.join(D1, "fig_w2_stab_enh.png")
FIG_W5 = os.path.join(D2, "fig_w5_ecology.png")

def f2(x): return f"{float(x):.2f}"
def f3(x): return f"{float(x):.3f}"

# ---- build the W1 grid table (k rows x capacity cols) ----
def w1_table():
    caps = sorted({int(r["capacity"]) for r in w1})
    ks = sorted({int(r["sufficiency_k"]) for r in w1})
    hdr = ["k \\ capacity"] + [str(c) for c in caps]
    body = []
    for k in ks:
        row = [str(k)] + [f2(next(r["final_manifest_share"] for r in w1
                             if int(r["sufficiency_k"]) == k and int(r["capacity"]) == c))
                          for c in caps]
        body.append(row)
    return hdr, body

def w2_table():
    facs = sorted({float(r["enhanced_factor"]) for r in w2})
    boosts = sorted({float(r["stabilization_boost"]) for r in w2})
    hdr = ["boost \\ enhanced"] + [f"{e:g}" for e in facs]
    body = []
    for b in boosts:
        row = [f"{b:g}"] + [f2(next(r["final_manifest_share"] for r in w2
                            if float(r["stabilization_boost"]) == b and float(r["enhanced_factor"]) == e))
                           for e in facs]
        body.append(row)
    return hdr, body

def w3_table():
    hdr = ["Transmissibility mode", "Carrier fraction (per big thing)", "Pure carriers", "Manifest share"]
    body = [[r["mode"], f2(r["carrier_per_bt"]), f2(r["pure_carrier"]), f2(r["manifest_share"])]
            for r in w3]
    return hdr, body

def w8_table():
    hdr = ["Initial element density (capacity 6)", "Final adoption", "Peak adoption"]
    body = [[r["initial_element_density"], f2(r["final_manifest_share"]),
             f2(float(r["final_manifest_share"]) + float(r["overshoot"]))] for r in w8]
    return hdr, body

def w4_table():
    hdr = ["Element overlap", "Insular leakage to beta", "Outside beta adoption"]
    body = [[r["element_overlap"], f2(r["insular_leakage_to_beta"]), f2(r["outside_beta_adoption"])]
            for r in w4]
    return hdr, body

def w5_table():
    betas = sorted({float(r["beta_compression"]) for r in w5})
    alphas = sorted({float(r["alpha_compression"]) for r in w5})
    hdr = ["Alpha compression"] + [f"Alpha share (rival {b:g})" for b in betas]
    body = []
    for a in alphas:
        row = [f"{a:g}"] + [f2(next(r["alpha_share"] for r in w5
                            if float(r["alpha_compression"]) == a and float(r["beta_compression"]) == b))
                           for b in betas]
        body.append(row)
    return hdr, body

def w6_table():
    hdr = ["Channel", "Matrix entry", "Final adoption", "Lapse rate"]
    body = []
    for r in w6:
        if r["kind"] == "off_diagonal":
            body.append(["cross-target (off-diagonal)", f"{float(r['value']):g}", f2(r["final"]), f2(r["lapse_rate"])])
    for r in w6:
        if r["kind"] == "diagonal":
            body.append(["same-target (diagonal)", f"{float(r['value']):g}", f2(r["final"]), f2(r["lapse_rate"])])
    return hdr, body

def w7_table():
    order = ["elements_only", "whole_package_gated", "whole_package", "both"]
    d = {r["mode"]: r for r in w7}
    hdr = ["Transmissibility mode", "Final adoption", "Overshoot", "Lapse rate", "Observability gap"]
    body = [[m, f2(d[m]["final"]), f2(d[m]["overshoot"]), f2(d[m]["lapse_rate"]), f2(d[m]["observability_gap"])]
            for m in order if m in d]
    return hdr, body

# ---- prose (neutral register; numbers verifiable against the tables) ----
CONTENT = [
 ("H1", "Follow-up analyses (2026-07 review round)"),
 ("P", "The analyses in this section were added in response to the 2026-07 review "
       "comments. Each uses the same engine and the deterministic sweep protocol, 30 "
       "replications per cell at base seed 0. Three mechanisms were added for these "
       "analyses, a cue-gated whole-package transmissibility mode, an explicit coupling "
       "matrix, and per-big-thing mechanism endowments. Each was verified as byte-identical "
       "to the prior model across 18 mechanism paths when it is not enabled, so the earlier "
       f"results are unchanged. From sweeps {S1} and {S2}."),
 ("P", "Capacity transition and the needed-components ratio. The capacity transition "
       "tracks the ratio of needed components to memory slots. Holding the requirement at 4 "
       "and sweeping both capacity and the sufficiency threshold k, final adoption is "
       "organized by k over capacity. The half-adoption capacity is near 3.7, 5.6, and 7.2 "
       "for k of 2, 3, and 4, a needed-components-to-slots ratio near 0.54 in each case. "
       f"From sweep {S1}."),
 ("TABLE", w1_table),
 ("FIG", FIG_W1),
 ("P", "Stabilization and enhanced transmission, crossed. Crossing stabilization strength "
       "with the enhanced-transmission factor confirms the interaction. Adoption rises with "
       "the enhanced factor at every level of protection and rises as protection increases, "
       "from 0.27 at no protection and no enhancement to 1.00 at full protection with a "
       "threefold enhanced factor. Neither mechanism reaches saturation alone. "
       f"From sweep {S1}."),
 ("TABLE", w2_table),
 ("FIG", FIG_W2),
 ("P", "Carriers as a measured quantity. The separation of exposure from adoption is "
       "measured as the carrier fraction, the share of agents that hold and can transmit a "
       "big thing's elements while not being manifest for it. Under elements-only "
       "transmission the carrier fraction is 0.35 per big thing, and 0.08 of agents hold "
       "big-thing elements while manifest for no big thing at all. Under whole-package "
       "transmission the carrier fraction is 0.01, because the manifest state itself "
       "transmits. The carrier population is a property of piecemeal transmission. "
       f"From sweep {S1}."),
 ("TABLE", w3_table),
 ("P", "Element density under a binding capacity. Sweeping the initial element density "
       "with capacity held at the binding value of 6, final adoption is flat across the "
       "range, from 0.65 at density 0.05 to 0.65 at density 0.60, with the peak likewise "
       "flat. Under a binding capacity, initial density sets the timing of the latent build "
       f"and not the endpoint, which is fixed by the capacity constraint. From sweep {S1}."),
 ("TABLE", w8_table),
 ("P", "Cue-gated whole-package, isolating transmissibility. The whole-package and "
       "elements-only arms differ both in transmissibility and in whether adoption waits for "
       "a cue. A cue-gated whole-package mode was added in which the assembled element set "
       "moves as a unit but adoption still waits for the trigger, matching elements-only on "
       "cue-gating. Final adoption is 0.65 under elements-only, 0.89 under cue-gated "
       "whole-package, and 0.99 under whole-package. The adoption gap separates into a "
       "transmissibility component of 0.24, present even when both arms are cue-gated, and a "
       "cue-gating component of 0.10. The gap does not depend on the cue asymmetry. "
       f"From sweep {S2}."),
 ("TABLE", w7_table),
 ("P", "Coupling matrix, separating the two channels. The single coupling scalar welds a "
       "same-target reinforcement, which reproduces complex contagion, to a cross-target "
       "influence. An explicit matrix separates them. With the cross-target entry alone, "
       "adoption falls from 0.65 at no coupling to 0.51 under strong cross-target suppression "
       "and rises to 0.72 under cross-target facilitation. With the same-target entry alone, "
       "adoption is nearly flat, from 0.65 to 0.67, because same-target reinforcement raises "
       "churn under reversible adoption. The earlier result that antagonism raises adoption "
       "is a combined effect, present only when same-target reinforcement and cross-target "
       "suppression act together. The matrix and the scalar coincide when big things share no "
       "elements and differ where elements are shared, because the scalar counts a shared "
       f"element's owners as same-target only. From sweep {S2}."),
 ("TABLE", w6_table),
 ("P", "Competitive ecology and the recruitment-retention question. Two big things compete "
       "for members under mutual exclusivity, each with its own graded compression as an "
       "encapsulation lever. Sweeping one big thing's compression against a fixed rival, its "
       "captured share rises with its own compression at every rival level, from 0.40 to 0.74 "
       "against a weakly encapsulating rival and from 0.23 to 0.61 against a strongly "
       "encapsulating rival, with the best response at full compression in every case. The "
       "recruitment-retention trade-off reported by Shi, Dokshin, Genkin, and <author>, in "
       "which intermediate encapsulation is optimal, does not appear in this mapping. "
       "Compression here frees capacity and does not sever the recruitment channel, since "
       "elements continue to circulate, so retention carries no offsetting cost. Reproducing "
       "the trade-off would require an encapsulation mechanism that also throttles onward "
       f"transmission. From sweep {S2}."),
 ("TABLE", w5_table),
 ("FIG", FIG_W5),
 ("P", "Porousness and element overlap. An insular manifest-alpha cluster was placed in a "
       "population where beta's elements circulate, and the element overlap between the two "
       "big things was swept. The share of the insular cluster that acquires beta and defects "
       "rises with overlap, from 0.68 at no overlap to 0.83 at overlap 3. Leakage is "
       "substantial even at zero overlap, because elements still diffuse across the cluster "
       "boundary over the run, so reducing shared content lowers defection without sealing the "
       "boundary. This is consistent with the point that a community sharing elements with the "
       f"outside cannot fully close itself to them. From sweep {S2}."),
 ("TABLE", w4_table),
 ("P", "New specification details. Three mechanisms were added for the analyses above. "
       "whole_package_gated is a transmissibility mode in which the assembled element set "
       "transfers as a unit but manifestation still waits for the trigger, so it differs from "
       "elements-only only in transmissibility. bigthing_endowments assigns each big thing "
       "its own compression, stabilization, and enhanced-transmission settings, and "
       "compression may be set as a probability from 0 to 1 for graded encapsulation. "
       "coupling_matrix replaces the single coupling scalar with a big-thing-by-big-thing "
       "matrix whose diagonal is same-target reinforcement and whose off-diagonal is "
       "cross-target influence. Each is absent by default and a no-op when not set, verified "
       "byte-identical to the prior model."),
]

def set_borders(tbl):
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'single'); el.set(qn('w:sz'), '4')
        el.set(qn('w:space'), '0'); el.set(qn('w:color'), '000000')
        borders.append(el)
    tblPr.append(borders)

def build_para(doc, text):
    p = doc.add_paragraph(); pf = p.paragraph_format
    pf.space_before = Pt(12); pf.space_after = Pt(6)
    if ". " in text:
        lead, rest = text.split(". ", 1)
        r = p.add_run(lead + ". "); r.font.bold = True
        p.add_run(rest)
    else:
        p.add_run(text)
    return p._p

def build_heading(doc, text):
    p = doc.add_paragraph(); r = p.add_run(text); r.font.bold = True; r.font.size = Pt(14)
    p.paragraph_format.space_before = Pt(18); p.paragraph_format.space_after = Pt(6)
    return p._p

def build_table(doc, hdr, body):
    t = doc.add_table(rows=1, cols=len(hdr))
    set_borders(t)
    for j, h in enumerate(hdr):
        c = t.rows[0].cells[j]; c.paragraphs[0].add_run(h).font.bold = True
    for row in body:
        cells = t.add_row().cells
        for j, v in enumerate(row):
            cells[j].paragraphs[0].add_run(str(v))
    return t._tbl

def build_fig(doc, path, w):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Inches(w))
    return p._p

def update_transmissibility_cell(doc):
    """Append whole_package_gated to the options cell of the parameter table."""
    for tbl in doc.tables:
        for r in tbl.rows:
            for c in r.cells:
                if c.text.strip() == "elements_only / whole_package / both":
                    c.paragraphs[0].clear() if hasattr(c.paragraphs[0], "clear") else None
                    # rewrite run text
                    para = c.paragraphs[0]
                    for run in list(para.runs):
                        run.text = ""
                    para.add_run("elements_only / whole_package / both / whole_package_gated")
                    return True
    return False

def main():
    for f in (DOCX, FIG_W1, FIG_W2, FIG_W5):
        if not os.path.exists(f):
            raise SystemExit(f"missing {f}")
    bak = DOCX + ".bak6"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak); print(f"backup -> {bak}")

    doc = docx.Document(DOCX)
    sec = doc.sections[0]
    fig_w = min(5.6, (sec.page_width - sec.left_margin - sec.right_margin) / 914400.0 * 0.9)

    anchor = None
    for p in doc.paragraphs:
        if p.text.strip().startswith("Confirmation at larger populations"):
            anchor = p._p
    if anchor is None:
        raise SystemExit("anchor 'Confirmation at larger populations' not found")

    upd = update_transmissibility_cell(doc)
    print("transmissibility_mode cell updated:", upd)

    els = []
    n_tab = n_fig = n_par = 0
    for item in CONTENT:
        kind = item[0]
        if kind == "H1":
            els.append(build_heading(doc, item[1]))
        elif kind == "P":
            els.append(build_para(doc, item[1])); n_par += 1
        elif kind == "TABLE":
            hdr, body = item[1](); els.append(build_table(doc, hdr, body)); n_tab += 1
        elif kind == "FIG":
            els.append(build_fig(doc, item[1], fig_w)); n_fig += 1

    e = anchor
    for el in els:
        e.addnext(el); e = el

    doc.save(DOCX)
    print(f"folded: {n_par} paragraphs, {n_tab} tables, {n_fig} figures")

if __name__ == "__main__":
    main()
