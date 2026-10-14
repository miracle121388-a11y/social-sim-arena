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

## 2026-10-10 接续异常记录
源隔离开工检查退出码1，因两个Codex内部refs相对旧基线不同；受控文本/元数据/HEAD/index/status无差异。结束检查单独保存，不还原、不重写基线。完整引用路径见provenance/isolation_checks/proposal-20261010-*.json。这不是模拟运行失败。

一次文档记录更新的JavaScript编排因模板字符串中的反引号导致SyntaxError，发生在执行前，未运行shell或写入文件；随后改用结构化载荷完成。两次PDF构建成功，第二次仅增大字号。本轮未新增模拟失败批次。

## 2026-10-10 证据核对方法修正
一次旧验收源码核对误用原始字节SHA256，导致断言失败；不是源码改动证据。run.py实际使用njusim.io.sha(read_text)，即对规范JSON字符串计算SHA256。按原算法重核12项全部一致，冻结3项按原始字节SHA256也全部一致；未改旧清单或源码。失败前事实源写入已完成，失败后补齐validation.json和registry，未重复追加正文。结束源审计仍为相对旧基线的相同两个refs路径差异，未报受控文本/元数据/HEAD/index/status差异。

文档更新初次使用Windows默认文本写出引入CRLF，git diff --check提示行尾空白；已仅将本轮修改的文档恢复为原有LF，未改冻结源码。后续差异检查通过。

2026-10-10提交版源核验仍报告此前相同两处内部refs路径与旧基线不同，未报受控文本/元数据/HEAD/index/status变化，未还原。两次PDF生成成功，第二次为措辞与行末排版调整。

## 2026-10-11 V2准备检查
本轮50项原生测试、1000组NumPy随机检查及准备性联调均通过，未发生新的模拟失败。源旧基线仍有两处既有Codex内部refs差异，独立保存start/end核验，不还原。

保留非有利结果：v2-preparation-20261011-01的两次证据揭示后，实际预测分歧都略增加；期望缩减不保证每次实现值下降，更不代表现实预测误差下降。该合成例查询同质，不能用于声称主动选择优于随机。

原runner产生CRLF的tests-latest与新registry行，普通git diff --check将CR标为行尾空白。本轮用仅命令生效的core.whitespace=cr-at-eol检查；未因此改写实验trace、旧记录或Git配置。
