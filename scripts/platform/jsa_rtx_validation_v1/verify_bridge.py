"""Offline exact checks from raw outputs; no runner comparisons imported."""
import json,hashlib,os
from pathlib import Path
REPO=Path(__file__).resolve().parents[3];PUB=REPO/'benchmarks/jsa_rtx_validation_v1';LOCAL=Path(os.environ.get('JSA_LOCAL_ROOT',str(REPO.parent/'jsa')))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    refs={r['id']:r for r in read(LOCAL/'OFFLINE_BRIDGE_REFERENCES.json')};tasks={r['id']:r for r in read(PUB/'BRIDGE_INPUTS.json')};root=LOCAL/'runs/S_bridge';checks=[]
    for p in sorted(root.glob('capture-*/*.json')):
        a=read(p)
        if 'response' not in a or 'task' not in a:continue
        r=a['response'];t=tasks[a['task']];ref=refs[a['task']];ids=r['tokens'];endpoint='EOS' if r['stop_type']=='eos' else 'limit'
        checks.append({'slot':a['slot'],'equal':ids==ref['original_reference_ids'] and endpoint==ref['original_endpoint'],'cache_zero':r['timings']['cache_n']==0,'prompt_equal':r['prompt']==t['formatted_prompt'],'not_truncated':not r['truncated'],'length_correct':len(ids)==r['tokens_predicted'] and (len(ids)==t['cap'] or endpoint=='EOS')})
    trace_checks=[]
    for p in sorted(root.glob('capture-1-*/trace.jsonl')):
        rows=[json.loads(s) for s in p.read_text().splitlines()];dec=[r for r in rows if r.get('event')=='decode'];mask=read(p.parent/'COMMAND.json')['condition']['mask'];checks_phase=[]
        for r in dec:
            bit={'target':1,'draft':4}[r['role']]*(1 if r['phase']=='prefill' else 2)
            checks_phase.append(r['scope_active']==bool(mask&bit) and r['scope_mask']==mask)
        resets=[r for r in dec if r['role']=='target' and r['phase']=='prefill' and r['positions'][0]==0]
        trace_checks.append({'block':p.parent.name,'scope_phase_all_equal':all(checks_phase),'target_prefill_resets':len(resets),'resets_at_least_warm_plus_four':len(resets)>=5,'decode_events':len(dec)})
    passed=len(checks)==32 and all(all(v for k,v in r.items() if k!='slot') for r in checks) and len(trace_checks)==4 and all(r['scope_phase_all_equal'] and r['resets_at_least_warm_plus_four'] for r in trace_checks)
    result={'status':'PASS' if passed else 'ORIGINAL_CONFIGURATION_NOT_REPRODUCED','requests':len(checks),'warmups':8,'checks':checks,'trace_checks':trace_checks,'arrays_source':str(root),'references_offline_only':True}
    (PUB/'S_BRIDGE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'requests':len(checks),'trace_checks':trace_checks}),flush=True)
    if not passed:raise SystemExit(1)
if __name__=='__main__':main()
