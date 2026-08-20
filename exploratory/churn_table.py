#!/usr/bin/env python3
"""Churn view of the sweep: peak adoption, overshoot (peak that eroded away), and
lapse rate per stage. Surfaces the reversibility-driven dynamics that final
adoption alone hides (e.g. mechanisms that looked 'flat' at the endpoint).

  python churn_table.py
"""

import csv
import glob
import os
import sys

from results_table import NAMES, ORDER
from abm import phases as P


def latest_full():
    here = os.path.dirname(os.path.abspath(__file__))
    ds = [d for d in sorted(glob.glob(os.path.join(here, "results", "*-full")))
          if os.path.isfile(os.path.join(d, "aggregated.csv"))]
    return ds[-1] if ds else sys.exit("no full sweep with churn columns yet")


def build_churn_rows():
    rdir = latest_full()
    rows = list(csv.DictReader(open(os.path.join(rdir, "aggregated.csv"))))
    if "overshoot_mean" not in rows[0]:
        sys.exit(f"{rdir} has no churn columns; re-run the sweep on the churn build")
    by = {}
    for r in rows:
        by.setdefault(r["phase"], []).append(r)

    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return v

    out = []
    for pid in ORDER:
        if pid not in by:
            continue
        canon = P.PHASE_INDEX[pid]["focal"]["values"]
        bv = {str(r["focal_value"]): r for r in by[pid]}
        levels = [str(v) for v in canon if str(v) in bv]
        adopt = [float(bv[l]["final_manifest_share_mean"]) for l in levels]
        over = [float(bv[l]["overshoot_mean"]) for l in levels]
        lr = [float(bv[l]["lapse_rate_mean"]) for l in levels]
        out.append([NAMES[pid],
                    f"{min(adopt):.2f}-{max(adopt):.2f}",
                    f"{max(over):.2f}",               # worst overshoot in the sweep
                    f"{min(lr):.2f}-{max(lr):.2f}"])
    return out, os.path.basename(rdir)


def main():
    rows, tag = build_churn_rows()
    print(f"# Churn view ({tag})\n")
    print("_Overshoot = peak adoption minus final (how much adoption eroded after "
          "peaking). Lapse rate = reversions per tick. High values = churn-heavy._\n")
    print("| Stage | Final adoption (range) | Max overshoot | Lapse rate (range) |")
    print("|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(r) + " |")


if __name__ == "__main__":
    main()
