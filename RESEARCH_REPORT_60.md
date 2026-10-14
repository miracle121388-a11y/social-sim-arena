# 60 轮自动研究记录

2026-10-14。完成 60 轮有效实验：10 次保留，50 次回退，没有实验崩溃或超时。每轮在改动前写入假设，单独提交 method.py，再运行固定 dev 评测器；下降超过 1e-8 才保留。60 个候选源码哈希不同，所有候选提交都只改了 method.py，50 个被拒绝的提交仍有 Git 引用。

用户本轮明确要求覆盖原有 3 轮及 45 分钟上限。只调整本地状态与审计记录，没有修改 program.md、评测器、缓存、依赖、固定测试或哈希锁。实验账本保留了原始评测行，并追加 keep/discard 裁决行；统计按 run_id 去重，不能把两种行算成两次实验。

## 结果

| 指标 | 结果 |
|---|---:|
| 初始 dev AUC | 0.02579135 |
| 最佳 dev AUC | 0.00543199 |
| dev 相对下降 | 78.94% |
| 冻结后 test AUC | 0.00691577 |
| 单轮 fast_dev 用时 | 4.03–9.39 秒 |
| 回归测试 | 14 项通过 |

最佳算法提交 `eb641c2`，来自第 58 轮。它对历史轨迹中的高模拟噪声维度降低权重，再按最难拟合的历史事件构造初始候选权重。注意、参与和退出参数仍跨活动共享；相容集合筛选、协方差选证据、贝叶斯更新和完整轨迹预测接口保留。

最佳参数：训练核宽度 0.0007，方差下限 1e-5。噪声尺度来自训练缓存的种子方差，未使用开发或测试答案作为方法输入。全程没有修改获取成本、预算、评价指标或数据划分。

## 这次搜索说明了什么

轨迹预测的主指标下降，但没有建立主动取证的优势。硬筛选仍保留 170 个相容机制，实际初始权重的有效机制数只有 1.000385，最大权重 0.999808。移除组合目标的 NoCombination 与最终方法的 test AUC 完全相同。

过程预测还有代价：dev Brier 从 0.1893 变为 0.2421（越低越好）。因此不能把群体轨迹拟合改善写成机制恢复或个体行为拟合改善。当前最重的机制参数为 [0.4166666567325592, 0.6833333373069763, 0.41999998688697815]；候选权重基本退化成一个模型。

固定 SinglePoint 对照按原有过程误差加轨迹误差选点，与本次接受的校准目标不同。因此，即使本方法分数低于该对照，也不能据此声称“集合优于单点”。NoSharing 同时改变参数共享方式与先验，也有混杂因素。

这是同一小型合成世界上的 60 次开发集搜索，不是 60 份独立验证。冻结后只运行了一次完整测试套件；在读取测试分数后没有继续修改算法。单次合成测试不足以证明跨领域有效性、MIT 榜单兼容性、真实数据有效性或论文创新性。真正保密的外部评测仍未实现。

## 可复核文件

- `provenance/campaign60/summary.json`：摘要、分数与提交。
- `provenance/campaign60/hypotheses.jsonl`：提交前的假设。
- `provenance/campaign60/trials.jsonl`：60 轮候选、裁决、运行时间和原始结果位置。
- `provenance/campaign60/experiments.tsv`：完整账本快照；根 experiments.tsv 保留原始追加记录。
- `provenance/campaign60/dev.json` 与 `test.json`：最终完整对照/消融结果。
- `paper/20261014T054247Z-c010344b/` 与 `paper/20261014T054254Z-092b064c/`：各三张 Booktabs 表和曲线 PDF/PNG。
- `provenance/campaign60/integrity.json`：60 个 method-only 提交、50 个回退引用、固定底座与 2,077 个 legacy 文件的核验。

原项目审计仍仅出现原先记录的两处 Git refs 差异，受检查源码没有新增差异。收尾时一次清单读取因 Windows 默认 GBK 解码失败；改为明确 UTF-8 后校验通过。该读取失败没有改变实验结果或文件，单独记在完整性记录中。

## 逐轮账本

| 轮次 | 假设 | dev AUC | 裁决 | 提交 |
|---:|---|---:|---|---|
| 1 | Training-trajectory soft weighting reduces bias from equally weighting poorly fitting compatible mechanisms | 0.02103133 | keep | `9004e27` |
| 2 | Test trajectory kernel width 0.025: stronger training-fit weighting may reduce prior predictive bias | 0.01612103 | keep | `6bb9ddb` |
| 3 | Test trajectory kernel width 0.015: stronger training-fit weighting may reduce prior predictive bias | 0.01106276 | keep | `73386c1` |
| 4 | Test trajectory kernel width 0.008: stronger training-fit weighting may reduce prior predictive bias | 0.00996100 | keep | `728d215` |
| 5 | Test trajectory kernel width 0.004: stronger training-fit weighting may reduce prior predictive bias | 0.00954380 | keep | `ba8b306` |
| 6 | Test trajectory width 0.002: locate training-fit concentration versus mechanism-diversity tradeoff | 0.00776780 | keep | `d5e58c8` |
| 7 | Test trajectory width 0.001: locate training-fit concentration versus mechanism-diversity tradeoff | 0.00734499 | keep | `ef86a46` |
| 8 | Test trajectory width 0.003: locate training-fit concentration versus mechanism-diversity tradeoff | 0.00921580 | discard | `73f16c4` |
| 9 | Test trajectory width 0.006: locate training-fit concentration versus mechanism-diversity tradeoff | 0.00969213 | discard | `478719a` |
| 10 | Test evidence posterior temperature 0.05: overcome concentration using informative independent audit records | 0.01102639 | discard | `05f5dcf` |
| 11 | Test evidence posterior temperature 0.1: overcome concentration using informative independent audit records | 0.01080275 | discard | `b4c4fca` |
| 12 | Test evidence posterior temperature 0.25: overcome concentration using informative independent audit records | 0.00780723 | discard | `3088266` |
| 13 | Test evidence posterior temperature 0.5: overcome concentration using informative independent audit records | 0.00734522 | discard | `b4fe2a0` |
| 14 | Test prior mixture floor 0.001: retain compatible-mechanism diversity rather than effectively collapsing to one fit | 0.00735953 | discard | `3df239c` |
| 15 | Test prior mixture floor 0.005: retain compatible-mechanism diversity rather than effectively collapsing to one fit | 0.00741803 | discard | `25afcf5` |
| 16 | Test prior mixture floor 0.01: retain compatible-mechanism diversity rather than effectively collapsing to one fit | 0.00749185 | discard | `4b1e757` |
| 17 | Test prior mixture floor 0.03: retain compatible-mechanism diversity rather than effectively collapsing to one fit | 0.00779464 | discard | `bff1fc7` |
| 18 | Test process-fit energy strength 50.0: disjoint passive process observations may resolve trajectory-fit ambiguity | 0.00734499 | discard | `ff4fbbf` |
| 19 | Test process-fit energy strength 200.0: disjoint passive process observations may resolve trajectory-fit ambiguity | 0.00734499 | discard | `dbba10b` |
| 20 | Test process-fit energy strength 500.0: disjoint passive process observations may resolve trajectory-fit ambiguity | 0.00734499 | discard | `e09f641` |
| 21 | Test process-fit energy strength 1000.0: disjoint passive process observations may resolve trajectory-fit ambiguity | 0.00734499 | discard | `35d2997` |
| 22 | Test strong process-fit energy 10000.0: earlier process terms were dominated by the sharply concentrated trajectory fit | 0.00734499 | discard | `99e2128` |
| 23 | Test strong process-fit energy 50000.0: earlier process terms were dominated by the sharply concentrated trajectory fit | 0.00734499 | discard | `0a72bd0` |
| 24 | Test historical channel weights (1.0, 0.25, 1.0): calibrate process-sensitive occupancy channels at a different relative scale | 0.00734499 | discard | `2721c24` |
| 25 | Test historical channel weights (1.0, 4.0, 1.0): calibrate process-sensitive occupancy channels at a different relative scale | 0.00737358 | discard | `6ebab02` |
| 26 | Test historical channel weights (1.0, 1.0, 0.25): redistribute fit emphasis across state trajectories without target labels | 0.00734499 | discard | `0cae7ed` |
| 27 | Test historical channel weights (1.0, 1.0, 4.0): redistribute fit emphasis across state trajectories without target labels | 0.00734532 | discard | `7292291` |
| 28 | Test historical channel weights (0.25, 1.0, 1.0): redistribute fit emphasis across state trajectories without target labels | 0.00739139 | discard | `037df88` |
| 29 | Test historical channel weights (4.0, 1.0, 1.0): redistribute fit emphasis across state trajectories without target labels | 0.00734499 | discard | `d83f2e1` |
| 30 | Test worst_event training-fit objective: protect the least-fitting historical event under shared parameters | 0.00704311 | keep | `98d6fb0` |
| 31 | Test worst_channel training-fit objective: avoid hiding a poorly fitted state channel in the average | 0.00734499 | discard | `bc4d425` |
| 32 | Test absolute training-fit objective: reduce sensitivity to stochastic historical trajectory outliers | 0.00738014 | discard | `55a1b8f` |
| 33 | Test huber training-fit objective: retain local quadratic fit while reducing leverage of large residuals | 0.00734523 | discard | `f29e090` |
| 34 | Trim largest ten percent of historical residuals to reduce simulator-noise leverage | 0.00751265 | discard | `07fe993` |
| 35 | Emphasize settled historical states rather than early transient fit | 0.00734499 | discard | `4e8b0ca` |
| 36 | Broaden worst-event calibration kernel to retain nearby robust mechanisms | 0.00706689 | discard | `f929916` |
| 37 | Further broaden robust calibration kernel to test uncertainty versus bias | 0.00823951 | discard | `f7fee7e` |
| 38 | Sharpen worst-event calibration to test whether the retained neighboring mechanisms help prediction | 0.00704303 | keep | `6a44dfc` |
| 39 | Test smooth worst-event risk 1e-05: avoid selecting mechanisms by one noisy historical event | 0.00704303 | discard | `9007fd6` |
| 40 | Test smooth worst-event risk 0.0001: avoid selecting mechanisms by one noisy historical event | 0.00734499 | discard | `4612d6b` |
| 41 | Test smooth worst-event risk 0.0005: avoid selecting mechanisms by one noisy historical event | 0.00734499 | discard | `7702d9c` |
| 42 | Test probe-coordinate exponent 0.5: reweight prediction dimensions while preserving exact binary covariance identity | 0.00704303 | discard | `6ff50b7` |
| 43 | Test probe-coordinate exponent 1.0: reweight prediction dimensions while preserving exact binary covariance identity | 0.00704303 | discard | `eb9bd17` |
| 44 | Test probe-coordinate exponent -0.5: reweight prediction dimensions while preserving exact binary covariance identity | 0.00704303 | discard | `8361b7a` |
| 45 | Test probe-coordinate exponent -1.0: reweight prediction dimensions while preserving exact binary covariance identity | 0.00704303 | discard | `be36314` |
| 46 | Test posterior temperature 0.1 after robust event calibration: isolate evidence-update effects under the new prior | 0.00704304 | discard | `871658d` |
| 47 | Test posterior temperature 0.75 after robust event calibration: isolate evidence-update effects under the new prior | 0.00704303 | discard | `f7077c6` |
| 48 | Test posterior temperature 2.0 after robust event calibration: isolate evidence-update effects under the new prior | 0.00704303 | discard | `320da5d` |
| 49 | Test posterior temperature 8.0 after robust event calibration: isolate evidence-update effects under the new prior | 0.00704303 | discard | `945ecb9` |
| 50 | Test diversity floor 0.001 with robust event calibration: check whether evidence selection helps a deliberately nondegenerate ensemble | 0.00704964 | discard | `34ebfd4` |
| 51 | Test diversity floor 0.01 with robust event calibration: check whether evidence selection helps a deliberately nondegenerate ensemble | 0.00711002 | discard | `72363f1` |
| 52 | Test diversity floor 0.05 with robust event calibration: check whether evidence selection helps a deliberately nondegenerate ensemble | 0.00739650 | discard | `39cf814` |
| 53 | Test diversity floor 0.1 with robust event calibration: check whether evidence selection helps a deliberately nondegenerate ensemble | 0.00782675 | discard | `307cd3d` |
| 54 | Test seed-marginal whole-path kernel width 0.003: account for finite-seed uncertainty instead of treating mean rollouts as exact | 0.00802215 | discard | `c34f927` |
| 55 | Test seed-marginal whole-path kernel width 0.006: account for finite-seed uncertainty instead of treating mean rollouts as exact | 0.00829448 | discard | `a7e246c` |
| 56 | Test seed-marginal whole-path kernel width 0.012: account for finite-seed uncertainty instead of treating mean rollouts as exact | 0.01073823 | discard | `3c56dc0` |
| 57 | Test seed-marginal whole-path kernel width 0.024: account for finite-seed uncertainty instead of treating mean rollouts as exact | 0.01507502 | discard | `b4ee347` |
| 58 | Test training-noise variance floor 1e-05: downweight stochastic trajectory dimensions in robust historical calibration | 0.00543199 | keep | `eb641c2` |
| 59 | Test training-noise variance floor 0.0001: downweight stochastic trajectory dimensions in robust historical calibration | 0.01300248 | discard | `1b4c940` |
| 60 | Test training-noise variance floor 0.001: downweight stochastic trajectory dimensions in robust historical calibration | 0.00704303 | discard | `135f671` |
