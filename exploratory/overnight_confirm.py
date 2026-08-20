#!/usr/bin/env python3
"""Overnight confirmation / validity runs (NOT part of the signed-off doc).

  PART 1  MECHANISM TEST for the bistability. Tonight's claim: the path dependence
          comes from the k-of-R threshold slack (an adopter tolerates losing
          elements down to k). Falsifiable prediction: with NO slack (k==R) the
          adopted state should erode and the bistability gap should collapse; with
          MORE slack (k << R) it should strengthen. Fixed capacity, vary (R,k).

  PART 2  CONFIRMATION AT SCALE. The three load-bearing results re-checked at
          N=500 and N=1000: the wedge gap, the observability-gap sign flip, and the
          capacity bistability. Confirms they are not small-N / small-rep artifacts.

Operating point: config_for_phase('V1') / ('V1-W'). Numbers derive from the engine.

Usage:
    python overnight_confirm.py --reps 5     # pilot
    python overnight_confirm.py --reps 50    # full
"""

import argparse
import csv
import json
import os
import time

from abm import phases as P
from abm.model import World
from explore_tipping import force_fully_adopted

HERE = os.path.dirname(os.path.abspath(__file__))


def final(w, key="manifest_share"):
    return w.history[-1][key]


def msd(xs):
    m = sum(xs) / len(xs)
    return round(m, 4), round((sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5, 4)


def save_csv(path, rows):
    if not rows:
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)


# ---------------------------------------------------------------------------
# Part 1: threshold-slack mechanism test
# ---------------------------------------------------------------------------
def part1(reps, capacity=6):
    # (R, k) pairs spanning no-slack (k==R) to large slack (k<<R)
    combos = [(3, 3), (3, 2), (4, 4), (4, 3), (4, 2),
              (5, 5), (5, 3), (6, 6), (6, 4), (6, 3)]
    rows = []
    for R, k in combos:
        cell = {}
        lapses_above = []
        for cond in ("from_below", "from_above"):
            finals = []
            for s in range(reps):
                w = World(P.config_for_phase("V1", {"capacity": capacity,
                          "requirement_size": R, "sufficiency_k": k, "seed": s}))
                if cond == "from_above":
                    force_fully_adopted(w)
                w.run()
                finals.append(final(w))
                if cond == "from_above":
                    lapses_above.append(w.lapses)
            cell[cond], _ = msd(finals)
        # lapses in from_above tell persistence mode: ~0 = held by slack / reservoir
        # without reversion; >0 = sustained through churn (lose-and-reacquire).
        rows.append({"requirement_size": R, "sufficiency_k": k, "slack": R - k,
                     "capacity": capacity,
                     "from_below": cell["from_below"], "from_above": cell["from_above"],
                     "bistability_gap": round(cell["from_above"] - cell["from_below"], 4),
                     "lapses_above_mean": round(sum(lapses_above) / len(lapses_above), 1)})
    return rows


# ---------------------------------------------------------------------------
# Part 2: confirmation at scale
# ---------------------------------------------------------------------------
def part2_wedge(reps, sizes):
    rows = []
    for N in sizes:
        for mode in ("elements_only", "whole_package", "both"):
            ms, gaps = [], []
            for s in range(reps):
                w = World(P.config_for_phase("V1-W", {"transmissibility_mode": mode,
                          "n_agents": N, "seed": s}))
                w.run()
                ms.append(final(w)); gaps.append(final(w, "observability_gap"))
            mm, msd_ = msd(ms); gm, gsd = msd(gaps)
            rows.append({"n_agents": N, "mode": mode, "n": reps,
                         "final_manifest_share_mean": mm, "final_manifest_share_sd": msd_,
                         "final_obs_gap_mean": gm, "final_obs_gap_sd": gsd})
    return rows


def part2_bistability(reps, N, caps):
    rows = []
    for cap in caps:
        cell = {}
        for cond in ("from_below", "from_above"):
            finals = []
            for s in range(reps):
                w = World(P.config_for_phase("V1", {"capacity": cap, "n_agents": N, "seed": s}))
                if cond == "from_above":
                    force_fully_adopted(w)
                w.run()
                finals.append(final(w))
            cell[cond], _ = msd(finals)
        rows.append({"n_agents": N, "capacity": cap,
                     "from_below": cell["from_below"], "from_above": cell["from_above"],
                     "bistability_gap": round(cell["from_above"] - cell["from_below"], 4)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=50)
    args = ap.parse_args()
    reps = args.reps

    stamp = time.strftime("%Y%m%d-%H%M%S")
    d = os.path.join(HERE, "results", f"{stamp}-confirm")
    os.makedirs(d, exist_ok=True)
    print(f"out: {d}\nreps: {reps}")

    print("\n[1] threshold-slack mechanism test (capacity 6, vary R,k)...")
    p1 = part1(reps)
    save_csv(os.path.join(d, "part1_slack.csv"), p1)
    print(f"  {'R':>2} {'k':>2} {'slack':>5} {'below':>6} {'above':>6} {'gap':>6}")
    for r in p1:
        print(f"  {r['requirement_size']:>2} {r['sufficiency_k']:>2} {r['slack']:>5} "
              f"{r['from_below']:>6.2f} {r['from_above']:>6.2f} {r['bistability_gap']:>+6.2f}")

    print("\n[2a] wedge + observability gap at scale (N=500, 1000)...")
    p2w = part2_wedge(reps, [500, 1000])
    save_csv(os.path.join(d, "part2_wedge_scale.csv"), p2w)
    for r in p2w:
        print(f"  N={r['n_agents']:>4} {r['mode']:14s} adopt={r['final_manifest_share_mean']:.3f} "
              f"final_obs_gap={r['final_obs_gap_mean']:+.3f}")

    print("\n[2b] capacity bistability at scale (N=500)...")
    p2b = part2_bistability(reps, 500, [4, 5, 6, 7, 8])
    save_csv(os.path.join(d, "part2_bistability_scale.csv"), p2b)
    for r in p2b:
        print(f"  cap={r['capacity']:>2} below={r['from_below']:.2f} "
              f"above={r['from_above']:.2f} gap={r['bistability_gap']:+.2f}")

    with open(os.path.join(d, "metadata.json"), "w") as f:
        json.dump({"created": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "purpose": "overnight confirmation: threshold-slack mechanism test + scale confirmation",
                   "operating_point": "config_for_phase('V1' / 'V1-W')",
                   "reps": reps, "scale_sizes": [500, 1000]}, f, indent=2, default=str)
    print(f"\nwrote: {sorted(os.listdir(d))}")


if __name__ == "__main__":
    main()
