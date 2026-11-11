"""Recompute the newly incorporated B2 panel from all published operations.

Inputs are commit-pinned public timing records. This script performs arithmetic
reconstruction; native numerical qualification is documented in the source study.
"""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib, json, math

P = Path(__file__).resolve().parents[1]
p = P / 'data_added/b2_matched_history_public_stats.json'
b = p.read_bytes()
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest() == '61a27fc5a230179ba6b17231605bf8c486a18ff3'
d = json.loads(b)
obs = d['observations']
assert len(obs) == 128
assert Counter(o['role'] for o in obs) == {'warm':64,'measured':64}
assert len({(o['worker'],o['role'],o['ordinal']) for o in obs}) == 128
workers = defaultdict(lambda: defaultdict(list))
for o in obs:
    assert math.isfinite(o['operation_s']) and o['operation_s'] > 0
    workers[(o['core'],o['boundary'],o['worker'])][(o['role'],o['path'])].append(o['operation_s'])
assert len(workers) == 16
for v in workers.values():
    assert set(v) == {('warm','q4pair'),('warm','q8'),('measured','q4pair'),('measured','q8')}
    assert all(len(a)==2 for a in v.values())
rows=[];table=[]
for c in d['contrasts']:
    ratios=[sum(v['measured','q8'])/sum(v['measured','q4pair'])
            for k,v in workers.items() if k[:2] == (c['core'],c['boundary'])]
    assert len(ratios)==4
    for a,e in zip(ratios,c['process_ratios']):
        assert math.isclose(a,e,rel_tol=0,abs_tol=2e-14)
    g=math.exp(sum(map(math.log,ratios))/len(ratios))
    assert math.isclose(g,c['geometric_B_over_A'],rel_tol=0,abs_tol=2e-14)
    rows.append(dict(core=c['core'],prefix_coordinate=c['boundary'],process_ratios=ratios,
                     geometric_ratio=g,observed_range=[min(ratios),max(ratios)]))
    label='Loop4' if c['core']=='loop4' else 'Packed'
    table.append(f"{label} & {c['boundary']} & {g:.4f} & {min(ratios):.4f}--{max(ratios):.4f} \\\\")
out=dict(status='PASS',source_commit='4fe337a8ff349d547023f9dd60b8e114e5323207',
         source_path='benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_B2_20261110/INDEPENDENT_PUBLIC_STATS_01.json',
         source_blob='61a27fc5a230179ba6b17231605bf8c486a18ff3',source_sha256=hashlib.sha256(b).hexdigest(),
         operations_checked=128,measurements=64,warmups=64,processes=16,root_count=1,
         summaries=rows,interval_type='Observed process range; no population confidence interval',new_GPU_requests=0)
(P/'generated/B2_RECHECK.json').write_text(json.dumps(out,indent=2)+'\n')
(P/'generated/b2_rows.tex').write_text('\n'.join(table)+'\n')
(P/'generated/b2_macro.tex').write_text('\\newcommand{\\BTwoRows}{%\n'+'\n'.join(table)+'\n}\n')
print('B2 reconstruction PASS: 128 operations, 16 process ratios, 4 geometric summaries.')
