#!/usr/bin/env python3
"""Fixed-content packetization: does joint arrival matter at identical content?

The dose-response comparison showed a bundled advantage at roughly matched
material, but "material acquired per agent" is itself produced by the diffusion
process, so comparing two parameterised systems that happen to move similar
amounts is not the same as experimentally assigning the same flow. This assigns
it.

A block is one recipient, four eligible delivery opportunities, and exactly one
instance of each of the four required focal elements.

  piecemeal   the four elements are permuted and one is delivered at each of the
              four opportunities
  bundled     one of those same four opportunities is chosen uniformly and all
              four elements are delivered there. The other three carry no focal
              material.

Paired arms use the same network, the same seed, and the SAME block schedule,
so recipient, opportunity count, opportunity timing, total focal content and
background traffic are all held fixed. The only manipulated property is whether
complementary material arrives jointly or separately.

Delivery goes through the ordinary admission path, so capacity and eviction
process the material in both arms. Bundled does NOT mean the recipient is handed
an adopted state or a special package object: four elements arriving at once
into six slots displace whatever is there, which is the mechanism under test.

Flow is manipulated by block FREQUENCY, not block contents. Frequencies are
calibrated once against realised focal acquisitions per agent and then frozen.

  ABM_REPS=200 python explore_packetization.py [calibrate|run]
"""
import csv, os, statistics as st, sys, time

import numpy as np

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
# Fixed horizon, no quiescence stopping, so both arms are exposed to exactly the
# same block schedule. With quiescence the arms stop at different ticks and the
# amount of focal material offered stops being matched, which is the one thing
# this design must hold fixed.
HORIZON = 300
BASE = dict(transmissibility_mode="elements_only", trigger_type="exogenous",
            reversible_adoption=True, run_length=HORIZON)
# C=6 is the operating point named in the brief. Under a fixed horizon it sits
# near a ceiling (baseline about 0.79), so C=5 is run alongside it as the regime
# where capacity actually binds (baseline about 0.50) and there is room to move.
CAPACITIES = (6, 5)
ARMS = ("piecemeal", "bundled")

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-packetization"))
os.makedirs(OUT, exist_ok=True)


def log_to(path):
    f = open(path, "w")
    def log(*a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True)
        f.write(s + "\n"); f.flush()
    return log


def make_schedule(world, blocks_per_agent, seed):
    """Block schedule shared by both arms: (recipient, [4 opportunity ticks]).

    Drawn from a dedicated generator so it is identical across arms regardless
    of how many random draws the two arms consume internally.
    """
    rng = np.random.default_rng(seed + 7_000_003)
    T = world.cfg["run_length"]
    sched = []
    for i in range(world.n):
        for _ in range(blocks_per_agent):
            ticks = sorted(rng.choice(np.arange(1, T + 1), size=4, replace=False).tolist())
            # which opportunity carries the bundle, and the piecemeal order
            bundle_at = int(rng.integers(0, 4))
            order = rng.permutation(4).tolist()
            sched.append((i, ticks, bundle_at, order))
    return sched


def run_one(arm, blocks_per_agent, seed, capacity):
    w = World(P.config_for_phase("V1", {**BASE, "capacity": capacity, "seed": seed}))
    focal = list(w.big_things[0].required)          # the four required focal elements
    sched = make_schedule(w, blocks_per_agent, seed)
    # index deliveries by tick for cheap lookup
    by_tick = {}
    for (i, ticks, bundle_at, order) in sched:
        for slot, t in enumerate(ticks):
            if arm == "piecemeal":
                by_tick.setdefault(t, []).append((i, [focal[order[slot]]]))
            else:
                if slot == bundle_at:
                    by_tick.setdefault(t, []).append((i, list(focal)))
    # Match the engine's own stopping rule. Running the full length instead
    # accumulates about three times the material and pushes adoption to a
    # ceiling where the arms cannot be told apart.
    offered = acquired = 0
    for _ in range(w.cfg["run_length"]):
        w.step()
        for (i, elems) in by_tick.get(w.t, ()):
            for e in elems:
                offered += 1
                if w._add_element(w.agents[i], e):
                    acquired += 1
    s = summarize_history(w.history, [b.label for b in w.big_things])
    n = w.n
    return {"final": s["final_manifest_share"], "peak": s["peak_manifest_share"],
            "lapse_rate": s["lapse_rate"],
            "focal_offered_per_agent": offered / n,
            "focal_acquired_per_agent": acquired / n,
            "total_acquired_per_agent": w.elements_added / n,
            "evictions_per_agent": w.evictions / n,
            "required_evictions_per_agent": w.evictions_required / n}


FIELDS = ["final", "peak", "lapse_rate", "focal_offered_per_agent",
          "focal_acquired_per_agent", "total_acquired_per_agent",
          "evictions_per_agent", "required_evictions_per_agent"]


def cell(arm, bpa, reps, capacity, raw=None, tag=""):
    vals = {k: [] for k in FIELDS}
    for r in range(reps):
        row = run_one(arm, bpa, r, capacity)
        if raw is not None:
            raw.append({"cell": tag, "rep": r, "seed": r,
                        **{k: round(row[k], 4) for k in FIELDS}})
        for k in FIELDS:
            vals[k].append(row[k])
    out = {k: round(st.mean(v), 4) for k, v in vals.items()}
    out["final_sd"] = round(st.pstdev(vals["final"]), 4)
    out["n"] = reps
    return out


def calibrate():
    """Pick block frequencies hitting roughly 9-10 and 13-14 focal acquisitions
    per agent, then stop. Frequencies are frozen before the real run."""
    log = log_to(os.path.join(OUT, "LOG-calibration.md"))
    log(f"# Packetization calibration  {STAMP}")
    log("choosing block frequencies by realised focal acquisitions per agent "
        "(targets: about 9-10 low, 13-14 high)")
    log(f"{'blocks/agent':>13} {'arm':>10} {'focal offered':>14} "
        f"{'focal acquired':>15} {'total acquired':>15} {'adoption':>9}")
    for bpa in (2, 4, 6, 9, 12):
        for arm in ARMS:
            a = cell(arm, bpa, 8, 5)
            log(f"{bpa:>13} {arm:>10} {a['focal_offered_per_agent']:>14.2f} "
                f"{a['focal_acquired_per_agent']:>15.2f} "
                f"{a['total_acquired_per_agent']:>15.2f} {a['final']:>9.4f}")


def run(low, high):
    log = log_to(os.path.join(OUT, "LOG.md"))
    log(f"# Fixed-content packetization  ({REPS} paired replications)  {STAMP}")
    log(f"out: {OUT}")
    log("Same recipient, same four delivery opportunities, same four focal "
        "elements, same background traffic, same seed. Only joint versus "
        "separate arrival differs.")
    log(f"frozen block frequencies: low={low} blocks/agent, high={high}")
    raw, agg = [], []
    res = {}
    for cap in CAPACITIES:
        log(f"\n## capacity {cap}"
            + ("   (the operating point named in the brief)" if cap == 6
               else "   (capacity binds harder under a fixed horizon)"))
        for flow, bpa in (("low", low), ("high", high)):
            for arm in ARMS:
                tag = f"c{cap}/{arm}/{flow}"
                a = cell(arm, bpa, REPS, cap, raw, tag)
                agg.append({"capacity": cap, "arm": arm, "flow": flow,
                            "blocks_per_agent": bpa, **a})
                res[(cap, arm, flow)] = a
                with open(os.path.join(OUT, "packetization.csv"), "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(agg[0].keys()))
                    w.writeheader(); w.writerows(agg)
                with open(os.path.join(OUT, "packetization_raw.csv"), "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(raw[0].keys()))
                    w.writeheader(); w.writerows(raw)
                log(f"  {arm:10s} {flow:5s} adoption={a['final']:.4f} "
                    f"(sd {a['final_sd']:.4f})  focal offered/agent="
                    f"{a['focal_offered_per_agent']:.2f}  acquired="
                    f"{a['focal_acquired_per_agent']:.2f}  total="
                    f"{a['total_acquired_per_agent']:.2f}  req.evictions="
                    f"{a['required_evictions_per_agent']:.2f}")
        bl = res[(cap,"bundled","low")]["final"] - res[(cap,"piecemeal","low")]["final"]
        bh = res[(cap,"bundled","high")]["final"] - res[(cap,"piecemeal","high")]["final"]
        pf = res[(cap,"piecemeal","high")]["final"] - res[(cap,"piecemeal","low")]["final"]
        bf = res[(cap,"bundled","high")]["final"] - res[(cap,"bundled","low")]["final"]
        log(f"  contrasts at capacity {cap}:")
        log(f"    bundling effect, low flow    {bl:+.4f}")
        log(f"    bundling effect, high flow   {bh:+.4f}")
        log(f"    return to flow, piecemeal    {pf:+.4f}")
        log(f"    return to flow, bundled      {bf:+.4f}")
        log(f"    delivery x flow interaction  {bf - pf:+.4f}")

    log("\nDONE.")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "calibrate"
    if what == "calibrate":
        calibrate()
    else:
        run(int(sys.argv[2]), int(sys.argv[3]))
