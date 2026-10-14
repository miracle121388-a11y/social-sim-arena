# 决策

2026-10-14：按用户要求精简工作区。可再生缓存删除；有独立信息的旧代码、文档、结果及失败记录统一归档，避免凭主观判断丢失研究证据。归档内部结构和文件内容不变，根目录仅保留新阶段入口及本地基础设施。

不重写 V2 开题报告，不把校园限定为研究范围。用户已确认 Auto Research 指自动化科研方法。以 program.md 作为后续科研循环入口，无需安装特定插件。

2026-10-14 AutoResearch v0：用户明确指定根目录文件结构，覆盖此前 src/njusim/research 布局约定；原项目只读和 legacy 冻结不变。采用 Karpathy 单文件迭代范式，使用 codex/autoresearch-v0 分支和有限首批预算。新建 .venv-research 安装 torch 2.7.1+cu126 及五项所需依赖，精确环境在 requirements.lock.txt。

校验阶段独立固定对照组，防止 method.py 演化连带更改基线。取证池限定为可获取记录；历史/评价缺失值仍被边缘化或屏蔽。两个早期基础设施锁和所有运行结果均保留；最终锁在 infrastructure.lock.json。没有根据 dev 分数调整阈值或掩盖效果不佳。

偏移规则用于诊断模型失配；低分歧并不代表可靠。取消共享使用独立事件参数库，也改变先验，论文必须说明这一混杂因素。MIT 只建立通用数据契约，不虚构官方兼容性。

2026-10-14 完成 60 轮循环：用户最新指令覆盖旧 3 轮上限，延长本地状态预算；固定 program/evaluator/cache/lock 原样保留。每轮先记假设、提交 method.py、评测，再按 1e-8 改善阈值决定 keep/discard。只在 60 轮结束后冻结方法并读取 test，没有根据 test 再调参。

保留第 58 轮：训练种子方差加权 + 最差历史事件校准。主指标改善，但模型几乎单点化，个体过程 Brier 变差，移除组合目标没有损失。将其记录为校准结果，而非主动取证方法的成功证据。收尾文档提交在搜索结束之后，不计入 60 轮。

2026-10-14 用户要求停止搜索并收尾。冻结算法及原评测底座，新增 closure_evaluate.py 独立扩展层，不修改黄金指标。原缓存三活动有关联，补充 24 个独立世界，按世界而非时间格或随机种子重采样。保留原 SinglePoint，同时增加同校准 MAP 以消除选点目标混淆；增加同先验取证对照，避免将校准收益误记为取证收益。补充模拟器只改变真值等待/传播规则，无偏移逐张量匹配原模拟器。

用户给出 socialsim.org/docs.html 后只读核对官方协议，固定上游版本 7002f435a89bd42ec0cc55d5e05dcfa1ad9c7f4c。它需要真实任务的预测及及时提交，不将合成 AUC 转写为官方成绩。本次只准备离线格式辅助，不注册、不部署、不提交。

2026-10-14 论文依据已封存证据撰写，不执行新搜索或修改冻结算法。采用既定 canonical test/supplement 而非挑选最低测试分；所有结果文件仅登记、不重复计为独立样本。明确区分 pooled 与 macro AUC，matched-prior 与原混杂对照；协方差恒等式不作为新理论，批量假设分支不声称一般次模性，二元缺失不冒充右删失模型。直接检查事件配置发现训练冲突开关全部为零，正文披露该覆盖限制。按用户明确要求新建 paper/ 工程，原编辑器 PAPER_TABLES.tex 保持不变；多文件工程使用本地 pdfLaTeX/BibTeX 编译。

2026-10-14 用户请求中文版供审阅，新增 main_zh.tex 与 sections_zh/，保留完整正文和负结果，不覆盖英文稿或原逻辑摘要。字体使用本机宋体、黑体、仿宋和楷体文件并嵌入 PDF，消除 Fandol 字体脚本警告；未修改实验与算法。


## 2026-10-14 Round 2：已完成并冻结

用户授权的新分支 `exp/v2-non-collapsed` 已完成 30 轮有效实验：3 KEEP、27 REVERT、0 运行失败。最优为 R05 / `0d094ecdf021a9def8daf6d5f38ada0e6cc9686d`，method SHA256 `5125975a933bf283ddc117a67f82e0a9e7d726aac3d21a39a0651796b92f6e48`。本轮搜索已结束，不再修改算法或根据测试结果调参。

独立高分歧基准满足预检：固定机制对历史 RMSE 0，组合 RMSE 0.280944；原 V1 缓存和源代码快照保持不变。新基准有 256 agents、200 candidates、8 rollout seeds、12 steps，12 dev / 24 test worlds；测试世界是相同组合设计的新实现，不是额外的新组合或真实域迁移。V2 开发 AUC 0.0756868720，初始 ESS 26.447500，B16 Brier 0.174162686；所有 KEEP 护栏通过，30 次 fast_dev 用时 6.00--7.09 秒。

冻结测试：V1 AUC 0.1438880861 / ESS 1.014551；V2 AUC 0.0577634424 / ESS 26.447500，B0->B16 RMSE 0.133194521->0.039475828，B16 Brier 0.174377561。同先验 AUC 相对 Random / Entropy 改善 50.11% / 56.63%。V2 测试 AUC 95% 世界 bootstrap 区间 [0.04947585,0.06688226]。各活动及配对区间均保存；不能把相关活动和时间步当作独立样本。

边界：Full 与 ParamIG 完全持平；批量幻想分支消融不改变选择；ESS 下限 8--24 在最终核宽下均未触发，不能把改善全部归因于温度下限。证据池刻意包含已知 p=.5 的高熵无关可用性记录；这是合成压力测试，不证明通用策略优势、真实数据成效或官方榜单成绩。初始 V2 Brier 劣于 V1，但取证后更好。原场景 V1 ESS 1.000385 与新场景 1.014551 不得混写。

证据：`experiments_v2.tsv`、追加的 `experiments.tsv`、`provenance/v2/`；完整 30 次 Git 源码、决策、拒绝 refs 与 30 组逐活动统计已核对。固定环境见 `infrastructure.v2.lock.json`；协议见 `provenance/v2/protocol.md`。V1 原版记录位于 `provenance/v2/v1_snapshot/`，其可复现发行包仍在 `dist/njusim-frozen-research.zip`。

阅读 `ROUND2_RESULTS.md`，中英文论文第 4.5 节位于 `paper/sections/05_round2.tex` 和 `paper/sections_zh/05_round2.tex`。中文版从 PDF 第 10 页开始，英文版从第 11 页开始。使用 `reproduce_round2.ps1` 或 `.sh` 复现冻结版本和论文；不要将旧 V1 锁直接应用到新的基础设施。新结果仅为 tested_synthetic，validated_real 仍为空。
