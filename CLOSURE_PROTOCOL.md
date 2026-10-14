# Frozen-method supplementary evaluation protocol

Declared 2026-10-14, after the original test had already been opened. This is a
post-freeze robustness study, not a new blinded confirmatory test or a search.
No parameter, formula, threshold or source byte in method.py will change.

The original evaluator and cache remain hash sealed. Its normalized pooled-RMSE
AUC is reproduced separately. Supplementary results never replace that score.

1. Reconstruct all posterior paths from the sealed evaluator's recorded queries.
   Add NoBatchDedup (unchanged-posterior greedy selection within each two-record
   batch, without repeating a record), MatchedMAP (argmax of the evolved initial
   weights), and four SamePrior acquisition comparisons. NoSharing retains the
   original event-specific permutation prior and its confounding caveat.
2. Use 24 independently generated test worlds, seed 51000 + 101 * world index;
   candidate seed is this seed, truth seed is this seed + 100000. The three fixed
   test event templates interact within a world. Each event template therefore
   has 24 independent activity realizations. Report each template separately.
   For aggregate intervals resample whole worlds, never the three dependent
   events, time cells, agents or eight Monte Carlo paths as independent units.
   Training data, evidence outcomes and selected query paths stay fixed. These
   intervals are conditional on those data and templates, not cross-domain CIs.
3. Use paired percentile bootstrap (2,000 draws, seed 782), 95% confidence
   intervals for mean event AUC and paired AUC differences. Average Random's
   three query repetitions inside each world before bootstrap. Also report
   original pooled AUC separately from supplementary macro-event AUC. Report
   per-event 90% predictive coverage/width, epistemic/aleatoric variance and
   per-time/channel errors; predictive intervals are not confidence intervals.
4. Candidate simulations keep the original rules. Truth additionally uses
   unknown waiting impatience (extra dropout 0.45 from time 2), unknown
   two-hop propagation (coefficient 0.90 instead of 0.35), both together, and
   the original transport shock. SupplementalStressSimulator is a documented
   copy of the sealed simulator; its no-shift output must be byte equal.
5. Report two post-observation diagnostics: the original low-disagreement /
   RMSE flag (epistemic < .0025 and error > .08), and an interval-miscoverage
   alarm (more than 20% of observed path cells outside the pointwise 90%
   prediction interval). The latter uses one realized path per independent
   activity, not its simulator expectation. Report benign false alarm rate
   and shifted detection rates separately, including all failures. These
   thresholds are descriptive, not calibrated detectors or early warnings.
6. Compare covariance and explicit enumeration under both the frozen prior
   and uniform hard-compatible prior, synchronized GPU timings, 10 paired
   repetitions. Report the median paired speed ratio and raw timing samples;
   timing repetitions do not create additional statistical event samples.
7. Official SocioVerse and MIT scores remain unavailable unless a named licensed
   dataset, official split, adapter and evaluation protocol are actually run.
   Do not relabel this constructed campus benchmark as either official dataset.

All attempts, including failed tooling/evaluations, are append-only in closure
provenance. The package includes raw outputs and this protocol for audit.
