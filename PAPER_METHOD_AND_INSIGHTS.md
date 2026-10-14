# Frozen Method, Evolution Evidence, and Applicability Boundaries

2026-10-14 · `tested_synthetic` · best algorithm commit `eb641c22eb197d038696894a5e6857d31002af78`

`method.py` SHA256: `b8389adc234ee11e923d59084eaeb83b3821986c5f2f714c9ad5a84ed14650af`.
本次收尾没有修改算法。以下英文方法段和公式对应实际执行分支；后面的实验分析区分观测事实、解释和未验证主张。

## 1. What the present evidence supports

当前最明确的结果是：在这个固定的合成系统上，训练轨迹校准目标的改变降低了测试轨迹误差。
证据尚不支持“主动取证优于同先验随机取证”“集合保留带来实质优势”或“能够可靠发现未知规则”。
协方差公式与二元结果枚举等价，并且在当前 GPU 实现中快得多；等价恒等式本身不能直接作为创新性主张。

原始 dev AUC 从 0.02579135 降至 0.00543199，下降 78.94%。这是在同一个 dev 上进行 60 次自适应选择后的结果，
不是 60 次独立验证。封存 test AUC 为 0.00691577，本次重跑一致。完整轨迹 RMSE 的 AUC 与逐活动 RMSE 后求平均的
macro AUC 不相同，正文不能混用。所有人口比例指标乘 128 可换算为本例人数尺度。

## 2. Method: compatible mechanisms and budgeted process evidence

### 2.1 State, mechanisms, and observations

Let \(\theta_m=(a_m,b_m,d_m)\), \(m=1,\ldots,M\), index shared attention, participation,
and waiting-dropout mechanisms. The simulator advances each agent through local observation,
decision, interaction, environmental settlement, and feedback. An intention is recorded before
capacity, schedule and budget constraints settle admissions. The cached trajectory
\(X_{msetc}\) records population fractions for simulation seed \(s\), event \(e\), time \(t\),
and channel \(c\in\{\mathrm{registered},\mathrm{waitlisted},\mathrm{attended}\}\).

The implementation uses \(M=200\), \(S=8\), 128 agents and eight time steps. Interest, availability,
budget and experience are agent states; shared mechanism parameters do not imply identical states.
Candidate simulations use common random numbers. Observed trajectories and audit outcomes use
separate cohorts and seeds. Each audit record appears once; process totals are not added again as
independent likelihood factors.

For an intent record whose viewing is unobserved, the standardized cohort model marginalizes viewing:

\[
 P(I_r=1\mid\theta_m)=P(V_r=1\mid\theta_m)
 P(I_r=1\mid V_r=1,\theta_m)=a_m\,\rho_{e(r)}\,b_m\,u_r,
\]

where \(\rho_e\) is notification reach and \(u_r\) is interest. This formula describes the
independent audit cohort, not an arbitrary action history inside the interacting simulator.
Waiting records condition on a known waiting-risk state. Missingness is MCAR in the supplied benchmark.

### 2.2 Separate compatibility checks and robust trajectory weighting

Let \(\bar X_{metc}=S^{-1}\sum_s X_{msetc}\), and let \(Y_{etc}\) denote the observed historical
trajectory mean. For observed historical process records \(\mathcal O\), define

\[
 B_m=\frac{1}{|\mathcal O|}\sum_{r\in\mathcal O}(p_{mr}-y_r)^2,
 \qquad
 R_m=\sqrt{\frac{1}{ETC}\sum_{e,t,c}(\bar X_{metc}-Y_{etc})^2}.
\]

If \(\mathcal O\) is empty, the implementation sets all \(B_m=0\). The hard-compatible set is

\[
 \mathcal C=\{m:B_m\leq\min_j B_j+0.045\}\cap\{m:R_m\leq0.10\}.
\]

An empty intersection raises an error; thresholds are not silently relaxed. These tolerances define
a computational compatibility set, not a frequentist confidence set.

The final evolved weighting accounts for estimated simulation noise and the worst-fitting event:

\[
 v_{etc}=\frac{1}{M}\sum_m\frac{1}{S}\sum_s
 (X_{msetc}-\bar X_{metc})^2,\qquad
 \bar v=\frac{1}{ETC}\sum_{etc}v_{etc},\qquad
 r_{etc}=\frac{v_{etc}+\epsilon}{\bar v+\epsilon},
\]
\[
 D_m=\max_e\frac{1}{TC}\sum_{t,c}
 \frac{(\bar X_{metc}-Y_{etc})^2}{r_{etc}},\qquad
 w_m^{(0)}=
 \frac{\mathbf1\{m\in\mathcal C\}\exp[-D_m/(2\sigma^2)]}
 {\sum_{j\in\mathcal C}\exp[-D_j/(2\sigma^2)]},
 \quad\epsilon=10^{-5},\quad\sigma=7\times10^{-4}.
\]

The variance uses a population divisor \(S\), matching `unbiased=False`, and averages over all
candidate mechanisms before the compatibility mask. It is not the variance of the Monte Carlo mean.
The weights are a Gibbs calibration distribution, not an exact data-generating likelihood posterior.
The Brier term gates compatibility; it is not added to the final exponential energy.

### 2.3 Prediction-directed evidence selection

Let \(z_m\in\mathbb R^D\) be the flattened mean trajectory of fixed training-rule combination probes,
and let \(p_{mr}\) be the cached probability of binary process record \(r\). For current weights \(w\),

\[
 \mu=\sum_m w_m z_m,\qquad q_r=\sum_m w_m p_{mr},\qquad
 c_r=\sum_m w_m(p_{mr}-q_r)(z_m-\mu).
\]

Using \(\sum_mw_m(z_m-\mu)=0\), all covariances can be computed as a matrix product:

\[
 C=P^\top\operatorname{diag}(w)(Z-\mathbf1\mu^\top),\qquad
 A_r(w)=\frac{\|c_r\|_2^2/D}{k_r q_r(1-q_r)}.
\]

Here \(k_r>0\) is evidence cost. The implementation clamps the denominator below by \(10^{-12}\).
Only available, previously unqueried and affordable records are eligible.

**Proposition (binary variance-reduction identity).** For fixed cached predictions and the
model-implied binary observation law, the expected reduction of the mean coordinate variance equals
\(\|c_r\|_2^2/[Dq_r(1-q_r)]\), for \(0<q_r<1\).

**Proof.** Let \(\mu_1=E[Z\mid Y_r=1]\) and \(\mu_0=E[Z\mid Y_r=0]\). Bayes' rule gives
\(\mu_1-\mu=c_r/q_r\) and \(\mu_0-\mu=-c_r/(1-q_r)\). The law of total covariance yields

\[
 \frac{1}{D}\operatorname{tr}\!\left(\operatorname{Cov}(Z)
 -E_{Y_r}\operatorname{Cov}(Z\mid Y_r)\right)
 =\frac{q_r\|\mu_1-\mu\|^2+(1-q_r)\|\mu_0-\mu\|^2}{D}
 =\frac{\|c_r\|^2}{Dq_r(1-q_r)}.\quad\square
\]

At deterministic outcomes, the exact covariance is zero and the exact expected reduction is zero.
Floating-point regularization does not create additional evidence. This identity concerns epistemic
variance of conditional mean trajectories. It does not assert monotone observed RMSE, reduction of
aleatoric variance, identification of the true mechanism, or detection of model misspecification.

For a batch, let \(\mathcal F_j=\{(\pi_f,w_f)\}\) contain all possible outcomes of the first \(j\)
selected records. Choose

\[
 r_{j+1}=\arg\max_{r\ \mathrm{eligible}}\sum_{f\in\mathcal F_j}\pi_f A_r(w_f).
\]

Each branch splits into outcomes \(y\in\{0,1\}\) with
\(L_{mry}=p_{mr}^y(1-p_{mr})^{1-y}\),
\(q_{fy}=\sum_mw_{fm}L_{mry}\),
\(\pi_{fy}=\pi_fq_{fy}\), and \(w_{fym}=w_{fm}L_{mry}/q_{fy}\).
No actual label is read during selection. This is exact fantasy averaging for a greedy batch,
not globally optimal batch selection. It assumes record independence conditional on a candidate;
correlated observations would require a joint likelihood. Batch size is two in the experiment
(the implementation supports up to four).

### 2.4 Evidence update and whole-trajectory predictive distributions

For revealed records \(\mathcal Q\), observed mask \(o_r\), and temperature \(\tau=1\),

\[
 w'_m\propto w_m\exp\!\left\{\frac{1}{\tau}\sum_{r\in\mathcal Q}\log\ell_{mr}\right\},
 \qquad \ell_{mr}=\begin{cases}
 p_{mr}^{y_r}(1-p_{mr})^{1-y_r},&o_r=1,\\
 1,&o_r=0\text{ under ignorable missingness}.
 \end{cases}
\]

Probabilities are clipped to \([10^{-7},1-10^{-7}]\) for logarithms. If known observation
probabilities \(\rho_{mry}=P(O_r=1\mid Y_r=y,\theta_m)\) are supplied, the observed likelihood
is multiplied by \(\rho_{mry_r}\); missing likelihood is
\((1-p_{mr})(1-\rho_{mr0})+p_{mr}(1-\rho_{mr1})\). This optional MNAR branch is unit-tested,
but not validated on a real missingness process. In the main acquisition experiment, retrieval
availability is public metadata and only available records may be selected.

For target whole paths \(X^*_{ms}\), the predictive law and variance decomposition are

\[
 \widehat P(X^*\mid\mathcal Q)=\sum_m\sum_{s=1}^S\frac{w'_m}{S}\delta_{X^*_{ms}},
 \quad \widehat\mu=\sum_mw'_m\bar X^*_m,
\]
\[
 V_{\rm epi}=\sum_mw'_m(\bar X^*_m-\widehat\mu)^2,\qquad
 V_{\rm alea}=\sum_mw'_m\frac1S\sum_s(X^*_{ms}-\bar X^*_m)^2.
\]

Both variances are coordinatewise and sum to the mixture variance. The 5th and 95th weighted
quantiles produce pointwise 90% intervals; they are not simultaneous path bands. The full empirical
mixture preserves dependence across time and channels even though marginal intervals do not show it.

### 2.5 Algorithm 1 (LaTeX, algorithm + algpseudocode packages)

```latex
\begin{algorithm}[t]
\caption{Frozen compatible-mechanism inference with budgeted process evidence}
\label{alg:compatible-evidence}
\begin{algorithmic}[1]
\Require Historical observations, cached $X,P,Z,X^*$, costs $k$, pool $U$, budget $B$
\State Compute process Brier errors $B_m$ and trajectory errors $R_m$
\State $\mathcal C\gets\{m:B_m\leq\min_j B_j+0.045,\ R_m\leq0.10\}$
\If{$\mathcal C=\emptyset$} \State \textbf{raise} model-inadequacy error \EndIf
\State Compute noise-normalized worst-event distance $D_m$
\State $w_m\gets\mathrm{softmax}_{m\in\mathcal C}[-D_m/(2\sigma^2)]$
\While{budget remains and an affordable record exists}
  \State $\mathcal F\gets\{(1,w)\}$; $Q\gets\emptyset$
  \For{$j=1,\ldots,\min(2,\text{remaining record budget})$}
    \State Compute $A_r(w_f)$ by weighted covariance for every branch $f$
    \State $r\gets\arg\max_{r\in U\setminus Q,\ k_r\leq B}\sum_f\pi_f A_r(w_f)$
    \State $Q\gets Q\cup\{r\}$; reserve cost $k_r$ from $B$
    \State Expand $\mathcal F$ using both hypothetical binary outcomes of $r$
  \EndFor
  \State Acquire only records in $Q$; integrate missing outcomes
  \State Update $w$ by the temperature-scaled likelihood; $U\gets U\setminus Q$
\EndWhile
\State \Return whole-path mixture $\sum_{m,s}(w_m/S)\delta_{X^*_{ms}}$, $V_{\rm epi},V_{\rm alea}$
\end{algorithmic}
\end{algorithm}
```

The loop shown uses unit record costs, as in the experiment. For general costs the code stops when
no eligible affordable record remains, rather than using the integer budget as a record count.
After development selection, all constants, formulas and source bytes are frozen before test evaluation.

## 3. What changed during the 60-round evolution

审计逐条核对了 `experiments.tsv`、候选提交的 `git show` 和 `trials.jsonl`：60 个不同候选，10 个 KEEP，
50 个 REVERT，没有评测崩溃。原账本用 `discard` 表示 REVERT；一次评测行和后续决策行按 `run_id`
关联，不能算作两次实验。完整记录和每轮算法原文位于 `provenance/closure/evolution-audit.json` 与 `candidates/`。

| 轮次 | 已测改动 | dev AUC 变化 | 可以得出的结论 |
|---|---|---|---|
| R1–R7 | 对相容集合按训练轨迹拟合软加权，逐步收窄核宽 | 0.02579135 → 0.00734499 | 这个基准上，校准偏差比保持广泛权重更影响主指标；不能外推到真实机制恢复 |
| R30 | 平均轨迹损失改为最差活动损失 | 0.00734499 → 0.00704311 | 共享参数下约束最差历史活动有小幅收益，尚无跨数据集重复 |
| R38 | 核宽收窄至 0.0007 | 0.0070431092 → 0.0070430333 | 达到预设 KEEP 阈值，但差值只有约 7.6e-8，不是实质跃升 |
| R58 | 训练噪声归一化，方差底值 1e-5 | 0.00704303 → 0.00543199 | 本轮后期最大的改进；与该缓存的有限种子噪声结构有关 |

R1–R7 的收益不能分解成七项独立贡献，因为每轮以之前接受的算法为起点。R58 的局部降幅约 22.87%，
也只是同一 dev 上的顺序比较。分析应写成经验观察，不应把噪声加权或 worst-event 损失本身包装为已有理论未覆盖的新概念。

### REVERT 记录告诉了我们什么

| 轮次 | 假设 | 观测结果 | 解释与限制 |
|---|---|---|---|
| R8–R9、R36–R37 | 放宽轨迹核，保留更多候选 | 更差；R37 为 0.00823951 | 多样性可增加当前先验的预测偏差；不证明集合方法一般无效 |
| R10–R13 | 加强已取证记录的似然更新 | 温度 0.05/0.1 明显更差：0.01102639/0.01080275 | 少量二元记录可能放大噪声或失配；没有建立更强更新必然更好的证据 |
| R14–R17、R50–R53 | 混入均匀权重防止集合坍缩 | 全部未改善；R53 为 0.00782675 | 数值多样性和准确的不确定性不是同一回事 |
| R18–R23 | 加入过程 Brier 能量 | 几乎不变 | 在高度集中的轨迹权重下，所测过程项未改变有效预测；并非过程证据不重要 |
| R24–R29 | 改变状态通道权重 | 没有超过接受阈值的收益 | R24/R26/R29 虽有约 1e-9 改善仍按规则回退，不能写成失败导致显著退化 |
| R31–R35 | worst-channel、绝对误差、Huber、截尾、后半段损失 | 全部回退 | 所测试的鲁棒性形式并不等价；有限种子与不同时段的信息结构会影响校准 |
| R39–R41 | 平滑最差活动目标 | 无实质收益或更差 | 平滑并非必然有益；R39 的微小改善未达阈值 |
| R42–R45 | 重标度组合探针坐标 | AUC 完全相同 | 先验近乎单点时，改变取证几何可能不改变可见预测 |
| R46–R49 | 在新先验下改变后验温度 | 仅浮点量级变化 | 不能据此选择一个温度并声称有效 |
| R54–R57 | 在随机种子层面边缘化整条轨迹核 | 0.00802215–0.01507502，均更差 | 比较同时涉及核宽和种子层面目标；不能归因于“随机性建模有害” |
| R59–R60 | 把训练方差底值增至 1e-4/1e-3 | 0.01300248 / 0.00704303 | 最优方案对噪声正则尺度敏感，应作为脆弱性披露 |

## 4. Theoretical analysis and boundary discussion

### 4.1 Compatibility is not identification

当前硬相容集合有 170 个机制，但 float32 下仅 12 个权重非零，权重大于 1e-4 的只有两个。
初始 ESS 为 1.00038481，最大权重为 0.99980766。最重候选为约 \((0.4167,0.6833,0.42)\)，
合成真值为 \((0.90,0.30,0.27)\)。低轨迹误差并不表示正确找回注意、参与和退出机制。

When \(w\) tends to a point mass, \(\operatorname{Cov}_w(p_r,Z)\to0\) for every record. Thus a
nonempty hard-compatible set can coexist with an effectively inactive evidence selector. Keeping
multiple candidates in a data structure is not sufficient to preserve meaningful epistemic uncertainty.

### 4.2 Equal agreement can be confidently wrong

As a counterexample, suppose every candidate predicts the same path \(z_0\), but an unmodeled
environmental rule changes the truth to \(z_0+\Delta\). Then every acquisition score and epistemic
variance is zero, while squared prediction error is \(\|\Delta\|^2/D\). The covariance identity still
holds internally. It provides no out-of-model guarantee. A post-observation discrepancy can reveal
this failure, but agreement alone cannot warn about it before the new outcome is observed.

补充实验固定规则和阈值后运行 24 个独立世界，每个活动模板有 24 次独立实现。完整方法在无偏移时的
区间告警率为 4.2%、25.0%、8.3%；未知等待规则下为 12.5%、20.8%、8.3%；未知传播下为 8.3%、16.7%、16.7%。
三个活动在强交通冲击下均检出，但这不能抵消对较弱偏移的漏检。原有 `RMSE > .08` 告警对等待和传播偏移全部不触发。
固定阈值不是经过校准的异常检测器，也不是提前预警。测试中的等待偏移本身较小，应同时报告真值轨迹的偏移幅度。

### 4.3 Matched comparisons change the interpretation

原封存的 Random/Entropy/ParamIG/Standard_OED 使用均匀相容权重，而 Full 使用进化后的校准。
两者差异同时包含校准和取证，不能把整段差距都归因于主动策略。补充实验额外提供 SamePrior 对照。
在相同进化先验下，Random 的 macro AUC 为 0.00705892，Full 为 0.00706354；没有主动策略优越的证据。

原 SinglePoint 按“过程误差＋轨迹误差”选择候选，与 Full 的最重机制不同。补充的 MatchedMAP
只把 Full 初始权重替换为它的 argmax，其他条件一致。24 个世界的 macro AUC 为：

| 对照 | Macro AUC | 95% 世界重采样区间 |
|---|---:|---|
| Full | 0.00706354 | [0.00602473, 0.00809948] |
| MatchedMAP | 0.00706548 | [0.00602672, 0.00810121] |
| w/o combination target | 0.00706354 | [0.00602473, 0.00809948] |
| w/o batch redundancy update | 0.00706354 | [0.00602473, 0.00809948] |
| w/o parameter sharing | 0.03982375 | [0.03854018, 0.04103227] |

MatchedMAP 与 Full 的差异约 1.94e-6，在实际效应量上极小。即使条件配对区间排除零，也不能直接称为机制集合的
实质优势。NoSharing 的候选空间和先验也发生变化，因此其差值不是参数共享的纯因果效应。
逐活动区间和配对差值见补充 `RESULTS.md`；不要以两个边际区间是否重叠替代配对检验。

### 4.4 Calibration tradeoffs and finite computation

dev Brier 从 0.18933 变为 0.24205；冻结 test Brier 为 0.245921。轨迹预测改善伴随着个体行为概率质量下降。
90% 点态区间的 test 覆盖率为 97.92%，宽度为 0.03038 左右；覆盖率高并不表示自动获得了准确或紧致的全轨迹不确定性。
八个种子只能粗略估计随机波动，浮点下溢也进一步缩小实际权重支持集。

Covariance scoring and naive explicit outcome enumeration both require \(O(MRD)\) arithmetic.
The observed speedup comes from shared computation and batched matrix operations rather than a
different asymptotic order. Branch enumeration grows exponentially in batch size, which motivates
the explicit small-batch limit. The initial supplemental timing measured median speedups of
217.95x (frozen weights) and 275.16x (uniform compatible weights); these are hardware/runtime-specific
microbenchmarks, not whole-pipeline speedups. Raw synchronized paired timings and equality residuals are retained.

### 4.5 Evaluation units and external validity

原缓存三个测试活动共享人群、预算和时间冲突，不能把它们或其时段当作独立重复。补充评测按整个世界重采样，
每个活动模板分别报告区间；训练观测、证据答案和模板保持固定。因此这些区间只反映新生成群体和 Monte Carlo 路径的
变化，尚未涵盖新训练集、新活动类型、证据抽样或真实人群之间的迁移风险。

封存测试已经打开；本次重复是复现核验。补充实验在停止搜索后预先写定协议，但仍属于事后扩展，不能包装成
完全盲测。下一阶段若继续研究，应另建协议与未见数据；本次没有继续调参。

用户指定的 [Social Simulation Arena](https://socialsim.org/docs.html) 是实时总体、群体画像和排名预测任务。
其 [接口契约](https://github.com/Social-Atoms/social-sim-arena/blob/main/docs/agent-api.md) 与本地活动轨迹张量不等价。
当前没有有效的 Arena 榜单成绩，也没有 SocioVerse 官方数据成绩。接入差距与已核对版本见 `SOCIALSIM_INTEGRATION.md`。

## 5. Evidence index

- `provenance/closure/evolution-audit.json`: every KEEP/REVERT reconciled against the ledger and Git source bytes.
- `provenance/closure/candidates/`: all 60 candidate algorithm files, including rejected candidates.
- `provenance/campaign60/summary.json`: campaign counts, original scores and concentration diagnostics.
- `CLOSURE_PROTOCOL.md`: post-freeze independent-world, stress and timing protocol.
- `provenance/closure/golden-test.json` and `supplement.json`: immutable copied outputs used for this report.
- `provenance/closure/paper/`: complete three-experiment LaTeX tables, curves and raw event metrics.

本报告支持写出可审计的方法章节和诚实的结果分析；尚不支持宣称已达到顶会创新标准、完成机制辨识或取得官方榜单成绩。
