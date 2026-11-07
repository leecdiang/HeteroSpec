"""Prospective C1536 strongest-control panel after all native gates."""
from operator_service_host import *
from design import schedule
from analyze import analyze
import sys
HERE=Path(__file__).resolve().parent;FREEZE=ROOT/'O-FREEZE.json'
def prepare():
    for name in ('O-REAL-OPERAND-QUALIFICATION.json','O-RUNTIME-BRIDGE.json','O-BOUNDARY-QUALIFICATION.json'):
        assert json.loads((ROOT/name).read_bytes())['all_equal']
    assert json.loads((ROOT/'O-SERVICE-QUALIFICATION.json').read_bytes())['status']=='FINITE_NATIVE_CAPTURE_MATCH'
    assert json.loads((ROOT/'O-TRACE-REVIEW.json').read_bytes())['actual_loop4_route_verified']
    scripts=('formal_o_host.py','operator_service_host.py','operator_host.py','native_adapter.py','bridge_host.py','build_host.py','runner.py','common.py','design.py','active_kv.py','analyze.py','qualify_host.py','normalize.py','trace.py','qualify.py','archive_host.py','build_operator_driver.py')
    pins={str(HERE/name):sha(HERE/name) for name in scripts};pins[str(HERE/'operator_replay.inc')]=sha(HERE/'operator_replay.inc')
    for name in ('O-REAL-OPERAND-QUALIFICATION.json','O-RUNTIME-BRIDGE.json','O-BOUNDARY-QUALIFICATION.json','O-SERVICE-QUALIFICATION.json','O-SERVICE-RUNTIME-BINDING.json','O-TRACE-REVIEW.json'):pins[str(ROOT/name)]=sha(ROOT/name)
    for arm in ('original',*ARMS):
        path=Path('D:/rtx184-operator')/(arm+'-service-v4')
        for p in [path/'service.cpp',path/'BUILD.json',path/'bin/service.exe']:pins[str(p)]=sha(p)
        if arm!='original':
            for ix in range(4):
                for stage in ('development','priming'):
                    qualified=json.loads((ROOT/'O-SERVICE-RUNTIME-BINDING.json').read_bytes())['proofs'];entry=next(x for x in qualified if x['root']==ix and x['arm']==arm)
                    receipt=Path(entry[stage])/'session-result.json';r=json.loads(receipt.read_bytes());assert all(x['executable_sha256']==sha(path/'bin/service.exe') for x in r['records']);pins[str(receipt)]=sha(receipt)
                    prior=json.loads((receipt.parent/'job.json').read_bytes())['build_manifest'];current=json.loads((path/'BUILD.json').read_bytes());assert prior==current,'qualified runtime bundle differs';pins[str(receipt.parent/'job.json')]=sha(receipt.parent/'job.json')
                    observed=json.loads((receipt.parent/'ACTUAL_MODULES.json').read_bytes())
                    external=json.loads((ROOT/'O-EXTERNAL-MODULES.json').read_bytes())
                    for phase in ('before','after'):
                        for name,h in external.items():assert any(Path(x['path']).name.lower()==Path(name).name.lower() and x['sha256']==h for x in observed[phase]),'qualification external runtime drift'
    for name,h in json.loads((ROOT/'O-EXTERNAL-MODULES.json').read_bytes()).items():assert sha(Path(name))==h;pins[name]=h
    pins[str(ROOT/'O-EXTERNAL-MODULES.json')]=sha(ROOT/'O-EXTERNAL-MODULES.json')
    sel=ROOT/'selection-v3';panel=json.loads((sel/'O-panel.json').read_bytes());sched=schedule(panel,'rtx-operator')
    put(FREEZE,dict(status='FROZEN_BEFORE_TEST_OUTPUTS',lane='rtx-operator',panel=panel,schedule=sched,inputs=json.loads((sel/'O-inputs.json').read_bytes()),file_pins=pins,profile=json.loads((ROOT/'O-profile-8B/PROFILE.json').read_bytes()),lifecycle='PR171 C1536 all-GPU target plus draft, k3, cap128, QB-local target width32; each version-specific worker establishes its qualified same-arm warmup followed by resident-reset measurement; model/pool construction outside unchanged complete-service clock and separately charged',main_requests=432,limits=LIMITS,original_reference=sha(FROZEN.parent/'oracle01/service.exe'),no_wb_rescue_panel=True))
def main():
    f=json.loads(FREEZE.read_bytes());assert f['status']=='FROZEN_BEFORE_TEST_OUTPUTS'
    for name,h in f['file_pins'].items():assert sha(Path(name))==h,('freeze drift',name)
    freeze_sha=sha(FREEZE);profile=f['profile'];references={};outrefs=ROOT/'O-main-reference';outrefs.mkdir()
    for ix,input in enumerate(f['inputs']):
        out=execute(job('O-main-original-'+str(ix),'old',input,('ref',)));r=json.loads((out/'native/ref/receipt.json').read_bytes());n=len(input['prompt_ids']);ids=r['ids']
        replay=job('O-main-forced-'+str(ix),'original',input);replay['operator_service'].pop('blocks');replay['operator_service']['forced']=dict(no_candidate_payload=True,prompt_ids=input['prompt_ids'],producer=dict(caller_lengths=[n],last_output_flags=[True]),paths=[dict(suffix=ids,positions=[n+len(ids)-1,n+len(ids)])]);replay['reservation']=dict(requests=1,token_rows=n+len(ids),operators=0)
        out=execute(replay);rr=json.loads((out/'native/result.json').read_bytes());states={}
        for cap in rr['paths'][0]['captures']:
            p=out/'native'/cap['directory'];can,_=parse((p/'sequence.bin').read_bytes(),list(range(cap['position'])),profile);states[str(cap['position'])]=dict(active_kv=hashlib.sha256(can).hexdigest(),frontier=sha(p/'frontier.f32'),native=str(p))
        references[input['id']]=dict(endpoint=r['endpoint'],ids=ids,states=states);put(outrefs/(str(ix)+'.json'),references[input['id']]);print('O independent main reference',ix,flush=True)
    records=[];inputs={x['id']:x for x in f['inputs']}
    for session in range(6):
        slots=[x for x in f['schedule']['slots'] if x['session']==session];session_rows=[];actual_work=dict(requests=0,token_rows=0,operators=0);start=time.monotonic()
        for j in range(0,len(slots),2):
            pair=slots[j:j+2];arm=pair[0]['arm'];input=inputs[pair[0]['input_id']];ref=references[input['id']]
            pair_job=job('O-main-s'+str(session)+'-pair'+str(j//2),arm,input,tuple(p['slot'] for p in pair))
            pair_job['external_modules']=json.loads((ROOT/'O-EXTERNAL-MODULES.json').read_bytes())
            for slot,planned in zip(pair_job['operator_service']['blocks'][0]['slots'],pair):slot.update(kind=planned['kind'],planned=planned)
            out=execute(pair_job)
            work=json.loads((out/'session-result.json').read_bytes())['actual_work']
            for k in actual_work:actual_work[k]+=work[k]
            for planned in pair:
                p=out/'native'/planned['slot'];r=json.loads((p/'receipt.json').read_bytes());assert r['endpoint']==ref['endpoint'] and r['ids']==ref['ids'],'O main endpoint incompatibility; retain and invalidate'
                raw=p/'target/state/final-clean';meta=dict(x.split('=',1) for x in (raw/'capture.txt').read_text().splitlines());count=int(meta['position_max'])+1;assert str(count) in ref['states'];expected=ref['states'][str(count)];can,_=parse((raw/'sequence.bin').read_bytes(),list(range(count)),profile)
                assert hashlib.sha256(can).hexdigest()==expected['active_kv'] and sha(raw/'frontier.f32')==expected['frontier'],'O main state incompatibility; retain and invalidate'
                for name in ('sequence.bin','frontier.f32'):
                    reference=Path(expected['native'])/name;copy=raw/name
                    if sha(reference)==sha(copy) and not os.path.samefile(reference,copy):temp=copy.with_name(copy.name+'.verified-link');os.link(reference,temp);os.replace(temp,copy)
                row=dict(planned,service_s=r['service_seconds'],status='COMPLETE',endpoint_equal=True,endpoint_sha256=digest(r['endpoint']),fallback_count=0,source_freeze_sha256=freeze_sha,numeric_profile_sha256=digest(profile),final_state_equal=True,final_frontier_equal=True,materialized_count=count,native=str(p/'receipt.json'),post_service_state_s=r['post_service_state_seconds'],prefill_wall_s=r['prefill_wall_seconds'])
                records.append(row);session_rows.append(row)
            put(out/'SLOT_VALIDATION.json',session_rows[-2:]);print('O main pair complete',session,j//2,arm,flush=True)
        put(ROOT/('O-main-session-'+str(session)+'.json'),dict(attempt_id='O-main-session-'+str(session),binding_sha256=freeze_sha,completed=True,actual_work=actual_work,records=session_rows,host_wall_s=time.monotonic()-start,worker_loads=36))
    result=dict(lane='rtx-operator',panel_sha256=digest(f['panel']),frozen_before_test=True,qualification_status='FINITE_NATIVE_CAPTURE_MATCH',source_freeze_sha256=freeze_sha,numeric_profile_sha256=digest(profile),records=records)
    put(ROOT/'O-MAIN-RECORDS.json',result);put(ROOT/'O-MAIN-ANALYSIS.json',analyze(f['panel'],'rtx-operator',result))
if __name__=='__main__':prepare() if sys.argv[1]=='prepare' else main()
