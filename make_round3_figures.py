#!/usr/bin/env python3
"""Round 3 main-text figures 1-5, rebuilt to the revised ontology.

Supersedes the figure layer inherited from Round 1. Nothing is recomputed: every
plotted value is read from stored output under results/, from the same columns
the earlier generators used. The changes are terminological, definitional, and
presentational.

What changed relative to make_manuscript_figures.py / make_revised_figures.py:

  Fig 1  "higher-order object" -> "focal object"; components -> elements;
         the retired label "latent-ready" -> "ready"; corrupted A->A shorthand
         rendered correctly; retention presented as a condition on assembly
         rather than as part of the definition of latent diffusion.
  Fig 2  Panel A series carry their own denominators (relevant actor-element
         cells vs actor-object pairs) instead of a shared "share of population".
         Panel B replaces the pure-carrier diagnostic with the broad (>=1) and
         strict (>=2) object-specific carrier measures, with dotted reference
         lines at their initialized prevalence. Panel C relabelled to elements.
  Fig 3  k is labelled as the readiness threshold, not the number of required
         elements, and the fixed four-element requirement set is stated on the
         axis so k cannot be read as the requirement set size.
  Fig 4  distinct components -> distinct elements; the x axis is the assigned
         transmission probability (0.05 / 0.20), not realized throughput; the
         panel C annotation states the ordering that holds in all four
         conditions rather than only the low-loss sign change.
  Fig 5  Titles and axis labels carry the persistence claim rather than a
         "return to transmission" framing; Panel A states that protection acts
         on spontaneous loss only; Panel B annotates the peak-to-endpoint gap.

Outputs a vector PDF and a 600 dpi PNG per figure into results/figures-round3/.

  python3 make_round3_figures.py
"""
import csv, glob, math, os, statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
OUT = os.path.join(R, "figures-round3")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.bbox": "tight", "pdf.fonttype": 42, "ps.fonttype": 42,
})

INK, MUTE, LIGHT = "#1a1a1a", "#8a8a8a", "#d9d9d9"
# Series identities are carried by marker and linestyle as well as hue, so the
# reading survives grayscale conversion.
C_ELEM, C_SRC, C_CNT = "#1b3a6b", "#3f7d5a", "#c1663b"
PALE, EVICT = "#e8eef7", "#8c3b3b"


def rows(d, name):
    with open(os.path.join(R, d, name)) as f:
        return list(csv.DictReader(f))


def save(fig, stem):
    for ext, kw in ((".pdf", {}), (".png", {"dpi": 600})):
        p = os.path.join(OUT, stem + ext)
        fig.savefig(p, **kw)
        print("wrote", os.path.relpath(p, HERE))
    plt.close(fig)


# ----------------------------------------------------------------- Figure 1
def figure1():
    """Conceptual schematic. No simulation data: this panel is an argument.

    Architecture preserved from the figure Brashears approved. Only the
    vocabulary, the retired state label, and the retention framing change.
    """
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6),
                             gridspec_kw={"width_ratios": [1, 1.5, 1.20]})
    for ax in axes:
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # -- left: the focal object and the elements that constitute it ----------
    ax = axes[0]
    ax.set_title("A focal object", loc="left")
    ax.add_patch(Rectangle((.22, .62), .56, .26, fill=False, ec=INK, lw=1.2))
    ax.text(.5, .75, "object A", ha="center", va="center", weight="bold")
    for lab, x in zip("abcd", [.16, .37, .58, .79]):
        ax.add_patch(Rectangle((x, .22), .14, .16, fc=PALE, ec=C_ELEM, lw=1))
        ax.text(x + .07, .30, lab, ha="center", va="center",
                color=C_ELEM, weight="bold")
    for x in [.23, .44, .65, .86]:
        ax.add_patch(FancyArrowPatch((x, .40), (.5, .60), arrowstyle="-",
                                     color=MUTE, lw=.7, ls=":"))
    ax.text(.5, .09, "element set: four distinct elements", ha="center", color=MUTE)
    ax.text(.5, .005, "readiness threshold: any three", ha="center", color=MUTE)

    # -- centre: elements moving through actors who do not manifest A --------
    ax = axes[1]
    ax.set_title("Elements move through nonadopters", loc="left")
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
                   edgecolor=C_ELEM, lw=1.4 if assembling else 1, zorder=2)
        ax.text(x, y, holds[k], ha="center", va="center", fontsize=7,
                color=C_ELEM, weight="bold", zorder=3)
    ax.annotate("holds a sufficient\nconfiguration (three of four)",
                xy=(.42, .40), xytext=(.40, .09),
                ha="center", fontsize=6.5, color=INK,
                arrowprops=dict(arrowstyle="->", color=MUTE, lw=.7))
    ax.text(.02, .005, "none of these actors manifests A", fontsize=6.5, color=MUTE)

    # -- right: retention as a condition on assembly, and actor state --------
    ax = axes[2]
    ax.set_title("Finite retention can prevent coexistence", loc="left")
    for i, lab in enumerate(["a", "b", "c", "z"]):
        outgoing = lab == "z"
        ax.add_patch(Rectangle((.06 + i * .17, .70), .15, .17,
                               fc="#f2dcdc" if outgoing else PALE,
                               ec=EVICT if outgoing else C_ELEM, lw=1))
        ax.text(.135 + i * .17, .785, lab, ha="center", va="center",
                color=EVICT if outgoing else C_ELEM)
    ax.annotate("", xy=(.645, .89), xytext=(.645, .975),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.1))
    ax.text(.70, .955, "d arrives", fontsize=6.2, color=C_ELEM, va="center")
    ax.annotate("", xy=(.72, .60), xytext=(.68, .69),
                arrowprops=dict(arrowstyle="->", color=EVICT, lw=1))
    ax.text(.74, .585, "z displaced", fontsize=6, color=EVICT, va="center")
    ax.text(.02, .585, "retention full", fontsize=6.5, color=MUTE)
    ax.text(.02, .50, "a condition on assembly, not part of the definition",
            fontsize=5.9, color=MUTE, style="italic")

    # actor state sequence: carrier -> ready -> manifest ("latent-ready" retired)
    for i, (lab, col) in enumerate([("carrier", C_ELEM), ("ready", C_ELEM),
                                    ("manifest", "#6b1b1b")]):
        ax.text(.10, .38 - i * .13, lab, fontsize=7, color=col, va="center")
        if i < 2:
            ax.add_patch(FancyArrowPatch((.055, .345 - i * .13), (.055, .285 - i * .13),
                                         arrowstyle="-|>", mutation_scale=7,
                                         color=MUTE, lw=.8, shrinkA=0, shrinkB=0))
    ax.text(.44, .195, "activation\ncondition", fontsize=6, color=MUTE, va="center")

    ax.plot([.02, .98], [.075, .075], color="#dddddd", lw=.8)
    ax.text(.02, -.01, "A → A    |    x+x+x → A    |    a+b+c → A",
            fontsize=6.6, color=INK, style="italic")

    fig.tight_layout()
    save(fig, "figure1_architecture_round3")


# ----------------------------------------------------------------- Figure 2
def figure2():
    tr = [r for r in rows("20260731-endogenous", "trajectories.csv")
          if r["trigger_type"] == "endogenous" and r["mode"] == "elements_only"]
    t = [int(r["t"]) for r in tr]
    sub = [float(r["substrate"]) for r in tr]        # bigthing_element_saturation
    man = [float(r["manifest_share"]) for r in tr]   # mean over actor-object pairs
    shape = {r["trigger_type"]: r for r in rows("20260731-endogenous", "e1_shape.csv")
             if r["mode"] == "elements_only"}
    onset = float(shape["endogenous"]["onset"])
    onset_sd = float(shape["endogenous"]["onset_sd"])
    sub_at = float(shape["endogenous"]["sub_at_onset"])

    ct = [r for r in rows("20260816-carrier-diagnostics-endo", "carrier_trajectory.csv")
          if int(r["n"]) >= 200]
    ct_t = [int(r["t"]) for r in ct]
    ge1 = [float(r["carrier_ge1"]) for r in ct]
    ge2 = [float(r["carrier_ge2"]) for r in ct]
    ends = {r["measure"]: r for r in
            rows("20260816-carrier-diagnostics-endo", "carrier_initial_vs_endpoint.csv")}
    ge1_0, ge1_E = float(ends["carrier_ge1"]["t0"]), float(ends["carrier_ge1"]["endpoint"])
    ge2_0, ge2_E = float(ends["carrier_ge2"]["t0"]), float(ends["carrier_ge2"]["endpoint"])

    # Panel C: decomposition of SUCCESSFUL RELEVANT TRANSFERS by sender state.
    # Not a population share.
    share = {}
    for d, lab in (("20260816-carrier-diagnostics-endo", "Locally triggered"),
                   ("20260816-carrier-diagnostics", "Scheduled")):
        m = {r["measure"]: float(r["mean"]) for r in rows(d, "transfer_by_sender_state.csv")}
        share[lab] = (m["share_nonmanifest"], 1.0 - m["share_nonmanifest"])

    fig = plt.figure(figsize=(6.5, 4.8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.45, 1], hspace=.70, wspace=.30)

    # -- A: circulation vs manifestation, each with its own denominator ------
    ax = fig.add_subplot(gs[0, 0])
    ax.plot(t, sub, color=INK, lw=1.6, ls="-",
            label="latent substrate\n(relevant actor–element cells)")
    ax.plot(t, man, color=INK, lw=1.6, ls="--",
            label="manifestation\n(mean over actor–object pairs)")
    ax.axvline(onset, color=MUTE, lw=.8, ls=":")
    ax.annotate(f"mean onset t = {onset:.0f}\n(SD {onset_sd:.0f} ticks)",
                xy=(onset, .97), xytext=(onset + 18, .97),
                fontsize=6.1, color=MUTE, va="top",
                arrowprops=dict(arrowstyle="->", color=MUTE, lw=.6))
    ax.text(.97, .06, f"substrate at each run's\nown onset = {sub_at:.2f}",
            transform=ax.transAxes, ha="right", fontsize=6.1, color=INK,
            bbox=dict(fc="white", ec=LIGHT, lw=.6, pad=2.4))
    ax.set_xlim(0, max(t)); ax.set_ylim(0, 1)
    ax.set_xlabel("tick"); ax.set_ylabel("proportion")
    ax.set_title("A. Elements accumulate before adoption", loc="left")
    ax.legend(frameon=False, loc="center right", fontsize=6.0, labelspacing=.8)

    # -- B: broad and strict object-specific carrier measures ----------------
    ax = fig.add_subplot(gs[0, 1])
    for lvl, col in ((ge1_0, INK), (ge2_0, MUTE)):
        ax.axhline(lvl, color=col, lw=.7, ls=":", zorder=0)
    lblbox = dict(fc="white", ec="none", pad=1.2)
    ax.text(.98, ge1_0 + .025, f"≥1 at initialization = {ge1_0:.2f}",
            transform=ax.get_yaxis_transform(), ha="right", fontsize=5.9,
            color=INK, bbox=lblbox)
    ax.text(.02, ge2_0 - .055, f"≥2 at initialization = {ge2_0:.2f}",
            transform=ax.get_yaxis_transform(), ha="left", fontsize=5.9,
            color=MUTE, bbox=lblbox)
    ax.plot(ct_t, ge1, "o-", color=INK, lw=1.5, ms=2.8,
            label="carriers, ≥1 relevant element")
    ax.plot(ct_t, ge2, "s--", color=MUTE, lw=1.3, ms=2.6,
            label="carriers, ≥2 relevant elements")
    # The two run-end values coincide to within 0.001; offset in x and annotate
    # once so the marker pair does not read as a single series.
    xe = max(ct_t) + 48
    ax.scatter([xe - 12], [ge1_E], marker="D", s=20, color=INK, zorder=3)
    ax.scatter([xe + 12], [ge2_E], marker="D", s=20, color=MUTE, zorder=3)
    ax.annotate(f"run end\n{ge1_E:.2f} / {ge2_E:.2f}",
                xy=(xe, (ge1_E + ge2_E) / 2 + .02), xytext=(xe, .335),
                fontsize=5.9, color=MUTE, ha="center", va="bottom",
                bbox=dict(fc="white", ec="none", pad=1.2),
                arrowprops=dict(arrowstyle="-", color=MUTE, lw=.5))
    ax.set_xlim(0, xe + 34); ax.set_ylim(0, 1)
    ax.set_xlabel("tick")
    ax.set_ylabel("share of actors\n(mean across focal objects)")
    ax.set_title("B. Transmission builds carriers", loc="left")
    ax.legend(frameon=False, loc="upper right", fontsize=6.0)

    # -- C: successful relevant-element transfers by sender state ------------
    ax = fig.add_subplot(gs[1, :])
    labels = ["Scheduled\nactivation", "Locally triggered\nactivation"]
    keys = ["Scheduled", "Locally triggered"]
    for yi, k in zip([0, 1], keys):
        non, mani = share[k]
        ax.barh(yi, non, height=.42, color="white", edgecolor=INK, lw=.9, hatch="////")
        ax.barh(yi, mani, height=.42, left=non, color=LIGHT, edgecolor=INK, lw=.9)
        ax.text(non / 2, yi, f"{non*100:.0f}%", ha="center", va="center", fontsize=7.5,
                bbox=dict(fc="white", ec="none", pad=1.4))
        ax.text(non + mani / 2, yi, f"{mani*100:.0f}%", ha="center", va="center",
                fontsize=7.5)
    ax.set_yticks([0, 1]); ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("share of successful relevant-element transfers")
    ax.set_title("C. Sender manifestation state at successful transfer", loc="left")
    ax.spines["left"].set_visible(False)
    h1 = Rectangle((0, 0), 1, 1, fc="white", ec=INK, lw=.9, hatch="////")
    h2 = Rectangle((0, 0), 1, 1, fc=LIGHT, ec=INK, lw=.9)
    ax.legend([h1, h2],
              ["Sender manifests no focal object served by the element",
               "Sender manifests at least one focal object served by the element"],
              frameon=False, loc="upper center", bbox_to_anchor=(.5, -.40), ncol=1)
    ax.text(0, -1.02, "The two shares differ by activation regime; they are not "
            "invariant model constants.",
            transform=ax.transAxes, fontsize=6.2, color=MUTE, style="italic")
    save(fig, "figure2_elements_before_adoption_round3")


# ----------------------------------------------------------------- Figure 3
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

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9),
                             gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    im = ax.imshow(M, cmap="Greys", vmin=0, vmax=1, aspect="auto", origin="lower")
    ax.set_xticks(range(len(cs))); ax.set_xticklabels(cs)
    ax.set_yticks(range(len(ks))); ax.set_yticklabels(ks)
    ax.set_xlabel("retention capacity C")
    # k is the readiness threshold, NOT the size of the requirement set, which is
    # fixed at four throughout. Stating both on the axis forecloses the misreading.
    ax.set_ylabel("readiness threshold k\n(distinct elements sufficient)")
    ax.set_title("A. Mean object-specific adoption", loc="left")

    def xpos(c):
        # cs is not uniformly spaced (…7, 8, 10); interpolate between bracketing
        # tick positions rather than assuming unit spacing.
        for i, (a, b) in enumerate(zip(cs, cs[1:])):
            if a <= c <= b:
                return i + (c - a) / (b - a)
        return float("nan")

    for yi, k in enumerate(ks):
        if k in halves:
            xi = xpos(halves[k])
            ax.scatter([xi], [yi], marker="o", s=34, facecolor="white",
                       edgecolor="black", lw=1.1, zorder=3)
            ax.text(xi, yi + .28, f"C = {halves[k]:.1f}", ha="center", fontsize=6.5,
                    color=INK, zorder=4,
                    path_effects=[pe.withStroke(linewidth=2.0, foreground="white")])
    ax.text(.02, -.34, "Requirement set fixed at four elements throughout; k is the "
            "number sufficient for readiness.",
            transform=ax.transAxes, fontsize=6.1, color=MUTE)
    ax.text(.02, -.46, "White markers: interpolated capacity at mean object-specific "
            "adoption = 0.50.",
            transform=ax.transAxes, fontsize=6.1, color=MUTE)
    fig.colorbar(im, ax=ax, fraction=.046, pad=.03)

    ax = axes[1]
    w8 = rows("20260730-102229-comments", "w8_density_under_cap.csv")
    x = [float(r["initial_element_density"]) for r in w8]
    y = [float(r["final_manifest_share"]) for r in w8]
    ax.plot(x, y, "o-", color=C_ELEM, lw=1.4, ms=4)
    ax.set_ylim(0, 1); ax.set_xlabel("element density at initialization")
    ax.set_ylabel("mean object-specific adoption")
    ax.set_title("B. More material, same endpoint (C = 6)", loc="left")
    ax.annotate(f"{y[0]:.2f}", xy=(x[0], y[0]), xytext=(x[0] + .02, y[0] + .10), fontsize=7)
    ax.annotate(f"{y[-1]:.2f}", xy=(x[-1], y[-1]), xytext=(x[-1] - .10, y[-1] + .10),
                fontsize=7)
    fig.tight_layout()
    save(fig, "figure3_retention_conversion_round3")


# ----------------------------------------------------------------- Figure 4
FLOWS = {"low": 0.05, "high": 0.20}   # assigned transmission probability


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
    rules = [("compositional", "distinct elements", C_ELEM, "o", "-"),
             ("source", "distinct senders", C_SRC, "s", "--"),
             ("count", "equal count", C_CNT, "^", ":")]

    def cell(rule, cap, loss, flow):
        return st.mean(by[(rule, cap, loss, flow)].values())

    def ret(rule, cap, loss):
        lo, hi = by[(rule, cap, loss, "low")], by[(rule, cap, loss, "high")]
        d = [hi[k] - lo[k] for k in sorted(lo)]
        return st.mean(d), st.pstdev(d) / math.sqrt(len(d))

    fig = plt.figure(figsize=(7.0, 4.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[.50, 1], hspace=.46,
                          width_ratios=[1, 1, 1.55], wspace=.62)

    # --- conceptual strip: source diversity and element identity are independent
    ax = fig.add_subplot(gs[0, :])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    rowsy = [.68, .34]
    examples = [(["a₁", "a₂", "a₃"], ("✓", "✓", "✕")),
                (["a₁", "b₁", "c₁"], ("✓", "✕", "✓"))]
    hdr = ["equal count", "distinct senders", "distinct elements"]
    for j, h in enumerate(hdr):
        ax.text(.40 + j * .19, .96, h, fontsize=6.8, color=MUTE, ha="center")
    for yi, (toks, marks) in zip(rowsy, examples):
        for i, tok in enumerate(toks):
            ax.add_patch(Rectangle((.02 + i * .085, yi - .09), .07, .19,
                                   fc="white", ec=INK, lw=.9,
                                   transform=ax.transAxes))
            ax.text(.055 + i * .085, yi, tok, fontsize=8.5, ha="center", va="center")
        for j, mk in enumerate(marks):
            ax.text(.40 + j * .19, yi, mk, fontsize=10, ha="center", va="center",
                    color=INK if mk == "✓" else MUTE)
    ax.text(0, .10, "Letter = element; subscript = sender.  Within each paired run, "
            "retained tokens are identical. Only the readiness rule changes.",
            fontsize=6.5, color=INK, style="italic")
    ax.text(0, -.02, "Distinct senders is a control for source nonredundancy, not a "
            "representation of complex contagion.",
            fontsize=6.3, color=MUTE, style="italic")

    for i, cap in enumerate(["c6", "c5"]):
        ax = fig.add_subplot(gs[1, i])
        for rule, lab, col, mk, ls in rules:
            ys = [cell(rule, cap, "l0.0", f) for f in ("low", "high")]
            ax.plot([0, 1], ys, marker=mk, linestyle=ls, color=col, lw=1.6, ms=4.5,
                    label=lab)
            ax.annotate(f"{ys[1]:.2f}", xy=(1, ys[1]), xytext=(1.06, ys[1]),
                        fontsize=6.2, color=col, va="center")
        ax.set_xticks([0, 1])
        ax.set_xticklabels([f"{FLOWS['low']:g}", f"{FLOWS['high']:g}"])
        ax.set_xlim(-.25, 1.5); ax.set_ylim(0, .75)
        ax.set_xlabel("transmission probability\n(assigned)")
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
    ax.text(.25, .97, "no loss", transform=ax.transAxes, ha="center", fontsize=6.2,
            color=MUTE)
    ax.text(.78, .97, "loss = .01", transform=ax.transAxes, ha="center", fontsize=6.2,
            color=MUTE)
    ax.set_ylim(-.11, .27)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([c[2] for c in conds], fontsize=6.2)
    ax.set_ylabel("return to increased transmission\n(paired high − low)")
    ax.set_title("C. Paired difference in final adoption", loc="left", pad=10)
    # The stable claim is the ordering, which holds in all four conditions; the
    # sign change is its sharpest instance, not the claim itself.
    ax.text(.5, -.34, "Distinct elements returns least in all four conditions.",
            transform=ax.transAxes, ha="center", fontsize=6.3, color=INK,
            style="italic")
    ax.legend(frameon=False, loc="lower right", fontsize=6.1, handletextpad=.4,
              borderpad=.2, labelspacing=.25)
    save(fig, "figure4_element_identity_round3")


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

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.1),
                             gridspec_kw={"width_ratios": [1.35, 1], "wspace": .40})

    ax = axes[0]
    im = ax.imshow(M, cmap="Greys", vmin=0, vmax=1, aspect="auto", origin="lower")
    ax.set_xticks(range(len(enh))); ax.set_xticklabels([f"{e:g}x" for e in enh])
    ax.set_yticks(range(len(prot_rows))); ax.set_yticklabels(labels)
    ax.set_xlabel("transmission multiplier")
    ax.set_ylabel("post-manifest protection\n(none to full)")
    for yi in range(len(prot_rows)):
        for xi in range(len(enh)):
            v = M[yi][xi]
            ax.text(xi, yi, f"{v:.2f}", ha="center", va="center", fontsize=6.8,
                    color="white" if v > .55 else INK)
    ax.set_title("A. Endpoint adoption by transmission\nand post-manifest stability",
                 loc="left", fontsize=8)
    # Protection acts on spontaneous loss only. Saying so on the axis prevents the
    # figure from implying protection against displacement.
    ax.text(0, -.30, "Protection reduces spontaneous loss after manifestation only. "
            "It does not prevent displacement\nwhen a new element enters a full "
            "retention set.",
            transform=ax.transAxes, fontsize=6.1, color=MUTE)
    fig.colorbar(im, ax=ax, fraction=.046, pad=.03)

    ax = axes[1]
    x = [float(r["focal_value"]) for r in agg]
    peak = [float(r["peak_manifest_share_mean"]) for r in agg]   # stored, not derived
    fin = [float(r["final_manifest_share_mean"]) for r in agg]
    ax.plot(x, peak, "s--", color=MUTE, lw=1.3, ms=4, label="peak manifestation")
    ax.plot(x, fin, "o-", color=INK, lw=1.6, ms=4.5, label="endpoint manifestation")
    for xi, p_, f_ in zip(x, peak, fin):
        ax.plot([xi, xi], [f_, p_], color=LIGHT, lw=.8, zorder=0)
    # Annotate the widening peak-to-endpoint gap: adoption generated along the
    # trajectory that does not persist.
    for xi, p_, f_ in ((x[0], peak[0], fin[0]), (x[-1], peak[-1], fin[-1])):
        ax.annotate(f"gap {p_-f_:.2f}", xy=(xi, f_ - .02), xytext=(xi, .47),
                    fontsize=6.3, color=INK, ha="center", va="top",
                    arrowprops=dict(arrowstyle="-", color=MUTE, lw=.5,
                                    shrinkA=2, shrinkB=2))
    ax.set_ylim(0, 1); ax.set_xlabel("transmission multiplier")
    ax.set_ylabel("mean object-specific manifestation")
    ax.set_xticks(x); ax.set_xticklabels([f"{v:g}x" for v in x])
    ax.set_xlim(min(x) - .35, max(x) + .35)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("B. Transmission alone,\nno spontaneous loss", loc="left", fontsize=8)
    save(fig, "figure5_post_manifest_retention_round3")


if __name__ == "__main__":
    figure1(); figure2(); figure3(); figure4(); figure5()
    print("\nRound 3 figures in", os.path.relpath(OUT, HERE))
