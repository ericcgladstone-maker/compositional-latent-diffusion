#!/usr/bin/env python3
"""Revised main-text figures 2, 4 and 5.

Separate from make_manuscript_figures.py so the original generator stays intact
and the two can be compared. Every plotted value is read from stored output
under results/. Nothing is recomputed and nothing is taken from prose.

Outputs, for each figure, a vector PDF and a 600 dpi PNG into
results/figures-revised/.

  python make_revised_figures.py
"""
import csv, glob, math, os, statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
OUT = os.path.join(R, "figures-revised")
os.makedirs(OUT, exist_ok=True)

# typography held consistent across the three revised figures
plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.bbox": "tight", "pdf.fonttype": 42, "ps.fonttype": 42,
})
INK, MUTE, LIGHT = "#1a1a1a", "#8a8a8a", "#d9d9d9"
# grayscale-safe series identities: interpretation never depends on colour
C_COMP, C_SRC, C_CNT = "#1b3a6b", "#3f7d5a", "#c1663b"


def rows(d, name):
    with open(os.path.join(R, d, name)) as f:
        return list(csv.DictReader(f))


def save(fig, stem):
    for ext, kw in ((".pdf", {}), (".png", {"dpi": 600})):
        p = os.path.join(OUT, stem + ext)
        fig.savefig(p, **kw)
        print("wrote", os.path.relpath(p, HERE))
    plt.close(fig)


# ----------------------------------------------------------------- Figure 2
def figure2():
    tr = [r for r in rows("20260731-endogenous", "trajectories.csv")
          if r["trigger_type"] == "endogenous" and r["mode"] == "elements_only"]
    t = [int(r["t"]) for r in tr]
    sub = [float(r["substrate"]) for r in tr]
    man = [float(r["manifest_share"]) for r in tr]
    shape = {r["trigger_type"]: r for r in rows("20260731-endogenous", "e1_shape.csv")
             if r["mode"] == "elements_only"}
    onset = float(shape["endogenous"]["onset"])
    sub_at = float(shape["endogenous"]["sub_at_onset"])

    ct = [r for r in rows("20260816-carrier-diagnostics-endo", "carrier_trajectory.csv")
          if int(r["n"]) >= 200]
    ct_t = [int(r["t"]) for r in ct]
    car = [float(r["carrier_ge1"]) for r in ct]
    pure = [float(r["pure_carrier"]) for r in ct]
    ends = {r["measure"]: r for r in
            rows("20260816-carrier-diagnostics-endo", "carrier_initial_vs_endpoint.csv")}
    car0 = float(ends["carrier_ge1"]["t0"])
    carE = float(ends["carrier_ge1"]["endpoint"])
    pureE = float(ends["pure_carrier"]["endpoint"])

    # Panel C: decomposition of SUCCESSFUL RELEVANT TRANSFERS by sender state.
    # Not a population share. Sender state is defined per transferred component.
    share = {}
    for d, lab in (("20260816-carrier-diagnostics-endo", "Locally triggered"),
                   ("20260816-carrier-diagnostics", "Scheduled")):
        m = {r["measure"]: float(r["mean"]) for r in rows(d, "transfer_by_sender_state.csv")}
        share[lab] = (m["share_nonmanifest"], 1.0 - m["share_nonmanifest"])

    fig = plt.figure(figsize=(6.5, 4.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.45, 1], hspace=.62, wspace=.28)

    ax = fig.add_subplot(gs[0, 0])
    ax.plot(t, sub, color=INK, lw=1.6, ls="-", label="relevant components held")
    ax.plot(t, man, color=INK, lw=1.6, ls="--", label="manifest adoption")
    ax.axvline(onset, color=MUTE, lw=.8, ls=":")
    ax.annotate(f"mean onset\nt = {onset:.0f}", xy=(onset, .95), xytext=(onset + 16, .93),
                fontsize=6.3, color=MUTE, va="top",
                arrowprops=dict(arrowstyle="->", color=MUTE, lw=.6))
    ax.text(.97, .06, f"substrate at each run's\nown onset = {sub_at:.2f}",
            transform=ax.transAxes, ha="right", fontsize=6.1, color=INK,
            bbox=dict(fc="white", ec=LIGHT, lw=.6, pad=2.4))
    ax.set_xlim(0, max(t)); ax.set_ylim(0, 1)
    ax.set_xlabel("tick"); ax.set_ylabel("share of population")
    ax.set_title("A. Components accumulate before adoption", loc="left")
    ax.legend(frameon=False, loc="center right")

    ax = fig.add_subplot(gs[0, 1])
    ax.axhline(car0, color=MUTE, lw=.8, ls=":")
    ax.text(.02, car0 + .022, f"carriers at initialization = {car0:.2f}",
            transform=ax.get_yaxis_transform(), ha="left", fontsize=6.1, color=MUTE)
    ax.plot(ct_t, car, "o-", color=INK, lw=1.5, ms=2.8, label="carriers (per object)")
    ax.plot(ct_t, pure, "s--", color=MUTE, lw=1.2, ms=2.6, label="pure carriers")
    xe = max(ct_t) + 55
    ax.scatter([xe, xe], [carE, pureE], marker="D", s=22, color=[INK, MUTE], zorder=3)
    ax.text(xe, .04, "run end", fontsize=6, color=MUTE, ha="center")
    ax.set_xlim(0, xe + 25); ax.set_ylim(0, 1)
    ax.set_xlabel("tick"); ax.set_ylabel("share of population")
    ax.set_title("B. Carriers are built, then converted", loc="left")
    ax.legend(frameon=False, loc="upper right")

    ax = fig.add_subplot(gs[1, :])
    labels = ["Scheduled\nactivation", "Locally triggered\nactivation"]
    keys = ["Scheduled", "Locally triggered"]
    y = [0, 1]
    for yi, k in zip(y, keys):
        non, mani = share[k]
        ax.barh(yi, non, height=.42, color="white", edgecolor=INK, lw=.9, hatch="////")
        ax.barh(yi, mani, height=.42, left=non, color=LIGHT, edgecolor=INK, lw=.9)
        ax.text(non / 2, yi, f"{non*100:.0f}%", ha="center", va="center", fontsize=7.5,
                bbox=dict(fc="white", ec="none", pad=1.4))
        ax.text(non + mani / 2, yi, f"{mani*100:.0f}%", ha="center", va="center", fontsize=7.5)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("share of successful relevant component transfers")
    ax.set_title("C. Who transmits: decomposition of successful transfers by sender state",
                 loc="left")
    ax.spines["left"].set_visible(False)
    h1 = Rectangle((0, 0), 1, 1, fc="white", ec=INK, lw=.9, hatch="////")
    h2 = Rectangle((0, 0), 1, 1, fc=LIGHT, ec=INK, lw=.9)
    # Sender state is classified by any(bid in sender.manifest for bid in owners):
    # a sender counts as manifest if it manifests AT LEAST ONE object served by
    # the transferred component. This matters only for the shared component,
    # which both objects require. Labels must not imply per-object evaluation.
    ax.legend([h1, h2],
              ["Sender manifests no object served by component",
               "Sender manifests at least one object served by component"],
              frameon=False, loc="upper center", bbox_to_anchor=(.5, -.42), ncol=2)
    ax.text(0, -.98, "For components serving both objects, a sender is classified as "
            "manifest if either associated object is manifest.",
            transform=ax.transAxes, fontsize=6.2, color=MUTE)
    save(fig, "figure2_components_before_adoption_revised")


# ----------------------------------------------------------------- Figure 4
def _threearm():
    raw = []
    for f in glob.glob(os.path.join(R, "20260816-sourcenonredundant", "sourcecmp_*_raw.csv")):
        raw += list(csv.DictReader(open(f)))
    by = defaultdict(dict)
    for r in raw:
        rule, cap, loss, flow = r["cell"].split("/")
        by[(rule, cap, loss, flow)][int(r["rep"])] = float(r["adoption"])
    return by


def figure4():
    by = _threearm()
    rules = [("compositional", "distinct components", C_COMP, "o", "-"),
             ("source", "distinct senders", C_SRC, "s", "--"),
             ("count", "equal count", C_CNT, "^", ":")]

    def cell(rule, cap, loss, flow):
        return st.mean(by[(rule, cap, loss, flow)].values())

    def ret(rule, cap, loss):
        lo, hi = by[(rule, cap, loss, "low")], by[(rule, cap, loss, "high")]
        d = [hi[k] - lo[k] for k in sorted(lo)]
        return st.mean(d), st.pstdev(d) / math.sqrt(len(d))

    fig = plt.figure(figsize=(6.5, 4.5))
    gs = fig.add_gridspec(2, 3, height_ratios=[.46, 1], hspace=.40,
                          width_ratios=[1, 1, 1.55], wspace=.42)

    # --- conceptual strip: why source and component diversity are independent ---
    ax = fig.add_subplot(gs[0, :])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    rowsy = [.66, .30]
    examples = [(["a₁", "a₂", "a₃"], ("✓", "✓", "×")),
                (["a₁", "b₁", "c₁"], ("✓", "×", "✓"))]
    hdr = ["equal count", "distinct senders", "distinct components"]
    for j, h in enumerate(hdr):
        ax.text(.40 + j * .19, .95, h, fontsize=6.8, color=MUTE, ha="center")
    for yi, (toks, marks) in zip(rowsy, examples):
        for i, tok in enumerate(toks):
            ax.add_patch(Rectangle((.02 + i * .085, yi - .09), .07, .19,
                                   fc="white", ec=INK, lw=.9,
                                   transform=ax.transAxes))
            ax.text(.055 + i * .085, yi, tok, fontsize=8.5, ha="center", va="center")
        for j, mk in enumerate(marks):
            ax.text(.40 + j * .19, yi, mk, fontsize=10, ha="center", va="center",
                    color=INK if mk == "✓" else MUTE)
    ax.text(0, .02, "Letter = component; subscript = sender.  Within each paired run, "
            "retained tokens are identical. Only the readiness rule changes.",
            fontsize=6.6, color=INK, style="italic")

    for i, cap in enumerate(["c6", "c5"]):
        ax = fig.add_subplot(gs[1, i])
        for rule, lab, col, mk, ls in rules:
            ys = [cell(rule, cap, "l0.0", f) for f in ("low", "high")]
            ax.plot([0, 1], ys, marker=mk, linestyle=ls, color=col, lw=1.6, ms=4.5,
                    label=lab)
            ax.annotate(f"{ys[1]:.2f}", xy=(1, ys[1]), xytext=(1.06, ys[1]),
                        fontsize=6.2, color=col, va="center")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["low", "high"])
        ax.set_xlim(-.25, 1.5); ax.set_ylim(0, .75)
        ax.set_xlabel("component flow")
        if i == 0:
            ax.set_ylabel("final adoption")
            ax.legend(frameon=False, loc="center left", fontsize=6.1,
                      handletextpad=.4, borderpad=.2, labelspacing=.25)
        ax.set_title(f"{'AB'[i]}. C = {cap[1]}, no loss", loc="left")

    ax = fig.add_subplot(gs[1, 2])
    conds = [("c6", "l0.0", "C=6\nno loss"), ("c5", "l0.0", "C=5\nno loss"),
             ("c6", "l0.01", "C=6\nloss .01"), ("c5", "l0.01", "C=5\nloss .01")]
    w = .21
    for j, (rule, lab, col, mk, _ls) in enumerate(rules):
        xs = [i + (j - 1) * w for i in range(len(conds))]
        ms = [ret(rule, c, l)[0] for c, l, _ in conds]
        es = [1.96 * ret(rule, c, l)[1] for c, l, _ in conds]
        ax.errorbar(xs, ms, yerr=es, fmt=mk, color=col, ms=4, lw=0,
                    elinewidth=1.1, capsize=2.2, label=lab)
    ax.axhline(0, color=INK, lw=.7)
    ax.axvline(1.5, color=LIGHT, lw=1, ls=":")
    ax.text(.25, .97, "no loss", transform=ax.transAxes, ha="center", fontsize=6.2, color=MUTE)
    ax.text(.78, .97, "loss = .01", transform=ax.transAxes, ha="center", fontsize=6.2, color=MUTE)
    ax.set_ylim(-.10, .27)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([c[2] for c in conds], fontsize=6.2)
    ax.set_ylabel("return to increased flow")
    ax.set_title("C. Paired high-minus-low difference", loc="left", pad=10)
    ax.legend(frameon=False, loc="lower right", fontsize=6.1, handletextpad=.4,
              borderpad=.2, labelspacing=.25)
    save(fig, "figure4_component_identity_revised")


# ----------------------------------------------------------------- Figure 5
def figure5():
    w2 = rows("20260730-102229-comments", "w2_stab_x_enh.csv")
    boosts = sorted({float(r["stabilization_boost"]) for r in w2})
    enh = sorted({float(r["enhanced_factor"]) for r in w2})
    g = {(float(r["stabilization_boost"]), float(r["enhanced_factor"])):
         float(r["final_manifest_share"]) for r in w2}
    # display recoding: protection = 1 - stabilization_boost, so higher means more
    prot_rows = sorted(boosts, reverse=True)
    M = [[g[(b, e)] for e in enh] for b in prot_rows]
    labels = [f"{1-b:.2f}" for b in prot_rows]

    agg = sorted([r for r in rows("20260730-093338-full", "aggregated.csv")
                  if r["phase"] == "V2-enhanced"], key=lambda r: float(r["focal_value"]))

    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.0),
                             gridspec_kw={"width_ratios": [1.35, 1], "wspace": .34})

    ax = axes[0]
    im = ax.imshow(M, cmap="Greys", vmin=0, vmax=1, aspect="auto", origin="lower")
    ax.set_xticks(range(len(enh))); ax.set_xticklabels([f"{e:g}x" for e in enh])
    ax.set_yticks(range(len(prot_rows))); ax.set_yticklabels(labels)
    ax.set_xlabel("transmission multiplier")
    ax.set_ylabel("protection of manifested configurations\n(none to full)")
    for yi in range(len(prot_rows)):
        for xi in range(len(enh)):
            v = M[yi][xi]
            ax.text(xi, yi, f"{v:.2f}", ha="center", va="center", fontsize=6.8,
                    color="white" if v > .55 else INK)
    ax.set_title("A. Transmission × post-manifest protection,\nwith spontaneous loss",
                 loc="left", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=.046, pad=.03)

    ax = axes[1]
    x = [float(r["focal_value"]) for r in agg]
    peak = [float(r["peak_manifest_share_mean"]) for r in agg]   # stored, not derived
    fin = [float(r["final_manifest_share_mean"]) for r in agg]
    ax.plot(x, peak, "s--", color=MUTE, lw=1.3, ms=4, label="peak adoption")
    ax.plot(x, fin, "o-", color=INK, lw=1.6, ms=4.5, label="final adoption")
    for xi, p_, f_ in zip(x, peak, fin):
        ax.plot([xi, xi], [f_, p_], color=LIGHT, lw=.8, zorder=0)
    ax.set_ylim(0, 1); ax.set_xlabel("transmission multiplier")
    ax.set_ylabel("share of population")
    ax.set_xticks(x); ax.set_xticklabels([f"{v:g}x" for v in x])
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("B. Transmission alone,\nno spontaneous loss", loc="left", fontsize=8)
    save(fig, "figure5_retention_transmission_revised")


if __name__ == "__main__":
    figure2(); figure4(); figure5()
    print("\nrevised figures in", os.path.relpath(OUT, HERE))
