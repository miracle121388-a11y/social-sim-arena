# 交接

最新任务：用户要求完整可跑的 AutoResearch 框架、实际 GPU 基线分数及第一次提交。四个指定主文件、Git 控制器和测试已建。正式 dev_auc_error=0.02579135；快速评估 5.49 秒；完整结果见 provenance/baseline-v0-final.json。

先读 program.md。算法研究只允许修改 method.py；固定底座已哈希封存。原始缓存一次生成，不覆盖。测试前必须通过 autoresearch.py freeze-test；当前尚未做测试集评价，不应为了出图提前解封。

使用 autoresearch.py status 查看当前基线状态；init 只用于首次提交后的单次初始化，不要重复初始化。后续研究指令通过 trial 启动候选实验。初始上限 3 次，连续失败 2 次或总计 45 分钟停止。控制器不内置 LLM、不跨会话调度。十四项测试已通过，含真实 Git 过渡测试；测试 fixture 仅在 .tmp，不是研究结果。

失败记录：首轮 argsort 参数兼容错误及缓存缺失保存在 provenance/bootstrap_failures.json 和结果登记中。早期 AUC 0.01968210 是尚未限制查询可获取性的搭建版本；正式结果 0.02579135，不混用。v0 没有建立方法优势，偏移检测漏检也已保留。

legacy 2,077 个文件字节一致；source 审计仅原有两处 refs 差异，没有新增受检查源码变化。根 scripts/isolation.py 使用归档基线；不要执行旧项目或直接运行 legacy 下带路径假设的脚本。
