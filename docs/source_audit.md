# 原项目只读审计

访问日期2026-10-09；SOURCE_ROOT=`D:\Users\Lenovo\Desktop\NJU-xianlinSWM`；Git HEAD=`b01975506de3a36b1bdcbc15ac188b6357e39582`。以下路径相对SOURCE_ROOT，行号来自本轮静态读取。源码优先于历史文档。没有运行、导入、测试或调用原项目服务。

| 链路 | 代码证据 | 已找到的能力、依赖和限制 |
|---|---|---|
| 原校园入口 | `frontend/lib/world-request.ts`；`serving/api.py:915`；`world/engine.py:43`；`campus/api.py:13` | API委派 world/Concordia；校园app移除部分旧事件/城市入口，不能将所有模块称为当前界面能力。FastAPI与前端代码存在，待隔离运行验证。 |
| 事件分流与时间 | `campus/event_scope.py:28`、`:110`、`:121`；`campus/event_time.py` | regex识别招新，explicit_facts识别物理约束，其他进入open_forecast；时间窗与明确人数校验；这并非单一通用事件内核。 |
| 自然语言条件 | `concordia_backend/scenario_v4.py:176`、`:354` | compile_scenario调用Provider生成结构化条件，ground核验覆盖；需要模型、校园地点与世界配置；未复跑解析准确性。 |
| 人物选择 | `concordia_backend/population.py:38`、`:88`、`:170`；`personas/catalog.py:43`、`:241` | 过滤、事件相关日程排序、网络增长、特定路径均匀抽样；profile/corpus/图依赖Arrow、NumPy；CATALOG_SIZE=5000、synthetic标签有代码证据，实际文件行数未读。 |
| 局部观察 | `concordia_backend/situated.py:136`、`:271`；`situated_world.py:163`、`:296` | 可见场所属性、私有预算/日程/记忆、递送消息与观测；full bank不是全局容量保证。源码有实现，未对原运行实例动态验证。 |
| Jev/LLM | `concordia_backend/situated.py:288`、`:354`、`:372`；`jev.py:38`、`:150`；`core/config.py:82` | Jev官方SDK system_one(state, questions, model)，默认jev-1.13.0；typesafe-sdk==0.7.1。LLM结构化分布也走个体抽样；缓存、限流、预算和失败处理已有；真实调用需要凭据和预算。 |
| 意图与结算 | `situated.py:463`；`situated_world.py:526`、`:757` | 稳定顺序结算、acquire容量和预算、apply_plan计划执行、到达和资源失败；不同旧policy规则类仍保留。 |
| 状态反馈与传播 | `situated_world.py:149`、`:265`、`:296`、`:718`；`social.py:74` | 事件账本、反馈触发、delayed delivery、clock advance；social-v5按已存在合成联系人传播，记忆由Concordia组件管理；非真实关系网络验证。 |
| 日志／报告 | `concordia_backend/engine.py:561`；`situated_report.py:10`、`:129`；`world/engine.py:295` | 持久化run、轨迹、replay、场景快照；situated由run.metrics/执行账本汇总。SQLite检查点、磁盘缓存和输出路径均有副作用，未运行。 |
| 模型宏观综合 | `campus/open_forecast.py:203`、`:287` | conditional_reactions从个体分布算均值；模型 complete生成Forecast内estimates/timeline/followups，经来源、时间和算术校验后仍为情景估计，不是执行计数。 |

## 独立执行路径与宏观数字

1. **物理校园事件**：event_scope检测explicit_facts → situated-v4 → SituatedRules/SituatedWorld，场所可用性、容量、预算、行程执行和服务分钟由环境结算；situated_report按runs.metrics汇总。
2. **社团招新**：event_scope:121起把请求设为independent、legacy-v1、decision_model=llm、horizon=1、单次journey选择。假定人物已看过完整通知。recruitment_outcomes:195的sample_count来自抽样选择；application_rate是模型分布的逐人均值，reach_scenarios再乘300/600/1000的情景触达规模。后者是条件期望外推，不是执行日志里的报名/排队/到场人数，也不是模型直接写出的最终数字。
3. **开放事件**：open_forecast.configure与social-v5决策/合成图递送可产生真实“执行计数”（在模拟内）；但outcomes另外调用模型生成外部影响/阅读等情景范围。二者不能互换。其他legacy/adaptive/deliberative分支保留用于历史恢复。
4. 仓库还含 `event_forecasting/`、`city/`、`simulation_v2/`、`research/` 与旧 `studies/persona_signal/`，属于独立/研究/历史路径；未假设为当前校园主界面入口，未沿用其既有结果。

`engine.persist:570–584`使用连续if：open_forecast/recruitment报告之后，在adaptive策略时还会被相应outcomes覆盖。因此报告归属必须同时看event_plan.kind与simulation_policy，不能只看事件名称。

## 复用清单

| 文件／模块 | 本轮处理 | 许可／运行条件 |
|---|---|---|
| `core/ids.py` | 普通文件复制至legacy_snapshot；未改字节 | stdlib；项目pyproject声明Apache-2.0，bundled license保留；用户明确允许必要本地复用 |
| `concordia_backend/choice_sampling.py` | 同上；新内核经窄包装调用 | 只依赖ids；1200组模块parity通过，不代表全系统parity |
| `licenses/swm-LICENSE.txt` | 原样复制 | 保留来源与版权声明；公开再分发前仍需审阅来源权属 |
| Jev缓存／Provider／SQLite检查点 | 仅参考接口和职责；未复制执行 | 耦合Settings、密钥、缓存、线程及费用管理；原系统整个baseline暂缺 |
| SituatedWorld、事件计划、人物catalog | 只读参考，新内核独立实现所需最小机制 | 依赖Concordia、NumPy、Pydantic、场所/人口/图资产；未审定整条数据链可发布性 |
| 3D、字体、图片、原人口、数据库、现有轨迹 | 不复制 | 首轮不需要；避免依赖、许可与敏感性扩大 |

所有实际复制的源绝对路径、HEAD、SHA256、目的、许可见provenance/reuse_manifest.json。快照无源路径import、无硬链接／软链接。B0全系统因依赖图、人口与场所输入尚未隔离而未运行；不能用新内核或抽样parity冒充B0。

## 原目录完整性范围

374个受控小型代码／文档／配置文本的SHA256，769项受控遍历文件的size/mtime，Git HEAD、index、refs哈希与porcelain状态。初始有两处tracked修改及多项untracked文件。源与上级路径未发现reparse point；Git root确认为原目录，上级不是Git仓库；受控遍历仅发现原根.git。

不读取秘密值/生产数据库；排除数据、巨型资产、依赖、隐藏缓存等目录。排除树内的嵌套repo/link不作全量保证，也不访问它们。哈希不证明排除内容不变；未安装OS只读ACL，避免改动原项目与影响并行工作。新离线runner有进程级写路径和网络审计钩子，不能等同OS沙箱。没有发现受控范围变化，核验记录见provenance/isolation_checks/。

受控内容扩展名白名单为`.py/.ts/.tsx/.mjs/.md/.toml/.yml/.yaml/.css/.jinja2/.txt`且小于2MB，并排除疑似秘密名称。JSON/CSV/二进制等仅在未排除树中记录元数据，不作内容一致保证。初始广泛扫描中断后，正式基线从scripts/isolation.py的受控扫描开始；此之前也只有只读查询和新目录创建。
