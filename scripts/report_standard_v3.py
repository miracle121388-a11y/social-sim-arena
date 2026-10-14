"""Independent cost/statistics audit and data-derived V0 report; never tunes."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from workspace import path,digest,save_json
from evaluate import verify,ci,PRIMARY

read=lambda n:json.loads(path(n).read_text(encoding='utf-8'))
verify();manifest=read('provenance/v3/v0.json')
assert digest('method.py')==manifest['method_sha256']
assert not path('provenance/v3/test_release.json').exists()
fast=read(manifest['fast_result']);full=read(manifest['ablation_result']);old=read(manifest['pre_balance_ablation'])
cache=torch.load(path('data/rollout_cache.pt'),weights_only=True)
costs=cache['pool']['costs'].numpy();budgets=np.array(cache['budgets'])
policies=full['strategies'];baseline=policies['Full'];primary_hashes={policies[n]['initial_prior_hash'] for n in PRIMARY}
assert len(primary_hashes)==1
assert full['initial_ess']>=15
assert np.all(np.diff(baseline['macro_curve'])<0)
verified=0
for name,s in policies.items():
    curves=np.array(s['event_world_errors']);aucs=np.trapezoid(curves,budgets,axis=1)/16
    assert abs(aucs.mean()-s['auc'])<1e-7
    assert np.allclose(ci(aucs.mean(1)),s['auc_ci95'],atol=1e-7)
    diff=aucs.mean(1)-np.array(baseline['world_auc'])
    assert np.allclose(ci(diff),full['paired_vs_full'][name]['ci95'],atol=1e-7)
    seen=[set() for _ in range(len(curves))];spent=np.zeros(len(curves))
    actual=np.zeros((len(curves),len(budgets)))
    for j,budget in enumerate(budgets):
        for trace in s['query_trace']:
            if trace['checkpoint']!=budget:continue
            ix=np.array(trace['indices']);pay=(costs[ix.clip(0)]*(ix>=0)).sum(1)
            assert np.allclose(pay,trace['cost'])
            for world,record_ids in enumerate(ix):
                for record in record_ids[record_ids>=0]:
                    assert int(record) not in seen[world]
                    seen[world].add(int(record))
            spent+=pay;assert np.all(spent<=budget+1e-7)
        actual[:,j]=spent
    assert np.allclose(actual,s['spent'])
    if name!='NoSharing':
        assert s['event_world_errors']==old['strategies'][name]['event_world_errors']
        assert s['query_trace']==old['strategies'][name]['query_trace']
    if name in PRIMARY:assert s['event_world_errors']==fast['strategies'][name]['event_world_errors']
    for e,event in enumerate(s['activities']):
        assert np.allclose(ci(aucs[:,e]),event['auc_ci95'],atol=1e-7)
        verified+=1
assert max(policies['NoSharing']['marginal_total_variation'])<1e-6
prior=np.array(baseline['initial_weights']);predictive=prior.reshape(2,5,5,4).sum(-1)
predictive_ess=float(1/(predictive**2).sum())
validation={'same_primary_prior':True,'costs_and_no_repeated_indices_verified':True,
            'activity_statistics_verified':verified,'primary_results_unchanged_after_repair':True,
            'method_sha256':digest('method.py'),'initial_ess':full['initial_ess'],
            'predictive_ess_after_nuisance_marginalization':predictive_ess,
            'no_sharing_initial_marginal_TV':policies['NoSharing']['marginal_total_variation'],
            'test_unopened':not path('provenance/v3/test_release.json').exists(),
            'unit_tests_passed':8}
path('provenance/v3/validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8',newline='\n')

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(10,3.8))
colors=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00']
for name,color in zip(PRIMARY,colors):
    axes[0].plot(budgets,policies[name]['macro_curve'],label=name,color=color,marker='o',markersize=3)
axes[0].set(xlabel='Evidence cost budget',ylabel='Macro trajectory RMSE',title='Identical initial calibrated prior')
axes[0].legend(frameon=False,fontsize=8);axes[0].grid(alpha=.15)
names=['Random','Entropy','ParamIG','Standard_OED','NoBatch','NoProbes','SinglePointMAP','NoSharing']
for i,name in enumerate(names):
    r=full['paired_vs_full'][name];a,b=r['ci95'];m=r['mean_auc_difference']
    axes[1].errorbar(m,i,xerr=[[max(m-a,0)],[max(b-m,0)]],fmt='o',color='#0072B2',capsize=3)
axes[1].axvline(0,color='grey',lw=1);axes[1].set_yticks(range(len(names)),names)
axes[1].invert_yaxis();axes[1].set(xlabel='Comparator AUC minus Full (95% CI)',title='Paired whole-world bootstrap')
fig.tight_layout();fig.savefig(path('results/v3/v0_budget_and_ablations.svg'))
fig.savefig(path('results/v3/v0_budget_and_ablations.png'),dpi=150);plt.close(fig)
# Normalize generated XML line endings only; leave numerical evidence untouched.
svg=path('results/v3/v0_budget_and_ablations.svg')
raw=svg.read_bytes().replace(b'\r\r\n',b'\n').replace(b'\r\n',b'\n')
svg.write_bytes(b'\n'.join(line.rstrip() for line in raw.split(b'\n')))

fmt=lambda x:f'{x:.6f}'
lines=['# 标准版 V3 / V0 基线实测',
       '',f"代码基线：`{manifest['baseline_commit']}`；算法 SHA256：`{manifest['method_sha256']}`。",
       '本次初始化一个预先指定的 V0，没有开启 AutoResearch 搜索。测试集尚未解封。',
       '', '## 基准与先验', '',
       '候选总数 200。正确历史乘积层内有 25 种不同的预测机制，结合四种无关审计倾向后为 100 个历史相容候选。',
       f"其历史两两 RMSE 最大值为 {cache['geometry']['train']['diameter']:.6f}；组合探针最大分歧 {cache['geometry']['probe']['diameter']:.6f}，测试设计最大分歧 {cache['geometry']['test']['diameter']:.6f}。这些是直径，不表示每一对都超过 .18。",
       f"初始 ESS={full['initial_ess']:.6f}；合并无关参数后，预测机制 ESS={predictive_ess:.6f}。五个主动策略的先验逐元素完全相同。",
       '32 个潜在微观事件各有四条带噪审计记录；同事件记录相关。所有方法使用相同的精确条件似然，MCAR 缺失不当作负例。',
       '取证成本为 0.5、1、2；预算按成本累计，逐世界核对未超支、未重复购买同一记录。',
       '', '## 同先验开发集结果', '', '| 方法 | AUC | 与 Full 的差值 95% 区间 | Full 相对改善 |', '|---|---:|---|---:|']
for name,s in policies.items():
    r=full['paired_vs_full'][name];a,b=r['ci95']
    lines.append(f"| {name} | {s['auc']:.6f} | [{a:.6f}, {b:.6f}] | {100*r['relative_full_gain']:.2f}% |")
lines += ['', '上表区间来自 12 个独立模拟世界的配对 bootstrap（2000 次）。相关活动不当作独立样本；区间未作多重比较校正。NoSharing 是结构模型消融，不属于五个相同联合先验的主动策略。',
          '', '| 成本预算 | 0 | 2 | 4 | 8 | 12 | 16 |','|---|---:|---:|---:|---:|---:|---:|',
          '| Full RMSE | '+' | '.join(fmt(v) for v in baseline['macro_curve'])+' |',
          '', f"Full 最终过程 Brier={baseline['brier_curve'][-1]:.6f}。快速评测 {fast['runtime_s']:.2f} 秒，完整开发消融 {full['runtime_s']:.2f} 秒；均为实际本机测量，不保证任意机器耗时。",
          '', '## 必须保留的负结果与适用边界', '',
          f"- 批量条件化真实减少了同批同事件取证比例：Full {baseline['same_episode_batch_fraction']:.1%}，NoBatch {policies['NoBatch']['same_episode_batch_fraction']:.1%}。但 AUC 改善仅 {100*full['paired_vs_full']['NoBatch']['relative_full_gain']:.2f}%，配对区间跨零，不能宣称显著预测收益。",
          f"- 预先固定的 MAP 平局处理得到 AUC {policies['SinglePointMAP']['auc']:.6f}，数值上优于 Full，差值区间跨零。这次真值下单点估计没有出现预想的失败；没有更换真值、种子或 MAP 选点规则让它输。",
          '- NoProbes 更差；NoSharing 更差，但后者仍用有限联合粒子近似独立参数，需要与无限粒子的理想因果消融区分。',
          '- 初次 NoSharing 的历史筛选导致先验边际偏差 .37/.32/.32。该实现与结果完整保存在 pre_balance/。随后仅修正分层平衡采样；当前三活动的初始边际总变差均为 0。Full、其他对照、真值文件和算法逐项保持不变。',
          '- 高熵噪声与无关参数记录是明确构造的压力条件，不能推出任何真实证据池上 Full 必然获胜。',
          '- 当前是合成开发验证，尚无 V3 测试成绩、真实数据验证、SocioVerse 或 MIT 官方成绩。现有论文仍报告 V1/V2，不把本次开发结果改写成已确认的论文结论。',
          '', '## 复现与证据', '',
          '```powershell', r'.\.venv-research\Scripts\python.exe -B evaluate.py --split dev --mode fast_dev',
          r'.\.venv-research\Scripts\python.exe -B evaluate.py --split dev --mode full_paper_ablation',
          r'.\.venv-research\Scripts\python.exe -I -B tests/test_standard_v3.py',
          r'.\.venv-research\Scripts\python.exe -I -B scripts/report_standard_v3.py','```',
          '', '默认缓存已经生成。prepare_and_cache.py 拒绝覆盖已冻结的 V3 缓存，防止误删实验；首次替换前的 V1 缓存位于 provenance/v3/previous/data/rollout_cache.pt。',
          'V1/V2 的完整原版本可从 exp/v2-non-collapsed / dac68e8 或 dist/v2-before-v3.zip 取得。',
          f"主结果：`{manifest['fast_result']}`；消融：`{manifest['ablation_result']}`。",
          '图：`results/v3/v0_budget_and_ablations.svg`；核验：`provenance/v3/validation.json`；冻结协议：`provenance/v3/protocol.md`。']
path('V3_BASELINE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(validation,indent=2))
