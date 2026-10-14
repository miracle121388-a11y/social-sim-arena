# Social Simulation Arena 接入核对

核对日期：2026-10-14。用户指定入口：[socialsim.org/docs.html](https://socialsim.org/docs.html)。
接口版本固定到上游提交 `7002f435a89bd42ec0cc55d5e05dcfa1ad9c7f4c`；URL、文件摘要与版本记录在
`provenance/closure/arena-sources.json`。本次只读取公开文档并做本地检查，没有注册、发布服务或发送预测。

## 与当前研究任务的关系

该 Arena 评测现实人群的未来观测。主要输出为总体预测分布、多个群体单元的联合画像、排名；
相应指标包括 CRPS、Energy Score、排名距离。官方榜单结果依赖合规的预测提交与后续真实结果发布。
本地“证据预算—活动轨迹 RMSE AUC”没有直接的榜单对应字段。[任务与评分说明](https://socialsim.org/docs.html#scoring)

因此 `MIT_Benchmark_Adapter` 这个旧类名不能视为已经接入该 Arena。校园的报名、候补和到场人数，
不能通过改名转成民意、消费预期或群体画像。即使输出 JSON 合法，也不能据此声称模型具备这些任务的预测能力。

## 已完成的离线准备

`src/njusim/adapters/socialsim_arena.py` 提供纯本地的 `response(request, forecast)`：
检查三种已覆盖答案类型、正标准差、完整群体单元、排名长度与去重，以及请求给定的截止时间。
它接收调用方已经生成的领域预测，不会从校园缓存造出答案，也不是完整的 JSON Schema、签名或服务验证器。
另含 normal CRPS 单元核对；使用文档的已发布算例检查数学实现，不把算例成绩登记为参赛成绩。

这些检查依据 `ssa-agent-api-v2` 的[接口契约](https://github.com/Social-Atoms/social-sim-arena/blob/7002f435a89bd42ec0cc55d5e05dcfa1ad9c7f4c/docs/agent-api.md)。
通用张量接口保留用于今后的领域数据映射；本次不修改冻结的 `method.py`。

## 正式接入仍需完成

1. 选择具体 Arena 任务及目标人群。建立对应的状态、机制、过程证据和输出变量，明确哪些微观证据实际可获得。
2. 用带发布时间的数据做历史回放；训练/开发/时间外测试按任务分开。重建过程必须遵守各题的信息截止，
   不能用如今更新后的历史序列冒充当时可见的数据。当前仓库没有执行这一步。
3. 单独确定分布输出如何映射到官方评分；保留官方持久性基线。活动 AUC 作为方法研究指标单列。
4. 选择 HTTPS endpoint 或签名提交途径，准备真实参赛身份与运行环境。在部署前用上游官方工具检查传输、
   三种答案类型和幂等行为。当前只测试了本地格式，尚未通过官方 endpoint probe。
5. 在用户明确要求实际注册、部署或提交后执行公开操作；当前没有可提交的真实 Arena 预测。

接口的 `lock_at` 应当作为输入读取，不硬编码每周或“发布前 48 小时”的通用规则。
同一上游版本的 schema 描述还保留旧的周批次文字，而截止说明已经解释恢复逐题关闭；
未来上线必须以实际题目和有效协议为准。[截止说明](https://github.com/Social-Atoms/social-sim-arena/blob/7002f435a89bd42ec0cc55d5e05dcfa1ad9c7f4c/docs/submission-window.md)

## 提交状态

| 对象 | 状态 | 本研究包能够提供的内容 |
|---|---|---|
| 合成机制研究 | tested_synthetic | 冻结算法、独立世界重复、消融、公式、全部实验轨迹 |
| SocioVerse 官方赛道 | NOT_EVALUATED | 可复现方法材料；尚无官方数据评测成绩 |
| Social Simulation Arena | NOT_EVALUATED | 具名协议核对、本地格式检查、接入差距说明 |
| 真实人群/跨领域有效性 | 未验证 | 不能由合成缓存推断 |

这不是换一套输出字段就能完成的接入。需要一个新的领域实验，而本次收尾任务保持当前方法和已封存结论不变。
