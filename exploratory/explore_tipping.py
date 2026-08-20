#!/usr/bin/env python3
"""Exploratory follow-up #2 (NOT part of the signed-off build doc): tipping points
and bistability/hysteresis. Operating point: config_for_phase('V1').

  A. TIPPING POINT. Two views of the V1 capacity transition.
     A1 capacity distribution: capacity 4..8 at high replication, with per-run
        final adoption binned low/mid/high. If the distribution goes bimodal at
        the transition (mass at the extremes, little in the middle) the tipping
        point is a genuine bistable threshold rather than a gradual rise.
     A2 continuous collapse: loss_rate swept finely. A continuous control knob, to
        see whether adoption falls off a cliff at a critical loss rate.

  B. BISTABILITY (the cause of hysteresis). At each capacity and eviction rule,
     run from two initial conditions: from_below (fresh seeding, low adoption) and
     from_above (population forced fully adopted). If from_above settles higher
     than from_below at the same parameter, two stable states coexist, which is
     bistability and the precondition for hysteresis. Hypothesis: value_weighted
     eviction (agents protect the elements completing a big thing) sustains the
     adopted state where random eviction does not.

     A first design used a quasi-static capacity ramp with end-state carryover;
     its flat-ramp sanity control drifted (cumulative churn erosion across
     re-equilibrations), so it was discarded for this cleaner two-IC test.

Usage:
    python explore_tipping.py --reps 5      # pilot
    python explore_tipping.py --reps 30     # full
"""

import argparse
import csv
import json
import os
import time
from collections import Counter

from abm import phases as P
from abm.model import World

HERE = os.path.dirname(os.path.abspath(__file__))


def final_adopt(w):
    return w.history[-1]["manifest_share"]


def bins(finals):
    n = len(finals)
    return (round(sum(1 for x in finals if x < 0.33) / n, 3),
            round(sum(1 for x in finals if 0.33 <= x <= 0.66) / n, 3),
            round(sum(1 for x in finals if x > 0.66) / n, 3))


def msd(xs):
    m = sum(xs) / len(xs)
    return round(m, 4), round((sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5, 4)


# ---------------------------------------------------------------------------
# A1: capacity distribution / bimodality
# ---------------------------------------------------------------------------
def part_a1(caps, reps):
    rows, agg = [], []
    for cap in caps:
        finals = []
        for s in range(reps):
            w = World(P.config_for_phase("V1", {"capacity": cap, "seed": s}))
            w.run()
            f = final_adopt(w)
            finals.append(f)
            rows.append({"capacity": cap, "seed": s, "final_manifest_share": round(f, 4)})
        m, sd = msd(finals)
        lo, mid, hi = bins(finals)
        agg.append({"capacity": cap, "n": reps, "adopt_mean": m, "adopt_sd": sd,
                    "frac_low(<0.33)": lo, "frac_mid(0.33-0.66)": mid, "frac_high(>0.66)": hi})
    return rows, agg


# ---------------------------------------------------------------------------
# A2: continuous collapse via loss_rate
# ---------------------------------------------------------------------------
def part_a2(losses, reps):
    rows, agg = [], []
    for lr in losses:
        finals = []
        for s in range(reps):
            w = World(P.config_for_phase("V1", {"loss_rate": lr, "seed": s}))
            w.run()
            f = final_adopt(w)
            finals.append(f)
            rows.append({"loss_rate": lr, "seed": s, "final_manifest_share": round(f, 4)})
        m, sd = msd(finals)
        agg.append({"loss_rate": lr, "n": reps, "adopt_mean": m, "adopt_sd": sd})
    return rows, agg


# ---------------------------------------------------------------------------
# B: bistability (two initial conditions)
# ---------------------------------------------------------------------------
def force_fully_adopted(w):
    """Set every agent to the maximal-adoption holding set for this capacity, then
    manifest everything that meets sufficiency. A uniform 'from above' state."""
    cnt = Counter()
    for bt in w.big_things:
        for e in bt.required:
            cnt[e] += 1
    order = sorted(cnt, key=lambda e: (-cnt[e], e))      # shared elements first
    hold = order[: w.cfg["capacity"]]
    for a in w.agents:
        a.held = set(hold); a.order = list(hold)
        a.chunks = set(); a.manifest = set(); a.latent = set(); a.variant = {}
    w._recompute_all_latent()
    for a in w.agents:
        for bid in list(a.latent):
            w._manifest(a, bid)
    w._recompute_all_latent()
    w.t = 0; w.lapses = 0
    w.history = [w.metrics()]


def part_b(caps, evictions, reps):
    runs, agg = [], []
    for eviction in evictions:
        for cap in caps:
            for cond in ("from_below", "from_above"):
                finals = []
                for s in range(reps):
                    w = World(P.config_for_phase("V1", {"capacity": cap,
                                                         "eviction_rule": eviction, "seed": s}))
                    if cond == "from_above":
                        force_fully_adopted(w)
                    start = final_adopt(w) if cond == "from_above" else None
                    w.run()
                    finals.append(final_adopt(w))
                    runs.append({"eviction": eviction, "capacity": cap, "condition": cond,
                                 "seed": s, "start_adopt": round(start, 4) if start is not None else "",
                                 "final_manifest_share": round(final_adopt(w), 4)})
                m, sd = msd(finals)
                agg.append({"eviction": eviction, "capacity": cap, "condition": cond,
                            "n": reps, "adopt_mean": m, "adopt_sd": sd})
    # bistability gap = from_above_final - from_below_final, per (eviction, capacity)
    gap = []
    for eviction in evictions:
        for cap in caps:
            ab = next(a for a in agg if a["eviction"] == eviction and a["capacity"] == cap
                      and a["condition"] == "from_above")
            be = next(a for a in agg if a["eviction"] == eviction and a["capacity"] == cap
                      and a["condition"] == "from_below")
            gap.append({"eviction": eviction, "capacity": cap,
                        "from_below": be["adopt_mean"], "from_above": ab["adopt_mean"],
                        "bistability_gap": round(ab["adopt_mean"] - be["adopt_mean"], 4)})
    return runs, agg, gap


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--dist-reps", type=int, default=100)
    args = ap.parse_args()

    stamp = time.strftime("%Y%m%d-%H%M%S")
    d = os.path.join(HERE, "results", f"{stamp}-tipping")
    os.makedirs(d, exist_ok=True)
    print(f"out: {d}\nB reps: {args.reps}, A1 dist-reps: {args.dist_reps}")

    print("\n[A1] capacity distribution / bimodality...")
    caps_fine = [4, 5, 6, 7, 8]
    a1_rows, a1_agg = part_a1(caps_fine, args.dist_reps)
    save_csv(os.path.join(d, "part_a1_runs.csv"), a1_rows)
    save_csv(os.path.join(d, "part_a1_aggregated.csv"), a1_agg)
    for r in a1_agg:
        print(f"  cap={r['capacity']} adopt={r['adopt_mean']:.2f}(sd {r['adopt_sd']:.2f}) "
              f"low/mid/high={r['frac_low(<0.33)']:.2f}/{r['frac_mid(0.33-0.66)']:.2f}/"
              f"{r['frac_high(>0.66)']:.2f}")

    print("\n[A2] continuous collapse via loss_rate...")
    losses = [0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04]
    a2_rows, a2_agg = part_a2(losses, max(30, args.reps))
    save_csv(os.path.join(d, "part_a2_runs.csv"), a2_rows)
    save_csv(os.path.join(d, "part_a2_aggregated.csv"), a2_agg)
    for r in a2_agg:
        print(f"  loss={r['loss_rate']:.3f} adopt={r['adopt_mean']:.2f}(sd {r['adopt_sd']:.2f})")

    print("\n[B] bistability (from_below vs from_above)...")
    caps_b = [4, 5, 6, 7, 8, 10]
    b_runs, b_agg, b_gap = part_b(caps_b, ["random", "value_weighted"], args.reps)
    save_csv(os.path.join(d, "part_b_runs.csv"), b_runs)
    save_csv(os.path.join(d, "part_b_aggregated.csv"), b_agg)
    save_csv(os.path.join(d, "part_b_bistability.csv"), b_gap)
    for ev in ("random", "value_weighted"):
        print(f"  {ev}:")
        for r in [x for x in b_gap if x["eviction"] == ev]:
            print(f"    cap={r['capacity']:>2} below={r['from_below']:.2f} "
                  f"above={r['from_above']:.2f} gap={r['bistability_gap']:+.2f}")

    with open(os.path.join(d, "metadata.json"), "w") as f:
        json.dump({"created": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "purpose": "tipping points (capacity bimodality, loss-rate collapse) and bistability",
                   "operating_point": "config_for_phase('V1')",
                   "a1_caps": caps_fine, "a1_reps": args.dist_reps,
                   "a2_losses": losses, "b_caps": caps_b, "b_reps": args.reps,
                   "evictions": ["random", "value_weighted"]}, f, indent=2, default=str)
    print(f"\nwrote: {sorted(os.listdir(d))}")


if __name__ == "__main__":
    main()
