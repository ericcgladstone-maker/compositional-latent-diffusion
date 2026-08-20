#!/usr/bin/env python3
"""Fold the endogenous-trigger robustness analysis into the docx.

Adds one section before the closing specification note: three paragraphs, three
tables and one figure. Every number in the prose and in the tables is computed
here from the result CSVs, so nothing is transcribed by hand.

The section reports a mixed result and says so: the lag of adoption behind the
substrate, the adoption gap between transmissibility modes, and the capacity
transition all survive an endogenous trigger, while the stepwise shape of the
adoption curve and the sign contrast in the final observability gap do not.

Usage:
  python fold_endogenous_docx.py            # preview, writes nothing
  python fold_endogenous_docx.py apply
"""
import csv, glob, os, shutil, sys

import docx
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))
SRC = os.environ.get("SRC_endo") or os.path.basename(
    sorted(glob.glob(os.path.join(HERE, "results", "*-endogenous")))[-1])
D = os.path.join(HERE, "results", SRC)
FIG = os.path.join(HERE, "results", "figures-200rep", "fig_endogenous_trigger.png")
ANCHOR = "New specification details"


def rows(name):
    with open(os.path.join(D, name)) as f:
        return list(csv.DictReader(f))


def f2(x):
    return f"{float(x):.2f}"


def g(x):
    return f"{float(x):g}"


def load():
    v = {}
    e1 = rows("e1_shape.csv")
    v["e1"] = {(r["trigger_type"], r["mode"]): r for r in e1}
    v["reps"] = int(e1[0]["n"])
    cap = {}
    for trig in ("exogenous", "endogenous"):
        for r in rows(f"e2_capacity_{trig}.csv"):
            cap[(trig, int(r["capacity"]))] = r
    v["cap"] = cap
    v["caps"] = sorted({k[1] for k in cap})
    v["thr"] = rows("e4_threshold.csv")
    return v


def tables(v):
    e1, cap = v["e1"], v["cap"]
    modes = ["elements_only", "whole_package_gated", "whole_package"]
    label = {"exogenous": "scheduled", "endogenous": "endogenous"}

    t1 = (["Trigger", "Transmissibility mode", "Final adoption",
           "Onset mean (sd)", "Cascade width", "Substrate at onset",
           "Observability gap"], [])
    for trig in ("exogenous", "endogenous"):
        for m in modes:
            r = e1[(trig, m)]
            t1[1].append([label[trig], m, f2(r["final"]),
                          f"{float(r['onset']):.0f} ({float(r['onset_sd']):.1f})",
                          f"{float(r['rise']):.0f}", f2(r["sub_at_onset"]),
                          f2(r["final_gap"])])

    t2 = (["Capacity", "Adoption, scheduled trigger",
           "Adoption, endogenous trigger"], [])
    for c in v["caps"]:
        t2[1].append([str(c), f2(cap[("exogenous", c)]["final"]),
                      f2(cap[("endogenous", c)]["final"])])

    t3 = (["Endogenous threshold", "Final adoption", "Onset mean (sd)",
           "Observability gap"], [])
    for r in v["thr"]:
        t3[1].append([g(r["endogenous_trigger_threshold"]), f2(r["final"]),
                      f"{float(r['onset']):.0f} ({float(r['onset_sd']):.1f})",
                      f2(r["final_gap"])])
    return t1, t2, t3


def paragraphs(v):
    e1, cap = v["e1"], v["cap"]
    eo_x, eo_n = e1[("exogenous", "elements_only")], e1[("endogenous", "elements_only")]
    wp_x, wp_n = e1[("exogenous", "whole_package")], e1[("endogenous", "whole_package")]
    thr = {g(r["endogenous_trigger_threshold"]): r for r in v["thr"]}
    lo_cap, hi_cap = v["caps"][0], v["caps"][-1]
    onset_sds = [float(e1[("endogenous", m)]["onset_sd"])
                 for m in ("elements_only", "whole_package_gated", "whole_package")]

    p1 = (
        "Triggering regime and the shape of adoption. Every result above uses a "
        "trigger that fires on a fixed schedule, so the moment at which latent "
        "adopters become manifest is set by the schedule rather than produced by "
        "the model. The engine also supports an endogenous trigger, under which an "
        "agent becomes manifest once the share of its neighbours that are latent or "
        "manifest for that big thing reaches a threshold. Running the transmissibility "
        "comparison under both regimes separates what follows from assembly from what "
        "follows from the schedule. Three results hold under both. Adoption lags the "
        "substrate through the build-up, and the population is substantially equipped "
        f"before adoption is visible, with substrate at onset {f2(eo_n['sub_at_onset'])} "
        "under endogenous triggering. The adoption gap between piecemeal and "
        f"whole-package transmission persists, at {f2(eo_n['final'])} against "
        f"{f2(wp_n['final'])}. Onset varies across replications under endogenous "
        f"triggering, with a standard deviation of {min(onset_sds):.0f} to "
        f"{max(onset_sds):.0f} ticks, and is identically the scheduled tick under the "
        "exogenous trigger, so the timing of the transition is produced by the model "
        "rather than imposed. One result does not hold. The stepwise adoption curve is "
        "a property of the schedule. Under endogenous triggering adoption follows one "
        "graded rise rather than a sequence of jumps. The inertia before adoption "
        "follows from assembly, and the abruptness of the transition follows from the "
        f"triggering regime. From sweep {SRC}, {v['reps']} replications per cell.")

    p2 = (
        "Observability gap under endogenous triggering. The sign of the final "
        "observability gap does not separate the two transmissibility modes under "
        "endogenous triggering as it does under the schedule. Under the scheduled "
        f"trigger the gap is positive for elements-only at {f2(eo_x['final_gap'])} and "
        f"negative for whole-package at {f2(wp_x['final_gap'])}. Under endogenous "
        f"triggering both are negative, at {f2(eo_n['final_gap'])} and "
        f"{f2(wp_n['final_gap'])}, so the two modes differ in magnitude rather than in "
        "sign. The sign for elements-only also depends on the threshold, moving from "
        f"{f2(thr['0.5']['final_gap'])} at a threshold of 0.5 to "
        f"{f2(thr['0.7']['final_gap'])} at 0.7. The separation between the modes "
        "survives the change of regime. The reversal of sign reported earlier is "
        "specific to the scheduled trigger.")

    # the endpoints coincide in both regimes, so the comparison that carries
    # information is the middle of the transition
    mid = [c for c in v["caps"] if 4 < c < 7] or v["caps"][1:2]
    mid_txt = " and ".join(
        f"{f2(cap[('endogenous', c)]['final'])} against "
        f"{f2(cap[('exogenous', c)]['final'])} at capacity {c}" for c in mid)
    p3 = (
        "Capacity transition under endogenous triggering. The capacity-threshold "
        "transition does not depend on the triggering regime. Adoption rises from "
        f"{f2(cap[('endogenous', lo_cap)]['final'])} at capacity {lo_cap} to "
        f"{f2(cap[('endogenous', hi_cap)]['final'])} at capacity {hi_cap} under an "
        "endogenous trigger, over the same range of capacities as under the schedule. "
        f"Through the transition adoption is higher under endogenous triggering, "
        f"{mid_txt}, because agents are converted as soon as local conditions are met "
        "rather than waiting for the next scheduled firing. The transition is a "
        "property of capacity relative to assembly requirements and not of the trigger.")
    return p1, p2, p3


def set_borders(tbl):
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        b.append(el)
    tbl._tbl.tblPr.append(b)


BANNED = ["wedge", "clean", "core", "central", "genuine", "interesting", "natural",
          "mirror images", "what we are seeing", "brain breaker", "sanity baseline"]


def governance(paras):
    """The doc's prose rules, checked before anything is written."""
    bad = []
    for i, t in enumerate(paras, 1):
        if "—" in t:
            bad.append(f"paragraph {i} contains an em dash")
        if ";" in t:
            bad.append(f"paragraph {i} contains a semicolon")
        low = t.lower()
        import re
        for b in BANNED:
            if re.search(r"\b" + re.escape(b) + r"\b", low):
                bad.append(f"paragraph {i} contains banned term {b!r}")
    return bad


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    for f in (DOCX, FIG):
        if not os.path.exists(f):
            sys.exit(f"missing {f}")
    v = load()
    t1, t2, t3 = tables(v)
    paras = paragraphs(v)

    bad = governance(paras)
    print(f"source: results/{SRC}  ({v['reps']} replications)")
    print("prose governance:", "OK" if not bad else "FAILED")
    for b in bad:
        print("   " + b)
    if bad:
        sys.exit(1)

    for i, p in enumerate(paras, 1):
        print(f"\n--- paragraph {i} ({len(p.split())} words)\n{p}")
    for name, (hdr, body) in (("shape", t1), ("capacity", t2), ("threshold", t3)):
        print(f"\n--- table {name}: {len(body)} rows x {len(hdr)} cols")
        print("   " + " | ".join(hdr))
        for r in body:
            print("   " + " | ".join(r))

    if not apply:
        print("\npreview only, nothing written.")
        return

    bak = DOCX + ".bak12"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"\nbackup -> {os.path.basename(bak)}")

    doc = docx.Document(DOCX)
    sec = doc.sections[0]
    fig_w = min(6.0, (sec.page_width - sec.left_margin - sec.right_margin)
                / 914400.0 * 0.95)
    anchor = None
    for p in doc.paragraphs:
        if p.text.strip().startswith(ANCHOR):
            anchor = p._p
            break
    if anchor is None:
        sys.exit(f"anchor {ANCHOR!r} not found")

    def make_para(text):
        pp = doc.add_paragraph()
        pf = pp.paragraph_format
        pf.space_before = Pt(12)
        pf.space_after = Pt(6)
        lead, rest = text.split(". ", 1)
        pp.add_run(lead + ". ").font.bold = True
        pp.add_run(rest)
        return pp._p

    def make_table(spec):
        hdr, body = spec
        t = doc.add_table(rows=1, cols=len(hdr))
        set_borders(t)
        for j, h in enumerate(hdr):
            t.rows[0].cells[j].paragraphs[0].add_run(h).font.bold = True
        for row in body:
            c = t.add_row().cells
            for j, val in enumerate(row):
                c[j].paragraphs[0].add_run(val)
        return t._tbl

    def make_figure():
        fp = doc.add_paragraph()
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fp.add_run().add_picture(FIG, width=Inches(fig_w))
        return fp._p

    # each claim followed by the evidence for it, matching the rest of the document
    made = [
        make_para(paras[0]),   # shape of adoption under each regime
        make_table(t1),
        make_figure(),
        make_para(paras[1]),   # observability gap
        make_table(t3),        # threshold sensitivity backs that paragraph
        make_para(paras[2]),   # capacity transition
        make_table(t2),
    ]

    for el in made:
        anchor.addprevious(el)
    doc.save(DOCX)
    print(f"\nfolded: 3 paragraphs, 3 tables, 1 figure, before {ANCHOR!r}")


if __name__ == "__main__":
    main()
