#!/usr/bin/env python3
"""Why an equipped, motivated minority fails to move adoption.

The build sweeps change_agent_fraction from 0.05 to 0.20 and finds adoption flat.
That establishes insensitivity to HOW MANY change agents there are, not whether
having them matters at all: there is no zero condition in that phase, and the V1
runs are not a usable control because they use a different ambient element
density (0.15 against 0.05). This supplies the missing control and the rest of
the evidence the claim needs.

Four parts, each answering the next objection a reader would raise:

  A  Do they lift adoption at all?  fraction 0 through 0.20, in a permissive and
     a constrained regime. Also measures the carrier fraction, so we can say what
     the minority produces instead of adopters.
  B  Are they simply too quiet?  sweep change_agent_evangelism, which multiplies
     their send probability.
  C  What is it about them that fails?  the same minority under whole-package
     transmission, where they pass the assembled package rather than components.
     This is the mechanism test: if they work there and not under elements-only,
     the failure is a property of the spread unit and not of the agents.
  D  Is it an artifact of the scheduled trigger?  repeat under endogenous
     triggering.

Every cell is 200 replications with deterministic seeds 0..REPS-1, and every
per-replication row is written out so each mean can be re-derived by hand.

  ABM_REPS=200 ABM_PARTS=A,B,C,D python explore_changeagent.py
"""
import csv, os, statistics as st, time

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
PARTS = set(os.environ.get("ABM_PARTS", "A,B,C,D").split(","))

# permissive: unaided adoption is high, so failure can only show as "no lift"
# constrained: unaided adoption is low, so failure shows as a curve that stays low
REGIMES = {"permissive": 6, "constrained": 4}
FRACTIONS = [0.0, 0.05, 0.10, 0.15, 0.20]
EVANGELISM = [1.0, 2.0, 4.0, 8.0]

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-changeagent"))
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
    """Adoption plus the carrier measures, from a single run."""
    cfg = P.config_for_phase("change-agent", {**ov, "seed": seed})
    w = World(cfg)
    w.run()
    s = summarize_history(w.history, [b.label for b in w.big_things])
    n = len(w.agents)
    total = set()
    for bt in w.big_things:
        total |= bt.required_set
    # carrier: holds at least one of a big thing's elements, so can pass them on,
    # while not being manifest for it. Same definition as the W3 analysis.
    per_bt = [sum(1 for a in w.agents
                  if (a.held & bt.required_set) and bt.bid not in a.manifest) / n
              for bt in w.big_things]
    return {"final": s["final_manifest_share"], "peak": s["peak_manifest_share"],
            "overshoot": s["overshoot"], "lapse_rate": s["lapse_rate"],
            "carrier_per_bt": st.mean(per_bt),
            "pure_carrier": sum(1 for a in w.agents
                                if (a.held & total) and not a.manifest) / n}


FIELDS = ["final", "peak", "overshoot", "lapse_rate", "carrier_per_bt", "pure_carrier"]


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
    log(f"# Change agents: does an equipped minority move adoption?  "
        f"({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    log("base: phase change-agent (elements_only, ambient element density 0.05). "
        "'constrained' lowers capacity so unaided diffusion is weak.")

    if "A" in PARTS:
        log("\n## A  fraction sweep including the missing zero control")
        raw, agg = [], []
        for reg, cap in REGIMES.items():
            line = []
            for f in FRACTIONS:
                tag = f"A/{reg}/frac{f}"
                a = cell(tag, {"capacity": cap, "change_agent_fraction": f}, raw)
                agg.append({"part": "A", "regime": reg, "capacity": cap,
                            "change_agent_fraction": f, "scenario": True, **a})
                line.append((f, a["final"]))
                write(agg, "a_fraction.csv"); write(raw, "a_fraction_raw.csv")
            # independent control: the scenario switched off entirely
            tag = f"A/{reg}/no-scenario"
            a = cell(tag, {"capacity": cap, "change_agent_scenario": False}, raw)
            agg.append({"part": "A", "regime": reg, "capacity": cap,
                        "change_agent_fraction": None, "scenario": False, **a})
            write(agg, "a_fraction.csv"); write(raw, "a_fraction_raw.csv")
            log(f"  {reg:12s} " + "  ".join(f"f{f:g}={v:.4f}" for f, v in line) +
                f"   [scenario off = {a['final']:.4f}]")
            base = dict(line)[0.0]
            log(f"  {'':12s} lift over the zero control at the largest fraction: "
                f"{dict(line)[0.20] - base:+.4f}")
        log("  carrier fraction (what the minority produces instead of adopters):")
        for r in agg:
            if r["change_agent_fraction"] in (0.0, 0.20):
                log(f"    {r['regime']:12s} fraction {r['change_agent_fraction']}: "
                    f"adoption {r['final']:.4f}  carriers {r['carrier_per_bt']:.4f}")

    if "B" in PARTS:
        log("\n## B  are they too quiet?  evangelism multiplies their send probability")
        raw, agg = [], []
        for reg, cap in REGIMES.items():
            line = []
            for e in EVANGELISM:
                tag = f"B/{reg}/evang{e}"
                a = cell(tag, {"capacity": cap, "change_agent_fraction": 0.20,
                               "change_agent_evangelism": e}, raw)
                agg.append({"part": "B", "regime": reg, "capacity": cap,
                            "change_agent_evangelism": e, **a})
                line.append((e, a["final"]))
                write(agg, "b_evangelism.csv"); write(raw, "b_evangelism_raw.csv")
            log(f"  {reg:12s} " + "  ".join(f"x{e:g}={v:.4f}" for e, v in line))

    if "C" in PARTS:
        log("\n## C  mechanism: the same minority under whole-package transmission")
        raw, agg = [], []
        for reg, cap in REGIMES.items():
            for mode in ("elements_only", "whole_package"):
                res = {}
                for f in (0.0, 0.20):
                    tag = f"C/{reg}/{mode}/frac{f}"
                    a = cell(tag, {"capacity": cap, "change_agent_fraction": f,
                                   "transmissibility_mode": mode}, raw)
                    agg.append({"part": "C", "regime": reg, "capacity": cap,
                                "transmissibility_mode": mode,
                                "change_agent_fraction": f, **a})
                    res[f] = a["final"]
                    write(agg, "c_mechanism.csv"); write(raw, "c_mechanism_raw.csv")
                log(f"  {reg:12s} {mode:15s} none={res[0.0]:.4f}  "
                    f"minority={res[0.20]:.4f}  lift={res[0.20]-res[0.0]:+.4f}")

    if "D" in PARTS:
        log("\n## D  does it depend on the scheduled trigger?")
        raw, agg = [], []
        for reg, cap in REGIMES.items():
            for trig in ("exogenous", "endogenous"):
                res = {}
                for f in (0.0, 0.20):
                    tag = f"D/{reg}/{trig}/frac{f}"
                    a = cell(tag, {"capacity": cap, "change_agent_fraction": f,
                                   "trigger_type": trig}, raw)
                    agg.append({"part": "D", "regime": reg, "capacity": cap,
                                "trigger_type": trig,
                                "change_agent_fraction": f, **a})
                    res[f] = a["final"]
                    write(agg, "d_trigger.csv"); write(raw, "d_trigger_raw.csv")
                log(f"  {reg:12s} {trig:11s} none={res[0.0]:.4f}  "
                    f"minority={res[0.20]:.4f}  lift={res[0.20]-res[0.0]:+.4f}")

    log("\nDONE.")
    LOG.close()


if __name__ == "__main__":
    main()
