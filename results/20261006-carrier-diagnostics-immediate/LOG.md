# Carrier diagnostics: seeded or generated?  (200 reps)  20261006-124004
out: results/20261006-carrier-diagnostics-immediate
k = 3, so the 'k-1 distinct' variant is the same measure as >=2 relevant,
because the shipped engine stores distinct element types rather than tokens.

  ... 50/200
  ... 100/200
  ... 150/200
  ... 200/200

run stops at tick 361.5 on average (quiescence or run_length)

## carrier quantities, initialization against endpoint
measure                 t=0   endpoint     change
carrier_ge1          0.4737     0.2183    -0.2554
carrier_ge2          0.1091     0.2179    +0.1088
pure_carrier         0.6751     0.0015    -0.6737
manifest_any         0.0000     0.9986    +0.9986

## carrier trajectory
  t=0     n=200  ge1=0.4737  ge2=0.1091  pure=0.6751  manifest=0.0000
  t=5     n=200  ge1=0.5417  ge2=0.1371  pure=0.7240  manifest=0.0454
  t=10    n=200  ge1=0.6050  ge2=0.1825  pure=0.7681  manifest=0.0711
  t=20    n=200  ge1=0.6829  ge2=0.2585  pure=0.7841  manifest=0.1389
  t=30    n=200  ge1=0.7120  ge2=0.3200  pure=0.7430  manifest=0.2210
  t=40    n=200  ge1=0.7078  ge2=0.3606  pure=0.6737  manifest=0.3089
  t=50    n=200  ge1=0.6877  ge2=0.3858  pure=0.5963  manifest=0.3947
  t=60    n=200  ge1=0.6519  ge2=0.3961  pure=0.5145  manifest=0.4812
  t=80    n=200  ge1=0.5705  ge2=0.3904  pure=0.3724  manifest=0.6268
  t=100   n=200  ge1=0.4906  ge2=0.3672  pure=0.2616  manifest=0.7383
  t=125   n=200  ge1=0.4023  ge2=0.3272  pure=0.1610  manifest=0.8389
  t=150   n=200  ge1=0.3371  ge2=0.2917  pure=0.0973  manifest=0.9028
  t=200   n=200  ge1=0.2596  ge2=0.2438  pure=0.0323  manifest=0.9677
  t=250   n=200  ge1=0.2299  ge2=0.2252  pure=0.0111  manifest=0.9889
  t=300   n=184  ge1=0.2216  ge2=0.2200  pure=0.0043  manifest=0.9957
  t=400   n=32   ge1=0.2105  ge2=0.2102  pure=0.0000  manifest=1.0000

## successful component transfers by sender state
  relevant transfers per run     : 811.6
  from NONMANIFEST sender        : 308.8
  from manifest sender           : 502.9
  share from nonmanifest sender  : 0.3825 (sd 0.0356)

DONE.
