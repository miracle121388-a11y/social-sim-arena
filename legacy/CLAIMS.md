# 主张台账｜2026-10-10

| ID | 主张 | 状态 | 证据 | 限制 |
|---|---|---|---|---|
| C01 | 2026-10-09受控核验通过；2026-10-10相对旧基线有两处内部refs差异 | tested_synthetic（限定历史工程核验） | provenance/source_manifest.json；proposal-20261010-start/end.json | 当前非全部Git一致；文本/元数据/HEAD/index/status未报差异，未还原；非全盘证明 |
| C02 | 同一内核运行S1/S2/S3，局部信息与资源契约可测 | tested_synthetic | artifacts/acceptance-v1/smoke；test-acceptance.log | 30 synthetic人物，不能推广现实有效性 |
| C03 | 冻结sampler与窄包装输出一致 | tested_synthetic | artifacts/legacy_parity.json，1200组 | 非完整B0 |
| C04 | 固定响应与输入可以重建全部状态/微日志 | tested_synthetic | 各smoke/replay.json、缓存重执行测试 | 不保证live API重现；无中途崩溃恢复 |
| C05 | 新内核官方包装不重复推进并保留微日志 | tested_synthetic | artifacts/adapter-acceptance | 限定官方commit、cold-run、一outer round；非原系统包装 |
| C06 | 三种校准目标与事件/S3场景留出可执行 | tested_synthetic | acceptance-v1/pilot；fixtures.py；experiments.py | 两离线后端/指定DGP；S3同时新增peer/conflict，非纯组合泛化证明；非真实收益 |
| C07 | 同一个训练聚合数可对应不同过程参数 | tested_synthetic | artifacts/identifiability.json | 单一总量/有限网格示例，不是正式可识别性定理 |
| C08 | 经过程+轨迹约束的共享机制改善真实新事件/组合预测 | proposed | 尚无真实证据 | 必须允许无提升或退化；不是已成立方法结论 |
| C09 | 人格或记忆改善真实行为预测 | proposed | 无 | 不预设有效，需真实标签与消融 |
| C10 | Jev/LLM插件接口可替换 | implemented | src/njusim/backends.py；fake client测试；SDK0.7.1源码核对 | 无live运行，无真实校准结论 |
| C11 | 论文原创性、真实因果机制、获奖/录用 | proposed（未建立） | 无 | 模块化、记忆、概率校准、回放不自动创新；不承诺结果 |

状态只允许依据新证据升级。当前没有任何validated_real项；proposed不是已提交或已证实。原系统旧报告和作者论文数字不可写为本项目独立验证。

## 材料状态（非行为有效性主张）
C12：两页提案审阅稿已生成并通过PDF检查（implemented），证据为output/pdf/nju-track-c-proposal-20261010-review.pdf及artifacts/proposal-20261010/validation.json。未提交，数据渠道/团队/报名状态待确认。材料制作不增加validated_real项或实验样本数。

C13：正式提交版提案已完成（implemented），证据artifacts/proposal-submit-20261010/validation.json；取代审阅稿作为用户上传用PDF。材料完成不等于比赛已提交或真实行为已验证。

## V2新增主张｜2026-10-11

| ID | 主张 | 状态 | 证据 | 限制 |
|---|---|---|---|---|
| C14 | 经验相容集合、取证控制、缓存与预算AUC接口可运行 | tested_synthetic | artifacts/v2-tests-20261011-01.log | 无置信覆盖或真实授权证明，进程内oracle非安全边界 |
| C15 | 二元协方差评分与显式枚举一致 | tested_synthetic | artifacts/v2-numpy-20261011-01.json | 1000组随机/5组边界；有限混合、固定目标、正确条件概率；非新定理 |
| C16 | 新方法模块可接入既有原生内核 | tested_synthetic | artifacts/v2-preparation-20261011-01 | 9候选/6保留/85推演/2取证；构造型、同质查询，无封存预算评测 |
| C17 | V1回归结果保持 | tested_synthetic | artifacts/v2-regression-20261011-01 | 原生S1/S2/S3及pilot；未重跑官方适配，未增加支持模式 |
| C18 | 主动取证提高独立新组合或跨领域的数据效率 | proposed | experiments/v2/*.json；docs/V2_RESEARCH_PLAN.md | 尚无完整预算对照、跨领域或真实有效性结果；validated_real=0 |
