"""Read-only costs. Null means unmeasured; phase subtotals never become speedups."""
from pathlib import Path
import argparse, hashlib, json, math

TARGET=('target_prefill','target_ordinary','target_verify')
DRAFT=('draft_prefill','draft_sync','draft_proposal','draft_continuation_unsplit')

def finite(value, name):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError('Invalid nonnegative time: '+name)
    return float(value)

def decompose(service_s, sidecar):
    service=finite(service_s,'service')
    if sidecar is None:
        return {'service_s':service,'target_s':None,'draft_s':None,'other_s':None,
                'exclusive_accounted_s':None,'not_instrumented_s':None,'mode':0}
    if sidecar.get('schema')!='b570-cost-v1' or sidecar.get('valid') is not True or sidecar.get('mode') not in (1,2):
        raise ValueError('Unknown/incomplete timing sidecar')
    phases=sidecar['phases']
    # Sum self times only: transition is the parent of export/import/check spans.
    for name,row in phases.items():
        inclusive=finite(row['inclusive_s'],name);exclusive=finite(row['exclusive_s'],name)
        if exclusive>inclusive+1e-9:raise ValueError('Exclusive exceeds inclusive')
        if type(row['calls'])!=int or row['calls']<0:raise ValueError('Invalid call count')
    for name in TARGET+DRAFT:
        if name not in phases:raise ValueError('Missing phase: '+name)
    accounted=sum(x['exclusive_s'] for x in phases.values())
    if accounted>service+1e-6:raise ValueError('Diagnostic spans outside service or double counting')
    target=sum(phases[n]['exclusive_s'] for n in TARGET)
    draft=sum(phases[n]['exclusive_s'] for n in DRAFT)
    return {'service_s':service,'target_s':target,'draft_s':draft,
        'other_s':service-target-draft,'exclusive_accounted_s':accounted,
        'not_instrumented_s':max(0.,service-accounted),'mode':sidecar['mode'],
        'phase_exclusive_s':{k:v['exclusive_s'] for k,v in phases.items()},
        'draft_sync_proposal_separately_measured':phases['draft_continuation_unsplit']['calls']==0,
        'phase_inclusive_s':{k:v['inclusive_s'] for k,v in phases.items()},
        'interpretation':'mode1 host envelopes; mode2 synchronized diagnostic, neither replaces clean service'}

def economic_identity(m,d):
    if m['mode']!=d['mode']:raise ValueError('Different timing modes')
    if any(x[k] is None for x in (m,d) for k in ('target_s','draft_s','other_s')):
        return {'full_service_saving_s':m['service_s']-d['service_s'],
                'target_saved_s':None,'draft_added_s':None,'other_added_s':None}
    target_saved=m['target_s']-d['target_s']
    draft_added=d['draft_s']-m['draft_s'];other_added=d['other_s']-m['other_s']
    net=target_saved-draft_added-other_added
    if not math.isclose(net,m['service_s']-d['service_s'],abs_tol=1e-8):raise ValueError('Cost partition mismatch')
    return {'full_service_saving_s':net,'target_saved_s':target_saved,
            'draft_added_s':draft_added,'other_added_s':other_added,
            'causal_effect':False,'scope':'descriptive matched-request identity; trajectories may differ'}

def scan_saved(campaign, panel):
    """Exact PR187 naming from smol_timing.py; no discovery by output/performance."""
    campaign=Path(campaign);panel=json.loads(Path(panel).read_text())
    records=json.loads((campaign/'RECORDS.json').read_text())['records']
    indices={r['id']:i for i,r in enumerate(panel['test'])}
    if len(indices)!=len(panel['test']):raise ValueError('Duplicate input IDs')
    root_by_id={r['id']:r['root_id'] for r in panel['test']}
    arms=('M','H1','C1U1','C4U1','C4U2','C4U4')
    expected={(s,r['root_id'],a,k) for s in range(6) for r in panel['test'] for a in arms for k in ('warmup','measure')}
    seen=set();out=[]
    for r in records:
        key=(r['session'],r['root_id'],r['arm'],r['kind'])
        if key in seen:raise ValueError('Duplicate slot')
        seen.add(key)
        if root_by_id[r['input_id']]!=r['root_id']:raise ValueError('Root/input identity mismatch')
        if r['status']!='COMPLETE' or not r['endpoint_equal']:raise ValueError('Incomplete/unqualified original slot')
        i=indices[r['input_id']];j={'warmup':0,'measure':1}[r['kind']]
        folder=campaign/'runs'/f"main-s{r['session']}-r{i}-{r['arm']}"
        p=folder/f'{j}.json.metrics.json';data=p.read_bytes()
        if hashlib.sha256(data).hexdigest()!=r['metrics_sha256']:raise ValueError('Original metric SHA mismatch')
        metrics=json.loads(data);service=finite(metrics['service_ms'],'service_ms')/1000
        if not math.isclose(service,r['service_s'],abs_tol=1e-9):raise ValueError('Service mismatch')
        # Old generation includes transfer; never rename it decode time.
        components={k:(finite(metrics[k],k)/1000 if k in metrics else None)
                    for k in ('generation_ms','prefill_ms','whole_request_ms')}
        trace=folder/f'{j}.json.cost.json'
        row={k:r[k] for k in ('slot','root_id','input_id','session','arm','kind')}
        row.update(decompose(service,json.loads(trace.read_text()) if trace.exists() else None))
        row['legacy_windows_s']=components;out.append(row)
    if seen!=expected:raise ValueError('Incomplete original six-arm/six-session panel')
    groups={}
    for r in out:
        if r['kind']=='measure':groups.setdefault(r['arm'],[]).append(r)
    summary={a:{'requests':len(rs),'service_s':sum(x['service_s'] for x in rs),
        'legacy_generation_s':sum(x['legacy_windows_s']['generation_ms'] for x in rs)
             if all(x['legacy_windows_s']['generation_ms'] is not None for x in rs) else None,
        'detailed_phase_available':all(x['mode']>0 for x in rs)} for a,rs in groups.items()}
    return {'status':'SAVED_METADATA_RECOMPUTED','model_forwards':0,'slots':len(out),
        'summary':summary,'records':out,'legacy_generation_is_pure_decode':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign',type=Path,required=True);p.add_argument('--panel',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=scan_saved(a.campaign,a.panel)
    with a.out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
