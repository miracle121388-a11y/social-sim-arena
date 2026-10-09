# 首轮实际交付｜2026-10-09

## 路径与源保护

SOURCE_ROOT：`D:\Users\Lenovo\Desktop\NJU-xianlinSWM`。  
RESEARCH_ROOT：`D:\Users\Lenovo\Desktop\njusim-contest`。  
同级独立目录和Git；无源分支/worktree/源写入，无软硬链接/共享Git对象库。源初始HEAD b01975506de3a36b1bdcbc15ac188b6357e39582，原有两处tracked修改和多个untracked文件保持原样。

最终核验`provenance/isolation_checks/final.json`：374个受控文本SHA256、769项元数据、Git HEAD/index/refs/status未变。未对数据、生产DB、缓存、依赖、巨型资产等排除项做完整字节验证，没有设置OS只读ACL，不能将受控一致扩大为全盘证明。发现并行变化时不还原的规则已写入AGENTS。

## 审计和复用

docs/source_audit.md逐段给出自然语言事件→选人→观察→Jev/LLM→结算→反馈→报告的实际路径。物理校园、招新单次条件选择、开放事件social-v5分流。报告数字分为：执行计数、模型概率的条件期望外推、模型直接生成的情景估计。源码中的5000是合成人物目录声明，没有读取/核实5000份真实个人记录。

只复制core/ids.py、concordia_backend/choice_sampling.py及Apache许可证到legacy_snapshot；绝对源路径、HEAD、SHA256和许可见reuse_manifest。冻结sampler直接调用与新包装1200组一致。B0全系统尚未复现，不拿此测试替代。

## 已运行的最小闭环与测试

同一个新内核、固定10分钟、每场30 synthetic人物、零API调用。下表均为模拟日志计算，不能解释为真实行为验证。

| 场景 | 微日志条数 | 首次报名成功 | 候补递补成功 | 到场 | 状态还原/缓存重执行 |
|---|---:|---:|---:|---:|---|
| S1 通知参与 | 293 | 20 | 0 | 19 | 通过/通过 |
| S2 名额等待退出 | 275 | 5 | 3 | 5 | 通过/通过 |
| S3 同伴/冲突/名额 | 128 | 5 | 0 | 3 | 通过/通过 |

S3该seed不必激活每个稀有约束；另外的可控fixture强制触发容量失败、冲突和递补并通过测试。32项测试通过：未接收信息隔离、未来特征拒绝、容量/预算守恒、重复报名/取消/候补、有效时间窗、不同驱动步长一致、遍历次序一致和抽签覆盖、日志指标、篡改检测与固定响应回放、干预前缀一致、默认live禁用、越界写/网络/子进程拒绝，以及真实数据授权/缺失校验。

官方适配使用固定9c3ac77的真实LongitudinalSimulator及四个ABC，三场景各330行独立DuckDB，完整sidecar分别与新原生293/275/128条微记录逐条相同；重复apply被拒绝。Core warm_start及外层多round暂不支持。没有修改官方核心。

## 已运行的科研原型

两个离线后端×未校准/仅局部/仅宏观/联合，共7个合成事件（2 train、1 dev、4 test），产生32条分模式评测和96个测试rollouts。S3完全从训练开发保留，另设新人事件。阶段NLL/Brier/可靠性分箱与群体轨迹MAE分别记录，模型在开发选择后冻结。没有两个真实模型的已完成实验。合成不可识别性示例发现9组同训练单一总数、不同过程尝试的参数对，不是实际机制恢复。

## 命令与产物

在RESEARCH_ROOT执行：

```powershell
.\.venv\Scripts\python.exe -I -B run.py test
.\.venv\Scripts\python.exe -I -B run.py all --batch reproduce-01
.\.venv-socioverse\Scripts\python.exe -I -B studies\nju_compositional_simulation\run.py adapter-reproduce-01
.\.venv\Scripts\python.exe -I -B run.py replay --trace artifacts\acceptance-v1\smoke\S2\trace.jsonl
.\.venv\Scripts\python.exe -I -B scripts\isolation.py reproduce-check.json
```

以上是可复制的新batch示例；本轮实际batch为acceptance-v1、adapter-acceptance；自定义JSON配置CLI也通过custom-config-v1验收。实际控制台、trace/responses/state/metrics/replay、manifest与锁文件均保存在项目中。原生只需Python标准库，额外适配依赖全在.venv-socioverse；无服务端口、无真实通知。

失败保留：pilot-v1/failure.json及console记录一次metrics参数错误；修复后pilot-v2及最终acceptance-v1通过。此前只读扫描过宽、PowerShell展开、UTF-8/GBK复制失败与首次parity文件缺失均在docs/failures.md，不隐藏为成功。

## 事实源、比赛与下一步

PROJECT_CONTEXT、STATUS、DECISIONS、SESSION_HANDOFF、CLAIMS、AGENTS及experiments/registry.csv均已更新。submission含开题结构、核心实验表及视频脚本草案，未作正式提交材料。提案官网已延期到2026-10-12 23:59 UTC+8；终稿10月31日同时间。材料/接口证据见competition_rules，发表兼容条款未确认。

当前validated_real=0。优先三项：①确认真实过程数据授权与风险集、人工审核冻结事件/组合划分；②补齐完整隔离B0与获授权B2响应；③独立事件/组合消融和群集不确定性评估，按证据完善论文及比赛材料。没有人格/方法必然增益主张，没有报名、上传、公开发布或未授权费用。
