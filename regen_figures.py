#!/usr/bin/env python3
"""Regenerate every figure embedded in the docx from the 200-replication runs.

The document's figures were drawn from 30-replication data. Once the tables are
updated a figure drawn from the old data would disagree with the table above it,
so all fourteen are rebuilt from the same sources the tables now cite.

Two of them had no generator in the repo and are defined here:
  - the W5c inverted-U line chart (previously produced ad hoc)
  - nothing else; the rest delegate to the existing report scripts

Usage: python regen_figures.py
Prints the path of every figure it wrote.
"""
import csv, glob, os, subprocess, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
PY = sys.executable

CANON = os.environ.get("SRC_canon", "20260730-093338-full")
FIGDIR = os.path.join(RESULTS, "figures-200rep")

SERIF = {"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
         "font.size": 10}

# the six per-stage figures embedded in the doc, in document order
STAGE_FIGS = ["V1", "V2-stabilization", "V2-enhanced", "V2-tiestrength",
              "V2-internal-coupling", "V2-neighbor-coupling"]


def newest(pattern):
    ds = sorted(glob.glob(os.path.join(RESULTS, pattern)))
    return ds[-1] if ds else None


def stage_figures():
    """Per-stage adoption/overshoot/lapse figures, from the new canon."""
    import results_to_docx as R
    rows = list(csv.DictReader(open(os.path.join(RESULTS, CANON, "aggregated.csv"))))
    by = {}
    for r in rows:
        by.setdefault(r["phase"], {})[str(r["focal_value"])] = r
    os.makedirs(FIGDIR, exist_ok=True)
    out = []
    for pid in STAGE_FIGS:
        p = os.path.join(FIGDIR, f"{pid}.png")
        R.make_figure(pid, by, p)
        out.append(p)
    return out


def w5c_figure():
    """alpha's captured share vs its own compression, one line per loss level,
    at a fixed rival. The inverted-U is the interior peak on the lossy lines."""
    d = newest("*merged-comments4") or newest("*-comments4")
    src = os.path.join(d, "w5c_member_gated.csv")
    rows = list(csv.DictReader(open(src)))
    rival = "0.5"
    series = {}
    for r in rows:
        if f"{float(r['beta_compression']):g}" != rival:
            continue
        series.setdefault(float(r["loss_rate"]), []).append(
            (float(r["alpha_compression"]), float(r["alpha_share"])))
    for k in series:
        series[k].sort()
    # At 200 replications the best response is at the edge for loss 0 and 0.001
    # and interior from 0.002 up, so the result is a threshold. The figure plots
    # 0.001 (the last edge case) in place of 0.004, which brackets that threshold:
    # two curves that fall monotonically, then two with an interior peak. Four
    # series keeps the grayscale line styles distinguishable in print.
    WANT = [0.0, 0.001, 0.002, 0.006]
    losses = [l for l in WANT if l in series]
    styles = [("-", "o", "0.0"), ("--", "s", "0.35"), (":", "^", "0.55"),
              ("-.", "D", "0.7")]
    plt.rcParams.update(SERIF)
    fig, ax = plt.subplots(figsize=(5.4, 3.1))
    for (ls, mk, col), loss in zip(styles, losses):
        xs = [a for a, _ in series[loss]]
        ys = [v for _, v in series[loss]]
        ax.plot(xs, ys, ls=ls, marker=mk, color=col, lw=1.4, ms=5,
                label=f"loss = {loss:g}")
    ax.set_xlabel("alpha compression rate (encapsulation / retention)")
    ax.set_ylabel("alpha captured share")
    ax.set_title(f"rival compression = {rival}", fontsize=9, loc="right")
    ax.grid(True, color="0.9", lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="best")
    fig.tight_layout()
    os.makedirs(FIGDIR, exist_ok=True)
    p = os.path.join(FIGDIR, "fig_w5c_inverted_u.png")
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return [p]


def endogenous_figure(src_dir=None):
    """Substrate and adoption over time, scheduled trigger versus endogenous.

    Two panels sharing a y axis. The substrate curve is nearly identical in both
    panels because transmission does not depend on the trigger; what changes is
    the shape of adoption, which is the point of the comparison.
    """
    d = src_dir or newest("*-endogenous")
    rows = list(csv.DictReader(open(os.path.join(d, "trajectories.csv"))))
    plt.rcParams.update(SERIF)
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.9), sharey=True)
    titles = {"exogenous": "scheduled trigger", "endogenous": "endogenous trigger"}
    for ax, trig in zip(axes, ("exogenous", "endogenous")):
        r = [x for x in rows if x["trigger_type"] == trig]
        t = [int(x["t"]) for x in r]
        ax.plot(t, [float(x["substrate"]) for x in r], ls="--", color="0.45", lw=1.4,
                label="substrate held")
        ax.plot(t, [float(x["manifest_share"]) for x in r], ls="-", color="0.0", lw=1.6,
                label="adoption")
        ax.set_title(titles[trig], fontsize=9)
        ax.set_xlabel("tick")
        ax.grid(True, color="0.9", lw=0.6)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("share of population")
    axes[0].legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    os.makedirs(FIGDIR, exist_ok=True)
    p = os.path.join(FIGDIR, "fig_endogenous_trigger.png")
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return [p]


def changeagent_figure(src_dir=None):
    """Adoption against the size of the seeded minority, in both regimes.

    The dashed reference is what adoption would be if every seeded adopter simply
    stayed adopted and recruited no one: the no-agent baseline plus the share the
    minority itself contributes at the start, which is its fraction divided by the
    number of big things. Observed adoption falls below that line, so the seed
    does not even persist intact.
    """
    d = src_dir or newest("*-changeagent")
    rows = [r for r in csv.DictReader(open(os.path.join(d, "a_fraction.csv")))
            if r["change_agent_fraction"] not in ("", "None")]
    n_big = 2   # the build's change-agent stage runs two big things
    plt.rcParams.update(SERIF)
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    styles = {"permissive": ("-", "o", "0.0"), "constrained": ("--", "s", "0.45")}
    for reg, (ls, mk, col) in styles.items():
        rs = sorted([r for r in rows if r["regime"] == reg],
                    key=lambda r: float(r["change_agent_fraction"]))
        xs = [float(r["change_agent_fraction"]) for r in rs]
        ys = [float(r["final"]) for r in rs]
        base = ys[0]
        ax.plot(xs, ys, ls=ls, marker=mk, color=col, lw=1.6, ms=5, label=reg)
        ax.plot(xs, [base + x / n_big for x in xs], ls=":", color=col, lw=1.2)
    ax.set_xlabel("share of population seeded as equipped, manifest adopters")
    ax.set_ylabel("final adoption")
    ax.grid(True, color="0.9", lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="center left")
    ax.text(0.02, 0.97, "dotted: if each seeded adopter merely stayed adopted",
            transform=ax.transAxes, fontsize=7.5, va="top", color="0.3")
    fig.tight_layout()
    os.makedirs(FIGDIR, exist_ok=True)
    p = os.path.join(FIGDIR, "fig_changeagent.png")
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return [p]


def rate_matched_figure(src_dir=None):
    """Adoption against material actually moved, for piecemeal and bundled delivery.

    The x axis is elements acquired per agent, counted in the engine, so the two
    arms are compared at equal throughput rather than at equal parameter values.
    The slopes have opposite signs: pushing more material through a piecemeal
    channel lowers adoption, pushing more through a bundled channel raises it.
    """
    d = src_dir or newest("*-rate-matched")
    rows = list(csv.DictReader(open(os.path.join(d, "rate_matched.csv"))))
    plt.rcParams.update(SERIF)
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    for mode, lab, ls, mk, col in (
            ("elements_only", "piecemeal", "-", "o", "0.0"),
            ("whole_package_gated", "bundled, cue-matched", "--", "s", "0.45")):
        pts = sorted((float(r["elements_per_agent"]), float(r["final"]))
                     for r in rows if r["mode"] == mode)
        ax.plot([x for x, _ in pts], [y for _, y in pts], ls=ls, marker=mk,
                color=col, lw=1.6, ms=5, label=lab)
    ax.set_xlabel("elements acquired per agent over the run")
    ax.set_ylabel("final adoption")
    ax.grid(True, color="0.9", lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    os.makedirs(FIGDIR, exist_ok=True)
    p = os.path.join(FIGDIR, "fig_rate_matched.png")
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return [p]


def run(script):
    r = subprocess.run([PY, os.path.join(HERE, script)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  !! {script} failed:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
        return False
    return True


def main():
    print(f"canon: {CANON}")
    wrote = []

    print("\n[1] per-stage figures (from canon aggregated.csv)")
    wrote += stage_figures()

    print("[2] wedge report (observability gap + collapse)")
    run("wedge_report.py")

    print("[3] tipping report (bistability)")
    run("tipping_report.py")

    print("[4] confirmation report (assembly difficulty)")
    run("confirm_report.py")

    print("[5] comment figures (W1, W2, W5)")
    run("make_comment_figs.py")

    print("[6] W5c inverted-U")
    wrote += w5c_figure()

    print("\nfigures written directly by this script:")
    for p in wrote:
        print("   " + os.path.relpath(p, HERE))
    print("\nfigures written by the report scripts, newest dirs:")
    for pat, names in ((f"{CANON}", []),
                       ("*-wedge-explore", ["fig_observability_gap.png", "fig_collapse.png"]),
                       ("*-tipping", ["fig_bistability.png"]),
                       ("*-confirm", ["fig_assembly_difficulty.png"]),
                       ("*-comments", ["fig_w1_capacity_ratio.png", "fig_w2_stab_enh.png"]),
                       ("*-comments2", ["fig_w5_ecology.png"])):
        d = newest(pat)
        for n in names:
            p = os.path.join(d, n) if d else None
            ok = p and os.path.exists(p)
            print(f"   {'OK ' if ok else '!! '} {os.path.relpath(p, HERE) if p else pat + '/' + n}")


if __name__ == "__main__":
    main()
