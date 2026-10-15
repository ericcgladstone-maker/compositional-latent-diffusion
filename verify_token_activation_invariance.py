#!/usr/bin/env python3
"""The three-arm result does not depend on the activation rule: a check, not evidence.

Round-4 comment C18 asks what happens if a ready actor manifests immediately. For the
token-memory comparison the answer is analytic. In `token_model.py`:

  * transmission and retention draw from `rng`, activation from a separate `arng`;
  * manifestation never feeds back into transmission or retention;
  * runs last exactly `run_length` = 1000 ticks, a multiple of the scheduled
    trigger interval (100), so the scheduled trigger also fires on the final tick;
  * trigger reach is 1 and adoption is reversible.

So the token history is identical under either rule, and final adoption equals the
share of actor-object pairs that are ready at tick 1000 in both. This script confirms
that, replication by replication, for every cell of the three-arm design, and also
confirms that the scheduled arm reproduces the canonical per-rep output exactly.

Exit 0 only if every per-replication adoption value is identical across the two
activation rules and the scheduled values match the canonical raw CSVs.

  python verify_token_activation_invariance.py
"""
import csv, glob, math, os, statistics as st, sys
from multiprocessing import Pool

from token_model import TokenWorld

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.join(HERE, "results", "20260816-sourcenonredundant")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", "20261006-token-activation-invariance"))
REPS = 200
FLOWS = {"low": 0.05, "high": 0.20}
RULES = ("compositional", "source", "count")
CAPACITIES = (6, 5)
LOSSES = (0.0, 0.01)
TRIGGERS = {"scheduled": 100, "immediate": 1}


def one(job):
    trig, rule, cap, loss, flow, seed = job
    c = dict(seed=seed, capacity=cap, loss_rate=loss, transmission_prob=FLOWS[flow],
             sufficiency_rule=rule, trigger_time=TRIGGERS[trig])
    if rule == "count":
        c["count_threshold"] = 3
    w = TokenWorld(c)
    assert w.cfg["run_length"] % 100 == 0, "invariance argument needs run_length divisible by 100"
    return job, w.run().history[-1]["adoption"]


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [(t, r, c, l, f, s) for t in TRIGGERS for r in RULES for c in CAPACITIES
            for l in LOSSES for f in FLOWS for s in range(REPS)]
    res = {}
    with Pool(max(1, (os.cpu_count() or 2) - 1)) as p:
        for job, v in p.imap_unordered(one, jobs, chunksize=20):
            res[job] = v

    canon = {}
    for f in glob.glob(os.path.join(CANON, "sourcecmp_*_raw.csv")):
        for r in csv.DictReader(open(f)):
            canon[(r["cell"], int(r["rep"]))] = float(r["adoption"])

    rows, bad = [], 0
    for rule in RULES:
        for cap in CAPACITIES:
            for loss in LOSSES:
                d_sched, d_imm, max_abs, canon_mis = [], [], 0.0, 0
                for s in range(REPS):
                    v = {(t, f): res[(t, rule, cap, loss, f, s)] for t in TRIGGERS for f in FLOWS}
                    for f in FLOWS:
                        max_abs = max(max_abs, abs(v[("scheduled", f)] - v[("immediate", f)]))
                        tag = f"{rule}/c{cap}/l{loss}/{f}"
                        if round(v[("scheduled", f)], 4) != canon[(tag, s)]:
                            canon_mis += 1
                    d_sched.append(v[("scheduled", "high")] - v[("scheduled", "low")])
                    d_imm.append(v[("immediate", "high")] - v[("immediate", "low")])
                ok = max_abs == 0.0 and canon_mis == 0
                bad += not ok
                se = lambda d: st.pstdev(d) / math.sqrt(len(d))
                rows.append({"rule": rule, "capacity": cap, "loss_rate": loss, "n": REPS,
                             "return_scheduled": round(st.mean(d_sched), 4),
                             "return_immediate": round(st.mean(d_imm), 4),
                             "se_scheduled": round(se(d_sched), 4),
                             "max_abs_per_rep_diff": max_abs,
                             "scheduled_vs_canon_mismatches": canon_mis,
                             "identical": ok})
    with open(os.path.join(OUT, "token_activation_invariance.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)
    with open(os.path.join(OUT, "LOG.md"), "w") as fh:
        fh.write(__doc__ + "\n\n")
        for r in rows:
            fh.write(f"{r}\n")
        fh.write(f"\ncells failing: {bad} of {len(rows)}\n")
    for r in rows:
        print(f"{r['rule']:13s} cap{r['capacity']} loss{r['loss_rate']:<5} "
              f"sched {r['return_scheduled']:+.4f} imm {r['return_immediate']:+.4f} "
              f"max|diff| {r['max_abs_per_rep_diff']} canon-mismatch {r['scheduled_vs_canon_mismatches']}")
    print(f"{len(rows) - bad} of {len(rows)} cells identical and canon-reproducing")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
