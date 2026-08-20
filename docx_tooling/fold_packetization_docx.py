#!/usr/bin/env python3
"""Fold the fixed-content packetization experiment into the docx.

This is a negative result and is written as one. The controlled test does not
support the reading that joint arrival of complementary material is what
produces the difference between piecemeal and bundled delivery.

Every number is computed from the result CSVs, including the paired contrasts.

  python fold_packetization_docx.py            # preview
  python fold_packetization_docx.py apply
"""
import csv, glob, math, os, re, shutil
import statistics as st
import sys

import docx
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))
RESULTS = os.path.join(HERE, "results")
SRC = os.environ.get("SRC_pk") or os.path.basename(
    sorted(glob.glob(os.path.join(RESULTS, "*-packetization")))[-1])
D = os.path.join(RESULTS, SRC)
ANCHOR = "New specification details"


def f2(x):
    return f"{float(x):.2f}"


def load():
    agg = list(csv.DictReader(open(os.path.join(D, "packetization.csv"))))
    raw = list(csv.DictReader(open(os.path.join(D, "packetization_raw.csv"))))
    by = {}
    for r in raw:
        cap, arm, flow = r["cell"].split("/")
        by.setdefault((cap, arm, flow), {})[int(r["rep"])] = float(r["final"])

    def paired(a, b):
        d = [a[k] - b[k] for k in sorted(a) if k in b]
        m = st.mean(d)
        se = st.pstdev(d) / math.sqrt(len(d))
        return m, se

    con = {}
    for cap in ("c6", "c5"):
        for flow in ("low", "high"):
            con[(cap, "bundling", flow)] = paired(by[(cap, "bundled", flow)],
                                                  by[(cap, "piecemeal", flow)])
        for arm in ("piecemeal", "bundled"):
            con[(cap, "flow", arm)] = paired(by[(cap, arm, "high")],
                                             by[(cap, arm, "low")])
        db = {k: by[(cap, "bundled", "high")][k] - by[(cap, "bundled", "low")][k]
              for k in by[(cap, "bundled", "high")]}
        dp = {k: by[(cap, "piecemeal", "high")][k] - by[(cap, "piecemeal", "low")][k]
              for k in by[(cap, "piecemeal", "high")]}
        con[(cap, "interaction", "")] = paired(db, dp)
    return agg, con, int(agg[0]["n"])


def tables(agg, con):
    t1 = (["Capacity", "Delivery", "Flow", "Adoption mean (sd)",
           "Focal offered per agent", "Focal acquired per agent",
           "Total acquired per agent", "Required-element evictions per agent"], [])
    for r in agg:
        t1[1].append([r["capacity"], r["arm"], r["flow"],
                      f"{float(r['final']):.2f} ({float(r['final_sd']):.2f})",
                      f2(r["focal_offered_per_agent"]), f2(r["focal_acquired_per_agent"]),
                      f2(r["total_acquired_per_agent"]),
                      f2(r["required_evictions_per_agent"])])
    t2 = (["Capacity", "Contrast", "Paired difference", "Standard error"], [])
    LAB = {("bundling", "low"): "bundling effect, low flow",
           ("bundling", "high"): "bundling effect, high flow",
           ("flow", "piecemeal"): "return to flow, piecemeal",
           ("flow", "bundled"): "return to flow, bundled",
           ("interaction", ""): "delivery by flow interaction"}
    for cap in ("6", "5"):
        for key, lab in LAB.items():
            m, se = con[(f"c{cap}", key[0], key[1])]
            t2[1].append([cap, lab, f"{m:+.3f}", f"{se:.3f}"])
    return t1, t2


def paragraph(agg, con, reps):
    b6l, s6l = con[("c6", "bundling", "low")]
    b6h, s6h = con[("c6", "bundling", "high")]
    b5l, s5l = con[("c5", "bundling", "low")]
    b5h, s5h = con[("c5", "bundling", "high")]
    i6, si6 = con[("c6", "interaction", "")]
    i5, si5 = con[("c5", "interaction", "")]
    fp5, _ = con[("c5", "flow", "piecemeal")]
    fb5, _ = con[("c5", "flow", "bundled")]
    a = {(r["capacity"], r["arm"], r["flow"]): r for r in agg}
    acq_p = float(a[("5", "piecemeal", "low")]["focal_acquired_per_agent"])
    acq_b = float(a[("5", "bundled", "low")]["focal_acquired_per_agent"])
    return (
        "Joint versus separate arrival of the same material. The comparison of "
        "response curves above compares two systems whose material flow is produced "
        "by the diffusion process rather than assigned, so it cannot separate joint "
        "arrival from the amount delivered. This assigns the content directly. A "
        "block is one recipient, four delivery opportunities and exactly one instance "
        "of each of the four required elements. Under separate arrival the four "
        "elements are permuted and one is delivered at each opportunity. Under joint "
        "arrival one of those same four opportunities is chosen and all four are "
        "delivered there. Paired runs use the same network, the same seed and the "
        "same schedule, so recipient, opportunity count and timing, total content and "
        "background traffic are held fixed and only the grouping of arrivals differs. "
        "Delivery uses the ordinary admission path, so capacity and eviction act on "
        "the material in both conditions. The run has a fixed horizon of 300 ticks "
        "rather than stopping at quiescence, because the two conditions otherwise "
        "stop at different ticks and the content offered stops being matched. "
        "Capacity 6 is the operating point used elsewhere, and capacity 5 is reported "
        "alongside it because under a fixed horizon adoption at capacity 6 sits near "
        "its ceiling. The result does not support the reading that joint arrival is "
        f"what matters. At capacity 6 the difference is {b6l:+.3f} at low flow and "
        f"{b6h:+.3f} at high flow, against standard errors of {s6l:.3f} and "
        f"{s6h:.3f}. At capacity 5 it is {b5l:+.3f} at low flow and {b5h:+.3f} at "
        "high flow, so it changes sign between flow levels and is smaller than 0.01 "
        f"in both. The interaction between delivery and flow is {i6:+.3f} at capacity "
        f"6 and {i5:+.3f} at capacity 5, the second of which runs opposite to the "
        "direction the assembly reading predicts. Joint arrival also delivered more "
        f"material, {acq_b:.2f} required elements acquired per agent against "
        f"{acq_p:.2f} under separate arrival, and still produced no advantage. "
        "Increasing assigned flow lowers adoption under both forms of delivery, by "
        f"{fp5:+.3f} under separate arrival and {fb5:+.3f} under joint arrival at "
        "capacity 5, which is consistent with material displacing partially assembled "
        "sets rather than with any property of grouping. The difference between "
        "piecemeal and bundled systems reported above therefore stands as a property "
        "of those systems and is not explained by the joint arrival of complementary "
        f"material. From sweep {SRC}, {reps} paired replications per cell.")


def set_borders(tbl):
    b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{e}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0"); el.set(qn("w:color"), "000000")
        b.append(el)
    tbl._tbl.tblPr.append(b)


BANNED = ["wedge", "clean", "core", "central", "genuine", "interesting", "natural",
          "mirror images", "what we are seeing", "brain breaker", "sanity baseline"]


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    agg, con, reps = load()
    t1, t2 = tables(agg, con)
    para = paragraph(agg, con, reps)
    bad = []
    if "—" in para:
        bad.append("em dash")
    if ";" in para:
        bad.append("semicolon")
    for b in BANNED:
        if re.search(r"\b" + re.escape(b) + r"\b", para.lower()):
            bad.append(f"banned term {b!r}")
    print(f"source: results/{SRC} ({reps} paired replications)")
    print("prose governance:", "OK" if not bad else "FAILED " + ", ".join(bad))
    if bad:
        sys.exit(1)
    print(f"\n{para}\n")
    for nm, (h, b) in (("cells", t1), ("contrasts", t2)):
        print(f"--- table {nm}: {len(b)} rows\n   " + " | ".join(h))
        for r in b:
            print("   " + " | ".join(r))
        print()
    if not apply:
        print("preview only, nothing written.")
        return
    bak = DOCX + ".bak17"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"backup -> {os.path.basename(bak)}")
    doc = docx.Document(DOCX)
    anchor = None
    for p in doc.paragraphs:
        if p.text.strip().startswith(ANCHOR):
            anchor = p._p
            break
    if anchor is None:
        sys.exit("anchor not found")
    pp = doc.add_paragraph()
    pf = pp.paragraph_format
    pf.space_before = Pt(12); pf.space_after = Pt(6)
    lead, rest = para.split(". ", 1)
    pp.add_run(lead + ". ").font.bold = True
    pp.add_run(rest)
    els = [pp._p]
    for spec in (t1, t2):
        h, b = spec
        t = doc.add_table(rows=1, cols=len(h))
        set_borders(t)
        for j, x in enumerate(h):
            t.rows[0].cells[j].paragraphs[0].add_run(x).font.bold = True
        for row in b:
            c = t.add_row().cells
            for j, x in enumerate(row):
                c[j].paragraphs[0].add_run(x)
        els.append(t._tbl)
    for el in els:
        anchor.addprevious(el)
    doc.save(DOCX)
    print("folded: 1 paragraph, 2 tables")


if __name__ == "__main__":
    main()
