"""Cross-check the summary tables against executed native records and checkpoint bytes."""
from pathlib import Path
import json,hashlib,math
from functools import lru_cache
def verification(root):
    root=Path(root)
    def read(p):return json.loads(p.read_text(encoding='utf-8'))
    @lru_cache
    def records(pattern):
        result=[]
        for f in sorted((root/'units').glob(pattern)):
            native=f/'native/result.json'
            if native.is_file():result.extend(read(native).get('records',[]))
        return result
    def grid(rows,g):
        match=[r for r in rows if r['slot']['base']==g['head'] and len(r['slot']['ids'])==g['q'] and r['slot']['arm']==g['arm']]
        if match:
            assert all(r['greedy']==match[0]['greedy'] and r['vectors']==match[0]['vectors'] for r in match)
            return match[0]
    cells=0;timings=0;states=0
    for f in root.glob('CONTROL-*.json'):
        for g in read(f):
            tag=f'ctlB-{g["family"]}-{g["C"]}-b{g["B"]}'
            a=grid(records(tag+'-'+g['arm']+'-*'),g)
            rows=records(tag+'-R-*')
            if g['family']=='qwen' and g['C']==1024:rows=rows+records('r-grid-qwen-1024*')
            r=grid(rows,dict(g,arm='S1'))
            assert (a['vectors'] if a else None)==g['actual_vectors']
            assert (r['vectors'] if r else None)==g['reference_vectors']
            if a:assert a['graph_calls']==g['graph_calls'] and a['greedy']==g['greedy']
            cells+=1
    for f in root.glob('SCALAR-*.json'):
        for g in read(f):
            a=grid(records(f'scalar1-{g["family"]}-{g["C"]}-b{g["B"]}-*'),g)
            if a:assert a['slot']['ub']==1
            assert (a['vectors'] if a else None)==g['actual_vectors']
            assert bool(a and g['reference_vectors'] and a['vectors']==g['reference_vectors'])==g['equal']
    for f in root.glob('TIMES-*.json'):
        for g in read(f):
            tag=f'timeB-{g["family"]}-{g["C"]}-b{g["B"]}-r{g["rep"]}'
            a=grid(records(tag+'-*'),g)
            assert (a['seconds'] if a else None)==g['seconds'];timings+=1
    if (root/'NATURAL_COST.json').exists():
        rows=read(root/'NATURAL_COST.json');schedule=read(root/'NATURAL_SCHEDULE.json')
        assert len(rows)==len(schedule)==288
        for i,(r,b) in enumerate(zip(rows,schedule)):
            assert all(r[k]==v for k,v in b.items())
            name=f'paired-{i:03d}'
            if (root/'units'/(name+'-retry')).exists():name+='-retry'
            raw=records(name)
            assert (raw[1]['seconds'] if len(raw)==2 else None)==r['seconds']
            if len(raw)==2:assert [v['slot']['stage'] for v in raw]==['warmup','measure']
    if (root/'NATURAL_QUAL.json').exists():
        for r in read(root/'NATURAL_QUAL.json'):
            orig=records(f'blind-{r["i"]}-R-*')
            cand=records(f'blind-{r["i"]}-{r["arm"]}-*')
            assert (orig[0]['vectors'] if orig else None)==r['reference_vectors']
            assert (cand[0]['vectors'] if cand else None)==r['candidate_vectors']
            if cand:assert cand[0]['greedy']==r['actual_ids']
    if (root/'FAST_COST.json').exists():
        for r in read(root/'FAST_COST.json'):
            raw=records(r['unit'])
            assert (raw[1]['seconds'] if len(raw)==2 else None)==r['seconds']
    for d in (root/'units').glob('seed-*'):
        for r in records(d.name):
            for s in r.get('states',[]):
                with (d/'native'/f'state-{s["head"]}.bin').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==s['sha256']
                states+=1
    supervised=[(p,read(p)) for p in sorted((root/'units').rglob('SUPERVISOR.json'))]
    assert all(s.get('job_accounting',{}).get('active_processes')==0 for _,s in supervised)
    return dict(observed_or_missing_cells_reconstructed=cells,raw_fixed_costs_reconstructed=timings,checkpoint_objects_verified=states,
                all_native_processes=len(supervised),all_native_seconds=math.fsum(s['charged_seconds'] for _,s in supervised),
                legacy_supervised_jobs=[p.parent.relative_to(root).as_posix() for p,_ in supervised if not (p.parent/'RECEIPT.json').exists()])
