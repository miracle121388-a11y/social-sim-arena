# 状态

2026-10-14：Autonomous Research Loop 完成并封存。

- 60 轮有效实验；10 keep，50 discard，0 crash。每个候选只改 method.py。
- 最佳算法提交：eb641c2（第 58 轮）。dev AUC=0.00543199，冻结后 test AUC=0.00691577。
- 14 项测试通过。固定底座哈希和 2,077 个 legacy 文件校验通过。
- 最佳模型有效机制数约 1.0004；过程 Brier 变差。不能声称主动取证有效。
- 测试集已按程序在最后解封，方法已冻结。本轮不得继续调参；不要重置实验计数或覆盖结果。

详细报告：RESEARCH_REPORT_60.md。账本与结果快照：provenance/campaign60/。真实数据、MIT 具名适配和安全外部评测仍未验证。

## 2026-10-14 收尾验证

- method.py SHA256 仍为 b8389adc234ee11e923d59084eaeb83b3821986c5f2f714c9ad5a84ed14650af。搜索未继续。
- 请求的 test full_paper_ablation 与 paper_artifacts 已运行；test AUC=0.00691576924873516。
- 24 个独立世界、每模板 24 个活动实现，按世界 bootstrap；完整补充消融和压力测试完成。
- 22 项测试通过；Git for Windows Bash 的 reproduce_all.sh 全流程通过。
- 2077 个 legacy 文件一致；原项目 374 个受控源码无新增变化，仍有两处既有 Git 内部引用差异。
- 原始结果、全部候选与逐活动报告见 provenance/closure；复现包生成器与 README 已完成。
- LaTeX 表格源码已生成，内置编译器未返回，不能声称 PDF 表格编译验证通过；曲线 PDF/PNG 已生成并目视检查。

复现包已在全新解压目录用 Bash 完整运行通过，22 项测试及 24 世界统计与原工作区完全一致；校验见 provenance/closure/package-validation.json。

## 2026-10-14 论文交付

- 完整英文稿及中文逻辑对照在 paper/；17 页 PDF 编译无警告、无未解析引用，矢量图和公式排版已检查。
- 76 份结果已登记；60 次 Git/账本决定一致；38 组逐活动/宏平均统计及区间已重新计算。
- method.py、10 个锁定文件、2077 个 legacy 文件保持一致；PAPER_TABLES.tex 未改。原项目 374 个受控源码无新增差异，仅两处既有 Git refs 差异。
- 论文明确报告集合坍缩、同先验取证无优势、较弱未知规则漏检；官方成绩仍 NOT_EVALUATED。
- 完整稿采用中性匿名会议风格；不是某届会议的官方模板或已获接收的论文。

## 2026-10-14 中文译稿

15 页中文全文已用 XeLaTeX/BibTeX 编译，最终零警告并逐页渲染检查。12 张表的数字与英文版逐行一致，全部展示公式及章节标签一致，3 张图已中文化。核验见 paper/qa/zh/verification.json；原项目审计仍仅两处既有 refs 差异，374 个受控源文件无新增变化。


## 2026-10-14 Round 2：已完成并冻结

用户授权的新分支 `exp/v2-non-collapsed` 已完成 30 轮有效实验：3 KEEP、27 REVERT、0 运行失败。最优为 R05 / `0d094ecdf021a9def8daf6d5f38ada0e6cc9686d`，method SHA256 `5125975a933bf283ddc117a67f82e0a9e7d726aac3d21a39a0651796b92f6e48`。本轮搜索已结束，不再修改算法或根据测试结果调参。

独立高分歧基准满足预检：固定机制对历史 RMSE 0，组合 RMSE 0.280944；原 V1 缓存和源代码快照保持不变。新基准有 256 agents、200 candidates、8 rollout seeds、12 steps，12 dev / 24 test worlds；测试世界是相同组合设计的新实现，不是额外的新组合或真实域迁移。V2 开发 AUC 0.0756868720，初始 ESS 26.447500，B16 Brier 0.174162686；所有 KEEP 护栏通过，30 次 fast_dev 用时 6.00--7.09 秒。

冻结测试：V1 AUC 0.1438880861 / ESS 1.014551；V2 AUC 0.0577634424 / ESS 26.447500，B0->B16 RMSE 0.133194521->0.039475828，B16 Brier 0.174377561。同先验 AUC 相对 Random / Entropy 改善 50.11% / 56.63%。V2 测试 AUC 95% 世界 bootstrap 区间 [0.04947585,0.06688226]。各活动及配对区间均保存；不能把相关活动和时间步当作独立样本。

边界：Full 与 ParamIG 完全持平；批量幻想分支消融不改变选择；ESS 下限 8--24 在最终核宽下均未触发，不能把改善全部归因于温度下限。证据池刻意包含已知 p=.5 的高熵无关可用性记录；这是合成压力测试，不证明通用策略优势、真实数据成效或官方榜单成绩。初始 V2 Brier 劣于 V1，但取证后更好。原场景 V1 ESS 1.000385 与新场景 1.014551 不得混写。

证据：`experiments_v2.tsv`、追加的 `experiments.tsv`、`provenance/v2/`；完整 30 次 Git 源码、决策、拒绝 refs 与 30 组逐活动统计已核对。固定环境见 `infrastructure.v2.lock.json`；协议见 `provenance/v2/protocol.md`。V1 原版记录位于 `provenance/v2/v1_snapshot/`，其可复现发行包仍在 `dist/njusim-frozen-research.zip`。

阅读 `ROUND2_RESULTS.md`，中英文论文第 4.5 节位于 `paper/sections/05_round2.tex` 和 `paper/sections_zh/05_round2.tex`。中文版从 PDF 第 10 页开始，英文版从第 11 页开始。使用 `reproduce_round2.ps1` 或 `.sh` 复现冻结版本和论文；不要将旧 V1 锁直接应用到新的基础设施。新结果仅为 tested_synthetic，validated_real 仍为空。

最终核验：一键 PowerShell 复现通过，英文 19 页 / 中文 18 页，均零编译诊断；30 个候选源码及决策、30 组逐活动统计已独立核对。原项目 374 个受控源文件无新增差异；仅原先已有的两处内部 Git refs 差异，未回滚。完整候选源码已另存 provenance/v2/candidates/，拒绝 refs 也保留。


## 2026-10-14 标准版 V3 / V0：当前默认入口

用户本轮授权重构 prepare_and_cache.py / evaluate.py / method.py 并替换默认缓存。独立分支为 exp/v3-standard-v0，代码基线 494ddf9；算法哈希 3551eea8b92707f76232e7b226ac93fdbecd3ff9fd52ec1614ef2ca295d16ba7。本次没有启动搜索循环，V0 的算法在初次开发评测之后没有改动。

默认 data/rollout_cache.pt 已是 V3；V1 缓存、入口和 V2 方法的字节快照在 provenance/v3/previous/。V1/V2 完整版本保留于 exp/v2-non-collapsed / dac68e8，以及 dist/v2-before-v3.zip。旧锁不适用于当前默认入口，当前锁是 infrastructure.v3.lock.json。legacy 未修改，原项目仍只读。

200 候选中含 25 种不同预测机制、100 个历史相容候选，历史两两轨迹最大 RMSE 为 0；组合探针 / 测试设计最大分歧 0.256035 / 0.233434。并非所有候选对都相差 >.18。初始 ESS=100，去掉四种无关审计倾向后的预测机制 ESS=25。五个主动对照同一先验，预算按成本 0.5/1/2 累计。32 个潜在事件各有四条相关传感记录，使用条件联合似然而非重复独立计数；MCAR 缺失被边缘化。

V0 开发 Full AUC 0.085853629；B0->B16 RMSE 0.134855404->0.073028207，在 [0,2,4,8,12,16] 上单调下降。Random/Entropy/ParamIG/Standard_OED AUC 为 0.114701/0.112174/0.102989/0.113458，Full 相对改善 25.15%/23.46%/16.64%/24.33%，配对 95% 世界 bootstrap 区间均大于零（未作多重比较校正）。最终 Brier 0.193683，快速运行 7.63s，完整开发消融 6.40s。

必须保留负结果：NoBatch AUC 0.086398，差值区间跨零；同批同事件比例 42.9% 对 Full 17.9%，说明机制分支确实生效，但没有显著预测收益。MAP AUC 0.082177，数值优于 Full，差值区间也跨零；没有人为更换平局规则让其失败。NoProbes 0.113458，NoSharing 0.123833。NoSharing 最初 800 粒子引入边际先验混杂，原运行与缓存保存在 pre_balance/；修正为 3200 个分层平衡联合粒子（V0 下 400 个非零），三个活动初始边际与 Full 完全一致。联合独立性仍为有限粒子近似。除该结构缓存外，算法、shared 缓存、训练/证据/真值与所有其他策略曲线经校验完全不变。这是一次明确记录的消融正确性修复，不是额外算法搜索。

测试集未解封，未创建 test_release.json。本轮仅 tested_synthetic 的开发验证，不能声称所有核心模块显著有效、SOTA、真实数据验证或官方比赛/MIT 成绩。现有 paper/ 仍是 V1/V2 论文，未把 V3 开发结果偷偷写成测试结论。

结果入口：V3_BASELINE.md；指定运行：provenance/v3/v0.json；8 项科学契约测试通过；scripts/report_standard_v3.py 独立核验全部成本、重复索引、同先验、27 组逐活动统计及修复前后不变性。运行默认 evaluate.py --split dev --mode fast_dev 或 --mode full_paper_ablation。默认 prepare_and_cache.py 已执行，已有冻结缓存时拒绝重复生成。下一步若继续研究，需要新的明确指令；不要直接调用历史 V1/V2 搜索控制器。

原项目 374 个受控源码无新增差异，仅两处既有内部 Git refs 差异；不回滚。
