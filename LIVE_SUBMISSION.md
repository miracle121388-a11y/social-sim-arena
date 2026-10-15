# Arena 首批正式参赛操作

状态：9 题已冻结，0 正式提交。等待用户完成 GitHub 登录或 fork，然后提交登记 PR，等待主办方合并。

仅上传 `provenance/live/registration.json` 的内容到官方仓库 `entrants/njusim-mace.json`。不要上传研究仓库、`.private/` 或密钥。

PR 标题：Register njusim-mace for signed scalar forecasts

PR 正文：
Register NjuSim MACE Forecast, owned by @Ustinian5, for signed forecast POSTs using the attached Ed25519 public key. This is a statistical expert ensemble with budgeted historical calibration and CRPS-based weighting, initially covering scalar public-opinion and consumer rounds. It does not use an LLM or require an endpoint. Retrospective results have not established superiority to persistence; prospective submissions will be evaluated separately. No private key or forecast payload is included in this registration.

## 登记合并后

当前目录必须为 `D:\Users\Lenovo\Desktop\njusim-contest`。先核查官方登记包含本地公钥、题目仍开放，然后逐题执行：

```powershell
.\.venv-research\Scripts\python.exe -I -B arena_live.py submit --round yougov-2026-w43-rv-approval
```

题目全集在 `provenance/live/prepared.json`。入口会重新检查登记、关闭状态、原截止时间和预测哈希，拒绝重定向；每题保存原签名请求及服务端回执。网络超时重试会复用相同请求；已经有本地回执则不再 POST。HTTP 拒绝不会记为成功；若首次请求未受理且时间戳已过期，需要人工核查后为该题新增有审计记录的尝试，不覆盖旧签名。

最早截止北京时间 2026-10-18 22:00，之后一组为 2026-10-21 22:00。如登记未及时合并，则记录错过，不能回填。冻结方法不因这一批结果调参。官方成绩应按全部受理题目报告，披露漏交及失败；当前没有正式成绩。

原有 dist/arena-v1-frozen.zip 保留为方法发行包，本次上线外围尚未并入该包。
