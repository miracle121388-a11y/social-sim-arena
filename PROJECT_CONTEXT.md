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
