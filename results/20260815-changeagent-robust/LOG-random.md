# Change agents: robustness to population size and topology  (200 reps)  20260815-115028
out: results/20260815-changeagent-robust
'expected if seed persists' = no-minority adoption plus the seeded share divided by the number of big things, which is what the minority contributes at the first tick before any transmission.
  random       N=100  permissive   none=0.6493 minority=0.6595 lift=+0.0102   expected-if-seed-persists=0.7493 shortfall=-0.0898   carriers=0.3382
  random       N=100  constrained  none=0.1133 minority=0.1493 lift=+0.0360   expected-if-seed-persists=0.2133 shortfall=-0.0640   carriers=0.8338
  random       N=500  permissive   none=0.6469 minority=0.6645 lift=+0.0176   expected-if-seed-persists=0.7469 shortfall=-0.0824   carriers=0.3339
  random       N=500  constrained  none=0.1103 minority=0.1222 lift=+0.0119   expected-if-seed-persists=0.2103 shortfall=-0.0881   carriers=0.8623

DONE.
