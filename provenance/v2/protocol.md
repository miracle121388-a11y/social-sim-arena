# Round 2 preregistered protocol (before any development score)

This is a new synthetic stress benchmark, not a revision of V1 measurements.
V1 source, original cache and original 60-trial history remain preserved. The
branch is exp/v2-non-collapsed. Only method.py evolves during 30 valid trials.

## Constructed ambiguity and scope
Two fixed mechanisms (a,b,d)=(.2,.95,.12) and (.95,.2,.12) have equal a*b.
Initial inverse-transform common random numbers make historical intentions
identical. Queue-enabled peer notices activate a local eight-neighbor cascade
only when both queueing and forwarding are enabled. Historical activities
enable one intervention at a time; probes activate all three, including .9
same-time conflict blocking. This deliberately strong, known interaction
stress test should not be described as an empirical social law. The algorithm
does not know which candidate generates the truth. The pool has 24 view,
40 availability (known p=.5), and 96 marginalized intention records. Entropy
therefore faces irreducible nuisance uncertainty. Conclusions must disclose
this composition; no claim of universal superiority over entropy selection.

The pair's candidate-trajectory geometry is checked once before search on
train, probe, and test event designs. No test truth is read for this check.
Test is fresh-world replication on the same constructed design, not a new
combination beyond the probes and not cross-domain transfer.

## Frozen measurement and KEEP decision
M=200, S=8, N=256, T=12; budgets [0,2,4,8,12,16]. Twelve dev and 24 test worlds
and all seeds are frozen in configs/high_disagreement_mode.json. Test truth is
in a separate file and is loaded only after the winner is sealed. This is an
audit boundary, not a secure sandbox.

Primary AUC is trapezoidal area divided by 16 of activitywise trajectory RMSE,
averaged across three activities and independent worlds. Resample whole worlds
(2000 paired bootstrap replicates, seed 880301); never treat correlated events
or time steps as independent samples. Report each activity separately, plus the
equal-weight macro. These conditional CIs do not correct 30-trial adaptive
selection; frozen test is the confirmation.

A candidate is KEEP only if macro dev AUC improves the incumbent by >1e-8 AND:
initial ESS >=8; both initial and B16 independent process-audit Brier <=.195;
the paired 95% bootstrap CI lower bound for macro (B0 error - B16 error) >0;
Full AUC <.95*Random AUC AND <.95*Entropy AUC; fast-dev runtime <=15 seconds.
Full, Random, Entropy have identical w0, pool, costs, answers, budgets, MCAR mask,
likelihood temperature and posterior code. Only their acquisition differs.
The extra initial AND final Brier requirement conservatively resolves the
user's phrase 'calibrated process Brier'. The significance rule is fixed now.

V1 is first rerun on this cache and supplies the initial incumbent AUC threshold.
It is a benchmark comparator, not an eligible Round-2 solution. If no candidate
passes, restore V1, label the campaign unsuccessful, and do not call a diagnostic
best candidate a winner. Keep rejected commits under refs/autoresearch-v2/rejected.
No reset --hard. Every hypothesis and configuration is logged before evaluation.
Infrastructure failures are recorded separately; they do not count as valid
experiments. No threshold, data, seed or evaluator changes during the campaign.

## Search and publication
Thirty preregistered configurations explore calibration width, process weight,
ESS floor, objective aggregation, likelihood temperature, late-time weighting,
and batch fantasy conditioning. This is a controlled finite configuration
search, not 30 independent confirmatory hypothesis tests. Temperature-matched
fantasy conditioning is a heuristic for tau !=1; no submodularity theorem or
exact variance-reduction identity is claimed in that case.

After round 30 seal method hash, evaluate V1 and V2 on test, and append section
4.5 to both manuscripts. Preserve the earlier V1 methods, tables and negative
conclusions with explicit version labels. No further method tuning after test.
