# 标准版 V3 / V0 基线实测

代码基线：`494ddf9`；算法 SHA256：`3551eea8b92707f76232e7b226ac93fdbecd3ff9fd52ec1614ef2ca295d16ba7`。
本次初始化一个预先指定的 V0，没有开启 AutoResearch 搜索。测试集尚未解封。

## 基准与先验

候选总数 200。正确历史乘积层内有 25 种不同的预测机制，结合四种无关审计倾向后为 100 个历史相容候选。
其历史两两 RMSE 最大值为 0.000000；组合探针最大分歧 0.256035，测试设计最大分歧 0.233434。这些是直径，不表示每一对都超过 .18。
初始 ESS=100.000000；合并无关参数后，预测机制 ESS=25.000001。五个主动策略的先验逐元素完全相同。
32 个潜在微观事件各有四条带噪审计记录；同事件记录相关。所有方法使用相同的精确条件似然，MCAR 缺失不当作负例。
取证成本为 0.5、1、2；预算按成本累计，逐世界核对未超支、未重复购买同一记录。

## 同先验开发集结果

| 方法 | AUC | 与 Full 的差值 95% 区间 | Full 相对改善 |
|---|---:|---|---:|
| Full | 0.085854 | [0.000000, 0.000000] | 0.00% |
| Random | 0.114701 | [0.018774, 0.038381] | 25.15% |
| Entropy | 0.112174 | [0.018172, 0.033367] | 23.46% |
| ParamIG | 0.102989 | [0.010982, 0.022901] | 16.64% |
| Standard_OED | 0.113458 | [0.013829, 0.039571] | 24.33% |
| NoBatch | 0.086398 | [-0.001362, 0.002231] | 0.63% |
| NoProbes | 0.113458 | [0.013829, 0.039571] | 24.33% |
| SinglePointMAP | 0.082177 | [-0.024840, 0.013866] | -4.47% |
| NoSharing | 0.123833 | [0.019226, 0.053858] | 30.67% |

上表区间来自 12 个独立模拟世界的配对 bootstrap（2000 次）。相关活动不当作独立样本；区间未作多重比较校正。NoSharing 是结构模型消融，不属于五个相同联合先验的主动策略。

| 成本预算 | 0 | 2 | 4 | 8 | 12 | 16 |
|---|---:|---:|---:|---:|---:|---:|
| Full RMSE | 0.134855 | 0.103518 | 0.093676 | 0.077701 | 0.073469 | 0.073028 |

Full 最终过程 Brier=0.193683。快速评测 7.63 秒，完整开发消融 6.40 秒；均为实际本机测量，不保证任意机器耗时。

## 必须保留的负结果与适用边界

- 批量条件化真实减少了同批同事件取证比例：Full 17.9%，NoBatch 42.9%。但 AUC 改善仅 0.63%，配对区间跨零，不能宣称显著预测收益。
- 预先固定的 MAP 平局处理得到 AUC 0.082177，数值上优于 Full，差值区间跨零。这次真值下单点估计没有出现预想的失败；没有更换真值、种子或 MAP 选点规则让它输。
- NoProbes 更差；NoSharing 更差，但后者仍用有限联合粒子近似独立参数，需要与无限粒子的理想因果消融区分。
- 初次 NoSharing 的历史筛选导致先验边际偏差 .37/.32/.32。该实现与结果完整保存在 pre_balance/。随后仅修正分层平衡采样；当前三活动的初始边际总变差均为 0。Full、其他对照、真值文件和算法逐项保持不变。
- 高熵噪声与无关参数记录是明确构造的压力条件，不能推出任何真实证据池上 Full 必然获胜。
- 当前是合成开发验证，尚无 V3 测试成绩、真实数据验证、SocioVerse 或 MIT 官方成绩。现有论文仍报告 V1/V2，不把本次开发结果改写成已确认的论文结论。

## 复现与证据

```powershell
.\.venv-research\Scripts\python.exe -B evaluate.py --split dev --mode fast_dev
.\.venv-research\Scripts\python.exe -B evaluate.py --split dev --mode full_paper_ablation
.\.venv-research\Scripts\python.exe -I -B tests/test_standard_v3.py
.\.venv-research\Scripts\python.exe -I -B scripts/report_standard_v3.py
```

默认缓存已经生成。prepare_and_cache.py 拒绝覆盖已冻结的 V3 缓存，防止误删实验；首次替换前的 V1 缓存位于 provenance/v3/previous/data/rollout_cache.pt。
V1/V2 的完整原版本可从 exp/v2-non-collapsed / dac68e8 或 dist/v2-before-v3.zip 取得。
主结果：`results/v3/dev-fast_dev-b99c5cb68dc8.json`；消融：`results/v3/dev-full_paper_ablation-30421d8b3efe.json`。
图：`results/v3/v0_budget_and_ablations.svg`；核验：`provenance/v3/validation.json`；冻结协议：`provenance/v3/protocol.md`。
