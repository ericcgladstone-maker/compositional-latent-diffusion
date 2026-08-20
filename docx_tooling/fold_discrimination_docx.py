#!/usr/bin/env python3
"""Fold the two discrimination experiments into the docx.

  1. Compositional versus count-only readiness under one shared token-memory
     retention process. Decides whether requiring DISTINCT prerequisites does
     work that accumulating undifferentiated exposure does not.
  2. The latent transmission channel: how much of the diffusion runs through
     agents who have not adopted, compared at equal measured material.

Every number is computed from the result CSVs, including paired contrasts.

  python fold_discrimination_docx.py            # preview
  python fold_discrimination_docx.py apply
"""
import csv, glob, math, os, re, shutil, sys
import statistics as st

import docx
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))
RESULTS = os.path.join(HERE, "results")
ANCHOR = "New specification details"


def newest(pat):
    return os.path.basename(sorted(glob.glob(os.path.join(RESULTS, pat)))[-1])


SRC_CO = os.environ.get("SRC_co") or newest("*-countonly")
SRC_CC = os.environ.get("SRC_cc") or newest("*-carrier-channel")


def f2(x):
    return f"{float(x):.2f}"


def f3(x):
    return f"{float(x):.3f}"


def paired(a, b):
    d = [a[k] - b[k] for k in sorted(a) if k in b]
    m = st.mean(d)
    se = st.pstdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
    return m, se


# ------------------------------------------------------------------ count-only
def count_only():
    agg, raw = [], []
    for f in sorted(glob.glob(os.path.join(RESULTS, SRC_CO, "countonly_*.csv"))):
        (raw if f.endswith("_raw.csv") else agg).extend(csv.DictReader(open(f)))
    by = {}
    for r in raw:
        rule, cap, loss, flow = r["cell"].split("/")
        by.setdefault((rule, cap, loss, flow), {})[int(r["rep"])] = float(r["adoption"])
    ret = {}
    for rule in ("compositional", "count-literal", "count-calibrated"):
        for cap in ("c6", "c5"):
            for loss in ("l0.0", "l0.01"):
                ret[(rule, cap, loss)] = paired(by[(rule, cap, loss, "high")],
                                                by[(rule, cap, loss, "low")])
    carr = {}
    for rule in ("compositional", "count-literal", "count-calibrated"):
        rows = [r for r in raw if r["cell"].startswith(rule) and r["cell"].endswith("high")]
        carr[rule] = st.mean(float(r["carrier_per_bt"]) for r in rows)
    return agg, ret, carr, int(agg[0]["n"])


def count_only_tables(agg, ret):
    t1 = (["Readiness rule", "Capacity", "Loss", "Flow", "Adoption mean (sd)",
           "Carriers", "Evictions per agent"], [])
    for r in agg:
        t1[1].append([r["rule"], r["capacity"], f"{float(r['loss_rate']):g}", r["flow"],
                      f"{float(r['adoption']):.2f} ({float(r['adoption_sd']):.2f})",
                      f2(r["carrier_per_bt"]), f"{float(r['evictions_per_agent']):.0f}"])
    t2 = (["Readiness rule", "Capacity", "Loss", "Return to flow", "Standard error"], [])
    for (rule, cap, loss), (m, se) in ret.items():
        t2[1].append([rule, cap.lstrip("c"), loss.lstrip("l"),
                      f"{m:+.3f}", f"{se:.3f}"])
    return t1, t2


def count_only_para(ret, carr, reps):
    c60, s60 = ret[("compositional", "c6", "l0.0")]
    c50, s50 = ret[("compositional", "c5", "l0.0")]
    l60, _ = ret[("count-literal", "c6", "l0.0")]
    l50, _ = ret[("count-literal", "c5", "l0.0")]
    c6L, _ = ret[("compositional", "c6", "l0.01")]
    l6L, _ = ret[("count-literal", "c6", "l0.01")]
    d6 = c60 - l60
    d5 = c50 - l50
    return (
        "Distinct prerequisites against accumulated exposure. The reduction in "
        "adoption under greater transmission could follow from requiring several "
        "distinct components, or simply from a finite memory filling up with anything "
        "at all. A token-memory variant separates the two. Both conditions share one "
        "retention process in which capacity counts tokens, eviction and loss remove "
        "tokens, and duplicates are retainable, and they differ only in the rule that "
        "reads readiness off that memory. The compositional rule requires k distinct "
        "required types. The count rule requires k required tokens with duplicates "
        "included. Paired runs of the two produce identical token holdings at every "
        "tick, which is asserted rather than assumed, so any difference in adoption "
        "follows from the readiness rule alone. Without element loss the reduction "
        f"appears only under the compositional rule. Adoption falls by {abs(c60):.3f} "
        f"at capacity 6 and {abs(c50):.3f} at capacity 5 as transmission rises, "
        f"against {l60:+.3f} and {l50:+.3f} under the count rule, a difference of "
        f"{d6:+.3f} and {d5:+.3f}. With loss at 0.01 both rules gain from additional "
        "transmission, because transmission then replaces material that has been lost, "
        f"but the compositional gain is much the smaller, {c6L:+.3f} against "
        f"{l6L:+.3f} at capacity 6. The carrier fraction differs in the same "
        f"direction, {carr['compositional']:.2f} under the compositional rule against "
        f"{carr['count-literal']:.2f} under the count rule. Requiring distinct "
        "components therefore does work that accumulating undifferentiated exposure "
        "does not, and the carrier population is largely a consequence of that "
        "requirement. A third condition with the count threshold calibrated to match "
        "compositional adoption where retention does not bind is reported for "
        "completeness and is not usable. The calibrated threshold of 6 exceeds a "
        "capacity of 5 and cannot be satisfied at all, and at capacity 6 it occupies "
        "the whole of memory, so a calibration carried out where retention does not "
        f"bind does not transfer to the regimes of interest. From sweep {SRC_CO}, "
        f"{reps} paired replications per cell.")


# ------------------------------------------------------------- carrier channel
def carrier_channel():
    agg = list(csv.DictReader(open(os.path.join(RESULTS, SRC_CC, "carrier_channel.csv"))))
    curves = {}
    for r in agg:
        curves.setdefault((r["capacity"], r["carrier_channel"]), []).append(
            (float(r["elements_per_agent"]), float(r["final"])))
    for k in curves:
        curves[k].sort()
    return agg, curves, int(agg[0]["n"])


def interp(curve, x):
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def carrier_tables(agg):
    t = (["Capacity", "Transmission channel", "Transmission probability",
          "Material moved per agent", "Adoption", "Carriers"], [])
    for r in agg:
        t[1].append([r["capacity"], r["carrier_channel"],
                     f"{float(r['transmission_prob']):g}",
                     f2(r["elements_per_agent"]), f2(r["final"]), f2(r["carrier_per_bt"])])
    return t


def carrier_para(agg, curves, reps):
    lines = []
    for cap in sorted({r["capacity"] for r in agg}, key=int):
        op, cl = curves[(cap, "open")], curves[(cap, "closed")]
        pts = [(x, y, interp(cl, x)) for x, y in op if interp(cl, x) is not None]
        if pts:
            lo, hi = pts[0], pts[-1]
            lines.append(
                f"at capacity {cap} the open channel differs from the closed one by "
                f"{lo[1] - lo[2]:+.3f} at {lo[0]:.1f} elements moved per agent and by "
                f"{hi[1] - hi[2]:+.3f} at {hi[0]:.1f}")
        else:
            lines.append(f"at capacity {cap} the two channels do not overlap in "
                         "material moved, so they cannot be compared at matched flow")
    return (
        "Whether the diffusion runs through agents who have not adopted. A carrier "
        "population is only part of the process if the agents in it transmit. Closing "
        "the latent channel, so that only an agent manifest for a big thing may pass "
        "on that big thing's elements, gives the counterfactual in which diffusion "
        "runs through adopters alone. Both conditions are seeded with a manifest "
        "minority of 0.05, because with the channel closed and nobody manifest at the "
        "outset nothing transmits and adoption is identically zero, which would "
        "measure a starting condition rather than the channel. The two channels move "
        "different amounts of material at the same transmission probability, so both "
        "are swept and compared at equal measured material rather than at equal "
        f"settings. Comparing the curves, {', and '.join(lines)}. The latent channel "
        "therefore does not simply add diffusion. Where the comparison can be made it "
        "carries a cost, because the channel moves a large volume of material that is "
        "not directed at any particular assembly, and under a binding capacity that "
        "material displaces partially assembled sets held by others. Two limits on "
        "this comparison should be stated. Closing the channel changes both who may "
        "transmit and what is transmitted, since a gated sender passes on only the "
        "elements of a big thing it is manifest for, so the contrast combines the "
        "identity of transmitters with the composition of traffic and does not "
        "isolate either. And at the tighter capacity the gated condition cannot reach "
        "the volumes the open condition produces at any transmission probability "
        "tested, so there is no overlap at which to compare them. What the comparison "
        "does establish is that agents who have not adopted are not passive holders. "
        "They move most of the material in this model, and that traffic is consequential "
        f"for adoption. From sweep {SRC_CC}, {reps} replications per cell.")


# ----------------------------------------------------------------------- write
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
    agg_co, ret, carr, reps_co = count_only()
    t1, t2 = count_only_tables(agg_co, ret)
    p_co = count_only_para(ret, carr, reps_co)
    agg_cc, curves, reps_cc = carrier_channel()
    t3 = carrier_tables(agg_cc)
    p_cc = carrier_para(agg_cc, curves, reps_cc)

    bad = []
    for i, t in enumerate((p_co, p_cc), 1):
        if "—" in t:
            bad.append(f"text {i}: em dash")
        if ";" in t:
            bad.append(f"text {i}: semicolon")
        for b in BANNED:
            if re.search(r"\b" + re.escape(b) + r"\b", t.lower()):
                bad.append(f"text {i}: banned term {b!r}")
    print(f"sources: {SRC_CO} | {SRC_CC}")
    print("prose governance:", "OK" if not bad else "FAILED " + "; ".join(bad))
    if bad:
        sys.exit(1)
    for nm, t in (("count-only", p_co), ("carrier channel", p_cc)):
        print(f"\n--- {nm} ({len(t.split())} words)\n{t}")
    for nm, (h, b) in (("count-only cells", t1), ("count-only contrasts", t2),
                       ("carrier channel", t3)):
        print(f"\n--- table {nm}: {len(b)} rows\n   " + " | ".join(h))
        for r in b[:6]:
            print("   " + " | ".join(r))
        if len(b) > 6:
            print(f"   ... {len(b) - 6} more rows")
    if not apply:
        print("\npreview only, nothing written.")
        return

    bak = DOCX + ".bak18"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"\nbackup -> {os.path.basename(bak)}")
    doc = docx.Document(DOCX)
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

    for el in [mk_para(p_co), mk_table(t1), mk_table(t2),
               mk_para(p_cc), mk_table(t3)]:
        anchor.addprevious(el)
    doc.save(DOCX)
    print("folded: 2 paragraphs, 3 tables")


if __name__ == "__main__":
    main()
