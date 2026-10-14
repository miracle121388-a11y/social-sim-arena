# AutoResearch Round 2：非坍缩取证实验

当前分支 `exp/v2-non-collapsed` 已完成并封存 30 轮搜索。最优方法为 `0d094ec`，初始有效机制数 26.45，开发 / 测试 AUC 为 0.07569 / 0.05776；同先验测试 AUC 比 Random / Entropy 低 50.1% / 56.6%。Full 与 ParamIG 持平，数据仍全部为构造的合成压力测试。

- 结果与限制：[ROUND2_RESULTS.md](ROUND2_RESULTS.md)
- 中文论文：`paper/main_zh.pdf` 第 10 页起，第 4.5 节；英文 `paper/main.pdf` 第 11 页起。
- 冻结复现：`powershell -NoProfile -File reproduce_round2.ps1`，或 `bash reproduce_round2.sh`。不重启搜索。
- 手动评测：`.venv-research/Scripts/python.exe -B evaluate.py --campaign v2 --split test --mode full_paper_ablation`；同缓存 V1 加 `--method-version v1`。
- 证据核对：`.venv-research/Scripts/python.exe -I -B scripts/validate_round2.py`。
- 全部候选：`experiments_v2.tsv`；固定协议与历史快照：`provenance/v2/`。

V1 的旧缓存、实验和研究包保持不变。以下保留的是 **V1 历史说明**；其旧锁和根目录命令不适用于已升级的 V2 分支。V1 可复现发行包为 `dist/njusim-frozen-research.zip`。

---

# Frozen social-simulation research package

研究问题：历史总量相近的不同微观机制，面对新的事件组合可能给出不同预测。本项目实现相容机制校准、按组合预测分歧选择过程证据、完整轨迹混合预测。校园活动只是首个合成实例。**全部实证结果目前均为合成测试，不是 SocioVerse 或 MIT 官方成绩。**

AutoResearch 已停止。最优算法提交为 `eb641c22eb197d038696894a5e6857d31002af78`。
`method.py` 固定 SHA256：`b8389adc234ee11e923d59084eaeb83b3821986c5f2f714c9ad5a84ed14650af`。
收尾脚本只读取它；复现不运行搜索、不重建缓存、不注册或上传任何内容。

## 先看结果

- 封存 test：归一化预算—群体轨迹 RMSE AUC **0.00691577**；本次重跑一致。
- 24 个独立世界补充评测：macro-event AUC **0.00706354**，95% CI **[0.00602473, 0.00809948]**。两种 AUC 的聚合顺序不同，不能混成一个指标。
- 有效机制数约 1.0004。MatchedMAP 与 Full 几乎相同；去掉组合目标或批量去冗余，结果不变。同先验随机取证没有输给 Full。当前证据主要支持校准改善，不支持主动取证优越性。
- 未知等待、传播规则的告警检出率低；强交通冲击更容易被发现。完整失败结果也已保留。

| 材料 | 位置 |
|---|---|
| 公式、Algorithm 1、60 轮演化分析、适用边界 | [PAPER_METHOD_AND_INSIGHTS.md](PAPER_METHOD_AND_INSIGHTS.md) |
| 逐活动区间、完整消融、告警、速度比 | [补充结果](provenance/closure/paper/RESULTS.md) |
| 三组 Booktabs 表格 | `provenance/closure/paper/experiment1.tex`、`experiment2.tex`、`experiment3.tex` |
| 独立活动曲线 PDF/PNG、机器可读指标 | `provenance/closure/paper/` |
| 原黄金评测、补充评测原始 JSON | `provenance/closure/golden-test.json`、`supplement.json` |
| 全部 KEEP/REVERT 与候选原文 | `provenance/closure/evolution-audit.json`、`candidates/` |
| 具名 MIT Arena 接入核对 | [SOCIALSIM_INTEGRATION.md](SOCIALSIM_INTEGRATION.md) |
| 补充实验预定协议 | [CLOSURE_PROTOCOL.md](CLOSURE_PROTOCOL.md) |

## 一键复现

已测试环境：Windows、Python 3.13.9、PyTorch 2.7.1+cu126、RTX 4060 Laptop 8GB。精确依赖在 `requirements.lock.txt`。本次黄金全量测试约 8 秒；补充的 24 世界全套约 32 秒，不适用单次 fast_dev 的 15 秒预算。GPU 首次初始化、机器负载会影响耗时。

当前工作区已安装环境。在 **Git for Windows Bash** 中执行：

```bash
bash reproduce_all.sh
```

PowerShell 可直接执行相同驱动：

```powershell
.\.venv-research\Scripts\python.exe -B reproduce.py
```

流程：核对算法/底座/缓存摘要 → 全部单元测试 → dev fast_dev 复现 → test full_paper_ablation → 原图表 → 独立世界及补充消融 → 补充图表 → 再次核对摘要。每次输出新文件，失败日志也保留在 `results/reproduce-<time-id>/`。`--golden-only` 可跳过独立世界补充；默认完整运行。运行时无需联网。将 `RESEARCH_PYTHON` 指向已有环境也可运行 Bash 脚本。

压缩包已经带上冻结缓存，不需要执行 `prepare_and_cache.py`；该命令会拒绝覆盖已有缓存。不要为了重跑修改缓存、锁文件或 `method.py`。新机器应保留 Windows 环境；被冻结的 `workspace.py` 使用 Windows 路径属性检查，**当前没有宣称 Linux/macOS 可运行**。

### 新的 Windows 环境

先安装 Python、Git for Windows 和合适的 NVIDIA 驱动。在解压目录中安装依赖（此步骤需要网络）：

```powershell
New-Item -ItemType Directory -Force .tmp,.cache | Out-Null
$env:TEMP = $env:TMP = (Resolve-Path .tmp).Path
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
uv venv --python 3.13 .venv-research
uv pip install --python .venv-research/Scripts/python.exe --index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cu126 -r requirements.lock.txt
.\.venv-research\Scripts\python.exe -B reproduce.py
```

若不用 uv，可先用 `python -m venv .venv-research`，再用该环境的 pip 安装相同锁定依赖。CPU 可用于正确性复现，但未承诺速度预算或跨设备逐位一致。GPU 软件版本变化可能引起微小数值差异。复现压缩包第一次运行时会在解压目录创建本地 Git 收据提交；它不是原实验提交，原始提交和源码摘要另有记录。

## 文件与实验边界

- **原只读底座**：`prepare_and_cache.py`、`evaluate.py`、`paper_artifacts.py`、`workspace.py`、`autoresearch.py`、`program.md`、依赖和原测试，均受 `infrastructure.lock.json` 约束。
- **冻结算法**：`method.py`。保留历史分支，当前执行的是噪声归一化 worst-event 校准；本次没有为排版或清理改写算法。
- **独立收尾层**：`closure_evaluate.py`、`closure_artifacts.py`、`supplemental_rules.py`。补充新对照和新真值规则，原分数定义不变。无偏移补充模拟器与原模拟器逐张量一致，已有回归测试。
- **离线 Arena 辅助**：`src/njusim/adapters/socialsim_arena.py`，只检查调用方提供的三种预测格式。它不是对应任务的预测模型，也不是线上服务。
- **复现与打包**：`reproduce_all.sh`、`reproduce.py`、`build_research_package.py`。
- 原始工程材料保存在工作区 `legacy/`，其 2,077 个文件保持原样，不放进最小复现包。

原套件包含 Random、Entropy、ParamIG、Standard_OED、SimpleStats、Uncalibrated、ProcessOnly、TrajectoryOnly、PassiveV1、NoSharing、NoCombination、SinglePoint。补充套件新增 NoBatchDedup、MatchedMAP 和四个 SamePrior 取证对照。原套件的 SinglePoint 使用不同选点目标；NoSharing 还改变候选先验，因此均须保留解释限制。NoBatchDedup 仍不允许重复购买同一记录。

## 如何读取不确定性

原缓存的三个活动相互冲突、共享参与者，不是三个独立样本。补充实验生成 24 个独立世界；对每个活动模板有 24 次独立实现。跨活动平均时，bootstrap 重采样整个世界，保留内部相关性。Random 的三个取证种子先在世界内部平均，不能算成 72 个独立世界。

区间条件于固定历史、证据答案和三个模板；它们不涵盖新领域或新训练集的不确定性。90% 预测区间基于候选机制 × 模拟种子的整轨迹混合，是点态预测区间；95% CI 则描述平均误差估计。二者不同。缺失查看不作为否定，过程审计与群体轨迹来自不同群体，汇总人数不重复计入独立似然。

本地缓存含评测真值；摘要核验是完整性审计，不能充当防泄漏的外部沙箱。本次 test 重跑是已开启测试集的复现，不是新的盲测。继续科研必须新建验证计划，不能据此继续挑方法。

## 生成复现包

```powershell
.\.venv-research\Scripts\python.exe -B build_research_package.py
```

默认生成 `dist/njusim-frozen-research.zip` 和 SHA256 校验文件，拒绝覆盖。包内 `PACKAGE_MANIFEST.json` 校验所有打包文件；包含缓存、代码、60 个候选原文与实际评测记录、图表。不包含虚拟环境、API key、原项目、legacy、第三方全文文档。上游文档保留链接及摘要。这是可复现研究材料包；官方报名、提交格式和有效榜单评测仍需按各平台协议另行完成。

AutoResearch 范式参考：[karpathy/autoresearch](https://github.com/karpathy/autoresearch)。SocialSim 文档核对入口：[Social Simulation Arena](https://socialsim.org/docs.html)。
