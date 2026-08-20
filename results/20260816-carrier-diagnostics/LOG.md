# Carrier diagnostics: seeded or generated?  (200 reps)  20260816-112652
out: results/20260816-carrier-diagnostics
k = 3, so the 'k-1 distinct' variant is the same measure as >=2 relevant,
because the shipped engine stores distinct element types rather than tokens.

  ... 50/200
  ... 100/200
  ... 150/200
  ... 200/200

run stops at tick 366.2 on average (quiescence or run_length)

## carrier quantities, initialization against endpoint
measure                 t=0   endpoint     change
carrier_ge1          0.4737     0.3517    -0.1220
carrier_ge2          0.1091     0.3513    +0.2422
pure_carrier         0.6751     0.0783    -0.5968
manifest_any         0.0000     0.9217    +0.9217

## carrier trajectory
  t=0     n=200  ge1=0.4737  ge2=0.1091  pure=0.6751  manifest=0.0000
  t=5     n=200  ge1=0.5651  ge2=0.1641  pure=0.7682  manifest=0.0000
  t=10    n=200  ge1=0.6424  ge2=0.2244  pure=0.8375  manifest=0.0000
  t=20    n=200  ge1=0.7558  ge2=0.3390  pure=0.9203  manifest=0.0000
  t=30    n=200  ge1=0.8334  ge2=0.4468  pure=0.9623  manifest=0.0000
  t=40    n=200  ge1=0.8850  ge2=0.5396  pure=0.9826  manifest=0.0000
  t=50    n=200  ge1=0.9195  ge2=0.6193  pure=0.9909  manifest=0.0000
  t=60    n=200  ge1=0.9430  ge2=0.6875  pure=0.9955  manifest=0.0000
  t=80    n=200  ge1=0.9712  ge2=0.7912  pure=0.9990  manifest=0.0000
  t=100   n=200  ge1=0.4897  ge2=0.3672  pure=0.2650  manifest=0.7348
  t=125   n=200  ge1=0.5186  ge2=0.4461  pure=0.2753  manifest=0.7246
  t=150   n=200  ge1=0.5454  ge2=0.5019  pure=0.2931  manifest=0.7069
  t=200   n=200  ge1=0.2622  ge2=0.2472  pure=0.0364  manifest=0.9637
  t=250   n=200  ge1=0.3689  ge2=0.3633  pure=0.0939  manifest=0.9061
  t=300   n=188  ge1=0.2206  ge2=0.2187  pure=0.0044  manifest=0.9956
  t=400   n=39   ge1=0.2086  ge2=0.2083  pure=0.0005  manifest=0.9995
  t=500   n=1    ge1=0.2350  ge2=0.2350  pure=0.0000  manifest=1.0000

## successful component transfers by sender state
  relevant transfers per run     : 821.7
  from NONMANIFEST sender        : 493.8
  from manifest sender           : 328.0
  share from nonmanifest sender  : 0.6039 (sd 0.0394)

DONE.
