#!/usr/bin/env python3
"""Do nonadopters actually carry the diffusion, or merely exist?

A latent-diffusion claim needs two properties, and the second is what stops it
being a restatement of "people consider things before adopting":

  1. the transmissible state can exist in actors who have not adopted
  2. those actors causally participate in onward transmission

Property 1 is already measured: the carrier fraction. Property 2 has never been
tested. `member_gated_transmission` restricts transmission of a big thing's
elements to agents who are manifest for it, which is precisely the counterfactual
in which only adopters transmit and the latent channel is switched off.

The gap between the two conditions is how much of the diffusion runs through
actors who have not adopted. If it is near zero, carriers are a bookkeeping
category rather than part of the process, and the latent-diffusion framing would
not be earned.

Everything else is held fixed: same phase, same capacity sweep, same seeds.

  ABM_REPS=200 python explore_carrier_channel.py
"""
import csv, os, statistics as st, time

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
CAPACITIES = (4, 6)
# The two channels move different amounts of material at the same transmission
# probability (about 10 against 6 elements per agent), so comparing them at one
# parameter setting confounds the channel with the dose. Both are swept instead
# and compared at equal MEASURED material, as with the transmissibility arms.
PROBS = (0.05, 0.1, 0.2, 0.35, 0.5)

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-carrier-channel"))
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "LOG.md"), "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n"); LOG.flush()


def one(cap, gated, prob, seed):
    # Both arms are seeded with a small manifest minority. Without it the closed
    # channel cannot start at all: nobody is manifest at t=0, so nobody may
    # transmit, so nobody becomes manifest. That deadlock would measure a
    # bootstrap artifact rather than the contribution of the latent channel.
    w = World(P.config_for_phase("V1", {
        "capacity": cap, "transmissibility_mode": "elements_only",
        "member_gated_transmission": gated, "transmission_prob": prob,
        "change_agent_scenario": True, "change_agent_fraction": 0.05,
        "seed": seed}))
    w.run()
    s = summarize_history(w.history, [b.label for b in w.big_things])
    n = w.n
    per_bt = [sum(1 for a in w.agents
                  if (a.held & bt.required_set) and bt.bid not in a.manifest) / n
              for bt in w.big_things]
    return {"final": s["final_manifest_share"], "carrier_per_bt": st.mean(per_bt),
            "elements_per_agent": w.elements_added / n}


FIELDS = ["final", "carrier_per_bt", "elements_per_agent"]


def cell(cap, gated, prob, raw, tag):
    vals = {k: [] for k in FIELDS}
    for r in range(REPS):
        row = one(cap, gated, prob, r)
        raw.append({"cell": tag, "rep": r, "seed": r,
                    **{k: round(row[k], 4) for k in FIELDS}})
        for k in FIELDS:
            vals[k].append(row[k])
    out = {k: round(st.mean(v), 4) for k, v in vals.items()}
    out["final_sd"] = round(st.pstdev(vals["final"]), 4)
    out["n"] = REPS
    return out


def main():
    log(f"# How much diffusion runs through nonadopters  ({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    log("open channel: any holder transmits. closed channel: only agents manifest "
        "for a big thing transmit its elements.")
    log("both arms seeded with a manifest minority of 0.05 so the closed channel "
        "can start; without it nothing transmits and adoption is identically zero.")
    raw, agg = [], []
    for cap in CAPACITIES:
        log(f"\n## capacity {cap}")
        for gated, lab in ((False, "open"), (True, "closed")):
            for prob in PROBS:
                tag = f"cap{cap}/{lab}/p{prob}"
                a = cell(cap, gated, prob, raw, tag)
                agg.append({"capacity": cap, "carrier_channel": lab,
                            "transmission_prob": prob, **a})
                with open(os.path.join(OUT, "carrier_channel.csv"), "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(agg[0].keys()))
                    w.writeheader(); w.writerows(agg)
                with open(os.path.join(OUT, "carrier_channel_raw.csv"), "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(raw[0].keys()))
                    w.writeheader(); w.writerows(raw)
                log(f"  {lab:6s} p={prob:<5} adoption={a['final']:.4f}  "
                    f"material/agent={a['elements_per_agent']:.2f}  "
                    f"carriers={a['carrier_per_bt']:.4f}")

    log("\nDONE.")


if __name__ == "__main__":
    main()
