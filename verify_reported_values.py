#!/usr/bin/env python3
"""Recompute every value reported in the article from stored output.

The article states that a verification script recomputes every reported value
and exits nonzero on any mismatch. This is that script. It reads only the CSVs
under `results/`, recomputes each quantity from per-replication data where the
quantity is a contrast, and compares against the value as printed in the paper.

It does not re-run the simulation. Re-running is a separate and much longer
check (`python run.py --phase V1` and friends); this verifies that what the
paper says matches what the stored output contains.

  python verify_reported_values.py          # exits 0 if all match
  python verify_reported_values.py -v       # show every check
"""
import csv, glob, math, os, statistics as st, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
VERBOSE = "-v" in sys.argv

FAILS, CHECKS = [], 0


def rows(d, name):
    with open(os.path.join(R, d, name)) as f:
        return list(csv.DictReader(f))


def check(label, got, want, tol=0.005):
    """Compare a recomputed value against the figure printed in the article."""
    global CHECKS
    CHECKS += 1
    ok = got is not None and abs(got - want) <= tol
    if not ok:
        FAILS.append(f"{label}: article says {want}, recomputed {got}")
    if VERBOSE or not ok:
        mark = "ok  " if ok else "FAIL"
        shown = "None" if got is None else f"{got:+.4f}"
        print(f"  [{mark}] {label:58s} paper {want:+.4f}  recomputed {shown}")
    return ok


def paired_return(by, key_lo, key_hi):
    lo, hi = by[key_lo], by[key_hi]
    d = [hi[k] - lo[k] for k in sorted(lo) if k in hi]
    return st.mean(d), st.pstdev(d) / math.sqrt(len(d))


# ------------------------------------------------- Diffusion Before Manifestation
def section_carriers():
    print("\nDiffusion Before Manifestation")
    e = {r["measure"]: r for r in
         rows("20260816-carrier-diagnostics-endo", "carrier_initial_vs_endpoint.csv")}
    check("carrier fraction at initialization", float(e["carrier_ge1"]["t0"]), 0.474)
    check("carrier fraction at run end (endogenous)",
          float(e["carrier_ge1"]["endpoint"]), 0.222)
    check("strict (k-1) carrier at initialization",
          float(e["carrier_ge2"]["t0"]), 0.109)
    check("strict (k-1) carrier at run end", float(e["carrier_ge2"]["endpoint"]), 0.221)

    traj = [r for r in rows("20260816-carrier-diagnostics-endo",
                            "carrier_trajectory.csv") if int(r["n"]) >= 200]
    check("carrier peak (endogenous)",
          max(float(r["carrier_ge1"]) for r in traj), 0.852)
    check("strict carrier peak (endogenous)",
          max(float(r["carrier_ge2"]) for r in traj), 0.562)

    # analytic: P(hold >=1 of a 4-element requirement set) at density 0.15
    check("seeding-alone probability", 1 - 0.85 ** 4, 0.478)

    shape = {r["trigger_type"]: r for r in
             rows("20260731-endogenous", "e1_shape.csv") if r["mode"] == "elements_only"}
    check("substrate at onset", float(shape["endogenous"]["sub_at_onset"]), 0.46)
    check("onset standard deviation", float(shape["endogenous"]["onset_sd"]), 9.0, tol=0.5)

    for d, lab, want in (("20260816-carrier-diagnostics-endo", "endogenous", 0.49),
                         ("20260816-carrier-diagnostics", "scheduled", 0.60)):
        m = {r["measure"]: r for r in rows(d, "transfer_by_sender_state.csv")}
        check(f"transfers from nonmanifest sender, {lab}",
              float(m["share_nonmanifest"]["mean"]), want)

    cc = rows("20260815-carrier-channel", "carrier_channel.csv")
    for chan, want_ad, want_car in (("open", 0.60, 0.40), ("closed", 0.96, 0.04)):
        r = [x for x in cc if x["capacity"] == "6" and x["carrier_channel"] == chan
             and abs(float(x["transmission_prob"]) - 0.20) < 1e-9][0]
        check(f"carrier channel {chan}: adoption", float(r["final"]), want_ad)
        check(f"carrier channel {chan}: carriers", float(r["carrier_per_bt"]), want_car)


# --------------------------------------------- From Latent Substrate to Adoption
def section_conversion():
    print("\nFrom Latent Substrate to Manifest Adoption")
    w1 = rows("20260730-102229-comments", "w1_capacity_x_k.csv")
    grid = {(int(r["sufficiency_k"]), int(r["capacity"])): float(r["final_manifest_share"])
            for r in w1}
    for k, want in ((2, 3.7), (3, 5.6), (4, 7.2)):
        pts = sorted((c, v) for (kk, c), v in grid.items() if kk == k)
        half = None
        for (c0, v0), (c1, v1) in zip(pts, pts[1:]):
            if v0 < 0.5 <= v1:
                half = c0 + (0.5 - v0) * (c1 - c0) / (v1 - v0)
        check(f"half-adoption capacity, k={k}", half, want, tol=0.06)
        if half:
            check(f"ratio k/half-adoption, k={k}", k / half, 0.54, tol=0.02)

    w8 = rows("20260730-102229-comments", "w8_density_under_cap.csv")
    pts = sorted((float(r["initial_element_density"]),
                  float(r["final_manifest_share"])) for r in w8)
    check("adoption at density 0.05", pts[0][1], 0.67)
    check("adoption at density 0.60", pts[-1][1], 0.65)

    for trig, vals in (("endogenous", {4: 0.13, 6: 0.78}),
                       ("exogenous", {4: 0.13, 6: 0.65, 7: 0.99})):
        e2 = {int(r["capacity"]): float(r["final"])
              for r in rows("20260731-endogenous", f"e2_capacity_{trig}.csv")}
        for cap, want in vals.items():
            check(f"capacity {cap}, {trig} trigger", e2[cap], want)


# ------------------------------------------ Composition Is Not Accumulated Exposure
def section_three_arm():
    print("\nComposition Is Not Accumulated Exposure")
    raw = []
    for f in glob.glob(os.path.join(R, "20260816-sourcenonredundant", "sourcecmp_*_raw.csv")):
        raw += list(csv.DictReader(open(f)))
    ad, car, ev = defaultdict(dict), defaultdict(list), defaultdict(list)
    for r in raw:
        rule, cap, loss, flow = r["cell"].split("/")
        ad[(rule, cap, loss, flow)][int(r["rep"])] = float(r["adoption"])
        car[(rule, cap, loss, flow)].append(float(r["carrier_per_bt"]))
        ev[(rule, cap, loss, flow)].append(float(r["evictions_per_agent"]))

    # levels quoted in the text and in Figure 4
    for rule, cap, flow, want in (("compositional", "c6", "low", 0.19),
                                  ("compositional", "c6", "high", 0.13),
                                  ("source", "c6", "low", 0.45),
                                  ("source", "c6", "high", 0.46),
                                  ("count", "c6", "low", 0.61),
                                  ("count", "c6", "high", 0.60),
                                  ("compositional", "c5", "low", 0.12),
                                  ("compositional", "c5", "high", 0.09),
                                  ("source", "c5", "low", 0.34),
                                  ("source", "c5", "high", 0.37),
                                  ("count", "c5", "low", 0.50),
                                  ("count", "c5", "high", 0.51)):
        check(f"adoption {rule}/{cap}/{flow}",
              st.mean(ad[(rule, cap, "l0.0", flow)].values()), want)

    # returns to flow, no loss
    rets = {}
    for rule, cap, want_m, want_se in (("compositional", "c6", -0.058, 0.006),
                                       ("source", "c6", +0.011, 0.008),
                                       ("count", "c6", -0.009, 0.009),
                                       ("compositional", "c5", -0.032, 0.005),
                                       ("source", "c5", +0.033, 0.009),
                                       ("count", "c5", +0.017, 0.010)):
        m, se = paired_return(ad, (rule, cap, "l0.0", "low"), (rule, cap, "l0.0", "high"))
        rets[(rule, cap)] = m
        check(f"return to flow {rule}/{cap}, no loss", m, want_m, tol=0.002)
        check(f"  its standard error", se, want_se, tol=0.002)

    for cap, vs_src, vs_cnt in (("c6", -0.068, -0.049), ("c5", -0.065, -0.049)):
        check(f"gap compositional minus source, {cap}",
              rets[("compositional", cap)] - rets[("source", cap)], vs_src, tol=0.002)
        check(f"gap compositional minus count, {cap}",
              rets[("compositional", cap)] - rets[("count", cap)], vs_cnt, tol=0.002)

    # returns under loss
    for rule, cap, want in (("compositional", "c6", +0.059), ("source", "c6", +0.185),
                            ("count", "c6", +0.215), ("compositional", "c5", +0.018),
                            ("source", "c5", +0.140), ("count", "c5", +0.173)):
        m, _ = paired_return(ad, (rule, cap, "l0.01", "low"), (rule, cap, "l0.01", "high"))
        check(f"return to flow {rule}/{cap}, loss .01", m, want, tol=0.002)

    # evictions identical across rules by construction
    for flow, want in (("low", 45), ("high", 195)):
        vals = [st.mean(ev[(rule, "c6", "l0.0", flow)])
                for rule in ("compositional", "source", "count")]
        check(f"evictions per agent at C=6, {flow} flow", st.mean(vals), want, tol=1.0)
        if max(vals) - min(vals) > 1e-9:
            FAILS.append("evictions differ across rules; the paired design is broken")

    # carrier fractions under identical holdings
    check("carriers, distinct components (C=6 high)",
          st.mean(car[("compositional", "c6", "l0.0", "high")]), 0.79, tol=0.01)
    check("carriers, distinct senders (C=6 high)",
          st.mean(car[("source", "c6", "l0.0", "high")]), 0.46, tol=0.01)
    check("carriers, equal count (C=6 high)",
          st.mean(car[("count", "c6", "l0.0", "high")]), 0.32, tol=0.01)

    # calibrated diagnostic
    cal = defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(
            R, "20260815-countonly", "countonly_count-calibrated_raw.csv"))):
        _rule, cap, loss, flow = r["cell"].split("/")
        cal[(cap, loss, flow)][int(r["rep"])] = float(r["adoption"])
    check("calibrated arm adoption, C=6 no loss, low flow",
          st.mean(cal[("c6", "l0.0", "low")].values()), 0.060)
    m, se = paired_return(cal, ("c6", "l0.0", "low"), ("c6", "l0.0", "high"))
    check("calibrated arm return to flow", m, +0.028, tol=0.002)
    check("  its standard error", se, 0.005, tol=0.002)


# ------------------------------------------------------- What the Mechanism Is Not
def section_packetization():
    print("\nWhat the Mechanism Is Not")
    raw = list(csv.DictReader(open(os.path.join(
        R, "20260815-packetization", "packetization_raw.csv"))))
    by = defaultdict(dict)
    for r in raw:
        cap, arm, flow = r["cell"].split("/")
        by[(cap, arm, flow)][int(r["rep"])] = float(r["final"])
    for cap, flow, want_m, want_se in (("c6", "low", -0.001, 0.003),
                                       ("c6", "high", -0.002, 0.004),
                                       ("c5", "low", +0.008, 0.003),
                                       ("c5", "high", -0.008, 0.002)):
        m, se = paired_return(by, (cap, "piecemeal", flow), (cap, "bundled", flow))
        check(f"joint minus separate, {cap} {flow} flow", m, want_m, tol=0.002)
        check(f"  its standard error", se, want_se, tol=0.002)


# ---------------------------------------- Retention Determines Return to Transmission
def section_retention():
    print("\nRetention Determines the Return to Transmission")
    agg = [r for r in rows("20260730-093338-full", "aggregated.csv")
           if r["phase"] == "V2-enhanced"]
    byf = {float(r["focal_value"]): r for r in agg}
    check("transmission alone, 1x: adoption",
          float(byf[1.0]["final_manifest_share_mean"]), 0.65)
    check("transmission alone, 3x: adoption",
          float(byf[3.0]["final_manifest_share_mean"]), 0.64)
    check("transmission alone, 1x: overshoot", float(byf[1.0]["overshoot_mean"]), 0.14)
    check("transmission alone, 3x: overshoot", float(byf[3.0]["overshoot_mean"]), 0.18)

    w2 = {(float(r["stabilization_boost"]), float(r["enhanced_factor"])):
          float(r["final_manifest_share"])
          for r in rows("20260730-102229-comments", "w2_stab_x_enh.csv")}
    check("unprotected, 1x", w2[(1.0, 1.0)], 0.28)
    check("unprotected, 3x", w2[(1.0, 3.0)], 0.43)
    check("fully protected, 1x", w2[(0.0, 1.0)], 0.88)
    check("fully protected, 3x", w2[(0.0, 3.0)], 1.00)


# --------------------------------------------- Manifest Advocates and Latent Conversion
def section_advocates():
    print("\nManifest Advocates and Latent Conversion")
    a = rows("20260814-changeagent", "a_fraction.csv")

    def cell(regime, frac):
        return [r for r in a if r["regime"] == regime
                and r["change_agent_fraction"] == frac][0]

    check("no seeded minority (higher capacity)",
          float(cell("permissive", "0.0")["final"]), 0.67)
    check("seeded 0.20 (higher capacity)",
          float(cell("permissive", "0.2")["final"]), 0.71)
    check("scenario-off control",
          float([r for r in a if r["regime"] == "permissive"
                 and not r["change_agent_fraction"]][0]["final"]), 0.67)
    check("no seeded minority (lower capacity)",
          float(cell("constrained", "0.0")["final"]), 0.12)
    check("seeded 0.20 (lower capacity)",
          float(cell("constrained", "0.2")["final"]), 0.20)
    check("carriers at lower capacity, seeded 0.20",
          float(cell("constrained", "0.2")["carrier_per_bt"]), 0.79)

    b = rows("20260814-changeagent", "b_evangelism.csv")

    def ev(regime, mult):
        return float([r for r in b if r["regime"] == regime
                      and abs(float(r["change_agent_evangelism"]) - mult) < 1e-9][0]["final"])

    check("promotion 1x (higher capacity)", ev("permissive", 1), 0.71)
    check("promotion 8x (higher capacity)", ev("permissive", 8), 0.65)
    check("promotion 1x (lower capacity)", ev("constrained", 1), 0.20)
    check("promotion 8x (lower capacity)", ev("constrained", 8), 0.23)


# ------------------------------------------------- seeded-source sensitivity (S5.5)
def section_seedsource():
    print("\nSupplement S5.5: seeded-source sensitivity")
    src = defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(
            R, "20260816-sourcenonredundant", "sourcecmp_source_raw.csv"))):
        _rule, cap, loss, flow = r["cell"].split("/")
        src[("unique", cap, loss, flow)][int(r["rep"])] = float(r["adoption"])
    for mode in ("shared", "social_only"):
        for r in csv.DictReader(open(os.path.join(
                R, "20260817-seedsource", f"seedsource_{mode}_raw.csv"))):
            _tag, cap, loss, flow = r["cell"].split("/")
            src[(mode, cap, loss, flow)][int(r["rep"])] = float(r["adoption"])
    worst = 0.0
    for cap in ("c6", "c5"):
        for loss in ("l0.0", "l0.01"):
            vals = [paired_return(src, (m, cap, loss, "low"), (m, cap, loss, "high"))[0]
                    for m in ("unique", "shared", "social_only")]
            worst = max(worst, max(vals) - min(vals))
    global CHECKS
    CHECKS += 1
    ok = worst <= 0.0001
    if not ok:
        FAILS.append(f"seed-source conventions disagree by {worst:.5f}, article says 0.0001")
    if VERBOSE or not ok:
        print(f"  [{'ok  ' if ok else 'FAIL'}] seed-source conventions agree to within"
              f" {worst:.5f} (article says 0.0001)")


def main():
    print("Recomputing every value reported in the article from stored output.")
    for fn in (section_carriers, section_conversion, section_three_arm,
               section_packetization, section_retention, section_advocates,
               section_seedsource):
        fn()
    print(f"\n{CHECKS} values checked, {len(FAILS)} mismatched.")
    if FAILS:
        print("\nMISMATCHES:")
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL REPORTED VALUES MATCH STORED OUTPUT.")


if __name__ == "__main__":
    main()
