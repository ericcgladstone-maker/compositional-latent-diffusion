"""Sanity + invariant tests for the latent-adoption ABM.

These encode the experimental sanity gates from the design (V0 saturates, V1 is
constrained, the transmissibility wedge separates the regimes) plus the
structural invariants that catch bookkeeping bugs.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abm import config as C
from abm import phases as P
from abm import invariants
from abm.model import World


# ---------------------------------------------------------------------------
# Config registry
# ---------------------------------------------------------------------------
def test_defaults_complete():
    cfg = C.default_config()
    assert set(cfg) == set(C.PARAM_INDEX)
    assert cfg["capacity"] == 6 and cfg["requirement_size"] == 4


def test_validate_drops_unknown_and_coerces():
    cfg = C.validate_config({"capacity": "8", "bogus": 1, "stabilization": "true"})
    assert cfg["capacity"] == 8 and "bogus" not in cfg and cfg["stabilization"] is True


def test_validate_rejects_bad_choice():
    with pytest.raises(ValueError):
        C.validate_config({"topology": "hypercube"})


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
def test_same_seed_same_result():
    cfg = P.config_for_phase("V1", {"seed": 42, "run_length": 300})
    a = World(dict(cfg)); a.run()
    b = World(dict(cfg)); b.run()
    assert a.history[-1]["manifest_share"] == b.history[-1]["manifest_share"]
    assert a.history[-1]["element_saturation"] == b.history[-1]["element_saturation"]


def test_different_seed_can_differ():
    base = P.config_for_phase("V1", {"run_length": 400})
    xs = []
    for s in range(4):
        w = World({**base, "seed": s}); w.run()
        xs.append(w.history[-1]["manifest_share"])
    assert len(set(xs)) > 1  # stochastic, should not all be identical


# ---------------------------------------------------------------------------
# Experimental sanity gates
# ---------------------------------------------------------------------------
def test_v0_saturates():
    w = World(P.config_for_phase("V0", {"seed": 1, "run_length": 800}))
    w.run()
    assert w.history[-1]["manifest_share"] > 0.95


def test_v1_constrained_below_v0():
    w0 = World(P.config_for_phase("V0", {"seed": 1, "run_length": 800})); w0.run()
    w1 = World(P.config_for_phase("V1", {"seed": 1, "run_length": 1500})); w1.run()
    assert w1.history[-1]["manifest_share"] < w0.history[-1]["manifest_share"]


def test_wedge_whole_package_spreads_more_than_elements_only():
    # The defining contrast: under whole-package transmission the big thing moves
    # like a standard contagion; under elements-only it must reassemble piecemeal.
    common = {"seed": 3, "run_length": 800}
    eo = World(P.config_for_phase("V1-W", {**common, "transmissibility_mode": "elements_only"})); eo.run()
    wp = World(P.config_for_phase("V1-W", {**common, "transmissibility_mode": "whole_package"})); wp.run()
    assert wp.history[-1]["manifest_share"] >= eo.history[-1]["manifest_share"]


# ---------------------------------------------------------------------------
# Structural invariants
# ---------------------------------------------------------------------------
def test_capacity_never_exceeded_v1():
    w = World(P.config_for_phase("V1", {"seed": 5, "run_length": 600}))
    invariants.run_with_checks(w, every=20)
    for a in w.agents:
        assert w._capacity_used(a) <= w.cfg["capacity"]


def test_no_manifest_below_sufficiency_elements_only():
    w = World(P.config_for_phase("V1", {"seed": 7, "run_length": 600}))
    w.run()
    invariants.check_state(w)  # raises if any manifest holds < sufficiency_k elements


def test_change_agent_scenario_runs_and_seeds():
    w = World(P.config_for_phase("change-agent", {"seed": 2, "run_length": 200}))
    n_ca = sum(1 for a in w.agents if a.is_change_agent)
    assert n_ca >= 1
    w.run()
    invariants.check_state(w)


# ---------------------------------------------------------------------------
# Every phase builds and steps without error
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("phase_id", [p["id"] for p in P.PHASES])
def test_phase_builds_and_steps(phase_id):
    w = World(P.config_for_phase(phase_id, {"seed": 1, "run_length": 60}))
    w.run()
    invariants.check_state(w)
    assert w.t > 0


# ---------------------------------------------------------------------------
# Mechanisms actually change behaviour
# ---------------------------------------------------------------------------
def test_compression_frees_capacity():
    # With compression on, an agent can end up effectively holding more big things
    # than capacity/requirement_size would allow as loose elements.
    w = World(P.config_for_phase("V2-compression", {"seed": 4, "run_length": 800}))
    w.run()
    invariants.check_state(w)
    assert any(len(a.chunks) >= 1 for a in w.agents)
