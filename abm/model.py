"""Canonical latent-adoption / combinatoric-diffusion model core.

This module contains NO rendering and NO I/O. It is the single source of truth
for the dynamics. The live viewer and the headless sweep both drive this same
World object, so there can be no divergence between "what you watched" and "what
got reported".

Vocabulary (from the design docs):
  element     -- a small, mostly-invisible constituent (an element TYPE id).
  big thing   -- alpha, beta, ... assembled from a set of elements.
  latent      -- an agent holding a sufficient element set, not yet manifest.
  manifest    -- an agent in whom the big thing has been triggered into action.
  trigger     -- the generic cue that flips latent -> manifest.

Every mechanism in Section 3 of the design doc is a switch read from config.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from . import config as C
from . import topology as topo


# ---------------------------------------------------------------------------
# Static structure
# ---------------------------------------------------------------------------
@dataclass
class BigThing:
    bid: int
    label: str
    required: Tuple[int, ...]      # element types defining this big thing

    @property
    def required_set(self) -> frozenset:
        return frozenset(self.required)


def build_big_things(cfg: dict) -> Tuple[List[BigThing], int]:
    """Construct big-thing definitions with the configured overlap.

    Returns (big_things, effective_n_element_types). The element count is
    auto-expanded if the requested overlap/size/count would not fit, so the
    viewer never crashes on a bad slider combination -- the expansion is
    reported back so it is visible, not silent.
    """
    B = cfg["n_big_things"]
    R = cfg["requirement_size"]
    O = min(cfg["element_overlap"], R - 1)  # cannot overlap more than R-1
    stride = max(1, R - O)
    needed = (B - 1) * stride + R
    eff_T = max(cfg["n_element_types"], needed)

    big_things = []
    names = ["alpha", "beta", "gamma", "delta", "epsilon"]
    for b in range(B):
        start = b * stride
        required = tuple(range(start, start + R))
        big_things.append(BigThing(b, names[b % len(names)], required))
    return big_things, eff_T


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
@dataclass
class Agent:
    idx: int
    held: Set[int] = field(default_factory=set)        # loose elements
    order: List[int] = field(default_factory=list)     # acquisition order (recency/ordering)
    chunks: Set[int] = field(default_factory=set)      # compressed big things (bids)
    latent: Set[int] = field(default_factory=set)      # bids satisfying sufficiency
    manifest: Set[int] = field(default_factory=set)    # bids triggered into action
    variant: Dict[int, Tuple[int, ...]] = field(default_factory=dict)
    is_change_agent: bool = False


# ---------------------------------------------------------------------------
# The world
# ---------------------------------------------------------------------------
class World:
    def __init__(self, cfg: dict):
        self.cfg = C.validate_config(cfg)
        self.rng = np.random.default_rng(int(self.cfg["seed"]))
        self.big_things, self.n_element_types = build_big_things(self.cfg)
        self.element_owners = self._element_owner_map()
        self.adjacency, self.tie_strength = topo.build_network(self.cfg, self.rng)
        self.n = len(self.adjacency)
        self.chunk_cost = 2 if self.cfg["differential_slot_cost"] else 1
        self.t = 0
        self.trigger_fired_at: List[int] = []
        self.lapses = 0  # cumulative reversions (manifest -> non-adopter); churn measure
        # Side-effect-only counter of element acquisitions through _add_element.
        # Used to check empirically that two transmissibility arms move the same
        # amount of material per unit time rather than trusting the arithmetic.
        # Never read by the dynamics.
        self.elements_added = 0
        # Observational instrumentation only. These counters are incremented
        # AFTER a transfer has already succeeded, draw no random numbers, and
        # touch no agent state, so they cannot alter a trajectory. Verified by
        # reproducing canonical cell values bit for bit.
        self.transfers_relevant = 0
        self.transfers_from_manifest_sender = 0
        self.transfers_from_nonmanifest_sender = 0
        self.transfers_irrelevant = 0
        # side-effect-only eviction counters, for the packetization diagnostics
        self.evictions = 0
        self.evictions_required = 0
        self.agents: List[Agent] = [Agent(i) for i in range(self.n)]
        self.history: List[dict] = []
        self._positions = None  # lazily computed for the viewer
        self._seed_population()
        self._recompute_all_latent()
        self.history.append(self.metrics())

    # ---- setup -----------------------------------------------------------
    def _element_owner_map(self) -> Dict[int, List[int]]:
        owners: Dict[int, List[int]] = {}
        for bt in self.big_things:
            for e in bt.required:
                owners.setdefault(e, []).append(bt.bid)
        return owners

    def _seed_population(self):
        cfg = self.cfg
        T = self.n_element_types
        scheme = cfg["seeding_scheme"]
        dens = cfg["initial_element_density"]

        if scheme == "single_source":
            # All initial elements concentrated in a few seed agents.
            n_seeds = max(1, int(round(0.05 * self.n)))
            seeds = self.rng.choice(self.n, size=n_seeds, replace=False)
            for s in seeds:
                for e in range(T):
                    self._add_element(self.agents[s], e, enforce_capacity=False)
        elif scheme == "clustered":
            # Each element type is concentrated in a contiguous block of agents.
            for e in range(T):
                block = max(1, int(round(dens * self.n)))
                start = int(self.rng.integers(0, self.n))
                for d in range(block):
                    a = self.agents[(start + d) % self.n]
                    self._add_element(a, e, enforce_capacity=False)
        else:  # uniform_random
            for a in self.agents:
                for e in range(T):
                    if self.rng.random() < dens:
                        self._add_element(a, e, enforce_capacity=False)

        if cfg["change_agent_scenario"]:
            self._inject_change_agents()

        # Enforce capacity once after seeding (single_source/clustered may overfill).
        for a in self.agents:
            self._enforce_capacity(a)

    def _inject_change_agents(self):
        cfg = self.cfg
        n_ca = max(1, int(round(cfg["change_agent_fraction"] * self.n)))
        target = self.big_things[0]  # change agents push the first big thing
        if cfg["change_agent_clustered"]:
            start = int(self.rng.integers(0, self.n))
            idxs = [(start + d) % self.n for d in range(n_ca)]
        else:
            idxs = list(self.rng.choice(self.n, size=n_ca, replace=False))
        for i in idxs:
            a = self.agents[i]
            a.is_change_agent = True
            # Fully equipped with the target big thing and already manifest.
            for e in target.required:
                if e not in a.held:
                    a.held.add(e)
                    a.order.append(e)
            a.latent.add(target.bid)
            self._manifest(a, target.bid)

    # ---- per-big-thing endowments (W5 ecology; absent => global, no-op) --
    def _endow(self, bid: int, key: str, default):
        """Per-big-thing mechanism value. When no bigthing_endowments dict is
        configured this returns the global default, so behavior is byte-identical
        to the single-switch model. When present, each big thing carries its own
        compression / stabilization / enhanced settings (a competitive ecology)."""
        endow = self.cfg.get("bigthing_endowments")
        if not endow:
            return default
        return endow.get(bid, {}).get(key, default)

    def _stab_boost_for(self, a: "Agent", e: int):
        """Effective stabilization boost protecting element e (the most protective
        across the manifest big things that own it and stabilize it), or None if
        unprotected. Reduces exactly to the global stabilization check when no
        per-big-thing endowments are set."""
        endow = self.cfg.get("bigthing_endowments")
        if not endow:
            if self.cfg["stabilization"] and self._is_stabilized(a, e):
                return self.cfg["stabilization_boost"]
            return None
        best = None
        for bid in self.element_owners.get(e, []):
            if bid in a.manifest and endow.get(bid, {}).get("stabilization", False):
                b = endow.get(bid, {}).get("stabilization_boost",
                                           self.cfg["stabilization_boost"])
                best = b if best is None else min(best, b)
        return best

    # ---- element bookkeeping --------------------------------------------
    def _capacity_used(self, a: Agent) -> int:
        return len(a.held) + self.chunk_cost * len(a.chunks)

    def _record_transfer(self, sender: Agent, e: int):
        """Classify a successful transfer by the sender's manifest state.

        A transfer is 'relevant' when the element belongs to at least one big
        thing. It counts as coming from a manifest sender when the sender is
        manifest for at least one big thing that element serves, and from a
        nonmanifest sender otherwise. Purely observational: no rng, no state.
        """
        owners = self.element_owners.get(e, [])
        if not owners:
            self.transfers_irrelevant += 1
            return
        self.transfers_relevant += 1
        if any(bid in sender.manifest for bid in owners):
            self.transfers_from_manifest_sender += 1
        else:
            self.transfers_from_nonmanifest_sender += 1

    def _add_element(self, a: Agent, e: int, enforce_capacity: bool = True) -> bool:
        if e in a.held:
            return False
        if enforce_capacity and self._capacity_used(a) + 1 > self.cfg["capacity"]:
            if not self._make_room(a, incoming=e):
                return False
        a.held.add(e)
        a.order.append(e)
        self.elements_added += 1
        return True

    def _make_room(self, a: Agent, incoming: int) -> bool:
        """Evict one loose element per the eviction rule. Chunks are never
        evicted. Returns True if room was freed."""
        if not a.held:
            return False
        rule = self.cfg["eviction_rule"]
        candidates = list(a.held)
        if rule == "random":
            victim = candidates[int(self.rng.integers(0, len(candidates)))]
        elif rule == "recency":
            victim = next((e for e in a.order if e in a.held), candidates[0])
        else:  # value_weighted: drop the element least useful to a near-complete big thing
            victim = min(candidates, key=lambda e: self._element_value(a, e))
        self.evictions += 1
        if self.element_owners.get(victim):
            self.evictions_required += 1
        self._remove_element(a, victim)
        return True

    def _element_value(self, a: Agent, e: int) -> float:
        """How much element e contributes to completing some big thing for a.
        Higher = more worth keeping. Stabilized elements get protected."""
        best = 0
        for bid in self.element_owners.get(e, []):
            bt = self.big_things[bid]
            best = max(best, len(a.held & bt.required_set))
        val = float(best)
        sb = self._stab_boost_for(a, e)
        if sb is not None:
            # Make stabilized elements expensive to evict (boost in (0,1] -> divide).
            boost = max(1e-3, sb)
            val = val / boost + 1.0
        # Tiny random jitter for tie-breaking, deterministic via rng.
        return val + 1e-6 * self.rng.random()

    def _remove_element(self, a: Agent, e: int):
        a.held.discard(e)
        # keep order list lean
        if e in a.order:
            try:
                a.order.remove(e)
            except ValueError:
                pass

    def _is_stabilized(self, a: Agent, e: int) -> bool:
        for bid in self.element_owners.get(e, []):
            if bid in a.manifest:
                return True
        return False

    def _enforce_capacity(self, a: Agent):
        while self._capacity_used(a) > self.cfg["capacity"] and a.held:
            self._make_room(a, incoming=-1)

    # ---- latent / manifest ----------------------------------------------
    def _count_required(self, a: Agent, bt: BigThing) -> int:
        if bt.bid in a.chunks or bt.bid in a.manifest:
            return len(bt.required)  # fully realized
        return len(a.held & bt.required_set)

    def _is_latent_for(self, a: Agent, bt: BigThing) -> bool:
        enc = self.cfg["requirement_encoding"]
        cnt = self._count_required(a, bt)
        if enc == "additive":
            return cnt >= self.cfg["requirement_size"]  # needs the full set (the slider full)
        # set_sufficiency and ordering both use k-of-R
        return cnt >= self.cfg["sufficiency_k"]

    def _recompute_latent(self, a: Agent):
        need = (self.cfg["requirement_size"] if self.cfg["requirement_encoding"] == "additive"
                else self.cfg["sufficiency_k"])
        for bt in self.big_things:
            if bt.bid in a.manifest:
                # Reversible adoption: a node that falls below sufficiency lapses
                # back to non-adopter. A chunk-held big thing is fully realized and
                # cannot lapse this way. Persistence comes from stabilization, which
                # protects the elements that keep a node above threshold. We check
                # actual held elements here (not _count_required, which reports a
                # manifest node as fully realized).
                held_cnt = len(a.held & bt.required_set)
                if (self.cfg["reversible_adoption"] and bt.bid not in a.chunks
                        and held_cnt < need):
                    a.manifest.discard(bt.bid)
                    a.variant.pop(bt.bid, None)
                    self.lapses += 1
                else:
                    continue
            # Under incompatibility, a node committed to one big thing is not
            # "ready" for another (so the trigger never tries to flip it).
            if self.cfg["incompatibility"] and any(o != bt.bid for o in a.manifest):
                a.latent.discard(bt.bid)
                continue
            if self._is_latent_for(a, bt):
                a.latent.add(bt.bid)
            else:
                a.latent.discard(bt.bid)

    def _recompute_all_latent(self):
        for a in self.agents:
            self._recompute_latent(a)

    def _variant_for(self, a: Agent, bt: BigThing) -> Tuple[int, ...]:
        held_req = [e for e in bt.required if e in a.held]
        if self.cfg["requirement_encoding"] == "ordering":
            # order of acquisition selects the manifestation
            return tuple(e for e in a.order if e in bt.required_set)
        return tuple(sorted(held_req))

    def _manifest(self, a: Agent, bid: int):
        bt = self.big_things[bid]
        if bid in a.manifest:
            return
        # Content-specific exclusivity: cannot hold two big things at once.
        if self.cfg["incompatibility"] and any(o != bid for o in a.manifest):
            return
        a.variant[bid] = self._variant_for(a, bt)
        a.manifest.add(bid)
        a.latent.discard(bid)
        comp = self._endow(bid, "compression", self.cfg["compression"])
        # A per-big-thing endowment may set compression to a probability in [0,1]
        # (graded "encapsulation" for the W5 ecology). A bool keeps the original
        # deterministic behavior and draws no rng, so existing runs are unchanged.
        do_compress = comp is True if isinstance(comp, bool) else self.rng.random() < float(comp)
        if do_compress:
            # constituent loose elements collapse into a chunk
            for e in list(bt.required):
                if e in a.held:
                    self._remove_element(a, e)
            a.chunks.add(bid)

    # ---- transmission ----------------------------------------------------
    def _transmittable_elements(self, sender: Agent) -> List[int]:
        # In every mode, loose elements can be handed over piecemeal.
        if self.cfg.get("member_gated_transmission"):
            # Recruitment runs through active members: only elements of a big thing
            # the sender is manifest for can be transmitted. Absent this flag the
            # behavior is unchanged (any held element is transmittable).
            return [e for e in sender.held
                    if any(bid in sender.manifest
                           for bid in self.element_owners.get(e, []))]
        return list(sender.held)

    def _send_prob(self, sender: Agent, e: int, strength: float) -> float:
        p = self.cfg["transmission_prob"]
        if self.cfg["tie_strength_channels"]:
            p *= strength
        for bid in self.element_owners.get(e, []):
            if bid in sender.manifest and self._endow(
                    bid, "enhanced_transmission", self.cfg["enhanced_transmission"]):
                p *= self._endow(bid, "enhanced_factor", self.cfg["enhanced_factor"])
                break
        if sender.is_change_agent:
            p *= self.cfg["change_agent_evangelism"]
        return min(1.0, p)

    def _accept_factor(self, receiver: Agent, e: int) -> float:
        """Coupling multiplier on the probability an incoming element 'takes'."""
        if self.cfg.get("coupling_matrix") is not None:
            return self._accept_factor_matrix(receiver, e)
        cs = self.cfg["coupling_strength"]
        if cs == 0.0:
            return 1.0
        effect = 0.0
        owners = set(self.element_owners.get(e, []))

        if self.cfg["internal_coupling"]:
            if self.cfg["coupling_level"] == "big_thing":
                for bid in (receiver.manifest | receiver.latent):
                    if bid not in owners:           # off-diagonal only
                        effect += cs
            else:  # element level
                other = sum(1 for h in receiver.held
                            if owners.isdisjoint(self.element_owners.get(h, [])))
                effect += cs * (other / max(1, self.n_element_types))

        if self.cfg["neighbor_coupling"]:
            nbrs = self.adjacency[receiver.idx]
            if nbrs:
                # same-target facilitation == complex contagion (always positive)
                for bid in owners:
                    f_same = sum(1 for j in nbrs
                                 if bid in self.agents[j].manifest
                                 or bid in self.agents[j].latent) / len(nbrs)
                    effect += abs(cs) * f_same
                # off-target signed influence
                for bt in self.big_things:
                    if bt.bid in owners:
                        continue
                    f_a = sum(1 for j in nbrs
                              if bt.bid in self.agents[j].manifest
                              or bt.bid in self.agents[j].latent) / len(nbrs)
                    effect += cs * f_a
        return float(np.clip(1.0 + effect, 0.0, 3.0))

    def _accept_factor_matrix(self, receiver: Agent, e: int) -> float:
        """Coupling via an explicit B x B matrix M (W6). M[i][j] is the influence
        of source big thing j on acceptance of an element feeding target big thing
        i. The DIAGONAL M[i][i] is same-target reinforcement (complex contagion);
        the OFF-DIAGONAL M[i][j], i!=j, is cross-target facilitation/suppression.
        This separates the two effects that the single coupling_strength scalar
        welds together. Operates at big-thing level."""
        M = self.cfg["coupling_matrix"]
        owners = set(self.element_owners.get(e, []))
        if not owners:
            return 1.0
        effect = 0.0
        if self.cfg["internal_coupling"]:
            held = receiver.manifest | receiver.latent
            for i in owners:
                for j in held:
                    effect += M[i][j]
        if self.cfg["neighbor_coupling"]:
            nbrs = self.adjacency[receiver.idx]
            if nbrs:
                for i in owners:
                    for bt in self.big_things:
                        j = bt.bid
                        f_j = sum(1 for k in nbrs
                                  if j in self.agents[k].manifest
                                  or j in self.agents[k].latent) / len(nbrs)
                        effect += M[i][j] * f_j
        return float(np.clip(1.0 + effect, 0.0, 3.0))

    def _whole_package_candidates(self, sender: Agent, receiver: Agent) -> List[int]:
        """Big things sender can hand over as a unit, per transmissibility mode."""
        mode = self.cfg["transmissibility_mode"]
        if mode == "elements_only":
            return []
        out = []
        for bid in sender.manifest:
            if bid in receiver.manifest:
                continue
            if mode in ("whole_package", "whole_package_gated"):
                out.append(bid)
            elif mode == "both":
                # chunk passes intact only to someone equipped to receive it
                if self._equipped_to_receive(receiver, bid):
                    out.append(bid)
        return out

    def _equipped_to_receive(self, receiver: Agent, bid: int) -> bool:
        bt = self.big_things[bid]
        if bid in receiver.chunks or bid in receiver.latent or bid in receiver.manifest:
            return True
        return len(receiver.held & bt.required_set) >= max(1, self.cfg["sufficiency_k"] - 1)

    def _deliver_whole(self, receiver: Agent, bid: int):
        bt = self.big_things[bid]
        if self.cfg["transmissibility_mode"] == "whole_package_gated":
            # Cue-matched twin of whole_package: the assembled element set arrives
            # as a unit, but adoption still waits for the trigger (as in
            # elements_only). Latency is recomputed at end of tick; do not manifest.
            for e in bt.required:
                self._add_element(receiver, e)
            return
        if self._endow(bid, "compression", self.cfg["compression"]):
            receiver.chunks.add(bid)
        else:
            for e in bt.required:
                self._add_element(receiver, e)
        receiver.latent.add(bid)
        self._manifest(receiver, bid)

    def _contact(self, sender: Agent, receiver: Agent, strength: float):
        # Whole-package transfer (only in whole_package / both modes).
        # whole_package_transfer_prob defaults to 1.0, which is the original
        # behaviour: an eligible package is always delivered. Below 1.0 it gates
        # the transfer so the package arm can be matched to elements_only on the
        # amount of material moved per contact.
        wp = self.cfg["whole_package_transfer_prob"]
        for bid in self._whole_package_candidates(sender, receiver):
            if wp >= 1.0 or self.rng.random() < wp:
                self._deliver_whole(receiver, bid)

        # Piecemeal element transfer (the heart of the model).
        elems = self._transmittable_elements(sender)
        if not elems:
            return
        e = elems[int(self.rng.integers(0, len(elems)))]
        if e in receiver.held:
            return
        p = self._send_prob(sender, e, strength) * self._accept_factor(receiver, e)
        if self.rng.random() < min(1.0, p):
            if self._add_element(receiver, e):
                self._record_transfer(sender, e)

    # ---- per-tick processes ---------------------------------------------
    def _do_loss(self):
        if self.cfg["loss_rate"] <= 0.0:
            return
        for a in self.agents:
            for e in list(a.held):
                p = self.cfg["loss_rate"]
                sb = self._stab_boost_for(a, e)
                if sb is not None:
                    p *= sb
                if self.rng.random() < p:
                    self._remove_element(a, e)

    def _apply_trigger(self):
        cfg = self.cfg
        reach = cfg["trigger_reach"]
        if cfg["trigger_type"] == "exogenous":
            tt = max(1, cfg["trigger_time"])
            if self.t % tt != 0:
                return
            self.trigger_fired_at.append(self.t)
            for a in self.agents:
                for bid in list(a.latent):
                    if self.rng.random() < reach:
                        self._manifest(a, bid)
        else:  # endogenous
            thr = cfg["endogenous_trigger_threshold"]
            fired = False
            for a in self.agents:
                nbrs = self.adjacency[a.idx]
                if not nbrs:
                    continue
                for bid in list(a.latent):
                    f = sum(1 for j in nbrs
                            if bid in self.agents[j].manifest
                            or bid in self.agents[j].latent) / len(nbrs)
                    if f >= thr and self.rng.random() < reach:
                        self._manifest(a, bid)
                        fired = True
            if fired:
                self.trigger_fired_at.append(self.t)

    def step(self):
        self.t += 1
        cfg = self.cfg
        contacts = cfg["contacts_per_tick"]

        if cfg["scheduling"] == "synchronous":
            # gather all transfers against the start-of-tick state, then apply.
            pending = []
            for a in self.agents:
                nbrs = self.adjacency[a.idx]
                if not nbrs:
                    continue
                for _ in range(contacts):
                    k = int(self.rng.integers(0, len(nbrs)))
                    pending.append((a.idx, nbrs[k], self.tie_strength[a.idx][k]))
            for si, ri, strength in pending:
                self._contact(self.agents[si], self.agents[ri], strength)
        else:  # asynchronous
            order = self.rng.permutation(self.n)
            for si in order:
                a = self.agents[si]
                nbrs = self.adjacency[si]
                if not nbrs:
                    continue
                for _ in range(contacts):
                    k = int(self.rng.integers(0, len(nbrs)))
                    self._contact(a, self.agents[nbrs[k]], self.tie_strength[si][k])

        self._do_loss()
        for a in self.agents:
            self._enforce_capacity(a)
            self._recompute_latent(a)
        self._apply_trigger()

        snap = self.metrics()
        self.history.append(snap)
        return snap

    # ---- metrics ---------------------------------------------------------
    def metrics(self) -> dict:
        n = self.n
        per_big = {}
        for bt in self.big_things:
            n_manifest = sum(1 for a in self.agents if bt.bid in a.manifest)
            n_latent = sum(1 for a in self.agents if bt.bid in a.latent)
            n_at_risk = sum(1 for a in self.agents
                            if bt.bid not in a.manifest and bt.bid not in a.latent
                            and self._count_required(a, bt) == self.cfg["sufficiency_k"] - 1)
            n_resistant = sum(1 for a in self.agents
                              if self._count_required(a, bt) == 0)
            variants = {}
            for a in self.agents:
                if bt.bid in a.variant:
                    key = ",".join(map(str, a.variant[bt.bid]))
                    variants[key] = variants.get(key, 0) + 1
            per_big[bt.label] = {
                "manifest": n_manifest,
                "latent": n_latent,
                "at_risk": n_at_risk,
                "resistant": n_resistant,
                "variants": variants,
            }
        total_required = set()
        for bt in self.big_things:
            total_required |= bt.required_set
        elem_sat = (sum(len(a.held) for a in self.agents)
                    / (n * self.n_element_types)) if n else 0.0
        # observability gap: avg element-saturation of big-thing elements minus avg manifest share
        bt_elem_sat = (sum(len(a.held & total_required) for a in self.agents)
                       / (n * len(total_required))) if total_required else 0.0
        manifest_share = (sum(len(a.manifest) for a in self.agents)
                          / (n * len(self.big_things))) if self.big_things else 0.0
        return {
            "t": self.t,
            "element_saturation": elem_sat,
            "bigthing_element_saturation": bt_elem_sat,
            "manifest_share": manifest_share,
            "observability_gap": bt_elem_sat - manifest_share,
            "lapses": self.lapses,
            "per_big": per_big,
        }

    # ---- run -------------------------------------------------------------
    def quiescent(self) -> bool:
        w = self.cfg["quiescence_window"]
        if w <= 0 or len(self.history) <= w + 1:
            return False
        recent = self.history[-(w + 1):]
        first = recent[0]["element_saturation"]
        return all(abs(s["element_saturation"] - first) < 1e-9 for s in recent)

    def run(self, max_ticks: Optional[int] = None, progress=None):
        limit = max_ticks if max_ticks is not None else self.cfg["run_length"]
        for _ in range(limit):
            self.step()
            if progress is not None:
                progress(self.t, limit, self.history[-1])
            if self.quiescent():
                break
        return self.history

    # ---- viewer support --------------------------------------------------
    def positions(self):
        if self._positions is None:
            self._positions = topo.layout_positions(
                self.adjacency, np.random.default_rng(int(self.cfg["seed"]) + 7))
        return self._positions

    def agent_states(self) -> List[dict]:
        """Per-agent state for the live network view."""
        out = []
        for a in self.agents:
            # dominant status for coloring: manifest > latent > at-risk > none
            status = "none"
            best_bid = None
            if a.manifest:
                status = "manifest"
                best_bid = sorted(a.manifest)[0]
            elif a.latent:
                status = "latent"
                best_bid = sorted(a.latent)[0]
            else:
                for bt in self.big_things:
                    if self._count_required(a, bt) == self.cfg["sufficiency_k"] - 1:
                        status = "at_risk"
                        best_bid = bt.bid
                        break
            out.append({
                "i": a.idx,
                "status": status,
                "bid": best_bid,
                "n_held": len(a.held),
                "is_change_agent": a.is_change_agent,
            })
        return out

    def edges(self) -> List[Tuple[int, int]]:
        out = []
        for i in range(self.n):
            for j in self.adjacency[i]:
                if j > i:
                    out.append((i, j))
        return out
