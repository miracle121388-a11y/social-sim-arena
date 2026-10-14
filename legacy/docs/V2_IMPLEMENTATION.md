# V2 模块与复现入口

源码位于src/njusim/research，独立于V1的calibration.py；后者保持原样，不改成同名目录。

| 文件 | 职责 |
|---|---|
| hypotheses.py | 带来源/版本/训练误差的候选集合、经验阈值筛选、有效候选数 |
| acquisition.py | 标准库二元协方差评分、显式枚举、候选权重更新、行为熵/信息增益 |
| acquisition_numpy.py | 可选NumPy评分；使用已有.venv-socioverse，不增加原生依赖 |
| evidence.py | learner可见查询元数据、预算、权限、机会、历史版本及揭示记录 |
| evaluator.py | 演示专用SyntheticOracle；不声称OS或进程隔离 |
| probes.py | 版本化探针缓存、机制均值与种子方差、分区检查、等事件权重预算AUC |
| preparation.py | 接入现有内核的构造型演示；不是完整V2实验 |

方法层只接受数字向量与通用标识。只有preparation.py依赖现有场景；未来领域适配应遵循V2_RESEARCH_PLAN.md的接口职责，不把其校园字段传播到评分器。

## 运行

所有命令在D:\Users\Lenovo\Desktop\njusim-contest执行，批次/文件名必须未用过：

```powershell
Set-Location 'D:\Users\Lenovo\Desktop\njusim-contest'
.\.venv\Scripts\python.exe -I -B run.py test
.\.venv\Scripts\python.exe -I -B scripts\prepare_v2.py --batch v2-next-preparation
.\.venv-socioverse\Scripts\python.exe -I -B scripts\verify_v2_numpy.py artifacts\v2-next-numpy.json
.\.venv\Scripts\python.exe -I -B run.py all --batch v2-next-regression
```

已执行记录：
- artifacts/v2-tests-20261011-01.log：50项测试通过。
- artifacts/v2-numpy-20261011-01.json：1000组随机对照、5组边界；NumPy 2.5.3。
- artifacts/v2-preparation-20261011-01：冻结准备配置、候选、缓存、构造配对、已揭示证据和summary。
- experiments/registry.csv：运行状态；失败不得覆盖。

准备性桥接中的训练与探针均为合成，并不提供封存测试集。训练初始证据仅取两个初始时刻的view记录；后续查询限定同一时刻其他个体的view机会，在给定候选条件下独立这一构造假设下更新。真实顺序过程或相关人群不能套用此概率表。

缓存键包含候选、后端、内核、人口、规则、目标schema/尺度、种子及流版本。当前缓存为进程内对象，准备性运行将结果导出JSON；尚无跨运行加载/校验服务。多个随机种子的期望是Monte Carlo估计，不是精确期望；方差及尾哈希另记。

## 四份实验配置的使用

experiments/v2/*.json是待人审的协议模板，而非可直接运行的结果配置。status=proposed和human_reviewed=false必须保留到真正冻结时。新的完整实验runner应拒绝未冻结配置；目前prepare_v2.py只运行独立的准备性示例，不消费这些模板。禁止把模板的预算格点或实验名称登记为已跑结果。

回归核对：artifacts/v2-regression-20261011-01的smoke汇总和完整pilot evaluation与acceptance-v1逐项一致；原12模块文本哈希和3冻结文件原始字节哈希一致，见准备批次verification.json。核验范围不包括原项目被排除的数据/数据库等资产。
