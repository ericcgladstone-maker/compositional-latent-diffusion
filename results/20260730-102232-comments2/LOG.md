# New-mechanism analyses (200 reps)  20260730-102232
out: results/20260730-102232-comments2

## W7  cue-gated whole-package (V1-W base; pre-trigger adoption vs final)
  elements_only        final=0.6482 pre_trigger=0.0 overshoot=0.1355 lapse=0.2478 gap=0.1004
  whole_package        final=0.9942 pre_trigger=0.0 overshoot=0.0058 lapse=0.5447 gap=-0.1742
  whole_package_gated  final=0.8557 pre_trigger=0.0 overshoot=0.0646 lapse=0.183 gap=-0.0057
  both                 final=0.9949 pre_trigger=0.0 overshoot=0.0042 lapse=0.565 gap=-0.1719
  DECOMPOSITION of the adoption gap (all modes bootstrap at the trigger; pre_trigger=0):
    elements_only 0.6482 -> whole_package_gated 0.8557  = pure transmissibility (+0.2075)
    whole_package_gated 0.8557 -> whole_package 0.9942  = cue-gating / adopt-on-contact (+0.1385)

## W6  coupling matrix (V2-neighbor-coupling base; two effects separated)
  (a) OFF-DIAGONAL sweep = cross-target only (diagonal 0):
    off_diag=-1.0: final=0.5165 lapse=0.081
    off_diag=-0.5: final=0.5943 lapse=0.182
    off_diag=+0.0: final=0.6482 lapse=0.248
    off_diag=+0.5: final=0.6737 lapse=0.279
    off_diag=+1.0: final=0.6949 lapse=0.298
  (b) DIAGONAL sweep = same-target / complex contagion only (off-diagonal 0):
    diag=+0.00: final=0.6482 lapse=0.248
    diag=+0.25: final=0.6795 lapse=0.257
    diag=+0.50: final=0.6778 lapse=0.269
    diag=+1.00: final=0.69 lapse=0.275
  (c) VALIDATION: matrix [[|x|,x],[x,|x|]] should reproduce scalar coupling_strength=x
    x=-1.0: matrix=0.6056 scalar=0.8871 (match => matrix generalizes the scalar's diag=|off-diag| slice)
    x=-0.5: matrix=0.6396 scalar=0.8471 (match => matrix generalizes the scalar's diag=|off-diag| slice)
    x=+0.5: matrix=0.6764 scalar=0.5625 (match => matrix generalizes the scalar's diag=|off-diag| slice)
    x=+1.0: matrix=0.7601 scalar=0.5553 (match => matrix generalizes the scalar's diag=|off-diag| slice)

## W4  overlap -> porousness/leakage (insular manifest-alpha cluster; defect to beta)
  overlap=0: insular_leakage_to_beta=0.6717 outside_beta_adoption=0.6424
  overlap=1: insular_leakage_to_beta=0.7335 outside_beta_adoption=0.6433
  overlap=2: insular_leakage_to_beta=0.786 outside_beta_adoption=0.6564
  overlap=3: insular_leakage_to_beta=0.8257 outside_beta_adoption=0.6744

## W5  competitive ecology: graded compression (encapsulation) of alpha vs beta
     (V1 + incompatibility; measure alpha's captured share vs its compression rate)
  beta_p=0.2: a0.0=0.407  a0.2=0.46  a0.4=0.552  a0.6=0.634  a0.8=0.692  a1.0=0.738   <- alpha best at compression=1.0 (share 0.738)
  beta_p=0.5: a0.0=0.323  a0.2=0.407  a0.4=0.496  a0.6=0.567  a0.8=0.632  a1.0=0.688   <- alpha best at compression=1.0 (share 0.688)
  beta_p=0.8: a0.0=0.215  a0.2=0.332  a0.4=0.432  a0.6=0.515  a0.8=0.581  a1.0=0.634   <- alpha best at compression=1.0 (share 0.634)

DONE.
