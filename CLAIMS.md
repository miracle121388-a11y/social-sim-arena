# 主张台账｜2026-10-09

| ID | 主张 | 状态 | 证据 | 限制 |
|---|---|---|---|---|
| C01 | 本轮未改原项目受控文件和Git状态 | tested_synthetic（工程核验） | provenance/source_manifest.json；isolation_checks | 非全盘字节证明；无OS ACL；排除数据/缓存/资产/DB等 |
| C02 | 同一内核运行S1/S2/S3，局部信息与资源契约可测 | tested_synthetic | artifacts/acceptance-v1/smoke；test-acceptance.log | 30 synthetic人物，不能推广现实有效性 |
| C03 | 冻结sampler与窄包装输出一致 | tested_synthetic | artifacts/legacy_parity.json，1200组 | 非完整B0 |
| C04 | 固定响应与输入可以重建全部状态/微日志 | tested_synthetic | 各smoke/replay.json、缓存重执行测试 | 不保证live API重现；无中途崩溃恢复 |
| C05 | 新内核官方包装不重复推进并保留微日志 | tested_synthetic | artifacts/adapter-acceptance | 限定官方commit、cold-run、一outer round；非原系统包装 |
| C06 | 三种校准目标与事件/组合分离评测可执行 | tested_synthetic | acceptance-v1/pilot/fits及evaluation | 仅两离线后端和指定DGP，非真实收益 |
| C07 | 同一个训练聚合数可对应不同过程参数 | tested_synthetic | artifacts/identifiability.json | 单一总量/有限网格示例，不是正式可识别性定理 |
| C08 | 经过程+轨迹约束的共享机制改善真实新事件/组合预测 | proposed | 尚无真实证据 | 必须允许无提升或退化；不是已成立方法结论 |
| C09 | 人格或记忆改善真实行为预测 | proposed | 无 | 不预设有效，需真实标签与消融 |
| C10 | Jev/LLM插件接口可替换 | implemented | src/njusim/backends.py；fake client测试；SDK0.7.1源码核对 | 无live运行，无真实校准结论 |
| C11 | 论文原创性、真实因果机制、获奖/录用 | proposed（未建立） | 无 | 模块化、记忆、概率校准、回放不自动创新；不承诺结果 |

状态只允许依据新证据升级。当前没有任何validated_real项；proposed不是已提交或已证实。原系统旧报告和作者论文数字不可写为本项目独立验证。
