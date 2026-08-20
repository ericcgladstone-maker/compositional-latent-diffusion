#!/usr/bin/env python3
"""Generate BUILD_SPEC.md straight from the code.

Introspects the parameter registry (config.py), the build phases (phases.py),
the per-tick metrics and per-run signatures (model.py / sweep.py) and emits a
terse, tabular specification of exactly what the simulation currently contains.
No hand-maintained prose to drift out of sync -- rerun after any change.

  python gen_spec.py
"""

import os

from abm import config as C
from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history


def fmt_range(p):
    if p.kind == "choice":
        return " \\| ".join(str(c) for c in p.choices)
    if p.kind == "bool":
        return "false \\| true"
    step = f" (step {g(p.step)})" if p.step is not None else ""
    return f"{g(p.low)} – {g(p.high)}{step}"


def g(v):
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def default_diff(phase_overrides):
    """Phase overrides shown as key=value, only the keys the phase actually sets."""
    return ", ".join(f"`{k}={g(v)}`" for k, v in phase_overrides.items())


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    L = []
    A = L.append

    A("# Build specification — latent-adoption ABM")
    A("")
    A("_Generated from code by `gen_spec.py`. Regenerate after any change. "
      "This reflects what the simulation **actually** implements._")
    A("")

    # -- 1. Parameters by group -------------------------------------------
    A(f"## 1. Parameters ({len(C.PARAM_SPECS)} total)")
    A("")
    for grp in C.GROUP_ORDER:
        params = [p for p in C.PARAM_SPECS if p.group == grp]
        if not params:
            continue
        A(f"### {C.GROUP_LABELS.get(grp, grp)}")
        A("")
        A("| parameter | type | default | range / choices | description |")
        A("|---|---|---|---|---|")
        for p in params:
            A(f"| `{p.name}` | {p.kind} | {g(p.default)} | {fmt_range(p)} | {p.doc} |")
        A("")

    # -- 2. Switchable conditions (categorical) ---------------------------
    A("## 2. Switchable conditions (categorical manipulations)")
    A("")
    A("| switch | options |")
    A("|---|---|")
    sep = " \\| "
    for p in C.PARAM_SPECS:
        if p.kind == "choice":
            A(f"| `{p.name}` | {sep.join(str(c) for c in p.choices)} |")
    A("")

    # -- 3. Mechanism switches (boolean) + their strength knobs -----------
    A("## 3. V2 mechanism switches (boolean) and associated strengths")
    A("")
    A("| mechanism (bool) | default | strength parameter(s) |")
    A("|---|---|---|")
    strengths = {
        "differential_slot_cost": "(chunk costs 2 slots when on)",
        "compression": "—",
        "stabilization": "`stabilization_boost`",
        "enhanced_transmission": "`enhanced_factor`",
        "tie_strength_channels": "`strong_tie_fraction`",
        "internal_coupling": "`coupling_strength`, `coupling_level`",
        "neighbor_coupling": "`coupling_strength`, `coupling_level`",
    }
    for name in ["differential_slot_cost", "compression", "stabilization",
                 "enhanced_transmission", "tie_strength_channels",
                 "internal_coupling", "neighbor_coupling"]:
        p = C.PARAM_INDEX[name]
        A(f"| `{name}` | {g(p.default)} | {strengths[name]} |")
    A("")

    # -- 4. Build phases / experimental conditions ------------------------
    A(f"## 4. Build phases / experimental conditions ({len(P.PHASES)})")
    A("")
    A("| phase id | focal sweep | focal values | predicted |")
    A("|---|---|---|---|")
    for ph in P.PHASES:
        fp = ph["focal"]["param"]
        fv = ", ".join(g(v) for v in ph["focal"]["values"])
        A(f"| `{ph['id']}` | `{fp}` | {fv} | {ph['predict']} |")
    A("")
    A("### Per-phase overrides (relative to registry defaults)")
    A("")
    A("| phase id | overrides applied |")
    A("|---|---|")
    for ph in P.PHASES:
        A(f"| `{ph['id']}` | {default_diff(ph['overrides'])} |")
    A("")

    # -- 5. Outcome measures ----------------------------------------------
    w = World(P.config_for_phase("V1", {"run_length": 5}))
    w.run()
    m = w.history[-1]
    per_big_keys = list(next(iter(m["per_big"].values())).keys())
    tick_keys = [k for k in m.keys() if k != "per_big"]
    summ = summarize_history(w.history, [b.label for b in w.big_things])

    A("## 5. Outcome measures (dependent variables)")
    A("")
    A("### Per-tick metrics (logged every step)")
    A("")
    A("| metric | note |")
    A("|---|---|")
    notes = {
        "t": "tick",
        "element_saturation": "mean fraction of all element-slots filled",
        "bigthing_element_saturation": "mean fraction of big-thing elements held",
        "manifest_share": "fraction of (agent × big-thing) cells manifest",
        "observability_gap": "bigthing_element_saturation − manifest_share",
    }
    for k in tick_keys:
        A(f"| `{k}` | {notes.get(k, '')} |")
    A(f"| `per_big[label]` | per big thing: {', '.join('`'+k+'`' for k in per_big_keys)} |")
    A("")
    A("### Per-run signatures (one row per replication in `summary.csv`)")
    A("")
    A("| signature | note |")
    A("|---|---|")
    snotes = {
        "ticks_run": "ticks until quiescence or run_length",
        "time_to_first_manifest": "first tick with any manifestation",
        "max_single_tick_jump": "largest one-tick rise in manifest share (plateau-then-jump)",
        "max_jump_tick": "when that jump occurred",
        "time_to_half_cascade": "tick reaching 50% of final adoption",
    }
    for k in summ.keys():
        A(f"| `{k}` | {snotes.get(k, '')} |")
    A("")

    out = os.path.join(here, "BUILD_SPEC.md")
    with open(out, "w") as f:
        f.write("\n".join(L))
    print(f"wrote {out}  ({len(C.PARAM_SPECS)} params, {len(P.PHASES)} phases)")


if __name__ == "__main__":
    main()
