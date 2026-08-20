"""Latent-adoption / combinatoric-diffusion ABM.

One canonical model core (model.py) driven by two front-ends:
  - the live viewer (server.py + viewer/)  -- intuition, phase selection, the
    Schelling-style "nudge a knob, watch the regime flip" exploration;
  - the headless sweep (sweep.py)          -- reproducible batch runs for the record.

All parameters live in config.py (nothing buried). Build stages live in phases.py.
"""

from . import config, model, phases, sweep, invariants, topology  # noqa: F401

__all__ = ["config", "model", "phases", "sweep", "invariants", "topology"]
