#!/usr/bin/env python3
"""The paired-arm invariant, for all three readiness rules.

Everything the comparison claims rests on one fact: the arms differ ONLY in the
function mapping retained material onto readiness. If the token histories ever
diverge, the comparison is between two different worlds and means nothing.

This asserts, tick by tick, that the complete retained token state, including
both component identity and source identity, is identical across the
compositional, count and source arms. It also checks the arrivals digest, which
captures the full ordered admission stream rather than just the end state.

  python verify_token_arms.py
"""
import sys

from token_model import TokenWorld

RULES = ("compositional", "count", "source")

CASES = [
    dict(capacity=6, loss_rate=0.0, transmission_prob=0.05),
    dict(capacity=6, loss_rate=0.0, transmission_prob=0.20),
    dict(capacity=5, loss_rate=0.0, transmission_prob=0.20),
    dict(capacity=6, loss_rate=0.01, transmission_prob=0.20),
    dict(capacity=5, loss_rate=0.01, transmission_prob=0.05),
]

TICKS = 300
SEEDS = (0, 1, 2)


def build(rule, case, seed):
    cfg = dict(case, seed=seed, sufficiency_rule=rule)
    if rule == "count":
        cfg["count_threshold"] = 3
    return TokenWorld(cfg)


def main():
    failures = 0
    checks = 0
    for case in CASES:
        for seed in SEEDS:
            worlds = {r: build(r, case, seed) for r in RULES}
            ref = RULES[0]
            # identical at construction, before any dynamics
            for r in RULES[1:]:
                if worlds[r].token_state_digest() != worlds[ref].token_state_digest():
                    print(f"FAIL seeding differs: {r} vs {ref} {case} seed={seed}")
                    failures += 1
            for t in range(TICKS):
                for r in RULES:
                    worlds[r].step()
                d = worlds[ref].token_state_digest()
                for r in RULES[1:]:
                    checks += 1
                    if worlds[r].token_state_digest() != d:
                        print(f"FAIL token state diverged at tick {t+1}: "
                              f"{r} vs {ref} {case} seed={seed}")
                        failures += 1
                        break
                else:
                    continue
                break
            a = worlds[ref].arrivals_digest()
            for r in RULES[1:]:
                checks += 1
                if worlds[r].arrivals_digest() != a:
                    print(f"FAIL arrivals digest differs: {r} vs {ref} {case} seed={seed}")
                    failures += 1
            # the arms MUST differ in adoption, or the manipulation did nothing
            ad = {r: worlds[r].history[-1]["adoption"] for r in RULES}
            if len(set(round(v, 6) for v in ad.values())) == 1:
                print(f"WARN all arms identical in adoption {case} seed={seed}: {ad}")
    print(f"\n{checks} identity checks, {failures} failures")
    if failures:
        sys.exit(1)
    print("PASS: compositional, count and source arms share one token history, "
          "including source metadata, at every tick.")


if __name__ == "__main__":
    main()
