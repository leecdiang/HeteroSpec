"""Make the label-only Figure 2 revision and two source-bound supplement figures.

Shared styling is imported from the retained ASV-inspired drawing module.
No model, inference runtime, new measurement or other main figure is invoked.
"""
from pathlib import Path
import copy, csv, hashlib, json, re
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from visual_figures import canvas, panel, text, box, arrow, divider, clean
from visual_figures import BLUE, OCHRE, GREEN, INK, GRAY, LIGHT, PALE_BLUE, PALE_GREEN

ROOT = Path(__file__).resolve().parents[1]


def binding(path):
    return dict(path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


def save(fig, name):
    for ext in ['pdf', 'svg']:
        metadata = {'CreationDate': None, 'ModDate': None} if ext == 'pdf' else {'Date': None}
        fig.savefig(ROOT / 'figures' / f'{name}.{ext}', metadata=metadata)
    plt.close(fig)


def figure2(inputs):
    data = copy.deepcopy(inputs['figure_2_natural_crosses'])
    causal = json.loads((ROOT / 'evidence/b57065/CAUSAL_RECHECK.json').read_text())
    fig = canvas(4.15)
    fig.text(.025, .965, 'Hold the committed prefix fixed; cross natural donor state with the current recipe.', fontsize=9, color=GRAY)
    titles = ['(A) Current-path effect', '(B) State-path interaction', '(C) Retained-state effect',
              '(D) Whole-recipe interaction', '(E) Whole-recipe interaction']
    display = []
    for idx, c in enumerate(data['cases']):
        row, col = divmod(idx, 3)
        x = .035 + col * .325
        y = .55 if row == 0 else .105
        ax = panel(fig, [x, y, .29, .32], titles[idx])
        matrix = c['matrix']
        rows, columns = list(c['rows']), list(c['columns'])
        if c['platform'] == 'B570':
            checks = [v for v in causal['cases'] if v['task'] == c['task']]
            assert len(checks) == 2 and all(v['focus']['decisions'] == matrix for v in checks)
            if c['task'] == 'MBPP/72':
                assert all(v['donor_labels'] == ['N1_repaired', 'N0_ordinary'] and v['current_columns_identical'] for v in checks)
                rows = ['N1', 'N0']
            else:
                assert all(v['donor_labels'] == ['N1_repaired', 'E_k1_ub2'] for v in checks)
                assert all([(r['ub'], r['outputs_max'], r['outputs_max_per_seq']) for r in v['recipes']] == [(1, 3, 3), (2, 2, 2)] for v in checks)
                rows = ['N1', 'Alt.']
                columns = ['UB1/r3', 'UB2/r2']
        display.append(dict(platform=c['platform'], task=c['task'], rows=rows, columns=columns,
                            alternate_recipe='E_k1_ub2' if idx in [3, 4] else None))
        text(ax, .55, .91, c['platform'] + ' ' + c['task'].replace('HumanEval/', 'HE/'), fontsize=9, color=GRAY)
        for r in range(2):
            for k in range(2):
                xx, yy = .30 + k * .40, .30 + (1-r) * .30
                color = BLUE if matrix[r][k] == matrix[0][0] else OCHRE
                ax.add_patch(Rectangle((xx-.13, yy-.09), .26, .18, facecolor='white', edgecolor=color, lw=.8))
                text(ax, xx, yy, str(matrix[r][k]), fontsize=10, color=color)
            text(ax, .105, .30 + (1-r) * .30, rows[r], fontsize=9)
        for k in range(2):
            text(ax, .30 + k*.40, .065, columns[k], fontsize=8.5)
        if idx == 0:
            for yy in [.30, .60]:
                arrow(ax, (.44, yy), (.56, yy), OCHRE)
        elif idx == 2:
            for xx in [.30, .70]:
                arrow(ax, (xx, .50), (xx, .405), OCHRE)
            text(ax, .50, -.10, 'Identical current recipes', fontsize=8.3, color=GRAY)
        else:
            rr = next(r for r in range(2) if matrix[r][0] != matrix[r][1])
            yy = .30 + (1-rr) * .30
            arrow(ax, (.44, yy), (.56, yy), OCHRE)
        text(ax, .005, .75, 'Donor', fontsize=8, color=GRAY, ha='left')
    ax = panel(fig, [.685, .105, .285, .32], '(F) Continue beyond a local check')
    text(ax, .5, .91, 'B570: same-state forks', color=GRAY)
    box(ax, .05, .49, .90, .22, 'Immediate decision changes: 0 / 72', BLUE, fs=8.7)
    arrow(ax, (.5, .49), (.5, .34), GRAY)
    box(ax, .05, .08, .90, .22, 'Downstream changes: 18 / 72', OCHRE, fs=8.7)
    text(ax, .50, -.075, 'Later alternate blocks remain UB128.', fontsize=8.3, color=GRAY)
    divider(fig, .345, .095, .345, .90)
    divider(fig, .67, .095, .67, .90)
    divider(fig, .035, .50, .97, .50)
    fig.text(.5, .047, 'Alt. = E_k1_ub2; r = output reservation (total / per sequence agree here).', ha='center', fontsize=8.3, color=GRAY)
    fig.text(.5, .020, 'IDs are categorical; colors group equality within each case. Own-path shams reproduce native decisions.', ha='center', fontsize=8.3)
    save(fig, 'figure_2_natural_crosses')
    data['display_labels_v0144'] = display
    data['label_source'] = binding('evidence/b57065/CAUSAL_RECHECK.json')
    inputs['figure_2_natural_crosses'] = data


def b570(inputs):
    with (ROOT / 'evidence/b57065/COSTS_RECOMPUTED.csv').open() as stream:
        records = list(csv.DictReader(stream))
    groups = {name: [r for r in records if r['label'] == name]
              for name in ['ordinary_R', 'matched_target', 'candidate', 'old_N1']}
    complete = {name: sum(all(any(r['task'] == task and r['round'] == str(round_) for r in rows) for round_ in [1, 2])
                          for task in {r['task'] for r in records}) for name, rows in groups.items()}
    assert len(records) == 119 and [len(groups[n]) for n in groups] == [30, 30, 30, 29]
    assert [complete[n] for n in groups] == [15, 15, 15, 14]
    candidate = groups['candidate']
    endpoint = sum(int(r['endpoint_length']) for r in candidate)
    raw = sum(int(r['raw_length']) for r in candidate)
    suffix = sum(int(r['raw_suffix']) for r in candidate)
    assert (endpoint, raw, suffix) == (1150, 1176, 26)
    code = 'source_records/benchmarks/b570_mechanism_pilot_v1/code/candidate-front/'
    phase = (ROOT / (code + 'phase.h')).read_text()
    native = (ROOT / (code + 'native.cpp')).read_text()
    assert 'same_context' in phase and 'before!=after' in phase
    assert 'pilot_phase' in native and 'pending' in native
    fig = canvas(3.7)
    ax = panel(fig, [.025, .60, .95, .28], '(A) Bind phases without a second target context')
    steps = [('Ordinary prefill\nUB128; reserve 512 / 1', BLUE, PALE_BLUE),
             ('Sample pending\nfirst token once', BLUE, 'white'),
             ('Bind same context\nUB128 to UB1', GREEN, PALE_GREEN),
             ('Native k = 2 loop\nDraft UB1', OCHRE, 'white')]
    for i, (label, color, fill) in enumerate(steps):
        x = .005 + i * .255
        box(ax, x, .39, .225, .36, label, color, fill, fs=9)
        if i < 3:
            arrow(ax, (x+.225, .57), (x+.255, .57), GREEN if i == 1 else GRAY)
    text(ax, .5, .16, 'Retain target KV and the live sampler; consume / accept the saved token once.', fontsize=9)
    text(ax, .5, -.02, 'Reservation values are total / per sequence. Capture-off omits witness readbacks.', fontsize=8.5, color=GRAY)
    divider(fig, .025, .535, .975, .535)
    ax = panel(fig, [.025, .09, .51, .35], '(B) Qualify the endpoint; pay all raw work')
    box(ax, .035, .56, .93, .27, 'Endpoint: first inclusive EOG or cap128', GREEN, PALE_GREEN, fs=9)
    arrow(ax, (.5, .56), (.5, .40), GRAY)
    box(ax, .035, .08, .93, .30, '1,150 endpoint IDs + 26 suffix IDs\n= 1,176 paid raw IDs', OCHRE, fs=10)
    text(ax, .5, -.11, 'Aggregate over 30 formal candidate responses.', fontsize=8.5, color=GRAY)
    divider(fig, .555, .08, .555, .49)
    ax = panel(fig, [.585, .09, .39, .35], '(C) Keep the missing unit visible')
    text(ax, .5, .88, 'Formal matrix: 119 / 120 payloads', fontsize=9)
    for x, label in [(.10, 'Path'), (.48, 'Rows'), (.83, 'Task pairs')]:
        text(ax, x, .68, label, fontsize=8.5, color=GRAY)
    for i, name in enumerate(groups):
        yy = .50 - i * .145
        label = {'ordinary_R':'R: ordinary', 'matched_target':'M: matched', 'candidate':'C: candidate', 'old_N1':'Old N1'}[name]
        text(ax, .0, yy, label, fontsize=8.7, ha='left')
        text(ax, .48, yy, str(len(groups[name])), fontsize=9)
        text(ax, .83, yy, str(complete[name]), fontsize=9)
    text(ax, .5, -.10, 'Old N1 / MBPP400 / round 1: unavailable', fontsize=8.3, color=GRAY)
    save(fig, 'figure_S1_b570_contract')
    inputs['figure_S1_b570_contract'] = dict(endpoint_ids=endpoint, raw_ids=raw, suffix_ids=suffix,
        observations={n:len(v) for n,v in groups.items()}, complete_task_pairs=complete,
        missing='E/FORMAL/1/old_N1/MBPP/400', formal_payloads=119, planned_payloads=120,
        mechanism='source-bound schematic, not a measured timeline or component-cost profile',
        sources=[binding('evidence/b57065/COSTS_RECOMPUTED.csv'), binding(code+'phase.h'), binding(code+'native.cpp')])


def floor358h(inputs):
    summary_path = 'source_records/analysis/358h_phase3_summary.json'
    budget_path = 'source_records/paper/mlsys2027/manuscript/sections/appendix_derived_v090.tex'
    summary = json.loads((ROOT / summary_path).read_text())
    bound_source = (ROOT / budget_path).read_text()
    match = re.search(r'Full-precision \$U\$ is ([0-9.]+) CPU and ([0-9.]+) NPU', bound_source)
    assert match
    floors = dict(zip(['CPU','NPU'], map(float, match.groups())))
    points = {device: dict(actual=summary['performance'][device]['geometric_mean_speedup'],
                           interval=summary['performance'][device]['bootstrap_ci95'],
                           ceiling=floors[device], necessary_uniform_target_cut=1-floors[device])
              for device in ['CPU', 'NPU']}
    fig = canvas(2.7)
    fig.text(.025, .93, '(A) Compare measured speed with a conditional ceiling', weight='bold', fontsize=10)
    ax = fig.add_axes([.115, .28, .45, .50])
    for device, yy in [('CPU',1), ('NPU',0)]:
        p = points[device]
        value, (lo,hi) = p['actual'], p['interval']
        ax.errorbar(value, yy+.065, xerr=[[value-lo],[hi-value]], fmt='o', color=BLUE, ms=4.5, lw=.8, capsize=2)
        ax.plot(p['ceiling'], yy-.065, marker='D', ms=5, mfc='white', mec=GREEN, mew=.8)
        ax.text(value, yy+.26, f'{value:.3f}', color=BLUE, ha='center', va='bottom', fontsize=9)
        ax.text(p['ceiling'], yy-.27, f'{p["ceiling"]:.3f}', color=GREEN, ha='center', va='top', fontsize=9)
    ax.axvline(1, ls='--', lw=.7, color=GRAY)
    ax.text(1, 1.46, 'Parity', ha='center', color=GRAY, fontsize=8.5)
    ax.set(xlim=(.25,1.08), ylim=(-.45,1.55), yticks=[1,0], yticklabels=['CPU draft','NPU draft'],
           xticks=[.4,.6,.8,1.0], xlabel='Matched target-only / speculative time')
    clean(ax)
    handles=[Line2D([],[],marker='o',color=BLUE,lw=.8,markersize=4,label='Measured; saved interval'),
             Line2D([],[],marker='D',color=GREEN,lw=0,markerfacecolor='white',markersize=5,label='Zero-other-work ceiling')]
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(.48,-.26), ncol=2, frameon=False,
              fontsize=8.3, handlelength=1.1, columnspacing=.9)
    divider(fig, .615, .09, .615, .87)
    ax = panel(fig, [.65, .20, .325, .60], '(B) Budget target work')
    text(ax, .5, .86, 'Fixed baseline and committed progress\nAll other work optimistically removed', fontsize=8.7, color=GRAY)
    text(ax, .5, .58, r'$F/(1-\delta)\geq 1\quad\Rightarrow\quad\delta\geq 1-F$', fontsize=11)
    box(ax, .02, .15, .96, .27, f'CPU: at least {100*points["CPU"]["necessary_uniform_target_cut"]:.2f}%\nNPU: at least {100*points["NPU"]["necessary_uniform_target_cut"]:.2f}%', OCHRE, fs=10)
    text(ax, .5, .0, 'Necessary budgets, not achieved savings.', fontsize=8.5, color=GRAY)
    save(fig, 'figure_S2_358h_budget')
    inputs['figure_S2_358h_budget'] = dict(points=points,
        estimator='GM across 30 prompt medians of three paired ratios; separate from pooled-total accounting',
        interpretation='Conditional arithmetic bound; no ceiling CI, measured optimization or NPU impossibility claim',
        sources=[binding(summary_path), binding(budget_path)],
        raw_prompt_ceiling_audit='Inherited original-host 180-row audit; not reopened by this drawing script')


def main():
    inputs = json.loads((ROOT / 'provenance/FIGURE_INPUTS_V0142.json').read_text())
    figure2(inputs)
    b570(inputs)
    floor358h(inputs)
    out = ROOT / 'output'
    out.mkdir(exist_ok=True)
    (out / 'FIGURE_INPUTS.json').write_text(json.dumps(inputs, indent=2) + '\n')
    (ROOT / 'provenance/FIGURE_INPUTS_V0144.json').write_bytes((out / 'FIGURE_INPUTS.json').read_bytes())
    lock = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in list((ROOT / 'figures').glob('*')) + list((ROOT / 'tables').glob('*.tex'))}
    (ROOT / 'provenance/LOCKED_REVISION_ASSETS.json').write_text(json.dumps(dict(version='v0.14.4',assets=lock),indent=2)+'\n')
    print('Figure 2 labels and two supplementary figures drawn from bound sources; four other main figures untouched.')


if __name__ == '__main__':
    main()
