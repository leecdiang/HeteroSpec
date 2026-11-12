"""Separately freeze and link the 145 fresh e04-v2 objects; never load the DLL."""
from pathlib import Path
import datetime,hashlib,json,subprocess,time
from input_closure_v2 import ReadFreeze

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;BASE=HERE/'build-v2';OUT=HERE/'link-v3';FREEZE=ROOT/'e04/freeze/link-v3'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2),encoding='utf8')

def main():
    OUT.mkdir(exist_ok=False);FREEZE.mkdir(parents=True,exist_ok=False)
    for name in ('bin','temp'):(OUT/name).mkdir()
    prior=ROOT/'e04/freeze/v2/FREEZE.json';frozen=json.loads(prior.read_bytes());compiled=json.loads((BASE/'COMPILE_RECEIPTS.json').read_bytes());state=json.loads((BASE/'BUILD.json').read_bytes())
    if len(compiled)!=145 or any(r['returncode']!=0 for r in compiled) or state['dependency_closure']!='PASS' or state['input_posthash_changes'] or state['input_membership_added'] or state['input_membership_removed']:raise RuntimeError('fresh unchanged compilation prerequisites failed')
    env=json.loads((ROOT/'e04/freeze/v2/ENVIRONMENT.json').read_bytes());env['TEMP']=env['TMP']=str(OUT/'temp')
    link=json.loads((ROOT/'e04/freeze/v2/LINK_COMMAND.json').read_bytes())
    link=[token.replace(str(BASE/'bin/ggml-cuda.dll'),str(OUT/'bin/ggml-cuda.dll')).replace(str(BASE/'ggml-cuda.lib'),str(OUT/'ggml-cuda.lib')) for token in link]
    rsp=OUT/'LINK.rsp';rsp.write_text('\n'.join(subprocess.list2cmdline([x]) for x in link[1:]),encoding='utf8')
    write(FREEZE/'ENVIRONMENT.json',env);write(FREEZE/'LINK_COMMAND.json',link)
    inputs=dict(frozen['inputs'])
    for receipt in compiled:
        path=receipt['object'];digest=receipt['object_sha256']
        if sha(path)!=digest:raise RuntimeError('fresh object hash changed before second freeze')
        inputs[path]={'sha256':digest,'bytes':Path(path).stat().st_size,'role':'FRESH_E04_V2_OBJECT_NOT_E03_OR_FAILED_V1'}
    for path in [prior,BASE/'COMPILE_RECEIPTS.json',BASE/'DEPENDENCY_CLOSURE.json',BASE/'BUILD.json',BASE/'LINK.json',BASE/'LINK_INPUT_FREEZE.json',FREEZE/'ENVIRONMENT.json',FREEZE/'LINK_COMMAND.json',rsp,Path(__file__)]:inputs[str(path)]={'sha256':sha(path),'bytes':path.stat().st_size}
    recipe={'schema':'heterospec.e04.separate-link-freeze.v1','created_utc':now(),'prior_full_source_freeze':str(prior),'prior_full_source_freeze_sha256':sha(prior),'prior_compile_result':str(BASE/'BUILD.json'),'prior_link_failure':'LNK1104 C:/Windows/lnk{...}.tmp; TEMP/TMP omitted from controlled link environment','fresh_objects':145,'e03_objects':0,'failed_v1_objects':0,'sessions':'v2 compile and link-v3 are separate lock sessions; no uninterrupted-freeze claim','new_link_env':str(FREEZE/'ENVIRONMENT.json'),'new_response':str(rsp),'inputs':inputs,'DLL_loads':0,'GPU_launches':0}
    write(FREEZE/'FREEZE.json',recipe);freeze_sha=sha(FREEZE/'FREEZE.json');print(json.dumps({'stage':'LINK_FROZEN','freeze_sha256':freeze_sha,'inputs':len(inputs),'fresh_objects':145}),flush=True)
    held=ReadFreeze();started=time.monotonic();error=None;code=None
    try:
        for path,row in inputs.items():
            if sha(path)!=row['sha256']:raise RuntimeError('input changed before link lock '+path)
            held.add(path)
        held.add(FREEZE/'FREEZE.json')
        if sha(FREEZE/'FREEZE.json')!=freeze_sha:raise RuntimeError('link freeze changed while locking')
        write(OUT/'ADMISSION.json',{'utc':now(),'freeze_sha256':freeze_sha,'read_handles':len(held.handles),'TEMP':env['TEMP'],'TMP':env['TMP'],'no_numerical_load':True})
        try:
            with (OUT/'link.log').open('xb') as f:process=subprocess.run([link[0],'@'+str(rsp)],cwd=OUT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
            code=process.returncode
        except Exception as exc:error=repr(exc)
        changed=[path for path,row in inputs.items() if sha(path)!=row['sha256']]
        freeze_after=sha(FREEZE/'FREEZE.json')
        dll=OUT/'bin/ggml-cuda.dll'
        result={'schema':'heterospec.e04.separate-fresh-object-link.v1','status':'NUMERICAL_DLL_LINKED_NOT_LOADED_NOT_QUALIFIED' if code==0 and not changed and freeze_after==freeze_sha else 'LINK_FAILED_OR_INPUT_CHANGED','source_compile_session':str(BASE),'fresh_e04_v2_compiled_objects':145,'e03_objects':0,'failed_v1_objects':0,'new_compile_invocations':0,'uninterrupted_compile_link_freeze':False,'link_returncode':code,'error':error,'link_wall_seconds_including_input_lock_hashes':time.monotonic()-started,'input_posthash_changes':changed,'freeze_sha256_before':freeze_sha,'freeze_sha256_after':freeze_after,'new_DLL_loaded':False,'metadata_exports_called':False,'model_requests':0,'target_draft_rows':0,'GPU_launches':0,'native_GPU_seconds':0,'native_budget_configure':'-6 NATIVE_BLOCKED (source/compile binding only; export not executed)','actual_loaded_modules':None,'sessions':'all145 objects freshly compiled in full-frozen v2 session, revalidated and frozen for this separate link-only continuation'}
        if dll.exists():result['DLL_path']=str(dll);result['DLL_sha256']=sha(dll);result['DLL_bytes']=dll.stat().st_size
        if (OUT/'link.log').exists():result['link_log_sha256']=sha(OUT/'link.log')
        write(OUT/'BUILD.json',result);print(json.dumps(result),flush=True)
    finally:held.release()

if __name__=='__main__':main()
