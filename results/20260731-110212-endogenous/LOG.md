# Endogenous versus exogenous triggering  (3 reps)  20260731-110212
out: results/20260731-110212-endogenous
endogenous: an agent flips when the share of its neighbours latent or manifest for that big thing reaches endogenous_trigger_threshold. No clock.

## E1/E3  trajectory shape and observability gap, by trigger type and mode
   onset = first tick adoption reaches a tenth of its final level
  exogenous/elements_only            final=0.6983  onset=100 (sd 0.0)  rise=100  substrate@onset=0.5948  final_gap=+0.0521
  endogenous/elements_only           final=0.7550  onset=52.3333 (sd 3.7712)  rise=148.3333  substrate@onset=0.4414  final_gap=-0.0117
  exogenous/whole_package_gated      final=0.8733  onset=100 (sd 0.0)  rise=100  substrate@onset=0.5948  final_gap=-0.0271
  endogenous/whole_package_gated     final=0.9983  onset=42.6667 (sd 2.8674)  rise=19  substrate@onset=0.4514  final_gap=-0.1655
  exogenous/whole_package            final=0.9900  onset=100 (sd 0.0)  rise=4  substrate@onset=0.5948  final_gap=-0.1743
  endogenous/whole_package           final=0.9933  onset=38 (sd 5.8878)  rise=9.3333  substrate@onset=0.431  final_gap=-0.1600

   ONSET SPREAD (the decisive number: zero under a clock)
     exogenous   elements_only        onset sd = 0.0
     endogenous  elements_only        onset sd = 3.7712
     exogenous   whole_package_gated  onset sd = 0.0
     endogenous  whole_package_gated  onset sd = 2.8674
     exogenous   whole_package        onset sd = 0.0
     endogenous  whole_package        onset sd = 5.8878

## E2  capacity transition under each trigger type
  exogenous   cap4=0.1417  cap5=0.2417  cap6=0.6983  cap7=0.9967  cap8=1.0000  cap10=1.0000
  endogenous  cap4=0.1250  cap5=0.4583  cap6=0.7550  cap7=0.9967  cap8=1.0000  cap10=1.0000

## E4  sensitivity to the endogenous threshold (elements_only)
  threshold=0.3: final=0.7600  onset=45.3333 (sd 1.2472)  rise=128.3333  final_gap=-0.0138
  threshold=0.5: final=0.7550  onset=52.3333 (sd 3.7712)  rise=148.3333  final_gap=-0.0117
  threshold=0.7: final=0.6933  onset=65.3333 (sd 5.9067)  rise=181.3333  final_gap=+0.0557

## mean trajectories (for the figure): adoption and substrate over time
  exogenous/elements_only: 347 ticks averaged over 3 runs
  endogenous/elements_only: 396 ticks averaged over 3 runs

DONE.
