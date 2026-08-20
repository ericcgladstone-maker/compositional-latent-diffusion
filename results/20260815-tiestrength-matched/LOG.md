# Tie strength, dose held constant  (200 reps)  20260815-121101
out: results/20260815-tiestrength-matched
base transmission_prob=0.1; weak tie weight 0.1, strong 1.0
mean send multiplier = 0.1 + 0.9 x fraction, so the as-is sweep raises mean send probability 3.7x across the range
normalised arm rescales transmission_prob by 0.37 / (mean multiplier)

  as-is
    fraction=0.0   transmission_prob=0.1000  final=0.4954  lapse=0.0043  elem/agent=5.04
    fraction=0.05  transmission_prob=0.1000  final=0.5565  lapse=0.0101  elem/agent=5.50
    fraction=0.1   transmission_prob=0.1000  final=0.6135  lapse=0.0181  elem/agent=6.05
    fraction=0.2   transmission_prob=0.1000  final=0.6922  lapse=0.0436  elem/agent=7.44
    fraction=0.3   transmission_prob=0.1000  final=0.7196  lapse=0.0759  elem/agent=8.88
    -> adoption 0.4954 to 0.7196 (+0.2242) while material moved goes 5.04 to 8.88

  normalised
    fraction=0.0   transmission_prob=0.3700  final=0.7210  lapse=0.0872  elem/agent=8.67
    fraction=0.05  transmission_prob=0.2552  final=0.7280  lapse=0.0777  elem/agent=8.83
    fraction=0.1   transmission_prob=0.1947  final=0.7291  lapse=0.0726  elem/agent=8.75
    fraction=0.2   transmission_prob=0.1321  final=0.7216  lapse=0.0713  elem/agent=8.69
    fraction=0.3   transmission_prob=0.1000  final=0.7196  lapse=0.0759  elem/agent=8.88
    -> adoption 0.7210 to 0.7196 (-0.0014) while material moved goes 8.67 to 8.88

DONE.
