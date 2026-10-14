# Frozen-method closure results

All numbers below are synthetic. Official SocioVerse and MIT: **NOT EVALUATED**.

Golden test rerun: `results/20261014T060132Z-bca025a6.json`. Supplement: `results/20261014T060605Z-closure-819380a8.json`.

Event AUC is computed before averaging across events. It differs from the golden pooled-RMSE AUC.
Intervals condition on fixed training/evidence and templates. Random repetitions are averaged inside each world.

| Method | Activity 1 AUC [95% CI] | Activity 2 | Activity 3 | Macro AUC [95% CI] |
|---|---|---|---|---|
| Full (frozen) | 0.00419 [0.00338, 0.00507] | 0.01085 [0.00878, 0.01285] | 0.00615 [0.00398, 0.00865] | 0.00706 [0.00602, 0.00810] |
| Random | 0.01782 [0.01723, 0.01839] | 0.01903 [0.01810, 0.02001] | 0.01496 [0.01446, 0.01544] | 0.01727 [0.01693, 0.01767] |
| Entropy | 0.01294 [0.01227, 0.01364] | 0.01015 [0.00921, 0.01116] | 0.00819 [0.00732, 0.00914] | 0.01042 [0.00989, 0.01106] |
| ParamIG | 0.01298 [0.01234, 0.01368] | 0.01080 [0.01006, 0.01159] | 0.00856 [0.00750, 0.00973] | 0.01078 [0.01017, 0.01144] |
| Standard_OED | 0.02359 [0.02232, 0.02475] | 0.02744 [0.02479, 0.03005] | 0.02158 [0.01934, 0.02361] | 0.02420 [0.02304, 0.02537] |
| SimpleStats | 0.02405 [0.02381, 0.02430] | 0.03230 [0.03039, 0.03418] | 0.01884 [0.01807, 0.01977] | 0.02506 [0.02445, 0.02570] |
| Uncalibrated | 0.01999 [0.01934, 0.02063] | 0.01708 [0.01525, 0.01887] | 0.01381 [0.01279, 0.01489] | 0.01696 [0.01636, 0.01759] |
| ProcessOnly | 0.02043 [0.01938, 0.02140] | 0.01994 [0.01730, 0.02245] | 0.01596 [0.01385, 0.01789] | 0.01878 [0.01770, 0.01986] |
| TrajectoryOnly | 0.01956 [0.01865, 0.02040] | 0.01766 [0.01515, 0.02003] | 0.01428 [0.01253, 0.01593] | 0.01717 [0.01622, 0.01812] |
| PassiveV1 | 0.02043 [0.01938, 0.02140] | 0.01994 [0.01730, 0.02245] | 0.01596 [0.01385, 0.01789] | 0.01878 [0.01770, 0.01986] |
| w/o parameter sharing* | 0.04719 [0.04523, 0.04901] | 0.02117 [0.01872, 0.02361] | 0.05111 [0.04860, 0.05335] | 0.03982 [0.03854, 0.04103] |
| w/o combination target | 0.00419 [0.00338, 0.00507] | 0.01085 [0.00878, 0.01285] | 0.00615 [0.00398, 0.00865] | 0.00706 [0.00602, 0.00810] |
| Single point (original)* | 0.00542 [0.00471, 0.00608] | 0.00754 [0.00592, 0.00935] | 0.00737 [0.00578, 0.00895] | 0.00678 [0.00601, 0.00753] |
| w/o batch redundancy update | 0.00419 [0.00338, 0.00507] | 0.01085 [0.00878, 0.01285] | 0.00615 [0.00398, 0.00865] | 0.00706 [0.00602, 0.00810] |
| Single point (matched MAP) | 0.00419 [0.00338, 0.00507] | 0.01085 [0.00878, 0.01285] | 0.00615 [0.00399, 0.00865] | 0.00707 [0.00603, 0.00810] |
| Same prior: Random | 0.00419 [0.00338, 0.00507] | 0.01084 [0.00877, 0.01284] | 0.00615 [0.00398, 0.00865] | 0.00706 [0.00602, 0.00810] |
| Same prior: Entropy | 0.00419 [0.00338, 0.00507] | 0.01085 [0.00878, 0.01285] | 0.00615 [0.00398, 0.00865] | 0.00706 [0.00602, 0.00810] |
| Same prior: ParamIG | 0.00419 [0.00338, 0.00507] | 0.01085 [0.00878, 0.01285] | 0.00615 [0.00398, 0.00865] | 0.00706 [0.00602, 0.00810] |
| Same prior: Standard_OED | 0.00419 [0.00338, 0.00507] | 0.01085 [0.00878, 0.01285] | 0.00615 [0.00398, 0.00865] | 0.00706 [0.00602, 0.00810] |

## Paired comparisons

Each value is comparator minus Full; positive favors Full. Same world bootstrap indices preserve pairing.

| Comparator | Activity 1 difference [95% CI] | Activity 2 | Activity 3 |
|---|---|---|---|
| Random | 0.01363 [0.01272, 0.01441] | 0.00818 [0.00539, 0.01106] | 0.00880 [0.00627, 0.01100] |
| Entropy | 0.00875 [0.00796, 0.00945] | -0.00070 [-0.00334, 0.00216] | 0.00204 [0.00009, 0.00379] |
| ParamIG | 0.00879 [0.00813, 0.00938] | -0.00005 [-0.00248, 0.00253] | 0.00241 [0.00058, 0.00406] |
| Standard_OED | 0.01940 [0.01758, 0.02094] | 0.01659 [0.01221, 0.02094] | 0.01543 [0.01095, 0.01908] |
| SimpleStats | 0.01986 [0.01886, 0.02077] | 0.02145 [0.01791, 0.02506] | 0.01269 [0.01076, 0.01445] |
| Uncalibrated | 0.01580 [0.01482, 0.01666] | 0.00623 [0.00260, 0.00986] | 0.00766 [0.00453, 0.01033] |
| ProcessOnly | 0.01624 [0.01467, 0.01761] | 0.00909 [0.00477, 0.01342] | 0.00981 [0.00544, 0.01339] |
| TrajectoryOnly | 0.01537 [0.01400, 0.01657] | 0.00681 [0.00260, 0.01102] | 0.00813 [0.00411, 0.01145] |
| PassiveV1 | 0.01624 [0.01467, 0.01761] | 0.00909 [0.00477, 0.01342] | 0.00981 [0.00544, 0.01339] |
| w/o parameter sharing* | 0.04300 [0.04075, 0.04489] | 0.01032 [0.00876, 0.01197] | 0.04496 [0.04042, 0.04885] |
| w/o combination target | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |
| Single point (original)* | 0.00123 [0.00037, 0.00198] | -0.00331 [-0.00612, -0.00032] | 0.00122 [-0.00079, 0.00306] |
| w/o batch redundancy update | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |
| Single point (matched MAP) | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00001] | 0.00000 [-0.00000, 0.00000] |
| Same prior: Random | -0.00000 [-0.00001, -0.00000] | -0.00001 [-0.00001, -0.00000] | -0.00000 [-0.00001, 0.00000] |
| Same prior: Entropy | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |
| Same prior: ParamIG | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |
| Same prior: Standard_OED | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |

## Stress rules and alarm rates

The no-shift row is false alarm rate. Shifted rows are detection rates; these are post-observation diagnostics.

| Method / rule | Activity 1 rate [95% CI] | Activity 2 | Activity 3 |
|---|---|---|---|
| Full (frozen) / none | 0.04167 [0.00000, 0.12500] | 0.25000 [0.08333, 0.41667] | 0.08333 [0.00000, 0.20833] |
| Full (frozen) / waiting | 0.12500 [0.00000, 0.25000] | 0.20833 [0.04167, 0.37500] | 0.08333 [0.00000, 0.20833] |
| Full (frozen) / propagation | 0.08333 [0.00000, 0.20833] | 0.16667 [0.04167, 0.33333] | 0.16667 [0.04167, 0.33333] |
| Full (frozen) / both | 0.12500 [0.00000, 0.25000] | 0.12500 [0.00000, 0.25000] | 0.16667 [0.04167, 0.33333] |
| Full (frozen) / transport | 1.00000 [1.00000, 1.00000] | 1.00000 [1.00000, 1.00000] | 1.00000 [1.00000, 1.00000] |
| Single point (matched MAP) / none | 0.04167 [0.00000, 0.12500] | 0.25000 [0.08333, 0.41667] | 0.08333 [0.00000, 0.20833] |
| Single point (matched MAP) / waiting | 0.12500 [0.00000, 0.25000] | 0.20833 [0.04167, 0.37500] | 0.08333 [0.00000, 0.20833] |
| Single point (matched MAP) / propagation | 0.08333 [0.00000, 0.20833] | 0.16667 [0.04167, 0.33333] | 0.16667 [0.04167, 0.33333] |
| Single point (matched MAP) / both | 0.12500 [0.00000, 0.25000] | 0.12500 [0.00000, 0.25000] | 0.16667 [0.04167, 0.33333] |
| Single point (matched MAP) / transport | 1.00000 [1.00000, 1.00000] | 1.00000 [1.00000, 1.00000] | 1.00000 [1.00000, 1.00000] |
| PassiveV1 / none | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |
| PassiveV1 / waiting | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |
| PassiveV1 / propagation | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |
| PassiveV1 / both | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |
| PassiveV1 / transport | 0.50000 [0.33333, 0.70833] | 0.58333 [0.37500, 0.75000] | 0.33333 [0.16667, 0.54167] |

## Timing

- frozen: median speedup 217.95x; max absolute score discrepancy 9.08e-16.
- uniform_compatible: median speedup 275.16x; max absolute score discrepancy 1.38e-10.

## Interpretation limits

NoSharing changes the prior as well as sharing. Original SinglePoint chooses a different point than the evolved MAP.
NoBatchDedup omits fantasy conditioning but still disallows duplicate records. Its label does not mean paying twice for one record.
Per-time/channel absolute errors, both alarm definitions, and all raw worlds are in the JSON.
The original cache contains three interacting events, so its per-event errors are descriptive and have no independent-event CI.
Unknown waiting/propagation rules are post-freeze stress tests. No rule or detector threshold was tuned to their outcomes.
95% bootstrap CIs can collapse for binary rates at zero or one with 24 worlds; they do not prove zero population risk.
The 90% trajectory intervals are marginal predictive intervals, not simultaneous bands or confidence intervals.
