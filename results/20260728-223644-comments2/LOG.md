# New-mechanism analyses (30 reps)  20260728-223644
out: results/20260728-223644-comments2

## W7  cue-gated whole-package (V1-W base; pre-trigger adoption vs final)
  elements_only        final=0.6528 pre_trigger=0.0 overshoot=0.1287 lapse=0.2436 gap=0.0943
  whole_package        final=0.9918 pre_trigger=0.0 overshoot=0.0082 lapse=0.5735 gap=-0.1739
  whole_package_gated  final=0.8902 pre_trigger=0.0 overshoot=0.0605 lapse=0.2019 gap=-0.0405
  both                 final=0.9937 pre_trigger=0.0 overshoot=0.0052 lapse=0.617 gap=-0.1716
  DECOMPOSITION of the adoption gap (all modes bootstrap at the trigger; pre_trigger=0):
    elements_only 0.6528 -> whole_package_gated 0.8902  = pure transmissibility (+0.2374)
    whole_package_gated 0.8902 -> whole_package 0.9918  = cue-gating / adopt-on-contact (+0.1016)

## W6  coupling matrix (V2-neighbor-coupling base; two effects separated)
  (a) OFF-DIAGONAL sweep = cross-target only (diagonal 0):
    off_diag=-1.0: final=0.5148 lapse=0.081
    off_diag=-0.5: final=0.5993 lapse=0.178
    off_diag=+0.0: final=0.6528 lapse=0.244
    off_diag=+0.5: final=0.6257 lapse=0.288
    off_diag=+1.0: final=0.7182 lapse=0.296
  (b) DIAGONAL sweep = same-target / complex contagion only (off-diagonal 0):
    diag=+0.00: final=0.6528 lapse=0.244
    diag=+0.25: final=0.6688 lapse=0.26
    diag=+0.50: final=0.675 lapse=0.266
    diag=+1.00: final=0.6692 lapse=0.287
  (c) VALIDATION: matrix [[|x|,x],[x,|x|]] should reproduce scalar coupling_strength=x
    x=-1.0: matrix=0.602 scalar=0.8667 (match => matrix generalizes the scalar's diag=|off-diag| slice)
    x=-0.5: matrix=0.6263 scalar=0.8467 (match => matrix generalizes the scalar's diag=|off-diag| slice)
    x=+0.5: matrix=0.6602 scalar=0.563 (match => matrix generalizes the scalar's diag=|off-diag| slice)
    x=+1.0: matrix=0.7488 scalar=0.5543 (match => matrix generalizes the scalar's diag=|off-diag| slice)

## W4  overlap -> porousness/leakage (insular manifest-alpha cluster; defect to beta)
  overlap=0: insular_leakage_to_beta=0.675 outside_beta_adoption=0.6562
  overlap=1: insular_leakage_to_beta=0.77 outside_beta_adoption=0.6533
  overlap=2: insular_leakage_to_beta=0.7633 outside_beta_adoption=0.6362
  overlap=3: insular_leakage_to_beta=0.825 outside_beta_adoption=0.66

## W5  competitive ecology: graded compression (encapsulation) of alpha vs beta
     (V1 + incompatibility; measure alpha's captured share vs its compression rate)
  beta_p=0.2: a0.0=0.397  a0.2=0.465  a0.4=0.519  a0.6=0.652  a0.8=0.663  a1.0=0.739   <- alpha best at compression=1.0 (share 0.739)
  beta_p=0.5: a0.0=0.315  a0.2=0.4  a0.4=0.486  a0.6=0.555  a0.8=0.612  a1.0=0.666   <- alpha best at compression=1.0 (share 0.666)
  beta_p=0.8: a0.0=0.232  a0.2=0.329  a0.4=0.406  a0.6=0.492  a0.8=0.551  a1.0=0.605   <- alpha best at compression=1.0 (share 0.605)

DONE.
