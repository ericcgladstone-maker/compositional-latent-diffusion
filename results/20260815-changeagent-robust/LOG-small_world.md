# Change agents: robustness to population size and topology  (200 reps)  20260815-115027
out: results/20260815-changeagent-robust
'expected if seed persists' = no-minority adoption plus the seeded share divided by the number of big things, which is what the minority contributes at the first tick before any transmission.
  small_world  N=100  permissive   none=0.6673 minority=0.7147 lift=+0.0474   expected-if-seed-persists=0.7673 shortfall=-0.0526   carriers=0.2853
  small_world  N=100  constrained  none=0.1213 minority=0.1988 lift=+0.0775   expected-if-seed-persists=0.2213 shortfall=-0.0225   carriers=0.7872
  small_world  N=500  permissive   none=0.6661 minority=0.6780 lift=+0.0119   expected-if-seed-persists=0.7661 shortfall=-0.0881   carriers=0.3220
  small_world  N=500  constrained  none=0.1145 minority=0.1839 lift=+0.0694   expected-if-seed-persists=0.2145 shortfall=-0.0306   carriers=0.8024

DONE.
