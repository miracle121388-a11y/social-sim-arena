# Arena 预测与参赛工作区

当前只维护 Arena v1。默认方法已经冻结；第二轮候选没有超过 persistence，未替换默认版本。当前9题已准备、0题正式提交，等待 GitHub fork、登记 PR 合并。

## 代码结构

```text
method.py                  预测算法；新的研究改动集中在这里
prepare_and_cache.py       固定数据适配与统计专家
forecast.py                本地预测接口
arena_live.py              参赛登记准备与签名提交
evaluate.py                评分与预算检查
autoresearch.py            已完成的24轮研究控制器
workspace.py               工作区路径与写入检查
requirements.txt           当前依赖总入口
scripts/                   隔离检查、冻结结果审计
tests/                     当前10项契约测试
data/arena_v1/             当前冻结数据和示例
results/arena_v1/          当前实验结果
provenance/arena_v1/       冻结协议、候选与凭证
provenance/live/           登记、9题清单及公开输入
provenance/maintenance/    清理清单与校验报告
.private/                  私钥、未公开预测与提交回执；禁止上传
archive/                   旧版本唯一归档入口
legacy/                    必须保持的原始参考档案
```

`.venv-research` 是运行环境；`.venv` 用于隔离检查。`.git`、缓存和临时目录不是业务代码。根目录的6份上下文文件为工作区规则要求，已压缩为职责明确的短文档。

## 三个日常操作

先在 PowerShell 进入 `D:\Users\Lenovo\Desktop\njusim-contest`。

测试：
```powershell
.\.venv-research\Scripts\python.exe -I -B -m unittest discover -s tests -p test_arena_v1.py
```

本地历史示例（每次选一个尚不存在的输出文件名）：
```powershell
.\.venv-research\Scripts\python.exe -I -B forecast.py --request data/arena_v1/example-request.json --output results/arena_v1/my-response.json --replay
```

正式提交（仅登记合并且题目未关闭时）：
```powershell
.\.venv-research\Scripts\python.exe -I -B arena_live.py submit --round yougov-2026-w43-rv-approval
```

操作详情见 [LIVE_SUBMISSION.md](LIVE_SUBMISSION.md)。当前批次不要重复执行 init/prepare，不要重跑已结束的搜索覆盖账本。当前原 test 已释放，不能再次当作未见测试。

## 效果与边界

详见 [ARENA_RESULTS.md](ARENA_RESULTS.md)。上轮回放留出主指标改善4.84%，区间跨零，官方平均skill=-0.076677；第二轮最佳开发skill=-0.000218，仍不如基线0。当前没有官方成绩，没有真实社会机制模拟或跨域有效性证明。

## 旧版本处理

旧源码、配置、测试、论文、第二轮诊断与旧结果已从活动路径移除，统一存入 `archive/history-before-simplification-20261015.zip`；内含原相对路径和 SHA256 清单。旧引用用 `归档.zip#原相对路径` 标记。需要复核时只提取到工作区内独立目录，不覆盖当前文件。

`legacy/`按原工作区规则保留不动。当前方法发行包仍在 `dist/arena-v1-frozen.zip`，它是先前冻结的研究发行包，不含后加的签名提交工具。私钥不在归档及发行包中。清理审计见 `provenance/maintenance/`。
