#!/usr/bin/env python3
"""Is the tie-strength result about structure, or about dose?

The build reports adoption rising from 0.50 to 0.72 as the strong-tie fraction
goes from 0 to 0.3, and reads it as repeated contact between the same agents
supporting assembly. The implementation makes that reading unidentified. Weak
ties carry weight 0.1 and strong ties 1.0, and send probability is multiplied by
the tie weight, so mean transmission probability is

    transmission_prob x (0.1 + 0.9 x strong_tie_fraction)

which rises from 0.1x to 0.37x of the base rate across that sweep. Raising the
strong-tie fraction raises total transmission by about 3.7 times at the same
time as it changes relational structure. Either could produce the result.

Two arms:
  as-is       the sweep as the build runs it
  normalised  transmission_prob rescaled by 0.37 / (0.1 + 0.9 x fraction) so mean
              send probability is held at the value it takes at fraction 0.3,
              leaving only the structural difference

Elements actually acquired are counted in the engine, so the normalisation is
checked rather than assumed. If adoption still rises in the normalised arm, the
structural reading survives. If it flattens, the original result was dose.

  ABM_REPS=200 python explore_tiestrength_matched.py
"""
import csv, os, statistics as st, time

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
PHASE = "V2-tiestrength"
FRACTIONS = [0.0, 0.05, 0.1, 0.2, 0.3]
WEAK, STRONG = 0.1, 1.0

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-tiestrength-matched"))
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


def mean_multiplier(frac):
    return WEAK + (STRONG - WEAK) * frac


def one_run(ov, seed):
    w = World(P.config_for_phase(PHASE, {**ov, "seed": seed}))
    w.run()
    s = summarize_history(w.history, [b.label for b in w.big_things])
    return {"final": s["final_manifest_share"],
            "lapse_rate": s["lapse_rate"],
            "elements_per_agent": w.elements_added / len(w.agents)}


FIELDS = ["final", "lapse_rate", "elements_per_agent"]


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
    base_p = P.config_for_phase(PHASE, {})["transmission_prob"]
    ref = mean_multiplier(max(FRACTIONS))
    log(f"# Tie strength, dose held constant  ({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    log(f"base transmission_prob={base_p}; weak tie weight {WEAK}, strong {STRONG}")
    log(f"mean send multiplier = {WEAK} + {STRONG - WEAK} x fraction, so the as-is "
        f"sweep raises mean send probability {mean_multiplier(max(FRACTIONS)) / mean_multiplier(min(FRACTIONS)):.1f}x "
        f"across the range")
    log(f"normalised arm rescales transmission_prob by {ref:g} / (mean multiplier)")
    raw, agg = [], []
    for arm in ("as-is", "normalised"):
        log(f"\n  {arm}")
        for f in FRACTIONS:
            ov = {"strong_tie_fraction": f}
            if arm == "normalised":
                ov["transmission_prob"] = base_p * ref / mean_multiplier(f)
            a = cell(f"{arm}/frac{f}", ov, raw)
            agg.append({"arm": arm, "strong_tie_fraction": f,
                        "transmission_prob": round(ov.get("transmission_prob", base_p), 6),
                        **a})
            log(f"    fraction={f:<5} transmission_prob={ov.get('transmission_prob', base_p):.4f}  "
                f"final={a['final']:.4f}  lapse={a['lapse_rate']:.4f}  "
                f"elem/agent={a['elements_per_agent']:.2f}")
            write(agg, "tiestrength_matched.csv")
            write(raw, "tiestrength_matched_raw.csv")
        rows = [r for r in agg if r["arm"] == arm]
        lo, hi = rows[0], rows[-1]
        log(f"    -> adoption {lo['final']:.4f} to {hi['final']:.4f} "
            f"({hi['final'] - lo['final']:+.4f}) while material moved goes "
            f"{lo['elements_per_agent']:.2f} to {hi['elements_per_agent']:.2f}")
    log("\nDONE.")
    LOG.close()


if __name__ == "__main__":
    main()
