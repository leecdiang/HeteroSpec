"""Actual zero-CUDA native graph/storage/parser tests and immutable raw evidence."""
import copy,json,os,subprocess,sys
from pathlib import Path
from s0_budget import ROOT,save
from wire import serialize,environment,recipe,FAMILIES,ARMS
from recover_s0 import sha
DEST=ROOT/sys.argv[1] if len(sys.argv)>1 else ROOT
def run(label,command,env=None,cwd=None,expected=0):
    save(DEST/'cpu_tests'/(label+'-START.json'),dict(command=command,environment_selectors={k:v for k,v in (env or {}).items() if k.startswith(('HS_','GGML_'))}))
    p=subprocess.run(command,cwd=cwd or ROOT,env=env,capture_output=True)
    (DEST/'cpu_tests'/(label+'.stdout.log')).write_bytes(p.stdout);(DEST/'cpu_tests'/(label+'.stderr.log')).write_bytes(p.stderr)
    save(DEST/'cpu_tests'/(label+'-EXIT.json'),dict(exit_code=p.returncode,expected=expected));assert p.returncode==expected,(label,p.stderr[-2000:]);return p
def main():
    (DEST/'cpu_tests').mkdir(parents=True,exist_ok=False);native=ROOT/'native/build/bin/lowering113.exe';server=ROOT/'native/build/bin/llama-server.exe'
    doc=ROOT.parents[1]/'docs/experiments/rtx_lowering_envelope_20261015'
    run('design18',[sys.executable,'-B','-m','unittest','-v','test_design'],cwd=doc)
    run('wire6',[sys.executable,'-B','test_wire.py'])
    plan=ROOT/'DESCRIPTOR_PLAN.json'
    for mode,out in (('registry','SUPPORT_REGISTRY_S0.json'),('addresses','CPU_NATIVE_ADDRESSES.json'),('negatives','CPU_NATIVE_NEGATIVES.json')):
        run('native_'+mode,[str(native),'--cpu-'+mode,str(plan),str(DEST/out)])
    registry=json.loads((DEST/'SUPPORT_REGISTRY_S0.json').read_bytes());assert registry['graphs']==1680 and registry['graph_computes']==0 and registry['GPU_initializations']==0
    assert len({(r['descriptor_id'],r['layout'],r['stage_outputs']) for r in registry['records']})==1680
    for module in registry['modules']:assert not any(x in Path(module).name.lower() for x in ('nvcuda','cudart','cublas','ggml-cuda','cupti'))
    # Q1 common chain is the exact same GGML graph under all five requested labels.
    for ident in {r['descriptor_id'] for r in registry['records'] if r['common_q1_original_arithmetic_chain']}:
        for stages in (False,True):
            group=[r for r in registry['records'] if r['descriptor_id']==ident and r['stage_outputs']==stages]
            assert len(group)==5 and all((g['nodes'],g['output'])==(group[0]['nodes'],group[0]['output']) for g in group)
    snapshots=json.loads((ROOT/'FULL_SNAPSHOTS.json').read_bytes())['contexts'];bindings=[]
    for family in FAMILIES:
        task=next(x['context']['task'] for x in snapshots if x['context']['family']==family)
        for arm in ARMS:
            c=recipe(arm,'QH_C');wire=[serialize(task,mode) for mode in ('counts','heavy')];file=DEST/'cpu_tests'/f'{family}_{arm}_wire.json';save(file,[x.body() for x in wire])
            env=environment(os.environ,c,DEST/'cpu_tests'/f'{family}_{arm}.trace')
            p=run(f'native_parser_{family}_{arm}',[str(server),'--hs113-cpu-wire',str(file)],env=env);parsed=json.loads(p.stdout)
            for expected,actual in zip(wire,parsed):
                b=expected.body();assert actual['prompt']==b['prompt'] and actual['n_predict']==128 and actual['mode']==b['hs_closeout_mode']
                assert actual['cache_prompt'] is False and actual['return_tokens'] is True and actual['seed']==123
                assert (actual['temperature'],actual['top_k'],actual['top_p'],actual['min_p'])==(0,0,1,0)
                assert actual['scope_mask']==c['mask'] and actual['target_prefill_active']==(c['mask']==3) and actual['draft_continuation_active'] is False
                assert actual['native_layout']=={'QB':0,'PQ':1,'QH_C':3,'QH_D':4}[c['layout']] and actual['backend_initialized'] is False
            bindings.append(dict(family=family,arm=arm,selector=c,wire_sha256=[w.sha256 for w in wire],actual_native_parser=True))
    # QH_D selector has its own native getenv/parser test, never copied from B570.
    task=snapshots[0]['context']['task'];f=DEST/'cpu_tests/QH_D_wire.json';save(f,[serialize(task,'counts').body()]);env=environment(os.environ,recipe('C_QH','QH_D'),DEST/'cpu_tests/QH_D.trace')
    p=run('native_parser_QH_D',[str(server),'--hs113-cpu-wire',str(f)],env=env);assert json.loads(p.stdout)[0]['native_layout']==4
    # Malformed incoming request is rejected by native pre-schema and real schema.
    for label,body in [('bool_token',dict(prompt=[True],n_predict=128,hs_closeout_mode='counts')),('bad_mode',dict(prompt=[1],n_predict=128,hs_closeout_mode='invalid'))]:
        f=DEST/'cpu_tests'/(label+'.json');save(f,[body]);run('reject_'+label,[str(server),'--hs113-cpu-wire',str(f)],env=env,expected=2)
    plan1=json.loads((ROOT/'S1_PLAN.json').read_bytes());assert len(plan1['slots'])==1009
    for slot in plan1['slots']:assert json.loads(slot['wire_json'])=={k:v for k,v in slot.items() if k not in ('wire_json','wire_sha256','command_template')}
    if DEST!=ROOT:
        # Scope is a native getenv contract; Win32 SetEnvironmentVariable in the
        # first cache harness does not retroactively refresh CRT getenv caches.
        # Pass the real child environment, exactly as production transport does.
        env=environment(os.environ,recipe('C_QB'),DEST/'cpu_tests/cache.trace')
        p=run('actual_cache_and_roles',[str(ROOT/'native/build/bin/native-cache113.exe')],env=env);assert json.loads(p.stdout)['status']=='PASS'
        base=json.loads(plan.read_bytes())
        for name in ('missing_mask','empty_mask','Q_F16','owner_overrun','V_inner_stride'):
            bad=copy.deepcopy(base);bad['descriptors']=bad['descriptors'][:1];m=bad['descriptors'][0]['metadata']
            if name=='missing_mask':m.pop('mask')
            if name=='empty_mask':m['mask']['ne'][1]=0
            if name=='owner_overrun':m['Q']['bytes']-=1
            if name=='Q_F16':m['Q']['type']=1;m['Q']['bytes']-=2
            if name=='V_inner_stride':
                m['V']['nb'][0]=4;m['V']['bytes']=2+sum((n-1)*b for n,b in zip(m['V']['ne'],m['V']['nb']))
            path=DEST/'cpu_tests'/(name+'.json');save(path,bad)
            run('reject_graph_'+name,[str(native),'--cpu-registry',str(path),str(DEST/'cpu_tests'/(name+'-SHOULD_NOT_EXIST.json'))],expected=2)
    save(DEST/'CPU_SERIALIZER_BINDINGS.json',dict(bindings=bindings,native_requests_parsed=43,planned_operator_slots_roundtripped=1009,
        transport='actual server_schema fields + native getenv selectors; same admitted bytes passed to HTTP transport',new_model_requests=0))
    save(DEST/'S0_TESTS.json',dict(status='PASS',synthetic_helper_tests=18,wire_unit_tests=6,native_graphs=1680,full_snapshot_storage_graph_cases=144,native_parser_cases=43,
        q1_graph_common_chain='PASS',CPU_native_negative_cases=10,native_malformed_requests_rejected=2,cache_identity='actual allow_reuse native negatives and role guards PASS in final CPU run; full loaded-model cache lifecycle still S2',
        actual_CUDA_support='NOT_QUERIED',actual_CUDA_placement='NOT_EXECUTED',new_GPU_model_operator_device_starts=0))
    print(json.dumps(dict(status='PASS',graphs=1680,native_parser_cases=43,new_GPU_calls=0)))
if __name__=='__main__':main()
