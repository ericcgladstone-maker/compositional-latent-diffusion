#!/usr/bin/env python3
"""Addendum to explore_wedge.py: the full wedge-collapse / validity test.

The 2x2 decomposition (part_c) showed that removing assembly AND activation does
NOT collapse the wedge (residual gap ~0.25). This isolates the third source,
capacity competition: with capacity=6 and 8 element types, the 6 non-big-thing
"noise" types crowd the slots and random eviction churns out the element that
matters. Removing capacity competition (unbounded capacity, or no noise types)
on top of assembly+activation drives the gap to ~0, confirming the wedge behaves
as claimed in its full degenerate limit.

Writes part_c_collapse.csv into the latest -wedge-explore results dir.
"""

import csv
import glob
import os
import sys

from abm import phases as P
from abm.model import World
from abm.sweep import summarize_history

HERE = os.path.dirname(os.path.abspath(__file__))
REPS = int(os.environ.get("ABM_REPS", "30"))


def adopt(ov):
    fs = []
    for s in range(REPS):
        w = World(P.config_for_phase("V1-W", {**ov, "seed": s}))
        w.run()
        fs.append(summarize_history(w.history, [b.label for b in w.big_things])
                  ["final_manifest_share"])
    return round(sum(fs) / len(fs), 4)


# each row: which of the three barriers remain present
CONDITIONS = [
    ("assembly + activation + capacity", "both", dict(requirement_size=4, sufficiency_k=3, trigger_time=100)),
    ("capacity only (assembly, activation removed)", "capacity",
     dict(requirement_size=1, sufficiency_k=1, trigger_time=1)),
    ("none: + unbounded capacity", "none-cap64",
     dict(requirement_size=1, sufficiency_k=1, trigger_time=1, capacity=64)),
    ("none: + no noise element types", "none-ntypes2",
     dict(requirement_size=1, sufficiency_k=1, trigger_time=1, n_element_types=2)),
]


def main():
    ds = sorted(glob.glob(os.path.join(HERE, "results", "*-wedge-explore")))
    if not ds:
        sys.exit("no -wedge-explore dir; run explore_wedge.py first")
    d = ds[-1]
    rows = []
    for label, key, ov in CONDITIONS:
        eo = adopt({**ov, "transmissibility_mode": "elements_only"})
        wp = adopt({**ov, "transmissibility_mode": "whole_package"})
        rows.append({"barriers_present": label, "key": key,
                     "requirement_size": ov["requirement_size"],
                     "trigger_time": ov["trigger_time"],
                     "capacity": ov.get("capacity", 6),
                     "n_element_types": ov.get("n_element_types", 8),
                     "elements_only": eo, "whole_package": wp,
                     "wedge_gap": round(wp - eo, 4)})
        print(f"{label:46s} elements={eo:.2f} whole={wp:.2f} gap={wp-eo:+.2f}")
    path = os.path.join(d, "part_c_collapse.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
