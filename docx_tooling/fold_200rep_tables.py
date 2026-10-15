#!/usr/bin/env python3
"""Rewrite the follow-up-analysis tables (W1-W8, W5b, W5c) in the master docx
from 200-replication result CSVs.

Every cell is computed from a CSV on disk. Nothing is typed by hand, so a cell
can only ever hold a value that exists in a source file. PREVIEW mode (default)
prints every intended change and writes nothing; `apply` edits in place.

Tables are located by their header row, not by index, so a table moving within
the document does not silently retarget the write.

Usage:
  python fold_200rep_tables.py                 # preview
  python fold_200rep_tables.py apply           # write
"""
import csv, glob, math, os, sys
import statistics as st
import docx

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))

# --- source dirs (single place to repoint) ---------------------------------
SRC = {
    "w1238": "20260730-102229-comments",
    "w4567": "20260730-102232-comments2",
    "w5b":   "20260730-093336-comments3",
    "w5c":   "20260730-merged-comments4",
    "ca":    "20260814-changeagent",
    "co":    "20260815-countonly",
    "cc":    "20260815-carrier-channel",
    "pk":    "20260815-packetization",
    "rm":    "20260815-rate-matched",
    "ts":    "20260815-tiestrength-matched",
    "rb":    "20260815-changeagent-robust",
    "cd":    "20260816-carrier-diagnostics",
    "cde":   "20260816-carrier-diagnostics-endo",
    "snr":   "20260816-sourcenonredundant",
    "ss":    "20260817-seedsource",
    "endo":  "20260731-endogenous",
    "rev":   "20260730-132108-reversibility",
    # immediate manifestation upon readiness (round-4 comment C18, 2026-10-06)
    "cdi":   "20261006-carrier-diagnostics-immediate",
    "imc":   "20261006-immediate-capacity",
    "tai":   "20261006-token-activation-invariance",
}
# Any entry can be repointed for a dry run, e.g. SRC_w4567=20260729-122300-comments2
for _k in list(SRC):
    SRC[_k] = os.environ.get("SRC_" + _k, SRC[_k])


def rows(key, name):
    with open(os.path.join(RESULTS, SRC[key], name)) as f:
        return list(csv.DictReader(f))


def f2(x):
    return f"{float(x):.2f}"


def g(x):
    return f"{float(x):g}"


# --- table specs: header signature -> builder -------------------------------
# Each builder returns {row_label_in_col0: [col1, col2, ...]} as formatted strings.

def t_w1():
    src = {(g(r["sufficiency_k"]), g(r["capacity"])): r
           for r in rows("w1238", "w1_capacity_x_k.csv")}
    def build(hdr):
        caps = hdr[1:]
        return {k: [f2(src[(g(k), g(c))]["final_manifest_share"]) for c in caps]
                for k in ("2", "3", "4")}
    return build


def t_w2():
    src = {(g(r["stabilization_boost"]), g(r["enhanced_factor"])): r
           for r in rows("w1238", "w2_stab_x_enh.csv")}
    def build(hdr):
        enh = hdr[1:]
        out = {}
        for b in sorted({g(k[0]) for k in src}, key=float):
            out[b] = [f2(src[(b, g(e))]["final_manifest_share"]) for e in enh]
        return out
    return build


def t_w3():
    src = {r["mode"]: r for r in rows("w1238", "w3_carriers.csv")}
    def build(hdr):
        return {m: [f2(src[m]["carrier_per_bt"]), f2(src[m]["pure_carrier"]),
                    f2(src[m]["manifest_share"])]
                for m in ("elements_only", "whole_package")}
    return build


def t_w8():
    src = {g(r["initial_element_density"]): r
           for r in rows("w1238", "w8_density_under_cap.csv")}
    def build(hdr):
        return {d: [f2(src[d]["final_manifest_share"]), f2(src[d]["peak_manifest_share"])]
                for d in src}
    return build


def t_w7():
    src = {r["mode"]: r for r in rows("w4567", "w7_cuegated.csv")}
    def build(hdr):
        return {m: [f2(src[m]["final"]), f2(src[m]["overshoot"]),
                    f2(src[m]["lapse_rate"]), f2(src[m]["observability_gap"])]
                for m in src}
    return build


def t_w6():
    # the CSV also carries validate_scalar_equiv rows, which have no lapse_rate
    # and are not part of this table; the doc table holds only the two channels
    src = {(r["kind"], g(r["value"])): r for r in rows("w4567", "w6_coupling_matrix.csv")
           if r["kind"] in ("off_diagonal", "diagonal") and r["lapse_rate"]}
    def build(hdr):
        return {k: [f2(v["final"]), f2(v["lapse_rate"])] for k, v in src.items()}
    return build


def t_w5():
    src = {(g(r["beta_compression"]), g(r["alpha_compression"])): r
           for r in rows("w4567", "w5_ecology.csv")}
    def build(hdr):
        alphas = sorted({k[1] for k in src}, key=float)
        return {a: [f2(src[(b, a)]["alpha_share"]) for b in ("0.2", "0.5", "0.8")]
                for a in alphas}
    return build


def t_w4():
    src = {g(r["element_overlap"]): r for r in rows("w4567", "w4_overlap_leakage.csv")}
    def build(hdr):
        return {o: [f2(src[o]["insular_leakage_to_beta"]),
                    f2(src[o]["outside_beta_adoption"])] for o in src}
    return build


def _ladder(key, fname):
    """Group an ecology CSV into {(loss, rival): [(alpha, share), ...]} sorted by alpha."""
    out = {}
    for r in rows(key, fname):
        out.setdefault((g(r["loss_rate"]), g(r["beta_compression"])), []).append(
            (float(r["alpha_compression"]), float(r["alpha_share"])))
    for k in out:
        out[k].sort()
    return out


def t_w5b():
    src = _ladder("w5b", "w5b_loss_ladder.csv")
    def build(hdr):
        out = {}
        for (loss, rival), curve in src.items():
            at0 = next(v for a, v in curve if a == 0.0)
            at1 = next(v for a, v in curve if a == 1.0)
            best = max(curve, key=lambda t: t[1])[0]
            out[(loss, rival)] = [f2(at0), f2(at1), g(best)]
        return out
    return build


def t_w5c():
    src = _ladder("w5c", "w5c_member_gated.csv")
    def build(hdr):
        out = {}
        for (loss, rival), curve in src.items():
            best_a, best_v = max(curve, key=lambda t: t[1])
            interior = 0.0 < best_a < 1.0
            out[(loss, rival)] = [g(best_a), f2(best_v), "yes" if interior else "no"]
        return out
    return build


def t_rev():
    src = {r["label"]: r for r in rows("rev", "reversibility.csv")}
    def build(hdr):
        return {lab: [f2(r["reversible"]), f2(r["irreversible"])]
                for lab, r in src.items()}
    return build


def t_endo_shape():
    src = {(r["trigger_type"], r["mode"]): r for r in rows("endo", "e1_shape.csv")}
    LAB = {"exogenous": "scheduled", "endogenous": "endogenous"}
    def build(hdr):
        return {(LAB[t], m): [f2(r["final"]),
                              f"{float(r['onset']):.0f} ({float(r['onset_sd']):.1f})",
                              f"{float(r['rise']):.0f}", f2(r["sub_at_onset"]),
                              f2(r["final_gap"])]
                for (t, m), r in src.items()}
    return build


def t_endo_cap():
    ex = {g(r["capacity"]): r for r in rows("endo", "e2_capacity_exogenous.csv")}
    en = {g(r["capacity"]): r for r in rows("endo", "e2_capacity_endogenous.csv")}
    def build(hdr):
        return {c: [f2(ex[c]["final"]), f2(en[c]["final"])] for c in ex}
    return build


def t_endo_thr():
    src = {g(r["endogenous_trigger_threshold"]): r
           for r in rows("endo", "e4_threshold.csv")}
    def build(hdr):
        return {k: [f2(r["final"]),
                    f"{float(r['onset']):.0f} ({float(r['onset_sd']):.1f})",
                    f2(r["final_gap"])] for k, r in src.items()}
    return build


def _ca(name):
    return rows("ca", name)


def t_ca_fraction():
    a = _ca("a_fraction.csv")
    have = {(r["regime"], g(r["change_agent_fraction"])): r for r in a
            if r["change_agent_fraction"] not in ("", "None")}
    off = {r["regime"]: r for r in a if r["change_agent_fraction"] in ("", "None")}
    def build(hdr):
        out = {}
        for k in {k[1] for k in have}:
            out[k] = [f2(have[("permissive", k)]["final"]),
                      f2(have[("permissive", k)]["carrier_per_bt"]),
                      f2(have[("constrained", k)]["final"]),
                      f2(have[("constrained", k)]["carrier_per_bt"])]
        out["scenario off"] = [f2(off["permissive"]["final"]),
                               f2(off["permissive"]["carrier_per_bt"]),
                               f2(off["constrained"]["final"]),
                               f2(off["constrained"]["carrier_per_bt"])]
        return out
    return build


def t_ca_evangelism():
    src = {(r["regime"], g(r["change_agent_evangelism"])): r
           for r in _ca("b_evangelism.csv")}
    def build(hdr):
        return {k: [f2(src[("permissive", k)]["final"]),
                    f2(src[("constrained", k)]["final"])]
                for k in {k[1] for k in src}}
    return build


def t_ca_bounds():
    c = {(r["regime"], r["transmissibility_mode"], g(r["change_agent_fraction"])): r
         for r in _ca("c_mechanism.csv")}
    d = {(r["regime"], r["trigger_type"], g(r["change_agent_fraction"])): r
         for r in _ca("d_trigger.csv")}
    LAB = {"permissive": "ample capacity", "constrained": "tight capacity"}
    def build(hdr):
        out = {}
        for reg, lab in LAB.items():
            for mode in ("elements_only", "whole_package"):
                n0 = float(c[(reg, mode, "0")]["final"])
                n1 = float(c[(reg, mode, "0.2")]["final"])
                out[f"{lab}, {mode}"] = [f2(n0), f2(n1), f"{n1 - n0:+.2f}"]
            n0 = float(d[(reg, "endogenous", "0")]["final"])
            n1 = float(d[(reg, "endogenous", "0.2")]["final"])
            out[f"{lab}, endogenous trigger"] = [f2(n0), f2(n1), f"{n1 - n0:+.2f}"]
        return out
    return build


def t_rate_matched():
    src = rows("rm", "rate_matched.csv")
    LAB = {"elements_only": "piecemeal",
           "whole_package_gated": "bundled, cue-matched"}
    def build(hdr):
        return {(LAB[r["mode"]], f"{float(r['elements_per_agent']):.2f}"):
                [f2(r["final"])] for r in src if r["mode"] in LAB}
    return build


def t_tiestrength_matched():
    src = rows("ts", "tiestrength_matched.csv")
    by = {(r["arm"], g(r["strong_tie_fraction"])): r for r in src}
    def build(hdr):
        return {g(f): [f2(by[("as-is", g(f))]["final"]),
                       f"{float(by[('as-is', g(f))]['elements_per_agent']):.2f}",
                       f2(by[("normalised", g(f))]["final"]),
                       f"{float(by[('normalised', g(f))]['elements_per_agent']):.2f}"]
                for f in {k[1] for k in by}}
    return build


def t_ca_robust():
    import glob as _glob
    src = []
    for f in sorted(_glob.glob(os.path.join(RESULTS, SRC["rb"], "robust_*.csv"))):
        if not f.endswith("_raw.csv"):
            src += list(csv.DictReader(open(f)))
    by = {(r["topology"], g(r["n_agents"]), r["regime"], g(r["change_agent_fraction"])): r
          for r in src}
    TL = {"small_world": "small world", "random": "random", "ring_lattice": "ring lattice"}
    RL = {"permissive": "ample", "constrained": "tight"}
    def build(hdr):
        out = {}
        for topo, tl in TL.items():
            for N in ("100", "500"):
                for reg, rl in RL.items():
                    b = by[(topo, N, reg, "0")]; m = by[(topo, N, reg, "0.2")]
                    nbt = int(m["n_big_things"])
                    base, obs = float(b["final"]), float(m["final"])
                    exp = base + 0.20 / nbt
                    out[(tl, N, rl)] = [f2(base), f2(obs), f2(exp),
                                        f"{obs - exp:+.2f}", f2(m["carrier_per_bt"])]
        return out
    return build


def t_packet_cells():
    src = {(r["capacity"], r["arm"], r["flow"]): r
           for r in rows("pk", "packetization.csv")}
    def build(hdr):
        return {k: [f"{float(v['final']):.2f} ({float(v['final_sd']):.2f})",
                    f2(v["focal_offered_per_agent"]), f2(v["focal_acquired_per_agent"]),
                    f2(v["total_acquired_per_agent"]),
                    f2(v["required_evictions_per_agent"])] for k, v in src.items()}
    return build


def t_countonly_cells():
    import glob as _g
    src = []
    for f in sorted(_g.glob(os.path.join(RESULTS, SRC["co"], "countonly_*.csv"))):
        if not f.endswith("_raw.csv"):
            src += list(csv.DictReader(open(f)))
    by = {(r["rule"], r["capacity"], g(r["loss_rate"]), r["flow"]): r for r in src}
    def build(hdr):
        return {k: [f"{float(v['adoption']):.2f} ({float(v['adoption_sd']):.2f})",
                    f2(v["carrier_per_bt"]),
                    f"{float(v['evictions_per_agent']):.0f}"] for k, v in by.items()}
    return build


def t_carrier_cells():
    src = {(r["capacity"], r["carrier_channel"], g(r["transmission_prob"])): r
           for r in rows("cc", "carrier_channel.csv")}
    def build(hdr):
        return {k: [f2(v["elements_per_agent"]), f2(v["final"]), f2(v["carrier_per_bt"])]
                for k, v in src.items()}
    return build


def isnum(s):
    try:
        float(s)
        return True
    except ValueError:
        return False



# ---------------------------------------------- carrier diagnostics (2026-08)
CARRIER_MEASURES = [("carrier_ge1", "Carrier, at least 1 component"),
                    ("carrier_ge2", "Carrier, at least 2 components (k-1)"),
                    ("pure_carrier", "Pure carrier"),
                    ("manifest_any", "Manifest for at least one big thing")]
REGIMES = [("cd", "Scheduled"), ("cde", "Endogenous")]


def t_carrier_diag():
    def _build(_hdr=None):
        """Initialization, peak and run-end for each carrier measure, both regimes.

        The peak matters: read on the endpoint alone the broad carrier measure looks
        like it shrinks, because manifestation converts carriers into adopters. The
        trajectory is what shows transmission building the population first.
        """
        out = {}
        for key, regime in REGIMES:
            ends = {r["measure"]: r for r in rows(key, "carrier_initial_vs_endpoint.csv")}
            # Past roughly t=250 runs begin reaching quiescence, so later grid points
            # are computed on a shrinking and non-random subset. A "peak" taken from
            # one surviving replication is an artifact, so only fully-populated grid
            # points count.
            full = max(int(r["n"]) for r in rows(key, "carrier_trajectory.csv"))
            traj = [r for r in rows(key, "carrier_trajectory.csv")
                    if int(r["n"]) >= full]
            for col, label in CARRIER_MEASURES:
                peak = max(float(r[col]) for r in traj)
                peak_t = [r["t"] for r in traj if abs(float(r[col]) - peak) < 1e-12][0]
                out[(label, regime)] = [f2(ends[col]["t0"]), f"{peak:.2f} (t {peak_t})",
                                        f2(ends[col]["endpoint"])]
        return out
    return _build

def t_transfer_state():
    def _build(_hdr=None):
        """Share of successful relevant transfers whose sender was nonmanifest."""
        out = {}
        for key, regime in REGIMES:
            m = {r["measure"]: r for r in rows(key, "transfer_by_sender_state.csv")}
            out[regime] = [f"{float(m['relevant']['mean']):.0f}",
                           f"{float(m['nonmanifest']['mean']):.0f}",
                           f"{float(m['manifest']['mean']):.0f}",
                           f"{float(m['share_nonmanifest']['mean']):.2f} "
                           f"({float(m['share_nonmanifest']['sd']):.2f})"]
        return out


    # ------------------------------------------- three readiness rules (2026-08)
    return _build

THREE_RULES = ("compositional", "source", "count")

def _snr_raw():
    raw = []
    for f in sorted(glob.glob(os.path.join(RESULTS, SRC["snr"], "sourcecmp_*_raw.csv"))):
        raw.extend(csv.DictReader(open(f)))
    return raw


def t_threearm_cells():
    def _build(_hdr=None):
        agg = []
        for f in sorted(glob.glob(os.path.join(RESULTS, SRC["snr"], "sourcecmp_*.csv"))):
            if not f.endswith("_raw.csv"):
                agg.extend(csv.DictReader(open(f)))
        out = {}
        for r in agg:
            out[(r["rule"], r["capacity"], g(r["loss_rate"]), r["flow"])] = [
                f"{float(r['adoption']):.2f} ({float(r['adoption_sd']):.2f})",
                f2(r["carrier_per_bt"]), f"{float(r['evictions_per_agent']):.0f}",
                f2(r["mean_distinct_sources"])]
        return out
    return _build

def t_threearm_returns():
    def _build(_hdr=None):
        by = {}
        for r in _snr_raw():
            rule, cap, loss, flow = r["cell"].split("/")
            by.setdefault((rule, cap.lstrip("c"), g(loss.lstrip("l")), flow), {})[
                int(r["rep"])] = float(r["adoption"])
        out = {}
        for rule in THREE_RULES:
            for cap in ("6", "5"):
                for loss in ("0", "0.01"):
                    lo = by[(rule, cap, loss, "low")]
                    hi = by[(rule, cap, loss, "high")]
                    d = [hi[k] - lo[k] for k in sorted(lo)]
                    m = st.mean(d)
                    se = st.pstdev(d) / math.sqrt(len(d))
                    comp = None
                    if rule != "compositional":
                        clo = by[("compositional", cap, loss, "low")]
                        chi = by[("compositional", cap, loss, "high")]
                        cd = [chi[k] - clo[k] for k in sorted(clo)]
                        comp = st.mean(cd) - m
                    out[(rule, cap, loss)] = [f"{m:+.3f}", f"{se:.3f}",
                                              "reference" if comp is None else f"{comp:+.3f}"]
        return out
    return _build


# ------------------- previously uncovered contrast tables (closed 2026-08-17)
def t_packet_contrasts():
    """Paired contrasts for the packetization test, recomputed from raw.

    This table and the count-only return table below were folded without being
    registered here, so the verifier never checked them. Both are numeric
    results derived from per-replication files, so both belong under the gate.
    """
    def _build(_hdr=None):
        raw = list(csv.DictReader(open(os.path.join(
            RESULTS, SRC["pk"], "packetization_raw.csv"))))
        by = {}
        for r in raw:
            cap, arm, flow = r["cell"].split("/")
            by.setdefault((cap, arm, flow), {})[int(r["rep"])] = float(r["final"])

        def pair(a, b):
            d = [a[k] - b[k] for k in sorted(a) if k in b]
            return st.mean(d), st.pstdev(d) / math.sqrt(len(d))

        out = {}
        for cap in ("c6", "c5"):
            C = cap.lstrip("c")
            for flow in ("low", "high"):
                m, se = pair(by[(cap, "bundled", flow)], by[(cap, "piecemeal", flow)])
                out[(C, f"bundling effect, {flow} flow")] = [f"{m:+.3f}", f"{se:.3f}"]
            for arm in ("piecemeal", "bundled"):
                m, se = pair(by[(cap, arm, "high")], by[(cap, arm, "low")])
                out[(C, f"return to flow, {arm}")] = [f"{m:+.3f}", f"{se:.3f}"]
            bh = by[(cap, "bundled", "high")]; bl = by[(cap, "bundled", "low")]
            ph = by[(cap, "piecemeal", "high")]; pl = by[(cap, "piecemeal", "low")]
            d = [(bh[k] - bl[k]) - (ph[k] - pl[k]) for k in sorted(bh)]
            out[(C, "delivery by flow interaction")] = [
                f"{st.mean(d):+.3f}", f"{st.pstdev(d) / math.sqrt(len(d)):.3f}"]
        return out
    return _build


def t_countonly_returns():
    """Paired return to flow for the original two-rule plus calibrated arms."""
    def _build(_hdr=None):
        raw = []
        for f in sorted(glob.glob(os.path.join(RESULTS, SRC["co"], "countonly_*_raw.csv"))):
            raw.extend(csv.DictReader(open(f)))
        by = {}
        for r in raw:
            rule, cap, loss, flow = r["cell"].split("/")
            by.setdefault((rule, cap.lstrip("c"), loss.lstrip("l"), flow), {})[
                int(r["rep"])] = float(r["adoption"])
        out = {}
        for rule in ("compositional", "count-literal", "count-calibrated"):
            for cap in ("6", "5"):
                for loss in ("0.0", "0.01"):
                    lo, hi = by[(rule, cap, loss, "low")], by[(rule, cap, loss, "high")]
                    d = [hi[k] - lo[k] for k in sorted(lo)]
                    out[(rule, cap, loss)] = [
                        f"{st.mean(d):+.3f}",
                        f"{st.pstdev(d) / math.sqrt(len(d)):.3f}"]
        return out
    return _build



# --------------------------------- seeded-source sensitivity (closed 2026-08-17)
SEED_MODES = [("unique", "unique origin per seeded token"),
              ("shared", "one exogenous origin per agent"),
              ("social_only", "no source until socially transmitted")]


def t_seedsource():
    """Return to flow for the source arm under three seeded-source conventions.

    The focal convention is read from the three-arm sweep rather than re-run,
    because the source arm there IS the unique-origin arm. Only the two
    alternatives needed new runs.
    """
    def _build(_hdr=None):
        by = {}
        for f in sorted(glob.glob(os.path.join(RESULTS, SRC["snr"], "sourcecmp_source_raw.csv"))):
            for r in csv.DictReader(open(f)):
                _rule, cap, loss, flow = r["cell"].split("/")
                by.setdefault(("unique", cap.lstrip("c"), g(loss.lstrip("l")), flow),
                              {})[int(r["rep"])] = float(r["adoption"])
        for mode, _lab in SEED_MODES[1:]:
            for r in csv.DictReader(open(os.path.join(
                    RESULTS, SRC["ss"], f"seedsource_{mode}_raw.csv"))):
                _tag, cap, loss, flow = r["cell"].split("/")
                by.setdefault((mode, cap.lstrip("c"), g(loss.lstrip("l")), flow),
                              {})[int(r["rep"])] = float(r["adoption"])
        out = {}
        # key on the human label, because that is what the docx column holds
        for mode, lab in SEED_MODES:
            for cap in ("6", "5"):
                for loss in ("0", "0.01"):
                    lo = by[(mode, cap, loss, "low")]
                    hi = by[(mode, cap, loss, "high")]
                    d = [hi[k] - lo[k] for k in sorted(lo)]
                    out[(lab, cap, loss)] = [
                        f"{st.mean(d):+.4f}",
                        f"{st.pstdev(d) / math.sqrt(len(d)):.4f}"]
        return out
    return _build


# ------------------------------- immediate manifestation upon readiness (2026-10)
IMM_REGIMES = [("cd", "Scheduled"), ("cde", "Endogenous"), ("cdi", "Immediate")]


def _carrier_peak(key, col):
    # same rule as t_carrier_diag: only grid points at which every replication is
    # still running count toward the peak
    traj = rows(key, "carrier_trajectory.csv")
    full = max(int(r["n"]) for r in traj)
    return max(float(r[col]) for r in traj if int(r["n"]) >= full)


def t_imm_carriers():
    def _build(_hdr=None):
        """Carrier build-up and nonmanifest traffic share under three activation timings.

        Immediate manifestation is a different stochastic regime, not a paired
        same-history contrast: the main engine draws activation from the same random
        stream as transmission, so element histories differ across timings.
        """
        out = {}
        for key, regime in IMM_REGIMES:
            ends = {r["measure"]: r for r in rows(key, "carrier_initial_vs_endpoint.csv")}
            tr = {r["measure"]: r for r in rows(key, "transfer_by_sender_state.csv")}
            out[regime] = [f2(ends["carrier_ge1"]["t0"]), f2(_carrier_peak(key, "carrier_ge1")),
                           f2(ends["carrier_ge2"]["t0"]), f2(_carrier_peak(key, "carrier_ge2")),
                           f"{float(tr['share_nonmanifest']['mean']):.2f} "
                           f"({float(tr['share_nonmanifest']['sd']):.2f})"]
        return out
    return _build


def t_imm_capacity():
    ex = {g(r["capacity"]): r for r in rows("endo", "e2_capacity_exogenous.csv")}
    en = {g(r["capacity"]): r for r in rows("endo", "e2_capacity_endogenous.csv")}
    im = {g(r["capacity"]): r for r in rows("imc", "e2_capacity_immediate.csv")}
    def build(hdr):
        return {c: [f2(ex[c]["final"]), f2(en[c]["final"]), f2(im[c]["final"])] for c in im}
    return build


def t_token_invariance():
    def _build(_hdr=None):
        out = {}
        for r in rows("tai", "token_activation_invariance.csv"):
            out[(r["rule"], r["capacity"], g(r["loss_rate"]))] = [
                f"{float(r['return_scheduled']):+.3f}", f"{float(r['return_immediate']):+.3f}",
                f"{float(r['max_abs_per_rep_diff']):g}"]
        return out
    return _build


def identify(hdr):
    """Which follow-up table is this, from its header row alone? None if not one.

    Shared by the folder and the verifier so both agree on what a table is.
    """
    h0 = hdr[0]
    if h0 == "Activation timing" and "Share from nonmanifest sender" in hdr:
        return "Immediate manifestation, carriers"
    if h0 == "Capacity" and "Adoption, immediate manifestation" in hdr:
        return "Immediate manifestation, capacity"
    if h0 == "Readiness rule" and "Return to flow, immediate" in hdr:
        return "Token activation invariance"
    if h0 == "k \\ capacity":
        return "W1 capacity x k"
    if h0 == "boost \\ enhanced":
        return "W2 stab x enhanced"
    if h0 == "Initial element density (capacity 6)":
        return "W8 density"
    if h0 == "Alpha compression":
        return "W5 ecology"
    if h0 == "Element overlap":
        return "W4 overlap"
    if h0 == "Channel":
        return "W6 coupling matrix"
    if h0 == "Trigger" and "Transmissibility mode" in hdr:
        return "Endogenous shape"
    if h0 == "Capacity" and "Adoption, scheduled trigger" in hdr:
        return "Endogenous capacity"
    if h0 == "Endogenous threshold":
        return "Endogenous threshold"
    # NB the count-only cells table shares its first two headers, so the
    # three-arm tables must be matched on a column unique to them first.
    if h0 == "Readiness rule" and "Distinct sources held" in hdr:
        return "Three-arm cells"
    if h0 == "Readiness rule" and "Loss rate" in hdr and "Return to flow" in hdr:
        return "Three-arm returns"
    if h0 == "Seed source convention":
        return "Seeded-source sensitivity"
    if h0 == "Carrier measure":
        return "Carrier diagnostics"
    if h0 == "Activation" and "Share from nonmanifest sender" in hdr:
        return "Transfers by sender state"
    if h0 == "Readiness rule" and "Evictions per agent" in hdr:
        return "Count-only cells"
    if h0 == "Readiness rule" and "Return to flow" in hdr:
        return "Count-only returns"
    if h0 == "Capacity" and "Paired difference" in hdr:
        return "Packetization contrasts"
    if h0 == "Capacity" and "Transmission channel" in hdr:
        return "Carrier channel cells"
    if h0 == "Capacity" and "Focal offered per agent" in hdr:
        return "Packetization cells"
    if h0 == "Delivery" and "Elements moved per agent" in hdr:
        return "Rate-matched transmissibility"
    # NB "Strong-tie fraction" is also the first header of the canonical
    # V2-tiestrength per-stage table, so match on a column unique to this one.
    if h0 == "Strong-tie fraction" and "Adoption, as run" in hdr:
        return "Tie strength, rate held constant"
    if h0 == "Topology" and "Shortfall" in hdr:
        return "Change agents, robustness"
    if h0 == "Seeded share":
        return "Change agents by share"
    if h0 == "Evangelism multiplier":
        return "Change agents by promotion intensity"
    if h0 == "Condition" and "No minority" in hdr:
        return "Change agents, bounding conditions"
    if h0 == "Internal coupling" and "Reversible (default)" in hdr:
        return "Reversibility evidence"
    if h0 == "Transmissibility mode":
        if "Carrier fraction (per big thing)" in hdr:
            return "W3 carriers"
        if "Observability gap" in hdr:
            return "W7 cue-gated"
    if h0 == "Loss rate":
        if "Best-response compression" in hdr and "Interior optimum" in hdr:
            return "W5c member-gated"
        if "Alpha share at compression 0" in hdr:
            return "W5b loss ladder"
    return None


BUILDERS = {
    "W1 capacity x k": (t_w1, "simple", 1),
    "W2 stab x enhanced": (t_w2, "simple", 1),
    "W3 carriers": (t_w3, "simple", 1),
    "W8 density": (t_w8, "simple", 1),
    "W7 cue-gated": (t_w7, "simple", 1),
    "W6 coupling matrix": (t_w6, "channel", 2),
    "W5 ecology": (t_w5, "simple", 1),
    "W4 overlap": (t_w4, "simple", 1),
    "Reversibility evidence": (t_rev, "simple", 1),
    "Endogenous shape": (t_endo_shape, "pair", 2),
    "Endogenous capacity": (t_endo_cap, "simple", 1),
    "Endogenous threshold": (t_endo_thr, "simple", 1),
    "Count-only cells": (t_countonly_cells, "quad", 4),
    "Carrier channel cells": (t_carrier_cells, "triple", 3),
    "Packetization cells": (t_packet_cells, "triple", 3),
    "Rate-matched transmissibility": (t_rate_matched, "pair", 2),
    "Tie strength, rate held constant": (t_tiestrength_matched, "simple", 1),
    "Change agents, robustness": (t_ca_robust, "triple", 3),
    "Change agents by share": (t_ca_fraction, "simple", 1),
    "Change agents by promotion intensity": (t_ca_evangelism, "simple", 1),
    "Change agents, bounding conditions": (t_ca_bounds, "simple", 1),
    "Carrier diagnostics": (t_carrier_diag, "pair", 2),
    "Transfers by sender state": (t_transfer_state, "simple", 1),
    "Three-arm cells": (t_threearm_cells, "quad", 4),
    "Three-arm returns": (t_threearm_returns, "triple", 3),
    "Seeded-source sensitivity": (t_seedsource, "triple", 3),
    "Count-only returns": (t_countonly_returns, "triple", 3),
    "Packetization contrasts": (t_packet_contrasts, "pair", 2),
    "Immediate manifestation, carriers": (t_imm_carriers, "simple", 1),
    "Immediate manifestation, capacity": (t_imm_capacity, "simple", 1),
    "Token activation invariance": (t_token_invariance, "triple", 3),
    "W5b loss ladder": (t_w5b, "ladder", 2),
    "W5c member-gated": (t_w5c, "ladder", 2),
}


def resolve_row(build, cur, mode):
    """Expected cell values for one table row, or None if the row has no source.

    Shared by the folder and the verifier. Keeping one implementation matters:
    when these were separate, adding a table mode to one silently broke the other.
    """
    if mode == "simple":
        key = g(cur[0]) if isnum(cur[0]) else cur[0]
        return build.get(key) or build.get(cur[0])
    if mode == "pair":
        return build.get((cur[0], cur[1]))
    if mode == "triple":
        return build.get((cur[0], cur[1], cur[2]))
    if mode == "quad":
        return build.get((cur[0], cur[1], cur[2], cur[3]))
    if mode == "channel":
        kind = "off_diagonal" if "cross" in cur[0] else "diagonal"
        return build.get((kind, g(cur[1])))
    return build.get((g(cur[0]), g(cur[1])))          # ladder


def set_cell(cell, text):
    p = cell.paragraphs[0]
    for run in list(p.runs):
        run.text = ""
    (p.runs[0] if p.runs else p.add_run("")).text = text


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    doc = docx.Document(DOCX)
    changes = 0
    tables_hit = 0

    for tbl in doc.tables:
        hdr = [c.text.strip() for c in tbl.rows[0].cells]
        label = identify(hdr)
        if label is None:
            continue
        factory, mode, start = BUILDERS[label]
        build = factory()(hdr)
        tables_hit += 1
        print(f"\n--- {label}  ({len(tbl.rows) - 1} data rows)")

        for r in tbl.rows[1:]:
            cur = [c.text.strip() for c in r.cells]
            exp = resolve_row(build, cur, mode)
            if exp is None:
                print(f"    [no source row for {cur[:2]}]")
                continue
            for j, val in enumerate(exp):
                col = start + j
                if col >= len(cur):
                    break
                if cur[col] != val:
                    changes += 1
                    print(f"    {str(cur[:start]):34s} col{col}: {cur[col]:>6} -> {val}")
                    if apply:
                        set_cell(r.cells[col], val)

    print(f"\n{tables_hit} follow-up tables matched, {changes} cell changes "
          f"({'APPLIED' if apply else 'preview only'}).")
    if apply:
        doc.save(DOCX)
        print("saved.")


if __name__ == "__main__":
    main()
