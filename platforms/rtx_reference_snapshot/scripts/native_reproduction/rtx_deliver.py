"""Package explicit native fixtures and raw records after all timing has ended."""
import argparse,csv,datetime,gzip,hashlib,json,pathlib,shutil,zipfile
from rtx_recover import sha,read,save
P=pathlib.Path
def zip_checked(path,members,fresh):
    assert not path.exists() and not fresh.exists();fresh.mkdir(parents=True)
    manifest={}
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,p in sorted(members.items()):
            assert '..' not in P(name).parts and not P(name).is_absolute()
            manifest[name]=dict(bytes=p.stat().st_size,sha256=sha(p));z.write(p,name)
        z.writestr('MEMBERS.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(path) as z:
        for name,v in manifest.items():
            p=fresh/name;p.parent.mkdir(parents=True,exist_ok=True)
            with z.open(name) as src,p.open('xb') as dst:shutil.copyfileobj(src,dst)
            assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
    return dict(path=path.name,bytes=path.stat().st_size,sha256=sha(path),members=len(manifest),fresh_copy=str(fresh),verification='all members freshly extracted and SHA256 checked')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=P);ap.add_argument('out',type=P);a=ap.parse_args();root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    state=read(root/'formal/CHECKPOINT.json');assert state['status']=='COMPLETE'
    receipts=out/'receipts';receipts.mkdir(exist_ok=False)
    names=['RECOVERY.json','CLEAN_BUILD.json','BRIDGE_BUILD.json','bridge-build-v2-BUILD.json','PANEL.json','STAGE_ORIGIN.json','STAGE_RESULT.json','HISTORICAL_R_ENDPOINTS.json','RECORDING_AMENDMENT.json','TOOLCHAIN_SUPPLEMENT.json','POST_EXECUTION_AUTHENTICATION.json','pilot-PROCESS.json','pilot-QUALIFICATION.json','qualification-PROCESS.json','qualification-v2-PROCESS.json','qualification-v2-QUALIFICATION.json']
    for name in names:shutil.copyfile(root/name,receipts/name)
    shutil.copyfile(root/'request-smoke/RESULT.json',receipts/'REQUEST_SMOKE.json')
    shutil.copyfile(root/'formal/CHECKPOINT.json',receipts/'CHECKPOINT.json')
    for p in (root/'formal').glob('*-ADMISSION.json'):shutil.copyfile(p,receipts/p.name)
    v1=read(root/'qualification/result.json');save(receipts/'QUALIFICATION_V1_DISPOSITION.json',dict(status=v1['status'],error=v1.get('error'),requests=len(v1['requests']),original_raw_result=str(root/'qualification/result.json'),sha256=sha(root/'qualification/result.json'),formal_use=False))
    slots=[]
    for name in ('qualification','qualification-v2'):
        actual={r['slot']['slot_id']:r for r in read(root/name/'result.json')['requests']}
        for slot in read(root/'QUALIFICATION_SLOTS.json'):
            sid=slot['slot_id'];slots.append(dict(attempt=name,slot_id=sid,task=slot['task'],k=slot['k'],lifecycle=slot['lifecycle'],arm=slot['label'],status='NATIVE_COMPLETED_PRESERVED' if sid in actual else 'NOT_RUN',qualified_attempt=name=='qualification-v2',raw_record=str(root/name/(sid+'.json')) if sid in actual else ''))
    with (out/'QUALIFICATION_ATTEMPTS.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(slots[0]));w.writeheader();w.writerows(slots)
    fixture={}
    for p in (root/'stage-fixture').iterdir():fixture['stage/input/'+p.name]=p
    for arm in ('MQ','PQ','QB'):
        for p in (root/'stage-replays'/('clean-build-'+arm+'-r0')).iterdir():fixture['stage/expected/'+arm+'/'+p.name]=p
    for p in (root/'request-smoke').rglob('*'):
        if p.is_file():fixture['request/historical-smoke/'+p.relative_to(root/'request-smoke').as_posix()]=p
    q=read(root/'qualification-v2/result.json')['requests']
    for r in q:
        if r['input_id']=='GSM8K/test/443' and r['capture'] and (r['arm']=='R' or (r['k']==3 and r['lifecycle']=='fresh')):
            p=root/'qualification-v2'/(r['folder']+'.json');fixture['request/new-bridge/'+p.name]=p
    fixture['request/PANEL.json']=root/'PANEL.json';fixture['request/MODEL_CONTRACT.json']=root/'MODEL_CONTRACT.json'
    nativezip=zip_checked(out/'NATIVE_FIXTURES.zip',fixture,root.parent/'native-fixture-fresh-verification')
    compact={}
    for s in range(6):
        item=state['sessions'][str(s)];p=P(item['result']);compact['sessions/'+p.parent.name+'/result.json']=p
        for suffix in ('-PROCESS.json','.stdout.log','.stderr.log'):
            f=root/(p.parent.name+suffix);compact['sessions/'+f.name]=f
    for name in ('pilot','qualification-v2'):
        compact[name+'/result.json']=root/name/'result.json'
        compact[name+'-PROCESS.json']=root/(name+'-PROCESS.json')
    formalzip=zip_checked(out/'NATIVE_RECORDS.zip',compact,root.parent/'native-records-fresh-verification')
    inventory={};size=0
    for p in sorted(root.rglob('*')):
        if p.is_file():
            rel=p.relative_to(root).as_posix();n=p.stat().st_size;inventory[rel]=dict(bytes=n,sha256=sha(p));size+=n
    manifest=out/'RAW_FILES.json.gz';assert not manifest.exists()
    with gzip.open(manifest,'wt',encoding='utf-8') as f:json.dump(dict(root=str(root),files=inventory),f,separators=(',',':'))
    count=len(inventory);print('RAW_MANIFEST_COMPLETE',count,size,flush=True)
    models=read(root/'MODEL_CONTRACT.json')['families']['Qwen']['models']
    native_requests=6+25+len(v1['requests'])+204+936
    accounting=dict(new_model_requests=native_requests,historical_smoke_requests=6,pilot_requests=25,interrupted_v1_qualification_native_requests=len(v1['requests']),v2_qualification_requests=204,formal_requests=936,formal_measurements=864,formal_warmups=72,model_processes=15,standalone_stage_processes=12,formal_technical_retries=0,global_auxiliary_compiler_descendants='not comprehensively counted',gpu_active_seconds='not measured',timed_sample_selection='none')
    save(out/'ACCOUNTING.json',accounting)
    access=dict(status='LOCAL_RAW_COMPLETE_AND_COMPACT_ARCHIVES_FRESHLY_VERIFIED',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),raw_root=str(root),raw_files=count,raw_bytes=size,raw_manifest=dict(path=manifest.name,sha256=sha(manifest)),compact_archives=[nativezip,formalzip],models=models,models_redistributed=False,numerical_DLLs_redistributed=False,
      historical_sources=[dict(path=str(P('D:/hsc95')/name),sha256=sha(P('D:/hsc95')/name)) for name in ('SOURCE_RUNTIME.zip','SOURCE_RUNTIME_V02.zip')],
      historical_git_commit='3235d44c26edd92db33e574094c26af8e29d2452',historical_git_directory='benchmarks/rtx_querylayout_mechanism_v1',
      limits='Bulk logits/source/build outputs and interrupted attempt remain local, indexed by exact SHA256. Git-only native execution additionally needs external model weights, numerical DLLs and source capsule recovery. Compact archive verification is not remote bulk raw delivery or external scientific certification.')
    save(out/'RAW_ACCESS.json',access)
    print(json.dumps(dict(nativezip=nativezip,records=formalzip,accounting=accounting)),flush=True)
if __name__=='__main__':main()
