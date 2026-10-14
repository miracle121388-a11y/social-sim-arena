# AutoResearch Round 2: frozen results

Branch: `exp/v2-non-collapsed`. Winner: `0d094ecdf021a9def8daf6d5f38ada0e6cc9686d`.
Method SHA-256: `5125975a933bf283ddc117a67f82e0a9e7d726aac3d21a39a0651796b92f6e48`.
30 valid trials: 3 KEEP, 27 REVERT, no execution failures.

| Quantity (same new benchmark) | V1 | V2 |
|---|---:|---:|
| Initial ESS | 1.014551 | 26.447500 |
| Dev Full AUC | 0.14410129 | 0.07568687 |
| Test Full AUC | 0.14388809 | 0.05776344 |
| Test B0 RMSE | 0.14600924 | 0.13319452 |
| Test B16 RMSE | 0.14006898 | 0.03947583 |
| Test initial Brier | 0.18296421 | 0.18800342 |
| Test B16 Brier | 0.18222658 | 0.17437756 |
| Same-prior gain vs Random | 1.4% | 50.1% |
| Same-prior gain vs Entropy | 1.5% | 56.6% |

Test AUC CI: [0.04948, 0.06688]. Paired B0-minus-B16 CI: [0.08321, 0.10258].
Whole worlds are the resampling unit (12 dev / 24 test); activitywise results are in the sealed JSON and paper tables.

## Interpretation

- Constructed mechanism-pair history RMSE 0.000000; combined disagreement 0.280944.
- All preregistered development guards passed; the same criteria also pass on frozen test.
- ParamIG ties Full exactly. Batch fantasy removal is inactive in the matched trials.
- ESS floors 8--24 are inactive at the winner's width; broader calibration and likelihood tempering explain the measured change, not a uniquely identified effect of the ESS constraint.
- The pool intentionally contains high-entropy nuisance availability records. This is a synthetic stress test, not a universal acquisition ranking.
- New test worlds reuse the probe event design. There is no official SocioVerse/MIT evaluation or real-data validation.
- V1's original ESS 1.000385 belongs to the old benchmark. Its ESS on the new benchmark is 1.014551; do not conflate the two.

## Reproduce

Use `.venv-research/Scripts/python.exe -B evaluate.py --campaign v2 --split test --mode full_paper_ablation`.
For V1 on this same cache add `--method-version v1`. `reproduce_round2.ps1` and `reproduce_round2.sh`
verify invariants, rerun both sealed versions, and rebuild the paper. They do not restart search.
The original V1 cache and `dist/njusim-frozen-research.zip` are preserved; legacy V1 root commands
use the old lock and should not be mixed with the V2 branch infrastructure.

The paper extension generator reads canonical sealed results, not the newest rerun.
`experiments_v2.tsv`, `configs/v2_trials.json`, and `provenance/v2/*-decision.json` contain all 30 trials.
Rejected source versions remain reachable under `refs/autoresearch-v2/rejected/`.
