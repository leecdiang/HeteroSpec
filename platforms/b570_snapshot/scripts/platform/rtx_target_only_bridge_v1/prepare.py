"""Validate existing assets and restore needed historical evidence through the CAS contract."""
import importlib.util, platform, shutil, sys, tarfile
from common import *

def main():
    if (DOC/'PREPARED.json').exists(): raise RuntimeError('Already prepared; inspect and resume')
    assert git('rev-parse','HEAD')==PIN
    DOC.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    old=ROOT/'benchmarks/rtx_target_verification_intervention_v1'
    contract=load(old/'INPUT_CONTRACT.json')
    assert [k for k,v in contract['inputs'].items() if v['group']=='old_regression']==TASKS
    archive=PRIOR/'work/rtx-target-v1/archive/raw-cas-v1.tar.gz'
    assert sha(archive)==load(old/'ARCHIVE_RECEIPT.json')['archive_sha256']
    # The existing documented clean restore is usable only after individual bindings
    # match its delivered CAS manifest. Missing files are extracted from verified CAS.
    mf=PRIOR/'work/rtx-target-v1/archive/MANIFEST.json';manifest=load(mf)
    history={};required={};restored=[]
    for t in TASKS:
        for c in ['N0','N1']:
            for rep in [1,2,3]:
                rel=f"work/rtx-target-v1/formal/{t.replace('/','-')}-{c}-r{rep}/result.json"
                rec=load(PRIOR/rel);bound=manifest['files'][rel]
                assert sha(PRIOR/rel)==bound['sha256']
                logs=[k for k in rec['files'] if k.endswith('/native.log')];assert len(logs)==1
                path=str(pathlib.PurePosixPath(rel).parent/logs[0])
                required[path]=manifest['files'][path]
                assert rec['files'][logs[0]]==required[path]['sha256']
                required[rel]=bound
                history[f'{t}/{c}/{rep}']={'result':rel,'native_log':path,'ids':rec['ids'],'endpoint':rec['endpoint']}
    for t in TASKS:
        for name in ['prompt','ids']: required[contract['inputs'][t][name]]=manifest['files'][contract['inputs'][t][name]]
    # Reuse clean-restored bytes, not unbound mutable working files.
    dest=DOC/'historical_raw';missing={}
    for rel,binding in required.items():
        p=PRIOR/'work/rtx-target-v1/clean-restored'/rel
        if p.exists() and sha(p)==binding['sha256']:
            q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);restored.append(rel)
        else: missing.setdefault(binding['sha256'],[]).append(rel)
    if missing:
        with tarfile.open(archive,'r:gz') as tf:
            for m in tf:
                h=m.name.removeprefix('cas/')
                if h in missing:
                    data=tf.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==h
                    for rel in missing.pop(h):
                        q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);restored.append(rel)
        assert not missing
    for rel,binding in required.items(): assert sha(dest/rel)==binding['sha256'] and (dest/rel).stat().st_size==binding['bytes']
    inputs={}
    for t in TASKS:
        orig=contract['inputs'][t];entry={'group':'old_regression'}
        for name in ['prompt','ids']:
            src=dest/orig[name];assert sha(src)==orig[name+'_sha256']
            rel=f"benchmarks/rtx_target_only_bridge_v1/inputs/{t.replace('/','-')}/"+('prompt.txt' if name=='prompt' else 'prompt_ids.json')
            q=ROOT/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,q)
            entry[name]=rel;entry[name+'_sha256']=sha(q)
        inputs[t]=entry
    save(DOC/'INPUT_CONTRACT.json',{'inputs':inputs,**{k:contract[k] for k in ['tokenizer_sha256','EOG','context','cap']},'source_sha256':sha(old/'INPUT_CONTRACT.json'),'format':'exact prior UTF-8 bytes; CLI removes one trailing LF; chat template thinking=false'})
    save(DOC/'COHORT.json',{'tasks':TASKS,'conditions':['N0','N1','U2'],'repetitions':3,'planned':171,'exposure':'retrospectively exposed 19-task cohort'})
    save(DOC/'HISTORICAL_BINDINGS.json',{'archive_sha256':sha(archive),'manifest_sha256':sha(mf),'files':required,'records':history})
    assets={};original=load(old/'ASSET_ENVIRONMENT.json')
    for label,b in original['files'].items():
        p=ASSET/pathlib.Path(b['path']).relative_to(pathlib.Path('D:/HeteroSpec-PC'))
        assert sha(p)==b['sha256'],label
        assets[label]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
    build=load(old/'BUILD_IDENTITY.json');native_dir=PRIOR/'work/rtx-target-v1/native-build/bin'
    for p in native_dir.iterdir():
        if p.suffix.lower() in ['.exe','.dll']:
            expected=build['binaries'][p.relative_to(PRIOR).as_posix()];assert sha(p)==expected
            assets['qualified_native/'+p.name]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
    tok=PRIOR/'work/rtx-target-v1/worker-bin/tokenizer.exe';assert sha(tok)==contract['tokenizer_sha256']
    assets['tokenizer']={'path':str(tok),'sha256':sha(tok),'bytes':tok.stat().st_size}
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.total,pci.bus_id','--format=csv,noheader'],text=True).strip()
    assert gpu.startswith('NVIDIA GeForce RTX 5070 Ti Laptop GPU,')
    save(DOC/'ASSET_ENVIRONMENT.json',{'captured_utc':now(),'gpu':gpu,'os':platform.platform(),'python':sys.version,'assets':assets,'original_runtime_all_hashes_equal':True,'qualified_native_binary_hash_equal':True,'prior_environment':original['environment'],'overrides_removed':{k:v for k,v in os.environ.items() if k.startswith(('HS_','LLAMA_','GGML_','CUDA_'))},'omitted_from_delivery':'model weights, runtime binaries; identities are not independent machine authentication'})
    spec=importlib.util.spec_from_file_location('native',ROOT/'scripts/platform/rtx_trajectory_cost_v4/native.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    base=native.templates(native.paths(ASSET));u=base['TARGET_REFERENCE'].copy();u[u.index('--ubatch-size')+1]='2'
    commands={};envs={}
    for c in ['N0','N1','U2']:
        cmd=(u if c=='U2' else base['RTX_BATCHED_K2']).copy()
        if c!='U2': cmd[0]=str(native_dir/'llama-cli.exe');cmd+=['--spec-draft-threads','24','--spec-draft-threads-batch','24']
        cmd+=['--threads','24','--threads-batch','24'];commands[c]=cmd
        envs[c]={'LLAMA_BATCH_DEBUG':'1'}
        if c!='U2': envs[c].update(HS_NATIVE_CAPTURE='{trace}',HS_TARGET_CONTINUATION_UB='2' if c=='N0' else '1')
    order=[['N0','N1','U2'],['N1','U2','N0'],['U2','N0','N1']]
    queue=[{'task':t,'condition':c,'rep':r,'key':f'{t}/{c}/{r}'} for r in [1,2,3] for t in TASKS for c in order[r-1]]
    save(DOC/'PROTOCOL.json',{'study':'RTX_TARGET_ONLY_BRIDGE_V1','version':1,'source':PIN,'upstream':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2','tasks':TASKS,'conditions':['N0','N1','U2'],'repetitions':3,'planned':171,'command_templates':commands,'environment_templates':envs,'balanced_order':order,'queue':queue,'engineering_tasks':['HumanEval/15','HumanEval/25','HumanEval/18','HumanEval/31'],'engineering_runs':12,'warmup':'--no-warmup, fresh processes, cache-ram0; OS file cache not flushed; no latency claim','qualification':'same byte-identical N0/N1 frontend, retained prior instrumentation qualification; local full endpoint/input/device/thread/handoff smoke; no inter-condition equality gate','endpoint':'first inclusive EOG or cap128; both stop markers at EOG128; raw samples/decisions retained separately','diagnostic_limit':12,'diagnostic_tasks_limit':4,'diagnostic_selection':'new U2/N1 mismatches or any within-condition instability, sorted by minimum zero-based first divergence then numeric task ID; fill with /15,/25,/18 in that order and /31 if needed; <=4','retries':{'maximum_attempts':3,'only':'infrastructure failure after diagnosis; never token disagreement','stall_seconds':120,'timeout_policy':'300 seconds with no raw-log growth for 120 seconds; progressing runs may exceed 300 seconds','restart_limit':1},'predicates':'full committed-array equality; endpoint equality; conjunction. Difference count=sum(positional substitutions over common length)+absolute length difference; denominator=max(lengths)','statistics':'19 task units, 57 paired stability observations; no independent-token/repetition inference','performance_claim':False})
    sources=['benchmarks/rtx_target_verification_intervention_v1/'+n for n in ['PROTOCOL.json','INPUT_CONTRACT.json','ASSET_ENVIRONMENT.json','HISTORICAL_MAPPING.json','G0_THREADS24.json','FREEZE.json','BUILD_IDENTITY.json','ARCHIVE_RECEIPT.json']]
    sources+=['benchmarks/rtx_trajectory_cost_v4/'+n for n in ['A_trajectory/RESERVED_PREDICTIONS.json','INPUT_CONTRACT.json','JOINT_PROTOCOL.json','EFFECTIVE_CONFIGURATION.json']]
    sources+=['paper/mlsys2027/reviews/reconstruction_v010/rtx/FORMAL_ARRAYS_NEUTRAL.json']
    save(DOC/'SOURCE_BINDINGS.json',{'commit':PIN,'files':{p:sha(ROOT/p) for p in sources}})
    save(DOC/'RESTORE_PREPARATION.json',{'status':'PASS','archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'selected_logical_files':len(restored),'route':'hash checked delivered CAS archive and its existing clean restoration; selected members checked by length/hash; no new full-archive audit claimed','files':required})
    save(DOC/'PREPARED.json',{'utc':now(),'status':'PREPARED_NOT_QUALIFIED','formal_runs':0,'local_native':str(native_dir/'llama-cli.exe')})
    print(json.dumps({'status':'PREPARED','assets':len(assets),'restored':len(restored),'formal':0}),flush=True)
if __name__=='__main__': main()
