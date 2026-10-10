"""Bounded scientific raw CAS plus private author source/build archive."""
import zipfile,shutil,uuid
from common import *
from rehydrate import restore
OUTPUTS=REPO.parent.parent/'outputs'

def add_records(mapping):
    for p in (LOCAL/'runs').rglob('*'):
        if p.is_file() and p.suffix in ['.json','.jsonl','.state']:
            if p.suffix=='.state' and 'F_natural' in p.parts:continue
            mapping['jsa/'+p.relative_to(LOCAL).as_posix()]=p
    for name in ['S_SLOTS.json','S_REMOTE_RECEIPT.json','OFFLINE_BRIDGE_REFERENCES.json','Qwen_SLOTS.json','Qwen_REMOTE_RECEIPT.json','SmolLM2_SLOTS.json','SmolLM2_REMOTE_RECEIPT.json','F_E_ENGINEERING_REMOTE_RECEIPT.json','FREEZE_HISTORY.json']:
        p=LOCAL/name
        if p.exists():mapping['jsa/'+name]=p

def make_zip(path,mapping,classification):
    entries=[];objects=set()
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for name,p in sorted(mapping.items()):
            h=sha(p);entries.append({'path':name,'sha256':h,'bytes':p.stat().st_size,'classification':classification})
            if h not in objects:z.write(p,'objects/'+h);objects.add(h)
        index={'schema':'heterospec.jsa.cas.v1','files':entries,'weights_and_release_DLLs':'excluded; dependency revision/file hashes in ASSET_CHECK/NATIVE_BUILD','bulk_logs':'excluded from bounded scientific archive; full author archive retains local logs','no_credentials':True}
        z.writestr('INDEX.json',json.dumps(index,indent=2)+'\n');z.write(Path(__file__).parent/'rehydrate.py','rehydrate.py')
    return {'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'files':len(entries),'unique_objects':len(objects)}

def main():
    OUTPUTS.mkdir(exist_ok=True);mapping={}
    for base in [PUB,Path(__file__).parent]:
        for p in base.rglob('*'):
            if p.is_file() and p.suffix in ['.json','.md','.csv','.py','.cpp'] and '__pycache__' not in p.parts and p.name not in ['EVIDENCE_MANIFEST.json','HASHES.json','RESTORE_CHECK.json','REMOTE_READBACK.json']:
                mapping['repository/'+p.relative_to(REPO).as_posix()]=p
    add_records(mapping)
    raw=make_zip(PUB/'RAW_EVIDENCE.zip',mapping,'bounded scientific raw arrays/timing/native shapes/selected state proofs/input contracts and independent verification source')
    assert raw['bytes']<50*1024**2,'bounded raw archive exceeds declared50MiB; do not silently exclude evidence'
    private=dict(mapping)
    for p in LOCAL.rglob('*'):
        if not p.is_file() or any(n in p.parts for n in ['models','runtime','build','__pycache__']):continue
        if p.suffix in ['.json','.jsonl','.md','.log','.py','.cpp','.h','.hpp','.c','.cmake','.txt','.sh','.bat','.ps1','.f32','.state','.kv'] or p.name in ['CMakeLists.txt']:
            private['jsa/'+p.relative_to(LOCAL).as_posix()]=p
    for p in (LOCAL/'native/source').rglob('*'):
        if p.is_file() and '.git' not in p.parts and p.suffix!='.gguf':private['jsa/'+p.relative_to(LOCAL).as_posix()]=p
    for rel in ['native/build/bin/llama-cli.exe','native/build/bin/llama-server.exe','native/build/bin/jsa-dvr-server.exe','native/vocabulary.exe','runtime/S/llama-cli.exe','runtime/S/llama-server.exe']:
        p=LOCAL/rel
        if p.exists():private['jsa/'+rel]=p
    # Official tokenizer/config/conversion receipts and zero-forward records;
    # no weights, entire downloaded dataset or cache is redistributed.
    for p in (LOCAL/'models').glob('*'):
        if p.suffix in ['.json','.jsonl','.log']:private['jsa/'+p.relative_to(LOCAL).as_posix()]=p
    full=make_zip(OUTPUTS/'HeteroSpec_RTX_同日补充实验_完整记录.zip',private,'private author evidence/source/build; weights, release DLLs and credentials excluded')
    receipt={'bounded_raw':raw,'author_archive':full,'Git_data_scope':'One explicitly bounded scientific CAS archive; no loose bulk runs/logs, weights, published DLLs or build products in Git','raw_url':'https://github.com/leecdiang/HeteroSpec/blob/experiment/jsa-rtx-validation-20261010/benchmarks/jsa_rtx_validation_v1/RAW_EVIDENCE.zip','archive_runtime_dependency':'Exact33 published DLLs in ASSET_CHECK; CUDA numerical libraries unchanged; rebind author-local runtime paths before optional GPU rerun','author_access':str(OUTPUTS)}
    save(PUB/'EVIDENCE_MANIFEST.json',receipt)
    target=REPO.parent/('restored-jsa-'+uuid.uuid4().hex[:8]);restored=restore(full['path'],target);py=read(LOCAL/'CONFIG.json')['python'];script=target/'repository/scripts/platform/jsa_rtx_validation_v1';env=dict(os.environ,JSA_LOCAL_ROOT=str(target/'jsa'));checks=[]
    for name,args in [('verify_s.py',[])]+[('verify_confirmation.py',[m]) for m in ['Qwen','SmolLM2'] if (PUB/(m+'_F0.json')).exists()]:
        # NumPy is required for the paired task bootstrap.
        executable=str(Path(read(LOCAL/'CONFIG.json')['asset'])/'.venv-analysis/Scripts/python.exe')
        r=subprocess.run([executable,str(script/name)]+args,env=env,capture_output=True,text=True);checks.append({'verifier':name,'args':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});assert r.returncode==0
    for p in (target/'repository/benchmarks/jsa_rtx_validation_v1').glob('*QUALIFICATION.json'):
        original=PUB/p.name
        if original.exists():assert sha(p)==sha(original),'restored verifier changed authority '+p.name
    save(PUB/'RESTORE_CHECK.json',{'status':'PASS','private_archive':full,'restored_root':str(target),'restored_objects':restored,'CPU_checks':checks,'all_qualification_bytes_equal':True});print(json.dumps({'raw_MiB':raw['bytes']/1024**2,'full_MiB':full['bytes']/1024**2,'restore':'PASS'}),flush=True)
if __name__=='__main__':main()
