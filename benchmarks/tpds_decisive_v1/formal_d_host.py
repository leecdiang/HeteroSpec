"""Frozen full logical sessions, immediate warmups, and independent final states."""
from native_adapter import *
from common import digest
from design import schedule
from active_kv import parse
from qualify_host import QUAL
import hashlib,sys
HERE=Path(__file__).resolve().parent;FREEZE=ROOT/'D-FREEZE.json'
def prepare():
    pins={};qualification=[]
    for ix in range(4):
        suffix='' if ix==0 else '-root'+str(ix)
        for arm in ('M','D1','D2','D4'):
            case=QUAL/(arm+suffix);proof=json.loads((case/'QUALIFICATION.json').read_bytes());assert proof['status']=='FINITE_NATIVE_CAPTURE_MATCH'
            use='D1' if arm=='M' else arm;exe=ROOT/'draft-v3'/use/'bin/worker.exe';native_row=json.loads((case/'candidate-row.json').read_bytes());assert native_row['identity']['executable_sha256']==sha(exe),'qualified executable differs from current executable'
            priming=RUNS/('priming-v3-'+arm+'-root'+str(ix))/'PRIMING_QUALIFICATION.json';assert json.loads(priming.read_bytes())['rows']
            prime_run=json.loads((priming.parent/'session-result.json').read_bytes());assert all(x['executable_sha256']==sha(exe) for x in prime_run['records'])
            forced_launch=json.loads((RUNS/('forced-v2-'+arm+suffix)/'launch.json').read_bytes());assert forced_launch['exe_sha256']==sha(ROOT/'forced-v2/bin/worker.exe'),'qualified independent reference version changed'
            qualification.append(dict(arm=arm,exposed_root=ix,executable_sha256=sha(exe),actual_worker_source_sha256=sha(exe.parent.parent/'worker.cpp'),actual_build_receipt_sha256=sha(exe.parent.parent/'BUILD.json'),inherited_legacy_worker_field=native_row['identity']['worker_source_sha256'],provenance_note='Early development rows retained original source/build metadata while correctly binding the derivative executable. Actual derivative source/build above comes from retained compiler command and binary receipt; no numerical executable changed.',numerical_modules=native_row['identity']['numerical_modules'],full=sha(case/'QUALIFICATION.json'),priming=sha(priming),candidate_capture=sha(case/'candidate/capture.json'),independent_capture=sha(case/'bank/capture.json')))
            pins[str(case/'QUALIFICATION.json')]=sha(case/'QUALIFICATION.json');pins[str(priming)]=sha(priming)
    scripts=('formal_d_host.py','native_adapter.py','bridge_host.py','build_host.py','runner.py','common.py','design.py','active_kv.py','analyze.py','qualify_host.py','normalize.py','trace.py','qualify.py')
    for p in [HERE/name for name in scripts]+[ROOT/'QWEN_PROFILE.json',ROOT/'PROFILE_VALIDATION.json',OLD/'bin/rtx-scope-transfer.exe',OLD/'BUILD.json',ROOT/'forced-v2/BUILD.json',ROOT/'forced-v2/bin/worker.exe',ROOT/'forced-v2/forced_host.cpp']+[OLD.parent/'admission-Qwen-v4'/name for name in ('BINDING.json','SLOTS.json','PLAN.json')]:
        pins[str(p)]=sha(p)
    for arm in ('D1','D2','D4'):
        build=ROOT/'draft-v3'/arm
        for p in [build/'worker.cpp',build/'target_capture.hpp',build/'BUILD.json',build/'bin/worker.exe']:pins[str(p)]=sha(p)
    sel=ROOT/'selection-v3';panel=json.loads((sel/'D-panel.json').read_bytes());sched=schedule(panel,'rtx-draft')
    for p in sel.glob('*.json'):pins[str(p)]=sha(p)
    put(FREEZE,dict(status='FROZEN_BEFORE_TEST_OUTPUTS',lane='rtx-draft',original_reference=sha(OLD/'bin/rtx-scope-transfer.exe'),panel=panel,schedule=sched,inputs=json.loads((sel/'D-inputs.json').read_bytes()),file_pins=pins,qualification=qualification,lifecycle='Each scheduled arm pair loads the original four resident pools outside service; warmup immediately precedes measurement, reset stays inside each complete service. Sequential version workers replay the independently qualified same priming history. Every load and post-service state export is retained separately.',profile=json.loads((ROOT/'QWEN_PROFILE.json').read_bytes()),service_clock='Unchanged PR151 complete request clock; no phase subtraction; final state readback after clock, separately recorded',limits=LIMITS,main_requests=384,reference_plan='12 unchanged autonomous R trajectories then 12 independent scalar forced paths capturing both possible final materialized prefixes; no candidate values sent to reference',no_optional_retuning=True))
def test_job(label,arm,records,input,modes=None):
    job=draft_job(label,arm,('warmup','measure') if modes is None else modes);job['panel']['inputs']=[input]
    for i,slot in enumerate(job['slots']):
        slot.update(source_index=0,input_id=input['id'],prompt_ids_sha256=input['prompt_ids_sha256'])
        if records:slot.update(slot_id=records[i]['slot'],planned=records[i],kind=records[i]['kind'])
    return job
def main():
    f=json.loads(FREEZE.read_bytes());assert f['status']=='FROZEN_BEFORE_TEST_OUTPUTS'
    for name,h in f['file_pins'].items():assert sha(Path(name))==h,('freeze drift',name)
    freeze_sha=sha(FREEZE);proofdir=ROOT/'D-main-reference';proofdir.mkdir();references={};profile=f['profile']
    original_slots=json.loads((OLD.parent/'admission-Qwen-v4/SLOTS.json').read_bytes());original=next(x for x in original_slots if x['arm']=='R' and x['source_index']==0)
    for ix,input in enumerate(f['inputs']):
        job=test_job('D-main-original-'+str(ix),'M',None,input,('r0',));job['exe']=str(OLD/'bin/rtx-scope-transfer.exe');job['binding']['families']['Qwen']['executable_sha256']=sha(Path(job['exe']))
        job['binding']['families']['Qwen'].update(worker_source_sha256=sha(OLD/'worker.cpp'),build_receipt_sha256=sha(OLD/'BUILD.json'))
        job['slots']=[dict(original,slot_id='r0',observer='off',source_index=0,input_id=input['id'],prompt_ids_sha256=input['prompt_ids_sha256'])]
        out=execute(job);r=json.loads((out/'native/r0.json').read_bytes());n=len(r['prompt_ids']);ids=r['ids'];assert ids
        exe=ROOT/'forced-v2/bin/worker.exe';binding=job['binding'];binding['families']['Qwen']['executable_sha256']=sha(exe)
        binding['families']['Qwen'].update(worker_source_sha256=sha(exe.parent.parent/'worker.cpp'),build_receipt_sha256=sha(exe.parent.parent/'BUILD.json'),study_source_files=json.loads((exe.parent.parent/'BUILD.json').read_bytes())['sources'])
        positions=sorted(set([n+len(ids)-1,n+len(ids)]));forced=dict(no_candidate_payload=True,prompt_ids=r['prompt_ids'],producer=dict(caller_lengths=[n],last_output_flags=[True]),paths=[dict(suffix=ids,positions=positions)])
        refout=execute(dict(attempt_id='D-main-forced-'+str(ix),exe=str(exe),binding=binding,forced=forced,reservation=dict(requests=1,token_rows=n+len(ids),operators=0)))
        rr=json.loads((refout/'native/result.json').read_bytes());states={}
        for cap in rr['paths'][0]['captures']:
            p=refout/'native'/cap['directory'];can,scope=parse((p/'sequence.bin').read_bytes(),list(range(cap['position'])),profile);states[str(cap['position'])]=dict(active_kv=hashlib.sha256(can).hexdigest(),frontier=sha(p/'frontier.f32'),native=str(p))
        references[input['id']]=dict(endpoint=r['endpoint'],ids=ids,prompt=r['prompt_ids'],states=states)
        put(proofdir/(str(ix)+'.json'),references[input['id']]);print('independent main reference',ix,flush=True)
    records=[];inputs={x['id']:x for x in f['inputs']};sched=f['schedule']['slots']
    for session in range(4):
        session_rows=[];actual_work=dict(requests=0,token_rows=0,operators=0);t=time.monotonic();slots=[x for x in sched if x['session']==session]
        for j in range(0,len(slots),2):
            pair=slots[j:j+2];arm=pair[0]['arm'];inp=inputs[pair[0]['input_id']];label='D-main-s'+str(session)+'-pair'+str(j//2)
            out=execute(test_job(label,arm,pair,inp));ref=references[inp['id']]
            work=json.loads((out/'session-result.json').read_bytes())['actual_work']
            for k in actual_work:actual_work[k]+=work[k]
            for planned in pair:
                r=json.loads((out/'native'/(planned['slot']+'.json')).read_bytes());assert r['endpoint']==ref['endpoint'] and r['ids']==ref['ids'],'main autonomous mismatch; invalidate version, no tuning'
                p=out/'native'/planned['slot']/'target/state/final-clean';meta=dict(x.split('=',1) for x in (p/'capture.txt').read_text().splitlines());count=int(meta['position_max'])+1;assert str(count) in ref['states']
                can,scope=parse((p/'sequence.bin').read_bytes(),list(range(count)),profile);expected=ref['states'][str(count)]
                assert hashlib.sha256(can).hexdigest()==expected['active_kv'] and sha(p/'frontier.f32')==expected['frontier'],'main final-state mismatch; invalidate version'
                for name in ('sequence.bin','frontier.f32'):
                    original=Path(expected['native'])/name;copy=p/name
                    if sha(original)==sha(copy) and not os.path.samefile(original,copy):
                        temp=copy.with_name(copy.name+'.verified-link');os.link(original,temp);os.replace(temp,copy)
                row=dict(planned,service_s=r['service_seconds'],status='COMPLETE',endpoint_equal=True,endpoint_sha256=digest(r['endpoint']),fallback_count=0,source_freeze_sha256=freeze_sha,numeric_profile_sha256=digest(profile),final_state_equal=True,final_frontier_equal=True,materialized_count=count,native=str(out/'native'/(planned['slot']+'.json')),post_service_state_s=r['post_service_state_seconds'])
                records.append(row);session_rows.append(row)
            put(out/'SLOT_VALIDATION.json',session_rows[-2:]);print('main pair complete',session,j//2,arm,flush=True)
        put(ROOT/('D-main-session-'+str(session)+'.json'),dict(attempt_id='D-main-session-'+str(session),binding_sha256=freeze_sha,completed=True,actual_work=actual_work,records=session_rows,host_wall_s=time.monotonic()-t,worker_loads=48))
    result=dict(lane='rtx-draft',panel_sha256=digest(f['panel']),frozen_before_test=True,qualification_status='FINITE_NATIVE_CAPTURE_MATCH',source_freeze_sha256=freeze_sha,numeric_profile_sha256=digest(profile),records=records)
    put(ROOT/'D-MAIN-RECORDS.json',result)
    from analyze import analyze
    put(ROOT/'D-MAIN-ANALYSIS.json',analyze(f['panel'],'rtx-draft',result))
if __name__=='__main__':prepare() if sys.argv[1]=='prepare' else main()
