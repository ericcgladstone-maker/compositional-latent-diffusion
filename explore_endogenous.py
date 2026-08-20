#!/usr/bin/env python3
"""Does inertia-then-cascade survive when the trigger is not a clock?

The stepwise adoption curve is the model's most visible signature, and in every
run so far the trigger is exogenous: it fires on a fixed schedule (trigger_time
= 100). That makes the timing of the jump imposed rather than produced, and it
is the one signature a contagion model plus a periodic trigger could imitate.
This re-runs the core results with trigger_type = endogenous, where an agent
flips from latent to manifest when the share of its neighbours that are latent
or manifest for that big thing reaches endogenous_trigger_threshold. No clock is
involved, so the timing of any cascade is emergent.

Four parts:
  E1  trajectory shape, exogenous vs endogenous, per transmissibility mode.
      The decisive statistic is the spread of cascade onset across seeds: under a
      clock it is identically trigger_time, so a spread greater than zero means
      the timing is produced by the model rather than scheduled.
  E2  the capacity transition under endogenous triggering.
  E3  the observability gap and its sign, under endogenous triggering.
  E4  sensitivity to endogenous_trigger_threshold, so the result is not a
      property of one threshold value.

Per-replication raw rows are written alongside every aggregate so each mean can
be re-derived by hand. Deterministic seeds 0..REPS-1.

Usage: ABM_REPS=200 python explore_endogenous.py
"""
import csv, os, statistics as st, time

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
MODES = ["elements_only", "whole_package_gated", "whole_package"]
CAPS = [4, 5, 6, 7, 8, 10]
THRESHOLDS = [0.3, 0.5, 0.7]

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")

# Parts can be run as separate processes across cores and share one output dir.
# Each part writes its own files and its own log, so there is no contention;
# every cell is seeded 0..REPS-1 independently, so splitting changes nothing.
#   ABM_PARTS=1,2exo,2endo,4,traj   (default: all)
#   ABM_OUT=<dirname>               (default: <stamp>-endogenous)
PARTS = set(os.environ.get("ABM_PARTS", "1,2exo,2endo,4,traj").split(","))
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-endogenous"))
os.makedirs(OUT, exist_ok=True)
_tag = "-".join(sorted(PARTS)) if len(PARTS) < 5 else "all"
LOG = open(os.path.join(OUT, f"LOG-{_tag}.md"), "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")
    LOG.flush()


def write(rows, name):
    if not rows:
        return
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def shape(hist):
    """Cascade shape of one run.

    onset  = first tick adoption reaches a tenth of its own final level
    t90    = first tick it reaches nine tenths
    rise   = t90 - onset, the width of the cascade
    sub_at_onset = how much substrate had accumulated by onset (the "invisible
                   build-up" the model claims precedes visible adoption)
    """
    final = hist[-1]["manifest_share"]
    if final <= 0:
        return None
    lo, hi = 0.1 * final, 0.9 * final
    onset = next((h["t"] for h in hist if h["manifest_share"] >= lo), None)
    t90 = next((h["t"] for h in hist if h["manifest_share"] >= hi), None)
    sub = next((h["bigthing_element_saturation"] for h in hist if h["t"] == onset), 0.0)
    peak_gap = max(h["observability_gap"] for h in hist)
    return {"final": final, "onset": onset, "t90": t90,
            "rise": (t90 - onset) if (t90 is not None and onset is not None) else None,
            "sub_at_onset": sub, "final_gap": hist[-1]["observability_gap"],
            "peak_gap": peak_gap, "ticks": hist[-1]["t"]}


def run(phase, ov):
    w = World(P.config_for_phase(phase, ov))
    w.run()
    s = summarize_history(w.history, [b.label for b in w.big_things])
    sh = shape(w.history)
    return w, s, sh


def cell(phase, ov, raw, tag):
    """Run REPS replications, returning aggregate means and stashing raw rows."""
    keep = {"final": [], "onset": [], "rise": [], "sub_at_onset": [],
            "final_gap": [], "peak_gap": [], "ticks": []}
    for r in range(REPS):
        w, s, sh = run(phase, {**ov, "seed": r})
        if sh is None:
            row = {"final": 0.0, "onset": None, "rise": None, "sub_at_onset": None,
                   "final_gap": w.history[-1]["observability_gap"], "peak_gap": None,
                   "ticks": w.history[-1]["t"]}
        else:
            row = sh
        raw.append({**{"cell": tag, "rep": r, "seed": r}, **row})
        for k in keep:
            if row.get(k) is not None:
                keep[k].append(row[k])
    out = {}
    for k, v in keep.items():
        out[k] = round(st.mean(v), 4) if v else None
        out[k + "_sd"] = round(st.pstdev(v), 4) if len(v) > 1 else 0.0
    out["n"] = REPS
    return out


def main():
    log(f"# Endogenous versus exogenous triggering  ({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    log("endogenous: an agent flips when the share of its neighbours latent or "
        "manifest for that big thing reaches endogenous_trigger_threshold. "
        "No clock.")
    raw1, agg1 = [], []

    if "1" in PARTS:
        log("\n## E1/E3  trajectory shape and observability gap, by trigger type "
            "and mode")
        log("   onset = first tick adoption reaches a tenth of its final level")
        for mode in MODES:
            for trig in ("exogenous", "endogenous"):
                tag = f"{trig}/{mode}"
                ov = {"transmissibility_mode": mode, "trigger_type": trig}
                a = cell("V1-W", ov, raw1, tag)
                agg1.append({"trigger_type": trig, "mode": mode, **a})
                log(f"  {tag:34s} final={a['final']:.4f}  onset={a['onset']}"
                    f" (sd {a['onset_sd']})  rise={a['rise']}  "
                    f"substrate@onset={a['sub_at_onset']}  "
                    f"final_gap={a['final_gap']:+.4f}")
                write(agg1, "e1_shape.csv")
                write(raw1, "e1_shape_raw.csv")

        log("\n   ONSET SPREAD (the decisive number: zero under a clock)")
        for r in agg1:
            log(f"     {r['trigger_type']:11s} {r['mode']:20s} "
                f"onset sd = {r['onset_sd']}")

    log("\n## E2  capacity transition under each trigger type")
    raw2, agg2 = [], []
    for trig in [t for t in ("exogenous", "endogenous") if f"2{t[:4]}" in PARTS]:
        line = []
        for cap in CAPS:
            tag = f"{trig}/cap{cap}"
            a = cell("V1", {"capacity": cap, "trigger_type": trig}, raw2, tag)
            agg2.append({"trigger_type": trig, "capacity": cap, **a})
            line.append((cap, a["final"]))
            write(agg2, f"e2_capacity_{trig}.csv")
            write(raw2, f"e2_capacity_{trig}_raw.csv")
        log(f"  {trig:11s} " + "  ".join(f"cap{c}={v:.4f}" for c, v in line))

    log("\n## E4  sensitivity to the endogenous threshold (elements_only)")
    raw4, agg4 = [], []
    for thr in (THRESHOLDS if "4" in PARTS else []):
        tag = f"thr{thr}"
        a = cell("V1-W", {"transmissibility_mode": "elements_only",
                          "trigger_type": "endogenous",
                          "endogenous_trigger_threshold": thr}, raw4, tag)
        agg4.append({"endogenous_trigger_threshold": thr, **a})
        log(f"  threshold={thr}: final={a['final']:.4f}  onset={a['onset']} "
            f"(sd {a['onset_sd']})  rise={a['rise']}  final_gap={a['final_gap']:+.4f}")
        write(agg4, "e4_threshold.csv")
        write(raw4, "e4_threshold_raw.csv")

    log("\n## mean trajectories (for the figure): adoption and substrate over time")
    traj = []
    for mode in (("elements_only",) if "traj" in PARTS else ()):
        for trig in ("exogenous", "endogenous"):
            runs = []
            for r in range(REPS):
                w = World(P.config_for_phase("V1-W", {
                    "transmissibility_mode": mode, "trigger_type": trig, "seed": r}))
                w.run()
                runs.append(w.history)
            T = max(h[-1]["t"] for h in runs)
            for t in range(1, T + 1):
                ms, ss = [], []
                for h in runs:
                    # a run that reached quiescence early holds its last state
                    rec = h[t - 1] if t - 1 < len(h) else h[-1]
                    ms.append(rec["manifest_share"])
                    ss.append(rec["bigthing_element_saturation"])
                traj.append({"trigger_type": trig, "mode": mode, "t": t,
                             "manifest_share": round(st.mean(ms), 4),
                             "substrate": round(st.mean(ss), 4), "n": REPS})
            log(f"  {trig}/{mode}: {T} ticks averaged over {REPS} runs")
    write(traj, "trajectories.csv")

    log("\nDONE.")
    LOG.close()


if __name__ == "__main__":
    main()
