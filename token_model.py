#!/usr/bin/env python3
"""A token-memory model for the compositional versus count-only comparison.

This is deliberately NOT the shipped engine. It is a constructed identification
experiment in which both arms share one retention process and differ only in the
function mapping retained material onto readiness.

  memory      each agent holds a multiset of tokens, each labelled with an
              element type. Duplicates are retainable in BOTH arms. Capacity
              counts tokens, eviction removes a token, loss removes tokens
              independently. Nothing about retention depends on the arm.

  readiness   compositional: at least k DISTINCT required TYPES present
              count:         at least k required TOKENS present, duplicates
                             included
              source:        at least k required tokens from k DISTINCT SENDERS,
                             regardless of which types they are

So with k=3, [A,A,A] from three different neighbours satisfies count and source
but fails compositional; [A,B,C] all from one neighbour satisfies count and
compositional but fails source; [A,B,C] from three neighbours satisfies all
three. The source arm is the rule the nonredundant-information literature
actually uses, and it sits between the other two.

Every token carries (type, source). Source is the immediate sender for a
transmitted token. Seeded tokens each receive their own unique source id, so
that initialization is neutral between the source and compositional rules; were
all of an agent's seeded tokens to share one source, the source arm would be
handicapped by the initialization rather than by the rule. `seed_source_mode`
exposes the alternative for sensitivity.

Because adoption never feeds back into transmission or retention here, paired
runs of the two arms should produce identical token trajectories tick by tick.
`verify_token_arms.py` asserts exactly that, which makes retention identical by
construction rather than matched statistically. The shipped engine stores
distinct types rather than tokens, so mapping this result back to it is a
separate question and is handled by the bridge check, not assumed.
"""
import hashlib
from typing import List

import numpy as np

from abm import topology as topo


DEFAULTS = dict(
    n_agents=100, topology="small_world", mean_degree=6, rewire_prob=0.1,
    strong_tie_fraction=0.0,   # unused: tie weighting is off for this experiment
    n_element_types=8, n_big_things=2, requirement_size=4, element_overlap=1,
    sufficiency_k=3, capacity=6,
    transmission_prob=0.1, contacts_per_tick=1,
    initial_element_density=0.15,
    loss_rate=0.0,
    trigger_time=100, trigger_reach=1.0,
    run_length=1000,
    reversible_adoption=True,
    sufficiency_rule="compositional",   # "compositional" | "count" | "source"
    count_threshold=None,               # count-only threshold; defaults to k
    seed_source_mode="unique",          # "unique" | "shared" | "social_only"
    seed=0,
)


def build_required_sets(cfg):
    """Same construction the shipped engine uses, so the element structure matches."""
    B, R = cfg["n_big_things"], cfg["requirement_size"]
    O = min(cfg["element_overlap"], R - 1)
    stride = max(1, R - O)
    needed = (B - 1) * stride + R
    n_types = max(cfg["n_element_types"], needed)
    req = [frozenset(range(b * stride, b * stride + R)) for b in range(B)]
    return req, n_types


# Seeded tokens under "social_only" carry this sentinel and are ignored by the
# source rule until the material has actually passed through a transmission.
NOSOCIAL = -10 ** 9


class TokenWorld:
    def __init__(self, cfg: dict):
        self.cfg = {**DEFAULTS, **cfg}
        c = self.cfg
        # TWO independent streams. Memory and transmission draw from `rng`;
        # adoption and the trigger draw from `arng`. They must be separate: the
        # trigger draws once per ready agent, and the two arms have different
        # numbers of ready agents, so a shared stream would desynchronise the
        # memory process at the first firing and the arms would stop being
        # comparable. verify_token_arms.py caught exactly that.
        self.rng = np.random.default_rng(int(c["seed"]))
        self.arng = np.random.default_rng(int(c["seed"]) + 1_000_003)
        self.required, self.n_types = build_required_sets(c)
        self.B = len(self.required)
        self.k = c["sufficiency_k"]
        self.kc = c["count_threshold"] if c["count_threshold"] else self.k
        self.adjacency, _ = topo.build_network(
            {**c, "tie_strength_channels": False}, self.rng)
        self.n = len(self.adjacency)
        # each token is (element_type, source_id); source < 0 marks seeded material
        self.tokens: List[List[tuple]] = [[] for _ in range(self.n)]
        self._seed_src = 0
        self.manifest: List[set] = [set() for _ in range(self.n)]
        self.t = 0
        self.history = []
        # hash of every admitted token, in order, for the paired-arm invariant
        self._arrivals = hashlib.blake2b(digest_size=16)
        self.evictions = 0            # tokens displaced by an arrival at capacity
        self.completions = 0          # transitions into readiness
        self._seed_population()
        self.history.append(self.metrics())

    # ---- memory operations (identical in both arms) ----------------------
    def _admit(self, i: int, e: int, src: int):
        toks = self.tokens[i]
        if len(toks) >= self.cfg["capacity"]:
            j = int(self.rng.integers(0, len(toks)))
            toks.pop(j)
            self.evictions += 1
        toks.append((e, src))
        self._arrivals.update(f"{self.t}:{i}:{e}:{src};".encode())

    def _seed_population(self):
        dens = self.cfg["initial_element_density"]
        mode = self.cfg["seed_source_mode"]
        for i in range(self.n):
            for e in range(self.n_types):
                if self.rng.random() < dens:
                    if mode == "shared":
                        src = -(i + 1)          # one exogenous origin per agent
                    elif mode == "social_only":
                        src = NOSOCIAL          # no social origin at all
                    else:
                        self._seed_src += 1
                        src = -self._seed_src   # one origin per seeded token
                    self._admit(i, e, src)

    # ---- readiness (the ONLY difference between arms) --------------------
    def _is_ready(self, i: int, b: int) -> bool:
        req = self.required[b]
        rel = [(e, s) for (e, s) in self.tokens[i] if e in req]
        rule = self.cfg["sufficiency_rule"]
        if rule == "count":
            return len(rel) >= self.kc
        if rule == "source":
            return len({s for (_, s) in rel if s != NOSOCIAL}) >= self.k
        return len({e for (e, _) in rel}) >= self.k

    # ---- dynamics --------------------------------------------------------
    def step(self):
        self.t += 1
        c = self.cfg
        order = self.rng.permutation(self.n)
        for si in order:
            nbrs = self.adjacency[si]
            if not nbrs:
                continue
            for _ in range(c["contacts_per_tick"]):
                ri = nbrs[int(self.rng.integers(0, len(nbrs)))]
                toks = self.tokens[si]
                if not toks:
                    continue
                e, _ = toks[int(self.rng.integers(0, len(toks)))]
                if self.rng.random() < c["transmission_prob"]:
                    self._admit(ri, e, int(si))   # source is the immediate sender

        if c["loss_rate"] > 0:
            for i in range(self.n):
                keep = [tok for tok in self.tokens[i]
                        if self.rng.random() >= c["loss_rate"]]
                self.tokens[i] = keep

        # reversible adoption: a manifest agent lapses if it drops below readiness
        if c["reversible_adoption"]:
            for i in range(self.n):
                for b in list(self.manifest[i]):
                    if not self._is_ready(i, b):
                        self.manifest[i].discard(b)

        # count readiness transitions, whether or not the trigger fires
        for i in range(self.n):
            for b in range(self.B):
                if b not in self.manifest[i] and self._is_ready(i, b):
                    self.completions += 1
        tt = max(1, c["trigger_time"])
        if self.t % tt == 0:
            for i in range(self.n):
                for b in range(self.B):
                    if b not in self.manifest[i] and self._is_ready(i, b):
                        if self.arng.random() < c["trigger_reach"]:
                            self.manifest[i].add(b)

        self.history.append(self.metrics())

    def run(self):
        for _ in range(self.cfg["run_length"]):
            self.step()
        return self

    # ---- measurement -----------------------------------------------------
    def metrics(self) -> dict:
        n, B = self.n, self.B
        adoption = sum(len(m) for m in self.manifest) / (n * B)
        carriers = []
        for b in range(B):
            req = self.required[b]
            carriers.append(sum(1 for i in range(n)
                                if any(e in req for (e, _) in self.tokens[i])
                                and b not in self.manifest[i]) / n)
        occ = [len(t) for t in self.tokens]
        dup = [len(t) - len({e for (e, _) in t}) for t in self.tokens]
        return {
            "t": self.t,
            "adoption": adoption,
            "carrier_per_bt": float(np.mean(carriers)),
            "mean_occupancy": float(np.mean(occ)),
            "frac_at_capacity": float(np.mean([o >= self.cfg["capacity"] for o in occ])),
            "mean_duplicates": float(np.mean(dup)),
            "mean_distinct_types": float(np.mean(
                [len({e for (e, _) in t}) for t in self.tokens])),
            "mean_distinct_sources": float(np.mean(
                [len({s for (_, s) in t}) for t in self.tokens])),
            "evictions_per_agent": self.evictions / n,
            "completions_per_agent": self.completions / n,
        }

    def arrivals_digest(self) -> str:
        return self._arrivals.hexdigest()

    def token_state_digest(self) -> str:
        h = hashlib.blake2b(digest_size=16)
        for t in self.tokens:
            h.update((",".join(f"{e}:{s}" for (e, s) in sorted(t)) + "|").encode())
        return h.hexdigest()
