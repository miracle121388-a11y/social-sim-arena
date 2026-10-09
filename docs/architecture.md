# 原生研究内核 0.1

EventSpec → LocalObservation → DecisionProposal → ActionAttempt → central settlement → AgentState → TransitionRecord → metrics。一个Simulator通过mechanisms配置支持S1/S2/S3；不按场景名分支执行引擎。

`contracts.py`分别定义稳定Persona和动态AgentState。Observation只传递已收到的消息、自己的预算/日程/历史及已知活动；容量和其他人私有状态不传决策后端。未知活动只能看到通知预览。发送/递送/查看分别记日志，理解未观测；不能从view自动生成真实心理标签。

每个通知一次查看机会，每个人对每个活动一次初始参与机会；选择加入后由环境检验预算、时段、名额。已报名或候补的人在获知后至少2分钟有一次撤销机会；成功报名在开场时有一次到场机会。没有永久保持意向的假设，但0.1版本不建模无限重试或多次再报名。报名成功不等于到场。候补是首次报名中事先约定的候补同意，递补时检查预算和冲突。

每逻辑分钟：外部通知排程 → 到达 → 局部查看和决策 → 全部意图冻结 → 取消释放 → 旧队列FIFO递补 → 同时新报名按seed/stream/time/agent/activity哈希抽签 → 分享下一分钟递送 → 到场 → 结束释放 →状态记录。相同时间同一人两个冲突活动的尝试都能提出，由全局抽签顺序与环境日程共同结算。FIFO只对既有候补优先，新一轮同刻顺序不受人物遍历或API返回顺序影响。

概率是固定1分钟逻辑机会的概率。chunk_minutes只改变驱动分组，仍执行每个逻辑边界，不把一个概率按显示步长重复抽样；不同真实时间尺度的风险率模型尚未实现。日程采用带时区的起点和相对分钟，区间左闭右开。

随机键包含stream(run replicate)、agent、logical time、stage、purpose；概率抽样复用冻结legacy sampler，资源排序使用独立allocation命名空间。模型版本与事件干预与随机seed分别记录。同一干预前缀使用同stream。固定第三方响应可回放；不能声称第三方live API由seed逐字复现。

日志采用追加式内存事件序列与独占创建的JSONL落盘，hash chain检查篡改，保存完整旧/新状态、证据引用、原始/校准概率、缓存引用、模型版本和随机键。`replay_trace`验证链并重建状态；另用冻结响应缓存重执行整个内核逐条比对。当前原生日志在正常完成时落盘，尚无崩溃中途持久化恢复保证。官方store逐步持久化panel，但完整sidecar仍需运行完成。禁止把此局限隐去。

宏观counts和各时点registered/waiting/attended/revenue从日志构造，没有模型改写数字。registered是当前占用，admitted是累计成功入队含递补，attended是累计实际到场；结束后的0占用不能当作0到场。价格整数单位，扣费计入环境revenue；取消全额返还，结束释放名额但不退费。各时点预算总额+revenue恒等初始总额。

低参数候选：跨事件共享join/cancel两个logit偏置，通用softmax接口支持互斥候选；interest_weight可配置但首轮固定0。9点有限网格、L2两档由开发事件选取。联合目标是平均阶段NLL+人口归一化轨迹MAE+L2；这不是已证实的新算法。共享参数与测试组合的区分贡献尚需真实数据。分组偏差、无共享消融、风险率、事件级统计区间仍列待办。

官方适配为Path C：共享Session在decide_batch内执行一个完整原生分钟，env.apply只验证其完成并投影，不再次扣款、推进时间或更新原生记忆。外层面板不能完整表达微事件，因此sidecar保留全部。仅支持interaction_rounds=1和cold run；拒绝warm_start。不修改官方Core、不访问原项目。
