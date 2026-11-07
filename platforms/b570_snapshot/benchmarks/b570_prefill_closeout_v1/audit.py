"""Independent CPU audit of raw files, endpoints, physical-q evidence and costs."""
import argparse, hashlib, math, sys
from pathlib import Path
from prepare import ROOT, PR134, read, write, item

KEYS=['ids','eog','length','terminal_id','stop_reason']
def equal(a,b,trace):
    for key in KEYS+(['cycles'] if trace else []):assert a[key]==b[key],key

def receipt(mode,i):
    r=read(ROOT/f'{mode}-{i}.PROCESS_RECEIPT.json')
    assert r['status']=='PROCESS_COMPLETED' and r['exit_observed'] and r['exit_code']==0
    assert r['normal_cleanup_returned'] and r['job_kill_on_close'] and r['capture_complete']
    n=read(ROOT/f'{mode}-{i}/result.json')
    assert n['status']==mode+'_PASS' and n['normal_cleanup_returned']
    return n,r

def qualification(mode):
    panel=read(ROOT/'INPUT_PANEL.json');rows=[];raw=[]
    for i in range(1 if mode=='E0' else 4):
        n,rc=receipt(mode,i);actual=n['requests'];labels=['BASE','SUBMIT'] if mode=='E0' else ['R','BASE','SUBMIT']
        assert len(actual)==len(labels)*2
        refbase=Path('C:/hs/b570-spec-bridge-20261020200000/results') if mode=='E0' else PR134/f'qual-{i}'
        reference=read(refbase/'result.json');captures={}
        for j,label in enumerate(labels):
            cap,count=actual[2*j:2*j+2];assert cap['label']==count['label']==label
            assert cap['capture'] is True and cap['observers_installed'] is True
            assert count['capture'] is False and count['observers_installed'] is False
            equal(reference['requests'][0 if label=='R' else 2],cap,label!='R');equal(cap,count,label!='R')
            oldraw=refbase/('QB' if mode=='E0' else ('qual-0' if label=='R' else 'qual-2'))
            newraw=ROOT/f'{mode}-{i}'/cap['raw_dir']
            aa={str(p.relative_to(oldraw)):p for p in oldraw.rglob('*.f32')}
            bb={str(p.relative_to(newraw)):p for p in newraw.rglob('*.f32')}
            assert set(aa)==set(bb) and len(aa)>0
            for k in aa:
                assert aa[k].read_bytes()==bb[k].read_bytes(),(mode,i,label,k)
                raw.append(dict(item(bb[k]),historical_reference=item(aa[k])))
            if label!='R':
                e=read(newraw/'prefill-events.json');q=e['qk'];prompt=panel['warmup'] if mode=='E0' else panel['inputs'][i]
                assert e['prompt_ids']==prompt['prompt_ids'] and e['last_token_logits_only']
                assert e['draft_kv_max']==e['target_kv_max']==len(prompt['prompt_ids'])-1
                assert len(q)==len(prompt['prompt_ids'])*28 and all(x['ne'][1]==1 for x in q)
                assert cap['draft_prefill_api_calls']==(1 if label=='SUBMIT' else len(prompt['prompt_ids']))
                assert cap['draft_microbatch_limit']==1
                for token in range(len(prompt['prompt_ids'])):
                    assert len({x['name'] for x in q[token*28:(token+1)*28]})==28
                captures[label]=e
            rows.append({'mode':mode,'input':cap['input_id'],'label':label,'full_vectors':len(aa),
                         'capture_count_equal':True,'endpoint':[cap['length'],cap['stop_reason']]})
        assert captures['BASE']==captures['SUBMIT'], 'Ordered physical q/key/mask metadata mismatch'
    name='E0_AUDIT.json' if mode=='E0' else 'QUALIFICATION_AUDIT.json'
    write(name,{'status':mode+'_FULL_PASS','rows':rows,'raw_vectors_rechecked':len(raw),
                'scope':'Fresh native endpoint/cycle, observer control, full historical byte and ordered q/key/mask metadata audit. No timed observer.'})
    write(mode+'_RAW_MANIFEST.json',raw)
    print(mode+'_FULL_PASS',len(raw),'vectors')

def geo(x):return math.exp(math.fsum(math.log(v) for v in x)/len(x))

def timing():
    order=read(ROOT/'ORDER.json');records=[];all_requests=[];previous=None
    for i in range(4):
        n,rc=receipt('E2',i)
        if previous:assert rc['started_utc']>previous
        previous=rc['exit_observed_utc']
        expected=[x for x in order if x['session']==i];assert len(expected)==len(n['requests'])==32
        for e,x in zip(expected,n['requests']):
            assert x['slot']==e['slot'] and x['category']==e['category'] and x['label']==e['arm']
            assert not x['capture'] and not x['observers_installed'] and not x['actual_signatures']
            assert math.isfinite(x['service_seconds']) and x['service_seconds']>=x['request_seconds']>0
            ref=read(PR134/f"qual-{e['input_index']}/result.json")['requests'][0 if e['arm']=='R' else 2]
            equal(ref,x,e['arm']!='R')
            records.append(dict(e,seconds=x['service_seconds'],qualified=True,exit_ok=True,
                                request_seconds=x['request_seconds']))
            all_requests.append(dict(x,session=i,input_index=e['input_index']))
    measured=[x for x in records if x['category']=='measured'];assert len(measured)==64
    blocks=[]
    for s in range(4):
        for i in range(4):
            cells={x['arm']:x['seconds'] for x in measured if x['session']==s and x['input_index']==i}
            baseline=(cells['BASE_A']+cells['BASE_B'])/2
            blocks.append({'session':s,'input_index':i,'candidate_over_dual_control':cells['SUBMIT']/baseline,
                           'candidate_over_R':cells['SUBMIT']/cells['R'],'dual_control_over_R':baseline/cells['R'],
                           'aa':cells['BASE_A']/cells['BASE_B']})
    primary=geo([x['candidate_over_dual_control'] for x in blocks]);aa=max(abs(geo([x['aa'] for x in blocks if x['input_index']==i])-1) for i in range(4))
    sessions=[geo([x['candidate_over_dual_control'] for x in blocks if x['session']==s]) for s in range(4)]
    own={'candidate_over_dual_control':primary,'candidate_over_R':geo([x['candidate_over_R'] for x in blocks]),
         'dual_control_over_R':geo([x['dual_control_over_R'] for x in blocks]),'aa_max_input':aa,
         'session_ratios':sessions,'practical_screen_pass':1-primary>max(.02,aa) and all(x<1 for x in sessions)}
    sys.path.insert(0,str(ROOT/'design'));import toolkit
    shared=toolkit.analyze('B570','Qwen3',[{k:v for k,v in x.items() if k!='request_seconds'} for x in records])
    for k in ['candidate_over_dual_control','candidate_over_R','dual_control_over_R','aa_max_input']:
        assert abs(own[k]-shared[k])<1e-12,k
    assert own['practical_screen_pass']==shared['practical_screen_pass']
    write('NORMALIZED_RECORDS.json',records);write('INDEPENDENT_ANALYSIS.json',dict(own,blocks=blocks,
        status='COMPLETE_RAW_TO_NORMALIZED_RECONSTRUCTION',measured=64,warmups=64,toolkit_agreement=True))
    write('TOOLKIT_ANALYSIS.json',shared);write('TIMING_REQUESTS.json',all_requests)
    print(own)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['E0','E1','E2']);a=p.parse_args()
    timing() if a.mode=='E2' else qualification(a.mode)
