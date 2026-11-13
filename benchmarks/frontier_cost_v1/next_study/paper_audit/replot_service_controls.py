"""Restore the fifth published service contrast; no model or timing execution.

Recompute ratios from source totals. Preserve the originally published root
points and adjusted intervals; root ratios alone cannot reconstruct their
ratio-of-totals bootstrap. Render a review figure without editing PR222.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

SOURCES = {
    'q8.json': ('2831e6b24d3c649a4f808de09b28ecd99877a91d',
        '592abdfe9267fd97ecbde18cd0ee9a1bfc319e20',
        'benchmarks/linux_transfer_v1/results_ampere_20261107/RESULTS.json'),
    'q14.json': ('0bee0c05f8ba2bafc8ac0f938eec2c1f9cfa3fb3',
        '0e9bb82432dc0a860a43ab9ba1c034f41176fe05',
        'benchmarks/server_expansion_v1/D14/results_complete_20261108/RESULTS_REPRODUCED.json'),
    'llama.json': ('1df7f9e06761b9aa10f90cea191d55b7ae0f46c2',
        '8990a80da23f75c071d6d161c8c79a2dc1347bd7',
        'benchmarks/server_expansion_v1/F/results_confirmation_20261108/RESULTS_REPRODUCED.json'),
    'data/applications.json': ('2b0436803117dabf99b4699534944633a4b16f8c',
        'e8a4981ef7db8f05cff7144fd4edc6e5a4109343',
        'papers/reference_compatible/20261111_tpds_mainline_rewrite/data/applications.json'),
}
CONTROLS = ('W_L4_M', 'W_P_M', 'L_L4_M', 'L_P_M', 'W_L4_D4')
MODELS = ('Qwen3-8B', 'Qwen3-14B', 'Llama-8B')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pinned_read(directory, name):
    raw = (directory / name).read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    require(blob == SOURCES[name][0], 'Source Git blob differs: ' + name)
    return json.loads(raw), {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                            'git_blob': blob, 'commit': SOURCES[name][1],
                            'repository_path': SOURCES[name][2]}


def derive(directory):
    manuscript, paper_pin = pinned_read(directory, 'data/applications.json')
    results = []
    pins = {'data/applications.json': paper_pin}
    for index, name in enumerate(('q8.json', 'q14.json', 'llama.json')):
        raw, pins[name] = pinned_read(directory, name)
        paper = manuscript[index]
        totals = raw.get('totals_s', raw.get('totals'))
        contrasts = raw.get('contrasts', raw.get('all_fixed_controls'))
        require(set(totals) == set(CONTROLS) | {'L_P_D4'}, 'Six-arm coverage')
        require(len(contrasts) == 5, 'Five-contrast family must be complete')
        require([c['denominator'] for c in contrasts] == list(CONTROLS), 'Published control ordering')
        require(all(c['numerator'] == 'L_P_D4' for c in contrasts), 'Candidate differs')
        for arm in totals:
            require(math.isfinite(totals[arm]) and totals[arm] > 0, 'Invalid total')
            require(abs(totals[arm] - paper['totals'][arm]) < 1e-10, 'Manuscript/source total mismatch')
        rows = []
        for j, contrast in enumerate(contrasts):
            denominator = contrast['denominator']
            ratio = totals['L_P_D4'] / totals[denominator]
            interval = contrast.get('adjusted_interval', contrast.get('interval'))
            points = contrast.get('per_root', contrast.get('root_ratios'))
            require(abs(ratio - contrast['total_ratio']) < 1e-12, 'Source ratio mismatch')
            require(abs(ratio - paper['reported_ratios'][j]) < 1e-12, 'Manuscript ratio mismatch')
            require(interval == paper['reported_intervals'][j], 'Published interval differs')
            require(len(points) == paper['roots'], 'Missing root points')
            require(all(math.isfinite(v) and v > 0 for v in points), 'Invalid root point')
            require(len(interval) == 2 and 0 < interval[0] <= interval[1], 'Invalid interval')
            rows.append({'control': denominator, 'ratio_of_totals': ratio,
                         'reduction_fraction': 1 - ratio,
                         'published_adjusted_99pct_interval': interval,
                         'published_root_ratios': points,
                         'interval_recomputed_here': False,
                         'joint_cut_and_packing_control': denominator == 'W_L4_D4'})
        if index == 0:
            windows = raw['host_windows']
            require(len(windows) == 24 and len({x['id'] for x in windows}) == 24,
                    'Qwen8B worker coverage')
            worker = defaultdict(float)
            for value in windows:
                session, arm = value['id'].split('-', 1)
                require(session in ('s0', 's1', 's2', 's3') and arm in totals,
                        'Unexpected worker identity')
                elapsed = value['clocks']['worker_wall_s']
                require(math.isfinite(elapsed) and elapsed > 0, 'Invalid worker time')
                worker[arm] += elapsed
            rounded = False
        else:
            worker = paper['process_s']
            rounded = paper['process_values_rounded']
        control = 'W_L4_D4'
        results.append({'model': MODELS[index], 'root_count': paper['roots'],
            'formal_per_arm': paper['formal_per_arm'], 'totals_s': totals,
            'means_s': {a: t / paper['formal_per_arm'] for a, t in totals.items()},
            'contrasts': rows, 'source_caveat': paper['caveat'],
            'strong_speculative_control': {
                'resident_reduction_fraction': rows[-1]['reduction_fraction'],
                'native_worker_control_s': worker[control],
                'native_worker_candidate_s': worker['L_P_D4'],
                'native_worker_reduction_fraction': 1 - worker['L_P_D4'] / worker[control],
                'worker_source_values_rounded': rounded,
                'worker_interval': None,
                'worker_scope': 'Original worker lifecycle, including initialization/warmup; no new measurement or deployed response-latency claim.'}})
    return {'schema': 'heterospec.service-fifth-contrast.v1',
        'status': 'RECOMPUTED_FIXED_PUBLIC_SUMMARIES', 'sources': pins,
        'studies': results, 'contrasts': 15, 'root_points': 220,
        'new_GPU_requests': 0, 'new_model_requests': 0,
        'limitations': [
            'Published root-bootstrap intervals retained verbatim; not independently resampled from absolute root times.',
            'Fifth contrast changes both cut and projection. Balanced factorial studies remain the component-attribution evidence.',
            'Qwen8B two D4 arms retain the same relative order; conditional root intervals do not address temporal-order confounding.',
            'Qwen8B and Qwen14B reuse root identities; three deployments are not 44 independent new tasks.',
            'Per-phase same-panel decomposition is not supplied by these projections and is not reconstructed by mixing studies.',
            'Worker summaries have a different lifecycle; no population interval is inferred for them.',
            'This is a review figure, not an edited manuscript or a new performance experiment.']}


def render(result, out):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager, transforms
    from matplotlib.collections import PathCollection
    # Reuse PR222's palette, type family, line weights and root/interval semantics.
    blue, orange, gray, rule, ink, light = '#3F6C9B', '#B8753B', '#62696D', '#D4D7D9', '#202326', '#A2A9AE'
    font = Path('/usr/share/fonts/opentype/urw-base35/P052-Roman.otf')
    for weight in ('Roman', 'Italic', 'Bold', 'BoldItalic'):
        candidate = font.with_name('P052-' + weight + '.otf')
        if candidate.exists():
            font_manager.fontManager.addfont(str(candidate))
    family = font_manager.FontProperties(fname=str(font)).get_name() if font.exists() else 'STIXGeneral'
    plt.rcParams.update({'font.family': family, 'font.size': 8.3, 'axes.linewidth': .55,
        'axes.edgecolor': gray, 'text.color': ink, 'axes.labelcolor': ink,
        'xtick.color': ink, 'ytick.color': ink, 'axes.spines.top': False,
        'axes.spines.right': False, 'svg.fonttype': 'none', 'figure.facecolor': 'white',
        'savefig.facecolor': 'white', 'mathtext.fontset': 'stix'})
    fig = plt.figure(figsize=(6.875, 4.7))
    ax = fig.add_axes([.32, .205, .515, .65])
    transform = transforms.blended_transform_factory(fig.transFigure, ax.transData)
    def label(x, y, value, **kw):
        return ax.text(x, y, value, transform=transform, clip_on=False, **kw)
    labels = ('Whole · loop4 M', 'Whole · packed M', 'Local · loop4 M',
              'Local · packed M', 'Whole · loop4 D4')
    for i, study in enumerate(result['studies']):
        ys = [17.8 - 6.0*i - j for j in range(5)]
        label(.018, ys[0] + .83, study['model'] + ' / ' + str(study['root_count']) + ' roots',
              ha='left', va='center', fontsize=8.7, fontweight='bold')
        a, b = study['means_s']['W_L4_D4'], study['means_s']['L_P_D4']
        label(.355, ys[0] + .83, f'D4 control {a:.3f} s → candidate {b:.3f} s',
              ha='left', va='center', fontsize=7.9, color=gray,
              bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1})
        for j, (y, contrast) in enumerate(zip(ys, study['contrasts'])):
            strong = j == 4; color = orange if strong else blue
            points = np.asarray(contrast['published_root_ratios'])
            ax.scatter(points, y + np.linspace(-.17, .17, len(points)), s=7,
                       c=light, alpha=.85, zorder=2, linewidths=0)
            interval = contrast['published_adjusted_99pct_interval']
            ax.plot(interval, [y, y], color=color, lw=1.35, zorder=3, solid_capstyle='round')
            for edge in interval:
                ax.plot([edge, edge], [y-.08, y+.08], color=color, lw=.7, zorder=3)
            ax.scatter(contrast['ratio_of_totals'], y, marker='D', s=27,
                       facecolors=color, edgecolors=color, linewidths=.9, zorder=4)
            label(.058, y, labels[j], ha='left', va='center', fontsize=8.1,
                  fontweight='bold' if strong else 'normal', color=color if strong else ink)
            label(.982, y, f"{100*contrast['reduction_fraction']:.2f}%",
                  ha='right', va='center', fontsize=8.5, color=color,
                  fontweight='bold' if strong else 'normal')
    for y in (12.95, 6.95):
        ax.plot([.54, 1.055], [y, y], color=rule, lw=.6)
    ax.axvline(1, color=gray, lw=.85, ls=(0, (3, 2)), zorder=1)
    ax.set(xlim=(.54, 1.055), ylim=(1.0, 19.15), xticks=[.6, .7, .8, .9, 1], yticks=[])
    ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=rule, lw=.45); ax.set_axisbelow(True)
    ax.set_xlabel('LOCAL-packed D4 / fixed control service time', labelpad=5)
    fig.text(.018, .966, 'Resident service with the strong speculative control · A5000',
             fontsize=9.2, fontweight='bold')
    fig.text(.058, .906, 'Fixed control', fontsize=8, color=gray)
    fig.text(.982, .906, 'Time reduction', fontsize=8, color=gray, ha='right')
    fig.text(.815, .906, '1 = equal time', fontsize=7.8, color=gray, ha='right')
    notes = [
        'Faint points: all roots. Lines: published adjusted 99% intervals. Diamonds: ratios of totals.',
        'Orange: same-panel speculative control; cut and projection change together.',
        'Qwen3-8B keeps the D4 arms in one relative order; intervals do not remove order bias.']
    for i, note in enumerate(notes):
        fig.text(.018, .094 - .028*i, note, fontsize=7.7, color=gray)
    fig.canvas.draw(); renderer = fig.canvas.get_renderer(); width, height = fig.canvas.get_width_height()
    outside = []
    for text in fig.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text(): continue
        box = text.get_window_extent(renderer)
        if box.x0 < -.5 or box.y0 < -.5 or box.x1 > width+.5 or box.y1 > height+.5:
            outside.append(text.get_text())
    points = [point for collection in ax.collections if isinstance(collection, PathCollection)
              for point in collection.get_offsets()]
    require(not outside, 'Text outside canvas: ' + str(outside))
    require(len(points) == 235, '15 estimates + 220 root markers required')
    require(all(.54 <= x <= 1.055 and 1.0 <= y <= 19.15 for x, y in points), 'Clipped data point')
    for extension in ('svg', 'png'):
        fig.savefig(out / ('service_controls_with_strong_baseline.' + extension), dpi=300,
                    metadata={'Date': None} if extension == 'svg' else None)
    plt.close(fig)
    return {'status': 'RENDERED_REVIEW_FIGURE', 'font_family': family,
            'plotted_markers': len(points), 'root_points': 220, 'point_estimates': 15,
            'clipped_points': 0, 'text_outside_canvas': outside,
            'style_source_commit': 'e8a4981ef7db8f05cff7144fd4edc6e5a4109343',
            'style_source_blob': 'b46c26b7214c6b54ba1b7d74d61530503798adee',
            'manuscript_edited': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    require(not args.out.exists(), 'Fresh output directory required')
    result = derive(args.sources)
    args.out.mkdir(parents=True)
    result['analyzer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (args.out/'RESULTS.json').write_text(json.dumps(result, indent=2)+'\n')
    rendered = render(result, args.out)
    (args.out/'FIGURE_CHECK.json').write_text(json.dumps(rendered, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'contrasts': 15, 'root_points': 220,
                      'new_GPU_requests': 0, 'figure': rendered['status']}))


if __name__ == '__main__':
    main()
