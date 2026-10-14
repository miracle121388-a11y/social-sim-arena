"""Export independent-world intervals and complete post-freeze paper tables."""
import argparse
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from workspace import path


LABELS = {'Covariance': 'Full (frozen)', 'NoSharing': 'w/o parameter sharing*',
          'NoCombination': 'w/o combination target', 'SinglePoint': 'Single point (original)*',
          'MatchedMAP': 'Single point (matched MAP)', 'NoBatchDedup': 'w/o batch redundancy update'}


def label(name):
    return LABELS.get(name, name.replace('SamePrior_', 'Same prior: '))


def interval(stat, event=None):
    values = [stat[k] if event is None else stat[k][event] for k in ['mean', 'ci95_low', 'ci95_high']]
    return f'{values[0]:.5f} [{values[1]:.5f}, {values[2]:.5f}]'


def booktabs(headers, rows, caption):
    def escape(s):
        return str(s).replace('_', r'\_').replace('%', r'\%').replace('&', r'\&')
    lines = [r'\begin{table*}[t]', r'\centering', r'\small', r'\caption{'+escape(caption)+'}',
             r'\begin{tabular}{l'+'c'*(len(headers)-1)+'}', r'\toprule',
             ' & '.join(map(escape, headers))+r' \\', r'\midrule']
    lines += [' & '.join(map(escape, row))+r' \\' for row in rows]
    return '\n'.join(lines+[r'\bottomrule', r'\end{tabular}', r'\end{table*}', ''])


def export(result_path):
    data = json.loads(path(result_path).read_text(encoding='utf-8'))
    out = path('paper/'+data['run_id'])
    out.mkdir(parents=True, exist_ok=False)
    summary = data['summary']
    names = list(summary)
    headers = ['Method', 'Activity 1 AUC [95% CI]', 'Activity 2 AUC [95% CI]', 'Activity 3 AUC [95% CI]']
    def rows(chosen):
        return [[label(n)]+[interval(summary[n]['event_auc'], e) for e in range(3)] for n in chosen]
    caption = ('Constructed synthetic test activities; 24 independent worlds, paired world-bootstrap 95% CIs. '
               'Activities interact inside each world; no resampling of dependent time cells. Fixed training/evidence/templates.')
    t1 = booktabs(headers, rows(['Covariance', 'SinglePoint', 'MatchedMAP', 'PassiveV1']),
                  'Experiment 1: mechanism set versus point estimates. '+caption)
    alarm_rows = []
    for n in ['Covariance', 'MatchedMAP', 'PassiveV1']:
        for shift, metrics in data['stress_summary'][n].items():
            alarm_rows.append([label(n)+' / '+shift]+[interval(metrics['interval_alarm'], e) for e in range(3)])
    t1 += booktabs(['Method / truth rule', 'Activity 1 alarm [95% CI]', 'Activity 2 alarm [95% CI]',
                   'Activity 3 alarm [95% CI]'], alarm_rows,
                  'Experiment 1 continued: post-observation interval alarm. None is false alarm rate; other rows '
                  'are detection rates. Threshold: >20% of cells outside the pointwise 90% interval. Not an early warning.')
    (out/'experiment1.tex').write_text(t1, encoding='utf-8')
    t2 = booktabs(headers, rows(['Random', 'Entropy', 'ParamIG', 'Standard_OED', 'Covariance']),
                  'Experiment 2: original calibration policies; acquisition and calibration differ. '+caption)
    t2 += booktabs(headers, rows(['SamePrior_Random', 'SamePrior_Entropy', 'SamePrior_ParamIG',
                                  'SamePrior_Standard_OED', 'Covariance']),
                   'Experiment 2 control: all acquisition methods start from the evolved prior. '+caption)
    timing_rows = [[n, f"{v['median_speedup']:.2f}", f"{v['max_abs_difference']:.3g}"] for n, v in data['timing'].items()]
    t2 += booktabs(['Prior', 'Median speedup (enumeration/covariance)', 'Max absolute score difference'],
                  timing_rows, 'GPU synchronized paired timing, ten repetitions; raw timings are in the JSON. '
                  'Both algorithms are O(MRD) in arithmetic; vectorization reduces dispatch overhead.')
    t2 += booktabs(['Official benchmark', 'Status'], [['SocioVerse', 'NOT EVALUATED'], ['MIT', 'NOT EVALUATED']],
                  'No official benchmark data or named MIT evaluation protocol is available. Synthetic scores are not submissions.')
    (out/'experiment2.tex').write_text(t2, encoding='utf-8')
    ablations = ['Covariance', 'NoSharing', 'NoCombination', 'SinglePoint', 'MatchedMAP', 'NoBatchDedup']
    (out/'experiment3.tex').write_text(booktabs(headers, rows(ablations),
        'Experiment 3: frozen-method ablations. *NoSharing changes the candidate prior; original SinglePoint '
        'uses another selection objective. MatchedMAP removes only the mixture. '+caption), encoding='utf-8')
    with (out/'event_metrics.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['method', 'event', 'metric', 'mean', 'ci95_low', 'ci95_high', 'independent_worlds'])
        for n in names:
            for metric in ['event_auc', 'coverage90', 'width90', 'epistemic', 'aleatoric']:
                for e in range(3):
                    stat = summary[n][metric]
                    writer.writerow([n, e+1, metric]+[stat[k][e] for k in ['mean', 'ci95_low', 'ci95_high']]+[data['worlds']])
    # Per-event curves. Shading is CI on mean error, not predictive coverage.
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.45), sharey=True, layout='constrained')
    for e, ax in enumerate(axes):
        for n in ['Random', 'Entropy', 'ParamIG', 'Standard_OED', 'Covariance']:
            stat = summary[n]['event_rmse_curve']
            ax.plot(data['budgets'], np.asarray(stat['mean'])[:, e], label=label(n), linewidth=1.3)
            ax.fill_between(data['budgets'], np.asarray(stat['ci95_low'])[:, e],
                            np.asarray(stat['ci95_high'])[:, e], alpha=.10)
        ax.set_title(f'Activity template {e+1}')
        ax.set_xlabel('Evidence budget')
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].set_ylabel('Trajectory RMSE (fraction)')
    axes[-1].legend(fontsize=6, frameon=False)
    fig.savefig(out/'event_budget_curves.pdf')
    fig.savefig(out/'event_budget_curves.png', dpi=220)
    plt.close(fig)
    lines = ['# Frozen-method closure results', '',
             'All numbers below are synthetic. Official SocioVerse and MIT: **NOT EVALUATED**.', '',
             f"Golden test rerun: `{data['golden_result']}`. Supplement: `{result_path}`.", '',
             'Event AUC is computed before averaging across events. It differs from the golden pooled-RMSE AUC.',
             'Intervals condition on fixed training/evidence and templates. Random repetitions are averaged inside each world.', '',
             '| Method | Activity 1 AUC [95% CI] | Activity 2 | Activity 3 | Macro AUC [95% CI] |',
             '|---|---|---|---|---|']
    for n in names:
        lines.append('| '+' | '.join([label(n)]+[interval(summary[n]['event_auc'], e) for e in range(3)]+[
            interval(summary[n]['macro_auc'])])+' |')
    lines += ['', '## Paired comparisons', '',
              'Each value is comparator minus Full; positive favors Full. Same world bootstrap indices preserve pairing.', '',
              '| Comparator | Activity 1 difference [95% CI] | Activity 2 | Activity 3 |', '|---|---|---|---|']
    for n, stat in data['paired_event_auc_minus_full'].items():
        lines.append('| '+' | '.join([label(n)]+[interval(stat, e) for e in range(3)])+' |')
    lines += ['', '## Stress rules and alarm rates', '',
              'The no-shift row is false alarm rate. Shifted rows are detection rates; these are post-observation diagnostics.', '',
              '| Method / rule | Activity 1 rate [95% CI] | Activity 2 | Activity 3 |', '|---|---|---|---|']
    for row in alarm_rows:
        lines.append('| '+' | '.join(row)+' |')
    lines += ['', '## Timing', '']
    for n, v in data['timing'].items():
        lines.append(f"- {n}: median speedup {v['median_speedup']:.2f}x; max absolute score discrepancy {v['max_abs_difference']:.3g}.")
    lines += ['', '## Interpretation limits', '',
              'NoSharing changes the prior as well as sharing. Original SinglePoint chooses a different point than the evolved MAP.',
              'NoBatchDedup omits fantasy conditioning but still disallows duplicate records. Its label does not mean paying twice for one record.',
              'Per-time/channel absolute errors, both alarm definitions, and all raw worlds are in the JSON.',
              'The original cache contains three interacting events, so its per-event errors are descriptive and have no independent-event CI.',
              'Unknown waiting/propagation rules are post-freeze stress tests. No rule or detector threshold was tuned to their outcomes.',
              '95% bootstrap CIs can collapse for binary rates at zero or one with 24 worlds; they do not prove zero population risk.',
              'The 90% trajectory intervals are marginal predictive intervals, not simultaneous bands or confidence intervals.', '']
    (out/'RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(out)
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--result', required=True)
    export(p.parse_args().result)
