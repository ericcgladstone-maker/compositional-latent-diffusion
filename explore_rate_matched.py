#!/usr/bin/env python3
"""Is the transmissibility gap about assembly, or about how much moves per contact?

The cue-gated comparison is the document's cleanest evidence that moving an
assembled set as a unit differs from requiring distributed assembly: adoption is
0.65 under elements_only against 0.86 under whole_package_gated, with both
waiting for the same cue. That comparison has an unexamined asymmetry. Per
contact from a manifest sender:

  elements_only        one randomly chosen element, delivered with probability
                       transmission_prob (0.1 at the operating point)
  whole_package_gated  every one of the requirement_size elements (4), delivered
                       with no probability check at all

So the package arm moves roughly forty times as much material per contact. Some
of the gap may be throughput rather than assembly.

Matching analytically does not work. Measured over a whole run the package arm
moves about 3.7 times the baseline material, not 40, because receivers saturate,
capacity binds and the piecemeal arm gets many contacts. So instead of one
"matched" point this traces a dose-response curve for each arm and compares them
at equal material moved.

  elements_only        transmission_prob swept, which sets its dose
  whole_package_gated  whole_package_transfer_prob swept, which sets its dose

Both arms record elements actually acquired per agent, counted in the engine, so
dose is measured rather than assumed. If at equal measured dose the package arm
still reaches higher adoption, co-transmission and assembly are doing the work.
If the two curves coincide, the original comparison was measuring bandwidth.

  ABM_REPS=200 python explore_rate_matched.py
"""
import csv, os, statistics as st, time

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
PHASE = "V1-W"
TRANSFER_PROBS = [1.0, 0.5, 0.25, 0.1, 0.05, 0.025, 0.01, 0.005]
# doses for the piecemeal arm, so it has a curve to be compared against
PIECEMEAL_PROBS = [0.025, 0.05, 0.1, 0.2, 0.4]

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-rate-matched"))
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "LOG.md"), "w")


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
    w = World(P.config_for_phase(PHASE, {**ov, "seed": seed}))
    w.run()
    s = summarize_history(w.history, [b.label for b in w.big_things])
    n = len(w.agents)
    per_bt = [sum(1 for a in w.agents
                  if (a.held & bt.required_set) and bt.bid not in a.manifest) / n
              for bt in w.big_things]
    return {"final": s["final_manifest_share"], "carrier_per_bt": st.mean(per_bt),
            "obs_gap": w.history[-1]["observability_gap"],
            # material actually moved: the empirical check on the rate match
            "elements_added": w.elements_added,
            "elements_per_agent": w.elements_added / n}


FIELDS = ["final", "carrier_per_bt", "obs_gap", "elements_added", "elements_per_agent"]


def cell(tag, ov, raw):
    vals = {k: [] for k in FIELDS}
    for r in range(REPS):
        row = one_run(ov, r)
        raw.append({"cell": tag, "rep": r, "seed": r,
                    **{k: round(row[k], 4) for k in FIELDS}})
        for k in FIELDS:
            vals[k].append(row[k])
    out = {k: round(st.mean(v), 4) for k, v in vals.items()}
    out["final_sd"] = round(st.pstdev(vals["final"]), 4)
    out["n"] = REPS
    return out


def main():
    cfg = P.config_for_phase(PHASE, {})
    p, R = cfg["transmission_prob"], cfg["requirement_size"]
    matched = round(p / R, 6)
    log(f"# Rate-matched transmissibility comparison  ({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    log(f"phase {PHASE}: transmission_prob={p}, requirement_size={R}")
    log(f"a piecemeal contact moves {p} elements in expectation, an ungated package "
        f"contact moves {R}, a ratio of {R / p:.0f}")
    log(f"rate-matched transfer probability = transmission_prob / requirement_size "
        f"= {matched}")
    raw, agg = [], []

    base = None
    log("\n  elements_only, transmission_prob swept (the piecemeal dose-response curve)")
    for tp in PIECEMEAL_PROBS:
        a = cell(f"elements_only/p{tp}",
                 {"transmissibility_mode": "elements_only", "transmission_prob": tp}, raw)
        agg.append({"mode": "elements_only", "transmission_prob": tp,
                    "whole_package_transfer_prob": "", **a})
        if abs(tp - p) < 1e-9:
            base = a
        log(f"    transmission_prob={tp:<6} final={a['final']:.4f}  "
            f"carriers={a['carrier_per_bt']:.4f}  "
            f"elem/agent={a['elements_per_agent']:.2f}"
            f"{'  <- operating point' if abs(tp - p) < 1e-9 else ''}")
        write(agg, "rate_matched.csv"); write(raw, "rate_matched_raw.csv")

    for mode in ("whole_package_gated", "whole_package"):
        log(f"\n  {mode}, whole_package_transfer_prob swept")
        probs = TRANSFER_PROBS if mode == "whole_package_gated" else [1.0]
        for tp in probs:
            a = cell(f"{mode}/tp{tp}", {"transmissibility_mode": mode,
                                        "whole_package_transfer_prob": tp}, raw)
            agg.append({"mode": mode, "transmission_prob": p,
                        "whole_package_transfer_prob": tp, **a})
            log(f"    transfer_prob={tp:<6} final={a['final']:.4f}  "
                f"carriers={a['carrier_per_bt']:.4f}  "
                f"elem/agent={a['elements_per_agent']:.2f} "
                f"({a['elements_per_agent'] / base['elements_per_agent']:.2f}x operating point)"
                f"{'  <- original' if tp == 1.0 else ''}")
            write(agg, "rate_matched.csv"); write(raw, "rate_matched_raw.csv")

    log("\nDONE.")
    LOG.close()


if __name__ == "__main__":
    main()
