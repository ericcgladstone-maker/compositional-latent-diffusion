"""Comment-driven analyses (2026-07 review round with Matt).

Four analyses requested/green-lit in the build-doc comments, using existing
params only (no engine changes):

  W1  capacity x sufficiency_k heatmap        (Matt: "specify what the ratio is")
  W2  stabilization_boost x enhanced_factor   (Matt id22: "Go for it" / heatmap)
  W8  initial_element_density under a binding cap (Eric caveat: does the ENDPOINT
      move, or only time-to-saturation, once capacity binds?)
  W3  carrier fraction: agents holding/transmitting big-thing elements while NOT
      manifest (Matt/Eric: make exposure != adoption a measured quantity)

Deterministic: seeds base_seed..base_seed+reps-1. Saves CSVs + a log under
results/<stamp>-comments/. Mirrors the explore_*.py convention.
"""
import csv, json, os, time, statistics as st
from abm import phases as P
from abm.model import World
from abm.sweep import run_one

REPS = int(os.environ.get("ABM_REPS", "30"))
BASE_SEED = 0

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", f"{STAMP}-comments")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "LOG.md"), "w")

def log(*a):
    line = " ".join(str(x) for x in a)
    print(line, flush=True)
    LOG.write(line + "\n"); LOG.flush()

def cell_mean(phase, overrides, reps=REPS, metric="final_manifest_share"):
    vals, extra = [], {"overshoot": [], "lapse_rate": [], "peak_manifest_share": [],
                       "time_to_first_manifest": []}
    for r in range(reps):
        cfg = P.config_for_phase(phase, {**overrides, "seed": BASE_SEED + r})
        s = run_one(cfg)
        vals.append(s[metric])
        for k in extra:
            extra[k].append(s[k])
    out = {metric: round(st.mean(vals), 4), f"{metric}_sd": round(st.pstdev(vals), 4)}
    for k, v in extra.items():
        out[k] = round(st.mean(v), 4)
    return out

def save_csv(name, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows: w.writerow(r)

# ---------------------------------------------------------------- W1
def w1_capacity_x_k():
    log("\n## W1  capacity x sufficiency_k  (V1 base, requirement_size=4)")
    caps = [3, 4, 5, 6, 7, 8, 10]
    ks = [2, 3, 4]
    rows = []
    for k in ks:
        line = []
        for c in caps:
            m = cell_mean("V1", {"capacity": c, "sufficiency_k": k, "requirement_size": 4})
            rows.append({"sufficiency_k": k, "capacity": c, "ratio_k_over_cap": round(k / c, 3),
                         **m})
            line.append(f"{m['final_manifest_share']:.2f}")
        log(f"  k={k}: " + "  ".join(f"cap{c}={v}" for c, v in zip(caps, line)))
    save_csv("w1_capacity_x_k.csv", rows)
    return rows

# ---------------------------------------------------------------- W2
def w2_stab_x_enh():
    log("\n## W2  stabilization_boost x enhanced_factor  (V2-stab-enh base, loss=0.01)")
    boosts = [0.0, 0.25, 0.5, 0.75, 1.0]
    facs = [1.0, 2.0, 3.0]
    rows = []
    for b in boosts:
        line = []
        for e in facs:
            m = cell_mean("V2-stab-enh", {"stabilization_boost": b, "enhanced_factor": e})
            rows.append({"stabilization_boost": b, "enhanced_factor": e, **m})
            line.append(f"{m['final_manifest_share']:.2f}(lap{m['lapse_rate']:.2f})")
        log(f"  boost={b}: " + "  ".join(f"e{e}={v}" for e, v in zip(facs, line)))
    save_csv("w2_stab_x_enh.csv", rows)
    return rows

# ---------------------------------------------------------------- W8
def w8_density_under_cap():
    log("\n## W8  initial_element_density under binding cap (V1 base, capacity=6)")
    dens = [0.05, 0.1, 0.15, 0.2, 0.3, 0.45, 0.6]
    rows = []
    for d in dens:
        m = cell_mean("V1", {"initial_element_density": d})
        rows.append({"initial_element_density": d, **m})
        log(f"  density={d}: final={m['final_manifest_share']} "
            f"peak={m['peak_manifest_share']} t_first={m['time_to_first_manifest']}")
    save_csv("w8_density_under_cap.csv", rows)
    return rows

# ---------------------------------------------------------------- W3
def carrier_metrics(cfg):
    """At run end, measure asymptomatic carriers.

    carrier_per_bt: mean over big things of the fraction of agents who HOLD >=1 of
      that big thing's elements (can transmit them) but are NOT manifest for it --
      i.e. spread the component without adopting the package. This is adoption-
      independent and the right operationalization of exposure != adoption.
    pure_carrier:   fraction of agents holding some big-thing element but manifest
      for NO big thing at all.
    manifest_share: doc-style (mean over big things).
    """
    w = World(cfg); w.run()
    n = len(w.agents)
    total = set()
    for bt in w.big_things:
        total |= bt.required_set
    per_bt = []
    for bt in w.big_things:
        rs = bt.required_set
        c = sum(1 for a in w.agents if (a.held & rs) and bt.bid not in a.manifest)
        per_bt.append(c / n)
    carrier_per_bt = st.mean(per_bt)
    pure_carrier = sum(1 for a in w.agents if (a.held & total) and not a.manifest) / n
    manifest_share = sum(len(a.manifest) for a in w.agents) / (n * len(w.big_things))
    return carrier_per_bt, pure_carrier, manifest_share

def w3_carriers():
    log("\n## W3  carrier fraction (holds/transmits a big thing's elements, not manifest for it)")
    rows = []
    for mode in ["elements_only", "whole_package"]:
        cpb, pc, mf = [], [], []
        for r in range(REPS):
            cfg = P.config_for_phase("V1-W", {"transmissibility_mode": mode,
                                              "seed": BASE_SEED + r})
            a, b, c = carrier_metrics(cfg)
            cpb.append(a); pc.append(b); mf.append(c)
        row = {"mode": mode,
               "carrier_per_bt": round(st.mean(cpb), 4),
               "carrier_per_bt_sd": round(st.pstdev(cpb), 4),
               "pure_carrier": round(st.mean(pc), 4),
               "manifest_share": round(st.mean(mf), 4)}
        rows.append(row)
        log(f"  {mode}: carrier_per_bt={row['carrier_per_bt']} "
            f"pure_carrier={row['pure_carrier']} manifest_share={row['manifest_share']}")
    save_csv("w3_carriers.csv", rows)
    return rows

if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    log(f"# Comment-driven analyses  ({REPS} reps, base_seed {BASE_SEED})  {STAMP}")
    log(f"out: {OUT}")
    if which in ("all", "smoke"):
        if which == "smoke":
            # one cheap cell each to prove the API wiring
            m = cell_mean("V1", {"capacity": 6, "sufficiency_k": 3, "requirement_size": 4}, reps=3)
            log("smoke V1 cap6 k3:", m)
            c, mm, h = carrier_fraction(P.config_for_phase("V1-W",
                        {"transmissibility_mode": "elements_only", "seed": 0}))
            log(f"smoke carrier elements_only: carriers={c:.3f} manifest={mm:.3f} holders={h:.3f}")
            sys.exit(0)
    w1_capacity_x_k()
    w2_stab_x_enh()
    w8_density_under_cap()
    w3_carriers()
    log("\nDONE.")
    LOG.close()
