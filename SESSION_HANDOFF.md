# 交接

用户要求不间断完成 60 轮有效实验，现已完成：10 keep、50 discard、无实验崩溃。全部候选只改 method.py，失败于改进阈值的提交仍保留在 refs/autoresearch/rejected。

最佳算法提交 eb641c22eb197d038696894a5e6857d31002af78。dev AUC=0.00543199，冻结后的 test AUC=0.00691577。60 轮日志、假设、账本、完整对照和核验结果在 provenance/campaign60，结论见 RESEARCH_REPORT_60.md。

frozen_method.json 已生成。本轮不允许继续试验或覆盖测试封存；当前控制器状态 trials=60/max_trials=60。不要重新 init，不要清空计数以绕过冻结。best_commit 指最后一个算法提交；后续收尾文档提交只记录结果，不是第 61 个候选。

科学结论有限：有效机制数约 1.0004，NoCombination 与完整方法同分，过程 Brier 变差。因此没有主动取证优势或机制恢复成功的证据。下一步若获授权，应重新设计独立验证协议，避免沿用已看过的测试集调参。

14 项测试通过，原项目审计仅旧 refs 差异，legacy 2,077 文件字节一致。收尾清单读取曾因默认 GBK 失败，明确 UTF-8 后核验完成；此操作错误不属于 60 轮实验，记录在 integrity.json。

## 最新用户指令：停止 AutoResearch，保持最优 method.py 不变

收尾工作已完成：原 test 全量复现、24 独立世界扩展、新消融与压力规则、60 轮 Git/账本审计、PAPER_METHOD_AND_INSIGHTS.md、README、一键复现、最小打包器。核对 provenance/closure/verification.json 和完整 RESULTS.md。方法与 infrastructure.lock.json 所列文件没有改动，禁止继续试参。

SocialSim 官方入口已由用户明确提供，见 SOCIALSIM_INTEGRATION.md。它是实时人群预测 Arena；尚未形成相应领域模型，没有官方成绩，也没有提交。不要将现有通用 MIT 类名当成已接入。

复现：Git for Windows Bash 执行 bash reproduce_all.sh，或 .venv-research/Scripts/python.exe -B reproduce.py。打包：同环境运行 build_research_package.py；默认拒绝覆盖 dist/njusim-frozen-research.zip。Windows 平台已测，Linux 未验证。源项目审计仍只有两处既有 refs 差异，不回滚。

可交付压缩包 dist/njusim-frozen-research.zip（约 2.3 MB）已通过全新目录端到端复现。SHA256 见同名 .sha256；包外验证收据同名 .validation.json。
