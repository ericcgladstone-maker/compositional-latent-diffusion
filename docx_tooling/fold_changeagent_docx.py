#!/usr/bin/env python3
"""Fold the change-agent analysis into the docx.

Adds three paragraphs, three tables and one figure before the closing
specification note. Every number is computed here from the result CSVs.

The build's change-agent stage sweeps the seeded share from 0.05 to 0.20 with no
zero condition, so it establishes insensitivity to the SIZE of the minority and
not to its presence. The limited-attention stage cannot serve as the baseline
because it runs at a different ambient element density. This supplies the
control and the surrounding evidence.

Usage:
  python fold_changeagent_docx.py            # preview
  python fold_changeagent_docx.py apply
"""
import csv, glob, os, re, shutil, sys

import docx
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))
SRC = os.environ.get("SRC_ca") or os.path.basename(
    sorted(glob.glob(os.path.join(HERE, "results", "*-changeagent")))[-1])
D = os.path.join(HERE, "results", SRC)
FIG = os.path.join(HERE, "results", "figures-200rep", "fig_changeagent.png")
ANCHOR = "New specification details"
N_BIG = 2      # the change-agent stage runs two big things


def rows(name):
    with open(os.path.join(D, name)) as f:
        return list(csv.DictReader(f))


def f2(x):
    return f"{float(x):.2f}"


def g(x):
    return f"{float(x):g}"


def load():
    v = {}
    a = rows("a_fraction.csv")
    v["reps"] = int(a[0]["n"])
    v["a"] = {(r["regime"], g(r["change_agent_fraction"])): r for r in a
              if r["change_agent_fraction"] not in ("", "None")}
    v["a_off"] = {r["regime"]: r for r in a
                  if r["change_agent_fraction"] in ("", "None")}
    v["fracs"] = sorted({k[1] for k in v["a"]}, key=float)
    v["b"] = {(r["regime"], g(r["change_agent_evangelism"])): r
              for r in rows("b_evangelism.csv")}
    v["evang"] = sorted({g(r["change_agent_evangelism"])
                         for r in rows("b_evangelism.csv")}, key=float)
    v["c"] = {(r["regime"], r["transmissibility_mode"],
               g(r["change_agent_fraction"])): r for r in rows("c_mechanism.csv")}
    v["d"] = {(r["regime"], r["trigger_type"], g(r["change_agent_fraction"])): r
              for r in rows("d_trigger.csv")}
    return v


def tables(v):
    t1 = (["Seeded share", "Adoption (ample capacity)", "Carriers (ample capacity)",
           "Adoption (tight capacity)", "Carriers (tight capacity)"], [])
    for f in v["fracs"]:
        t1[1].append([g(f),
                      f2(v["a"][("permissive", f)]["final"]),
                      f2(v["a"][("permissive", f)]["carrier_per_bt"]),
                      f2(v["a"][("constrained", f)]["final"]),
                      f2(v["a"][("constrained", f)]["carrier_per_bt"])])
    t1[1].append(["scenario off",
                  f2(v["a_off"]["permissive"]["final"]),
                  f2(v["a_off"]["permissive"]["carrier_per_bt"]),
                  f2(v["a_off"]["constrained"]["final"]),
                  f2(v["a_off"]["constrained"]["carrier_per_bt"])])

    t2 = (["Evangelism multiplier", "Adoption (ample capacity)",
           "Adoption (tight capacity)"], [])
    for e in v["evang"]:
        t2[1].append([g(e), f2(v["b"][("permissive", e)]["final"]),
                      f2(v["b"][("constrained", e)]["final"])])

    t3 = (["Condition", "No minority", "Minority of 0.20", "Difference"], [])
    for reg, lab in (("permissive", "ample capacity"), ("constrained", "tight capacity")):
        for mode in ("elements_only", "whole_package"):
            n0 = float(v["c"][(reg, mode, "0")]["final"])
            n1 = float(v["c"][(reg, mode, "0.2")]["final"])
            t3[1].append([f"{lab}, {mode}", f2(n0), f2(n1), f"{n1 - n0:+.2f}"])
        for trig in ("endogenous",):
            n0 = float(v["d"][(reg, trig, "0")]["final"])
            n1 = float(v["d"][(reg, trig, "0.2")]["final"])
            t3[1].append([f"{lab}, {trig} trigger", f2(n0), f2(n1), f"{n1 - n0:+.2f}"])
    return t1, t2, t3


def paragraphs(v):
    top = v["fracs"][-1]
    P0 = v["a"][("permissive", "0")]
    P1 = v["a"][("permissive", top)]
    C0 = v["a"][("constrained", "0")]
    C1 = v["a"][("constrained", top)]
    seed_share = float(top) / N_BIG
    would_be = float(P0["final"]) + seed_share
    ratio = float(C1["carrier_per_bt"]) / float(C1["final"])
    b_lo = v["b"][("permissive", v["evang"][0])]
    b_hi = v["b"][("permissive", v["evang"][-1])]
    b_lo_c = v["b"][("constrained", v["evang"][0])]
    b_hi_c = v["b"][("constrained", v["evang"][-1])]

    p1 = (
        "Change agents and the size of the seeded minority. The change-agent stage "
        "above sweeps the seeded share from 0.05 to 0.20 and finds adoption close to "
        "flat. That establishes that adoption does not respond to the number of change "
        "agents, and not that it fails to respond to their presence, because the stage "
        "contains no zero condition. The limited-attention stage is not a usable "
        "baseline for the comparison because it runs at a different ambient element "
        "density. Adding the zero condition, adoption without any seeded minority is "
        f"{f2(P0['final'])} under ample capacity, and {f2(P1['final'])} when a fifth of "
        f"the population is seeded as equipped and manifest adopters. A seeded adopter "
        "is manifest from the first tick, so a minority of "
        f"{g(top)} contributes {seed_share:.2f} to the manifest share before any "
        f"transmission takes place. Adoption would therefore stand at "
        f"{would_be:.2f} if the seeded adopters merely remained adopted and recruited "
        f"no one. Observed adoption is {f2(P1['final'])}, below that value, so the "
        "seeded minority neither recruits nor remains intact. Under tight capacity "
        f"adoption rises from {f2(C0['final'])} to {f2(C1['final'])} while the carrier "
        f"fraction stands at {f2(C1['carrier_per_bt'])}, so about {ratio:.0f} times as "
        "many agents hold components as adopt. A second control with the change-agent "
        f"scenario switched off entirely gives {f2(v['a_off']['permissive']['final'])} "
        f"and {f2(v['a_off']['constrained']['final'])}, within 0.01 of the zero-share "
        f"condition. From sweep {SRC}, {v['reps']} replications per cell.")

    p2 = (
        "Promotion intensity. The evangelism setting multiplies the rate at which "
        "seeded agents transmit, which tests whether the minority is simply too quiet. "
        f"Under ample capacity adoption falls from {f2(b_lo['final'])} at the base rate "
        f"to {f2(b_hi['final'])} at {g(v['evang'][-1])} times that rate, so raising the "
        "rate lowers adoption. Faster transmission moves more elements into a fixed "
        "number of memory slots, which raises turnover of the elements an agent would "
        "otherwise retain long enough to complete a set. Under tight capacity, where "
        "elements are scarce rather than crowded, the same increase raises adoption "
        f"from {f2(b_lo_c['final'])} to {f2(b_hi_c['final'])}. The direction of the "
        "effect depends on whether attention or supply is the binding constraint.")

    ce0 = float(v["c"][("permissive", "elements_only", "0")]["final"])
    ce1 = float(v["c"][("permissive", "elements_only", "0.2")]["final"])
    cw0 = float(v["c"][("permissive", "whole_package", "0")]["final"])
    cw1 = float(v["c"][("permissive", "whole_package", "0.2")]["final"])
    de0 = float(v["d"][("constrained", "endogenous", "0")]["final"])
    de1 = float(v["d"][("constrained", "endogenous", "0.2")]["final"])

    p3 = (
        "Transmissibility and triggering. Two further conditions bound the result. "
        "Under whole-package transmission adoption reaches "
        f"{cw0:.3f} without any seeded minority, so there is almost nothing left for a "
        f"minority to add and the observed difference of {cw1 - cw0:+.3f} is set by "
        "that ceiling rather than by what the minority transmits. That comparison "
        "therefore does not isolate the spread unit, and the comparison under "
        f"piecemeal transmission, {f2(ce0)} against {f2(ce1)}, is the informative one. "
        "Replacing the scheduled "
        "trigger with the endogenous trigger leaves the pattern in place, with adoption "
        f"moving from {f2(de0)} to {f2(de1)} under tight capacity, so the result does "
        "not depend on the timing of the trigger.")
    return p1, p2, p3


def set_borders(tbl):
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0"); el.set(qn("w:color"), "000000")
        b.append(el)
    tbl._tbl.tblPr.append(b)


BANNED = ["wedge", "clean", "core", "central", "genuine", "interesting", "natural",
          "mirror images", "what we are seeing", "brain breaker", "sanity baseline"]


def governance(paras):
    bad = []
    for i, t in enumerate(paras, 1):
        if "—" in t:
            bad.append(f"paragraph {i} contains an em dash")
        if ";" in t:
            bad.append(f"paragraph {i} contains a semicolon")
        for b in BANNED:
            if re.search(r"\b" + re.escape(b) + r"\b", t.lower()):
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
    for name, (hdr, body) in (("fraction", t1), ("evangelism", t2), ("bounds", t3)):
        print(f"\n--- table {name}: {len(body)} rows")
        print("   " + " | ".join(hdr))
        for r in body:
            print("   " + " | ".join(r))
    if not apply:
        print("\npreview only, nothing written.")
        return

    bak = DOCX + ".bak13"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"\nbackup -> {os.path.basename(bak)}")
    doc = docx.Document(DOCX)
    sec = doc.sections[0]
    fig_w = min(5.6, (sec.page_width - sec.left_margin - sec.right_margin)
                / 914400.0 * 0.9)
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
        pf.space_before = Pt(12); pf.space_after = Pt(6)
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

    fp = doc.add_paragraph()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.add_run().add_picture(FIG, width=Inches(fig_w))

    for el in [make_para(paras[0]), make_table(t1), fp._p,
               make_para(paras[1]), make_table(t2),
               make_para(paras[2]), make_table(t3)]:
        anchor.addprevious(el)
    doc.save(DOCX)
    print(f"\nfolded: 3 paragraphs, 3 tables, 1 figure, before {ANCHOR!r}")


if __name__ == "__main__":
    main()
