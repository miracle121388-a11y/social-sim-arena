# 本轮失败与限制记录

| 记录 | 实际问题 | 处理及证据 |
|---|---|---|
| audit-01 | 首次广泛只读遍历未排除`.tools`/`.venv-simulation`等隐藏依赖树，耗时过长 | 中断命令；未生成初始manifest、未执行后续Git/venv命令。改为受控白名单和隐藏树排除，再成功建立基线；没有源写入。 |
| audit-02 | PowerShell不支持shell花括号文件名展开，发生ParserError | 改为明确路径列表；失败命令未运行源代码。 |
| copy-01 | Windows默认GBK读取UTF-8 manifest，UnicodeDecodeError，复制未发生 | 显式UTF-8后复制成功。其后第一次parity因未复制报FileNotFoundError；重试1200组通过。 |
| rules-01 | web文本工具无法读动态赛事规则，GitHub API/build-study路径读取失败 | 动态浏览器读取官网，实际clone官方仓库定位接口；不凭猜测实现。 |
| pilot-v1 | macro_loss把Simulator对象直接传给metrics，TypeError | 修正为sim.records；保留artifacts/pilot-v1/failure.json和pilot-v1-console.log；pilot-v2成功。 |
| B0 | 未隔离原系统完整依赖、场所/人物输入和模型响应 | 标missing，只做冻结抽样模块parity；未把新实现当原系统。 |
| B2/live | 未获API调用/预算授权，也无真实响应缓存 | Jev/LLM注入式插件默认禁用；fake客户端仅验证调用形状。 |
| 真实验证 | 无授权真实过程、轨迹或网络 | 建立空模板和校验接口；真实有效性状态仍proposed。 |
| 官方回放 | 外层panel不含所有原生微动作 | 保留sidecar并拒绝官方warm-start及多round；native缓存回放已测。 |
| 中断恢复 | 原生事件在内存追加、结束时独占落盘 | 不声称具有崩溃后原生恢复；后续需增量日志与事务检查点。 |

失败目录与日志不删除；后续修复使用新的batch，不篡改原始结果。
