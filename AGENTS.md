# Auto Research 工作区规则

开始前读 PROJECT_CONTEXT.md、STATUS.md、DECISIONS.md、SESSION_HANDOFF.md、CLAIMS.md、AUTORESEARCH.md 和 experiments/registry.csv。

唯一写入根目录为 D:\Users\Lenovo\Desktop\njusim-contest。每条命令显式设置 cwd；写入、移动和删除前校验路径，不穿越链接、junction 或硬链接。环境、缓存、临时文件、数据库和日志均留在这里。

D:\Users\Lenovo\Desktop\NJU-xianlinSWM 永远只读。禁止执行或导入其中代码、安装、测试、构建、Git 修改、数据库连接、服务、通知、写日志或改 ACL。不要恢复或重置用户改动。

legacy/ 是旧阶段参考档案。不要改写原始实验、失败记录、开题报告和 vendor 核心。legacy/legacy_snapshot 必须保持字节一致；原清单在 legacy/provenance/reuse_manifest.json，路径相对于 legacy/。迁移清单在 provenance/legacy-migration.json。旧脚本的根路径假设需要复核，不直接执行旧启动命令。

研究面向跨领域多智能体社会模拟，校园只是首个工程例子。核心问题是机制歧义下的预算化过程证据选择，以及共享机制校准、可观测过程和闭环轨迹约束。保留 V1 被动校准作为基线。按用户本轮明确指定，新的可演化方法集中在根目录 method.py，固定环境/适配器在 prepare_and_cache.py；不恢复旧代码布局。

Auto Research 指自动化科研方法。执行 program.md 的有限循环，不默认联网、调用 API 或启动无限循环。付费模型、真实学生数据、注册、上传、发布和联系他人需要新的明确用户指令。

实验先冻结评价标准、预算、种子和保留集，再运行。记录失败；禁止修改旧轨迹、看到测试结果后改测试标准。B0/B2 缺失就是缺失，不用替代品冒名。区分 proposed / implemented / tested_synthetic / validated_real；目前无真实数据验证或跨领域有效性结论。进程内合成 oracle 不是安全评估边界。

关键阶段运行 .\.venv\Scripts\python.exe -I -B scripts/isolation.py <唯一文件名>.json，报告原项目差异但不回滚。结束时更新上下文、状态、决策、主张、登记表和交接。不要创建原项目分支或 worktree。

## AutoResearch v0 执行规则

本轮用户已授权安装列明依赖、运行合成缓存与评测、在研究仓库首次提交。研究循环只能编辑 method.py；固定文件由 infrastructure.lock.json 校验。具体 Git 状态机和预算见 program.md。原项目只读边界不变。
