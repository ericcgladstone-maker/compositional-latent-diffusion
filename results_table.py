#!/usr/bin/env python3
"""Reproduce the intended-runs table with a data-derived Result column.

Reads the newest full-sweep aggregated.csv and, for each stage, reports final
adoption at each swept level (aligned with the levels) plus a short trend phrase
computed from the numbers. First-pass diagnostic results, not manuscript claims.

  python results_table.py                 # newest results/*-full
  python results_table.py results/<dir>
"""

import csv
import glob
import os
import sys

from abm import phases as P

NAMES = {
    "V0": "Free spread (baseline)", "V1": "Limited attention",
    "V1-W": "Whole vs piecemeal", "V2-slotcost": "Add-on: differential slot cost",
    "V2-compression": "Add-on: compression", "V2-stabilization": "Add-on: stabilization",
    "V2-enhanced": "Add-on: enhanced transmission",
    "V2-stab-enh": "Add-on: stabilization and enhanced",
    "V2-tiestrength": "Add-on: tie strength (90/10)",
    "V2-internal-coupling": "Add-on: internal coupling",
    "V2-neighbor-coupling": "Add-on: neighbor coupling",
    "V2-incompatibility": "Add-on: content-specific incompatibility",
    "change-agent": "Evangelists (unready population)",
}
ORDER = [p["id"] for p in P.PHASES]


def latest():
    here = os.path.dirname(os.path.abspath(__file__))
    ds = [d for d in sorted(glob.glob(os.path.join(here, "results", "*-full")))
          if os.path.isfile(os.path.join(d, "aggregated.csv"))]
    if not ds:
        sys.exit("no full-sweep results found")
    return ds[-1]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def trend(levels, vals, numeric):
    spread = max(vals) - min(vals)
    if spread < 0.05:
        return f"flat near {sum(vals)/len(vals):.2f} (little effect on adoption)"
    if not numeric:
        # categorical: name the lowest and highest levels
        lo_i = vals.index(min(vals)); hi_i = vals.index(max(vals))
        return (f"{levels[lo_i]} {vals[lo_i]:.2f} vs {levels[hi_i]} {vals[hi_i]:.2f} "
                f"(spread {spread:.2f})")
    # numeric: monotone or not
    monotone_up = all(vals[i] <= vals[i+1] + 1e-9 for i in range(len(vals)-1))
    monotone_dn = all(vals[i] >= vals[i+1] - 1e-9 for i in range(len(vals)-1))
    if monotone_up:
        return f"rises {vals[0]:.2f} to {vals[-1]:.2f} with the parameter (range {spread:.2f})"
    if monotone_dn:
        return f"falls {vals[0]:.2f} to {vals[-1]:.2f} as the parameter rises (range {spread:.2f})"
    peak_i = vals.index(max(vals))
    return (f"non-monotone, peaks at {levels[peak_i]}={vals[peak_i]:.2f} "
            f"(ends {vals[0]:.2f} to {vals[-1]:.2f})")


def build_rows():
    here = os.path.dirname(os.path.abspath(__file__))
    # Gather every sweep's aggregated.csv; latest file wins per phase. This lets
    # the table combine the main full sweep with later supplementary stage sweeps
    # without recomputing what was already proven unchanged.
    dirs = sorted(glob.glob(os.path.join(here, "results", "*")),
                  key=lambda d: os.path.getmtime(d))
    by_phase, src = {}, {}
    for d in dirs:
        agg = os.path.join(d, "aggregated.csv")
        if not os.path.isfile(agg):
            continue
        for r in csv.DictReader(open(agg)):
            by_phase[r["phase"]] = by_phase.get(r["phase"], [])
            if src.get(r["phase"]) != d:                 # new source dir for this phase
                by_phase[r["phase"]] = []; src[r["phase"]] = d
            by_phase[r["phase"]].append(r)

    rows = []
    for pid in ORDER:
        if pid not in by_phase:
            continue
        fp = P.PHASE_INDEX[pid]["focal"]["param"]
        canon = P.PHASE_INDEX[pid]["focal"]["values"]          # canonical level order
        numeric = not isinstance(canon[0], str)
        bv = {str(r["focal_value"]): r for r in by_phase[pid]}  # value -> row
        levels = [str(v) for v in canon if str(v) in bv]
        adopt = [round(float(bv[lv]["final_manifest_share_mean"]), 2) for lv in levels]
        levels_disp = [lv.replace("_", "-") for lv in levels]
        rows.append([NAMES[pid], fp.replace("_", " "), ", ".join(levels_disp),
                     ", ".join(f"{a:.2f}" for a in adopt), trend(levels_disp, adopt, numeric)])
    return rows


def main():
    rows = build_rows()
    print("# Intended runs with results")
    print("\n_First-pass diagnostic results (30 reps/level). "
          "Final adoption = mean manifest share at end of run._\n")
    print("| Stage | Swept parameter | Levels | Final adoption per level | Trend |")
    print("|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(r) + " |")


if __name__ == "__main__":
    main()
