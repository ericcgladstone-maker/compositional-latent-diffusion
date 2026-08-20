"""Headless batch sweep runner.

Runs either a single phase's focal sweep or the full "absolute beginning to
absolute end" path over every phase. Replications are seeded and reproducible.
Results auto-save at intervals (after every cell), so an overnight run that is
interrupted still leaves usable partial output.

This is the engine that produces manuscript numbers. The live viewer is for
intuition; this is for the record.
"""

import csv
import json
import os
import time
from typing import Callable, List, Optional

from . import config as C
from . import phases as P
from .model import World


# ---------------------------------------------------------------------------
# Signature extraction from a single run's history
# ---------------------------------------------------------------------------
def summarize_history(history: List[dict], big_labels: List[str]) -> dict:
    final = history[-1]
    out = {
        "ticks_run": final["t"],
        "final_element_saturation": round(final["element_saturation"], 4),
        "final_bigthing_element_saturation": round(final["bigthing_element_saturation"], 4),
        "final_manifest_share": round(final["manifest_share"], 4),
        "final_observability_gap": round(final["observability_gap"], 4),
    }
    # per big thing finals
    for lab in big_labels:
        pb = final["per_big"][lab]
        out[f"{lab}_manifest"] = pb["manifest"]
        out[f"{lab}_latent"] = pb["latent"]
        out[f"{lab}_at_risk"] = pb["at_risk"]
        out[f"{lab}_resistant"] = pb["resistant"]
        out[f"{lab}_n_variants"] = len(pb["variants"])

    # dynamic signatures
    shares = [h["manifest_share"] for h in history]
    # churn: lapses (reversions), peak adoption, and overshoot (peak that eroded away)
    out["cumulative_lapses"] = final.get("lapses", 0)
    out["lapse_rate"] = round(final.get("lapses", 0) / max(1, final["t"]), 3)
    peak = max(shares)
    out["peak_manifest_share"] = round(peak, 4)
    out["overshoot"] = round(peak - shares[-1], 4)
    # time to first manifestation
    t_first = next((h["t"] for h in history if h["manifest_share"] > 0), -1)
    out["time_to_first_manifest"] = t_first
    # plateau-then-jump: largest single-tick increase in manifest share
    max_jump = 0.0
    jump_t = -1
    for i in range(1, len(shares)):
        d = shares[i] - shares[i - 1]
        if d > max_jump:
            max_jump = d
            jump_t = history[i]["t"]
    out["max_single_tick_jump"] = round(max_jump, 4)
    out["max_jump_tick"] = jump_t
    # time to cross half of final adoption (cascade timing)
    target = 0.5 * shares[-1]
    t_half = next((h["t"] for h in history if h["manifest_share"] >= target and target > 0), -1)
    out["time_to_half_cascade"] = t_half
    return out


# ---------------------------------------------------------------------------
# Running cells
# ---------------------------------------------------------------------------
def run_one(cfg: dict, with_invariants: bool = False) -> dict:
    w = World(cfg)
    if with_invariants:
        from . import invariants
        invariants.run_with_checks(w)
    else:
        w.run()
    return summarize_history(w.history, [bt.label for bt in w.big_things])


def run_cell(phase_id: str, focal_value, replications: int, base_seed: int,
             with_invariants: bool = False) -> List[dict]:
    phase = P.PHASE_INDEX[phase_id]
    focal = phase["focal"]["param"]
    rows = []
    for r in range(replications):
        cfg = P.config_for_phase(phase_id, {focal: focal_value, "seed": base_seed + r})
        summary = run_one(cfg, with_invariants=with_invariants)
        row = {"phase": phase_id, "focal_param": focal, "focal_value": focal_value,
               "rep": r, "seed": base_seed + r}
        row.update(summary)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Sweep orchestration with auto-save
# ---------------------------------------------------------------------------
def _outdir(tag: str) -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stamp = time.strftime("%Y%m%d-%H%M%S")
    d = os.path.join(here, "results", f"{stamp}-{tag}")
    os.makedirs(d, exist_ok=True)
    return d


def _save_rows(path: str, rows: List[dict]):
    if not rows:
        return
    # union of keys across rows, stable order
    keys = []
    for row in rows:
        for k in row:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def run_sweep(phase_ids: List[str],
              replications: Optional[int] = None,
              base_seed: int = 0,
              with_invariants: bool = False,
              progress: Optional[Callable] = None,
              tag: str = "sweep") -> str:
    """Run focal sweeps for the given phases. Returns the output directory.

    progress(done_cells, total_cells, message) is called after each cell.
    Results are written/overwritten after every cell (interval auto-save).
    """
    reps = replications if replications is not None else C.PARAM_INDEX["replications"].default
    outdir = _outdir(tag)

    # metadata: full registry + the phases being run, for reproducibility
    with open(os.path.join(outdir, "metadata.json"), "w") as f:
        json.dump({
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "phases": phase_ids,
            "replications": reps,
            "base_seed": base_seed,
            "with_invariants": with_invariants,
            "registry": C.registry_payload(),
            "phase_defs": [P.PHASE_INDEX[p] for p in phase_ids],
        }, f, indent=2, default=str)

    cells = []
    for pid in phase_ids:
        for val in P.PHASE_INDEX[pid]["focal"]["values"]:
            cells.append((pid, val))
    total = len(cells)

    all_rows: List[dict] = []
    summary_path = os.path.join(outdir, "summary.csv")
    agg_path = os.path.join(outdir, "aggregated.csv")

    for done, (pid, val) in enumerate(cells, start=1):
        rows = run_cell(pid, val, reps, base_seed, with_invariants=with_invariants)
        all_rows.extend(rows)
        _save_rows(summary_path, all_rows)
        _save_rows(agg_path, _aggregate(all_rows))
        if progress is not None:
            progress(done, total,
                     f"{pid} {P.PHASE_INDEX[pid]['focal']['param']}={val} "
                     f"({reps} reps)")
    return outdir


def run_full_sweep(replications: Optional[int] = None, base_seed: int = 0,
                   with_invariants: bool = False, progress: Optional[Callable] = None) -> str:
    """The whole path, V0 to the last scenario."""
    return run_sweep([p["id"] for p in P.PHASES], replications, base_seed,
                     with_invariants, progress, tag="full")


def _aggregate(rows: List[dict]) -> List[dict]:
    """Mean/sd of numeric columns grouped by (phase, focal_value)."""
    groups = {}
    for row in rows:
        key = (row["phase"], row["focal_param"], str(row["focal_value"]))
        groups.setdefault(key, []).append(row)
    numeric_keys = [k for k, v in rows[0].items()
                    if isinstance(v, (int, float)) and k not in ("rep", "seed")]
    out = []
    for (phase, fp, fv), grp in groups.items():
        agg = {"phase": phase, "focal_param": fp, "focal_value": fv, "n": len(grp)}
        for k in numeric_keys:
            vals = [g[k] for g in grp if isinstance(g.get(k), (int, float))]
            if vals:
                m = sum(vals) / len(vals)
                var = sum((x - m) ** 2 for x in vals) / len(vals)
                agg[f"{k}_mean"] = round(m, 4)
                agg[f"{k}_sd"] = round(var ** 0.5, 4)
        out.append(agg)
    return out
