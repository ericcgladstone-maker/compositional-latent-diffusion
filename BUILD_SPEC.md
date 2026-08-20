# Build specification — latent-adoption ABM

_Generated from code by `gen_spec.py`. Regenerate after any change. This reflects what the simulation **actually** implements._

## 1. Parameters (43 total)

### Structure

| parameter | type | default | range / choices | description |
|---|---|---|---|---|
| `n_element_types` | int | 8 | 6 – 16 (step 1) | Distinct element types in circulation. Must exceed the union of all big-thing requirements so competition is real. |
| `n_big_things` | int | 2 | 1 – 4 (step 1) | Number of big things (alpha, beta, ...). 2 creates competition. |
| `requirement_size` | int | 4 | 3 – 6 (step 1) | Size of each big thing's defining element set R. |
| `sufficiency_k` | int | 3 | 2 – 6 (step 1) | Any k-of-R held elements suffice to become a latent adopter (set-sufficiency encoding). k==R means strict all-of. |
| `element_overlap` | int | 1 | 0 – 3 (step 1) | How many element types two adjacent big things share. >0 makes big things compete for the same elements. |
| `requirement_encoding` | choice | set_sufficiency | set_sufficiency \| ordering \| additive | How elements compose into a big thing. set_sufficiency favored; ordering is an equivalent combinatoric encoding; additive disfavored. |

### Transmissibility (the wedge)

| parameter | type | default | range / choices | description |
|---|---|---|---|---|
| `transmissibility_mode` | choice | elements_only | elements_only \| whole_package \| both | THE WEDGE. elements_only = our model (big things never transmit whole). whole_package = recovers SIR / complex contagion in-model. both = whole only between compression-equipped agents. |

### Network & population

| parameter | type | default | range / choices | description |
|---|---|---|---|---|
| `n_agents` | int | 100 | 50 – 1000 (step 50) | Population size. 100 keeps iteration fast as mechanisms stack. |
| `topology` | choice | small_world | small_world \| ring_lattice \| random \| uniform_mixing | Network structure. small_world is the lead; uniform_mixing only for SIR-family legibility. |
| `mean_degree` | int | 6 | 2 – 20 (step 1) | Target average number of ties per agent (density driver). |
| `rewire_prob` | float | 0.1 | 0 – 1 (step 0.01) | Watts-Strogatz rewiring probability (small_world only). |

### Capacity & competition

| parameter | type | default | range / choices | description |
|---|---|---|---|---|
| `capacity` | int | 6 | 4 – 12 (step 1) | Max element-slots an agent can hold. The threshold/capacity ratio is the competition engine. |
| `eviction_rule` | choice | value_weighted | random \| recency \| value_weighted | Who gets dropped when capacity binds. value_weighted (keep elements feeding a near-complete big thing) is the substantively richest. |

### Transmission dynamics

| parameter | type | default | range / choices | description |
|---|---|---|---|---|
| `transmission_prob` | float | 0.1 | 0.02 – 0.5 (step 0.01) | Probability a held element transmits on a given contact. Low values lengthen the latent build phase where the interesting inertia lives. |
| `loss_rate` | float | 0 | 0 – 0.05 (step 0.005) | Spontaneous per-tick element forgetting. Off by default so V1 dynamics are not confounded. |
| `contacts_per_tick` | int | 1 | 1 – 5 (step 1) | Contacts each active agent makes per tick. Sets the clock. |
| `scheduling` | choice | asynchronous | asynchronous \| synchronous | asynchronous avoids lockstep-flip artifacts; synchronous updates all agents at once. |
| `run_length` | int | 1000 | 200 – 5000 (step 100) | Max ticks. Runs also stop early on quiescence. |
| `quiescence_window` | int | 50 | 0 – 500 (step 10) | Stop early if no element movement for this many ticks (0 disables). |

### V2 mechanisms

| parameter | type | default | range / choices | description |
|---|---|---|---|---|
| `differential_slot_cost` | bool | False | false \| true | Big ideas occupy 2 slots, elements 1. |
| `compression` | bool | False | false \| true | On activation, constituent elements collapse into a chunk at smaller footprint; frees capacity but can no longer be transmitted as pieces. |
| `stabilization` | bool | False | false \| true | On activation, constituent elements become harder to dislodge. |
| `enhanced_transmission` | bool | False | false \| true | On activation, constituent elements become more transmissible to neighbors (the invisible becomes visible). |
| `stabilization_boost` | float | 0.5 | 0 – 1 (step 0.05) | Multiplier reducing loss/eviction pressure on stabilized elements (0 = immovable, 1 = no effect). |
| `enhanced_factor` | float | 2 | 1 – 5 (step 0.1) | Multiplier on transmission_prob for elements of an active big thing. |
| `tie_strength_channels` | bool | False | false \| true | 90/10 weak/strong tie structure; per-interaction transmission scales with tie strength. |
| `strong_tie_fraction` | float | 0.1 | 0 – 0.5 (step 0.01) | Fraction of an agent's ties that are strong (tie_strength_channels). |
| `internal_coupling` | bool | False | false \| true | EXTENSION. Signed coupling: a held big thing biases adoption / element-retention of OTHER big things (off-diagonal). |
| `neighbor_coupling` | bool | False | false \| true | EXTENSION. Same signed structure sourced externally: a neighbor's big thing biases your adoption of others. Subsumes complex contagion as the positive same-target cell. |
| `coupling_level` | choice | big_thing | big_thing \| element | Does coupling act at the big-thing level or per element. |
| `coupling_strength` | float | 0 | -1 – 1 (step 0.05) | Signed coupling multiplier. Negative = antagonism, positive = facilitation. 0 = off even if a coupling switch is on. |

### Seeding

| parameter | type | default | range / choices | description |
|---|---|---|---|---|
| `seeding_scheme` | choice | uniform_random | uniform_random \| clustered \| single_source | Where elements start. clustered manufactures at-risk / resistant groups on purpose. |
| `initial_element_density` | float | 0.15 | 0 – 0.6 (step 0.01) | Fraction of (agent, element-type) cells seeded at t=0. |
| `change_agent_scenario` | bool | False | false \| true | Inject a fully-equipped, manifest minority into an unprepared population (produces the failed-diffusion signature). |
| `change_agent_fraction` | float | 0.1 | 0.05 – 0.2 (step 0.01) | Share of population seeded fully equipped and manifest. |
| `change_agent_clustered` | bool | False | false \| true | Place change agents in a cluster (vs dispersed). |
| `change_agent_evangelism` | float | 1 | 1 – 5 (step 0.1) | Multiplier on change agents' transmission probability (1.0 = baseline, like everyone else). |

### Trigger

| parameter | type | default | range / choices | description |
|---|---|---|---|---|
| `trigger_type` | choice | exogenous | exogenous \| endogenous | exogenous = global shock at a set time (mass-media exemplar). endogenous = fires when enough neighbors are latent/manifest (focal-point / emergent-need). |
| `trigger_time` | int | 100 | 1 – 2000 (step 10) | Tick at which the exogenous trigger fires (and recurs every trigger_time ticks). |
| `endogenous_trigger_threshold` | float | 0.5 | 0.1 – 0.9 (step 0.05) | Fraction of neighbors latent/manifest required to fire manifestation (endogenous only). |
| `trigger_reach` | float | 1 | 0.1 – 1 (step 0.05) | Fraction of latent adopters actually flipped when the trigger fires. |

### Run control

| parameter | type | default | range / choices | description |
|---|---|---|---|---|
| `seed` | int | 0 | 0 – 1000000 (step 1) | Random seed. Fixed seed => fully reproducible run. |
| `replications` | int | 30 | 1 – 100 (step 1) | Replications per parameter cell in a sweep (stochastic averaging). Ignored by single live runs. |

## 2. Switchable conditions (categorical manipulations)

| switch | options |
|---|---|
| `requirement_encoding` | set_sufficiency \| ordering \| additive |
| `transmissibility_mode` | elements_only \| whole_package \| both |
| `topology` | small_world \| ring_lattice \| random \| uniform_mixing |
| `eviction_rule` | random \| recency \| value_weighted |
| `scheduling` | asynchronous \| synchronous |
| `coupling_level` | big_thing \| element |
| `seeding_scheme` | uniform_random \| clustered \| single_source |
| `trigger_type` | exogenous \| endogenous |

## 3. V2 mechanism switches (boolean) and associated strengths

| mechanism (bool) | default | strength parameter(s) |
|---|---|---|
| `differential_slot_cost` | False | (chunk costs 2 slots when on) |
| `compression` | False | — |
| `stabilization` | False | `stabilization_boost` |
| `enhanced_transmission` | False | `enhanced_factor` |
| `tie_strength_channels` | False | `strong_tie_fraction` |
| `internal_coupling` | False | `coupling_strength`, `coupling_level` |
| `neighbor_coupling` | False | `coupling_strength`, `coupling_level` |

## 4. Build phases / experimental conditions (12)

| phase id | focal sweep | focal values | predicted |
|---|---|---|---|
| `V0` | `initial_element_density` | 0.05, 0.1, 0.15, 0.2 | Everyone acquires everything; all big things activate. |
| `V1` | `capacity` | 4, 5, 6, 7, 8, 10 | Hilly terrain; no universal saturation. |
| `V1-W` | `transmissibility_mode` | elements_only, whole_package, both | whole_package recovers SIR/complex contagion; elements_only gives latent adoption (long inertia then sudden manifestation). |
| `V2-slotcost` | `capacity` | 4, 6, 8, 10 | Tighter capacity pressure than V1. |
| `V2-compression` | `transmission_prob` | 0.05, 0.1, 0.2, 0.3 | Frees capacity; reduces downstream transmissibility. |
| `V2-stabilization` | `stabilization_boost` | 0, 0.25, 0.5, 0.75, 1 | Entrenched adoption; reservoirs persist. |
| `V2-enhanced` | `enhanced_factor` | 1, 1.5, 2, 3 | Faster secondary spread once a pocket flips. |
| `V2-stab-enh` | `enhanced_factor` | 1, 2, 3 | Compounding or offsetting of the two mechanisms. |
| `V2-tiestrength` | `strong_tie_fraction` | 0, 0.05, 0.1, 0.2, 0.3 | Latent preparation as a predominantly weak-tie phenomenon. |
| `V2-internal-coupling` | `coupling_strength` | -1, -0.5, 0, 0.5, 1 | Correlated bundles instead of generic crowding. |
| `V2-neighbor-coupling` | `coupling_strength` | -1, -0.5, 0, 0.5, 1 | Social-pressure suppression / facilitation across big things. |
| `change-agent` | `change_agent_fraction` | 0.05, 0.1, 0.15, 0.2 | Fails to spread under elements_only despite full equipment. |

### Per-phase overrides (relative to registry defaults)

| phase id | overrides applied |
|---|---|
| `V0` | `capacity=64`, `trigger_type=exogenous`, `trigger_time=1`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=False`, `compression=False`, `stabilization=False`, `enhanced_transmission=False`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `V1` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=False`, `compression=False`, `stabilization=False`, `enhanced_transmission=False`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `V1-W` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=False`, `compression=False`, `stabilization=False`, `enhanced_transmission=False`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `V2-slotcost` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=True`, `compression=True`, `stabilization=False`, `enhanced_transmission=False`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `V2-compression` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=False`, `compression=True`, `stabilization=False`, `enhanced_transmission=False`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `V2-stabilization` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0.01`, `differential_slot_cost=False`, `compression=False`, `stabilization=True`, `enhanced_transmission=False`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=False`, `transmissibility_mode=elements_only`, `eviction_rule=random` |
| `V2-enhanced` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=False`, `compression=False`, `stabilization=False`, `enhanced_transmission=True`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `V2-stab-enh` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0.01`, `differential_slot_cost=False`, `compression=False`, `stabilization=True`, `enhanced_transmission=True`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `V2-tiestrength` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=False`, `compression=False`, `stabilization=False`, `enhanced_transmission=False`, `tie_strength_channels=True`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `V2-internal-coupling` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=False`, `compression=False`, `stabilization=False`, `enhanced_transmission=False`, `tie_strength_channels=False`, `internal_coupling=True`, `neighbor_coupling=False`, `coupling_strength=-0.5`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `V2-neighbor-coupling` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=False`, `compression=False`, `stabilization=False`, `enhanced_transmission=False`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=True`, `coupling_strength=-0.5`, `change_agent_scenario=False`, `transmissibility_mode=elements_only` |
| `change-agent` | `capacity=6`, `trigger_type=exogenous`, `trigger_time=100`, `trigger_reach=1`, `loss_rate=0`, `differential_slot_cost=False`, `compression=False`, `stabilization=False`, `enhanced_transmission=False`, `tie_strength_channels=False`, `internal_coupling=False`, `neighbor_coupling=False`, `coupling_strength=0`, `change_agent_scenario=True`, `transmissibility_mode=elements_only`, `initial_element_density=0.05` |

## 5. Outcome measures (dependent variables)

### Per-tick metrics (logged every step)

| metric | note |
|---|---|
| `t` | tick |
| `element_saturation` | mean fraction of all element-slots filled |
| `bigthing_element_saturation` | mean fraction of big-thing elements held |
| `manifest_share` | fraction of (agent × big-thing) cells manifest |
| `observability_gap` | bigthing_element_saturation − manifest_share |
| `per_big[label]` | per big thing: `manifest`, `latent`, `at_risk`, `resistant`, `variants` |

### Per-run signatures (one row per replication in `summary.csv`)

| signature | note |
|---|---|
| `ticks_run` | ticks until quiescence or run_length |
| `final_element_saturation` |  |
| `final_bigthing_element_saturation` |  |
| `final_manifest_share` |  |
| `final_observability_gap` |  |
| `alpha_manifest` |  |
| `alpha_latent` |  |
| `alpha_at_risk` |  |
| `alpha_resistant` |  |
| `alpha_n_variants` |  |
| `beta_manifest` |  |
| `beta_latent` |  |
| `beta_at_risk` |  |
| `beta_resistant` |  |
| `beta_n_variants` |  |
| `time_to_first_manifest` | first tick with any manifestation |
| `max_single_tick_jump` | largest one-tick rise in manifest share (plateau-then-jump) |
| `max_jump_tick` | when that jump occurred |
| `time_to_half_cascade` | tick reaching 50% of final adoption |
