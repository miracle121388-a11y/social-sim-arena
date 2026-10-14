# 主张边界

已完成 / tested_synthetic：60 个不同候选的固定 dev 评测、10 次接受和 50 次回退；全部代码提交仅涉及 method.py；14 项回归测试通过。最佳 dev AUC=0.00543199；冻结后一次 test AUC=0.00691577。

主指标下降不能解释成主动取证或机制恢复有效。初始权重有效机制数约 1.0004，NoCombination 的 test AUC 与完整方法相同；dev Brier 从 0.1893 变差到 0.2421。SinglePoint 对照采用不同的选点目标，不能用其差值证明集合优势。

未验证：真实数据、跨领域稳定性、任何 MIT 榜单、SocioVerse 官方评测成绩、顶会创新性。B0/B2 旧有缺失没有被新名字替代。没有 validated_real 结论。本地哈希与接口限制不是保密执行沙箱。

## 2026-10-14 补充结果

Full 的 24 世界 macro-event AUC=0.00706354 [0.00602473,0.00809948]，这是不同于原 pooled AUC 的补充指标。MatchedMAP=0.00706548；NoCombination 与 NoBatchDedup 均与 Full 相同。同先验 Random=0.00705892，无 Full 取证优越的证据。

未知候补与传播规则检出率低，不能称为可靠越界检测。独立世界置信区间条件于固定训练数据、证据和三个模板，不是跨域有效性。22 项本地测试不等于 Arena 官方接入认证。官方 SocioVerse / MIT Arena 仍 NOT_EVALUATED。

## 2026-10-14 论文主张审计

英文全文完整、可编译（17 页），并非全部正向研究假设得到验证。当前贡献为明确的问题与实现、缓存化取证计算验证、匹配对照和集合坍缩边界分析。无官方 SocioVerse/MIT 成绩，无真实数据验证，无 SOTA 声明，无一般次模保证，无右删失实现。开发已经出现组合；训练历史没有启用冲突，所以不声称纯粹全组件已见、组合全开发未见的严格泛化。完整源码与真实图表不等于已满足具体会议模板/篇幅或录用标准。

2026-10-14 中文全文仅为英文论文的语言转换，公式、表格数值和科学主张不变，没有新增真实验证或官方成绩。


## 2026-10-14 Round 2：已完成并冻结

用户授权的新分支 `exp/v2-non-collapsed` 已完成 30 轮有效实验：3 KEEP、27 REVERT、0 运行失败。最优为 R05 / `0d094ecdf021a9def8daf6d5f38ada0e6cc9686d`，method SHA256 `5125975a933bf283ddc117a67f82e0a9e7d726aac3d21a39a0651796b92f6e48`。本轮搜索已结束，不再修改算法或根据测试结果调参。

独立高分歧基准满足预检：固定机制对历史 RMSE 0，组合 RMSE 0.280944；原 V1 缓存和源代码快照保持不变。新基准有 256 agents、200 candidates、8 rollout seeds、12 steps，12 dev / 24 test worlds；测试世界是相同组合设计的新实现，不是额外的新组合或真实域迁移。V2 开发 AUC 0.0756868720，初始 ESS 26.447500，B16 Brier 0.174162686；所有 KEEP 护栏通过，30 次 fast_dev 用时 6.00--7.09 秒。

冻结测试：V1 AUC 0.1438880861 / ESS 1.014551；V2 AUC 0.0577634424 / ESS 26.447500，B0->B16 RMSE 0.133194521->0.039475828，B16 Brier 0.174377561。同先验 AUC 相对 Random / Entropy 改善 50.11% / 56.63%。V2 测试 AUC 95% 世界 bootstrap 区间 [0.04947585,0.06688226]。各活动及配对区间均保存；不能把相关活动和时间步当作独立样本。

边界：Full 与 ParamIG 完全持平；批量幻想分支消融不改变选择；ESS 下限 8--24 在最终核宽下均未触发，不能把改善全部归因于温度下限。证据池刻意包含已知 p=.5 的高熵无关可用性记录；这是合成压力测试，不证明通用策略优势、真实数据成效或官方榜单成绩。初始 V2 Brier 劣于 V1，但取证后更好。原场景 V1 ESS 1.000385 与新场景 1.014551 不得混写。

证据：`experiments_v2.tsv`、追加的 `experiments.tsv`、`provenance/v2/`；完整 30 次 Git 源码、决策、拒绝 refs 与 30 组逐活动统计已核对。固定环境见 `infrastructure.v2.lock.json`；协议见 `provenance/v2/protocol.md`。V1 原版记录位于 `provenance/v2/v1_snapshot/`，其可复现发行包仍在 `dist/njusim-frozen-research.zip`。

阅读 `ROUND2_RESULTS.md`，中英文论文第 4.5 节位于 `paper/sections/05_round2.tex` 和 `paper/sections_zh/05_round2.tex`。中文版从 PDF 第 10 页开始，英文版从第 11 页开始。使用 `reproduce_round2.ps1` 或 `.sh` 复现冻结版本和论文；不要将旧 V1 锁直接应用到新的基础设施。新结果仅为 tested_synthetic，validated_real 仍为空。
