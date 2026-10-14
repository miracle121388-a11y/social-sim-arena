# SocioVerse Challenge 2026 核实记录

访问：2026-10-09，Asia/Shanghai。官方页面的静态提取只显示占位符；本轮另用浏览器加载动态页面并展开“自研框架”FAQ。没有填写报名表或登录提交。

| 项目 | 当前核实结果 | 依据 |
|---|---|---|
| 主赛道 | Track C关注方法/系统瓶颈，需对照说明有效性、代价与适用范围 | [官网tracks](https://socioverse.fudan-disc.com/challenge/#tracks) |
| 提案 | 已调整到2026-10-12 23:59 UTC+8，1–2页PDF；初筛决定额外API支持，不淘汰 | [官网timeline与submit](https://socioverse.fudan-disc.com/challenge/#timeline) |
| 终稿 | 2026-10-31 23:59 UTC+8 | [官网submit](https://socioverse.fudan-disc.com/challenge/#submit) |
| 材料 | 4–8页报告（含图表）、可复现实验包与说明、≤5分钟MP4；线上模式可用平台回放链接 | 同上 |
| 可复现性 | 一键脚本、固定seed、模型/调用量/费用披露、离线和live结果区分；真实真值的获取时间和隔离措施须声明 | 同上 |
| 自研框架 | 可以零改动包装，但必须形成studies结构；技术Path C不是赛事Track C | [官网FAQ](https://socioverse.fudan-disc.com/challenge/#faq)、[官方适配指南](https://socioverse.fudan-disc.com/docs/guides/wrap-legacy-model/) |
| 入口 | 报名确认邮件邀请码注册平台后，经研究目录参赛入口提交 | [研究目录](https://socioverse.fudan-disc.com/studies)；本轮未进入认证页面 |
| 评审 | 可复现性检查后专家评审；五项权重25/25/20/20/10，工程复现项有最低要求 | [官网review](https://socioverse.fudan-disc.com/challenge/#review) |
| 团队 | 正式成员1–5；一个主赛道的一项成果；指导老师另计 | [官网about](https://socioverse.fudan-disc.com/challenge/#about) |
| 数据 | 可公开分享或已获授权，真实个人数据需脱敏 | 官网submit；公开包仍需专项许可核查 |
| 开源许可 | 官方框架Apache-2.0；并不能由此推断参赛者全部资产自动授权公开 | [官方仓库LICENSE](https://github.com/sii-research/SocioVerse2/blob/main/LICENSE) |
| 出版/后续投稿 | 官网确认与LASS交流、优秀作品案例库；未找到明确的论文归档出版及后续投稿兼容条款 | 不把交流/收录案例等同非归档承诺；拟投期刊/会议政策仍待核实 |

日期冲突：2026-10-09读取的官方仓库README News仍列提案10月9日；动态赛事页将其标为旧日期并显示10月12日调整。当前按赛事页处理，保留差异，不静默混合。报名状态、队名、成员、具体子赛道命名均未确认；不自行填造。

技术版本：本轮只在新项目vendor内克隆官方仓库，固定commit `9c3ac774816511c121184ca11f539dc398ba1544`，库0.2.0；依赖锁见requirements-socioverse.lock.txt。实际阅读abc/environment.py、population.py、decision.py、trajectory.py及engine/loop.py、builder.py、schemas。采用Path-C共享Session工厂，不使用不匹配的Path-B通用装配。

官方Core的warm_start明确限制依赖可从保存Action重建状态且interaction_rounds=1；Path-C存在隐含内部状态不能假定支持。本适配显式拒绝warm_start与多轮外层，保留原生微日志sidecar并逐条parity检验。

## 2026-10-10 复核
本轮静态读取赛事页及适配指南后，用浏览器加载动态内容并展开自研框架FAQ；没有认证、注册或提交。
- [赛事提交页](https://socioverse.fudan-disc.com/challenge/#submit)：提案仍为1-2页PDF，截止2026-10-12 23:59 UTC+8；终稿截止2026-10-31同时间。初筛只影响额外API支持，不淘汰。
- Track C仍要求对照解释有效性、成本和适用范围。报告4-8页含图表，视频MP4不超过5分钟（在线可用平台回放替代），固定seed、声明模型调用/成本、真实真值获取时点及防泄漏。
- [FAQ](https://socioverse.fudan-disc.com/challenge/#faq)与[适配指南](https://socioverse.fudan-disc.com/docs/guides/wrap-legacy-model/)仍允许自研框架Path C适配，但成果必须为study；四接口及轨迹一致性要求仍在。
- 命名模板含子赛道字段，公开赛道描述未列具体子赛道选项，不自行发明。团队/报名/出版兼容性均未确认。
- 本轮未重读GitHub最新README，10月9日README日期冲突仅是历史记录。
- 已形成两页提案审阅稿；须据实际团队、数据来源和报名信息定稿。
