#!/usr/bin/env python3
"""The reversible-vs-irreversible internal-coupling test, made reproducible.

The docx carries an evidence table showing that the internal-coupling gradient
flattens when reversible adoption is switched off, which is what establishes
that coupling acts through churn rather than by suppressing adoption directly.
That table was produced ad hoc in an earlier session: no script and no saved
result directory. This reconstructs it from the phase definition so the number
in the document can be traced to a file like every other number.

Design: the V2-internal-coupling phase base, sweeping coupling_strength over the
levels the table reports, once with reversible_adoption on (the model default)
and once off. Deterministic seeds 0..REPS-1.

Usage: ABM_REPS=200 python explore_reversibility.py
"""
import csv, os, statistics as st, time

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
LEVELS = [-0.5, 0.0, 1.0, -1.0]        # the rows the docx table reports
LABEL = {-0.5: "Mild antagonism (-0.5)", 0.0: "No coupling (0)",
         1.0: "Facilitation (+1)", -1.0: "Hard antagonism (-1)"}

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", f"{STAMP}-reversibility")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "LOG.md"), "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")
    LOG.flush()


def cell(cs, reversible):
    fins = []
    for s in range(REPS):
        cfg = P.config_for_phase("V2-internal-coupling", {
            "coupling_strength": cs, "reversible_adoption": reversible, "seed": s})
        w = World(cfg)
        w.run()
        fins.append(summarize_history(
            w.history, [b.label for b in w.big_things])["final_manifest_share"])
    return round(st.mean(fins), 4), round(st.pstdev(fins), 4)


def main():
    log(f"# Internal coupling under reversible vs irreversible adoption "
        f"({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    log("base: phase V2-internal-coupling; only coupling_strength and "
        "reversible_adoption vary")
    rows = []
    for cs in LEVELS:
        rev, rev_sd = cell(cs, True)
        irr, irr_sd = cell(cs, False)
        rows.append({"coupling_strength": cs, "label": LABEL[cs],
                     "reversible": rev, "reversible_sd": rev_sd,
                     "irreversible": irr, "irreversible_sd": irr_sd,
                     "n": REPS})
        log(f"  {LABEL[cs]:24s} reversible={rev:.4f}  irreversible={irr:.4f}  "
            f"flattening={irr - rev:+.4f}")
    with open(os.path.join(OUT, "reversibility.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    spread_rev = max(r["reversible"] for r in rows) - min(r["reversible"] for r in rows)
    soft = [r for r in rows if r["coupling_strength"] != -1.0]
    spread_irr = (max(r["irreversible"] for r in soft)
                  - min(r["irreversible"] for r in soft))
    log(f"\nspread across coupling, reversible: {spread_rev:.4f}")
    log(f"spread across coupling, irreversible (excluding the -1 clip): {spread_irr:.4f}")
    log("DONE.")
    LOG.close()


if __name__ == "__main__":
    main()
