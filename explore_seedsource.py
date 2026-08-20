#!/usr/bin/env python3
"""Does the three-arm result depend on how seeded tokens get their source?

The distinct-sender rule needs a source label for every token, including the
ones present before any transmission. The focal specification gives each seeded
token its own origin, which keeps initialization neutral between the readiness
rules but is an artificial convention. Two alternatives are tested:

  unique       each seeded token is its own origin (focal)
  shared       everything an actor starts with counts as ONE exogenous origin
  social_only  seeded tokens never count toward source diversity at all

The seed mode changes only the source labels. Component histories, eviction,
loss, network, flow and activation are identical across modes, and the
compositional and count arms are invariant to it, which is asserted rather than
assumed. Only the source arm is therefore re-run.

The question is not which convention is preferable. It is whether the
qualitative ordering of returns to flow survives.

  ABM_REPS=200 python explore_seedsource.py <mode>
"""
import csv, math, os, statistics as st, sys

from token_model import TokenWorld

REPS = int(os.environ.get("ABM_REPS", "200"))
FLOWS = {"low": 0.05, "high": 0.20}
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", "20260817-seedsource"))
os.makedirs(OUT, exist_ok=True)
F = ["adoption", "carrier_per_bt", "evictions_per_agent", "mean_distinct_sources"]


def main():
    mode = sys.argv[1]
    raw, agg = [], []
    log = open(os.path.join(OUT, f"LOG-{mode}.md"), "w")

    def w(s):
        print(s, flush=True); log.write(s + "\n"); log.flush()

    w(f"# source arm under seed_source_mode={mode}  ({REPS} paired reps)")
    for cap in (6, 5):
        for loss in (0.0, 0.01):
            res = {}
            for flow in FLOWS:
                vals = {k: [] for k in F}
                for r in range(REPS):
                    m = TokenWorld(dict(seed=r, capacity=cap, loss_rate=loss,
                                        transmission_prob=FLOWS[flow],
                                        sufficiency_rule="source",
                                        seed_source_mode=mode)).run().history[-1]
                    raw.append({"cell": f"source-{mode}/c{cap}/l{loss}/{flow}",
                                "rep": r, **{k: round(m[k], 4) for k in F}})
                    for k in F:
                        vals[k].append(m[k])
                a = {k: round(st.mean(v), 4) for k, v in vals.items()}
                a["adoption_sd"] = round(st.pstdev(vals["adoption"]), 4)
                agg.append({"mode": mode, "capacity": cap, "loss_rate": loss,
                            "flow": flow, "n": REPS, **a})
                res[flow] = vals["adoption"]
            d = [h - l for h, l in zip(res["high"], res["low"])]
            m_, se = st.mean(d), st.pstdev(d) / math.sqrt(len(d))
            w(f"  cap {cap} loss {loss:<5} low={st.mean(res['low']):.4f} "
              f"high={st.mean(res['high']):.4f}  return={m_:+.4f} (SE {se:.4f})")
    for rows_, name in ((agg, f"seedsource_{mode}.csv"), (raw, f"seedsource_{mode}_raw.csv")):
        with open(os.path.join(OUT, name), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows_[0].keys()))
            wr.writeheader(); wr.writerows(rows_)
    w("DONE.")


if __name__ == "__main__":
    main()
