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

## 最新阶段：完整论文已写完

paper/main.pdf 为 17 页英文全文，paper/main.tex 和 sections/ 是源文件，paper/paper_zh.md 是中文核心逻辑对照。paper/paper-source.zip 是可独立 TeX 编译的源码包。再生成图表运行 paper/generate_artifacts.py；编译 paper/build.py；证据检查 paper/validate_evidence.py，使用 .venv-research/Scripts/python.exe -I -B。脚本从研究根目录运行，不改 method.py。

qa/compilation.json 和 qa/evidence-validation.json 记录编译及 60 候选/38 组统计核验，qa/review.json 记录逐页检查。原 source refs 两处差异仍是既有差异。论文引用已核查的一手资料，严格披露集合近单点、无主动取证优势及官方未评测状态。当前是中性匿名稿，不应声称已套用具体届次官方模板；后续若调整论文请只改 paper/，不得为改善叙事回头调已解封测试。

## 最新交付：完整中文版

paper/main_zh.pdf（15 页）可直接阅读；main_zh.tex 与 sections_zh/ 是对应源码。原 paper_zh.md 仍是核心逻辑摘要，勿混称全文。中文表格与图分别在 tables_zh/、figures_zh/，生成脚本 generate_zh_assets.py，编译脚本 build_zh.py。当前源码依赖 C:/Windows/Fonts/ 下的宋体/黑体/仿宋/楷体及 XeLaTeX；PDF 已嵌入字体，可独立阅读。英文 main.pdf、main.tex、PAPER_TABLES.tex、method.py 哈希均保持不变。编译与中英文一致性核验在 qa/zh/。
