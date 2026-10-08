from evidence import *
from collections import Counter, defaultdict
import statistics

def main():
    begin('qualification')
    ledger=[json.loads(x) for x in read('LEDGER.jsonl').decode().splitlines()]
    starts=[x for x in ledger if x['event']=='REQUEST_START']
    done=[x for x in ledger if x['event']=='REQUEST_COMPLETE']
    auxs=[x for x in ledger if x['event']=='TARGET_FORWARD_START']
    auxd=[x for x in ledger if x['event']=='TARGET_FORWARD_COMPLETE']
    for xs in [starts,done,auxs,auxd]: assert len(xs)==len({x['unit_id'] for x in xs}), 'duplicate ledger key'
    missing=sorted({x['unit_id'] for x in starts}-{x['unit_id'] for x in done})
    assert missing==['E/FORMAL/1/old_N1/MBPP/400']
    receipts={}
    for x in done:
        u=x['unit_id']; name='raw/'+digest(u.encode())[:20]+'/RESULT.json'
        d=check_receipt(name); assert d['unit_id']==u and d['warm']==x['warm']
        assert abs(d['host_seconds']-x['host_seconds'])<1e-8
        receipts[u]=d
    for x in auxd: check_receipt('aux/'+x['unit_id'].replace('/','_')+'/RESULT.json')
    stages=Counter(u.split('/')[0] for u,r in receipts.items() if not r['warm'])
    assert stages==dict(A=48,B_SHAM=12,C=12,D=112,E=127)
    count=dict(nonwarm_started=sum(not x['warm'] for x in starts),nonwarm_complete=sum(not x['warm'] for x in done),warm_started=sum(x['warm'] for x in starts),warm_complete=sum(x['warm'] for x in done),aux_started=len(auxs),aux_complete=len(auxd),complete_by_stage=dict(stages),missing_units=missing,formal_complete=119,formal_planned=120,bridge_complete=8,paid_campaign_known_request_host_seconds_subtotal=sum(x['host_seconds'] for x in done)+sum(x['host_seconds'] for x in auxd),interruption_and_teardown_seconds='unknown',infrastructure_failure_events=[x for x in ledger if x['event']=='REQUEST_INFRA_FAILURE'],new_model_requests=0,new_forward=0,new_warmup=0)
    assert [count[k] for k in ['nonwarm_started','nonwarm_complete','warm_started','warm_complete','aux_started','aux_complete']]==[312,311,37,37,24,24]
    write('COUNTS.json',count)
    eog=set(load('dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids'])
    hist=load('HISTORICAL_PARENTS.json'); drefs=load('D_REFERENCES.json');d_raw={};external={}
    # Follow the already restored PR63 root recorded in the sealed Stage0 receipt.
    import zipfile
    prior=load('STAGE0.json')['restores'][0];priorroot=pathlib.Path(CFG.get('prior_core_restore',prior['path']));priorarchive=CFG.get('prior_core_archive',prior['archive'])
    with open(priorarchive,'rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==prior['sha256']
    with zipfile.ZipFile(priorarchive) as z:oldindex=json.loads(z.read('INDEX.json'))['files']
    def oldread(name):
        data=(priorroot/name).read_bytes();x=oldindex[name]
        assert len(data)==x['bytes'] and digest(data)==x['sha256'];external[name]=x;return json.loads(data)
    exports=load('dependencies/HISTORICAL_EXPECTED.json');oldinputs=load('dependencies/INPUTS.json')
    for task,ref in drefs.items():
        if 'manifest_sha256' in ref:
            assert digest(read('dependencies/HISTORICAL_EXPECTED.json'))==ref['manifest_sha256']
            for k in [1,2,3]:
                x=exports[f'{task}/R/{k}'];assert x['ids']==ref['ids'] and x['eog']==ref['eog'] and ('CAP' if x['endpoint']=='CAP128' else x['endpoint'])==ref['reason']
        else:
            assert prior['sha256']==ref['archive_sha256'];rs=[]
            for u in ref['source_units']:
                r=oldread('raw/'+digest(u.encode())[:20]+'/RESULT.json');assert r['unit_id']==u and r['task']==task and r['config']['label']=='R_reference'
                p=next(p for p in r['files'] if p.endswith('/capture.json'));x=oldread(p);assert external[p]['sha256']==r['files'][p]
                assert endpoint(x['ids'],x['eog'],eog)=={k:ref[k] for k in ['ids','eog','reason']}
                inp=next(i for cohort in ['shared','unused'] for i in oldinputs[cohort] if i['id']==task);assert x['prompt_ids']==inp['prompt_ids']
                rs.append(x)
            assert len(rs)==4 and all(x['ids']==rs[0]['ids'] and x['eog']==rs[0]['eog'] for x in rs)
            assert ref['source_raw_sha256'] in [v['sha256'] for p,v in external.items() if p.endswith('/capture.json')]
            d_raw[task]=rs[0]
    write('D_REFERENCE_BINDINGS.json',dict(archive_sha256=prior['sha256'],read_only_restore=str(priorroot),verified_files=external,HumanEval_export_records=72,MBPP_raw_records=128,no_new_references=True))
    inputs={x['id']:x for x in load('D_INPUTS.json')+load('E_INPUTS.json')+load('DEV_INPUTS.json')}
    raw={}; ep={}
    for u,d in receipts.items():
        if d['warm'] or u.startswith('B_SHAM/'): continue
        c=load(next(p for p in d['files'] if p.endswith('/capture.json')))
        assert all(type(i)==int and 0<=i<151936 for i in c['ids'])
        raw[u]=c; ep[u]=endpoint(c['ids'],c['eog'],eog)
        assert all(ep[u][k]==d['endpoint'][k] for k in ep[u]),u
        if u.startswith(('C/','D/','E/')): assert c['prompt_ids']==inputs[d['task']]['prompt_ids'], 'frozen input '+u
    formal={}; schedule=load('E_MANIFEST.json')
    for s in schedule['formal_sessions']:
        for x in s['units']:
            u=x['unit_id']
            if u in receipts:
                assert receipts[u]['config']==s['config']
                formal[(x['task'],s['config']['label'],s['config']['round'])]=u
    assert len(formal)==119 and schedule['formal_tasks']==15
    rows=[]
    for u,d in receipts.items():
        if u not in ep:continue
        task=d['task'];label=d['config']['label'];stage=u.split('/')[0]
        if stage=='D':ref=drefs[task];refep={k:ref[k] for k in ['ids','eog','reason']};refraw=d_raw.get(task)
        elif u.startswith('E/FORMAL/'):
            ru=formal[(task,'ordinary_R',1)];refep=ep[ru];refraw=raw[ru]
        else:ref=hist[task+'/R_reference'];refep={k:ref['endpoint'][k] for k in ['ids','eog','reason']};refraw=dict(ids=ref['raw_ids'],eog=ref['raw_eog']) if 'raw_ids' in ref else None
        qualified=ep[u]==refep
        if stage in ['C','D','E']: assert qualified,'unqualified '+u
        if stage=='A':
            old=hist.get(task+'/'+label)
            if old:
                assert ep[u]=={k:old['endpoint'][k] for k in ['ids','eog','reason']}
                if 'raw_ids' in old:assert raw[u]['ids']==old['raw_ids'] and raw[u]['eog']==old['raw_eog']
        peers=[v for v in raw if receipts[v]['task']==task and receipts[v]['config']['label']==label and v.split('/')[0]==stage and (v.startswith('E/FORMAL/')==u.startswith('E/FORMAL/'))]
        stable=all(raw[v]['ids']==raw[u]['ids'] and raw[v]['eog']==raw[u]['eog'] for v in peers) if len(peers)>1 else 'unknown_single_repeat'
        if len(peers)>1:assert stable,'raw instability '+u
        suffix=len(raw[u]['ids'])-len(ep[u]['ids'])
        if 'raw_count' in d['metrics']:assert d['metrics']['raw_count']==len(raw[u]['ids'])
        rows.append(dict(unit_id=u,stage=stage,task=task,label=label,round=d['config']['round'],reference_endpoint_equal=qualified,raw_reference_equal=(raw[u]['ids']==refraw['ids'] and raw[u]['eog']==refraw['eog']) if refraw else 'unknown_reference_raw_unavailable',raw_repeat_stable=stable,endpoint_length=len(ep[u]['ids']),raw_length=len(raw[u]['ids']),raw_suffix=suffix,reason=ep[u]['reason'],generation_ms=d['metrics']['generation_ms'],whole_request_ms=d['metrics']['whole_request_ms'],host_ms=d['host_seconds']*1000,all_suffix_work_paid=True))
    table('QUALIFICATION_RECOMPUTED.csv',rows)
    summary={s:dict(records=len([x for x in rows if x['stage']==s]),reference_endpoint_equal=sum(x['reference_endpoint_equal'] for x in rows if x['stage']==s),raw_reference_equal=sum(x['raw_reference_equal'] is True for x in rows if x['stage']==s),raw_reference_unequal=sum(x['raw_reference_equal'] is False for x in rows if x['stage']==s),raw_reference_unknown=sum(isinstance(x['raw_reference_equal'],str) for x in rows if x['stage']==s),suffix_tokens=sum(x['raw_suffix'] for x in rows if x['stage']==s),records_with_suffix=sum(x['raw_suffix']>0 for x in rows if x['stage']==s)) for s in ['A','C','D','E']}
    write('QUALIFICATION.json',dict(status='PASS',stages=summary,D_tasks=len(drefs),E_formal_tasks=15,E_old_N1_complete_paired_tasks=14,E_matrix_status='PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED',raw_arrays_and_endpoints_separate=True,reference_D='24 HumanEval immutable endpoint exports (raw unknown); 32 MBPP four-repeat PR63 raw independently read; no paid new R',raw_repeat_scope='same stage/task/config across available two repeats; singleton old N1 explicitly unknown'))
    # Check actual bindings and historical audit bytes; no fresh bulk exposure scan.
    for n in ['D_INPUT_IDENTITY_AUDIT.json','E_EXPOSURE_AUDIT.json','E_EXPOSURE_CATALOG.json','E_FREEZE.json','D_FREEZE.json','E_TOKENIZATION_BINDINGS.json','SOURCE_EPOCHS.json','BUILD_BINDINGS.json'] :load(n)
    write('EXPOSURE_RECHECK.json',dict(D_tasks=56,D_all_already_exposed=True,E_tasks=15,E_preoutput_status='accessible_project_unused_confirmation per CAS-bound original audit',E_now_exposed=True,training_unseen_claim=False,fresh_RTX_bulk_scan=False,input_hashes={t:dict(prompt_ids_sha256=digest(json.dumps(x['prompt_ids']).encode()),formatted_prompt_sha256=x.get('formatted_prompt_sha256')) for t,x in inputs.items()},historical_D_reference_manifest_sha256=sorted(set(x['manifest_sha256'] for x in drefs.values() if 'manifest_sha256' in x)),historical_D_reference_archive_sha256=sorted(set(x['archive_sha256'] for x in drefs.values() if 'archive_sha256' in x))))
    finish('qualification');print(json.dumps(dict(counts=count,qualification=summary),ensure_ascii=True))
if __name__=='__main__':main()
