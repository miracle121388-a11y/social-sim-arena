# 核心实验表（状态必须随实际记录更新）

| 实验 | 控制项与输出 | 状态/证据 |
|---|---|---|
| S1/S2/S3最小闭环 | 同内核、30 synthetic personas；动作/资源/日志/回放 | tested_synthetic；artifacts/first-smoke |
| 抽样模块旧副本parity | 冻结字节 vs 窄包装，1200次 | tested_synthetic；artifacts/legacy_parity.json；非B0 |
| 官方包装parity | 新原生 vs 官方Core包装，微日志逐条比对 | tested_synthetic；artifacts/adapter-v1 |
| B1与未校准offline参照 | 同信息/机制/资源；one-step与free-rollout分别输出 | tested_synthetic；pilot-v2/evaluation.json |
| B3/B4/候选joint | 共享2参数、相同9点网格、开发选L2、测试冻结 | tested_synthetic；pilot-v2/fits；非真实收益 |
| 未见组合/新人 | S3不进入训练开发；新人ID与画像同分布 | tested_synthetic；split_manifest.json；无真实泛化结论 |
| 同聚合量不同过程 | 9点网格，训练到场总数相同但尝试不同，比较S3 | tested_synthetic；artifacts/identifiability.json；不要求全轨迹相同 |
| B0全原系统 | 审核必要依赖和非敏感输入后在副本运行，锁模型响应 | missing；未拿重写版替代 |
| B2真实Jev/LLM | 两个经授权后端，相同预算/局部观察/配对流 | implemented seam only；无凭据读取/无调用 |
| 无共享消融/分组偏差 | 对独立新事件的可部署参数规则预注册，避免测试事件独立拟合 | proposed |
| 真实阶段/完整推演验证 | 至少多个独立事件，真值时点隔离，群集不确定性 | proposed；真实数据0 |
| 画像/网络消融 | 仅在相应真实证据可用时开展 | proposed；不预设人格有益 |

局部指标不可代替闭环指标；单一宏观总量拟合不可代替机制可识别性。正式研究的样本量和检验力需按独立事件规划。
