#!/usr/bin/env python3
"""Exploratory follow-up (NOT part of the signed-off build doc).

Two questions about the transmissibility wedge, the core of the argument:

  A. TRAJECTORIES + OBSERVABILITY GAP. The main sweep saved only endpoints and
     scalar churn. Here we save the full time series for the three modes at the
     doc's wedge operating point, and characterize the observability gap
     (substrate present but not yet manifest) that the argument rests on.

  B. ROBUSTNESS / VALIDITY MAP. Every doc number is a 1-D slice at one operating
     point. Here we vary the structural knobs one at a time and ask whether the
     piecemeal-vs-whole-package adoption gap survives. Includes the degenerate
     validity test: at requirement_size == 1 the element IS the big thing, so the
     wedge MUST collapse to ~0. A model that predicts its own limit and hits it
     is more convincing than one that does not.

Operating point is config_for_phase('V1-W', ...), identical to the doc, so the
validation block must reproduce the doc endpoints (elements_only ~0.65,
whole_package ~0.99) before any new number is trusted.

Usage:
    python explore_wedge.py --reps 5     # quick pilot + validation
    python explore_wedge.py --reps 30    # full run
"""

import argparse
import csv
import json
import os
import time

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

HERE = os.path.dirname(os.path.abspath(__file__))
MODES = ["elements_only", "whole_package", "both"]

# Knob grid for Part B. Each knob is (name, [(level_label, overrides), ...]).
# requirement_size carries sufficiency_k = round(0.75*R) to hold difficulty ratio
# roughly fixed (default is k=3,R=4 -> 0.75); R=1 -> k=1 is the degenerate case.
def _rk(R):
    k = max(1, round(0.75 * R))
    return dict(requirement_size=R, sufficiency_k=k)

KNOBS = [
    ("requirement_size", [(f"R={R} (k={max(1, round(0.75*R))})", _rk(R)) for R in (1, 2, 3, 4, 5, 6)]),
    ("topology", [(t, dict(topology=t)) for t in
                  ("small_world", "random", "ring_lattice", "uniform_mixing")]),
    ("mean_degree", [(str(d), dict(mean_degree=d)) for d in (4, 6, 10)]),
    ("n_agents", [(str(n), dict(n_agents=n)) for n in (100, 300)]),
    ("transmission_prob", [(str(tp), dict(transmission_prob=tp)) for tp in (0.05, 0.1, 0.2)]),
]


def run_world(overrides, seed):
    cfg = P.config_for_phase("V1-W", {**overrides, "seed": seed})
    w = World(cfg)
    w.run()
    return w


def gap_stats(history):
    g = [h["observability_gap"] for h in history]
    peak = max(g)
    t_peak = next(h["t"] for h in history if h["observability_gap"] == peak)
    area = sum(g)  # ticks-weighted accumulation of the unobserved-substrate gap
    return round(peak, 4), t_peak, round(area, 2)


def outdir():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    d = os.path.join(HERE, "results", f"{stamp}-wedge-explore")
    os.makedirs(d, exist_ok=True)
    return d


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
        w.writeheader()
        w.writerows(rows)


def aggregate(rows, group_keys, numeric_keys):
    groups = {}
    for r in rows:
        key = tuple(r[k] for k in group_keys)
        groups.setdefault(key, []).append(r)
    out = []
    for key, grp in groups.items():
        agg = dict(zip(group_keys, key))
        agg["n"] = len(grp)
        for nk in numeric_keys:
            vals = [g[nk] for g in grp if isinstance(g.get(nk), (int, float))]
            if vals:
                m = sum(vals) / len(vals)
                var = sum((x - m) ** 2 for x in vals) / len(vals)
                agg[f"{nk}_mean"] = round(m, 4)
                agg[f"{nk}_sd"] = round(var ** 0.5, 4)
        out.append(agg)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=30)
    args = ap.parse_args()
    reps = args.reps
    d = outdir()
    print(f"out: {d}\nreps: {reps}")

    # ---- validation: must reproduce the doc wedge endpoints -----------------
    print("\n[validation] reproducing doc V1-W endpoints...")
    val = {}
    for mode in MODES:
        finals = []
        for s in range(reps):
            w = run_world({"transmissibility_mode": mode}, s)
            finals.append(summarize_history(w.history, [b.label for b in w.big_things])
                          ["final_manifest_share"])
        val[mode] = round(sum(finals) / len(finals), 4)
    print(f"  elements_only={val['elements_only']} (doc 0.65)  "
          f"whole_package={val['whole_package']} (doc 0.99)  both={val['both']} (doc 0.99)")

    # ---- Part A: trajectories + observability gap ---------------------------
    print("\n[A] trajectories...")
    traj_rows = []
    a_summary = []
    for mode in MODES:
        runs = [run_world({"transmissibility_mode": mode}, s) for s in range(reps)]
        maxlen = max(len(w.history) for w in runs)
        # padded mean trajectory (states are frozen after quiescence, so holding
        # the last value is exact, not an approximation)
        def series(w, key):
            v = [h[key] for h in w.history]
            return v + [v[-1]] * (maxlen - len(v))
        for t in range(maxlen):
            ms = [series(w, "manifest_share")[t] for w in runs]
            bs = [series(w, "bigthing_element_saturation")[t] for w in runs]
            og = [series(w, "observability_gap")[t] for w in runs]
            traj_rows.append({
                "mode": mode, "t": t,
                "manifest_share_mean": round(sum(ms) / len(ms), 4),
                "bt_elem_sat_mean": round(sum(bs) / len(bs), 4),
                "obs_gap_mean": round(sum(og) / len(og), 4),
            })
        peaks = [gap_stats(w.history) for w in runs]
        a_summary.append({
            "mode": mode,
            "final_manifest_share": val[mode],
            "obs_gap_peak_mean": round(sum(p[0] for p in peaks) / len(peaks), 4),
            "obs_gap_tpeak_mean": round(sum(p[1] for p in peaks) / len(peaks), 1),
            "obs_gap_area_mean": round(sum(p[2] for p in peaks) / len(peaks), 1),
        })
    save_csv(os.path.join(d, "part_a_trajectories.csv"), traj_rows)
    save_csv(os.path.join(d, "part_a_summary.csv"), a_summary)
    for r in a_summary:
        print(f"  {r['mode']:14s} gap peak={r['obs_gap_peak_mean']} "
              f"@t={r['obs_gap_tpeak_mean']}  area={r['obs_gap_area_mean']}")

    # ---- Part B: robustness / validity map ----------------------------------
    print("\n[B] robustness map...")
    b_runs = []
    for knob, levels in KNOBS:
        for label, ov in levels:
            for mode in ("elements_only", "whole_package"):
                for s in range(reps):
                    w = run_world({**ov, "transmissibility_mode": mode}, s)
                    summ = summarize_history(w.history, [b.label for b in w.big_things])
                    gp, gt, ga = gap_stats(w.history)
                    b_runs.append({
                        "knob": knob, "level": label, "mode": mode, "seed": s,
                        "final_manifest_share": summ["final_manifest_share"],
                        "peak_manifest_share": summ["peak_manifest_share"],
                        "overshoot": summ["overshoot"],
                        "lapse_rate": summ["lapse_rate"],
                        "obs_gap_peak": gp,
                    })
        print(f"  done: {knob}")
    save_csv(os.path.join(d, "part_b_runs.csv"), b_runs)
    b_agg = aggregate(b_runs, ["knob", "level", "mode"],
                      ["final_manifest_share", "peak_manifest_share",
                       "overshoot", "lapse_rate", "obs_gap_peak"])
    # gap = whole_package adoption - elements_only adoption, per (knob, level)
    by = {}
    for r in b_agg:
        by.setdefault((r["knob"], r["level"]), {})[r["mode"]] = r
    gap_rows = []
    for (knob, level), md in by.items():
        if "elements_only" in md and "whole_package" in md:
            eo = md["elements_only"]["final_manifest_share_mean"]
            wp = md["whole_package"]["final_manifest_share_mean"]
            gap_rows.append({
                "knob": knob, "level": level,
                "elements_only": eo, "whole_package": wp,
                "wedge_gap": round(wp - eo, 4),
                "obs_gap_peak_elements_only": md["elements_only"]["obs_gap_peak_mean"],
            })
    save_csv(os.path.join(d, "part_b_aggregated.csv"), b_agg)
    save_csv(os.path.join(d, "part_b_wedge_gap.csv"), gap_rows)

    # ---- Part C: decompose the wedge (assembly barrier x activation barrier) -
    # 2x2: requirement_size in {1,4} crossed with trigger_time in {1,100}.
    #   R=1, trigger=1   -> neither barrier  -> predict gap ~ 0 (wedge collapses)
    #   R=1, trigger=100 -> activation only  -> predict gap > 0
    #   R=4, trigger=1   -> assembly only    -> predict gap > 0
    #   R=4, trigger=100 -> both barriers    -> predict largest gap
    print("\n[C] wedge decomposition (assembly x activation)...")
    c_rows = []
    for R in (1, 4):
        for tt in (1, 100):
            ov = dict(_rk(R), trigger_time=tt)
            cell = {}
            for mode in ("elements_only", "whole_package"):
                finals = []
                for s in range(reps):
                    w = run_world({**ov, "transmissibility_mode": mode}, s)
                    finals.append(summarize_history(
                        w.history, [b.label for b in w.big_things])["final_manifest_share"])
                cell[mode] = round(sum(finals) / len(finals), 4)
            barriers = ("none" if (R == 1 and tt == 1) else
                        "activation only" if R == 1 else
                        "assembly only" if tt == 1 else "both")
            c_rows.append({
                "requirement_size": R, "trigger_time": tt, "barriers": barriers,
                "elements_only": cell["elements_only"],
                "whole_package": cell["whole_package"],
                "wedge_gap": round(cell["whole_package"] - cell["elements_only"], 4),
            })
    save_csv(os.path.join(d, "part_c_decomposition.csv"), c_rows)
    print("  barriers          R  trig  elements  whole   gap")
    for r in c_rows:
        print(f"  {r['barriers']:16s} {r['requirement_size']}  {r['trigger_time']:>4}  "
              f"{r['elements_only']:.2f}      {r['whole_package']:.2f}   {r['wedge_gap']:+.2f}")

    # ---- metadata -----------------------------------------------------------
    with open(os.path.join(d, "metadata.json"), "w") as f:
        json.dump({
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "purpose": "exploratory wedge follow-up (trajectories, observability gap, robustness/validity map)",
            "operating_point": "config_for_phase('V1-W')",
            "reps": reps, "base_seed": 0,
            "validation_endpoints": val,
            "knobs": {k: [lab for lab, _ in lv] for k, lv in KNOBS},
        }, f, indent=2, default=str)

    print(f"\nwrote: {sorted(os.listdir(d))}")
    print("\n[B] wedge gap by knob level:")
    for r in gap_rows:
        print(f"  {r['knob']:18s} {r['level']:16s} "
              f"elements={r['elements_only']:.2f} whole={r['whole_package']:.2f} "
              f"gap={r['wedge_gap']:+.2f}")


if __name__ == "__main__":
    main()
