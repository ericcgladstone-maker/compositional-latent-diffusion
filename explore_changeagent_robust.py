#!/usr/bin/env python3
"""Does the change-agent result survive a larger population and other topologies?

The change-agent analysis runs at 100 agents on a small-world graph of mean
degree 6. The scale confirmation from 2026-07-30 covers the transmissibility
modes only and never touches the change-agent scenario, so the finding the
argument leads with has not been checked outside that one setting. A result
about seeding a fraction of a population invites exactly that question, and a
fifth of 100 agents is 20 agents.

Design: the seeded share crossed with two capacity regimes, two population
sizes, and three topologies. The comparison of interest in every cell is the
same one: adoption with the minority against adoption without it, and against
what adoption would be if the seeded adopters merely persisted and recruited
nobody, which is the no-minority baseline plus the share the minority itself
contributes at the first tick.

  ABM_REPS=200 ABM_PARTS=small_world,random,ring_lattice python explore_changeagent_robust.py
"""
import csv, os, statistics as st, time

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
REGIMES = {"permissive": 6, "constrained": 4}
FRACTIONS = [0.0, 0.20]
SIZES = [100, 500]
TOPOLOGIES = ["small_world", "random", "ring_lattice"]
PARTS = set(os.environ.get("ABM_PARTS", ",".join(TOPOLOGIES)).split(","))

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-changeagent-robust"))
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
    per_bt = [sum(1 for a in w.agents
                  if (a.held & bt.required_set) and bt.bid not in a.manifest) / n
              for bt in w.big_things]
    return {"final": s["final_manifest_share"], "carrier_per_bt": st.mean(per_bt),
            "n_big_things": len(w.big_things)}


FIELDS = ["final", "carrier_per_bt"]


def cell(tag, ov, raw):
    vals = {k: [] for k in FIELDS}
    nbt = None
    for r in range(REPS):
        row = one_run(ov, r)
        nbt = row["n_big_things"]
        raw.append({"cell": tag, "rep": r, "seed": r,
                    **{k: round(row[k], 4) for k in FIELDS}})
        for k in FIELDS:
            vals[k].append(row[k])
    out = {k: round(st.mean(v), 4) for k, v in vals.items()}
    out["final_sd"] = round(st.pstdev(vals["final"]), 4)
    out["n_big_things"] = nbt
    out["n"] = REPS
    return out


def main():
    log(f"# Change agents: robustness to population size and topology  "
        f"({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    log("'expected if seed persists' = no-minority adoption plus the seeded share "
        "divided by the number of big things, which is what the minority contributes "
        "at the first tick before any transmission.")
    raw, agg = [], []
    for topo in [t for t in TOPOLOGIES if t in PARTS]:
        for N in SIZES:
            for reg, cap in REGIMES.items():
                res = {}
                for f in FRACTIONS:
                    tag = f"{topo}/N{N}/{reg}/frac{f}"
                    a = cell(tag, {"topology": topo, "n_agents": N, "capacity": cap,
                                   "change_agent_fraction": f}, raw)
                    agg.append({"topology": topo, "n_agents": N, "regime": reg,
                                "capacity": cap, "change_agent_fraction": f, **a})
                    res[f] = a
                    write(agg, f"robust_{topo}.csv")
                    write(raw, f"robust_{topo}_raw.csv")
                base = res[0.0]["final"]
                obs = res[0.20]["final"]
                nbt = res[0.20]["n_big_things"]
                expect = base + 0.20 / nbt
                log(f"  {topo:12s} N={N:<4} {reg:12s} none={base:.4f} "
                    f"minority={obs:.4f} lift={obs - base:+.4f}   "
                    f"expected-if-seed-persists={expect:.4f} "
                    f"shortfall={obs - expect:+.4f}   "
                    f"carriers={res[0.20]['carrier_per_bt']:.4f}")
    log("\nDONE.")
    LOG.close()


if __name__ == "__main__":
    main()
