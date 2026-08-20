# Change agents: robustness to population size and topology  (200 reps)  20260815-115029
out: results/20260815-changeagent-robust
'expected if seed persists' = no-minority adoption plus the seeded share divided by the number of big things, which is what the minority contributes at the first tick before any transmission.
  ring_lattice N=100  permissive   none=0.7040 minority=0.7286 lift=+0.0246   expected-if-seed-persists=0.8040 shortfall=-0.0754   carriers=0.2714
  ring_lattice N=100  constrained  none=0.1541 minority=0.2470 lift=+0.0929   expected-if-seed-persists=0.2541 shortfall=-0.0071   carriers=0.7373
  ring_lattice N=500  permissive   none=0.7109 minority=0.7227 lift=+0.0118   expected-if-seed-persists=0.8109 shortfall=-0.0882   carriers=0.2773
  ring_lattice N=500  constrained  none=0.1337 minority=0.2390 lift=+0.1053   expected-if-seed-persists=0.2337 shortfall=+0.0053   carriers=0.7455

DONE.
