"""Cheap structural invariants asserted during/after a run.

These catch the bookkeeping bugs that stacking many mechanisms tends to
introduce. They are the implementation-level sanity checks the design doc asked
for, distinct from the experimental sanity gates (V0 saturates, V1 produces
terrain) which live in the phase predictions / tests.
"""

from typing import List
from .model import World


class InvariantError(AssertionError):
    pass


def check_state(world: World):
    """Assert invariants on the current world state. Raises InvariantError."""
    cfg = world.cfg
    for a in world.agents:
        # 1. No agent ever exceeds the capacity cap.
        used = world._capacity_used(a)
        if used > cfg["capacity"]:
            raise InvariantError(
                f"agent {a.idx} capacity {used} > cap {cfg['capacity']}")
        # 2. A LATENT agent currently meets sufficiency. (Manifestation is an
        #    event: once manifest, an agent may later drop below sufficiency via
        #    eviction/loss and still remain manifest -- conversion persists, which
        #    is exactly why the stabilization mechanism exists. So we check the
        #    live latent set, not the manifest set.)
        need = (cfg["requirement_size"] if cfg["requirement_encoding"] == "additive"
                else cfg["sufficiency_k"])
        for bid in a.latent:
            bt = world.big_things[bid]
            cnt = world._count_required(a, bt)
            if cnt < need:
                raise InvariantError(
                    f"agent {a.idx} latent for {bt.label} with {cnt} < {need} elements")
        # 3. Held elements are valid types.
        for e in a.held:
            if not (0 <= e < world.n_element_types):
                raise InvariantError(f"agent {a.idx} holds invalid element {e}")


def check_monotonic_adoption(history: List[dict]):
    """When loss and capacity pressure are absent, total adoption only grows.

    Caller is responsible for only invoking this when loss_rate == 0 and
    capacity is effectively non-binding (e.g. the V0 baseline).
    """
    prev = -1.0
    for snap in history:
        cur = snap["manifest_share"]
        if cur + 1e-9 < prev:
            raise InvariantError(
                f"adoption decreased at t={snap['t']}: {prev} -> {cur}")
        prev = cur


def run_with_checks(world: World, every: int = 25, max_ticks=None) -> List[dict]:
    """Run a world, asserting state invariants every `every` ticks."""
    limit = max_ticks if max_ticks is not None else world.cfg["run_length"]
    for _ in range(limit):
        world.step()
        if world.t % every == 0:
            check_state(world)
        if world.quiescent():
            break
    check_state(world)
    return world.history
