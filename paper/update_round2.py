"""Generate the Round-2 paper extension exclusively from sealed measurements."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from workspace import path,digest
from v2_evaluation import ci,verify


def read(name):return json.loads(path(name).read_text(encoding='utf-8'))
def write(name,value):path(name).write_text(value,encoding='utf-8',newline='\n')
def pct(x):return f'{100*x:.1f}'
def fmt(x):return f'{x:.5f}'
def interval(a):return f'[{a[0]:.5f}, {a[1]:.5f}]'


verify()
frozen=read('provenance/v2/frozen.json')
assert digest('method.py')==frozen['method_sha256']
rows=list(csv.DictReader(path('experiments_v2.tsv').open(encoding='utf-8'),delimiter='\t'))
assert len(rows)==30 and all(r['status'] in ['KEEP','REVERT'] for r in rows)
winner=[r for r in rows if r['status']=='KEEP'][-1]
dev=read(winner['result']);test=read('provenance/v2/test-current.json')
v1dev=read('provenance/v2/baseline.json');v1test=read('provenance/v2/test-v1.json')
assert dev['method_sha256']==test['method_sha256']==frozen['method_sha256']
assert all(dev['guards'].values()) and all(test['guards'].values())
cf=dev['config'];full=test['strategies']['Full'];df=dev['strategies']['Full']
paired={name:ci(np.array(test['strategies'][name]['world_auc'])-np.array(full['world_auc'])) for name in ['Random','Entropy','ParamIG','Standard_OED']}
summary={'frozen':frozen,'winner':winner,'dev':{'auc':dev['auc_error'],'ess':dev['initial_ess'],'brier':df['final_brier'],'gains':dev['gains']},
         'test':{'auc':test['auc_error'],'ess':test['initial_ess'],'brier':full['final_brier'],'gains':test['gains'],'paired_auc_difference_ci95':paired},
         'v1_test_auc':v1test['auc_error'],'v2_relative_reduction_vs_v1':1-test['auc_error']/v1test['auc_error'],
         'unique_dev_auc_values':len(set(float(r['auc']) for r in rows)),
         'source_hashes':{p:digest(p) for p in ['provenance/v2/test-current.json','provenance/v2/test-v1.json',winner['result'],'experiments_v2.tsv']}}
write('provenance/v2/paper-summary.json',json.dumps(summary,indent=2)+'\n')


def table(name,caption,label,header,body,cols,zh=False):
    folder='tables_zh' if zh else 'tables'
    text='\\begin{table}[tbp]\n\\centering\\small\n\\setlength{\\tabcolsep}{4pt}\n'
    text+='\\caption{'+caption+'}\\label{'+label+'}\n'
    text+='\\begin{tabular}{'+cols+'}\n\\toprule\n'+header+' \\\\\n\\midrule\n'
    text+='\n'.join(' & '.join(r)+' \\\\' for r in body)
    text+='\n\\bottomrule\n\\end{tabular}\n\\end{table}\n'
    write(f'paper/{folder}/{name}.tex',text)


body=[]
for version,split,r in [('V1','Dev',v1dev),('V2','Dev',dev),('V1','Test',v1test),('V2','Test',test)]:
    f=r['strategies']['Full']
    body.append([version,split,f"{r['initial_ess']:.2f}",fmt(f['auc']),fmt(f['b0_error']),fmt(f['b16_error']),fmt(f['final_brier'])])
for zh in (False,True):
    table('v2_overview','第二阶段同一高分歧基准上的 V1/V2 对照。Brier 为预算 16 的独立过程审计误差。' if zh else
          'V1 and V2 on the same Round-2 stress benchmark. Brier is measured on the independent process audit at budget 16.',
          'tab:v2-overview','版本 & 划分 & 有效数 & AUC & B0 误差 & B16 误差 & Brier' if zh else
          'Version & Split & ESS & AUC & B0 error & B16 error & Brier',body,'llrrrrr',zh)
body=[]
for version,r in [('V1',v1test),('V2',test)]:
    for name,s in r['strategies'].items():
        body.append([version,name.replace('_','\\_'),fmt(s['auc']),interval(s['auc_ci95']),fmt(s['final_brier'])])
for zh in (False,True):
    table('v2_selectors','冻结测试：每个版本内严格共用先验和更新规则，区间按 24 个完整世界重采样。' if zh else
          'Frozen-test selectors, matched within each version on prior and update. Intervals resample 24 whole worlds.',
          'tab:v2-selectors','版本 & 策略 & AUC & 95\\% 区间 & Brier' if zh else
          'Version & Selector & AUC & 95\\% interval & Brier',body,'llrlr',zh)
body=[]
for version,r in [('V1',v1test),('V2',test)]:
    for a in r['strategies']['Full']['activity_results']:
        body.append([version,str(a['activity']+1),fmt(a['auc']),interval(a['auc_ci95']),interval(a['b0_b16_difference_ci95'])])
for zh in (False,True):
    table('v2_activities','逐活动的冻结测试结果。每个活动模板有 24 个独立世界实现；同一世界内的活动不视为独立。' if zh else
          'Frozen-test activity results. Each template has 24 independent world realizations; activities within a world are not independent.',
          'tab:v2-activities','版本 & 活动 & AUC & AUC 的 95\\% 区间 & B0--B16 的 95\\% 区间' if zh else
          'Version & Activity & AUC & AUC 95\\% interval & B0--B16 95\\% interval',body,'llrll',zh)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axes=plt.subplots(1,3,figsize=(7.4,2.55),sharey=False)
budgets=np.array([0,2,4,8,12,16]);cfg=read('configs/high_disagreement_mode.json')
rng=np.random.default_rng(cfg['bootstrap_seed']);ix=rng.integers(0,24,(2000,24))
series=[('V1 Full',v1test['strategies']['Full'],'#777777','--'),('V2 Full',full,'#0072B2','-'),
        ('V2 Random',test['strategies']['Random'],'#D55E00','-'),('V2 Entropy',test['strategies']['Entropy'],'#009E73',':')]
for event,ax in enumerate(axes):
    for label,s,color,ls in series:
        a=np.array(s['event_world_curves'])[:,:,event];low,high=np.quantile(a[ix].mean(1),[.025,.975],axis=0)
        ax.plot(budgets,a.mean(0),label=label,color=color,linestyle=ls,lw=1.5)
        ax.fill_between(budgets,low,high,color=color,alpha=.11)
    ax.set_title(f'Activity {event+1}');ax.set_xlabel('Evidence budget');ax.grid(alpha=.15)
axes[0].set_ylabel('Trajectory RMSE')
fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=4,frameon=False,bbox_to_anchor=(.5,-.02))
fig.tight_layout(rect=(0,.09,1,1))
for folder in ['figures','figures_zh']:
    target=path(f'paper/{folder}/v2_budget_curves.pdf');fig.savefig(target,bbox_inches='tight')
plt.close(fig)

en=r'''\subsection{Round 2: noncollapsed calibration and matched-prior acquisition}
\label{sec:round2}
\paragraph{A prospective extension, with V1 retained.}
Sections~\ref{sec:method} and 4.1--4.4 describe the original V1 study. We now test the specific failure identified there: can evidence acquisition become useful when calibration retains plausible alternatives? We preserve V1 commit \texttt{eb641c2} and its original data, then preregister a separate stress configuration, three statistical guards, and 30 development configurations. Both versions are evaluated on this new configuration; its scores must not be compared numerically with the earlier benchmark's scores as if only the algorithm had changed.

\paragraph{Controlled ambiguity and inferential units.}
The new simulator uses 256 agents, eight rollout seeds, 12 time steps, and 200 candidate mechanisms. The fixed pair $(a,b,d)=(.2,.95,.12)$ and $(.95,.2,.12)$ has the same attention--participation product. Inverse-transform common random numbers generate the same initial intentions for this pair. History activates queueing or forwarding separately; queue-enabled peer notices in the combination activate an eight-neighbor cascade, together with strong same-time conflict blocking. The pair's historical RMSE is @HIST@, whereas its probe and test-design disagreement is @GEOM@. This is a deliberately constructed interaction, not a fitted human behavioral law. Development uses 12 independently simulated worlds and test uses 24 fresh worlds. Test reuses the fixed combined event design; it is fresh-world replication, not an additional unseen combination beyond the probe design. All confidence intervals resample complete worlds and preserve within-world activity dependence.

\paragraph{Calibration and acceptance rule.}
For the V1-compatible support $\mathcal C$, let $r_{etc}$ denote the relative seed-variance normalization from Eq.~\eqref{eq:distance}. V2 uses
\begin{align}
 E_m^{(2)}&=\frac{1}{2\sigma^2}\operatorname{mean}_{e,t,c}
 \frac{(\bar X_{metc}-H_{etc})^2}{r_{etc}}+\lambda\ell_m^{\mathrm{proc}},\\
 \ell_m^{\mathrm{proc}}&=-\frac{1}{|\mathcal O|}\sum_{j\in\mathcal O}
 [y_j\log p_{mj}+(1-y_j)\log(1-p_{mj})],\\
 w_{0m}^{(2)}&\propto\mathbf1[m\in\mathcal C]\exp(-E_m^{(2)}/T),\qquad
 T=\inf\{t\geq1:\,N_{\mathrm{eff}}(w_0(t))\geq8\}.
 \label{eq:v2-calibration}
\end{align}
The implementation uses a small numerical margin and bisection for the temperature floor; MCAR missing history labels contribute no log likelihood. Unobserved views in intention records remain marginalized through $p_{mj}=a_mb_m I_j$. The support filter is unchanged. The mean residual above describes the selected V2 configuration; worst-event variants are also included in the search. Gibbs temperature has an entropy-regularization interpretation, but the enforced effective size is based on R\'enyi-2 entropy, not Shannon entropy.

A candidate is retained only if development AUC improves by more than $10^{-8}$ and all guards hold: initial effective size at least eight; both initial and budget-16 audit Brier at most .195; a strictly positive lower endpoint of the paired 95\% bootstrap interval for $R(0)-R(16)$; at least 5\% lower AUC than both matched-prior Random and Entropy; and fast-development runtime at most 15 seconds. All selectors within a version share initial weights, observations, costs, missingness, and posterior update. With selected evidence $D$, the update is
\begin{equation}
 w_m(D)\propto w_{0m}\exp\!\left\{\tau^{-1}
 \sum_{j\in D\cap\mathcal O}\log p_m(y_j)\right\}.
 \label{eq:v2-update}
\end{equation}
The winner uses $\sigma=@SIGMA@$, $\lambda=@LAMBDA@$ and $\tau=@TAU@$, with unweighted probe times and two-query fantasy conditioning. Both hypothetical branches use the same likelihood temperature as the real update. For $\tau\ne1$, this is a generalized-Bayes update: the original covariance score is still used as a heuristic acquisition ranking, and is not claimed to equal the exact variance reduction of the tempered posterior. No submodularity guarantee is added.

\paragraph{Frozen results.}
Thirty valid trials yield @KEEPS@ KEEP and @REVERTS@ REVERT decisions with no runtime failures. The selected commit is \texttt{@COMMIT@}. Initial effective size is @ESS@, compared with @V1ESS@ for V1 on this new cache. Table~\ref{tab:v2-overview} reports the matched benchmark comparison. V2 development AUC is @DEVAUC@, with gains of @DEVGR@\% and @DEVGE@\% over matched-prior Random and Entropy. The algorithm is sealed before test truth is loaded. Test Full AUC is @TESTAUC@ (95\% interval @TESTCI@), compared with @V1AUC@ for V1: a @VS1@\% reduction on the same new benchmark. V2 test error falls from @B0@ at zero evidence to @B16@ at budget 16; the paired improvement interval is @DELTA@. Initial and final test Brier are @IBRIER@ and @BRIER@, respectively. Initial Brier is worse than V1's even though both satisfy the guard; the improvement occurs after evidence acquisition.
\input{tables/v2_overview}
\input{tables/v2_selectors}

On test, Full improves AUC by @GR@\% over same-prior Random and @GE@\% over same-prior Entropy. The paired intervals for baseline-minus-Full AUC are @RDIFF@ and @EDIFF@. Figure~\ref{fig:v2-curves} shows that the reduction is present for each activity, with activitywise uncertainty in Table~\ref{tab:v2-activities}. However, ParamIG selects the same records and exactly matches Full, so this experiment does not establish superiority of prediction-oriented covariance scoring over parameter information gain. The standard OED control targets historical trajectories and is weaker here; it is not an optimized compositional OED oracle.
\begin{figure}[tbp]
\centering\includegraphics[width=\linewidth]{v2_budget_curves.pdf}
\caption{Round-2 frozen-test curves, separately by activity. Shading is a pointwise 95\% whole-world bootstrap interval. V2 selectors share their prior and update; V1 uses its own original calibration. ParamIG coincides with V2 Full and is omitted for legibility.}
\label{fig:v2-curves}
\end{figure}
\input{tables/v2_activities}

\paragraph{What changed, and what remains unproved.}
The thirty configurations produce @UNIQUE@ distinct development AUC values. Raising the effective-size floor from 8 to 24 at the winner's calibration width has no effect because its unconstrained effective size already exceeds 24. Thus the guard prevents inadmissible winners, but its active intervention is not the cause of the selected configuration's gain. With width .008 and process weight 8 fixed, changing $\tau$ from 1 to .5 reduces AUC from @TAU1AUC@ to @DEVAUC@; $\tau=2$ worsens it to @TAU2AUC@. These are controlled temperature comparisons. Comparisons across other groups also change width, process weight or loss aggregation and cannot identify their individual causal contributions. Removing fantasy conditioning produces the same selected records and score in the matched configurations; this pool supplies no evidence for a separate batch-conditioning benefit.

The acquisition pool deliberately contains 24 view records, 40 known-probability availability records with $p=.5$, and 96 marginalized intention records. Maximum entropy spends its budget on irreducible availability uncertainty, while the informative view records distinguish the ambiguous attention mechanisms. This design makes the failure mode interpretable but limits generality: it favors information-sensitive selection over a pure predictive-entropy heuristic, and does not establish robust dominance on arbitrary pools. The wider test improvement than development is conditional on the fixed historical cohort and different acquisition answers; the 12-world development set is small. This constructed setting restores acquisition value; it does not establish real-world identification, new risk guarantees, or official rankings.
'''

zh=r'''\subsection{第二阶段：非坍缩校准与同先验主动取证}
\label{sec:round2}
\paragraph{保留 V1，单独验证其失效原因。}
第~\ref{sec:method} 节及第 4.1--4.4 节报告原始 V1 研究。本节针对一个具体问题展开：如果校准后仍保留合理的候选机制，过程取证能否重新产生可测量的收益？我们保留 \texttt{eb641c2} 的代码、数据和原始结论，在独立分支预先固定新的压力场景、裁决护栏和 30 组开发配置。V1 与 V2 都在新场景上重新评测；不能把新旧基准的分数直接相减，再将差异全部归因于算法。

\paragraph{机制歧义的构造与统计单位。}
新配置采用 256 个智能体、8 个模拟种子、12 个时间步和 200 组候选机制。预先指定的两组机制为 $(a,b,d)=(.2,.95,.12)$ 与 $(.95,.2,.12)$，注意概率与参与概率的乘积相同。通过逆变换共同随机数耦合，二者生成相同的初始意图。历史活动分别启用候补或转发；组合活动同时启用候补通知触发的八邻居传播级联和强同时间冲突。这对机制的历史轨迹 RMSE 为 @HIST@，组合探针及测试事件设计上的轨迹分歧为 @GEOM@。这是专门构造的交互压力测试，不是从真实行为数据拟合出的社会规律。

开发和测试分别使用 12 个与 24 个独立模拟世界。测试更换世界、过程审计和取证答案，事件设计仍与组合探针相同，因此它验证的是同一设计下的新世界复现，不是超出探针的新组合迁移。区间以整个世界为单位进行配对 bootstrap，保留世界内活动之间的依赖，逐活动另行报告。

\paragraph{校准公式与保留条件。}
在 V1 的历史相容支持集 $\mathcal C$ 上，设 $r_{etc}$ 为式~\eqref{eq:distance} 中的相对种子方差归一化项。V2 采用
\begin{align}
 E_m^{(2)}&=\frac{1}{2\sigma^2}\operatorname{mean}_{e,t,c}
 \frac{(\bar X_{metc}-H_{etc})^2}{r_{etc}}+\lambda\ell_m^{\mathrm{proc}},\\
 \ell_m^{\mathrm{proc}}&=-\frac{1}{|\mathcal O|}\sum_{j\in\mathcal O}
 [y_j\log p_{mj}+(1-y_j)\log(1-p_{mj})],\\
 w_{0m}^{(2)}&\propto\mathbf1[m\in\mathcal C]\exp(-E_m^{(2)}/T),\qquad
 T=\inf\{t\geq1:\,N_{\mathrm{eff}}(w_0(t))\geq8\}.
 \label{eq:v2-calibration}
\end{align}
实现中通过二分求解温度，并留出很小的数值余量。MCAR 缺失标签不贡献对数似然；意图记录中未观测的查看状态仍按 $p_{mj}=a_mb_m I_j$ 边缘化。支持集筛选条件不变。上述平均残差对应最终选中的 V2；搜索也包含最坏活动残差版本。Gibbs 温度可以解释为熵正则强度，但这里直接约束的有效机制数对应二阶 R\'enyi 熵，并非 Shannon 熵。

KEEP 必须同时满足：开发 AUC 比当前最优值下降超过 $10^{-8}$；初始有效机制数至少为 8；初始及预算 16 的过程审计 Brier 均不超过 .195；$R(0)-R(16)$ 的配对 95\% bootstrap 区间下界严格大于零；AUC 比同先验 Random 和 Entropy 均至少低 5\%；快速开发评测不超过 15 秒。每个版本内部的三种策略共用先验、证据池、成本、答案、缺失掩码和后验更新。给定所选证据 $D$，更新为
\begin{equation}
 w_m(D)\propto w_{0m}\exp\!\left\{\tau^{-1}
 \sum_{j\in D\cap\mathcal O}\log p_m(y_j)\right\}.
 \label{eq:v2-update}
\end{equation}
最终配置为 $\sigma=@SIGMA@$、$\lambda=@LAMBDA@$、$\tau=@TAU@$，各时间步等权，批量大小为 2，并保留幻想分支条件化。假设答案分支与真实证据更新使用相同温度。由于 $\tau\ne1$，该更新属于广义贝叶斯；原协方差评分在此作为启发式排序使用，不能继续宣称它精确等于温度化后验的预期方差下降，也不增加次模性保证。

\paragraph{冻结后的对照结果。}
30 轮有效实验包含 @KEEPS@ 次 KEEP、@REVERTS@ 次 REVERT，没有运行失败，最优提交为 \texttt{@COMMIT@}。在同一新缓存上，V2 的初始有效机制数为 @ESS@，V1 为 @V1ESS@。表~\ref{tab:v2-overview} 给出同基准对照。V2 开发 AUC 为 @DEVAUC@，比同先验 Random 和 Entropy 分别低 @DEVGR@\% 和 @DEVGE@\%。读取测试真值前已冻结算法。测试 Full AUC 为 @TESTAUC@，95\% 区间为 @TESTCI@；V1 为 @V1AUC@，两者相差 @VS1@\%。V2 的误差从零证据时的 @B0@ 降至预算 16 时的 @B16@，配对改善区间为 @DELTA@。初始和最终测试 Brier 分别为 @IBRIER@ 与 @BRIER@。初始 Brier 实际劣于 V1，只是两者均满足护栏；过程预测的改善发生在取证之后。
\input{tables_zh/v2_overview}
\input{tables_zh/v2_selectors}

测试集上，Full AUC 比同先验 Random 低 @GR@\%，比同先验 Entropy 低 @GE@\%；“基线减 Full”的配对 AUC 差值区间分别为 @RDIFF@ 与 @EDIFF@。图~\ref{fig:v2-curves} 展示逐活动曲线，表~\ref{tab:v2-activities} 给出各活动的区间。然而 ParamIG 选择了相同记录，与 Full 完全持平，因此不能据此声称协方差取证优于参数信息增益。标准 OED 对照针对历史轨迹，表现较弱；它并不是经过优化的组合预测 OED 上界。
\begin{figure}[tbp]
\centering\includegraphics[width=\linewidth]{v2_budget_curves.pdf}
\caption{第二阶段冻结测试的逐活动曲线。阴影为逐点的 95\% 世界 bootstrap 区间。V2 的三种取证共用先验与更新；V1 使用原始校准。ParamIG 与 V2 Full 重合，为便于阅读省略。}
\label{fig:v2-curves}
\end{figure}
\input{tables_zh/v2_activities}

\paragraph{哪些变化有效，哪些结论仍不成立。}
30 组配置产生了 @UNIQUE@ 个不同的开发 AUC。在最终核宽下，将有效机制数下限从 8 提高到 24 没有改变权重，因为未触发温度提升时的有效机制数已超过 24。因此，护栏可以拒绝不合格候选，但最终配置的改善不能全部归因于护栏主动抬高温度。在核宽 .008、过程权重 8 不变时，将更新温度从 1 调到 .5，AUC 从 @TAU1AUC@ 降至 @DEVAUC@；温度 2 则恶化到 @TAU2AUC@。这是可直接比较的温度实验。其他配置组同时改变核宽、过程权重或损失聚合方式，不能据此单独确定每个因素的因果贡献。移除批量幻想分支条件化后，匹配配置的选择记录和分数相同，这个证据池没有展示独立的批量去冗余收益。

证据池固定包含 24 条查看记录、40 条概率已知为 .5 的可用性记录，以及 96 条边缘化意图记录。最大熵策略将预算花在不可约的可用性随机性上，查看记录则能区分歧义的注意机制。这种设计使失效原因容易解释，也限定了结论：它有利于具有信息敏感性的选择策略，不能证明任意证据池上的普遍优势。测试增益大于开发增益，与固定历史条件下不同的取证答案有关，开发集仅含 12 个世界。当前证据支持“构造场景中恢复了主动取证价值”，尚不支持真实世界机制识别、新的未知规则告警保证或任何官方榜单成绩。
'''
geo=read('provenance/v2/geometry.json')
values={'HIST':fmt(geo['train_pair_rmse']),'GEOM':fmt(geo['probe_pair_rmse']),
        'SIGMA':str(cf['sigma']),'LAMBDA':f"{cf['process_weight']:g}",'TAU':str(cf['update_temperature']),
        'KEEPS':str(frozen['keeps']),'REVERTS':str(30-frozen['keeps']),'COMMIT':frozen['commit'][:7],
        'ESS':f"{test['initial_ess']:.2f}",'V1ESS':f"{v1test['initial_ess']:.2f}",
        'DEVAUC':fmt(dev['auc_error']),'DEVGR':pct(dev['gains']['Random']),'DEVGE':pct(dev['gains']['Entropy']),
        'TESTAUC':fmt(test['auc_error']),'TESTCI':interval(full['auc_ci95']),'V1AUC':fmt(v1test['auc_error']),
        'VS1':pct(1-test['auc_error']/v1test['auc_error']),'B0':fmt(full['b0_error']),'B16':fmt(full['b16_error']),
        'DELTA':interval(full['b0_b16_difference_ci95']),'IBRIER':fmt(full['initial_brier']),'BRIER':fmt(full['final_brier']),
        'GR':pct(test['gains']['Random']),'GE':pct(test['gains']['Entropy']),
        'RDIFF':interval(paired['Random']),'EDIFF':interval(paired['Entropy']),
        'UNIQUE':str(summary['unique_dev_auc_values']),'TAU1AUC':fmt(float(rows[3]['auc'])),'TAU2AUC':fmt(float(rows[5]['auc']))}
for key,value in values.items():en=en.replace('@'+key+'@',value);zh=zh.replace('@'+key+'@',value)
assert '@' not in en+zh
for folder,content in [('sections',en),('sections_zh',zh)]:
    write(f'paper/{folder}/05_round2.tex',content)
    target=f'paper/{folder}/05_experiments.tex';existing=path(target).read_text(encoding='utf-8')
    addition='\\input{'+folder+'/05_round2}\n'
    if addition not in existing:write(target,existing+'\n'+addition)

report=f'''# AutoResearch Round 2: frozen results

Branch: `exp/v2-non-collapsed`. Winner: `{frozen['commit']}`.
Method SHA-256: `{frozen['method_sha256']}`.
30 valid trials: {frozen['keeps']} KEEP, {30-frozen['keeps']} REVERT, no execution failures.

| Quantity (same new benchmark) | V1 | V2 |
|---|---:|---:|
| Initial ESS | {v1test['initial_ess']:.6f} | {test['initial_ess']:.6f} |
| Dev Full AUC | {v1dev['auc_error']:.8f} | {dev['auc_error']:.8f} |
| Test Full AUC | {v1test['auc_error']:.8f} | {test['auc_error']:.8f} |
| Test B0 RMSE | {v1test['strategies']['Full']['b0_error']:.8f} | {full['b0_error']:.8f} |
| Test B16 RMSE | {v1test['strategies']['Full']['b16_error']:.8f} | {full['b16_error']:.8f} |
| Test initial Brier | {v1test['strategies']['Full']['initial_brier']:.8f} | {full['initial_brier']:.8f} |
| Test B16 Brier | {v1test['strategies']['Full']['final_brier']:.8f} | {full['final_brier']:.8f} |
| Same-prior gain vs Random | {pct(v1test['gains']['Random'])}% | {pct(test['gains']['Random'])}% |
| Same-prior gain vs Entropy | {pct(v1test['gains']['Entropy'])}% | {pct(test['gains']['Entropy'])}% |

Test AUC CI: {interval(full['auc_ci95'])}. Paired B0-minus-B16 CI: {interval(full['b0_b16_difference_ci95'])}.
Whole worlds are the resampling unit (12 dev / 24 test); activitywise results are in the sealed JSON and paper tables.

## Interpretation

- Constructed mechanism-pair history RMSE {geo['train_pair_rmse']:.6f}; combined disagreement {geo['probe_pair_rmse']:.6f}.
- All preregistered development guards passed; the same criteria also pass on frozen test.
- ParamIG ties Full exactly. Batch fantasy removal is inactive in the matched trials.
- ESS floors 8--24 are inactive at the winner's width; broader calibration and likelihood tempering explain the measured change, not a uniquely identified effect of the ESS constraint.
- The pool intentionally contains high-entropy nuisance availability records. This is a synthetic stress test, not a universal acquisition ranking.
- New test worlds reuse the probe event design. There is no official SocioVerse/MIT evaluation or real-data validation.
- V1's original ESS 1.000385 belongs to the old benchmark. Its ESS on the new benchmark is {v1test['initial_ess']:.6f}; do not conflate the two.

## Reproduce

Use `.venv-research/Scripts/python.exe -B evaluate.py --campaign v2 --split test --mode full_paper_ablation`.
For V1 on this same cache add `--method-version v1`. `reproduce_round2.ps1` and `reproduce_round2.sh`
verify invariants, rerun both sealed versions, and rebuild the paper. They do not restart search.
The original V1 cache and `dist/njusim-frozen-research.zip` are preserved; legacy V1 root commands
use the old lock and should not be mixed with the V2 branch infrastructure.

The paper extension generator reads canonical sealed results, not the newest rerun.
`experiments_v2.tsv`, `configs/v2_trials.json`, and `provenance/v2/*-decision.json` contain all 30 trials.
Rejected source versions remain reachable under `refs/autoresearch-v2/rejected/`.
'''
write('ROUND2_RESULTS.md',report)
print(json.dumps(summary,indent=2))
