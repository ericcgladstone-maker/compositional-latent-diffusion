#!/usr/bin/env python3
"""Does requiring DISTINCT prerequisites do work, or is it finite-memory congestion?

Both arms share one token-memory retention process. Capacity counts tokens,
eviction removes tokens, loss removes tokens, duplicates are retainable. The
only difference is the readiness function:

  compositional      at least k DISTINCT required types
  count-only         at least k required TOKENS, duplicates included
  count-calibrated   count-only with a threshold chosen so the two arms match
                     under a NON-binding retention condition, which removes the
                     objection that the literal k-versus-k comparison simply
                     gives count-only an easier threshold

`verify_token_arms.py` asserts the two arms produce identical token trajectories,
so any adoption difference is downstream of the readiness rule alone.

The estimand that decides the paper's framing is the interaction

    (A_comp,high - A_comp,low) - (A_count,high - A_count,low)

If the compositional arm's negative return to flow is markedly stronger, then
requiring heterogeneous prerequisites amplifies the retention bottleneck and the
mechanism is compositional. If the two arms behave the same, the mechanism is
finite-memory congestion and "compositional" should come out of the framing.

  ABM_REPS=200 python explore_countonly.py calibrate
  ABM_REPS=200 ABM_PARTS=compositional python explore_countonly.py run <kc>
"""
import csv, os, statistics as st, sys, time

from token_model import TokenWorld

REPS = int(os.environ.get("ABM_REPS", "30"))
FLOWS = {"low": 0.05, "high": 0.20}
CAPACITIES = (6, 5)
LOSSES = (0.0, 0.01)
RULES = ("compositional", "count-literal", "count-calibrated")
PARTS = set(os.environ.get("ABM_PARTS", ",".join(RULES)).split(","))

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-countonly"))
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, f"LOG-{'-'.join(sorted(PARTS))}.md"), "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n"); LOG.flush()


def write(rows, name):
    if not rows:
        return
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


FIELDS = ["adoption", "carrier_per_bt", "evictions_per_agent",
          "completions_per_agent", "mean_duplicates", "mean_distinct_types"]


def cfg_for(rule, kc, flow, cap, loss, seed):
    c = dict(seed=seed, capacity=cap, loss_rate=loss,
             transmission_prob=FLOWS[flow])
    if rule == "compositional":
        c["sufficiency_rule"] = "compositional"
    else:
        c["sufficiency_rule"] = "count"
        c["count_threshold"] = 3 if rule == "count-literal" else kc
    return c


def cell(rule, kc, flow, cap, loss, reps, raw=None, tag=""):
    vals = {k: [] for k in FIELDS}
    for r in range(reps):
        w = TokenWorld(cfg_for(rule, kc, flow, cap, loss, r)).run()
        m = w.history[-1]
        if raw is not None:
            raw.append({"cell": tag, "rep": r, "seed": r,
                        **{k: round(m[k], 4) for k in FIELDS}})
        for k in FIELDS:
            vals[k].append(m[k])
    out = {k: round(st.mean(v), 4) for k, v in vals.items()}
    out["adoption_sd"] = round(st.pstdev(vals["adoption"]), 4)
    out["n"] = reps
    return out


def calibrate():
    """Pick the calibrated count threshold under NON-binding retention."""
    log(f"# count-only threshold calibration  {STAMP}")
    log("reference condition: capacity 10, no loss, flow low, retention not binding")
    comp = cell("compositional", None, "low", 10, 0.0, 12)
    log(f"  compositional k=3 -> adoption {comp['adoption']:.4f}")
    best, bestd = None, 9e9
    for kc in (3, 4, 5, 6, 7):
        a = cell("count-calibrated", kc, "low", 10, 0.0, 12)
        d = abs(a["adoption"] - comp["adoption"])
        log(f"  count threshold {kc} -> adoption {a['adoption']:.4f}  |gap| {d:.4f}")
        if d < bestd:
            best, bestd = kc, d
    log(f"\ncalibrated count threshold = {best} (closest match under non-binding retention)")


def run(kc):
    log(f"# Compositional versus count-only readiness  ({REPS} paired reps)  {STAMP}")
    log(f"out: {OUT}")
    log(f"shared token retention; only the readiness rule differs. "
        f"calibrated count threshold = {kc}")
    raw, agg = [], []
    for rule in [r for r in RULES if r in PARTS]:
        log(f"\n## {rule}")
        for cap in CAPACITIES:
            for loss in LOSSES:
                res = {}
                for flow in FLOWS:
                    tag = f"{rule}/c{cap}/l{loss}/{flow}"
                    a = cell(rule, kc, flow, cap, loss, REPS, raw, tag)
                    agg.append({"rule": rule, "capacity": cap, "loss_rate": loss,
                                "flow": flow, "transmission_prob": FLOWS[flow], **a})
                    res[flow] = a
                    write(agg, f"countonly_{rule}.csv")
                    write(raw, f"countonly_{rule}_raw.csv")
                d = res["high"]["adoption"] - res["low"]["adoption"]
                log(f"  cap {cap} loss {loss:<5} low={res['low']['adoption']:.4f} "
                    f"high={res['high']['adoption']:.4f}  return to flow={d:+.4f}   "
                    f"carriers(high)={res['high']['carrier_per_bt']:.4f}  "
                    f"evictions/agent={res['high']['evictions_per_agent']:.1f}")
    log("\nDONE.")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "calibrate"
    if what == "calibrate":
        calibrate()
    else:
        run(int(sys.argv[2]))
