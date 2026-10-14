# Multi-agent social simulation · AutoResearch v0

A runnable synthetic research framework for mechanism ambiguity and budgeted process evidence. Campus participation is the first adapter; it does not define the research scope. No official challenge score, MIT leaderboard result or real-data validation is claimed.

## Run on this machine

```powershell
.\.venv-research\Scripts\Activate.ps1
python -B prepare_and_cache.py
python -B evaluate.py --split dev --mode fast_dev
python -B evaluate.py --split dev --mode full_paper_ablation
python -B paper_artifacts.py
python -B -m unittest discover -s tests -v
```

Preparation is one-time: the existing cache is never silently overwritten. On this machine it is already prepared, so start with evaluate.py. A new benchmark version must use a new workspace/cache artifact, not replace old evidence.

## Files and contract

- `prepare_and_cache.py`: fixed tensorized simulator, synthetic benchmark, generic external-data contract, 200-mechanism rollout cache.
- `evaluate.py`: fixed metric, baselines, ablations, integrity checks, test freeze gate.
- `method.py`: the only file a research campaign can evolve.
- `autoresearch.py` + `program.md`: commit/evaluate/keep/discard controller and coding-agent workflow.
- `paper_artifacts.py`: three Booktabs tables and a budget-error PDF/PNG; a full suite result is required.
- `tests/test_science.py`: mathematical and simulator contracts.
- `legacy/`: archived old work, preserved unchanged.

Baseline outputs append to `results/` and `experiments.tsv`. These generated traces and the cache stay local; their hashes and curated reports are versioned. Rejected candidate commits remain reachable. This framework does not invent hypotheses without a coding agent and does not schedule itself across sessions.

## Scientific definitions

Closed-loop state includes individual interest, availability, budget, information and experience. Information travels through local ring neighbors. Intent is recorded before budget/conflict/capacity settlement; waiting, cancellations/refunds and promotions are explicit. Eight random seeds are cached for each candidate and event.

Train events expose mechanisms individually; fixed probe rules compose them without target labels. Dev/test use new events and combinations. Process calibration, trajectory observations and active audit records use independent cohorts. Aggregate trajectory errors are compatibility constraints, not independent likelihood multipliers. Initial intent with unobserved viewing has likelihood attention × participation × interest. Acquisition records describe standardized known risk states, not arbitrary unobserved histories.

A binary record's expected reduction in normalized trajectory variance is mean(Cov(p,Z)^2)/(q(1-q)), divided by cost. Batch selection integrates both hypothetical outcomes. This identity assumes fixed cached predictions and conditionally independent audit records; it is not a guarantee of reduced real error.

Acquisition availability is known before selection; the pool excludes records that cannot be retrieved. Their labels are not revealed. Historical and target process missingness remains marginalized/masked. This keeps the binary fantasy model consistent with what an acquired record returns.

Predictions are mixtures of whole trajectories. Epistemic variance is between-mechanism variance of seed means; aleatoric variance is mean within-mechanism seed variance. Reported 90% intervals are pointwise, not simultaneous path bands. RMSE/MAE and widths are population fractions. Multiply by 128 for this example's count scale. NLL/Brier concern held-out next-decision audit records.

SimpleStats uses empirical historical paths. Uncalibrated is a uniform candidate mixture; ProcessOnly and TrajectoryOnly use one compatibility constraint. PassiveV1 applies both constraints with no active evidence. Standard_OED targets historical-event predictions; Covariance targets training-rule combinations. NoSharing uses independent event-specific parameter permutations, changing the prior as well as sharing; report that caveat.

The shifted world adds an unmodeled transport disruption. A post-observation flag marks shifted RMSE > .08 with epistemic variance < .0025. This is a fixed synthetic diagnostic, not reliable advance detection of all model misspecification.

## Environment and boundaries

Python 3.13, PyTorch 2.7.1 + CUDA 12.6 on RTX 4060 Laptop 8GB. Installation uses `uv pip install --python .venv-research/Scripts/python.exe torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126`, then the remaining packages in requirements.txt. Exact installed versions are in requirements.lock.txt. Configure TEMP/TMP and UV_CACHE_DIR under this workspace when installing.

Upstream paradigm: https://github.com/karpathy/autoresearch . The research adaptation uses a 15-second dev budget and an initially bounded campaign. `infrastructure.lock.json` freezes evaluator code after bootstrap. It cannot stop malicious local Python from reading files; a secure external evaluator remains future work. Source project NJU-xianlinSWM stays read-only. MIT data requires a named dataset, provenance, license, explicit mapping and authorization; no real data is bundled.
