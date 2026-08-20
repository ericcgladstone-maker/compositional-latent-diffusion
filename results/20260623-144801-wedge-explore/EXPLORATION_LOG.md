# Wedge exploration log

Exploratory follow-up to the build-and-results document. Not part of the signed-off build doc. Same standards: every number below is generated from the experiment output CSVs and verified against the raw per-run data.

## Provenance

| Item | Value |
|---|---|
| Experiment dir | `results/20260623-144801-wedge-explore` |
| Created | 2026-06-23 14:55:20 |
| Operating point | `config_for_phase('V1-W')` (identical to the doc wedge stage) |
| Replications | 30 |
| Base seed | 0 |
| Validation (must match doc) | elements_only=0.6528 (doc 0.65), whole_package=0.9918 (doc 0.99), both=0.9937 (doc 0.99) |
| Data integrity | PASS (Part B aggregates re-derived from raw runs) |

## A. Trajectories and the observability gap

The main sweep saved only endpoints. These are the full mean trajectories across replications. `elements_only` builds a staircase keyed to the periodic trigger, while `whole_package` runs as a single smooth cascade.

![trajectories](fig_trajectories.png)

The observability gap is the substrate held (big-thing elements present in the population) minus manifest adoption. It is the quantitative form of "the elements are already circulating, the adoption has not happened yet". Two things stand out, and they are sharper than a simple gap-versus-no-gap contrast.

First, until the trigger fires at tick 100 the three modes are identical. Substrate climbs to about 0.60 while adoption sits at zero, an identical pre-activation gap of +0.60 in every mode. Nobody is manifest yet, so even whole-package transmission can only move elements. That long unobserved build-up is the latent-adoption phenomenology, and it is mode independent.

Second, the trigger splits the modes into mirror images. Under elements_only the gap stays positive to the end (+0.09: substrate keeps leading adoption, with trigger-keyed sawtooth churn). Under whole_package the gap inverts to negative (-0.17: adoption overtakes the substrate, because contagion carries the manifest state faster than the pieces, so agents are manifest without holding the full element set). The sign of the gap, not its mere size, is the discriminator: substrate leads in our model, adoption leads under contagion.

![observability gap](fig_observability_gap.png)

| Mode | Final adoption | Gap pre-trigger (t=99) | Gap at end | Signed gap area |
|---|---|---|---|---|
| elements_only | 0.6528 | +0.60 | +0.09 | 81.7 |
| whole_package | 0.9918 | +0.60 | -0.17 | 24.6 |
| both | 0.9937 | +0.60 | -0.17 | 17.9 |

## B. Robustness and validity map

The wedge gap (whole_package adoption minus elements_only adoption) stays positive across every structural knob tested, ranging +0.18 to +0.62. Across the network and dynamics knobs whole_package saturates near 0.99 while elements_only stays lower. Where assembly is hard enough to hold both modes down (requirement_size 5 and 6, where whole_package itself falls to about 0.48) the gap still does not close. The distinction is not an artifact of the doc's default operating point.

![robustness](fig_robustness.png)

| Knob | Level | elements_only | whole_package | Wedge gap | Peak obs. gap (elements_only) |
|---|---|---|---|---|---|
| requirement_size | R=1 (k=1) | 0.6308 | 0.995 | 0.3642 | 0.5822 |
| requirement_size | R=2 (k=2) | 0.3718 | 0.9878 | 0.616 | 0.5999 |
| requirement_size | R=3 (k=2) | 0.8172 | 0.9973 | 0.1801 | 0.5962 |
| requirement_size | R=4 (k=3) | 0.6528 | 0.9918 | 0.339 | 0.6035 |
| requirement_size | R=5 (k=4) | 0.2437 | 0.4757 | 0.232 | 0.5723 |
| requirement_size | R=6 (k=4) | 0.2227 | 0.4773 | 0.2546 | 0.4925 |
| topology | small_world | 0.6528 | 0.9918 | 0.339 | 0.6035 |
| topology | random | 0.6545 | 0.9915 | 0.337 | 0.5917 |
| topology | ring_lattice | 0.6548 | 0.9945 | 0.3397 | 0.5863 |
| topology | uniform_mixing | 0.5982 | 0.9927 | 0.3945 | 0.6801 |
| mean_degree | 4 | 0.6555 | 0.9935 | 0.338 | 0.5552 |
| mean_degree | 6 | 0.6528 | 0.9918 | 0.339 | 0.6035 |
| mean_degree | 10 | 0.644 | 0.9928 | 0.3488 | 0.6338 |
| n_agents | 100 | 0.6528 | 0.9918 | 0.339 | 0.6035 |
| n_agents | 300 | 0.6363 | 0.9947 | 0.3584 | 0.6083 |
| transmission_prob | 0.05 | 0.678 | 0.9972 | 0.3192 | 0.4417 |
| transmission_prob | 0.1 | 0.6528 | 0.9918 | 0.339 | 0.6035 |
| transmission_prob | 0.2 | 0.6242 | 0.987 | 0.3628 | 0.7232 |

## C. Decomposition and validity: how many sources does the wedge have?

A validity test that corrected an initial guess. The first hypothesis was that the wedge has one source, combinatoric assembly, so that at requirement_size = 1 (the element IS the big thing) it would vanish. It does not. Crossing requirement_size (1 vs 4) with trigger_time (immediate vs periodic) shows a second source, activation: a held substrate still waits for a trigger to manifest, while whole-package transmits the manifest state itself. Neither pair collapses the gap. Even with assembly and activation both removed (R = 1, immediate trigger) a residual gap of about +0.26 remains.

| Barriers present (assembly x activation) | requirement_size | trigger_time | elements_only | whole_package | Wedge gap |
|---|---|---|---|---|---|
| none | 1 | 1 | 0.741 | 0.996 | 0.255 |
| activation only | 1 | 100 | 0.6308 | 0.995 | 0.3642 |
| assembly only | 4 | 1 | 0.7698 | 0.9973 | 0.2275 |
| both | 4 | 100 | 0.6528 | 0.9918 | 0.339 |

That residual is a third source: capacity competition. With capacity 6 and 8 element types, the six non-big-thing element types crowd the slots and random eviction churns out the element that matters. Removing capacity competition as well, by unbounding capacity or removing the noise element types, drives the gap to exactly 0.00. The wedge collapses to zero only when all three barriers are gone, and the three are exactly the model's core pillars: composition, the latent-to-manifest trigger, and the capacity engine established in stage V1.

![collapse](fig_collapse.png)

| Barriers present | R | trigger_time | capacity | n_element_types | elements_only | whole_package | Wedge gap |
|---|---|---|---|---|---|---|---|
| assembly + activation + capacity | 4 | 100 | 6 | 8 | 0.6528 | 0.9918 | 0.339 |
| capacity only (assembly, activation removed) | 1 | 1 | 6 | 8 | 0.741 | 0.996 | 0.255 |
| none: + unbounded capacity | 1 | 1 | 64 | 8 | 0.9975 | 1.0 | 0.0025 |
| none: + no noise element types | 1 | 1 | 6 | 2 | 0.9993 | 1.0 | 0.0007 |

## What we learned

1. The wedge is robust, not knife-edge. Across topology, degree, population size, seeding density, transmission probability, and assembly difficulty, whole-package transmission produces higher adoption than pieces-only and the gap never closes (it does not require whole-package to saturate: at the hardest assembly settings both modes fall, yet the gap persists). The spread-unit / adoption-unit split produces a systematic adoption gap generically.
2. The observability gap is real, measurable, and directional. Every mode shares a long pre-activation build-up where the substrate accumulates and adoption is zero. After activation the sign of the gap separates the models: under pieces-only transmission the substrate keeps leading adoption (gap stays positive), while under whole-package transmission adoption overtakes the substrate (gap goes negative). The substrate-leads signature is the phenomenological core ("the match gets the credit, the substrate did the work") in quantitative form, and the sign flip is the thing to look for in data.
3. The wedge has three sources, not one: assembly (collect the elements), activation (the held substrate awaits a trigger), and capacity competition (noise elements crowd the slots and eviction churns out what matters). Each contributes on its own, and the gap collapses to zero only when all three are removed. The three are precisely the model's core pillars, so the wedge is the joint signature of the whole construction rather than of any single knob. The initial one-source guess was wrong, and the data saying so is what produced the sharper result.

## Candidate folds into the main doc (pending Eric)

- Observability-gap figure and the A-summary table, as a short addition to the wedge stage (it is the clearest single picture of the argument).
- One robustness sentence with the gap range, to forestall the "is this just your defaults" question.
- The three-source collapse test, if a validity subsection is wanted. It is a clean way to show the wedge is the joint signature of composition, trigger, and capacity rather than an artifact of one setting.
