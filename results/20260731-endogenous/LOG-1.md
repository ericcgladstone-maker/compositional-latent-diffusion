# Endogenous versus exogenous triggering  (200 reps)  20260731-110415
out: results/20260731-endogenous
endogenous: an agent flips when the share of its neighbours latent or manifest for that big thing reaches endogenous_trigger_threshold. No clock.

## E1/E3  trajectory shape and observability gap, by trigger type and mode
   onset = first tick adoption reaches a tenth of its final level
  exogenous/elements_only            final=0.6482  onset=100 (sd 0.0)  rise=83.5  substrate@onset=0.6107  final_gap=+0.1004
  endogenous/elements_only           final=0.7785  onset=53.255 (sd 9.0261)  rise=138.295  substrate@onset=0.4628  final_gap=-0.0282
  exogenous/whole_package_gated      final=0.8557  onset=100 (sd 0.0)  rise=93.5  substrate@onset=0.6107  final_gap=-0.0057
  endogenous/whole_package_gated     final=0.9965  onset=37.055 (sd 7.9052)  rise=20.58  substrate@onset=0.4448  final_gap=-0.1582
  exogenous/whole_package            final=0.9942  onset=100 (sd 0.0)  rise=4.155  substrate@onset=0.6107  final_gap=-0.1742
  endogenous/whole_package           final=0.9957  onset=32.34 (sd 8.581)  rise=11.645  substrate@onset=0.4254  final_gap=-0.1618

   ONSET SPREAD (the decisive number: zero under a clock)
     exogenous   elements_only        onset sd = 0.0
     endogenous  elements_only        onset sd = 9.0261
     exogenous   whole_package_gated  onset sd = 0.0
     endogenous  whole_package_gated  onset sd = 7.9052
     exogenous   whole_package        onset sd = 0.0
     endogenous  whole_package        onset sd = 8.581

## E2  capacity transition under each trigger type

## E4  sensitivity to the endogenous threshold (elements_only)

## mean trajectories (for the figure): adoption and substrate over time

DONE.
