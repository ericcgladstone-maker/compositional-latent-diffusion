"""Single source of truth for every model parameter.

NOTHING IS BURIED. Every parameter the model uses -- including the "silent"
low-level ones (transmission probability, eviction rule, scheduling, loss rate,
replications, etc.) -- is declared here once, with:

  - a default value,
  - an exploration range (for numeric params) or choice set (for categorical),
  - the group it belongs to (for organizing the viewer panel),
  - a one-line description.

The live viewer reads this registry to build its slider/control panel.
The sweep runner reads this registry to build parameter grids.
The model reads only validated config dicts produced from this registry.

If a parameter is not in PARAM_SPECS, the model does not know about it.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


@dataclass
class Param:
    name: str
    default: Any
    kind: str  # 'float' | 'int' | 'bool' | 'choice'
    group: str
    doc: str
    low: Optional[float] = None          # numeric exploration range (inclusive)
    high: Optional[float] = None
    step: Optional[float] = None         # suggested slider step
    choices: Optional[List[Any]] = None  # for kind == 'choice'

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "default": self.default,
            "kind": self.kind,
            "group": self.group,
            "doc": self.doc,
            "low": self.low,
            "high": self.high,
            "step": self.step,
            "choices": self.choices,
        }


# ---------------------------------------------------------------------------
# The registry. Order within a group is the display order in the viewer.
# ---------------------------------------------------------------------------
PARAM_SPECS: List[Param] = [
    # --- Structure -----------------------------------------------------------
    Param("n_element_types", 8, "int", "structure",
          "Distinct element types in circulation. Must exceed the union of all "
          "big-thing requirements so competition is real.",
          low=6, high=16, step=1),
    Param("n_big_things", 2, "int", "structure",
          "Number of big things (alpha, beta, ...). 2 creates competition.",
          low=1, high=4, step=1),
    Param("requirement_size", 4, "int", "structure",
          "Size of each big thing's defining element set R.",
          low=3, high=6, step=1),
    Param("sufficiency_k", 3, "int", "structure",
          "Any k-of-R held elements suffice to become a latent adopter "
          "(set-sufficiency encoding). k==R means strict all-of.",
          low=2, high=6, step=1),
    Param("element_overlap", 1, "int", "structure",
          "How many element types two big things share. A shared element is a "
          "common enabler that counts toward both, so more overlap means less "
          "competition. Competition comes from the capacity limit instead, where "
          "an element unique to one big thing takes a slot the other could use.",
          low=0, high=3, step=1),
    Param("requirement_encoding", "set_sufficiency", "choice", "structure",
          "How elements compose into a big thing. set_sufficiency favored, "
          "ordering is an equivalent combinatoric encoding, additive disfavored.",
          choices=["set_sufficiency", "ordering", "additive"]),

    # --- Transmissibility (the theoretical wedge) ----------------------------
    Param("transmissibility_mode", "elements_only", "choice", "transmissibility",
          "Whether a big thing can move whole or only as pieces. elements_only "
          "is our model (big things never transmit whole). whole_package "
          "reproduces ordinary and complex contagion. both allows whole transfer "
          "only between already-equipped agents. whole_package_gated is a "
          "cue-matched twin of whole_package: the assembled element set moves as a "
          "unit, but adoption still waits for the trigger, so it differs from "
          "elements_only only in transmissibility, not in cue-gating.",
          choices=["elements_only", "whole_package", "both", "whole_package_gated"]),
    Param("whole_package_transfer_prob", 1.0, "float", "transmissibility",
          "Probability that an eligible whole-package transfer actually happens "
          "on a contact. At the default of 1.0 a package is delivered whenever it "
          "is eligible, which is the original behaviour. Lowering it lets the "
          "package arm be rate-matched to elements_only: a package carries "
          "requirement_size elements at once while a piecemeal contact carries at "
          "most one element with probability transmission_prob, so the two arms "
          "move very different amounts of material per contact unless this is set "
          "to transmission_prob / requirement_size.",
          low=0.0, high=1.0, step=0.005),

    # --- Network & population ------------------------------------------------
    Param("n_agents", 100, "int", "network",
          "Population size. 100 keeps iteration fast as mechanisms stack.",
          low=50, high=1000, step=50),
    Param("topology", "small_world", "choice", "network",
          "Network structure. small_world is the lead, uniform_mixing only for "
          "SIR-family legibility.",
          choices=["small_world", "ring_lattice", "random", "uniform_mixing"]),
    Param("mean_degree", 6, "int", "network",
          "Target average number of ties per agent (density driver).",
          low=2, high=20, step=1),
    Param("rewire_prob", 0.1, "float", "network",
          "Watts-Strogatz rewiring probability (small_world only).",
          low=0.0, high=1.0, step=0.01),

    # --- Capacity & competition ---------------------------------------------
    Param("capacity", 6, "int", "capacity",
          "Max element-slots an agent can hold. The threshold/capacity ratio "
          "is the competition engine.",
          low=4, high=12, step=1),
    Param("eviction_rule", "random", "choice", "capacity",
          "Who gets dropped when capacity binds. random is the neutral default. "
          "value_weighted (keep elements feeding a near-complete big thing) "
          "implies agents grow attached to near-complete sets, so it is a "
          "hypothesis to test as a named condition, not a default.",
          choices=["random", "recency", "value_weighted"]),
    Param("reversible_adoption", True, "bool", "capacity",
          "If on, a node reverts from adopter to non-adopter when it falls below "
          "the sufficiency threshold (lapsing), so persistence emerges from "
          "stabilization rather than being hard-coded. If off, adoption is "
          "permanent once triggered.",),

    # --- Transmission dynamics ----------------------------------------------
    Param("transmission_prob", 0.10, "float", "dynamics",
          "Probability a held element transmits on a given contact. Low values "
          "lengthen the latent build phase where the interesting inertia lives.",
          low=0.02, high=0.50, step=0.01),
    Param("loss_rate", 0.0, "float", "dynamics",
          "Spontaneous per-tick element forgetting. Off by default so the constrained "
          "dynamics are not confounded.",
          low=0.0, high=0.05, step=0.005),
    Param("contacts_per_tick", 1, "int", "dynamics",
          "Contacts each active agent makes per tick. Sets the clock.",
          low=1, high=5, step=1),
    Param("scheduling", "asynchronous", "choice", "dynamics",
          "asynchronous avoids lockstep-flip artifacts, whereas synchronous updates all "
          "agents at once.",
          choices=["asynchronous", "synchronous"]),
    Param("run_length", 1000, "int", "dynamics",
          "Max ticks. Runs also stop early on quiescence.",
          low=200, high=5000, step=100),
    Param("quiescence_window", 50, "int", "dynamics",
          "Stop early if no element movement for this many ticks (0 disables).",
          low=0, high=500, step=10),

    # --- V2 mechanisms (switchable elaborations) -----------------------------
    Param("differential_slot_cost", False, "bool", "mechanisms",
          "Big ideas occupy 2 slots, elements 1."),
    Param("compression", False, "bool", "mechanisms",
          "On activation, constituent elements collapse into a chunk at smaller "
          "footprint. Frees capacity but can no longer be transmitted as pieces."),
    Param("stabilization", False, "bool", "mechanisms",
          "On activation, constituent elements become harder to dislodge."),
    Param("enhanced_transmission", False, "bool", "mechanisms",
          "On activation, constituent elements become more transmissible to "
          "neighbors (the invisible becomes visible)."),
    Param("stabilization_boost", 0.5, "float", "mechanisms",
          "Strength of the stabilization switch above (only applies when "
          "stabilization is on). Multiplier on loss/eviction pressure for "
          "stabilized elements: 0 makes them immovable, 1 means no protection.",
          low=0.0, high=1.0, step=0.05),
    Param("enhanced_factor", 2.0, "float", "mechanisms",
          "Multiplier on transmission_prob for elements of an active big thing.",
          low=1.0, high=5.0, step=0.1),
    Param("tie_strength_channels", False, "bool", "mechanisms",
          "90/10 weak/strong tie structure, with per-interaction transmission scaling "
          "with tie strength."),
    Param("strong_tie_fraction", 0.10, "float", "mechanisms",
          "Fraction of an agent's ties that are strong (tie_strength_channels).",
          low=0.0, high=0.5, step=0.01),
    Param("internal_coupling", False, "bool", "mechanisms",
          "Lets a big thing you already hold raise or lower your adoption of "
          "other big things (the sign is set by coupling strength)."),
    Param("neighbor_coupling", False, "bool", "mechanisms",
          "Lets a big thing held by your neighbors raise or lower your adoption "
          "of other big things. The same-target case reproduces complex "
          "contagion."),
    Param("coupling_level", "big_thing", "choice", "mechanisms",
          "Does coupling act at the big-thing level or per element.",
          choices=["big_thing", "element"]),
    Param("coupling_strength", 0.0, "float", "mechanisms",
          "Signed coupling multiplier. Negative = antagonism, positive = "
          "facilitation. 0 = off even if a coupling switch is on.",
          low=-1.0, high=1.0, step=0.05),
    Param("member_gated_transmission", False, "bool", "mechanisms",
          "If on, a held element is transmitted only by an agent who is an active "
          "(manifest) member of a big thing that element belongs to, so recruitment "
          "runs through members rather than a shared element pool. Used for the "
          "competitive-ecology test of the recruitment-retention trade-off."),
    Param("incompatibility", False, "bool", "mechanisms",
          "Content-specific exclusivity: when on, big things are mutually exclusive, so "
          "a node can hold at most one manifest at a time and must lapse from one before "
          "adopting another. Distinct from capacity (content-free) and a clean "
          "alternative to driving coupling to its -1 floor."),

    # --- Seeding -------------------------------------------------------------
    Param("seeding_scheme", "uniform_random", "choice", "seeding",
          "Where elements start. clustered manufactures at-risk / resistant "
          "groups on purpose.",
          choices=["uniform_random", "clustered", "single_source"]),
    Param("initial_element_density", 0.15, "float", "seeding",
          "Fraction of (agent, element-type) cells seeded at t=0.",
          low=0.0, high=0.6, step=0.01),
    Param("change_agent_scenario", False, "bool", "seeding",
          "Inject a fully-equipped, manifest minority into an unprepared "
          "population (produces the failed-diffusion signature)."),
    Param("change_agent_fraction", 0.10, "float", "seeding",
          "Share of population seeded fully equipped and manifest.",
          low=0.05, high=0.20, step=0.01),
    Param("change_agent_clustered", False, "bool", "seeding",
          "Place change agents in a cluster (vs dispersed)."),
    Param("change_agent_evangelism", 1.0, "float", "seeding",
          "Multiplier on change agents' transmission probability (1.0 = "
          "baseline, like everyone else).",
          low=1.0, high=5.0, step=0.1),

    # --- Trigger -------------------------------------------------------------
    Param("trigger_type", "exogenous", "choice", "trigger",
          "exogenous = global shock at a set time (mass-media exemplar). "
          "endogenous = fires when enough neighbors are latent/manifest "
          "(focal-point / emergent-need).",
          choices=["exogenous", "endogenous"]),
    Param("trigger_time", 100, "int", "trigger",
          "Tick at which the exogenous trigger fires (and recurs every "
          "trigger_time ticks).",
          low=1, high=2000, step=10),
    Param("endogenous_trigger_threshold", 0.5, "float", "trigger",
          "Fraction of neighbors latent/manifest required to fire manifestation "
          "(endogenous only).",
          low=0.1, high=0.9, step=0.05),
    Param("trigger_reach", 1.0, "float", "trigger",
          "Fraction of latent adopters actually flipped when the trigger fires.",
          low=0.1, high=1.0, step=0.05),

    # --- Run control ---------------------------------------------------------
    Param("seed", 0, "int", "run",
          "Random seed. Fixed seed => fully reproducible run.",
          low=0, high=1_000_000, step=1),
    Param("replications", 30, "int", "run",
          "Replications per parameter cell in a sweep (stochastic averaging). "
          "Ignored by single live runs.",
          low=1, high=100, step=1),
]

# Name -> Param, for fast lookup / validation.
PARAM_INDEX = {p.name: p for p in PARAM_SPECS}

# Display order of groups in the viewer.
GROUP_ORDER = [
    "structure", "transmissibility", "network", "capacity", "dynamics",
    "mechanisms", "seeding", "trigger", "run",
]

GROUP_LABELS = {
    "structure": "Structure",
    "transmissibility": "Transmissibility",
    "network": "Network & population",
    "capacity": "Capacity & competition",
    "dynamics": "Transmission dynamics",
    "mechanisms": "Optional mechanisms",
    "seeding": "Seeding",
    "trigger": "Trigger",
    "run": "Run control",
}


def default_config() -> dict:
    """A fresh dict of every parameter at its default value."""
    return {p.name: p.default for p in PARAM_SPECS}


def validate_config(cfg: dict) -> dict:
    """Return a clean config: defaults filled in, unknown keys dropped,
    numeric kinds coerced, choices/bounds checked. Raises on bad choices."""
    out = default_config()
    for k, v in cfg.items():
        if k not in PARAM_INDEX:
            continue  # silently drop unknowns rather than poison the run
        p = PARAM_INDEX[k]
        if p.kind == "int":
            v = int(round(float(v)))
        elif p.kind == "float":
            v = float(v)
        elif p.kind == "bool":
            v = bool(v) if not isinstance(v, str) else v.lower() in ("1", "true", "yes", "on")
        elif p.kind == "choice":
            if v not in p.choices:
                raise ValueError(f"{k}={v!r} not in {p.choices}")
        out[k] = v
    # Structured (non-scalar) params are carried through untouched. They are not
    # slider-exposed in the registry; they default to absent (None) so every
    # existing run is byte-identical. Used by the per-big-thing endowment
    # (W5 ecology) and the coupling-matrix (W6) conditions.
    for k in ("bigthing_endowments", "coupling_matrix"):
        if cfg.get(k) is not None:
            out[k] = cfg[k]
    return out


def registry_payload() -> dict:
    """JSON-serializable description of the whole registry for the viewer."""
    return {
        "params": [p.to_dict() for p in PARAM_SPECS],
        "group_order": GROUP_ORDER,
        "group_labels": GROUP_LABELS,
    }
