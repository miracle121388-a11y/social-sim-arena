# 下一会话交接｜2026-10-11

最新用户要求：校园只是例子，项目面向更广的社会模拟；按V2材料准备后续研发，不再重写开题。请先读AGENTS、PROJECT_CONTEXT、STATUS、DECISIONS、CLAIMS、registry及docs/V2_RESEARCH_PLAN.md。

只在D:\Users\Lenovo\Desktop\njusim-contest写入。原NJU-xianlinSWM只读，冻结legacy_snapshot不改，官方Core不改。当前保留此前未提交的提案文档与用户新附件，不覆盖/还原；本轮也未作Git提交。

## 输入与定位

用户文件开题V2_技术路线与Codex实施补充.md、output/pdf/赛道C_蒋成康_开题提案_优化版V2.pdf已读，未修改。V2问题是历史相容机制存在组合预测分歧时，如何选择有限预算内的过程证据。V1联合校准保留被动基线。不要宣称公式本身新颖，也不要把校园新脚本当作项目目标。

## 本轮已做

src/njusim/research包含hypotheses、acquisition、acquisition_numpy、evidence、evaluator、probes、preparation。方法层不依赖校园字段；preparation是复用旧内核的演示桥。
- 原生50项测试通过：artifacts/v2-tests-20261011-01.log。
- NumPy1000随机/5边界检查通过：artifacts/v2-numpy-20261011-01.json，使用已有.venv-socioverse，无安装。
- v2-preparation-20261011-01：9候选、6保留、15组构造配对、85推演、2取证，完整计划/缓存/揭示日志已保存。
- v2-regression-20261011-01：V1 smoke/pilot通过；smoke尾哈希与旧验收一致。
- docs/V2_RESEARCH_PLAN.md和V2_IMPLEMENTATION.md给出研究范围、接口、工作包和验收。experiments/v2四份配置仍proposed/human_reviewed=false，没有完整V2实验结果。

## 必须保留的限制

当前查询都是完整初始view机会，给定候选条件独立；同质查询不能比较选择策略。两次实际分歧都略增加，未作有利筛选。普通Python私有字段不是安全边界，真实封存评测服务未实现。
探针cache为内存对象+JSON导出，跨运行装载/校验未做；顺序依赖概率、相关批次、潜状态过滤和候选重搜索未做。真实数据/模型/跨领域验证为0；B0/B2缺失。V1内核仍有固定行为契约，不能说已经变成全领域执行器。

## 下轮任务

P0领域接口与目标schema，P1真正封存评测及人审组合划分，P2完整合成预算/失配基准，P3第二领域及授权真实数据。研究计划内候选领域是方向，不是已完成或已获数据；按观测条件选择。不应先扩三维界面或人口规模。
各策略同初始证据/成本/候选/缓存/推演预算，标准预测导向对照允许与协方差法等价。主要预算AUC按事件等权。真实调用、数据访问、报名、上传和联系他人需新指示。

## 运行

cwd必须为独立研究根，批次名必须新：
.\.venv\Scripts\python.exe -I -B run.py test
.\.venv\Scripts\python.exe -I -B scripts\prepare_v2.py --batch <new-id>
.\.venv-socioverse\Scripts\python.exe -I -B scripts\verify_v2_numpy.py artifacts\<new-id>.json
.\.venv\Scripts\python.exe -I -B run.py all --batch <new-id>

原项目旧基线检查仍是两处Codex内部refs不同，受控文本/元数据/HEAD/index/status无差异，见provenance/isolation_checks/v2-prep-20261011-start/end.json。不得还原引用或重置基线。原生JSONL崩溃恢复与官方warm_start/多round限制未变化，未重跑适配。
