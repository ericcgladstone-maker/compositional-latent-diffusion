"""W5c: member-gated recruitment ecology (the definitive test of the U).

W5/W5b found retention (compression) wins monotonically because recruitment runs
through a shared element pool, not through members. W5c routes recruitment through
members: with member_gated_transmission on, only an active (manifest) member of a
big thing transmits that big thing's elements. A compressed member holds no loose
elements and so transmits nothing, so encapsulating members genuinely starves
recruitment. This is the structural change flagged as what Shi et al.'s trade-off
requires.

Member-gated recruitment cannot bootstrap from nothing (no members -> no
transmission -> no members), so each big thing is seeded with F founders, as an
organization starts with founders. Initial ambient element density is set to 0 so
all spread is member-routed.

Design: V1 + incompatibility + member_gated_transmission, F=10 founders per big
thing, alpha's graded compression swept against a fixed rival, across a loss ladder
(loss couples recruitment to sustained membership). We report alpha's captured
share and flag any interior optimum (the inverted-U / "less greedy than the
competition" signature). Deterministic seeds 0..REPS-1.
"""
import csv, os, time, statistics as st
from abm import phases as P
from abm.model import World

REPS = int(os.environ.get("ABM_REPS", "30"))
NAGENTS = int(os.environ.get("ABM_N", "100"))    # population size (finite-size checks)
F = max(1, int(round(0.10 * NAGENTS)))            # founders per big thing = 10% of N
# Loss ladder matches the 30-rep run folded into the doc (sweep 20260729-090619)
# so the 200-rep result is comparable cell-for-cell: 6 losses x 3 rivals = 18
# loss-by-rival cells. Compression grid is denser than that run (8 levels, adding
# 0.5 and 0.7) to resolve the interior optimum near ~0.6 rather than to find more
# of them; a denser grid can only make an interior argmax easier to detect, so the
# interior-cell count is reported against the stated grid, not compared naively.
LOSSES = [0.0, 0.001, 0.002, 0.004, 0.006, 0.01]
# Optional shard filter: ABM_LOSSES="0.0,0.002" runs only those loss levels. Each
# cell's replications are seeded 0..REPS-1 independently of which other cells run
# in the same process, so sharding by loss and concatenating the CSVs is identical
# to one serial pass. Used only to parallelize across cores.
if os.environ.get("ABM_LOSSES"):
    _want = [float(x) for x in os.environ["ABM_LOSSES"].split(",")]
    LOSSES = [x for x in LOSSES if any(abs(x - w) < 1e-12 for w in _want)]
    if not LOSSES:
        raise SystemExit(f"ABM_LOSSES={os.environ['ABM_LOSSES']} matched no loss level")
BETAS = [0.2, 0.5, 0.8]
ALPHAS = [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]        # denser near the ~0.6 peak

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", f"{STAMP}-comments4")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "LOG.md"), "w")

def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

def seed_founders(w):
    """Agents 0..F-1 = alpha founders, F..2F-1 = beta founders (manifest members)."""
    for bid, base in ((0, 0), (1, F)):
        bt = w.big_things[bid]
        for i in range(base, base + F):
            a = w.agents[i]
            for e in bt.required:
                w._add_element(a, e, enforce_capacity=False)
            a.latent.add(bid)
            w._manifest(a, bid)

def run_cell(alpha_p, beta_p, loss, raw_sink=None):
    al, be = [], []
    for r in range(REPS):
        cfg = P.config_for_phase("V1", {
            "incompatibility": True, "member_gated_transmission": True, "n_agents": NAGENTS,
            "bigthing_endowments": {0: {"compression": alpha_p}, 1: {"compression": beta_p}},
            "loss_rate": loss, "initial_element_density": 0.0, "seed": r})
        w = World(cfg)
        seed_founders(w)
        w.run()
        n = w.n
        a_sh = sum(1 for a in w.agents if 0 in a.manifest) / n
        b_sh = sum(1 for a in w.agents if 1 in a.manifest) / n
        al.append(a_sh); be.append(b_sh)
        if raw_sink is not None:
            raw_sink.append({"loss_rate": loss, "beta_compression": beta_p,
                             "alpha_compression": alpha_p, "rep": r, "seed": r,
                             "n_agents": NAGENTS, "alpha_share": round(a_sh, 4),
                             "beta_share": round(b_sh, 4)})
    return round(st.mean(al), 4), round(st.pstdev(al), 4), round(st.mean(be), 4)

def flush(items, name):
    """Checkpoint after every cell so a kill (lid-close sleep) costs one cell, not the run."""
    if not items:
        return
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(items[0].keys())); w.writeheader()
        for r in items:
            w.writerow(r)

def main():
    log(f"# W5c member-gated recruitment ecology  ({REPS} reps, N={NAGENTS}, F={F} founders/bigthing)  {STAMP}")
    log(f"out: {OUT}   founder floor = {F}/{NAGENTS} = {F/NAGENTS:.2f} per big thing")
    rows = []
    raw = []
    for loss in LOSSES:
        log(f"\n## loss_rate = {loss}")
        for beta_p in BETAS:
            curve = []
            for alpha_p in ALPHAS:
                am, asd, bm = run_cell(alpha_p, beta_p, loss, raw_sink=raw)
                rows.append({"loss_rate": loss, "beta_compression": beta_p,
                             "alpha_compression": alpha_p, "alpha_share": am,
                             "alpha_share_sd": asd, "n": REPS, "n_agents": NAGENTS,
                             "beta_share": bm})
                curve.append((alpha_p, am))
                flush(rows, "w5c_member_gated.csv")        # checkpoint agg
                flush(raw, "w5c_member_gated_raw.csv")     # checkpoint per-rep raw
            best = max(curve, key=lambda t: t[1])
            interior = 0.0 < best[0] < 1.0
            log(f"  rival={beta_p}: " + "  ".join(f"a{p}={v}" for p, v in curve) +
                f"   best={best[0]} (share {best[1]}) "
                f"{'INTERIOR (inverted-U)' if interior else 'edge'}")
    keys = list(rows[0].keys())
    with open(os.path.join(OUT, "w5c_member_gated.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows: w.writerow(r)
    # per-replication raw (full transparency for the marginal inverted-U claim)
    with open(os.path.join(OUT, "w5c_member_gated_raw.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(raw[0].keys())); w.writeheader()
        for r in raw: w.writerow(r)
    log(f"wrote per-rep raw: {len(raw)} rows")
    n_interior = sum(1 for loss in LOSSES for beta_p in BETAS
                     if (lambda c: 0.0 < max(c, key=lambda t: t[1])[0] < 1.0)(
                         [(a, next(r["alpha_share"] for r in rows
                                   if r["loss_rate"] == loss and r["beta_compression"] == beta_p
                                   and r["alpha_compression"] == a)) for a in ALPHAS]))
    log(f"\nINTERIOR OPTIMA (inverted-U cells): {n_interior} of {len(LOSSES)*len(BETAS)}")
    log("DONE.")
    LOG.close()

if __name__ == "__main__":
    main()
