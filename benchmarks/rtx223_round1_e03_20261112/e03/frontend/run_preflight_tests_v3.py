"""Focused native-host profile/gate tests; never pass a model-bearing job CLI."""
from pathlib import Path
import copy,hashlib,json,subprocess,time
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def main():
    out=HERE/'preflight-tests-v3';out.mkdir(exist_ok=False)
    runtime={'schema':'heterospec.e03.isolated-runtime.v1','device_uuid':'GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd','graph_policy':'disabled_for_all_arms_draft_and_reference','arm':'A','budget_family':'rtx221-round1-20261112-e01','native_release':'BLOCKED','directory':str(ROOT/'e03/runtime/build-v1/bin'),'modules':{'ggml-cuda.dll':{'sha256':'a'*64},'ggml-base.dll':{'sha256':'b'*64}},'expected_runtime_metadata':{'scope':'CPU_CONFIGURATION_FIXTURE_NOT_ACTUAL_IDENTITY'}}
    runtime['directory']=str(ROOT/'runtime/build-v2/bin')
    runtime['launch_budget']={'schema':'heterospec.e03.worker-launch-reservation.v1','family_limit':4096,'inherited_charged':0,'worker_reservation':128,'epoch_tag':'rtx223-round1-20261112-e03','coverage':'UNQUALIFIED_BLOCKED','expected_metadata':{'scope':'CPU_CONFIGURATION_FIXTURE_NOT_ACTUAL_IDENTITY'}}
    target={'execution_profile':'target_q8_capture','arm':'A','runtime_binding':runtime,'family':'Qwen','target_model':'not-loaded.gguf','target_sha256':'c'*64,'n_ctx':1024,'threads':24,'lowering':'LOCAL','draft':False,'draft_width':1,'residency':'target_only','profile':False,'k':7,'target_output_reserve':8,'proposal_mode':'live','evidence_capture_byte_reservation':67108864,'actual_q8_capture':{'schema':'heterospec.actual-q8-capture.v1','arm':'A','q':8,'weight_type':'Q8_0','activation_type':'F32','allow_derived_input':False,'phase':'VERIFY','weight_name':'blk.0.attn_q.weight','output_dir':str(out/'never-created-capture'),'capture_byte_reservation':67108864},'forced':[{'ids':[1,2,3],'phase':'PREFILL','all':False},{'ids':list(range(100,108)),'phase':'VERIFY','all':True}],'observe_positions':[],'state_positions':[],'capability_request':{}}
    def arm(job,name):
        job=copy.deepcopy(job);job['arm']=name;job['runtime_binding']['arm']=name
        if 'actual_q8_capture' in job:job['actual_q8_capture']['arm']=name
        return job
    m2=copy.deepcopy(target);m2.update(execution_profile='m2_dynamic_request',draft=True,draft_width=4,residency='matched',draft_model='not-loaded-draft.gguf',draft_sha256='d'*64,inputs=[{'name':'CPU_ONLY_NOT_EXECUTED','input':{'prompt_ids':[1,2,3],'cap':8}}]);[m2.pop(k) for k in ('forced','observe_positions','state_positions','actual_q8_capture')]
    cases=[]
    def case(name,core,job,code=0,reason=None,mode='--e03-preflight'):cases.append({'name':name,'core':core,'job':job,'expected_code':code,'expected_reason_contains':reason,'mode':mode})
    case('dedicated-target-A','loop4',target);case('dedicated-target-B','packed',arm(target,'B'));case('dedicated-target-C-cannot-masquerade-oracle','packed',arm(target,'C'),2,'oracle is A/B only')
    case('M2-live-D4-A','loop4',m2);case('M2-live-D4-C','packed',arm(m2,'C'))
    bad=copy.deepcopy(target);bad['draft']=True;case('target-profile-cannot-enable-draft','loop4',bad,2,'dedicated q8 capture profile')
    bad=copy.deepcopy(target);bad['draft_model']='unused.gguf';case('target-profile-unused-draft-identity-refuses','loop4',bad,2,'unused draft identities')
    bad=copy.deepcopy(m2);bad['draft']=False;case('M2-missing-draft-refuses','loop4',bad,2,'requires actual D4')
    bad=copy.deepcopy(target);bad['unbound_switch']=True;case('unknown-field-reject-before-backend','loop4',bad,2,'Unknown e03 native job field')
    case('wrong-core-C-loop4','loop4',arm(target,'C'),2,'linked graph core')
    bad=copy.deepcopy(target);bad['runtime_binding']['device_uuid']='GPU-foreign';case('foreign-device-refuses','loop4',bad,2,'wrong frozen physical device')
    bad=copy.deepcopy(target);bad['runtime_binding']['native_release']='READY';case('self-declared-release-refuses','loop4',bad,2,'cannot self-release')
    bad=copy.deepcopy(target);bad['forced']=[];case('empty-q8-input-refuses','loop4',bad,2,'nonempty forced native input')
    bad=copy.deepcopy(target);bad['actual_q8_capture']['allow_derived_input']=True;case('derived-input-capture-refuses','loop4',bad,2,'descriptor contract mismatch')
    bad=copy.deepcopy(target);bad['runtime_binding']['launch_budget']['worker_reservation']=4097;case('launch-reservation-overflow-refuses','loop4',bad,2,'original family cap')
    bad=arm(m2,'C');bad['actual_q8_capture']=copy.deepcopy(target['actual_q8_capture']);case('C-M2-cannot-label-oracle-capture','packed',bad,2,'cannot masquerade')
    bad=copy.deepcopy(target);bad['runtime_binding']['budget_family']='new-budget';case('budget-family-reset-refuses','loop4',bad,2,'budget family binding')
    bad=copy.deepcopy(target);bad['runtime_binding']['launch_budget']['coverage']='QUALIFIED';case('self-declared-kernel-coverage-refuses','loop4',bad,2,'cannot be self-released')
    case('native-DLL-gate-target-refuses','loop4',target,2,'NATIVE_BLOCKED',mode='--e03-native-gate')
    case('native-DLL-gate-M2-refuses','packed',arm(m2,'B'),2,'NATIVE_BLOCKED',mode='--e03-native-gate')
    (out/'FROZEN_CASES.json').write_text(json.dumps(cases,indent=2),encoding='utf8')
    build=json.loads((HERE/'build-v3/BUILD.json').read_bytes());records=[]
    for c in cases:
        fixture=out/(c['name']+'.json');fixture.write_text(json.dumps(c['job'],indent=2),encoding='utf8');exe=Path(build['builds'][c['core']]['exe']);expected=build['builds'][c['core']]['exe_sha256']
        if hashlib.sha256(exe.read_bytes()).hexdigest()!=expected:raise RuntimeError('EXE identity changed')
        args=[str(exe),c['mode'],str(fixture)];began=time.monotonic();r=subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=10,creationflags=0x08000000)
        log=out/(c['name']+'.log');log.write_bytes(r.stdout);data=json.loads(r.stdout)
        passed=r.returncode==c['expected_code'] and (c['expected_reason_contains'] is None or c['expected_reason_contains'] in data.get('reason','')) and data.get('CUDA_DLL_loads')==0
        records.append({'name':c['name'],'argv':args,'returncode':r.returncode,'seconds':time.monotonic()-began,'passed':passed,'result':data,'exe_sha256':expected,'log_sha256':hashlib.sha256(r.stdout).hexdigest()})
    record={'schema':'heterospec.e03.preflight-host-tests.v1','status':'PASS' if all(r['passed'] for r in records) else 'FAIL','cases':len(records),'records':records,'model_requests':0,'target_draft_rows':0,'CUDA_DLL_normal_loads':0,'GPU_launches':0,'native_qualification':'NOT_RUN','scope':'new CPU profile/explicit-denial tests; declared identities are fixtures, not actual runtime identity observations'}
    (out/'RESULT.json').write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps({'status':record['status'],'cases':len(records),'failed':[r['name'] for r in records if not r['passed']]},indent=2))
    if record['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
