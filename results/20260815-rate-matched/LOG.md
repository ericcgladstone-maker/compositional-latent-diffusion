# Rate-matched transmissibility comparison  (200 reps)  20260815-121059
out: results/20260815-rate-matched
phase V1-W: transmission_prob=0.1, requirement_size=4
a piecemeal contact moves 0.1 elements in expectation, an ungated package contact moves 4, a ratio of 40
rate-matched transfer probability = transmission_prob / requirement_size = 0.025

  elements_only, transmission_prob swept (the piecemeal dose-response curve)
    transmission_prob=0.025  final=0.7409  carriers=0.2589  elem/agent=7.88
    transmission_prob=0.05   final=0.7043  carriers=0.2957  elem/agent=9.20
    transmission_prob=0.1    final=0.6482  carriers=0.3517  elem/agent=10.58  <- operating point
    transmission_prob=0.2    final=0.6048  carriers=0.3952  elem/agent=12.20
    transmission_prob=0.4    final=0.4771  carriers=0.5229  elem/agent=14.68

  whole_package_gated, whole_package_transfer_prob swept
    transfer_prob=1.0    final=0.8557  carriers=0.1443  elem/agent=37.52 (3.55x operating point)  <- original
    transfer_prob=0.5    final=0.8337  carriers=0.1663  elem/agent=23.83 (2.25x operating point)
    transfer_prob=0.25   final=0.7913  carriers=0.2087  elem/agent=18.36 (1.74x operating point)
    transfer_prob=0.1    final=0.7003  carriers=0.2997  elem/agent=14.97 (1.41x operating point)
    transfer_prob=0.05   final=0.6804  carriers=0.3196  elem/agent=13.37 (1.26x operating point)
    transfer_prob=0.025  final=0.6748  carriers=0.3252  elem/agent=12.22 (1.15x operating point)
    transfer_prob=0.01   final=0.6720  carriers=0.3280  elem/agent=11.35 (1.07x operating point)
    transfer_prob=0.005  final=0.6667  carriers=0.3332  elem/agent=11.11 (1.05x operating point)

  whole_package, whole_package_transfer_prob swept
    transfer_prob=1.0    final=0.9942  carriers=0.0058  elem/agent=11.89 (1.12x operating point)  <- original

DONE.
