#!/usr/bin/env python3
"""Fold the identification results into the docx, including two corrections.

Three things go in:

  1. Rate-matched transmissibility. The cue-gated comparison held the trigger
     constant but not the amount of material moved. Added as a new subsection
     with a dose-response table and figure.
  2. Tie strength. This CORRECTS an existing paragraph. The reported increase is
     a transmission-rate effect, and the structural reading the document gives
     it is withdrawn.
  3. Change-agent robustness across population size and topology.

Every number is computed from the result CSVs.

  python fold_identification_docx.py            # preview
  python fold_identification_docx.py apply
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
RESULTS = os.path.join(HERE, "results")
FIGDIR = os.path.join(RESULTS, "figures-200rep")
ANCHOR = "New specification details"


def newest(pat):
    return os.path.basename(sorted(glob.glob(os.path.join(RESULTS, pat)))[-1])


SRC_RM = os.environ.get("SRC_rm") or newest("*-rate-matched")
SRC_TS = os.environ.get("SRC_ts") or newest("*-tiestrength-matched")
SRC_RB = os.environ.get("SRC_rb") or newest("*-changeagent-robust")


def rows(d, n):
    with open(os.path.join(RESULTS, d, n)) as f:
        return list(csv.DictReader(f))


def f2(x):
    return f"{float(x):.2f}"


def g(x):
    return f"{float(x):g}"


def interp(curve, x):
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


# ---------------------------------------------------------------- rate matched
def rate_matched():
    rs = rows(SRC_RM, "rate_matched.csv")
    pm = sorted((float(r["elements_per_agent"]), float(r["final"]))
                for r in rs if r["mode"] == "elements_only")
    gt = sorted((float(r["elements_per_agent"]), float(r["final"]))
                for r in rs if r["mode"] == "whole_package_gated")
    orig = [r for r in gt if abs(r[0] - max(x for x, _ in gt)) < 1e-9][0]
    overlap = [(x, y, interp(pm, x)) for x, y in gt if interp(pm, x) is not None]
    reps = int(rs[0]["n"])
    hdr = ["Delivery", "Elements moved per agent", "Final adoption"]
    body = ([["piecemeal", f"{x:.2f}", f2(y)] for x, y in pm] +
            [["bundled, cue-matched", f"{x:.2f}", f2(y)] for x, y in gt])
    return dict(pm=pm, gt=gt, orig=orig, overlap=overlap, reps=reps,
                table=(hdr, body))


def rate_matched_para(v):
    pm, gt, overlap = v["pm"], v["gt"], v["overlap"]
    lo, hi = overlap[0], overlap[-1]
    ratio = v["orig"][0] / [y for x, y in [(a, b) for a, b in
                            [(r[0], r[0]) for r in [pm[2]]]]][0] if False else \
        v["orig"][0] / pm[2][0]
    pm_slope = (pm[-1][1] - pm[0][1]) / (pm[-1][0] - pm[0][0])
    gt_slope = (gt[-1][1] - gt[0][1]) / (gt[-1][0] - gt[0][0])
    return (
        "Transmissibility and the amount transmitted. The cue-matched comparison "
        "above holds the trigger constant across the two arms but not the amount of "
        "material each moves. A piecemeal contact carries at most one element and "
        "only with the transmission probability, while a whole-package contact "
        "carries every required element and was subject to no probability at all. "
        f"Measured as elements acquired per agent over a run, the package arm moved "
        f"{ratio:.2f} times as much material as the piecemeal arm at the operating "
        "point. Gating the package transfer and sweeping the rate of both arms gives "
        "a response curve for each, which can then be compared at equal measured "
        "material rather than at equal parameter settings. The difference narrows and "
        f"does not close. At matched material the bundled arm exceeds the piecemeal "
        f"arm by {hi[1] - hi[2]:.2f} at {hi[0]:.1f} elements per agent and by "
        f"{lo[1] - lo[2]:.2f} at {lo[0]:.1f}. The two arms also respond to additional "
        "material in opposite directions. Adoption under piecemeal delivery falls from "
        f"{f2(pm[0][1])} to {f2(pm[-1][1])} as material moved rises from {pm[0][0]:.1f} "
        f"to {pm[-1][0]:.1f} per agent, a slope of {pm_slope:+.3f} per element, while "
        f"adoption under bundled delivery rises from {f2(gt[0][1])} to {f2(gt[-1][1])} "
        f"over a wider range, a slope of {gt_slope:+.3f}. The reported difference of "
        f"{f2(pm[2][1])} against {f2(v['orig'][1])} therefore overstates the effect of "
        "transmissibility alone. A smaller difference remains once the amount "
        "transmitted is held constant, and the sign of the return to further "
        f"transmission depends on whether it arrives assembled. From sweep {SRC_RM}, "
        f"{v['reps']} replications per cell.")


# ---------------------------------------------------------------- tie strength
def tie_strength():
    rs = rows(SRC_TS, "tiestrength_matched.csv")
    asis = sorted((float(r["strong_tie_fraction"]), float(r["final"]),
                   float(r["elements_per_agent"])) for r in rs if r["arm"] == "as-is")
    norm = sorted((float(r["strong_tie_fraction"]), float(r["final"]),
                   float(r["elements_per_agent"])) for r in rs if r["arm"] == "normalised")
    hdr = ["Strong-tie fraction", "Adoption, as run", "Material moved, as run",
           "Adoption, rate held constant", "Material moved, held constant"]
    body = [[g(a[0]), f2(a[1]), f"{a[2]:.2f}", f2(n[1]), f"{n[2]:.2f}"]
            for a, n in zip(asis, norm)]
    return dict(asis=asis, norm=norm, reps=int(rs[0]["n"]), table=(hdr, body))


def tie_strength_correction(v):
    a, n = v["asis"], v["norm"]
    mult = (0.1 + 0.9 * a[-1][0]) / (0.1 + 0.9 * a[0][0])
    old = ("Strong ties concentrate repeated contact between the same agents, which "
           "supports assembly of the required element set.")
    new = (
        "That increase is a transmission-rate effect. A strong tie carries a weight of "
        "1.0 and a weak tie 0.1, and the weight multiplies the send probability, so "
        f"mean transmission probability rises by a factor of {mult:.1f} across the "
        "sweep while the tie structure changes. Holding mean transmission probability "
        "constant by rescaling it against the strong-tie fraction, adoption is "
        f"{f2(n[0][1])} at no strong ties and {f2(n[-1][1])} at three in ten, a "
        f"difference of {n[-1][1] - n[0][1]:+.3f}, with material moved held within "
        f"{100 * (max(x[2] for x in n) / min(x[2] for x in n) - 1):.0f} percent across "
        "the sweep. The increase reported above follows from the higher transmission "
        "rate that strong ties carry and not from the arrangement of ties, so no "
        "conclusion about repeated contact supporting assembly is drawn from it. "
        f"From sweep {SRC_TS}, {v['reps']} replications per cell.")
    return old, new


# ------------------------------------------------------------------ robustness
def robustness():
    rs = []
    for f in sorted(glob.glob(os.path.join(RESULTS, SRC_RB, "robust_*.csv"))):
        if not f.endswith("_raw.csv"):
            rs += list(csv.DictReader(open(f)))
    by = {(r["topology"], g(r["n_agents"]), r["regime"], g(r["change_agent_fraction"])): r
          for r in rs}
    TL = {"small_world": "small world", "random": "random", "ring_lattice": "ring lattice"}
    RL = {"permissive": "ample", "constrained": "tight"}
    out = []
    for topo in TL:
        for N in ("100", "500"):
            for reg in RL:
                b, m = by[(topo, N, reg, "0")], by[(topo, N, reg, "0.2")]
                nbt = int(m["n_big_things"])
                base, obs = float(b["final"]), float(m["final"])
                exp = base + 0.20 / nbt
                out.append(dict(topo=TL[topo], N=N, reg=RL[reg], base=base, obs=obs,
                                exp=exp, short=obs - exp,
                                carr=float(m["carrier_per_bt"])))
    hdr = ["Topology", "Agents", "Capacity", "No minority", "Minority of 0.20",
           "If seed merely persisted", "Shortfall", "Carriers"]
    body = [[r["topo"], r["N"], r["reg"], f2(r["base"]), f2(r["obs"]), f2(r["exp"]),
             f"{r['short']:+.2f}", f2(r["carr"])] for r in out]
    return dict(rows=out, reps=int(rs[0]["n"]), table=(hdr, body))


def robustness_para(v):
    rs = v["rows"]
    neg = [r for r in rs if r["short"] < 0]
    pos = [r for r in rs if r["short"] >= 0]
    worst = min(rs, key=lambda r: r["short"])
    return (
        "Change agents across population size and topology. The change-agent analysis "
        "above uses one hundred agents on a small-world graph, and the confirmation at "
        "larger populations reported earlier covers the transmissibility modes rather "
        "than the change-agent scenario. Repeating the comparison across three "
        "topologies and two population sizes leaves the result in place. Observed "
        "adoption falls below the level the seeded minority would produce by persisting "
        f"alone in {len(neg)} of the {len(rs)} conditions, reaching "
        f"{abs(worst['short']):.2f} below it at most. " +
        ("The exception is " + ", ".join(f"{r['topo']} at {r['N']} agents under "
                                         f"{r['reg']} capacity" for r in pos) +
         f", where the shortfall is {pos[0]['short']:+.2f} and the seeded minority "
         "approximately holds its ground. " if pos else "") +
        "The carrier fraction remains well above adoption under tight capacity in every "
        f"condition. From sweep {SRC_RB}, {v['reps']} replications per cell.")


# ----------------------------------------------------------------------- write
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


def governance(texts):
    bad = []
    for i, t in enumerate(texts, 1):
        if "—" in t:
            bad.append(f"text {i}: em dash")
        if ";" in t:
            bad.append(f"text {i}: semicolon")
        for b in BANNED:
            if re.search(r"\b" + re.escape(b) + r"\b", t.lower()):
                bad.append(f"text {i}: banned term {b!r}")
    return bad


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    fig = os.path.join(FIGDIR, "fig_rate_matched.png")
    if not os.path.exists(fig):
        sys.exit(f"missing {fig}")

    rm, ts, rb = rate_matched(), tie_strength(), robustness()
    p_rm = rate_matched_para(rm)
    old_ts, new_ts = tie_strength_correction(ts)
    p_rb = robustness_para(rb)

    bad = governance([p_rm, new_ts, p_rb])
    print(f"sources: {SRC_RM} | {SRC_TS} | {SRC_RB}")
    print("prose governance:", "OK" if not bad else "FAILED")
    for b in bad:
        print("   " + b)
    if bad:
        sys.exit(1)

    for name, txt in (("rate-matched", p_rm), ("tie-strength CORRECTION", new_ts),
                      ("robustness", p_rb)):
        print(f"\n--- {name} ({len(txt.split())} words)\n{txt}")
    for name, spec in (("rate-matched", rm["table"]), ("tie-strength", ts["table"]),
                       ("robustness", rb["table"])):
        h, b = spec
        print(f"\n--- table {name}: {len(b)} rows\n   " + " | ".join(h))
        for r in b:
            print("   " + " | ".join(r))

    if not apply:
        print("\npreview only, nothing written.")
        return

    bak = DOCX + ".bak16"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"\nbackup -> {os.path.basename(bak)}")
    doc = docx.Document(DOCX)

    # --- the correction, applied in place -------------------------------
    hits = [p for p in doc.paragraphs if old_ts in p.text]
    if len(hits) != 1:
        sys.exit(f"tie-strength sentence matched {len(hits)} paragraphs, expected 1")
    p = hits[0]
    runs = [r for r in p.runs if r.text]
    bold = [r for r in runs if r.bold]
    lead = "".join(r.text for r in bold)
    full = "".join(r.text for r in runs)
    body = full[len(lead):].replace(old_ts, new_ts)
    for t in p._p.iter(qn("w:t")):
        t.text = ""
    norm = [r for r in runs if not r.bold]
    if lead and bold:
        bold[0].text = lead
        (norm[0] if norm else p.add_run("")).text = body
    else:
        runs[0].text = lead + body
    print("corrected the tie-strength interpretation in place")

    # --- new material before the closing spec note ----------------------
    sec = doc.sections[0]
    fw = min(5.6, (sec.page_width - sec.left_margin - sec.right_margin) / 914400.0 * 0.9)
    anchor = None
    for q in doc.paragraphs:
        if q.text.strip().startswith(ANCHOR):
            anchor = q._p
            break
    if anchor is None:
        sys.exit("anchor not found")

    def mk_para(text):
        pp = doc.add_paragraph()
        pf = pp.paragraph_format
        pf.space_before = Pt(12); pf.space_after = Pt(6)
        a, b = text.split(". ", 1)
        pp.add_run(a + ". ").font.bold = True
        pp.add_run(b)
        return pp._p

    def mk_table(spec):
        h, b = spec
        t = doc.add_table(rows=1, cols=len(h))
        set_borders(t)
        for j, x in enumerate(h):
            t.rows[0].cells[j].paragraphs[0].add_run(x).font.bold = True
        for row in b:
            c = t.add_row().cells
            for j, x in enumerate(row):
                c[j].paragraphs[0].add_run(x)
        return t._tbl

    fp = doc.add_paragraph()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.add_run().add_picture(fig, width=Inches(fw))

    for el in [mk_para(p_rm), mk_table(rm["table"]), fp._p,
               mk_table(ts["table"]),
               mk_para(p_rb), mk_table(rb["table"])]:
        anchor.addprevious(el)
    doc.save(DOCX)
    print("folded: 2 paragraphs, 3 tables, 1 figure, plus 1 in-place correction")


if __name__ == "__main__":
    main()
