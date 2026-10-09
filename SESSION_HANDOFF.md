# 下一会话交接｜2026-10-09

**只在 `D:\Users\Lenovo\Desktop\njusim-contest` 开发。** 原目录 `D:\Users\Lenovo\Desktop\NJU-xianlinSWM` 始终只读。当前聊天最初绑定旧目录，本轮所有创建新项目后的命令均明确cwd新目录；后续在Codex打开新目录作为工作区，不依赖旧聊天cwd。不能在旧目录创建记录/分支/环境。

开工先读PROJECT_CONTEXT、STATUS、DECISIONS、CLAIMS、AGENTS与experiments/registry.csv。两原附件保存在provenance/inputs。核心问题与用户边界已继承，不重新发散研究方向。

已交付：独立环境和Git、374文本哈希+769文件元数据/Git状态只读审计、冻结sampler两模块/许可证；S1/S2/S3各30合成人物；32项原生测试；1200组抽样parity；7事件合成校准实验；三场景官方真实循环/DuckDB包装逐条parity。无真实数据/真实API结果，B0完整原系统和B2原始Jev/LLM仍缺。

```powershell
Set-Location 'D:\Users\Lenovo\Desktop\njusim-contest'
.\.venv\Scripts\python.exe -I -B run.py test
.\.venv\Scripts\python.exe -I -B run.py all --batch next-session-01
.\.venv-socioverse\Scripts\python.exe -I -B studies\nju_compositional_simulation\run.py next-adapter-01
.\.venv\Scripts\python.exe -I -B scripts\isolation.py next-check.json
```

batch必须未使用。实际最终验收：artifacts/acceptance-v1、artifacts/adapter-acceptance、artifacts/test-acceptance.log。失败：pilot-v1/failure.json，全部说明docs/failures.md。官方固定commit9c3ac77，依赖锁requirements-socioverse.lock.txt。原生无需任何第三方库。

先做三件事：
1. 和用户确认真实活动过程数据的可得性与授权/审批路径，人工审核并冻结事件、风险集、可观测标签及组合保留设计；未经授权不采集真实学生数据。
2. 补齐任务匹配的B0完整隔离基线和B2授权响应缓存；先查输入/许可/依赖/预算，再做公平同环境对照。当前两离线后端不能冒充真实模型。
3. 完成独立事件、无共享/无过程/无闭环消融及可识别性/充分性与群集不确定性评估，按证据修订提案、报告和演示。

限制：原生日志完成时落盘，暂无崩溃恢复；官方warm-start/外层多round拒绝；配置尚无人类科学审核；合成seed范围不是实证CI；出版/后续投稿条款待查。官网提案截止10月12日23:59 UTC+8、终稿10月31日同时间；报名/上传未执行。所有主张遵循proposed/implemented/tested_synthetic/validated_real，当前validated_real=0。

结束时更新事实源、claims和registry，再复核源受控范围；若有差异报告即可，绝不擅自还原用户文件。
