#!/usr/bin/env python3
"""What separates this model from contagion when change agents fail in both.

An equipped, manifest minority failing to move adoption is not on its own a
result that distinguishes this model from the incumbent one: complex contagion
predicts the same thing whenever seeds sit below the reinforcement threshold.
Conceding that overlap and then showing what does differ is stronger than
claiming the failure itself is diagnostic.

The difference is structural. Where the adopted object travels as a unit, an
agent either has it or does not. Where it is assembled from parts that travel
separately, there is a population holding SOME of the parts: able to pass them
on, unable to adopt. That population has no analogue under contagion, and it is
measurable.

Three arms, all with and without the change-agent minority, in two regimes:

  piecemeal          elements_only (this model)
  simple contagion   whole_package, adopted on contact
  complex contagion  whole_package_gated with an endogenous trigger, so the
                     package arrives as a unit but adoption waits until a share
                     of neighbours already hold or show it. This is a complex-
                     contagion analogue built from this engine's parts, not a
                     reimplementation of any specific published model, and is
                     reported as such.

Measures, per big thing, among agents not manifest for it:
  partial_holder  holds at least one but not all required elements. The
                  population that only exists when the object is composite.
  full_not_manifest  holds every required element but is not manifest. Exists
                  under gating in any arm, so it is reported separately rather
                  than folded into the carrier count.

  ABM_REPS=200 ABM_PARTS=piecemeal,simple,complex python explore_contagion_contrast.py
"""
import csv, os, statistics as st, time

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
REGIMES = {"permissive": 6, "constrained": 4}
FRACTIONS = [0.0, 0.20]

# Ambient element density matters for this contrast and a pilot at 0.05 was
# misleading. At 0.05 the population starts holding random elements, so partial
# holders appear even under whole-package transmission, where they cannot be
# produced by the process itself. Running at 0 makes the seeded minority the
# only source of anything, which is what isolates what each arm transmits.
# Both are reported: 0 for the clean contrast, 0.05 because it is the setting
# the build's change-agent stage uses.
DENSITIES = [0.0, 0.05]

# arm -> config overrides layered on the change-agent phase
ARMS = {
    "piecemeal": {"transmissibility_mode": "elements_only"},
    "simple-contagion": {"transmissibility_mode": "whole_package"},
    "complex-contagion-0.3": {"transmissibility_mode": "whole_package_gated",
                              "trigger_type": "endogenous",
                              "endogenous_trigger_threshold": 0.3},
    "complex-contagion-0.5": {"transmissibility_mode": "whole_package_gated",
                              "trigger_type": "endogenous",
                              "endogenous_trigger_threshold": 0.5},
}
PARTS = set(os.environ.get("ABM_PARTS", ",".join(ARMS)).split(","))

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-contagion-contrast"))
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, f"LOG-{'-'.join(sorted(PARTS))}.md"), "w")


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


def one_run(ov, seed):
    w = World(P.config_for_phase("change-agent", {**ov, "seed": seed}))
    w.run()
    s = summarize_history(w.history, [b.label for b in w.big_things])
    n = len(w.agents)
    partial, full_nm = [], []
    for bt in w.big_things:
        rs = bt.required_set
        p = f = 0
        for a in w.agents:
            if bt.bid in a.manifest:
                continue
            k = len(a.held & rs)
            if k == 0:
                continue
            if k < len(rs):
                p += 1
            else:
                f += 1
        partial.append(p / n)
        full_nm.append(f / n)
    return {"final": s["final_manifest_share"],
            "partial_holder": st.mean(partial),
            "full_not_manifest": st.mean(full_nm)}


FIELDS = ["final", "partial_holder", "full_not_manifest"]


def cell(tag, ov, raw):
    vals = {k: [] for k in FIELDS}
    for r in range(REPS):
        row = one_run(ov, r)
        raw.append({"cell": tag, "rep": r, "seed": r,
                    **{k: round(v, 4) for k, v in row.items()}})
        for k in FIELDS:
            vals[k].append(row[k])
    out = {k: round(st.mean(v), 4) for k, v in vals.items()}
    out["final_sd"] = round(st.pstdev(vals["final"]), 4)
    out["n"] = REPS
    return out


def main():
    log(f"# Change agents under composition versus contagion  ({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    log("Question 1: does the seeded minority fail in every arm? (expected yes, "
        "which concedes the overlap)")
    log("Question 2: does the partial-holder population exist in every arm? "
        "(expected only where the object is composite)")
    raw, agg = [], []
    for dens in DENSITIES:
        log(f"\n--- ambient element density {dens:g}"
            + ("   (minority is the only source)" if dens == 0 else "   (build setting)"))
        for arm in [a for a in ARMS if a in PARTS]:
            for reg, cap in REGIMES.items():
                res = {}
                for f in FRACTIONS:
                    tag = f"{arm}/d{dens:g}/{reg}/frac{f}"
                    a = cell(tag, {**ARMS[arm], "capacity": cap,
                                   "initial_element_density": dens,
                                   "change_agent_fraction": f}, raw)
                    agg.append({"arm": arm, "density": dens, "regime": reg,
                                "capacity": cap, "change_agent_fraction": f, **a})
                    res[f] = a
                    write(agg, f"contrast_{arm}.csv")
                    write(raw, f"contrast_{arm}_raw.csv")
                lift = res[0.20]["final"] - res[0.0]["final"]
                log(f"  {arm:22s} {reg:12s} none={res[0.0]['final']:.4f} "
                    f"minority={res[0.20]['final']:.4f} lift={lift:+.4f}   "
                    f"partial-holders={res[0.20]['partial_holder']:.4f} "
                    f"full-not-manifest={res[0.20]['full_not_manifest']:.4f}")
    log("\nDONE.")
    LOG.close()


if __name__ == "__main__":
    main()
