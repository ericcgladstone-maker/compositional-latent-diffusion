# Change agents: does an equipped minority move adoption?  (200 reps)  20260814-215703
out: results/20260814-changeagent
base: phase change-agent (elements_only, ambient element density 0.05). 'constrained' lowers capacity so unaided diffusion is weak.

## A  fraction sweep including the missing zero control
  permissive   f0=0.6673  f0.05=0.6943  f0.1=0.6952  f0.15=0.6951  f0.2=0.7147   [scenario off = 0.6712]
               lift over the zero control at the largest fraction: +0.0474
  constrained  f0=0.1213  f0.05=0.1294  f0.1=0.1507  f0.15=0.1846  f0.2=0.1988   [scenario off = 0.1186]
               lift over the zero control at the largest fraction: +0.0775
  carrier fraction (what the minority produces instead of adopters):
    permissive   fraction 0.0: adoption 0.6673  carriers 0.3327
    permissive   fraction 0.2: adoption 0.7147  carriers 0.2853
    constrained  fraction 0.0: adoption 0.1213  carriers 0.8647
    constrained  fraction 0.2: adoption 0.1988  carriers 0.7872

DONE.
