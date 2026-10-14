# 当前方向

项目研究机制歧义下的预算化过程证据选择，校园仅为首个合成适配例子。原项目 NJU-xianlinSWM 永远只读；旧资产在 legacy。

2026-10-14 已完成用户明确要求的 60 轮 AutoResearch 搜索：固定评测底座，只演化 method.py，按 dev AUC 保留或回退。最佳方案是训练噪声加权的最差事件校准。群体轨迹分数改善，但有效机制集合几乎坍缩，过程预测变差，主动取证收益未建立。

当前方法和本轮测试均已封存，报告见 RESEARCH_REPORT_60.md。继续研究需要新的、独立的验证计划；不能把已读过的 test 继续当未见测试。尚无真实数据或跨领域有效性结论。

## 2026-10-14 封存收尾

用户明确停止搜索，method.py 字节固定。已补齐独立世界重复、NoBatchDedup、MatchedMAP、同先验基线和未知候补/传播规则压力测试；原黄金底座与分数不变。结果、公式与演化讨论见 PAPER_METHOD_AND_INSIGHTS.md，完整材料在 provenance/closure。

具名 MIT 目标现已确定为 socialsim.org 的 Social Simulation Arena，是实时分布/群体画像/排名预测，不是校园轨迹离线榜单。仅完成协议核对和本地格式测试，尚无官方成绩。

## 2026-10-14 完整论文

paper/main.tex 与六个完整章节、中文 paper_zh.md、13 条文献、3 张矢量图、12 张结果/审计表已生成；main.pdf 为 17 页，pdfLaTeX/BibTeX 编译零警告并逐页检查。paper/generate_artifacts.py 读取封存输入，paper/validate_evidence.py 核验原始世界统计和 Git 账本。方法未修改，未继续搜索。

## 2026-10-14 中文全文

paper/main_zh.pdf 为完整中文译稿（15 页），含中文图表、公式、算法与附录，非此前的核心逻辑摘要。英文稿与冻结算法保持不变。


## 2026-10-14 Round 2：已完成并冻结

用户授权的新分支 `exp/v2-non-collapsed` 已完成 30 轮有效实验：3 KEEP、27 REVERT、0 运行失败。最优为 R05 / `0d094ecdf021a9def8daf6d5f38ada0e6cc9686d`，method SHA256 `5125975a933bf283ddc117a67f82e0a9e7d726aac3d21a39a0651796b92f6e48`。本轮搜索已结束，不再修改算法或根据测试结果调参。

独立高分歧基准满足预检：固定机制对历史 RMSE 0，组合 RMSE 0.280944；原 V1 缓存和源代码快照保持不变。新基准有 256 agents、200 candidates、8 rollout seeds、12 steps，12 dev / 24 test worlds；测试世界是相同组合设计的新实现，不是额外的新组合或真实域迁移。V2 开发 AUC 0.0756868720，初始 ESS 26.447500，B16 Brier 0.174162686；所有 KEEP 护栏通过，30 次 fast_dev 用时 6.00--7.09 秒。

冻结测试：V1 AUC 0.1438880861 / ESS 1.014551；V2 AUC 0.0577634424 / ESS 26.447500，B0->B16 RMSE 0.133194521->0.039475828，B16 Brier 0.174377561。同先验 AUC 相对 Random / Entropy 改善 50.11% / 56.63%。V2 测试 AUC 95% 世界 bootstrap 区间 [0.04947585,0.06688226]。各活动及配对区间均保存；不能把相关活动和时间步当作独立样本。

边界：Full 与 ParamIG 完全持平；批量幻想分支消融不改变选择；ESS 下限 8--24 在最终核宽下均未触发，不能把改善全部归因于温度下限。证据池刻意包含已知 p=.5 的高熵无关可用性记录；这是合成压力测试，不证明通用策略优势、真实数据成效或官方榜单成绩。初始 V2 Brier 劣于 V1，但取证后更好。原场景 V1 ESS 1.000385 与新场景 1.014551 不得混写。

证据：`experiments_v2.tsv`、追加的 `experiments.tsv`、`provenance/v2/`；完整 30 次 Git 源码、决策、拒绝 refs 与 30 组逐活动统计已核对。固定环境见 `infrastructure.v2.lock.json`；协议见 `provenance/v2/protocol.md`。V1 原版记录位于 `provenance/v2/v1_snapshot/`，其可复现发行包仍在 `dist/njusim-frozen-research.zip`。

阅读 `ROUND2_RESULTS.md`，中英文论文第 4.5 节位于 `paper/sections/05_round2.tex` 和 `paper/sections_zh/05_round2.tex`。中文版从 PDF 第 10 页开始，英文版从第 11 页开始。使用 `reproduce_round2.ps1` 或 `.sh` 复现冻结版本和论文；不要将旧 V1 锁直接应用到新的基础设施。新结果仅为 tested_synthetic，validated_real 仍为空。
