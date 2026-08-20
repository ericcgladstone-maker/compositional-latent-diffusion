# Figure data audit

Every plotted value traces to a stored output file. No value is interpolated except where the transform column says so.

| figure | panel | source | x | y | conditioning | reps | value_kind | uncertainty | transform |
|---|---|---|---|---|---|---|---|---|---|
| 1 | all | none (conceptual schematic) | n/a | n/a | n/a | n/a | schematic | none | none |
| 2 | A | results/20260731-endogenous/trajectories.csv | t | manifest_share; substrate | trigger_type=endogenous, mode=elements_only | 200 | mean across replications at each tick | none plotted | sub_at_onset is NOT read off this curve; see next row |
| 2 | A (annotation) | results/20260731-endogenous/e1_shape.csv | n/a | onset; sub_at_onset | trigger_type=endogenous | 200 | mean over replications of each run's substrate at its OWN onset | onset_sd = 9.03 reported in text | shown as a text box, not as a point on the mean curve |
| 2 | B | results/20260816-carrier-diagnostics-endo/carrier_trajectory.csv | t | carrier_ge1; pure_carrier | trigger_type=endogenous, focal spec | 200 while n=200 | means at each sampled tick | sd columns available, not plotted | line drawn only where all 200 replications survive; endpoint from carrier_initial_vs_endpoint.csv shown as separate diamonds |
| 3 | A | results/20260730-102229-comments/w1_capacity_x_k.csv | capacity | final_manifest_share | sufficiency_k in {2,3,4} | 200 | raw means; half-adoption overlay is LINEAR INTERPOLATION between bracketing capacities | none plotted | half-adoption points interpolated, marked as such in caption |
| 3 | B | results/20260730-102229-comments/w8_density_under_cap.csv | initial_element_density | final_manifest_share | capacity=6 | 200 | raw means | none plotted | none |
| 4 | C [compositional, c6, l0.0] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=compositional, c6, l0.0 | 200 paired | paired contrast high-low = -0.0575 | paired SE = 0.0060 | none |
| 4 | C [source, c6, l0.0] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=source, c6, l0.0 | 200 paired | paired contrast high-low = +0.0105 | paired SE = 0.0083 | none |
| 4 | C [count, c6, l0.0] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=count, c6, l0.0 | 200 paired | paired contrast high-low = -0.0088 | paired SE = 0.0088 | none |
| 4 | C [compositional, c5, l0.0] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=compositional, c5, l0.0 | 200 paired | paired contrast high-low = -0.0322 | paired SE = 0.0052 | none |
| 4 | C [source, c5, l0.0] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=source, c5, l0.0 | 200 paired | paired contrast high-low = +0.0330 | paired SE = 0.0090 | none |
| 4 | C [count, c5, l0.0] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=count, c5, l0.0 | 200 paired | paired contrast high-low = +0.0169 | paired SE = 0.0101 | none |
| 4 | C [compositional, c6, l0.01] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=compositional, c6, l0.01 | 200 paired | paired contrast high-low = +0.0590 | paired SE = 0.0044 | none |
| 4 | C [source, c6, l0.01] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=source, c6, l0.01 | 200 paired | paired contrast high-low = +0.1852 | paired SE = 0.0075 | none |
| 4 | C [count, c6, l0.01] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=count, c6, l0.01 | 200 paired | paired contrast high-low = +0.2154 | paired SE = 0.0085 | none |
| 4 | C [compositional, c5, l0.01] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=compositional, c5, l0.01 | 200 paired | paired contrast high-low = +0.0178 | paired SE = 0.0038 | none |
| 4 | C [source, c5, l0.01] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=source, c5, l0.01 | 200 paired | paired contrast high-low = +0.1404 | paired SE = 0.0086 | none |
| 4 | C [count, c5, l0.01] | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | condition | adoption | rule=count, c5, l0.01 | 200 paired | paired contrast high-low = +0.1730 | paired SE = 0.0102 | none |
| 4 | A and B | results/20260816-sourcenonredundant/sourcecmp_*_raw.csv | flow (low=0.05, high=0.20 transmission prob) | adoption | loss=0; C=6 (A), C=5 (B); three readiness rules | 200 paired | raw means | not plotted on A/B; see C | none |
| 5 | A | results/20260730-102229-comments/w2_stab_x_enh.csv | enhanced_factor | final_manifest_share | stabilization_boost in {0,.25,.5,.75,1} | 200 | raw means | none plotted | y axis RECODED: protection = 1 - stabilization_boost, so raw boost=0 (maximal protection) plots at protection=1.00 |
| 5 | B | results/20260730-093338-full/aggregated.csv | focal_value (enhanced_factor) | final_manifest_share_mean; overshoot_mean | phase=V2-enhanced | 200 | raw means | not plotted | none |
| S-advocates | A | results/20260814-changeagent/a_fraction.csv | change_agent_fraction | final; carrier_per_bt | regime in {permissive C=6, constrained C=5} | 200 | raw means | final_sd available, not plotted | none |
| S-advocates | B | results/20260814-changeagent/b_evangelism.csv | change_agent_evangelism | final | regime | 200 | raw means | not plotted | x axis log base 2 |
| S-carriers | exogenous | results/20260816-carrier-diagnostics/carrier_trajectory.csv | t | carrier_ge1; carrier_ge2 | trigger=exogenous, focal spec | 200 while n=200 | means at sampled ticks | sd columns available | dotted horizontals are t=0 values; diamonds are run-end values from carrier_initial_vs_endpoint.csv |
| S-carriers | endogenous | results/20260816-carrier-diagnostics-endo/carrier_trajectory.csv | t | carrier_ge1; carrier_ge2 | trigger=endogenous, focal spec | 200 while n=200 | means at sampled ticks | sd columns available | dotted horizontals are t=0 values; diamonds are run-end values from carrier_initial_vs_endpoint.csv |
