"""W5b: recruitment-retention ecology under element loss.

W5 found retention (compression) wins monotonically, because recruitment does
not depend on members: elements sit in a free population reservoir that keeps
recruiting regardless of who compresses out. Turning on element loss removes the
free reservoir, so an element persists only where it is actively held and
transmitted. Then compressing a member (which stops transmitting its elements)
genuinely starves recruitment, while staying loose transmits but lapses under
loss. That is the Shi et al. recruitment-retention trade-off.

Design: same ecology as W5 (V1 + incompatibility; alpha vs beta graded
compression) swept over a loss-rate ladder. loss_rate = 0.0 reproduces W5 as a
built-in control. For each (loss, rival), we report alpha's captured share versus
its own compression, the best-response compression (argmax), and whether that
optimum is interior (an interior optimum is the inverted-U / "less greedy than
the competition" signature). No fishing: the full grid is reported.

Deterministic seeds 0..REPS-1. Saves CSV + LOG.
"""
import csv, os, time, statistics as st
from abm import phases as P
from abm.model import World

REPS = int(os.environ.get("ABM_REPS", "30"))
LOSSES = [0.0, 0.005, 0.01, 0.02]
BETAS = [0.2, 0.5, 0.8]
ALPHAS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", f"{STAMP}-comments3")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "LOG.md"), "w")

def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

def shares(cfg):
    w = World(cfg); w.run()
    n = w.n
    a = sum(1 for ag in w.agents if 0 in ag.manifest) / n
    b = sum(1 for ag in w.agents if 1 in ag.manifest) / n
    return a, b

def flush(rows, name):
    """Checkpoint: rewrite the CSV after every cell, so a kill (e.g. lid-close
    sleep) costs only the current cell, not the whole run."""
    if not rows:
        return
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
        for r in rows:
            w.writerow(r)

def main():
    log(f"# W5b recruitment-retention under element loss  ({REPS} reps)  {STAMP}")
    log(f"out: {OUT}")
    rows = []
    for loss in LOSSES:
        log(f"\n## loss_rate = {loss}")
        for beta_p in BETAS:
            curve = []
            for alpha_p in ALPHAS:
                endow = {0: {"compression": alpha_p}, 1: {"compression": beta_p}}
                al, be = [], []
                for r in range(REPS):
                    cfg = P.config_for_phase("V1", {"incompatibility": True,
                                                   "bigthing_endowments": endow,
                                                   "loss_rate": loss, "seed": r})
                    a, b = shares(cfg)
                    al.append(a); be.append(b)
                am, bm = round(st.mean(al), 4), round(st.mean(be), 4)
                rows.append({"loss_rate": loss, "beta_compression": beta_p,
                             "alpha_compression": alpha_p, "alpha_share": am,
                             "alpha_share_sd": round(st.pstdev(al), 4), "n": len(al),
                             "beta_share": bm})
                curve.append((alpha_p, am))
                flush(rows, "w5b_loss_ladder.csv")   # checkpoint after every cell
            best = max(curve, key=lambda t: t[1])
            interior = 0.0 < best[0] < 1.0
            monotone = all(curve[i][1] <= curve[i + 1][1] + 1e-9 for i in range(len(curve) - 1))
            log(f"  rival={beta_p}: " + "  ".join(f"a{p}={v}" for p, v in curve) +
                f"   best={best[0]} (share {best[1]}) "
                f"{'INTERIOR (inverted-U)' if interior else 'edge'} "
                f"{'monotone' if monotone else 'non-monotone'}")
    # write csv
    keys = list(rows[0].keys())
    with open(os.path.join(OUT, "w5b_loss_ladder.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows: w.writerow(r)
    log("\nDONE.")
    LOG.close()

if __name__ == "__main__":
    main()
