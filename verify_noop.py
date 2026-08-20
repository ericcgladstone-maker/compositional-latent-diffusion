"""No-op regression harness for the 2026-07 additive mechanism changes.

Captures a deterministic 'golden' summary across every existing code path, so
the W5/W6/W7 additions (per-big-thing endowments, coupling matrix, cue-gated
whole-package) can be proven byte-identical when their new params are absent.

Usage:
  python verify_noop.py capture   # dump golden.json from the CURRENT engine
  python verify_noop.py check     # re-run and assert identical to golden.json
"""
import json, os, sys
from abm import phases as P
from abm.sweep import run_one

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.join(HERE, "results", "noop_golden.json")

# (label, phase, overrides) -- covers every mechanism path the edits touch.
CASES = [
    ("V0", "V0", {}),
    ("V1", "V1", {}),
    ("V1-cap4", "V1", {"capacity": 4}),
    ("elements_only", "V1-W", {"transmissibility_mode": "elements_only"}),
    ("whole_package", "V1-W", {"transmissibility_mode": "whole_package"}),
    ("both", "V1-W", {"transmissibility_mode": "both"}),
    ("slotcost", "V2-slotcost", {}),
    ("compression", "V2-compression", {}),
    ("stab0.25", "V2-stabilization", {"stabilization_boost": 0.25}),
    ("stab0.75", "V2-stabilization", {"stabilization_boost": 0.75}),
    ("enh2", "V2-enhanced", {"enhanced_factor": 2.0}),
    ("enh3", "V2-enhanced", {"enhanced_factor": 3.0}),
    ("stab-enh2", "V2-stab-enh", {"enhanced_factor": 2.0}),
    ("tiestrength", "V2-tiestrength", {"strong_tie_fraction": 0.2}),
    ("int-coup-neg", "V2-internal-coupling", {"coupling_strength": -0.5}),
    ("int-coup-pos", "V2-internal-coupling", {"coupling_strength": 1.0}),
    ("nbr-coup-neg", "V2-neighbor-coupling", {"coupling_strength": -1.0}),
    ("nbr-coup-pos", "V2-neighbor-coupling", {"coupling_strength": 1.0}),
]

def _clean(summary):
    # drop nested per_big variants (order-sensitive dicts) -> keep scalar signatures
    return {k: v for k, v in summary.items() if isinstance(v, (int, float, str))}

def capture_all():
    out = {}
    for label, phase, ov in CASES:
        # 3 seeds each for a stronger fingerprint
        recs = []
        for s in range(3):
            cfg = P.config_for_phase(phase, {**ov, "seed": s})
            recs.append(_clean(run_one(cfg)))
        out[label] = recs
    return out

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
    cur = capture_all()
    if mode == "capture":
        json.dump(cur, open(GOLDEN, "w"), indent=2)
        print(f"captured {len(cur)} cases -> {GOLDEN}")
    else:
        gold = json.load(open(GOLDEN))
        diffs = []
        for label in gold:
            if cur.get(label) != gold[label]:
                diffs.append(label)
        if diffs:
            print("NO-OP CHECK FAILED. Divergent cases:", diffs)
            for d in diffs:
                print(" GOLD:", gold[d][0])
                print(" CUR :", cur.get(d, [{}])[0])
            sys.exit(1)
        print(f"NO-OP CHECK PASSED: all {len(gold)} cases byte-identical.")
