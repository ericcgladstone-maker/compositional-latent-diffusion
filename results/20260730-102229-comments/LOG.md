# Comment-driven analyses  (200 reps, base_seed 0)  20260730-102229
out: results/20260730-102229-comments

## W1  capacity x sufficiency_k  (V1 base, requirement_size=4)
  k=2: cap3=0.22  cap4=0.60  cap5=0.84  cap6=1.00  cap7=1.00  cap8=1.00  cap10=1.00
  k=3: cap3=0.01  cap4=0.13  cap5=0.32  cap6=0.65  cap7=0.99  cap8=1.00  cap10=1.00
  k=4: cap3=0.00  cap4=0.01  cap5=0.03  cap6=0.11  cap7=0.37  cap8=0.98  cap10=0.98

## W2  stabilization_boost x enhanced_factor  (V2-stab-enh base, loss=0.01)
  boost=0.0: e1.0=0.88(lap0.09)  e2.0=0.98(lap0.08)  e3.0=1.00(lap0.07)
  boost=0.25: e1.0=0.54(lap0.33)  e2.0=0.73(lap0.40)  e3.0=0.83(lap0.43)
  boost=0.5: e1.0=0.39(lap0.41)  e2.0=0.55(lap0.51)  e3.0=0.67(lap0.57)
  boost=0.75: e1.0=0.32(lap0.43)  e2.0=0.43(lap0.53)  e3.0=0.52(lap0.60)
  boost=1.0: e1.0=0.28(lap0.43)  e2.0=0.37(lap0.52)  e3.0=0.43(lap0.59)

## W8  initial_element_density under binding cap (V1 base, capacity=6)
  density=0.05: final=0.6712 peak=0.7886 t_first=100
  density=0.1: final=0.6472 peak=0.7844 t_first=100
  density=0.15: final=0.6482 peak=0.7837 t_first=100
  density=0.2: final=0.6716 peak=0.7858 t_first=100
  density=0.3: final=0.6521 peak=0.785 t_first=100
  density=0.45: final=0.6501 peak=0.7875 t_first=100
  density=0.6: final=0.6516 peak=0.784 t_first=100

## W3  carrier fraction (holds/transmits a big thing's elements, not manifest for it)
  elements_only: carrier_per_bt=0.3517 pure_carrier=0.0783 manifest_share=0.6482
  whole_package: carrier_per_bt=0.0058 pure_carrier=0.0 manifest_share=0.9942

DONE.
