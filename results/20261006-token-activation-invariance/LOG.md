The three-arm result does not depend on the activation rule: a check, not evidence.

Round-4 comment C18 asks what happens if a ready actor manifests immediately. For the
token-memory comparison the answer is analytic. In `token_model.py`:

  * transmission and retention draw from `rng`, activation from a separate `arng`;
  * manifestation never feeds back into transmission or retention;
  * runs last exactly `run_length` = 1000 ticks, a multiple of the scheduled
    trigger interval (100), so the scheduled trigger also fires on the final tick;
  * trigger reach is 1 and adoption is reversible.

So the token history is identical under either rule, and final adoption equals the
share of actor-object pairs that are ready at tick 1000 in both. This script confirms
that, replication by replication, for every cell of the three-arm design, and also
confirms that the scheduled arm reproduces the canonical per-rep output exactly.

Exit 0 only if every per-replication adoption value is identical across the two
activation rules and the scheduled values match the canonical raw CSVs.

  python verify_token_activation_invariance.py


{'rule': 'compositional', 'capacity': 6, 'loss_rate': 0.0, 'n': 200, 'return_scheduled': -0.0575, 'return_immediate': -0.0575, 'se_scheduled': 0.006, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'compositional', 'capacity': 6, 'loss_rate': 0.01, 'n': 200, 'return_scheduled': 0.059, 'return_immediate': 0.059, 'se_scheduled': 0.0044, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'compositional', 'capacity': 5, 'loss_rate': 0.0, 'n': 200, 'return_scheduled': -0.0322, 'return_immediate': -0.0322, 'se_scheduled': 0.0052, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'compositional', 'capacity': 5, 'loss_rate': 0.01, 'n': 200, 'return_scheduled': 0.0178, 'return_immediate': 0.0178, 'se_scheduled': 0.0038, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'source', 'capacity': 6, 'loss_rate': 0.0, 'n': 200, 'return_scheduled': 0.0105, 'return_immediate': 0.0105, 'se_scheduled': 0.0083, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'source', 'capacity': 6, 'loss_rate': 0.01, 'n': 200, 'return_scheduled': 0.1852, 'return_immediate': 0.1852, 'se_scheduled': 0.0075, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'source', 'capacity': 5, 'loss_rate': 0.0, 'n': 200, 'return_scheduled': 0.033, 'return_immediate': 0.033, 'se_scheduled': 0.009, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'source', 'capacity': 5, 'loss_rate': 0.01, 'n': 200, 'return_scheduled': 0.1404, 'return_immediate': 0.1404, 'se_scheduled': 0.0086, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'count', 'capacity': 6, 'loss_rate': 0.0, 'n': 200, 'return_scheduled': -0.0088, 'return_immediate': -0.0088, 'se_scheduled': 0.0088, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'count', 'capacity': 6, 'loss_rate': 0.01, 'n': 200, 'return_scheduled': 0.2154, 'return_immediate': 0.2154, 'se_scheduled': 0.0085, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'count', 'capacity': 5, 'loss_rate': 0.0, 'n': 200, 'return_scheduled': 0.0169, 'return_immediate': 0.0169, 'se_scheduled': 0.0101, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}
{'rule': 'count', 'capacity': 5, 'loss_rate': 0.01, 'n': 200, 'return_scheduled': 0.173, 'return_immediate': 0.173, 'se_scheduled': 0.0102, 'max_abs_per_rep_diff': 0.0, 'scheduled_vs_canon_mismatches': 0, 'identical': True}

cells failing: 0 of 12
