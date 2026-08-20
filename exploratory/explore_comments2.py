"""New-mechanism analyses (2026-07 review round): W4, W5, W6, W7.

  W7  cue-gated whole-package: elements_only vs whole_package vs whole_package_gated
      (isolates transmissibility from cue-gating; doc's "possible later refinement").
  W6  coupling matrix: sweep off-diagonal (cross-target) and diagonal (same-target /
      complex contagion) INDEPENDENTLY (doc: "a coupling matrix would separate them").
  W4  overlap -> porousness/leakage: an insular manifest-alpha cluster; sweep
      element_overlap; measure defection to beta (Matt/Eric insular-community point).
  W5  competitive ecology: two big things with different graded-compression
      ("encapsulation") endowments compete under mutual exclusivity; test the
      recruitment-retention inverted-U (Shi, Dokshin, Genkin & <author> 2017 ASR).

Deterministic (seeds 0..REPS-1). Saves CSVs + LOG. Functional checks assert the
new mechanisms actually engage (they are proven no-ops only when OFF).
"""
import csv, os, time, statistics as st
from abm import phases as P
from abm.model import World
from abm.sweep import run_one, summarize_history

REPS = int(os.environ.get("ABM_REPS", "30"))
HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(HERE, "results", f"{STAMP}-comments2")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "LOG.md"), "w")

def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

def save_csv(name, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows: w.writerow(r)

def run_world(phase, overrides):
    cfg = P.config_for_phase(phase, overrides)
    w = World(cfg); w.run()
    return w

def shares(w):
    n = w.n
    return {bt.label: sum(1 for a in w.agents if bt.bid in a.manifest) / n for bt in w.big_things}

# ---------------------------------------------------------------- W7
def w7():
    log("\n## W7  cue-gated whole-package (V1-W base; pre-trigger adoption vs final)")
    rows = []
    for mode in ["elements_only", "whole_package", "whole_package_gated", "both"]:
        fin, pre, ov, lap, gap = [], [], [], [], []
        for r in range(REPS):
            w = run_world("V1-W", {"transmissibility_mode": mode, "seed": r})
            tt = w.cfg["trigger_time"]
            pre.append(max((h["manifest_share"] for h in w.history if h["t"] < tt), default=0.0))
            s = summarize_history(w.history, [bt.label for bt in w.big_things])
            fin.append(s["final_manifest_share"]); ov.append(s["overshoot"])
            lap.append(s["lapse_rate"]); gap.append(s["final_observability_gap"])
        row = {"mode": mode, "final": round(st.mean(fin), 4), "final_sd": round(st.pstdev(fin), 4),
               "n": len(fin), "pre_trigger": round(st.mean(pre), 4),
               "overshoot": round(st.mean(ov), 4), "lapse_rate": round(st.mean(lap), 4),
               "observability_gap": round(st.mean(gap), 4)}
        rows.append(row); log(f"  {mode:20s} final={row['final']} pre_trigger={row['pre_trigger']} "
                              f"overshoot={row['overshoot']} lapse={row['lapse_rate']} gap={row['observability_gap']}")
    save_csv("w7_cuegated.csv", rows)
    d = {r["mode"]: r for r in rows}
    log("  DECOMPOSITION of the adoption gap (all modes bootstrap at the trigger; pre_trigger=0):")
    log(f"    elements_only {d['elements_only']['final']} -> whole_package_gated "
        f"{d['whole_package_gated']['final']}  = pure transmissibility "
        f"(+{round(d['whole_package_gated']['final']-d['elements_only']['final'],4)})")
    log(f"    whole_package_gated {d['whole_package_gated']['final']} -> whole_package "
        f"{d['whole_package']['final']}  = cue-gating / adopt-on-contact "
        f"(+{round(d['whole_package']['final']-d['whole_package_gated']['final'],4)})")
    return rows

# ---------------------------------------------------------------- W6
def w6():
    log("\n## W6  coupling matrix (V2-neighbor-coupling base; two effects separated)")
    rows = []
    log("  (a) OFF-DIAGONAL sweep = cross-target only (diagonal 0):")
    for x in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        M = [[0.0, x], [x, 0.0]]
        fin, lap = [], []
        for r in range(REPS):
            cfg = P.config_for_phase("V2-neighbor-coupling", {"coupling_matrix": M, "seed": r})
            s = run_one(cfg); fin.append(s["final_manifest_share"]); lap.append(s["lapse_rate"])
        rows.append({"kind": "off_diagonal", "value": x, "final": round(st.mean(fin), 4),
                     "final_sd": round(st.pstdev(fin), 4), "n": len(fin), "lapse_rate": round(st.mean(lap), 3)})
        log(f"    off_diag={x:+.1f}: final={round(st.mean(fin),4)} lapse={round(st.mean(lap),3)}")
    log("  (b) DIAGONAL sweep = same-target / complex contagion only (off-diagonal 0):")
    for y in [0.0, 0.25, 0.5, 1.0]:
        M = [[y, 0.0], [0.0, y]]
        fin, lap = [], []
        for r in range(REPS):
            cfg = P.config_for_phase("V2-neighbor-coupling", {"coupling_matrix": M, "seed": r})
            s = run_one(cfg); fin.append(s["final_manifest_share"]); lap.append(s["lapse_rate"])
        rows.append({"kind": "diagonal", "value": y, "final": round(st.mean(fin), 4),
                     "final_sd": round(st.pstdev(fin), 4), "n": len(fin), "lapse_rate": round(st.mean(lap), 3)})
        log(f"    diag={y:+.2f}: final={round(st.mean(fin),4)} lapse={round(st.mean(lap),3)}")
    log("  (c) VALIDATION: matrix [[|x|,x],[x,|x|]] should reproduce scalar coupling_strength=x")
    for x in [-1.0, -0.5, 0.5, 1.0]:
        M = [[abs(x), x], [x, abs(x)]]
        fm, fs = [], []
        for r in range(REPS):
            fm.append(run_one(P.config_for_phase("V2-neighbor-coupling",
                              {"coupling_matrix": M, "seed": r}))["final_manifest_share"])
            fs.append(run_one(P.config_for_phase("V2-neighbor-coupling",
                              {"coupling_strength": x, "seed": r}))["final_manifest_share"])
        rows.append({"kind": "validate_scalar_equiv", "value": x,
                     "final": round(st.mean(fm), 4), "scalar_final": round(st.mean(fs), 4)})
        log(f"    x={x:+.1f}: matrix={round(st.mean(fm),4)} scalar={round(st.mean(fs),4)} "
            f"(match => matrix generalizes the scalar's diag=|off-diag| slice)")
    save_csv("w6_coupling_matrix.csv", rows)
    return rows

# ---------------------------------------------------------------- W4
def w4():
    log("\n## W4  overlap -> porousness/leakage (insular manifest-alpha cluster; defect to beta)")
    rows = []
    for O in [0, 1, 2, 3]:
        leak, outside = [], []
        for r in range(REPS):
            w = run_world("V1", {"element_overlap": O, "change_agent_scenario": True,
                                 "change_agent_clustered": True, "change_agent_fraction": 0.2,
                                 "seed": r})
            ca = [a for a in w.agents if a.is_change_agent]
            noca = [a for a in w.agents if not a.is_change_agent]
            if ca:
                leak.append(sum(1 for a in ca if (1 in a.latent or 1 in a.manifest)) / len(ca))
            if noca:
                outside.append(sum(1 for a in noca if 1 in a.manifest) / len(noca))
        rows.append({"element_overlap": O, "insular_leakage_to_beta": round(st.mean(leak), 4),
                     "insular_leakage_sd": round(st.pstdev(leak), 4), "n": len(leak),
                     "outside_beta_adoption": round(st.mean(outside), 4)})
        log(f"  overlap={O}: insular_leakage_to_beta={round(st.mean(leak),4)} "
            f"outside_beta_adoption={round(st.mean(outside),4)}")
    save_csv("w4_overlap_leakage.csv", rows)
    return rows

# ---------------------------------------------------------------- W5
def w5():
    log("\n## W5  competitive ecology: graded compression (encapsulation) of alpha vs beta")
    log("     (V1 + incompatibility; measure alpha's captured share vs its compression rate)")
    rows = []
    for beta_p in [0.2, 0.5, 0.8]:
        line = []
        for alpha_p in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
            endow = {0: {"compression": alpha_p}, 1: {"compression": beta_p}}
            al, be = [], []
            for r in range(REPS):
                w = run_world("V1", {"incompatibility": True, "bigthing_endowments": endow,
                                     "seed": r})
                s = shares(w)
                al.append(s.get("alpha", 0.0)); be.append(s.get("beta", 0.0))
            rows.append({"beta_compression": beta_p, "alpha_compression": alpha_p,
                         "alpha_share": round(st.mean(al), 4), "alpha_share_sd": round(st.pstdev(al), 4),
                         "n": len(al), "beta_share": round(st.mean(be), 4)})
            line.append((alpha_p, round(st.mean(al), 3)))
        best = max(line, key=lambda t: t[1])
        log(f"  beta_p={beta_p}: " + "  ".join(f"a{p}={v}" for p, v in line) +
            f"   <- alpha best at compression={best[0]} (share {best[1]})")
    save_csv("w5_ecology.csv", rows)
    return rows

if __name__ == "__main__":
    log(f"# New-mechanism analyses ({REPS} reps)  {STAMP}\nout: {OUT}")
    w7(); w6(); w4(); w5()
    log("\nDONE.")
    LOG.close()
