#!/usr/bin/env python3
"""Is the carrier population produced by diffusion, or handed over by seeding?

The adversarial review observed that a carrier needs only ONE relevant element
while nonmanifest, and that at initial density .15 an agent already holds at
least one element of a four-element requirement set with probability
1 - .85**4 = .478 before anything has been transmitted. If so, the reported
endpoint carrier fraction is not something the diffusion process built.

This script settles it at the canonical 200 replications, and adds what the
manuscript needs in order to say something defensible instead:

  1. carrier quantities at t=0 and at the endpoint
  2. the whole carrier trajectory, so persistence can be shown rather than asserted
  3. stricter carrier definitions as sensitivity checks (>=2 relevant, and the
     k-1 distinct variant, which coincides with >=2 here because the shipped
     engine stores distinct types and k=3)
  4. the realized share of successful component transfers whose sender was
     nonmanifest for the object the element serves, which is the quantity that
     actually decides whether nonadopters carry the process

(4) uses counters added to the engine that increment after a transfer has
already succeeded. They draw no random numbers and touch no state. The no-op is
confirmed by reproducing the canonical V1 cell exactly.

  ABM_REPS=200 python explore_carrier_diagnostics.py
"""
import csv, os, statistics as st, time

from abm import phases as P
from abm.model import World

REPS = int(os.environ.get("ABM_REPS", "200"))
# optional: run the same diagnostic under endogenous activation so that
# Figure 2 can show both panels under one regime.
# ABM_TRIGGER=immediate (added 2026-10-06, round-4 comment C18): manifestation as soon
# as readiness is recomputed, i.e. the exogenous trigger firing every tick.
TRIG = {"endogenous": {"trigger_type": "endogenous"},
        "immediate": {"trigger_time": 1}}.get(os.environ.get("ABM_TRIGGER"), {})
HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", os.environ.get("ABM_OUT", f"{STAMP}-carrier-diagnostics"))
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "LOG.md"), "w")

# Trajectory sampling: full per-tick capture over 200 reps is large, and the
# run is 1000 ticks, so sample on a grid that is dense early where the action is.
GRID = [0, 5, 10, 20, 30, 40, 50, 60, 80, 100, 125, 150, 200, 250, 300,
        400, 500, 650, 800, 1000]


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n"); LOG.flush()


def carrier_measures(w):
    """All carrier variants at the current state, averaged over big things."""
    n = w.n
    out = {}
    for label, need in (("ge1", 1), ("ge2", 2)):
        per_bt = [sum(1 for a in w.agents
                      if len(a.held & bt.required_set) >= need
                      and bt.bid not in a.manifest) / n
                  for bt in w.big_things]
        out[f"carrier_{label}"] = st.mean(per_bt)
    # pure carrier: holds relevant material for something, manifests nothing
    out["pure_carrier"] = sum(
        1 for a in w.agents
        if any(a.held & bt.required_set for bt in w.big_things) and not a.manifest) / n
    out["manifest_any"] = sum(1 for a in w.agents if a.manifest) / n
    return out


FIELDS = ["carrier_ge1", "carrier_ge2", "pure_carrier", "manifest_any"]


def main():
    log(f"# Carrier diagnostics: seeded or generated?  ({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    log("k = 3, so the 'k-1 distinct' variant is the same measure as >=2 relevant,")
    log("because the shipped engine stores distinct element types rather than tokens.\n")

    traj = {g: {f: [] for f in FIELDS} for g in GRID}
    endpoint = {f: [] for f in FIELDS}
    initial = {f: [] for f in FIELDS}
    xfer = {"relevant": [], "nonmanifest": [], "manifest": [], "share_nonmanifest": []}
    stops = []

    for rep in range(REPS):
        w = World(P.config_for_phase("V1", {"seed": rep, **TRIG}))
        m0 = carrier_measures(w)
        for f in FIELDS:
            initial[f].append(m0[f]); traj[0][f].append(m0[f])
        # Follow the canonical protocol exactly: step until run_length OR
        # quiescence, whichever comes first. Measuring at a fixed t=1000 instead
        # lands at an arbitrary point of the trigger sawtooth and does not
        # reproduce the canonical endpoint.
        stop = None
        for g in [x for x in GRID if x > 0]:
            while w.t < g and stop is None:
                w.step()
                if w.quiescent() or w.t >= w.cfg["run_length"]:
                    stop = w.t
            if stop is not None and w.t < g:
                break
            m = carrier_measures(w)
            for f in FIELDS:
                traj[g][f].append(m[f])
            if stop is not None:
                break
        stops.append(stop if stop is not None else w.t)
        mE = carrier_measures(w)
        for f in FIELDS:
            endpoint[f].append(mE[f])
        rel = w.transfers_relevant
        xfer["relevant"].append(rel)
        xfer["nonmanifest"].append(w.transfers_from_nonmanifest_sender)
        xfer["manifest"].append(w.transfers_from_manifest_sender)
        xfer["share_nonmanifest"].append(
            w.transfers_from_nonmanifest_sender / rel if rel else float("nan"))
        if (rep + 1) % 50 == 0:
            log(f"  ... {rep+1}/{REPS}")

    def m(x):
        return st.mean(x)

    def sd(x):
        return st.pstdev(x)

    log(f"\nrun stops at tick {m(stops):.1f} on average (quiescence or run_length)")
    log("\n## carrier quantities, initialization against endpoint")
    log(f"{'measure':16s} {'t=0':>10s} {'endpoint':>10s} {'change':>10s}")
    rows = []
    for f in FIELDS:
        a, b = m(initial[f]), m(endpoint[f])
        log(f"{f:16s} {a:10.4f} {b:10.4f} {b-a:+10.4f}")
        rows.append({"measure": f, "t0": round(a, 4), "t0_sd": round(sd(initial[f]), 4),
                     "endpoint": round(b, 4), "endpoint_sd": round(sd(endpoint[f]), 4),
                     "change": round(b - a, 4), "n": REPS})
    with open(os.path.join(OUT, "carrier_initial_vs_endpoint.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)

    log("\n## carrier trajectory")
    trows = []
    for g in GRID:
        if not traj[g][FIELDS[0]]:
            continue
        r = {"t": g, "n": len(traj[g][FIELDS[0]])}
        r.update({f: round(m(traj[g][f]), 4) for f in FIELDS})
        r.update({f + "_sd": round(sd(traj[g][f]), 4) for f in FIELDS})
        trows.append(r)
        log(f"  t={g:<5d} n={r['n']:<4d} ge1={r['carrier_ge1']:.4f}  ge2={r['carrier_ge2']:.4f}  "
            f"pure={r['pure_carrier']:.4f}  manifest={r['manifest_any']:.4f}")
    with open(os.path.join(OUT, "carrier_trajectory.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(trows[0].keys())); wr.writeheader(); wr.writerows(trows)

    log("\n## successful component transfers by sender state")
    log(f"  relevant transfers per run     : {m(xfer['relevant']):.1f}")
    log(f"  from NONMANIFEST sender        : {m(xfer['nonmanifest']):.1f}")
    log(f"  from manifest sender           : {m(xfer['manifest']):.1f}")
    log(f"  share from nonmanifest sender  : {m(xfer['share_nonmanifest']):.4f} "
        f"(sd {sd(xfer['share_nonmanifest']):.4f})")
    with open(os.path.join(OUT, "transfer_by_sender_state.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["measure", "mean", "sd", "n"])
        wr.writeheader()
        for k, v in xfer.items():
            wr.writerow({"measure": k, "mean": round(m(v), 4),
                         "sd": round(sd(v), 4), "n": REPS})
    log("\nDONE.")


if __name__ == "__main__":
    main()
