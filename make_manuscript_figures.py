#!/usr/bin/env python3
"""Build every figure in the frozen manuscript from stored simulation output.

Nothing here recomputes a simulation. Every plotted value is read from a CSV in
results/ and, where a contrast or standard error is plotted, it is derived from
the per-replication raw file rather than from a summary. The script emits
FIGURE_DATA_AUDIT.md alongside the figures so each panel can be traced to its
source column.

  python make_manuscript_figures.py
"""
import csv, math, os, statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
OUT = os.path.join(R, "figures-manuscript")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})
COMP, COUNT = "#1b3a6b", "#c1663b"
INK, MUTE = "#222222", "#8a8a8a"

AUDIT = []


def rows(d, n):
    with open(os.path.join(R, d, n)) as f:
        return list(csv.DictReader(f))


def audit(fig, panel, src, x, y, cond, reps, kind, unc, transform="none"):
    AUDIT.append(dict(figure=fig, panel=panel, source=src, x=x, y=y,
                      conditioning=cond, reps=reps, value_kind=kind,
                      uncertainty=unc, transform=transform))


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p)
    plt.close(fig)
    print("wrote", os.path.relpath(p, HERE))


# ---------------------------------------------------------------- Figure 1
def figure1():
    """Conceptual schematic. No simulation data: this panel is an argument."""
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5),
                             gridspec_kw={"width_ratios": [1, 1.5, 1.15]})
    for ax in axes:
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)

    # -- left: the higher-order object and its components
    ax = axes[0]
    ax.set_title("A higher-order object", loc="left")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((.22, .62), .56, .26, fill=False, ec=INK, lw=1.2))
    ax.text(.5, .75, "object A", ha="center", va="center", weight="bold")
    for i, (lab, x) in enumerate(zip("abcd", [.16, .37, .58, .79])):
        ax.add_patch(Rectangle((x, .22), .14, .16, fc="#e8eef7", ec=COMP, lw=1))
        ax.text(x + .07, .30, lab, ha="center", va="center", color=COMP, weight="bold")
    for x in [.23, .44, .65, .86]:
        ax.add_patch(FancyArrowPatch((x, .40), (.5, .60), arrowstyle="-",
                                     color=MUTE, lw=.7, ls=":"))
    ax.text(.5, .06, "constituted by distinct components", ha="center", color=MUTE)

    # -- centre: carriers transmitting single components, one assembling
    ax = axes[1]
    ax.set_title("Components move through nonadopters", loc="left")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    nodes = {"n1": (.12, .74), "n2": (.12, .30), "n3": (.42, .52),
             "n4": (.72, .78), "n5": (.72, .26)}
    edges = [("n1", "n3"), ("n2", "n3"), ("n3", "n4"), ("n3", "n5"), ("n1", "n2")]
    for a, b in edges:
        ax.plot(*zip(nodes[a], nodes[b]), color="#cccccc", lw=.8, zorder=1)
    holds = {"n1": "a", "n2": "b", "n3": "abc", "n4": "c", "n5": "a"}
    for k, (x, y) in nodes.items():
        assembling = k == "n3"
        ax.scatter([x], [y], s=340 if assembling else 210,
                   facecolor="#dce7f5" if assembling else "white",
                   edgecolor=COMP, lw=1.4 if assembling else 1, zorder=2)
        ax.text(x, y, holds[k], ha="center", va="center", fontsize=7,
                color=COMP, weight="bold", zorder=3)
    ax.annotate("holds a sufficient\nconfiguration", xy=(.42, .40), xytext=(.36, .10),
                ha="center", fontsize=6.5, color=INK,
                arrowprops=dict(arrowstyle="->", color=MUTE, lw=.7))
    ax.text(.02, .04, "none of these actors manifests A", fontsize=6.5, color=MUTE)

    # -- right: retention, displacement, and the state sequence
    ax = axes[2]
    ax.set_title("Retention and state", loc="left")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    # All retention slots are OCCUPIED. An incoming component replaces one that
    # is already held: there is no spare slot to fall into.
    for i, lab in enumerate(["a", "b", "c", "z"]):
        outgoing = lab == "z"
        ax.add_patch(Rectangle((.06 + i * .17, .70), .15, .17,
                               fc="#f2dcdc" if outgoing else "#e8eef7",
                               ec="#8c3b3b" if outgoing else COMP, lw=1))
        ax.text(.135 + i * .17, .785, lab, ha="center", va="center",
                color="#8c3b3b" if outgoing else COMP)
    # incoming lands on the occupied slot
    ax.annotate("", xy=(.645, .89), xytext=(.645, .975),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.1))
    ax.text(.70, .955, "d arrives", fontsize=6.2, color=COMP, va="center")
    # the displaced item leaves
    ax.annotate("", xy=(.72, .60), xytext=(.68, .69),
                arrowprops=dict(arrowstyle="->", color="#8c3b3b", lw=1))
    ax.text(.74, .585, "z evicted", fontsize=6, color="#8c3b3b", va="center")
    ax.text(.02, .585, "all slots full", fontsize=6.5, color=MUTE)
    for i, (lab, col) in enumerate([("carrier", COMP), ("latent-ready", COMP),
                                    ("manifest", "#6b1b1b")]):
        ax.text(.06, .38 - i * .13, lab, fontsize=7, color=col, va="center")
        if i < 2:
            ax.annotate("", xy=(.045, .30 - i * .13), xytext=(.045, .355 - i * .13),
                        arrowprops=dict(arrowstyle="->", color=MUTE, lw=.8))
    ax.text(.46, .245, "activation\ncondition", fontsize=6, color=MUTE, va="center")
    ax.plot([.02, .98], [.10, .10], color="#dddddd", lw=.8)
    ax.text(.02, .015, "A to A   |   x+x+x to A   |   a+b+c to A", fontsize=6.2,
            color=INK, style="italic")

    fig.tight_layout()
    save(fig, "figure1_architecture.png")
    audit("1", "all", "none (conceptual schematic)", "n/a", "n/a", "n/a",
          "n/a", "schematic", "none")


# ---------------------------------------------------------------- Figure 2
def figure2():
    tr = [r for r in rows("20260731-endogenous", "trajectories.csv")
          if r["trigger_type"] == "endogenous" and r["mode"] == "elements_only"]
    t = [int(r["t"]) for r in tr]
    man = [float(r["manifest_share"]) for r in tr]
    sub = [float(r["substrate"]) for r in tr]
    shape = {r["trigger_type"]: r for r in rows("20260731-endogenous", "e1_shape.csv")
             if r["mode"] == "elements_only"}
    onset = float(shape["endogenous"]["onset"])
    sub_at = float(shape["endogenous"]["sub_at_onset"])

    # Carrier trajectory, same activation regime as panel A so the two panels
    # are comparable. Beyond t=250 the number of surviving replications falls as
    # runs reach quiescence, so the line is drawn only where n = 200 and the
    # endpoint is shown as a separate marker.
    ct = rows("20260816-carrier-diagnostics-endo", "carrier_trajectory.csv")
    full = [r for r in ct if int(r["n"]) >= 200]
    ct_t = [int(r["t"]) for r in full]
    car = [float(r["carrier_ge1"]) for r in full]
    pure = [float(r["pure_carrier"]) for r in full]
    ends = {r["measure"]: r for r in
            rows("20260816-carrier-diagnostics-endo", "carrier_initial_vs_endpoint.csv")}
    car0 = float(ends["carrier_ge1"]["t0"])
    carE = float(ends["carrier_ge1"]["endpoint"])
    pureE = float(ends["pure_carrier"]["endpoint"])

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
    ax = axes[0]
    ax.plot(t, sub, color=COMP, lw=1.7, ls="-", label="relevant substrate held")
    ax.plot(t, man, color="#6b1b1b", lw=1.7, ls="--", label="manifest adoption")
    ax.axvline(onset, color=MUTE, lw=.9, ls="--")
    ax.annotate(f"mean onset\nt = {onset:.0f}", xy=(onset, .95),
                xytext=(onset + 16, .93), fontsize=6.5, color=MUTE, va="top",
                arrowprops=dict(arrowstyle="->", color=MUTE, lw=.7))
    ax.text(.97, .06, f"substrate at each run's\nown onset = {sub_at:.2f}",
            transform=ax.transAxes, ha="right", fontsize=6.2, color=INK,
            bbox=dict(fc="white", ec="#dddddd", lw=.6, pad=2.5))
    ax.set_xlabel("tick"); ax.set_ylabel("share of population")
    ax.set_title("A. Substrate accumulates before onset", loc="left")
    ax.set_ylim(0, 1); ax.set_xlim(0, max(t))
    ax.legend(frameon=False, loc="center right")

    ax = axes[1]
    ax.axhline(car0, color=COMP, lw=.8, ls=":", alpha=.75)
    ax.text(.98, car0 - .055, f"carriers at initialization = {car0:.2f}",
            transform=ax.get_yaxis_transform(), ha="right",
            fontsize=6.2, color=COMP)
    ax.plot(ct_t, car, "o-", color=COMP, lw=1.6, ms=3, label="carriers (per object)")
    ax.plot(ct_t, pure, "s--", color="#5b8a72", lw=1.3, ms=2.8, label="pure carriers")
    xe = max(ct_t) + 55
    ax.scatter([xe, xe], [carE, pureE], marker="D", s=26,
               color=[COMP, "#5b8a72"], zorder=3)
    ax.annotate("", xy=(xe - 6, carE), xytext=(max(ct_t) + 4, car[-1]),
                arrowprops=dict(arrowstyle="-", color="#cccccc", lw=.8, ls=":"))
    ax.text(xe, .04, "at run end", fontsize=6, color=MUTE, ha="center")
    ax.set_xlabel("tick"); ax.set_ylabel("share of population")
    ax.set_ylim(0, 1); ax.set_xlim(0, xe + 25)
    ax.set_title("B. Carriers are built up, then converted", loc="left")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    save(fig, "figure2_before_manifestation.png")

    audit("2", "A", "results/20260731-endogenous/trajectories.csv",
          "t", "manifest_share; substrate",
          "trigger_type=endogenous, mode=elements_only", "200",
          "mean across replications at each tick", "none plotted",
          "sub_at_onset is NOT read off this curve; see next row")
    audit("2", "A (annotation)", "results/20260731-endogenous/e1_shape.csv",
          "n/a", "onset; sub_at_onset", "trigger_type=endogenous", "200",
          "mean over replications of each run's substrate at its OWN onset",
          "onset_sd = 9.03 reported in text",
          "shown as a text box, not as a point on the mean curve")
    audit("2", "B", "results/20260816-carrier-diagnostics-endo/carrier_trajectory.csv",
          "t", "carrier_ge1; pure_carrier",
          "trigger_type=endogenous, focal spec", "200 while n=200",
          "means at each sampled tick", "sd columns available, not plotted",
          "line drawn only where all 200 replications survive; endpoint from "
          "carrier_initial_vs_endpoint.csv shown as separate diamonds")


# ---------------------------------------------------------------- Figure 3
def figure3():
    w1 = rows("20260730-102229-comments", "w1_capacity_x_k.csv")
    ks = sorted({int(r["sufficiency_k"]) for r in w1})
    cs = sorted({int(r["capacity"]) for r in w1})
    grid = {(int(r["sufficiency_k"]), int(r["capacity"])): float(r["final_manifest_share"])
            for r in w1}
    M = [[grid.get((k, c), float("nan")) for c in cs] for k in ks]

    halves = {}
    for k in ks:
        pts = sorted((c, grid[(k, c)]) for c in cs if (k, c) in grid)
        for (c0, v0), (c1, v1) in zip(pts, pts[1:]):
            if v0 < .5 <= v1:
                halves[k] = c0 + (.5 - v0) * (c1 - c0) / (v1 - v0)

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7),
                             gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    im = ax.imshow(M, cmap="viridis", vmin=0, vmax=1, aspect="auto", origin="lower")
    ax.set_xticks(range(len(cs))); ax.set_xticklabels(cs)
    ax.set_yticks(range(len(ks))); ax.set_yticklabels(ks)
    ax.set_xlabel("retention capacity C"); ax.set_ylabel("distinct components required k")
    ax.set_title("A. Final adoption", loc="left")
    def xpos(c):
        # cs is not uniformly spaced (…7, 8, 10), so map a capacity onto the
        # categorical axis by interpolating between bracketing tick positions
        # rather than assuming unit spacing.
        for i, (a, b) in enumerate(zip(cs, cs[1:])):
            if a <= c <= b:
                return i + (c - a) / (b - a)
        return float("nan")

    for yi, k in enumerate(ks):
        if k in halves:
            xi = xpos(halves[k])
            ax.scatter([xi], [yi], marker="o", s=34, facecolor="white",
                       edgecolor="black", lw=1.1, zorder=3)
            ax.text(xi, yi + .30, f"C = {halves[k]:.1f}", ha="center", fontsize=6.5,
                    color="white", zorder=3)
    # "half-adoption" was ambiguous once the metric was adjudicated: the plotted
    # quantity is final_manifest_share, i.e. MEAN OBJECT-SPECIFIC adoption, not
    # the share of unique agents manifesting at least one object.
    ax.text(.02, -.30, "white markers: interpolated capacity at mean "
            "object-specific adoption = 0.50",
            transform=ax.transAxes, fontsize=6.2, color=MUTE)
    fig.colorbar(im, ax=ax, fraction=.046, pad=.03)

    ax = axes[1]
    w8 = rows("20260730-102229-comments", "w8_density_under_cap.csv")
    x = [float(r["initial_element_density"]) for r in w8]
    y = [float(r["final_manifest_share"]) for r in w8]
    ax.plot(x, y, "o-", color=COMP, lw=1.4, ms=4)
    ax.set_ylim(0, 1); ax.set_xlabel("initial element density")
    ax.set_ylabel("final adoption")
    ax.set_title("B. More material, same endpoint (C = 6)", loc="left")
    ax.annotate(f"{y[0]:.2f}", xy=(x[0], y[0]), xytext=(x[0] + .02, y[0] + .10), fontsize=7)
    ax.annotate(f"{y[-1]:.2f}", xy=(x[-1], y[-1]), xytext=(x[-1] - .10, y[-1] + .10), fontsize=7)
    fig.tight_layout()
    save(fig, "figure3_retention_conversion.png")

    audit("3", "A", "results/20260730-102229-comments/w1_capacity_x_k.csv",
          "capacity", "final_manifest_share", "sufficiency_k in {2,3,4}", "200",
          "raw means; half-adoption overlay is LINEAR INTERPOLATION between "
          "bracketing capacities", "none plotted",
          "half-adoption points interpolated, marked as such in caption")
    audit("3", "B", "results/20260730-102229-comments/w8_density_under_cap.csv",
          "initial_element_density", "final_manifest_share", "capacity=6", "200",
          "raw means", "none plotted")


# ---------------------------------------------------------------- Figure 4
SOURCE_C = "#3f7d5a"


def _threearm():
    """Per-replication adoption keyed by (rule, cap, loss, flow) -> {rep: value}."""
    raw = []
    for f in os.listdir(os.path.join(R, "20260816-sourcenonredundant")):
        if f.endswith("_raw.csv"):
            raw += rows("20260816-sourcenonredundant", f)
    by = defaultdict(dict)
    for r in raw:
        rule, cap, loss, flow = r["cell"].split("/")
        by[(rule, cap, loss, flow)][int(r["rep"])] = float(r["adoption"])
    return by


def figure4():
    by = _threearm()
    rules = [("compositional", "distinct components", COMP, "o", "-"),
             ("source", "distinct senders", SOURCE_C, "s", "--"),
             ("count", "equal count", COUNT, "^", ":")]

    def cell(rule, cap, loss, flow):
        return st.mean(by[(rule, cap, loss, flow)].values())

    def ret(rule, cap, loss):
        lo, hi = by[(rule, cap, loss, "low")], by[(rule, cap, loss, "high")]
        d = [hi[k] - lo[k] for k in sorted(lo)]
        return st.mean(d), st.pstdev(d) / math.sqrt(len(d))

    fig = plt.figure(figsize=(7.4, 3.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.75], wspace=.45)

    for i, cap in enumerate(["c6", "c5"]):
        ax = fig.add_subplot(gs[0, i])
        for rule, lab, col, mk, ls in rules:
            ys = [cell(rule, cap, "l0.0", f) for f in ("low", "high")]
            ax.plot([0, 1], ys, marker=mk, linestyle=ls, color=col, lw=1.7,
                    ms=5, label=lab)
            ax.annotate(f"{ys[1]:.2f}", xy=(1, ys[1]), xytext=(1.07, ys[1]),
                        fontsize=6.5, color=col, va="center")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["low", "high"])
        ax.set_xlim(-.25, 1.5); ax.set_ylim(0, .75)
        ax.set_xlabel("component flow")
        if i == 0:
            ax.set_ylabel("final adoption")
            ax.legend(frameon=False, loc="upper left", fontsize=6.3)
        ax.set_title(f"{'AB'[i]}. C = {cap[1]}, no loss", loc="left")

    ax = fig.add_subplot(gs[0, 2])
    conds = [("c6", "l0.0", "C=6\nno loss"), ("c5", "l0.0", "C=5\nno loss"),
             ("c6", "l0.01", "C=6\nloss .01"), ("c5", "l0.01", "C=5\nloss .01")]
    w = .21
    for j, (rule, lab, col, mk, _ls) in enumerate(rules):
        xs = [i + (j - 1) * w for i in range(len(conds))]
        ms = [ret(rule, c, l)[0] for c, l, _ in conds]
        es = [1.96 * ret(rule, c, l)[1] for c, l, _ in conds]
        ax.errorbar(xs, ms, yerr=es, fmt=mk, color=col, ms=4.5, lw=0,
                    elinewidth=1.3, capsize=2.5, label=lab)
    ax.axhline(0, color=INK, lw=.8)
    ax.axvline(1.5, color="#dddddd", lw=1, ls=":")
    ax.text(.25, .965, "no loss", transform=ax.transAxes, ha="center",
            fontsize=6.5, color=MUTE)
    ax.text(.78, .965, "loss = .01", transform=ax.transAxes, ha="center",
            fontsize=6.5, color=MUTE)
    ax.set_ylim(-.11, .27)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([c[2] for c in conds], fontsize=6.5)
    ax.set_ylabel("return to increased flow")
    ax.set_title("C. Only distinct components turn the response negative",
                 loc="left", pad=12, fontsize=8)
    ax.legend(frameon=False, loc="lower right", fontsize=6.3)
    save(fig, "figure4_composition_vs_count.png")

    for c, l, lab in conds:
        for rule, _, _, _, _ in rules:
            m, se = ret(rule, c, l)
            audit("4", f"C [{rule}, {c}, {l}]",
                  "results/20260816-sourcenonredundant/sourcecmp_*_raw.csv",
                  "condition", "adoption", f"rule={rule}, {c}, {l}", "200 paired",
                  f"paired contrast high-low = {m:+.4f}", f"paired SE = {se:.4f}")
    audit("4", "A and B", "results/20260816-sourcenonredundant/sourcecmp_*_raw.csv",
          "flow (low=0.05, high=0.20 transmission prob)", "adoption",
          "loss=0; C=6 (A), C=5 (B); three readiness rules", "200 paired",
          "raw means", "not plotted on A/B; see C")


# ---------------------------------------------------------------- Figure 5
def figure5():
    w2 = rows("20260730-102229-comments", "w2_stab_x_enh.csv")
    boosts = sorted({float(r["stabilization_boost"]) for r in w2})
    enh = sorted({float(r["enhanced_factor"]) for r in w2})
    g = {(float(r["stabilization_boost"]), float(r["enhanced_factor"])):
         float(r["final_manifest_share"]) for r in w2}
    prot_rows = sorted(boosts, reverse=True)      # boost 1.0 (no protection) first
    M = [[g[(b, e)] for e in enh] for b in prot_rows]
    labels = [f"{1-b:.2f}" for b in prot_rows]

    agg = [r for r in rows("20260730-093338-full", "aggregated.csv")
           if r["phase"] == "V2-enhanced"]

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9),
                             gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    im = ax.imshow(M, cmap="magma", vmin=0, vmax=1, aspect="auto", origin="lower")
    ax.set_xticks(range(len(enh))); ax.set_xticklabels([f"{e:g}x" for e in enh])
    ax.set_yticks(range(len(prot_rows))); ax.set_yticklabels(labels)
    ax.set_xlabel("transmission multiplier")
    ax.set_ylabel("retention protection (none to full)")
    for yi in range(len(prot_rows)):
        for xi in range(len(enh)):
            v = M[yi][xi]
            ax.text(xi, yi, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                    color="white" if v < .6 else "black")
    fig.colorbar(im, ax=ax, fraction=.046, pad=.03)
    ax.set_title("A. Protection raises the return to transmission", loc="left")

    ax = axes[1]
    x = [float(r["focal_value"]) for r in agg]
    ax.plot(x, [float(r["final_manifest_share_mean"]) for r in agg], "o-",
            color=COMP, lw=1.6, ms=4.5, label="final adoption")
    ax.plot(x, [float(r["overshoot_mean"]) for r in agg], "s--",
            color=MUTE, lw=1.2, ms=3.5, label="overshoot")
    ax.set_ylim(0, .8); ax.set_xlabel("transmission multiplier")
    ax.set_ylabel("share")
    ax.legend(frameon=False, loc="center right")
    ax.set_title("B. Transmission alone, unprotected", loc="left")
    fig.tight_layout()
    save(fig, "figure5_retention_returns.png")

    audit("5", "A", "results/20260730-102229-comments/w2_stab_x_enh.csv",
          "enhanced_factor", "final_manifest_share",
          "stabilization_boost in {0,.25,.5,.75,1}", "200", "raw means",
          "none plotted",
          "y axis RECODED: protection = 1 - stabilization_boost, so raw boost=0 "
          "(maximal protection) plots at protection=1.00")
    audit("5", "B", "results/20260730-093338-full/aggregated.csv",
          "focal_value (enhanced_factor)",
          "final_manifest_share_mean; overshoot_mean", "phase=V2-enhanced", "200",
          "raw means", "not plotted")


# ------------------------------------------------------- Supplementary S-x
def figureS_advocates():
    a = rows("20260814-changeagent", "a_fraction.csv")
    b = rows("20260814-changeagent", "b_evangelism.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6))
    styles = {"permissive": ("#1b3a6b", "higher capacity (C=6)"),
              # The advocate experiments use REGIMES = {permissive: 6,
              # constrained: 4} in explore_changeagent{,_robust}.py, and the
              # stored output contains capacities 4 and 6 only. The label read
              # C=5, which was wrong. Label only -- no data path changed.
              "constrained": ("#c1663b", "lower capacity (C=4)")}
    ax = axes[0]
    for reg, (col, lab) in styles.items():
        pts = sorted((float(r["change_agent_fraction"]), float(r["final"]),
                      float(r["carrier_per_bt"]))
                     for r in a if r["regime"] == reg and r["change_agent_fraction"])
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "o-", color=col, lw=1.5,
                ms=4, label=f"{lab}, adoption")
        ax.plot([p[0] for p in pts], [p[2] for p in pts], "s--", color=col, lw=1.1,
                ms=3.5, alpha=.55, label=f"{lab}, carriers")
    ax.set_xlabel("seeded manifest share"); ax.set_ylabel("share")
    ax.set_ylim(0, 1); ax.set_title("A. Seeding advocates", loc="left")
    ax.legend(frameon=False, fontsize=6)

    ax = axes[1]
    for reg, (col, lab) in styles.items():
        pts = sorted((float(r["change_agent_evangelism"]), float(r["final"]))
                     for r in b if r["regime"] == reg)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "o-", color=col, lw=1.5,
                ms=4, label=lab)
        ax.annotate(f"{pts[-1][1]:.2f}", xy=pts[-1], xytext=(pts[-1][0] - 1.4,
                    pts[-1][1] + .04), fontsize=6.5, color=col)
    ax.set_xscale("log", base=2); ax.set_xticks([1, 2, 4, 8])
    ax.set_xticklabels(["1x", "2x", "4x", "8x"])
    ax.set_xlabel("advocate transmission multiplier"); ax.set_ylabel("final adoption")
    ax.set_ylim(0, .85)
    ax.set_title("B. Sign changes with the binding constraint", loc="left")
    ax.legend(frameon=False, fontsize=6.5)
    fig.tight_layout()
    save(fig, "figureS_advocates.png")

    audit("S-advocates", "A", "results/20260814-changeagent/a_fraction.csv",
          "change_agent_fraction", "final; carrier_per_bt",
          "regime in {permissive C=6, constrained C=4}", "200", "raw means",
          "final_sd available, not plotted")
    audit("S-advocates", "B", "results/20260814-changeagent/b_evangelism.csv",
          "change_agent_evangelism", "final", "regime", "200", "raw means",
          "not plotted", "x axis log base 2")


def figureS_carriers():
    """Sensitivity of the carrier construct to its threshold, under both regimes."""
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), sharey=True)
    srcs = [("20260816-carrier-diagnostics", "A. Scheduled activation"),
            ("20260816-carrier-diagnostics-endo", "B. Endogenous activation")]
    for ax, (d, title) in zip(axes, srcs):
        ct = [r for r in rows(d, "carrier_trajectory.csv") if int(r["n"]) >= 200]
        t = [int(r["t"]) for r in ct]
        ends = {r["measure"]: r for r in rows(d, "carrier_initial_vs_endpoint.csv")}
        for key, col, lab in (("carrier_ge1", COMP, "carrier: at least 1 component"),
                              ("carrier_ge2", "#8c3b3b",
                               "carrier: at least 2 (= k-1) components")):
            y = [float(r[key]) for r in ct]
            ax.plot(t, y, "o-", color=col, lw=1.5, ms=3, label=lab)
            ax.axhline(float(ends[key]["t0"]), color=col, lw=.8, ls=":", alpha=.7)
            ax.scatter([max(t) + 40], [float(ends[key]["endpoint"])], marker="D",
                       s=24, color=col, zorder=3)
        ax.set_xlim(0, max(t) + 70); ax.set_ylim(0, 1)
        ax.set_xlabel("tick"); ax.set_title(title, loc="left")
        ax.text(max(t) + 40, .03, "end", fontsize=6, color=MUTE, ha="center")
    axes[0].set_ylabel("share of population")
    axes[0].legend(frameon=False, loc="lower right", fontsize=6.2)
    fig.tight_layout()
    save(fig, "figureS_carrier_sensitivity.png")
    for d, reg in (("20260816-carrier-diagnostics", "exogenous"),
                   ("20260816-carrier-diagnostics-endo", "endogenous")):
        audit("S-carriers", reg, f"results/{d}/carrier_trajectory.csv",
              "t", "carrier_ge1; carrier_ge2", f"trigger={reg}, focal spec",
              "200 while n=200", "means at sampled ticks", "sd columns available",
              "dotted horizontals are t=0 values; diamonds are run-end values "
              "from carrier_initial_vs_endpoint.csv")


def write_audit():
    cols = ["figure", "panel", "source", "x", "y", "conditioning", "reps",
            "value_kind", "uncertainty", "transform"]
    p = os.path.join(OUT, "FIGURE_DATA_AUDIT.md")
    with open(p, "w") as f:
        f.write("# Figure data audit\n\nEvery plotted value traces to a stored "
                "output file. No value is interpolated except where the transform "
                "column says so.\n\n")
        f.write("| " + " | ".join(cols) + " |\n")
        f.write("|" + "---|" * len(cols) + "\n")
        for r in AUDIT:
            f.write("| " + " | ".join(str(r.get(c, "")).replace("|", "/")
                                      for c in cols) + " |\n")
    print("wrote", os.path.relpath(p, HERE))


if __name__ == "__main__":
    figure1(); figure2(); figure3(); figure4(); figure5()
    figureS_advocates(); figureS_carriers()
    write_audit()
    print("\nall figures in", os.path.relpath(OUT, HERE))
