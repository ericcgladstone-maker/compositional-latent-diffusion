#!/usr/bin/env python3
"""Verify + visualize + write up the overnight confirmation run (overnight_confirm.py).

Integrity here is by reproducibility: the run saves aggregated means only, and the
script is deterministic given fixed seeds, so this report RE-RUNS one cell from
scratch and checks it matches the saved value exactly (no fabrication). Then it
renders grayscale figures and writes a confirmation log.

Usage: python confirm_report.py        # latest -confirm dir
"""

import csv
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from abm import phases as P
from abm.model import World
from explore_tipping import force_fully_adopted

HERE = os.path.dirname(os.path.abspath(__file__))


def latest(suffix):
    ds = sorted(glob.glob(os.path.join(HERE, "results", f"*-{suffix}")))
    return ds[-1] if ds else None


def rd(d, n):
    return list(csv.DictReader(open(os.path.join(d, n))))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return x


def spot_check(p1):
    """Re-run part1 cell (R=4,k=4) at the same reps and confirm exact match."""
    reps = 50
    R, k = 4, 4
    cell = {}
    for cond in ("from_below", "from_above"):
        finals = []
        for s in range(reps):
            w = World(P.config_for_phase("V1", {"capacity": 6, "requirement_size": R,
                      "sufficiency_k": k, "seed": s}))
            if cond == "from_above":
                force_fully_adopted(w)
            w.run()
            finals.append(w.history[-1]["manifest_share"])
        cell[cond] = round(sum(finals) / len(finals), 4)
    saved = next(r for r in p1 if int(r["requirement_size"]) == R and int(r["sufficiency_k"]) == k)
    ok = (abs(cell["from_below"] - fnum(saved["from_below"])) < 1e-9 and
          abs(cell["from_above"] - fnum(saved["from_above"])) < 1e-9)
    print(f"[spot-check] R=4,k=4 re-run below={cell['from_below']} above={cell['from_above']} "
          f"| saved below={saved['from_below']} above={saved['from_above']} | "
          f"{'EXACT MATCH' if ok else 'MISMATCH'}")
    return ok


def _style():
    plt.rcParams.update({"font.family": "serif",
                         "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 10})


def fig_assembly(d, p1):
    """The corrected mechanism: bistability gap is driven by assembly difficulty,
    indexed by from_below (low from_below = hard to assemble = large gap)."""
    _style()
    fb = [fnum(r["from_below"]) for r in p1]
    gap = [fnum(r["bistability_gap"]) for r in p1]
    noslack = [r["slack"] == "0" or fnum(r["slack"]) == 0 for r in p1]
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    for x, y, ns, r in zip(fb, gap, noslack, p1):
        ax.scatter(x, y, s=46, facecolor=("black" if ns else "0.7"),
                   edgecolor="black", zorder=3,
                   marker=("o" if ns else "s"))
        ax.annotate(f"{r['requirement_size']},{r['sufficiency_k']}", (x, y),
                    fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.axhline(0, color="0.6", lw=0.8)
    ax.set_xlabel("adoption from a fresh start (assembly success)")
    ax.set_ylabel("bistability gap (above minus below)")
    ax.grid(True, color="0.92", lw=0.6); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    # legend proxies
    ax.scatter([], [], facecolor="black", edgecolor="black", marker="o", label="k = R (no slack)")
    ax.scatter([], [], facecolor="0.7", edgecolor="black", marker="s", label="k < R (slack)")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_title("labels = (R,k); harder assembly (left) gives a larger gap", fontsize=8)
    fig.tight_layout()
    p = os.path.join(d, "fig_assembly_difficulty.png"); fig.savefig(p, dpi=200); plt.close(fig)
    return os.path.basename(p)


def fig_scale(d, pb_scale):
    """Bistability gap vs capacity at N=500, overlaid with N=100 from the tipping run."""
    _style()
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    caps5 = [int(r["capacity"]) for r in pb_scale]
    gap5 = [fnum(r["bistability_gap"]) for r in pb_scale]
    ax.plot(caps5, gap5, "o-", color="black", lw=1.6, ms=5, label="N = 500")
    tip = latest("tipping")
    if tip and os.path.exists(os.path.join(tip, "part_b_bistability.csv")):
        b100 = [r for r in rd(tip, "part_b_bistability.csv") if r["eviction"] == "random"
                and int(r["capacity"]) <= 8]
        ax.plot([int(r["capacity"]) for r in b100], [fnum(r["bistability_gap"]) for r in b100],
                "s--", color="0.55", lw=1.4, ms=4, label="N = 100")
    ax.set_xlabel("capacity"); ax.set_ylabel("bistability gap")
    ax.axhline(0, color="0.6", lw=0.8)
    ax.set_xticks(caps5)
    ax.grid(True, color="0.92", lw=0.6); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="best")
    fig.tight_layout()
    p = os.path.join(d, "fig_scale_bistability.png"); fig.savefig(p, dpi=200); plt.close(fig)
    return os.path.basename(p)


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def main():
    d = latest("confirm")
    if not d:
        sys.exit("no -confirm dir")
    tag = os.path.basename(d)
    print(f"dir: {d}")
    p1 = rd(d, "part1_slack.csv")
    pw = rd(d, "part2_wedge_scale.csv")
    pb = rd(d, "part2_bistability_scale.csv")

    ok = spot_check(p1)
    f1 = fig_assembly(d, p1)
    f2 = fig_scale(d, pb)

    # is the gap larger at k==R than at large slack? (corrected mechanism)
    noslack = [fnum(r["bistability_gap"]) for r in p1 if fnum(r["slack"]) == 0]
    slack2p = [fnum(r["bistability_gap"]) for r in p1 if fnum(r["slack"]) >= 2]

    L = []
    A = L.append
    A("# Overnight confirmation log")
    A("")
    A("Confirmation / validity runs for the wedge and tipping findings. Not part of "
      "the signed-off doc. Integrity here is by reproducibility: the run is "
      "deterministic given fixed seeds, and this report re-runs one cell from "
      "scratch to confirm an exact match.")
    A("")
    A(md_table(["Item", "Value"], [
        ["Experiment dir", f"`results/{tag}`"],
        ["Operating point", "`config_for_phase('V1' / 'V1-W')`"],
        ["Reps", "50"],
        ["Integrity spot-check", "PASS, exact match on a re-run cell" if ok else "FAIL"],
    ]))
    A("")
    A("## 1. Mechanism of the bistability: it is assembly difficulty, not threshold slack")
    A("")
    A("Last night's tipping log attributed the bistability to the k-of-R threshold "
      "slack. This run tests that directly by varying requirement_size R and "
      "sufficiency k at fixed capacity, and it corrects the claim. The prediction "
      "from the slack story, that no slack (k = R) would collapse the gap, is wrong. "
      f"The gap is LARGEST at k = R (mean {sum(noslack)/len(noslack):+.2f}) and "
      f"smallest or negative at large slack (mean {sum(slack2p)/len(slack2p):+.2f}).")
    A("")
    A("The real driver is how hard it is to assemble a crossing set from scratch. "
      "When many specific elements must be held at once (high k, strict), a fresh "
      "population cannot get there while a seeded population persists on the "
      "population-wide element reservoir, so the gap is large. When assembly is easy "
      "(low k), fresh populations reach adoption too and the gap closes. The "
      "bistability is an assembly-difficulty effect.")
    A("")
    A("The clincher for the persistence mechanism: the from_above state shows zero "
      "lapses in every cell, including the no-slack k = R cells. With no slack at "
      "all the adopted state still never reverts, so persistence cannot be a slack "
      "effect. It is reservoir-sustained re-acquisition. Caveat: the two negative-gap "
      "cells (R=5,k=3 and R=6,k=3) are not reverse bistability. There the forced "
      "from_above state seeds only one of the two big things under capacity, so it "
      "starts below what a fresh run accumulates over time. They mark a limit of the "
      "forced-state construction, not a real inversion.")
    A("")
    A(f"![assembly difficulty]({f1})")
    A("")
    A(md_table(["R", "k", "slack", "From below", "From above", "Bistability gap",
                "Lapses (above)"],
               [[r["requirement_size"], r["sufficiency_k"], r["slack"], r["from_below"],
                 r["from_above"], r["bistability_gap"], r["lapses_above_mean"]] for r in p1]))
    A("")
    A("## 2. Confirmation at scale (N = 500 and 1000)")
    A("")
    A("The three load-bearing results re-checked at larger populations.")
    A("")
    A("Wedge gap and observability-gap sign flip hold at scale:")
    A("")
    A(md_table(["N", "Mode", "Final adoption", "Final observability gap"],
               [[r["n_agents"], r["mode"], r["final_manifest_share_mean"],
                 r["final_obs_gap_mean"]] for r in pw]))
    A("")
    A("Capacity bistability holds at scale (gap vs capacity, N = 500 against N = 100):")
    A("")
    A(f"![scale bistability]({f2})")
    A("")
    A(md_table(["N", "Capacity", "From below", "From above", "Bistability gap"],
               [[r["n_agents"], r["capacity"], r["from_below"], r["from_above"],
                 r["bistability_gap"]] for r in pb]))
    A("")
    A("## What we learned")
    A("")
    A("1. The wedge, the observability-gap sign flip, and the capacity bistability "
      "all survive at N = 500 and N = 1000. They are not small-population or "
      "small-sample artifacts.")
    A("2. The bistability mechanism is assembly difficulty, not threshold slack. The "
      "gap grows as crossing the threshold from scratch gets harder, and it is "
      "largest at strict all-of assembly (k = R), the opposite of the slack "
      "prediction. Last night's mechanism note is corrected by this run.")
    A("3. Three nights of self-correction in a row (the eviction hypothesis, the "
      "churn hypothesis, now the slack hypothesis) point at one thing: these "
      "mechanisms are entangled, and the robust, repeatedly confirmed facts are the "
      "wedge and the assembly-driven bistability, not any single clean knob.")

    open(os.path.join(d, "EXPLORATION_LOG_3_confirmation.md"), "w").write("\n".join(L) + "\n")
    print(f"figures: {f1}, {f2}")
    print(f"report: {os.path.join(d, 'EXPLORATION_LOG_3_confirmation.md')}")


if __name__ == "__main__":
    main()
