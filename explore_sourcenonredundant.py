#!/usr/bin/env python3
"""Three readiness rules over one token history.

The count-only experiment compared compositional readiness against a count rule
that allows duplicates. That is the weakest possible accumulation rule, and the
nonredundant-information literature does not use it: there, a second exposure
from the SAME neighbour adds nothing while one from a new neighbour does. The
obvious objection is that we defeated a straw comparator.

So the arm that literature actually uses is added here, and all three are run
over the identical token history, including source metadata:

  count           at least k relevant retained tokens, duplicates allowed
  source          at least k relevant retained tokens from k DISTINCT senders
  compositional   at least k DISTINCT required component identities

Source diversity and content identity are logically independent: three tokens
of the same type from three neighbours satisfy source but not compositional,
and three distinct types from one neighbour satisfy compositional but not
source. The comparison therefore separates them.

`verify_token_arms.py` asserts tick-by-tick identity of the full token state
across all three arms, so the readiness function is the only difference.

  ABM_REPS=200 python explore_sourcenonredundant.py <rule>
"""
import csv, math, os, statistics as st, sys, time

from token_model import TokenWorld

REPS = int(os.environ.get("ABM_REPS", "200"))
FLOWS = {"low": 0.05, "high": 0.20}
CAPACITIES = (6, 5)
LOSSES = (0.0, 0.01)
RULES = ("compositional", "count", "source")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", "20260816-sourcenonredundant"))
os.makedirs(OUT, exist_ok=True)

FIELDS = ["adoption", "carrier_per_bt", "evictions_per_agent",
          "completions_per_agent", "mean_duplicates", "mean_distinct_types",
          "mean_distinct_sources"]


def cfg_for(rule, flow, cap, loss, seed):
    c = dict(seed=seed, capacity=cap, loss_rate=loss,
             transmission_prob=FLOWS[flow], sufficiency_rule=rule)
    if rule == "count":
        c["count_threshold"] = 3
    return c


def cell(rule, flow, cap, loss, raw, tag, log):
    vals = {k: [] for k in FIELDS}
    for r in range(REPS):
        m = TokenWorld(cfg_for(rule, flow, cap, loss, r)).run().history[-1]
        raw.append({"cell": tag, "rep": r, "seed": r,
                    **{k: round(m[k], 4) for k in FIELDS}})
        for k in FIELDS:
            vals[k].append(m[k])
    out = {k: round(st.mean(v), 4) for k, v in vals.items()}
    out["adoption_sd"] = round(st.pstdev(vals["adoption"]), 4)
    out["n"] = REPS
    return out


def main():
    rule = sys.argv[1]
    assert rule in RULES, rule
    log_path = os.path.join(OUT, f"LOG-{rule}.md")
    LOG = open(log_path, "w")

    def log(*a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

    log(f"# {rule} readiness over the shared token history  ({REPS} paired reps)")
    log(f"# {time.strftime('%Y-%m-%d %H:%M:%S')}")
    raw, agg = [], []
    for cap in CAPACITIES:
        for loss in LOSSES:
            res = {}
            for flow in FLOWS:
                tag = f"{rule}/c{cap}/l{loss}/{flow}"
                a = cell(rule, flow, cap, loss, raw, tag, log)
                agg.append({"rule": rule, "capacity": cap, "loss_rate": loss,
                            "flow": flow, "transmission_prob": FLOWS[flow], **a})
                res[flow] = a
                for rows, name in ((agg, f"sourcecmp_{rule}.csv"),
                                   (raw, f"sourcecmp_{rule}_raw.csv")):
                    with open(os.path.join(OUT, name), "w", newline="") as f:
                        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                        w.writeheader(); w.writerows(rows)
            d = res["high"]["adoption"] - res["low"]["adoption"]
            log(f"  cap {cap} loss {loss:<5} low={res['low']['adoption']:.4f} "
                f"high={res['high']['adoption']:.4f}  return={d:+.4f}  "
                f"carriers(high)={res['high']['carrier_per_bt']:.4f}  "
                f"evict/agent(high)={res['high']['evictions_per_agent']:.1f}")
    log("DONE.")


if __name__ == "__main__":
    main()
