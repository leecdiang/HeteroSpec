"""Independent requested-row coverage, including rows rejected before sampling."""
import argparse
import hashlib
import json
from pathlib import Path

def check(worker):
    decodes=[json.loads(line) for line in (worker/'trace.jsonl').read_bytes().splitlines()]
    decodes=[v for v in decodes if v.get('event')=='decode']
    events=[json.loads(line) for line in (worker/'capture/observer.jsonl').read_bytes().splitlines()]
    expected={(n+1,i) for n,v in enumerate(decodes) for i,wanted in enumerate(v['logits_mask']) if wanted and v['returncode']==0}
    actual=[(v['decode_id'],v['row']) for v in events if v['event']=='decision_vector']
    if len(actual)!=len(set(actual)) or expected!=set(actual):raise ValueError('Missing, duplicate or foreign requested logit rows')
    return {'status':'PASS_ALL_REQUESTED_ROWS_RETAINED','requested_rows':len(expected),'captured_rows':len(actual),'sampled_only_filter':False}

def main(config,out,stage):
    cfg=json.loads(config.read_bytes());root=Path(cfg['run_root']);summary=json.loads((root/'E1_SUMMARY.json').read_bytes()) if stage=='E1' else {}
    rows=[]
    for worker in sorted((root/'runs'/stage).glob('*/*')):
        if not (worker/'capture/observer.jsonl').exists():continue
        try:rows.append({'worker':str(worker.relative_to(root)),'family':worker.parent.name,**check(worker)})
        except Exception as error:rows.append({'worker':str(worker.relative_to(root)),'family':worker.parent.name,'status':'FAILURE','error':repr(error)})
    eligible=[f for f,v in summary.items() if v['status']=='QUALIFIED']
    qualified_family_gate=all(all(r['status']=='PASS_ALL_REQUESTED_ROWS_RETAINED' for r in rows if r['family']==family and (not r['worker'].endswith('_NATIVE_FAST') or summary[family]['fast_qualified'])) for family in eligible)
    if stage=='E1':
        for family in eligible:
            arms=['R','PQ','QB']+(['NATIVE_FAST'] if summary[family]['fast_qualified'] else [])
            expected={str(Path('runs')/'E1'/family/f'{i:02d}_{arm}') for i in range(12) for arm in arms}
            observed={r['worker'] for r in rows if r['family']==family and (not r['worker'].endswith('_NATIVE_FAST') or summary[family]['fast_qualified'])}
            qualified_family_gate &= expected==observed
    if stage=='calibration':qualified_family_gate=len(rows)==24 and all(r['status']=='PASS_ALL_REQUESTED_ROWS_RETAINED' for r in rows)
    result={'status':'PASS' if qualified_family_gate else 'BLOCK_E2','stage':stage,'rows':rows,'qualified_families':eligible,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'mandatory_before_E2':True,'model_requests':0,'criterion':'Every successfully decoded row whose native logits_mask is true must have exactly one full captured decision vector, including rejected verification rows'}
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(result['status'],len(rows),'workers; complete requested-row ownership')
    if not qualified_family_gate:raise SystemExit(2)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--stage',choices=['calibration','E1'],required=True);a=p.parse_args();main(a.config,a.out,a.stage)
