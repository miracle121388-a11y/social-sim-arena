# njusim-contest

独立的可校准、可组合、可验证社会模拟研究原型。**当前证据全部为合成软件/机制测试，真实行为验证为0。** 原南京大学校园模拟器仅作只读参考，本项目没有在其内部开发。

源码参考：`D:\Users\Lenovo\Desktop\NJU-xianlinSWM`  
唯一研发目录：`D:\Users\Lenovo\Desktop\njusim-contest`

## 立即运行

本机独立`.venv`已可用，原生内核仅用Python标准库，无API Key、无网络请求、无端口/服务。请从新目录运行；batch名必须未使用，以保留历史记录。

```powershell
Set-Location 'D:\Users\Lenovo\Desktop\njusim-contest'
.\.venv\Scripts\python.exe -I -B run.py test
.\.venv\Scripts\python.exe -I -B run.py all --batch reproduce-01
```

`all`一键跑30人S1/S2/S3 smoke、回放验证、两后端×四种校准方式的合成训练/开发/测试原型。输出在`artifacts/reproduce-01/`，自动追加experiments/registry.csv；约几十秒，具体取决于机器。首次到别的机器先在**独立新目录**创建环境：`python -I -B -m venv --copies --without-pip .venv`，无需pip安装原生依赖。本轮Python为3.13.9。

自定义冻结配置及日志回放：

```powershell
.\.venv\Scripts\python.exe -I -B run.py simulate --config configs\S3.json --backend statistical --batch custom-02
.\.venv\Scripts\python.exe -I -B run.py replay --trace artifacts\acceptance-v1\smoke\S2\trace.jsonl
.\.venv\Scripts\python.exe -I -B scripts\isolation.py manual-check.json
```

replay命令验证hash chain和状态连续性；smoke额外通过固定响应缓存重新执行，逐条比对。已有目录不覆盖；失败文件保留。主研究EventSpec仍需人工科学审核，见configs/review_manifest.json。

## 本轮已运行验收

- 原生32项测试通过：artifacts/test-acceptance.log、artifacts/tests-latest.json。
- S1/S2/S3各30人；293/275/128条记录；状态还原与缓存重执行均通过：artifacts/acceptance-v1/smoke。
- 抽样模块1200组parity：artifacts/legacy_parity.json，**不等于完整B0**。
- 合成pilot：7个配置事件，2 train/1 dev/4 test，32条评测结果、96个已保存测试rollouts；artifacts/acceptance-v1/pilot。real_events=0，API calls/cost=0。
- 9点参数网格中存在9组同一训练到场总数但过程尝试不同的参数对；artifacts/identifiability.json，仅作合成不可识别性示例。
- 初次pilot调用错误保留在artifacts/pilot-v1与docs/failures.md，修正后pilot-v2和acceptance-v1通过。

## 可选官方适配

独立`.venv-socioverse`已安装锁定依赖。官方vendor固定`9c3ac774816511c121184ca11f539dc398ba1544`，未修改Core。适配的是**本新项目内核**。

```powershell
.\.venv-socioverse\Scripts\python.exe -I -B studies\nju_compositional_simulation\run.py adapter-reproduce-01
```

三场景各330行独立DuckDB面板，完整sidecar与原生逐条一致。输出：artifacts/adapter-acceptance。不支持官方warm_start及外层多round，显式拒绝；不能拿外层panel单独宣称微事件可回放。

复建可选环境时，先把官方仓库克隆到本项目vendor/socioverse2并checkout上述提交，然后在新目录创建`.venv-socioverse`；使用其pip `--isolated install --cache-dir .cache/pip -r requirements-socioverse.lock.txt`。不要从原校园目录获取任何依赖、配置、数据或环境。下载/安装的TEMP/TMP指定到本项目.tmp。基础解释器/标准库来自本机Python安装，仅只读共享，与原校园环境无关。

## 导航与边界

事实源：PROJECT_CONTEXT.md / STATUS.md / DECISIONS.md / SESSION_HANDOFF.md / CLAIMS.md / AGENTS.md / experiments/registry.csv。源码审计：docs/source_audit.md。架构与时间语义：docs/architecture.md。官方规则：docs/competition_rules.md。近邻：docs/novelty_matrix.md。真实数据空模板和协议：data/templates、docs/data_protocol.md。提案、实验表、演示脚本草案：submission/。

B0完整原系统和B2真实Jev/LLM尚缺；live插件只验证了调用形状，默认不联网。沒有真实预测改进、人格收益、因果效应或论文创新的已证实主张。只在新目录写入；进程级防护不是OS只读沙箱，原项目核验范围与排除项见provenance。未读取密钥/生产数据库、未启动原项目、未报名/上传/公开发布。

## V2：机制分歧与预算证据选择（2026-10-11）
校园是首个工程例子；总体研究范围是跨事件、跨规则组合的社会模拟。通用方法代码在src/njusim/research，V1原生实现保留。新增准备性入口：

```powershell
.\.venv\Scripts\python.exe -I -B scripts\prepare_v2.py --batch <new-id>
.\.venv-socioverse\Scripts\python.exe -I -B scripts\verify_v2_numpy.py artifacts\<new-result>.json
```

本轮原生50测试及NumPy1000随机/5边界检查通过；V1回归批次v2-regression-20261011-01通过。准备性联调不等于完整主动学习基准或真实收益。完整后续路线见docs/V2_RESEARCH_PLAN.md，模块与运行说明见docs/V2_IMPLEMENTATION.md。四份experiments/v2协议仍为proposed/未人审。
