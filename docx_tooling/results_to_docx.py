#!/usr/bin/env python3
"""Insert per-stage results (tables + grayscale figures + interpretation prose)
into the build-review .docx, IN PLACE, from the canonical sweep aggregates only.

Nothing is hand-typed: every table cell and figure datapoint is read from
results/<CANON>/aggregated.csv. Existing prose paragraphs and comments are left
untouched. The four stages with no prose (V0, slotcost, stab-enh, tiestrength)
get newly authored interpretation, flagged in the run log.

Usage:
    python results_to_docx.py            # build figures + edit the docx in place
"""

import copy
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH

from abm import phases as P

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.abspath(os.path.join(HERE, "..", "latent-adoption-build-review.docx"))
CANON = "results/20260616-160339-full"
FIGDIR = os.path.join(HERE, CANON.split("/")[0], "figures")

NEW_TITLE = "Latent Adoption Model: Build and Results"

# ---------------------------------------------------------------------------
# Stage table: column order Adoption(sd) / Peak / Overshoot / Lapse rate
# ---------------------------------------------------------------------------
PARAM_LABEL = {
    "initial_element_density": "Initial element density",
    "capacity": "Capacity",
    "transmissibility_mode": "Transmissibility mode",
    "transmission_prob": "Transmission probability",
    "stabilization_boost": "Stabilization strength (boost)",
    "enhanced_factor": "Enhanced factor",
    "strong_tie_fraction": "Strong-tie fraction",
    "coupling_strength": "Coupling strength",
    "incompatibility": "Incompatibility",
    "change_agent_fraction": "Evangelist fraction",
}

# build-order stages. kind: exist (prose already in doc) / new (author prose).
# fig: draw a figure. anchor: text prefix of existing prose para (exist only).
# before: insert this new stage's block before the prose para with this prefix.
# after_table: for exist stages whose prose is followed by an embedded table,
#              place the inserted block after that embedded table.
STAGES = [
    dict(id="V0", kind="new", fig=False, before="Limited attention",
         prose=("Baseline. With no binding capacity constraint, every seeding density "
                "drives adoption to full saturation. Final adoption is 1.00 across the "
                "entire range of initial element density, with zero overshoot and zero "
                "lapse. This stage is the null case. The dynamics of interest do not "
                "appear until a constraint is introduced, so it is the reference against "
                "which every later stage is read.")),
    dict(id="V1", kind="exist", fig=True, anchor="Limited attention"),
    dict(id="V1-W", kind="exist", fig=False, anchor="Whole versus piecemeal",
         note=("Note on churn. Whole-package transmission shows near zero overshoot but a "
               "high lapse rate of 0.57. In the aggregate adoption saturates and stays "
               "saturated, while individual nodes drop below threshold and re-acquire the "
               "package rapidly. Pieces-only transmission shows the opposite, a lower lapse "
               "rate of 0.24 alongside substantial net erosion with overshoot of 0.13. The "
               "two readings describe a stable high-turnover equilibrium under whole-package "
               "transmission against a slowly eroding one under pieces-only.")),
    dict(id="V2-slotcost", kind="new", fig=False, before="Add-on: compression",
         prose=("Add-on: differential slot cost. Charging a large package two capacity "
                "slots rather than one sharpens the same capacity-driven regime seen under "
                "limited attention. Adoption rises from 0.32 at the tightest capacity to "
                "0.99 once capacity is ample. Overshoot and lapse stay at zero across the "
                "sweep, so the change rescales competition for slots without introducing a "
                "new dynamic.")),
    dict(id="V2-compression", kind="exist", fig=False, anchor="Add-on: compression"),
    dict(id="V2-stabilization", kind="exist", fig=True, anchor="Add-on: stabilization"),
    dict(id="V2-enhanced", kind="exist", fig=True, anchor="Add-on: enhanced transmission"),
    dict(id="V2-stab-enh", kind="new", fig=False, before="Add-on: internal coupling",
         prose=("Add-on: stabilization with enhanced transmission. Combining the two "
                "add-ons lets stronger transmission convert into durable adoption rather "
                "than transient gains. Adoption rises from 0.39 to 0.66 as the enhanced "
                "factor increases, while lapse rate rises from 0.40 to 0.56. Stabilization "
                "holds enough of each gain in place for faster transmission to accumulate, "
                "which neither mechanism achieves alone.")),
    dict(id="V2-tiestrength", kind="new", fig=True, before="Add-on: internal coupling",
         prose=("Add-on: tie strength channels. Adding a small fraction of strong ties on "
                "top of many weak ones raises adoption monotonically, from 0.51 with no "
                "strong ties to 0.73 when three in ten ties are strong. Churn stays low "
                "throughout, with overshoot no higher than 0.02. Strong ties concentrate "
                "repeated contact, which helps assemble the required element set without "
                "the instability seen under coupling.")),
    dict(id="V2-internal-coupling", kind="exist", fig=True, anchor="Add-on: internal coupling",
         after_table=True),
    dict(id="V2-neighbor-coupling", kind="exist", fig=True, anchor="Add-on: neighbor coupling"),
    dict(id="V2-incompatibility", kind="exist", fig=False,
         anchor="Add-on: content-specific incompatibility"),
    dict(id="change-agent", kind="exist", fig=False, anchor="Evangelists in an unready"),
]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_aggregates():
    rows = list(csv.DictReader(open(os.path.join(HERE, CANON, "aggregated.csv"))))
    by = {}
    for r in rows:
        by.setdefault(r["phase"], {})[str(r["focal_value"])] = r
    return by


def stage_levels(pid, by):
    ph = P.PHASE_INDEX[pid]
    canon = [str(v) for v in ph["focal"]["values"]]
    rows = by[pid]
    return ph["focal"]["param"], [l for l in canon if l in rows], rows


def num(v):
    return float(v)


# ---------------------------------------------------------------------------
# Figures (grayscale, printer-friendly, no color per author preference)
# ---------------------------------------------------------------------------
def make_figure(pid, by, path):
    param, levels, rows = stage_levels(pid, by)
    x = [float(l) for l in levels]
    adopt = [num(rows[l]["final_manifest_share_mean"]) for l in levels]
    sd = [num(rows[l]["final_manifest_share_sd"]) for l in levels]
    over = [num(rows[l]["overshoot_mean"]) for l in levels]
    lapse = [num(rows[l]["lapse_rate_mean"]) for l in levels]

    plt.rcParams.update({"font.family": "serif",
                         "font.serif": ["Times New Roman", "DejaVu Serif"],
                         "font.size": 10})
    fig, ax = plt.subplots(figsize=(5.4, 3.1))
    lo = [a - s for a, s in zip(adopt, sd)]
    hi = [a + s for a, s in zip(adopt, sd)]
    ax.fill_between(x, lo, hi, color="0.82", linewidth=0, zorder=1)
    ax.plot(x, adopt, "o-", color="black", lw=1.6, ms=5, zorder=3,
            label="adoption (mean)")
    ax.plot(x, over, "s--", color="0.35", lw=1.3, ms=4, zorder=2, label="overshoot")
    ax.plot(x, lapse, "^:", color="0.55", lw=1.3, ms=4, zorder=2, label="lapse rate")
    ax.set_xlabel(PARAM_LABEL.get(param, param))
    ax.set_ylabel("share / rate")
    ax.set_ylim(-0.02, 1.02)
    ax.set_xticks(x)
    ax.grid(True, color="0.9", lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------
# docx element construction
# ---------------------------------------------------------------------------
def _set_borders(tbl):
    tblPr = tbl._tbl.tblPr
    # match existing tables: Table1 style + single 4-sz black borders all sides
    style = OxmlElement("w:tblStyle"); style.set(qn("w:val"), "Table1")
    tblPr.insert(0, style)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
        borders.append(e)
    tblPr.append(borders)
    jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "left"); tblPr.append(jc)


def _cell(cell, text, bold=False):
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.font.bold = bold
    return cell


def build_table(doc, pid, by):
    """Per-stage data table. Returns the w:tbl element (appended at doc end)."""
    param, levels, rows = stage_levels(pid, by)
    header = [PARAM_LABEL.get(param, param), "Adoption mean (sd)",
              "Peak", "Overshoot", "Lapse rate"]
    tbl = doc.add_table(rows=1 + len(levels), cols=len(header))
    _set_borders(tbl)
    for j, h in enumerate(header):
        _cell(tbl.rows[0].cells[j], h, bold=True)
    for i, l in enumerate(levels, start=1):
        r = rows[l]
        cells = tbl.rows[i].cells
        _cell(cells[0], l)
        _cell(cells[1], f"{num(r['final_manifest_share_mean']):.2f} "
                        f"({num(r['final_manifest_share_sd']):.2f})")
        _cell(cells[2], f"{num(r['peak_manifest_share_mean']):.2f}")
        _cell(cells[3], f"{num(r['overshoot_mean']):.2f}")
        _cell(cells[4], f"{num(r['lapse_rate_mean']):.2f}")
    return tbl._tbl


def build_para(doc, text, bold_lead=True, spacing=True):
    """A prose paragraph matching existing style: bold lead-in up to first period."""
    p = doc.add_paragraph()
    if spacing:
        pf = p.paragraph_format
        pf.space_before = Pt(12)
        pf.space_after = Pt(12)
    if bold_lead and ". " in text:
        lead, rest = text.split(". ", 1)
        r1 = p.add_run(lead + ". "); r1.font.bold = True
        p.add_run(rest)
    else:
        p.add_run(text)
    return p._p


def build_figure_para(doc, path, width_in):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(path, width=Inches(width_in))
    return p._p


# ---------------------------------------------------------------------------
# Anchor lookup in the live body
# ---------------------------------------------------------------------------
def find_p(body, prefix):
    for p in body.findall(qn("w:p")):
        txt = "".join(t.text or "" for t in p.iter(qn("w:t")))
        if txt.startswith(prefix):
            return p
    raise SystemExit(f"anchor not found: {prefix!r}")


def main():
    if not os.path.exists(DOCX):
        sys.exit(f"missing {DOCX}")
    os.makedirs(FIGDIR, exist_ok=True)
    by = load_aggregates()

    # figure usable width from section page size
    doc = docx.Document(DOCX)
    sec = doc.sections[0]
    usable = (sec.page_width - sec.left_margin - sec.right_margin)
    fig_w = min(5.6, usable / 914400.0 * 0.92)  # EMU -> inches

    body = doc.element.body
    flags = []

    # 1) retitle (edit text in place; keep the run/comment structure)
    for p in body.findall(qn("w:p")):
        txt = "".join(t.text or "" for t in p.iter(qn("w:t")))
        if txt.strip().startswith("Latent Adoption Model: Build"):
            ts = p.findall(".//" + qn("w:t"))
            ts[0].text = NEW_TITLE
            for extra in ts[1:]:
                extra.text = ""
            flags.append(f"title -> {NEW_TITLE}")
            break

    # 2) provenance note right after the "The build is progressive" intro
    intro = find_p(body, "The build is progressive")
    prov = build_para(doc,
        "Provenance. All per-stage tables and figures below are generated from sweep "
        "20260616-160339 (base seed 0, 30 replications per cell). Final adoption is the "
        "mean manifest share at run end. Overshoot is peak adoption minus final adoption. "
        "Lapse rate is reversions per tick. Figures are shown only where a multi-level "
        "sweep has an informative shape.")
    intro.addnext(prov)
    flags.append("added provenance note")

    # 3) figures first (so all paths exist)
    fig_paths = {}
    for s in STAGES:
        if s["fig"]:
            fp = os.path.join(FIGDIR, f"{s['id']}.png")
            make_figure(s["id"], by, fp)
            fig_paths[s["id"]] = fp

    # 4) per-stage insertion
    for s in STAGES:
        pid = s["id"]
        tbl_el = build_table(doc, pid, by)
        fig_el = build_figure_para(doc, fig_paths[pid], fig_w) if s["fig"] else None

        if s["kind"] == "exist":
            anchor = find_p(body, s["anchor"])
            ref = anchor
            if s.get("after_table"):
                nxt = anchor.getnext()
                if nxt is not None and nxt.tag == qn("w:tbl"):
                    ref = nxt
            ref.addnext(tbl_el)
            last = tbl_el
            if fig_el is not None:
                tbl_el.addnext(fig_el); last = fig_el
            if s.get("note"):
                note_el = build_para(doc, s["note"])
                last.addnext(note_el)
            flags.append(f"{pid}: table" + (" + figure" if fig_el is not None else "")
                         + (" + churn note" if s.get("note") else "") + " after prose")
        else:  # new stage: prose, table, figure before the next stage's prose
            before = find_p(body, s["before"])
            prose_el = build_para(doc, s["prose"])
            before.addprevious(prose_el)
            before.addprevious(tbl_el)
            if fig_el is not None:
                before.addprevious(fig_el)
            flags.append(f"{pid}: NEW prose + table"
                         + (" + figure" if fig_el is not None else ""))

    # backup then save in place
    bak = DOCX + ".bak"
    if not os.path.exists(bak):
        import shutil
        shutil.copy2(DOCX, bak)
        print(f"backup -> {bak}")
    doc.save(DOCX)
    print("\nedits applied:")
    for f in flags:
        print("  -", f)
    print(f"\nfigures -> {FIGDIR}")


if __name__ == "__main__":
    main()
