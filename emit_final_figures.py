#!/usr/bin/env python3
"""Emit the final main-text figure set at publication spec.

Figures 2, 4, 5 come from make_revised_figures.py (the revised visual branch).
Figure 3 comes from make_manuscript_figures.py, re-emitted here as vector PDF +
600 dpi PNG because its printed marker label was corrected to match the
adjudicated adoption metric.

Writes results/figures-final/. Reads only stored output; recomputes nothing.

  python3 emit_final_figures.py
"""
import os, shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.join(HERE, "results", "figures-final")
os.makedirs(FINAL, exist_ok=True)

import make_revised_figures as MR

# --- Figures 2, 4, 5: regenerate through the revised generator -------------
MR.figure2(); MR.figure4(); MR.figure5()
for stem in ("figure2_components_before_adoption_revised",
             "figure4_component_identity_revised",
             "figure5_retention_transmission_revised"):
    for ext in (".pdf", ".png"):
        src = os.path.join(MR.OUT, stem + ext)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(FINAL, stem + ext))
            print("final:", stem + ext)

# --- Figure 3: re-emit at publication spec with the corrected label --------
import make_manuscript_figures as MM

def _save_both(fig, name):
    stem = os.path.splitext(name)[0]
    for ext, kw in ((".pdf", {}), (".png", {"dpi": 600})):
        p = os.path.join(FINAL, stem + ext)
        fig.savefig(p, bbox_inches="tight", **kw)
        print("final:", stem + ext)
    # keep the original manuscript-figure directory in step as well
    fig.savefig(os.path.join(MM.OUT, name))
    plt.close(fig)

MM.save = _save_both
MM.audit = lambda *a, **k: None   # do not rewrite the figure-data audit here
MM.figure3()
