"""Independent reconstruction from every raw timing record; no production audit imports."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def geo(values):
    values=list(values)
    return math.exp(math.fsum(math.log(x) for x in values)/len(values))


def endpoint(r):return tuple(json.dumps(r[k],sort_keys=True) for k in ('ids','eog','length','terminal_id','stop_reason'))


def transaction(r):
    ids=r['ids'];assert len(ids)==r['length'] and ids[-1]==r['terminal_id']
    assert len(ids)<=128 and len(r['eog'])==len(ids)
    assert not any(r['eog'][:-1])
    assert r['stop_reason']==('EOG' if r['eog'][-1] else 'CAP')
    assert r['eog'][-1] or len(ids)==128
    if not r['draft_enabled']:
        assert not r['cycles']
        assert r['target_final_kv']['max']==r['prompt_tokens']+len(ids)-2
        return
    output=[ids[0]];base=r['prompt_tokens'];ended=r['eog'][0]
    eos=set(r['vocabulary_eog'])
    for number,c in enumerate(r['cycles']):
        assert not ended and (c['cycle'],c['base'],c['seed'])==(number,base,output[-1])
        count=0;rejected=False;kind=None
        for j,proposal in enumerate(c['proposals']):
            rejected=proposal!=c['decisions'][j]
            output.append(c['decisions'][j]);kind='correction' if rejected else 'accepted'
            count+=not rejected;ended=output[-1] in eos or len(output)==128
            if ended or rejected:break
        if not ended and not rejected:
            output.append(c['decisions'][-1]);kind='bonus';ended=output[-1] in eos or len(output)==128
        base+=1+count
        assert (count,rejected,kind,len(output),ended,base)==(c['accepted'],c['rejected'],c['commit_kind'],c['output_length'],c['done'],c['keep'])
        assert c['pending_after']==(None if ended else output[-1])
        assert c['target_after']['max']==c['draft_after']['max']==base-1
    assert output==ids and ended
    assert r['target_final_kv']['max']==r['draft_final_kv']['max']==base-1


def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();b=a.bundle;panel=read(b/'HELDOUT.json')['inputs'];n=len(panel)
    labels=('R','M_PQ','M_QB','C_PQ_A','C_PQ_B','C_QB');values={};records={};refs={};loaded=[]
    components={category:{k:[] for k in ('setup_seconds','request_seconds','teardown_seconds','service_seconds')} for category in ('warmup','measured')}
    original=b/'units/original_references'
    for s in read(original/'SLOTS.json'):
        r=read(original/'native'/(s['slot_id']+'.json'))
        e=endpoint(r)
        if s['input_id'] in refs:assert refs[s['input_id']]==e
        refs[s['input_id']]=e
    for session in range(6):
        unit=b/'units'/('formal%d'%session);receipt=read(unit/'RECEIPT.json')
        assert receipt['success'] and receipt['active_processes_after_wait']==0
        provision=read(unit/'native/PROVISIONED.json')
        loaded.append({'session':session,'model_load_seconds':provision['model_load_seconds'],
          'resident_provisioning_seconds':provision['resident_provisioning_seconds'],
          'supervised_wall_seconds':receipt['seconds'],'provision_sha256':sha(unit/'native/PROVISIONED.json')})
        slots=read(unit/'SLOTS.json');assert len(slots)==12*n
        for s in slots:
            path=unit/'native'/(s['slot_id']+'.json');r=read(path);transaction(r)
            assert r['slot']==s and endpoint(r)==refs[s['input_id']]
            assert r['prompt_ids']==panel[s['source_index']]['prompt_ids']
            assert r['context_teardown_completed'] and s['lifecycle']=='fresh'
            assert not r['capture'] and not r['teacher_forced'] and r['observer_mode']=='off'
            assert r['llama_diagnostic']['mode']=='off' and s['repair']['trace']['mode']=='off'
            elapsed=r['service_seconds'];assert type(elapsed) in (float,int) and math.isfinite(elapsed) and elapsed>0
            assert elapsed+1e-6>=r['setup_seconds']+r['request_seconds']+r['teardown_seconds']
            key=(session,s['source_index'],s['experiment_arm'],s['category'])
            assert key not in values;values[key]=elapsed;records[str(path)]=sha(path)
            for name in components[s['category']]:components[s['category']][name].append(r[name])
    expected={(s,i,l,c) for s in range(6) for i in range(n) for l in labels for c in ('warmup','measured')}
    assert set(values)==expected
    blocks=[]
    for s in range(6):
        for i in range(n):
            t={l:values[s,i,l,'measured'] for l in labels};pq=(t['C_PQ_A']+t['C_PQ_B'])/2
            blocks.append(dict(session=s,input=i,layout=t['C_QB']/pq,AA=t['C_PQ_A']/t['C_PQ_B'],
              D_QB=t['M_QB']/t['C_QB'],D_PQ=t['M_PQ']/pq,CQB_R=t['C_QB']/t['R'],
              MQB_R=t['M_QB']/t['R'],MPQ_R=t['M_PQ']/t['R'],CPQ_R=pq/t['R']))
    means={k:geo(x[k] for x in blocks) for k in blocks[0] if k not in ('session','input')}
    aa=[geo(x['AA'] for x in blocks if x['input']==i) for i in range(n)]
    noise=max(max(x,1/x)-1 for x in aa)
    periods=[geo(x['layout'] for x in blocks if x['session']==s) for s in range(6)]
    gain=1-means['layout']>max(.02,noise) and all(x<1 for x in periods)
    produced=read(b/'FINAL_COST.json')
    for k,v in means.items():assert math.isclose(v,produced['means'][k],rel_tol=1e-12)
    assert math.isclose(noise,produced['AA_max_symmetric_input'],abs_tol=1e-12)
    assert all(math.isclose(x,y,rel_tol=1e-12) for x,y in zip(periods,produced['sessions']))
    assert gain==produced['practical_layout_gain']
    result={'status':'INDEPENDENT_COST_RECONSTRUCTED','records':len(values),'measured':len(values)//2,
      'warmups':len(values)//2,'means':means,'AA_max_symmetric_input':noise,'sessions':periods,
      'practical_layout_gain':gain,'all_raw_endpoints_and_transactions_valid':True,
      'scope':'Six loaded sessions, all input blocks retained; no population claim.',
      'script_sha256':sha(Path(__file__)),'produced_report_sha256':sha(b/'FINAL_COST.json'),
      'record_sha256':records,'all_service_seconds':math.fsum(values.values())}
    result['loaded_session_costs']=loaded
    result['service_components_seconds']={category:{k:math.fsum(v) for k,v in fields.items()} for category,fields in components.items()}
    result['reported_model_load_seconds']=math.fsum(x['model_load_seconds'] for x in loaded)
    result['cost_scope']='Service includes fresh context setup, request/prefill/decode/reconciliation/synchronization and teardown. Weight load is reported separately. Supervised wall time additionally contains host auditing, protocol waits and output I/O.'
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print({k:v for k,v in result.items() if k!='record_sha256'})


if __name__=='__main__':main()
