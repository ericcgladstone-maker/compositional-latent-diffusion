# Comment-driven analyses  (30 reps, base_seed 0)  20260728-220913
out: results/20260728-220913-comments

## W1  capacity x sufficiency_k  (V1 base, requirement_size=4)
  k=2: cap3=0.19  cap4=0.61  cap5=0.84  cap6=1.00  cap7=1.00  cap8=1.00  cap10=1.00
  k=3: cap3=0.01  cap4=0.11  cap5=0.31  cap6=0.65  cap7=0.99  cap8=1.00  cap10=1.00
  k=4: cap3=0.00  cap4=0.01  cap5=0.03  cap6=0.12  cap7=0.37  cap8=0.98  cap10=0.98

## W2  stabilization_boost x enhanced_factor  (V2-stab-enh base, loss=0.01)
  boost=0.0: e1.0=0.87(lap0.09)  e2.0=0.98(lap0.08)  e3.0=1.00(lap0.07)
  boost=0.25: e1.0=0.54(lap0.33)  e2.0=0.73(lap0.39)  e3.0=0.84(lap0.43)
  boost=0.5: e1.0=0.39(lap0.40)  e2.0=0.55(lap0.51)  e3.0=0.66(lap0.56)
  boost=0.75: e1.0=0.32(lap0.42)  e2.0=0.41(lap0.52)  e3.0=0.50(lap0.60)
  boost=1.0: e1.0=0.27(lap0.43)  e2.0=0.36(lap0.52)  e3.0=0.42(lap0.58)

## W8  initial_element_density under binding cap (V1 base, capacity=6)
  density=0.05: final=0.6478 peak=0.7755 t_first=100
  density=0.1: final=0.6327 peak=0.7772 t_first=100
  density=0.15: final=0.6528 peak=0.7815 t_first=100
  density=0.2: final=0.6925 peak=0.7905 t_first=100
  density=0.3: final=0.6787 peak=0.7838 t_first=100
  density=0.45: final=0.6627 peak=0.7937 t_first=100
  density=0.6: final=0.653 peak=0.7817 t_first=100

## W3  carrier fraction (holds/transmits a big thing's elements, not manifest for it)
  elements_only: carrier_per_bt=0.3472 pure_carrier=0.0767 manifest_share=0.6528
  whole_package: carrier_per_bt=0.0082 pure_carrier=0.0 manifest_share=0.9918

DONE.
