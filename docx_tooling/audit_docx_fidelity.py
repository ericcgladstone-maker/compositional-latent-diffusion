#!/usr/bin/env python3
"""Audit every number in the master docx against source data.

  A. Main sweep: re-derive aggregated.csv from the raw 1,620-run summary.csv.
  B. docx per-stage tables: every cell must match aggregated.csv.
  C. Wedge-fold prose numbers (gap range): re-derive from part_b raw runs.
  D. Wedge-fold prose numbers (observability gap 0.60 / +0.09 / -0.17): RE-RUN the
     trajectories from scratch and confirm they reproduce what the docx states.
  E. Stated counts (stages / cells / runs).

Exit 0 only if everything matches.
"""

import csv, glob, os, sys, zipfile
from collections import defaultdict
from xml.etree import ElementTree as ET

from abm import phases as P
from abm.model import World

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))

# Canonical source dirs. Overridable so the audit follows the canon rather than
# hardcoding one sweep: ABM_CANON_DIR / ABM_WEDGE_DIR. Replication count and the
# expected raw row count are read from the sweep's own metadata, not asserted as
# literals, so upgrading the canon's N does not require editing this file.
MAIN = os.environ.get("ABM_CANON_DIR") or os.path.join(HERE, "results", "20260616-160339-full")
WEDGE = os.environ.get("ABM_WEDGE_DIR") or os.path.join(HERE, "results", "20260623-144801-wedge-explore")
if not os.path.isabs(MAIN):
    MAIN = os.path.join(HERE, "results", MAIN)
if not os.path.isabs(WEDGE):
    WEDGE = os.path.join(HERE, "results", WEDGE)


def canon_reps():
    """Replications per cell for the canonical sweep, from its metadata."""
    import json
    with open(os.path.join(MAIN, "metadata.json")) as f:
        return int(json.load(f)["replications"])

PARAM_LABEL = {
    "initial_element_density": "Initial element density", "capacity": "Capacity",
    "transmissibility_mode": "Transmissibility mode", "transmission_prob": "Transmission probability",
    "stabilization_boost": "Stabilization strength (boost)", "enhanced_factor": "Enhanced factor",
    "strong_tie_fraction": "Strong-tie fraction", "coupling_strength": "Coupling strength",
    "incompatibility": "Incompatibility", "change_agent_fraction": "Evangelist fraction"}

fails = []


def check(cond, msg):
    print(("  OK  " if cond else "  FAIL") + "  " + msg)
    if not cond:
        fails.append(msg)


def fnum(x):
    return float(x)


# --- A. main sweep aggregated re-derived from raw ---------------------------
print("\n[A] re-derive main-sweep aggregated.csv from raw summary.csv")
raw = list(csv.DictReader(open(os.path.join(MAIN, "summary.csv"))))
agg = list(csv.DictReader(open(os.path.join(MAIN, "aggregated.csv"))))
g = defaultdict(list)
for r in raw:
    g[(r["phase"], str(r["focal_value"]))].append(fnum(r["final_manifest_share"]))
mm = 0
for a in agg:
    mine = sum(g[(a["phase"], str(a["focal_value"]))]) / len(g[(a["phase"], str(a["focal_value"]))])
    if abs(mine - fnum(a["final_manifest_share_mean"])) > 1e-3:
        mm += 1
REPS = canon_reps()
expected_raw = len(agg) * REPS
check(mm == 0, f"all {len(agg)} aggregated cells re-derive from {len(raw)} raw rows (mismatches={mm})")
check(len(raw) == expected_raw,
      f"raw row count == {len(agg)} cells x {REPS} reps == {expected_raw} (got {len(raw)})")
check(len(agg) == 54, f"aggregated cell count == 54 (got {len(agg)})")
# every cell must actually carry the full replication count (no short cells)
short = [k for k, v in g.items() if len(v) != REPS]
check(not short, f"every cell has exactly {REPS} replications (short cells={len(short)})")

# --- B. docx per-stage tables vs aggregated --------------------------------
print("\n[B] docx per-stage table cells vs aggregated.csv")
by = {}
for r in agg:
    by.setdefault(r["phase"], {})[str(r["focal_value"])] = r
lab2pids = defaultdict(list)
for pid in by:
    lab2pids[PARAM_LABEL[P.PHASE_INDEX[pid]["focal"]["param"]]].append(pid)
root = ET.fromstring(zipfile.ZipFile(DOCX).read("word/document.xml"))


def celltext(tc):
    return " ".join(t.text or "" for t in tc.iter(f"{W}t")).strip()


cells_checked = cells_bad = stage_tables = 0
for tbl in root.iter(f"{W}tbl"):
    rows = tbl.findall(f"{W}tr")
    hdr = [celltext(tc) for tc in rows[0].findall(f"{W}tc")]
    if not (len(hdr) == 5 and hdr[1] == "Adoption mean (sd)" and hdr[0] in lab2pids):
        continue
    stage_tables += 1
    data = {celltext(tr.findall(f'{W}tc')[0]): [celltext(c) for c in tr.findall(f'{W}tc')]
            for tr in rows[1:]}
    # disambiguate which phase by matching adoption values
    pid = None
    for cand in lab2pids[hdr[0]]:
        if all(lvl in by[cand] and r[1] == f"{fnum(by[cand][lvl]['final_manifest_share_mean']):.2f} "
               f"({fnum(by[cand][lvl]['final_manifest_share_sd']):.2f})"
               for lvl, r in data.items()):
            pid = cand; break
    if pid is None:
        cells_bad += 1; print(f"     no phase match for table {hdr[0]}"); continue
    for lvl, r in data.items():
        a = by[pid][lvl]
        exp = [lvl,
               f"{fnum(a['final_manifest_share_mean']):.2f} ({fnum(a['final_manifest_share_sd']):.2f})",
               f"{fnum(a['peak_manifest_share_mean']):.2f}", f"{fnum(a['overshoot_mean']):.2f}",
               f"{fnum(a['lapse_rate_mean']):.2f}"]
        cells_checked += 1
        if r != exp:
            cells_bad += 1; print(f"     MISMATCH {pid} {lvl}: {r} vs {exp}")
check(stage_tables == 13, f"13 per-stage tables found (got {stage_tables})")
check(cells_bad == 0, f"all {cells_checked} per-stage table cells match aggregated (bad={cells_bad})")

# --- C. wedge gap range re-derived from part_b raw runs --------------------
print("\n[C] wedge-fold gap range: re-derive from part_b raw runs and compare to the "
      "range the docx actually states")
braw = list(csv.DictReader(open(os.path.join(WEDGE, "part_b_runs.csv"))))
gb = defaultdict(lambda: defaultdict(list))
for r in braw:
    gb[(r["knob"], r["level"])][r["mode"]].append(fnum(r["final_manifest_share"]))
gaps = []
for key, md in gb.items():
    if "elements_only" in md and "whole_package" in md:
        eo = sum(md["elements_only"]) / len(md["elements_only"])
        wp = sum(md["whole_package"]) / len(md["whole_package"])
        gaps.append(wp - eo)
_alltext_c = " ".join(
    t.text or "" for t in
    ET.fromstring(zipfile.ZipFile(DOCX).read("word/document.xml")).iter(f"{W}t"))
_stated = f"about {min(gaps):+.2f} to {max(gaps):+.2f}"
check(_stated in _alltext_c,
      f"docx states the re-derived gap range '{_stated}' "
      f"(raw min {min(gaps):+.4f}, max {max(gaps):+.4f})")

# --- D. observability-gap numbers RE-RUN from scratch ----------------------
DREPS = int(os.environ.get("ABM_AUDIT_REPS", str(REPS)))
print(f"\n[D] re-run wedge trajectories (2 modes x {DREPS} reps) -> 0.60 / +0.09 / -0.17")
pre, fin = {}, {}
for mode in ("elements_only", "whole_package"):
    pres, fins = [], []
    for s in range(DREPS):
        w = World(P.config_for_phase("V1-W", {"transmissibility_mode": mode, "seed": s}))
        w.run()
        h = w.history
        pre99 = next((x["observability_gap"] for x in h if x["t"] == 99), h[-1]["observability_gap"])
        pres.append(pre99); fins.append(h[-1]["observability_gap"])
    pre[mode] = sum(pres) / len(pres); fin[mode] = sum(fins) / len(fins)
check(abs(pre["elements_only"] - 0.60) < 0.02, f"pre-trigger gap ~0.60 (got {pre['elements_only']:+.3f})")
check(abs(fin["elements_only"] - 0.09) < 0.03, f"elements_only final gap ~+0.09 (got {fin['elements_only']:+.3f})")
check(abs(fin["whole_package"] + 0.17) < 0.03, f"whole_package final gap ~-0.17 (got {fin['whole_package']:+.3f})")

# --- E. stated counts ------------------------------------------------------
print("\n[E] stated counts in docx prose")
alltext = " ".join(t.text or "" for t in root.iter(f"{W}t"))
for token in ("39", f"{expected_raw:,}", "54 settings", "13"):
    check(token in alltext, f"docx mentions '{token}'")
# the stated replication count must match the canon actually audited above
check(f"{REPS} replications" in alltext,
      f"docx states '{REPS} replications' (matching the audited canon)")

print("\n" + ("ALL CHECKS PASSED" if not fails else f"{len(fails)} FAILURE(S): " + "; ".join(fails)))
sys.exit(1 if fails else 0)
