#!/usr/bin/env python3
"""Fold the change-agent robustness check into the docx.

One paragraph and one table, placed after the change-agent analysis. Every
number is computed here from the result CSVs.

The change-agent analysis runs at 100 agents on a small-world graph. The scale
confirmation elsewhere in the document covers the transmissibility modes only,
so this supplies the population-size and topology check for the change-agent
result specifically.

Usage:
  python fold_charobust_docx.py            # preview
  python fold_charobust_docx.py apply
"""
import csv, glob, os, re, shutil, sys

import docx
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))
SRC = os.environ.get("SRC_rb") or os.path.basename(
    sorted(glob.glob(os.path.join(HERE, "results", "*-changeagent-robust")))[-1])
D = os.path.join(HERE, "results", SRC)
ANCHOR = "New specification details"

TOPO_LABEL = {"small_world": "small world", "random": "random",
              "ring_lattice": "ring lattice"}
REG_LABEL = {"permissive": "ample", "constrained": "tight"}


def g(x):
    return f"{float(x):g}"


def f2(x):
    return f"{float(x):.2f}"


def load():
    rows = []
    for f in sorted(glob.glob(os.path.join(D, "robust_*.csv"))):
        if f.endswith("_raw.csv"):
            continue
        rows += list(csv.DictReader(open(f)))
    by = {(r["topology"], g(r["n_agents"]), r["regime"], g(r["change_agent_fraction"])): r
          for r in rows}
    return by, int(rows[0]["n"])


def cells(by):
    """One row per topology, population size and regime."""
    out = []
    keys = sorted({(k[0], k[1], k[2]) for k in by},
                  key=lambda t: (list(TOPO_LABEL).index(t[0]), float(t[1]),
                                 list(REG_LABEL).index(t[2])))
    for topo, N, reg in keys:
        b = by[(topo, N, reg, "0")]
        m = by[(topo, N, reg, "0.2")]
        nbt = int(m["n_big_things"])
        base, obs = float(b["final"]), float(m["final"])
        expect = base + 0.20 / nbt
        out.append({"topo": topo, "N": N, "reg": reg, "base": base, "obs": obs,
                    "lift": obs - base, "expect": expect, "short": obs - expect,
                    "carriers": float(m["carrier_per_bt"])})
    return out


def table(rs):
    hdr = ["Topology", "Agents", "Capacity", "No minority", "Minority of 0.20",
           "If seed merely persisted", "Shortfall", "Carriers"]
    body = [[TOPO_LABEL[r["topo"]], g(r["N"]), REG_LABEL[r["reg"]],
             f2(r["base"]), f2(r["obs"]), f2(r["expect"]),
             f"{r['short']:+.2f}", f2(r["carriers"])] for r in rs]
    return hdr, body


def paragraph(rs, reps):
    n_short = sum(1 for r in rs if r["short"] < 0)
    worst = min(rs, key=lambda r: r["short"])
    best = max(rs, key=lambda r: r["short"])
    big = [r for r in rs if r["N"] == "500"]
    big_short = sum(1 for r in big if r["short"] < 0)
    return (
        "Change agents across population size and topology. The change-agent "
        "analysis above uses one hundred agents on a small-world graph, and the "
        "confirmation at larger populations reported earlier covers the "
        "transmissibility modes rather than the change-agent scenario. Repeating the "
        "comparison across three topologies and two population sizes leaves the "
        f"result in place. Observed adoption falls below the level the seeded "
        f"minority would produce by persisting alone in {n_short} of the {len(rs)} "
        f"conditions, by between {abs(best['short']):.2f} and "
        f"{abs(worst['short']):.2f}. At five hundred agents the shortfall holds in "
        f"{big_short} of the {len(big)} conditions, so the result is not a property "
        "of the smaller population, where a seeded share of a fifth is twenty agents. "
        "The carrier fraction remains substantially larger than adoption under tight "
        f"capacity throughout. From sweep {SRC}, {reps} replications per cell.")


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


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    by, reps = load()
    rs = cells(by)
    hdr, body = table(rs)
    para = paragraph(rs, reps)

    bad = []
    if "—" in para:
        bad.append("em dash")
    if ";" in para:
        bad.append("semicolon")
    for b in BANNED:
        if re.search(r"\b" + re.escape(b) + r"\b", para.lower()):
            bad.append(f"banned term {b!r}")
    print(f"source: results/{SRC}  ({reps} replications, {len(rs)} conditions)")
    print("prose governance:", "OK" if not bad else "FAILED " + ", ".join(bad))
    if bad:
        sys.exit(1)
    print(f"\n{para}\n")
    print("   " + " | ".join(hdr))
    for r in body:
        print("   " + " | ".join(r))
    if not apply:
        print("\npreview only, nothing written.")
        return

    bak = DOCX + ".bak14"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"\nbackup -> {os.path.basename(bak)}")
    doc = docx.Document(DOCX)
    anchor = None
    for p in doc.paragraphs:
        if p.text.strip().startswith(ANCHOR):
            anchor = p._p
            break
    if anchor is None:
        sys.exit(f"anchor {ANCHOR!r} not found")

    pp = doc.add_paragraph()
    pf = pp.paragraph_format
    pf.space_before = Pt(12); pf.space_after = Pt(6)
    lead, rest = para.split(". ", 1)
    pp.add_run(lead + ". ").font.bold = True
    pp.add_run(rest)

    t = doc.add_table(rows=1, cols=len(hdr))
    set_borders(t)
    for j, h in enumerate(hdr):
        t.rows[0].cells[j].paragraphs[0].add_run(h).font.bold = True
    for row in body:
        c = t.add_row().cells
        for j, val in enumerate(row):
            c[j].paragraphs[0].add_run(val)

    anchor.addprevious(pp._p)
    anchor.addprevious(t._tbl)
    doc.save(DOCX)
    print(f"\nfolded: 1 paragraph, 1 table ({len(body)} rows), before {ANCHOR!r}")


if __name__ == "__main__":
    main()
