"""Refine the seven ASV-style vector figures without changing scientific inputs.

Colors follow reference, alternate/draft, and constraint roles across documents.
Categorical links indicate equality only, never distances or causal transitions.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from visual_figures import canvas, panel, text, box, arrow, divider, clean
from visual_figures import BLUE, OCHRE, GREEN, INK, GRAY, LIGHT
from visual_figures import PALE_BLUE, PALE_OCHRE, PALE_GREEN
from revision_figures import b570, floor358h, save

ROOT = Path(__file__).resolve().parents[1]


def spaced_box(ax, rect, label, color, fill='white', fs=8.6):
    x, y, w, h = rect
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle='round,pad=0,rounding_size=0.009',
                 edgecolor=color, facecolor=fill, linewidth=.7))
    text(ax, x+w/2, y+h/2, label, fontsize=fs)


def clear_arrow(ax, start, end):
    ax.annotate('', xy=end, xytext=start,
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=.85,
                                shrinkA=0, shrinkB=0))


def architecture():
    fig = canvas(4.2)
    a = panel(fig, [.025, .565, .43, .345], '(A) Preserve the stateful transaction')
    box(a, .02, .68, .40, .18, 'Target KV +\npending state', BLUE, PALE_BLUE, 8.8)
    box(a, .56, .68, .40, .18, 'Draft KV +\nsampler state', OCHRE, PALE_OCHRE, 8.8)
    box(a, .62, .37, .30, .17, 'Propose', OCHRE)
    box(a, .05, .37, .39, .17, 'Target verification', BLUE)
    arrow(a, (.76, .68), (.76, .54), OCHRE)
    arrow(a, (.22, .68), (.22, .54), BLUE)
    arrow(a, (.62, .455), (.44, .455), OCHRE)
    box(a, .16, .07, .66, .16, 'Accept / correct / commit / rollback', GRAY, fs=8.8)
    arrow(a, (.245, .37), (.35, .23), BLUE)
    a.plot([.16, .0, .0, .20], [.15, .15, .96, .96], color=BLUE, lw=.7)
    arrow(a, (.20, .96), (.20, .86), BLUE)
    a.plot([.82, 1, 1, .77], [.15, .15, .96, .96], color=OCHRE, lw=.7)
    arrow(a, (.77, .96), (.77, .86), OCHRE)
    text(a, .50, -.09, 'Separate target and draft ownership; no state transplant\nin the measured RTX candidate.', fontsize=8.5, color=GRAY)
    divider(fig, .48, .505, .48, .93)
    b = panel(fig, [.51, .565, .465, .345], '(B) Move query columns into the batch axis')
    text(b, .22, .88, 'Ordinary query view', color=BLUE)
    text(b, .78, .88, 'Constrained view', color=GREEN)
    for i in range(4):
        b.add_patch(Rectangle((.08+i*.065, .49), .057, .22,
                             facecolor=PALE_BLUE, edgecolor=BLUE, lw=.65))
        text(b, .108+i*.065, .60, str(i+1), fontsize=8, color=BLUE)
    text(b, .20, .35, r'$(d,q,h,1)$', fontsize=11)
    arrow(b, (.38, .60), (.59, .60), GREEN)
    text(b, .48, .75, 'view', fontsize=8.5, color=GREEN)
    for i in range(4):
        x, y = .66+i*.058, .47+i*.047
        b.add_patch(Rectangle((x, y), .048, .22,
                             facecolor=PALE_GREEN, edgecolor=GREEN, lw=.65))
        text(b, x+.024, y+.11, str(i+1), fontsize=8, color=GREEN)
    text(b, .78, .35, r'$(d,1,h,q)$', fontsize=11)
    text(b, .5, .12, 'K/V broadcast across query batches', fontsize=9)
    text(b, .5, -.04, r'Mask: $(n_{\rm KV},q,1,1)\;\rightarrow\;(n_{\rm KV},1,1,q)$', fontsize=9)
    text(b, .5, -.19, 'Projection, output projection and FFN remain batched.', fontsize=8.5, color=GRAY)
    divider(fig, .025, .455, .975, .455)
    rect = [.025, .075, .95, .29]
    c = panel(fig, rect, '(C) Select the graph by role and phase')
    nodes = [(.005, .57, .182, .29), (.224, .57, .182, .29),
             (.005, .10, .182, .29), (.224, .10, .182, .29)]
    labels = ['Target prefill\nbit 1', 'Target continuation\nbit 2',
              'Draft prefill\nbit 4', 'Draft continuation\nbit 8']
    for i, (node, label) in enumerate(zip(nodes, labels)):
        spaced_box(c, node, label, BLUE if i < 2 else OCHRE,
                   PALE_BLUE if i < 2 else PALE_OCHRE)
    # A bracket gathers all four switches; no individual box-to-box arrows.
    c.plot([.424, .436, .436, .424], [.87, .87, .08, .08], color=GRAY, lw=.75)
    guard = [.51, .28, .116, .40]
    flag = [.69, .28, .131, .40]
    reuse = [.885, .28, .114, .40]
    spaced_box(c, guard, 'Scope\nguard', GREEN, PALE_GREEN)
    spaced_box(c, flag, 'Graph flag\nactive / inactive', GREEN, PALE_GREEN, fs=8.3)
    spaced_box(c, reuse, 'Reuse only if\nflag matches', GREEN, fs=8.3)
    arrows = [[.454, .492], [.644, .672], [.839, .867]]
    for x0, x1 in arrows:
        clear_arrow(c, (x0, .48), (x1, .48))
    fig.text(.50, .018, 'Implemented scope: Qwen3, non-flash attention, one KV stream; see Section 5 for guards.',
             ha='center', fontsize=8.5, color=GRAY)
    save(fig, 'figure_1_architecture')
    return dict(panel_rect=rect, phase_boxes=nodes, scope_guard=guard,
                graph_flag=flag, reuse=reuse, group_bracket_x=.436,
                arrow_intervals=arrows, arrow_y=.48, box_padding=0,
                horizontal_phase_gap_pt=(.224-.187)*.95*7.2*72,
                vertical_phase_gap_pt=(.57-.39)*.29*4.2*72)


def relation(ax, start, end, different):
    color = OCHRE if different else GRAY
    ax.plot([start[0], end[0]], [start[1], end[1]], color=color, lw=.85, zorder=1)
    mid = [(a+b)/2 for a, b in zip(start, end)]
    text(ax, *mid, r'$\ne$' if different else '=', fontsize=10.5, color=color,
         bbox=dict(facecolor='white', edgecolor='none', pad=.2), zorder=3)


def natural_crosses(data):
    fig = canvas(4.15)
    fig.text(.025, .965, 'Hold the committed prefix fixed; cross natural donor state with the current recipe.', fontsize=9, color=GRAY)
    titles = ['(A) Current-path effect', '(B) State-path interaction', '(C) Retained-state effect',
              '(D) Whole-recipe interaction', '(E) Whole-recipe interaction']
    adjacency = []
    for idx, (case, display) in enumerate(zip(data['cases'], data['display_labels_v0144'])):
        row, col = divmod(idx, 3)
        ax = panel(fig, [.035+col*.325, .55 if row == 0 else .105, .29, .32], titles[idx])
        matrix = case['matrix']
        text(ax, .565, .945, case['platform']+' '+case['task'].replace('HumanEval/', 'HE/'), fontsize=9, color=GRAY)
        text(ax, .005, .89, 'Donor', fontsize=8, color=GRAY, ha='left')
        hdiff = [matrix[r][0] != matrix[r][1] for r in range(2)]
        vdiff = [matrix[0][k] != matrix[1][k] for k in range(2)]
        for r, yy in enumerate([.725, .285]):
            relation(ax, (.465, yy), (.645, yy), hdiff[r])
        for k, xx in enumerate([.34, .77]):
            relation(ax, (xx, .64), (xx, .37), vdiff[k])
        for r, yy in enumerate([.725, .285]):
            for k, xx in enumerate([.34, .77]):
                anchor = matrix[r][k] == matrix[0][0]
                color, fill = (BLUE, PALE_BLUE) if anchor else (OCHRE, PALE_OCHRE)
                spaced_box(ax, [xx-.125, yy-.085, .25, .17], str(matrix[r][k]), color, fill, fs=10.5)
            text(ax, .09, yy, display['rows'][r], fontsize=9)
        for k, xx in enumerate([.34, .77]):
            text(ax, xx, .075, display['columns'][k], fontsize=8.5)
        if idx == 2:
            text(ax, .53, -.10, 'Identical current recipes', fontsize=8.3, color=GRAY)
        adjacency.append(dict(platform=case['platform'], task=case['task'],
                              horizontal_different=hdiff, vertical_different=vdiff))
    ax = panel(fig, [.685, .105, .285, .32], '(F) Continue beyond a local check')
    text(ax, .5, .935, 'B570: same-state forks', color=GRAY)
    for y, label, count in [(.67, 'Immediate changes', data['immediate_changed']),
                             (.29, 'Downstream changes', data['downstream_changed'])]:
        text(ax, .04, y+.10, label, fontsize=9, ha='left')
        text(ax, .96, y+.10, f'{count} / {data["forks"]}', fontsize=10.5,
             color=OCHRE if count else BLUE, ha='right')
        fraction = count/data['forks']
        ax.add_patch(Rectangle((.04, y-.045), .92, .09,
                              facecolor=PALE_BLUE, edgecolor=BLUE, lw=.65))
        if count:
            ax.add_patch(Rectangle((.04, y-.045), .92*fraction, .09,
                                  facecolor=OCHRE, edgecolor=OCHRE, lw=.65))
    text(ax, .50, .035, 'Same 72 forks in each check.\nLater alternate blocks remain UB128.', fontsize=8.3, color=GRAY)
    divider(fig, .345, .095, .345, .90)
    divider(fig, .67, .095, .67, .90)
    divider(fig, .035, .50, .97, .50)
    fig.text(.5, .047, 'Alt. = E_k1_ub2; r = output reservation (total / per sequence agree here).', ha='center', fontsize=8.3, color=GRAY)
    fig.text(.5, .020, r'Links: = same ID; $\ne$ different ID. IDs are categorical. Own-path shams reproduce native decisions.', ha='center', fontsize=8.3)
    save(fig, 'figure_2_natural_crosses')
    return adjacency


def phase_matrix(data):
    fig = canvas(3.85)
    a = fig.add_axes([.065, .16, .57, .67])
    fig.text(.025, .94, '(A) Locate a sufficient phase scope', weight='bold', fontsize=10)
    fig.text(.33, .88, 'Constraints enabled                  Full-response match', ha='center', fontsize=8.5, color=GRAY)
    for entry in data['factorial']:
        r = entry['mask']
        if r == 3:
            a.add_patch(Rectangle((-.52, r-.48), 8.13, .96, facecolor=PALE_GREEN, edgecolor=GREEN, lw=.9, zorder=0))
        for j, enabled in enumerate(entry['bits']):
            color = BLUE if j < 2 else OCHRE
            a.scatter(j, r, marker='s', s=20, facecolors=color if enabled else 'white',
                      edgecolors=color if enabled else LIGHT, linewidths=.6)
        for j, passes in enumerate(entry['probe_passes'], 4):
            a.scatter(j, r, marker='o' if passes else 'x', s=19 if passes else 21,
                      color=GREEN if passes else OCHRE, linewidths=.75)
        if entry['qualifies']:
            a.text(7.52, r, '*' if r == 3 else '+', color=GREEN, va='center', ha='center', weight='bold', fontsize=11)
    a.axvline(3.5, color=LIGHT, lw=.6)
    a.set(xlim=(-.5, 7.8), ylim=(15.6, -.7))
    a.set_xticks(range(8), ['T-P', 'T-C', 'D-P', 'D-C', '/15', '/18', '/25', '/31'])
    a.xaxis.tick_top()
    a.tick_params(length=0, pad=4)
    a.set_yticks(range(16), [f'{i:02}' for i in range(16)], fontsize=8)
    a.set_ylabel('Phase mask', fontsize=9, labelpad=7)
    for spine in a.spines.values():
        spine.set_visible(False)
    fig.text(.065, .075, 'T / D: target / draft; P / C: prefill / continuation', fontsize=8.3)
    fig.text(.065, .035, 'Filled square: enabled.  * minimal mask 3; + passing supersets', fontsize=8.3, color=GREEN)
    divider(fig, .645, .075, .645, .95)
    b = panel(fig, [.68, .14, .29, .72], '(B) Recheck wider geometry')
    text(b, .52, .88, 'Full-panel output qualification', fontsize=8.5, color=GRAY)
    for i, (k, ub) in enumerate(zip([1, 3, 5, 7], [2, 4, 6, 8])):
        text(b, .01, .64-i*.135, f'{k} / {ub}', fontsize=9, ha='left')
        for j, cap in enumerate([128, 256, 512]):
            entry = next(r for r in data['geometry'] if (r['k'], r['UB'], r['cap']) == (k, ub, cap))
            ok = entry['qualifies']
            b.scatter(.40+j*.25, .64-i*.135, marker='o' if ok else 'x', s=30,
                      color=GREEN if ok else OCHRE, linewidths=.9)
    text(b, .01, .79, r'$k$ / UB', fontsize=9, ha='left')
    for j, cap in enumerate([128, 256, 512]):
        text(b, .40+j*.25, .79, str(cap), fontsize=9)
    b.plot([0, .97], [.73, .73], color=LIGHT, lw=.6)
    text(b, .49, .08, '11 inputs; fresh references at each cap.\nMBPP/229 fails at UB6 and UB8.', fontsize=8.5)
    text(b, .49, -.045, 'Cap 512 is a limit; observed length ≤ 261.', fontsize=8.1, color=GRAY)
    fig.text(.68, .025, '● match     × failure     (two repeats)', fontsize=8.2, color=GRAY)
    save(fig, 'figure_3_phase_matrix')


def paid_cost(data):
    fig = canvas(3.7)
    a = panel(fig, [.03, .69, .94, .22], '(A) Separate the two design decisions')
    box(a, .015, .15, .245, .57, 'R: ordinary target only\nmask 0 / UB1', BLUE, PALE_BLUE, fs=9)
    box(a, .385, .15, .245, .57, 'M: constrained target only\nmask 3 / UB4', GREEN, PALE_GREEN, fs=9)
    box(a, .755, .15, .23, .57, 'C: constrained speculation\nmask 3 / UB4 / k = 3', OCHRE, PALE_OCHRE, fs=8.8)
    arrow(a, (.265, .42), (.38, .42))
    arrow(a, (.635, .42), (.75, .42))
    text(a, .322, .87, 'Change target path', fontsize=8.2, color=GREEN)
    text(a, .695, .87, 'Add draft', fontsize=8.2, color=OCHRE)
    comps = [('scalar_reference', 'target_scopes', 'Deployment  R/C', GRAY, 'D'),
             ('scalar_reference', 'matched_target', 'Target path  R/M', GREEN, 's'),
             ('matched_target', 'target_scopes', 'Draft increment  M/C', OCHRE, 'o')]
    for rect, timer, title in [([.24, .245, .29, .335], 'generation', '(B) Generation'),
                               ([.66, .245, .30, .335], 'whole', '(C) Resident request')]:
        ax = fig.add_axes(rect)
        clean(ax)
        ax.axvline(1, color=GRAY, lw=.75, ls='--')
        for y, (baseline, candidate, label, color, marker) in enumerate(comps):
            entry = next(s for s in data['comparisons'] if (s['timer'], s['baseline'], s['candidate']) == (timer, baseline, candidate))
            value, (lo, hi) = entry['ratio'], entry['interval']
            ax.errorbar(value, y, xerr=[[value-lo], [hi-value]], fmt=marker, ms=4.7, capsize=2, color=color, lw=.8, zorder=4)
            ax.annotate(f'{value:.3f}×', (value, y), xytext=(0, 9), textcoords='offset points', ha='center', fontsize=9, color=color)
        ax.set_ylim(2.6, -.65)
        ax.set_title(title, loc='left', weight='bold', fontsize=10, pad=12)
        ax.set_xlim((.975, 1.255) if timer == 'generation' else (.95, 1.91))
        ax.set_yticks(range(3), [r[2] for r in comps] if timer == 'generation' else ['R/C', 'R/M', 'M/C'])
        ax.set_xlabel('Baseline / compared-path time', fontsize=8.5)
    divider(fig, .59, .17, .59, .61)
    fig.text(.5, .073, r'Request ratios: $1.742 \simeq 1.683 \times 1.035$; most deployment gain exists without a draft.', ha='center', fontsize=9)
    fig.text(.5, .025, 'Different timer intervals and x-axis ranges; ratios are multiplicative comparisons, not component costs.', ha='center', fontsize=8.5, color=GRAY)
    save(fig, 'figure_4_paid_cost')


def task_variation(data):
    fig = canvas(4.65)
    order = data['order']
    for rect, timer, title in [([.07, .23, .28, .62], 'generation', '(A) Generation'),
                               ([.405, .23, .28, .62], 'whole', '(B) Resident request')]:
        ax = fig.add_axes(rect)
        clean(ax)
        ax.axvline(1, color=GRAY, lw=.75, ls='--')
        values = [data['ratios'][timer][task] for task in order]
        gm = float(np.exp(np.mean(np.log(values))))
        for i, value in enumerate(values):
            ax.scatter(value, i, marker='o' if value > 1 else '<', s=18,
                       facecolors=OCHRE if value > 1 else 'white', edgecolors=OCHRE, lw=.8, zorder=3)
        ax.axvline(gm, color=OCHRE, lw=.6, ls=':')
        ax.set(xlim=(.80, 1.48), ylim=(23.7, -.7))
        ax.set_xticks([.8, 1, 1.2, 1.4])
        ax.set_yticks(range(24), [task.split('/')[-1] for task in order] if timer == 'generation' else ['']*24, fontsize=8)
        ax.set_title(title, loc='left', weight='bold', fontsize=10, pad=23)
        ax.text(.5, 1.03, f'{sum(x > 1 for x in values)}/24 faster; GM {gm:.3f}', ha='center', transform=ax.transAxes, fontsize=9, color=OCHRE)
        ax.set_xlabel('Matched / speculative time', fontsize=8.5)
        if timer == 'generation':
            ax.set_ylabel('MBPP task (shared request-sorted order)', fontsize=8.5)
    divider(fig, .715, .14, .715, .94)
    ax = fig.add_axes([.80, .51, .17, .34])
    clean(ax)
    ax.axvline(1, color=GRAY, lw=.75, ls='--')
    for i, entry in enumerate(data['rounds']):
        value = entry['gm']
        ax.scatter(value, i, marker='o' if value > 1 else '<', s=25,
                   facecolors=OCHRE if value > 1 else 'white', edgecolors=OCHRE, lw=.9, zorder=3)
        ax.annotate(f'{value:.3f}', (value, i), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8.5)
    ax.set(xlim=(.91, 1.075), ylim=(3.6, -.65))
    ax.set_yticks(range(4), ['1', '2', '3', '4'])
    ax.set_xticks([.94, 1, 1.06])
    ax.set_ylabel('Round', fontsize=8.5)
    ax.set_title('(C) Request rounds', weight='bold', fontsize=10, pad=23, loc='center')
    ax.set_xlabel('Matched / speculative', fontsize=8)
    fig.text(.875, .32, 'Round 2 reverses\nthe aggregate direction.', ha='center', fontsize=9, color=OCHRE)
    fig.text(.875, .21, '24 task pairs per round;\nno session-level interval\nis inferred.', ha='center', fontsize=8.5, color=GRAY)
    fig.text(.50, .075, 'Filled circles: faster     Open left triangles: slower     Dashed: parity     Dotted: task-median GM', ha='center', fontsize=8.5)
    fig.text(.50, .022, 'A and B share the same x-axis scale and task order; C reports round GMs, not task-median aggregation.', ha='center', fontsize=8.4, color=GRAY)
    save(fig, 'figure_5_task_variation')


def main():
    inputs = json.loads((ROOT/'provenance/INITIAL_V0144_FIGURE_INPUTS.json').read_text())
    manifest_path = ROOT/'provenance/SEMANTIC_VISUAL_REVISION.json'
    manifest = json.loads(manifest_path.read_text())
    geometry = architecture()
    adjacency = natural_crosses(inputs['figure_2_natural_crosses'])
    phase_matrix(inputs['figure_3_phase_matrix'])
    paid_cost(inputs['figure_4_paid_cost'])
    task_variation(inputs['figure_5_task_variation'])
    b570(inputs)
    floor358h(inputs)
    original = json.loads((ROOT/'provenance/INITIAL_V0144_FIGURE_INPUTS.json').read_text())
    assert inputs == original, 'Scientific inputs must remain exactly unchanged'
    inputs['semantic_visual_revision'] = dict(figure1c_geometry=geometry,
        figure2_categorical_adjacency=adjacency, palette_roles=manifest['palette_roles'],
        figure_roles=manifest['figure_roles'], relational_links='Undirected equality/difference only',
        continuation_bars='Aggregate fractions; no ordering, timing or trajectory is implied')
    for target in [ROOT/'output/FIGURE_INPUTS.json', ROOT/'provenance/FIGURE_INPUTS_V0144.json']:
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(inputs, indent=2)+'\n')
    assets = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(list((ROOT/'figures').glob('*'))+list((ROOT/'tables').glob('*.tex')))}
    (ROOT/'provenance/LOCKED_REVISION_ASSETS.json').write_text(json.dumps(dict(version='v0.14.4', assets=assets), indent=2)+'\n')
    manifest['current_asset_sha256'] = {name: assets[name] for name in manifest['initial_asset_sha256']}
    manifest['renderer_sha256'] = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                 for name in ['scripts/semantic_figures.py', 'scripts/revision_figures.py']}
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    print('Seven vector figures refined; all seven original scientific-input objects equal.')


if __name__ == '__main__':
    main()
