# AutoResearch: compatible mechanisms and active evidence

Read README.md, AGENTS.md and STATUS.md first. This is an adaptation of Andrej Karpathy's single-edit-file paradigm: https://github.com/karpathy/autoresearch/blob/master/program.md . We freeze evaluation, commit a candidate before running it, then keep improvements and rewind rejected candidates. The coding agent supplies hypotheses; autoresearch.py supplies the Git state machine. No external LLM API is called.

## Fixed experiment

Minimize dev_auc_error: normalized trapezoidal area under population-fraction RMSE across evidence budgets [0,2,4,8,12,16]. Use the existing 200-mechanism cache, eight simulation seeds, and the same evidence pool. The full evaluator also reports missingness-aware process scores, pointwise mixture intervals and variance decomposition. Test outcomes must never guide selection.

The ONLY file editable during a campaign is method.py. Do not modify the fixed infrastructure, cache, lock, requirements, tests or this program. Do not read target answer tensors from disk in method.py, modify scores, change the pool or budgets, install packages, or use the internet during search. Method inputs include training observations, acquisition probabilities, probe trajectories, selected evidence and target predictions; target answers are evaluator-owned.

## Start and loop

1. Baseline infrastructure, dependencies and cache must already exist. Use the local .venv-research interpreter. All commands run from the research root.
2. Use a dedicated codex/ branch. After the initial baseline commit, run `python autoresearch.py init` once. This verifies a clean index, evaluates baseline and records the accepted commit/score.
3. Form one falsifiable hypothesis. Edit only method.py. Keep the public API intact.
4. Run `python autoresearch.py trial --description "one concrete hypothesis"`. The controller commits the candidate, runs the fixed dev evaluator, and preserves its logs.
5. Lower dev_auc_error by more than 1e-8: keep the commit. Otherwise: save the rejected commit under refs/autoresearch/rejected and restore only method.py and the branch pointer. Crashes and timeouts are recorded and rejected. No reset --hard.
6. Read the result and propose the next single change. Stop after three candidates, two consecutive failures or 45 minutes for this initial campaign. Evaluation subprocess timeout is 30 seconds; fast_dev runtime above 15 seconds is rejected. Use measurements, not claims of guaranteed speed.
7. When development selection is finished, `python autoresearch.py freeze-test` seals the accepted method hash. Only then run `python evaluate.py --split test --mode full_paper_ablation`. No further development trials in that campaign.

## Research direction

Do not assume active evidence helps. Test whether reduction of model-internal probe disagreement improves independent event predictions, especially under unmodeled rules. Preserve V1 passive calibration as a baseline. Use training-rule probes; missing views are latent, not negative observations. The next method candidate may change posterior temperature or acquisition objectives, but must not consume dev/test answers or change evaluation.

The default domain is a small synthetic engineering example. MIT_Benchmark_Adapter is a generic data contract, not a verified adapter for any named MIT benchmark. No real-data or cross-domain validity has been established. Local hash checks are audit safeguards, not a secure held-out execution sandbox.
