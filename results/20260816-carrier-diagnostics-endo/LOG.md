# Carrier diagnostics: seeded or generated?  (200 reps)  20260816-113003
out: results/20260816-carrier-diagnostics-endo
k = 3, so the 'k-1 distinct' variant is the same measure as >=2 relevant,
because the shipped engine stores distinct element types rather than tokens.

  ... 50/200
  ... 100/200
  ... 150/200
  ... 200/200

run stops at tick 365.1 on average (quiescence or run_length)

## carrier quantities, initialization against endpoint
measure                 t=0   endpoint     change
carrier_ge1          0.4737     0.2215    -0.2522
carrier_ge2          0.1091     0.2210    +0.1120
pure_carrier         0.6751     0.0032    -0.6720
manifest_any         0.0000     0.9969    +0.9969

## carrier trajectory
  t=0     n=200  ge1=0.4737  ge2=0.1091  pure=0.6751  manifest=0.0000
  t=5     n=200  ge1=0.5651  ge2=0.1641  pure=0.7682  manifest=0.0001
  t=10    n=200  ge1=0.6424  ge2=0.2243  pure=0.8374  manifest=0.0001
  t=20    n=200  ge1=0.7542  ge2=0.3369  pure=0.9168  manifest=0.0040
  t=30    n=200  ge1=0.8207  ge2=0.4350  pure=0.9392  manifest=0.0226
  t=40    n=200  ge1=0.8518  ge2=0.5049  pure=0.9160  manifest=0.0650
  t=50    n=200  ge1=0.8496  ge2=0.5469  pure=0.8528  manifest=0.1386
  t=60    n=200  ge1=0.8196  ge2=0.5616  pure=0.7594  manifest=0.2364
  t=80    n=200  ge1=0.7232  ge2=0.5430  pure=0.5611  manifest=0.4380
  t=100   n=200  ge1=0.6061  ge2=0.4787  pure=0.3761  manifest=0.6237
  t=125   n=200  ge1=0.4830  ge2=0.4059  pure=0.2200  manifest=0.7800
  t=150   n=200  ge1=0.3923  ge2=0.3455  pure=0.1318  manifest=0.8682
  t=200   n=200  ge1=0.2837  ge2=0.2680  pure=0.0440  manifest=0.9560
  t=250   n=200  ge1=0.2461  ge2=0.2412  pure=0.0175  manifest=0.9825
  t=300   n=194  ge1=0.2264  ge2=0.2248  pure=0.0073  manifest=0.9927
  t=400   n=32   ge1=0.2183  ge2=0.2175  pure=0.0044  manifest=0.9956

## successful component transfers by sender state
  relevant transfers per run     : 818.4
  from NONMANIFEST sender        : 401.1
  from manifest sender           : 417.4
  share from nonmanifest sender  : 0.4925 (sd 0.0409)

DONE.
