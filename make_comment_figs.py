"""Grayscale figures for the 2026-07 comment-driven analyses.

Printer-friendly, no color, serif -- matches results_to_docx.py convention.
Reads the newest results/*-comments and results/*-comments2 CSVs. Figures land
next to the CSVs and are embedded into the docx by fold_comments_docx.py.
"""
import csv, glob, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family": "serif", "font.size": 9,
                     "axes.edgecolor": "black", "axes.linewidth": 0.8})

HERE = os.path.dirname(os.path.abspath(__file__))
D1 = sorted(glob.glob(os.path.join(HERE, "results", "*-comments")))[-1]
D2 = sorted(glob.glob(os.path.join(HERE, "results", "*-comments2")))[-1]

def rows(path):
    return list(csv.DictReader(open(path)))

# ---- W1: capacity x sufficiency_k heatmap (needed-components / slots ratio) ----
def fig_w1():
    data = rows(os.path.join(D1, "w1_capacity_x_k.csv"))
    ks = sorted({int(r["sufficiency_k"]) for r in data})
    caps = sorted({int(r["capacity"]) for r in data})
    grid = [[next(float(r["final_manifest_share"]) for r in data
                  if int(r["sufficiency_k"]) == k and int(r["capacity"]) == c) for c in caps]
            for k in ks]
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    im = ax.imshow(grid, cmap="Greys", vmin=0, vmax=1, aspect="auto", origin="lower")
    ax.set_xticks(range(len(caps))); ax.set_xticklabels(caps)
    ax.set_yticks(range(len(ks))); ax.set_yticklabels(ks)
    ax.set_xlabel("capacity (memory slots)"); ax.set_ylabel("sufficiency k (needed components)")
    for i in range(len(ks)):
        for j in range(len(caps)):
            v = grid[i][j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    color="white" if v > 0.55 else "black", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, label="final adoption")
    fig.tight_layout()
    p = os.path.join(D1, "fig_w1_capacity_ratio.png"); fig.savefig(p, dpi=200); plt.close(fig)
    return p

# ---- W2: stabilization_boost x enhanced_factor heatmap (interaction) ----
def fig_w2():
    data = rows(os.path.join(D1, "w2_stab_x_enh.csv"))
    boosts = sorted({float(r["stabilization_boost"]) for r in data})
    facs = sorted({float(r["enhanced_factor"]) for r in data})
    grid = [[next(float(r["final_manifest_share"]) for r in data
                  if float(r["stabilization_boost"]) == b and float(r["enhanced_factor"]) == e)
             for e in facs] for b in boosts]
    fig, ax = plt.subplots(figsize=(4.6, 3.1))
    im = ax.imshow(grid, cmap="Greys", vmin=0, vmax=1, aspect="auto", origin="lower")
    ax.set_xticks(range(len(facs))); ax.set_xticklabels([f"{e:g}" for e in facs])
    ax.set_yticks(range(len(boosts))); ax.set_yticklabels([f"{b:g}" for b in boosts])
    ax.set_xlabel("enhanced factor"); ax.set_ylabel("stabilization boost (0 = full protection)")
    for i in range(len(boosts)):
        for j in range(len(facs)):
            v = grid[i][j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    color="white" if v > 0.55 else "black", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, label="final adoption")
    fig.tight_layout()
    p = os.path.join(D1, "fig_w2_stab_enh.png"); fig.savefig(p, dpi=200); plt.close(fig)
    return p

# ---- W5: recruitment-retention inverted-U (competitive ecology) ----
def fig_w5():
    data = rows(os.path.join(D2, "w5_ecology.csv"))
    betas = sorted({float(r["beta_compression"]) for r in data})
    styles = [("o-", "black"), ("s--", "0.4"), ("^:", "0.6")]
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    for bi, b in enumerate(betas):
        pts = sorted([(float(r["alpha_compression"]), float(r["alpha_share"]))
                      for r in data if float(r["beta_compression"]) == b])
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        mk, col = styles[bi % len(styles)]
        ax.plot(xs, ys, mk, color=col, lw=1.5, ms=5, label=f"rival compression = {b:g}")
    ax.set_xlabel("alpha compression rate (encapsulation / retention)")
    ax.set_ylabel("alpha captured share")
    ax.grid(True, color="0.9", lw=0.6)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    p = os.path.join(D2, "fig_w5_ecology.png"); fig.savefig(p, dpi=200); plt.close(fig)
    return p

if __name__ == "__main__":
    for f in (fig_w1, fig_w2, fig_w5):
        try:
            print("wrote", f())
        except Exception as ex:
            print("SKIP", f.__name__, "->", ex)
