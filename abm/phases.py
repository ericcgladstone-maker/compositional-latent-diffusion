"""Build-stage phases and the focal sweeps attached to each.

Each phase is expressed as a set of config OVERRIDES on top of the registry
defaults (config.default_config()). Phases are the experimental backbone: every
stage is the control condition for the next, so each mechanism's contribution is
cleanly attributable.

Each phase also names a `focal` parameter and the values to sweep for it -- this
is what the viewer's "select a phase" and the sweep runner both use. The phase
list IS the "absolute beginning to absolute end" exploration path.
"""

from typing import List
from . import config as C


def _v0_overrides() -> dict:
    # Unrestricted baseline: unlimited capacity, immediate manifestation,
    # everything else off. Should saturate.
    return {
        "capacity": 64,            # effectively unlimited for our element counts
        "trigger_type": "exogenous",
        "trigger_time": 1,         # latent -> manifest immediately, every tick
        "trigger_reach": 1.0,
        "loss_rate": 0.0,
        "differential_slot_cost": False,
        "compression": False,
        "stabilization": False,
        "enhanced_transmission": False,
        "tie_strength_channels": False,
        "internal_coupling": False,
        "neighbor_coupling": False,
        "coupling_strength": 0.0,
        "change_agent_scenario": False,
        "transmissibility_mode": "elements_only",
    }


def _v1_overrides() -> dict:
    # Capacity + competition. The core result.
    ov = _v0_overrides()
    ov.update({
        "capacity": 6,
        "trigger_time": 100,       # real, periodic exogenous trigger
        "trigger_reach": 1.0,
    })
    return ov


PHASES: List[dict] = [
    {
        "id": "V0",
        "title": "V0 — unrestricted baseline",
        "desc": "Elements diffuse, big things activate on composition, unlimited "
                "capacity. Should saturate. Confirms the machinery.",
        "overrides": _v0_overrides(),
        "focal": {"param": "initial_element_density", "values": [0.05, 0.1, 0.15, 0.2]},
        "predict": "Everyone acquires everything; all big things activate.",
    },
    {
        "id": "V1",
        "title": "V1 — capacity & competition",
        "desc": "Adds activation threshold + capacity cap. The core result: "
                "pockets, at-risk groups, resistant groups, sudden flips.",
        "overrides": _v1_overrides(),
        "focal": {"param": "capacity", "values": [4, 5, 6, 7, 8, 10]},
        "predict": "Hilly terrain; no universal saturation.",
    },
    {
        "id": "V1-W",
        "title": "V1-W — the transmissibility wedge",
        "desc": "V1 held fixed; sweep the transmissibility mode. Establishes the "
                "wedge in isolation before any elaboration.",
        "overrides": _v1_overrides(),
        "focal": {"param": "transmissibility_mode",
                  "values": ["elements_only", "whole_package", "both"]},
        "predict": "whole_package recovers SIR/complex contagion; elements_only "
                   "gives latent adoption (long inertia then sudden manifestation).",
    },
    {
        "id": "V2-slotcost",
        "title": "V2 — differential slot costs",
        "desc": "Big ideas (compressed chunks) cost 2 slots.",
        "overrides": {**_v1_overrides(), "compression": True, "differential_slot_cost": True},
        "focal": {"param": "capacity", "values": [4, 6, 8, 10]},
        "predict": "Tighter capacity pressure than V1.",
    },
    {
        "id": "V2-compression",
        "title": "V2 — compression",
        "desc": "On activation, elements collapse into a chunk that frees "
                "capacity but can no longer transmit as pieces.",
        "overrides": {**_v1_overrides(), "compression": True},
        "focal": {"param": "transmission_prob", "values": [0.05, 0.1, 0.2, 0.3]},
        "predict": "Frees capacity; reduces downstream transmissibility.",
    },
    {
        "id": "V2-stabilization",
        "title": "V2 — stabilization",
        "desc": "On activation, constituent elements become harder to dislodge.",
        "overrides": {**_v1_overrides(), "stabilization": True,
                      "loss_rate": 0.01, "eviction_rule": "random"},
        "focal": {"param": "stabilization_boost", "values": [0.0, 0.25, 0.5, 0.75, 1.0]},
        "predict": "Entrenched adoption; reservoirs persist.",
    },
    {
        "id": "V2-enhanced",
        "title": "V2 — enhanced transmission",
        "desc": "On activation, constituent elements become more transmissible.",
        "overrides": {**_v1_overrides(), "enhanced_transmission": True},
        "focal": {"param": "enhanced_factor", "values": [1.0, 1.5, 2.0, 3.0]},
        "predict": "Faster secondary spread once a pocket flips.",
    },
    {
        "id": "V2-stab-enh",
        "title": "V2+ — stabilization × enhanced (interaction)",
        "desc": "The explicit interaction condition.",
        "overrides": {**_v1_overrides(), "stabilization": True,
                      "enhanced_transmission": True, "loss_rate": 0.01},
        "focal": {"param": "enhanced_factor", "values": [1.0, 2.0, 3.0]},
        "predict": "Compounding or offsetting of the two mechanisms.",
    },
    {
        "id": "V2-tiestrength",
        "title": "V2 — tie-strength channels (90/10)",
        "desc": "Most element bits arrive via many weak ties; few via strong ties.",
        "overrides": {**_v1_overrides(), "tie_strength_channels": True},
        "focal": {"param": "strong_tie_fraction", "values": [0.0, 0.05, 0.1, 0.2, 0.3]},
        "predict": "Latent preparation as a predominantly weak-tie phenomenon.",
    },
    {
        "id": "V2-internal-coupling",
        "title": "V2 — internal coupling (extension)",
        "desc": "Signed: a held big thing biases adoption of other big things.",
        "overrides": {**_v1_overrides(), "internal_coupling": True, "coupling_strength": -0.5},
        "focal": {"param": "coupling_strength", "values": [-1.0, -0.5, 0.0, 0.5, 1.0]},
        "predict": "Correlated bundles instead of generic crowding.",
    },
    {
        "id": "V2-neighbor-coupling",
        "title": "V2 — neighbor coupling (extension)",
        "desc": "Signed: a neighbor's big thing biases your adoption of others. "
                "Subsumes complex contagion as the same-target cell.",
        "overrides": {**_v1_overrides(), "neighbor_coupling": True, "coupling_strength": -0.5},
        "focal": {"param": "coupling_strength", "values": [-1.0, -0.5, 0.0, 0.5, 1.0]},
        "predict": "Social-pressure suppression / facilitation across big things.",
    },
    {
        "id": "V2-incompatibility",
        "title": "V2 — content-specific incompatibility (extension)",
        "desc": "Big things made mutually exclusive: a node holds at most one at a "
                "time. The clean, content-specific version of exclusivity, distinct "
                "from capacity and from the coupling -1 floor.",
        "overrides": _v1_overrides(),
        "focal": {"param": "incompatibility", "values": [False, True]},
        "predict": "With exclusivity on, a node holds at most one big thing, so total "
                   "adoption falls toward half of the unconstrained level.",
    },
    {
        "id": "change-agent",
        "title": "Scenario — change-agent seeding",
        "desc": "Equipped, manifest minority injected into an unprepared "
                "population. Produces the failed-diffusion signature.",
        "overrides": {**_v1_overrides(), "change_agent_scenario": True,
                      "initial_element_density": 0.05},
        "focal": {"param": "change_agent_fraction", "values": [0.05, 0.1, 0.15, 0.2]},
        "predict": "Fails to spread under elements_only despite full equipment.",
    },
]

PHASE_INDEX = {p["id"]: p for p in PHASES}


def config_for_phase(phase_id: str, extra_overrides: dict = None) -> dict:
    """Resolve a phase id to a full validated config."""
    if phase_id not in PHASE_INDEX:
        raise ValueError(f"unknown phase {phase_id!r}; have {list(PHASE_INDEX)}")
    cfg = C.default_config()
    cfg.update(PHASE_INDEX[phase_id]["overrides"])
    if extra_overrides:
        cfg.update(extra_overrides)
    return C.validate_config(cfg)


def phase_list_payload() -> list:
    """Lightweight phase descriptions for the viewer dropdown."""
    return [{"id": p["id"], "title": p["title"], "desc": p["desc"],
             "focal": p["focal"], "predict": p["predict"]} for p in PHASES]
