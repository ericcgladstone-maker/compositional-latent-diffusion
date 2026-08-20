#!/usr/bin/env python3
"""Summarize a sweep's results into a readable per-phase report.

  python analyze.py                 # newest results/ dir
  python analyze.py results/<dir>   # a specific run

For each phase it prints the focal sweep (focal value -> key signatures) and a
short data-driven verdict on whether the phase's prediction held.
"""

import csv
import glob
import os
import sys


def latest_results_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    dirs = sorted(glob.glob(os.path.join(here, "results", "*")))
    dirs = [d for d in dirs if os.path.isfile(os.path.join(d, "aggregated.csv"))]
    if not dirs:
        sys.exit("no results found; run a sweep first")
    return dirs[-1]


def load(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def f(row, key, default=0.0):
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def main():
    rdir = sys.argv[1] if len(sys.argv) > 1 else latest_results_dir()
    print(f"== {os.path.basename(rdir)} ==\n")
    agg = load(os.path.join(rdir, "aggregated.csv"))

    # group rows by phase, preserving order
    phases, order = {}, []
    for row in agg:
        p = row["phase"]
        if p not in phases:
            phases[p] = []
            order.append(p)
        phases[p].append(row)

    for p in order:
        rows = sorted(phases[p], key=lambda r: (isinstance(num(r["focal_value"]), str),
                                                num(r["focal_value"])))
        fp = rows[0]["focal_param"]
        print(f"### {p}   (sweep: {fp})")
        print(f"    {'value':>14} | {'manifest':>9} | {'elem sat':>9} | "
              f"{'maxjump':>8} | {'t→½':>6} | {'obs gap':>8} | {'variety':>7}")
        shares = []
        for r in rows:
            ms = f(r, "final_manifest_share_mean")
            shares.append(ms)
            es = f(r, "final_element_saturation_mean")
            mj = f(r, "max_single_tick_jump_mean")
            th = f(r, "time_to_half_cascade_mean")
            og = f(r, "final_observability_gap_mean")
            var = f(r, "alpha_n_variants_mean") + f(r, "beta_n_variants_mean")
            print(f"    {str(r['focal_value']):>14} | {ms:9.3f} | {es:9.3f} | "
                  f"{mj:8.3f} | {th:6.0f} | {og:8.3f} | {var:7.1f}")
        print("    verdict:", verdict(p, rows, shares), "\n")


def verdict(phase, rows, shares):
    spread = max(shares) - min(shares) if shares else 0.0
    if phase == "V0":
        return ("SATURATES as predicted" if min(shares) > 0.95
                else f"did NOT fully saturate (min {min(shares):.2f}) — check seeding/density")
    if phase == "V1":
        return (f"regime transition across capacity (range {min(shares):.2f}–{max(shares):.2f})"
                if spread > 0.1 else f"little variation (range {spread:.2f}) — widen the sweep")
    if phase == "V1-W":
        by = {r["focal_value"]: f(r, "final_manifest_share_mean") for r in rows}
        eo = by.get("elements_only", 0.0)
        wp = by.get("whole_package", 0.0)
        return (f"wedge holds: whole_package {wp:.2f} ≥ elements_only {eo:.2f}"
                if wp >= eo else f"WEDGE INVERTED: wp {wp:.2f} < eo {eo:.2f} — investigate")
    if phase == "change-agent":
        return (f"adoption stays low under elements-only (mean {sum(shares)/len(shares):.2f}) "
                "— failed-diffusion signature" if sum(shares)/len(shares) < 0.6
                else f"spread more than expected (mean {sum(shares)/len(shares):.2f})")
    # generic: did the mechanism move anything?
    return (f"mechanism moves outcome (range {spread:.2f})" if spread > 0.05
            else f"little effect over this sweep (range {spread:.2f})")


if __name__ == "__main__":
    main()
