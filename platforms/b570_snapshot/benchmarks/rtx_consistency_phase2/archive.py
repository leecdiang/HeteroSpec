"""Content-addressed Phase 2 archive; retains the separate immutable Phase 1 dependency."""
import hashlib,json,subprocess,time,zipfile
from base import HERE,read,save,sha

OUT=HERE.parent.parent/'outputs'

def main():
    assert read(HERE/'generated/analysis/POST_AUDIT.json')['status']=='PASS'
    bundle=HERE/'generated/FROZEN_HISTORY.bundle';assert not bundle.exists()
    subprocess.check_call(['git','bundle','create',str(bundle),'--all'],cwd=HERE)
    subprocess.check_call(['git','bundle','verify',str(bundle)],cwd=HERE)
    prior=OUT/'HeteroSpec_局部一致性实验_完整记录.zip'
    dependency={'archive':prior.name,'sha256':'4e2f990f79d80d2eb74c27ecb1f172d50cc4e0b432f180020dc78c091b7f06d6',
                'role':'Preserved Phase 1 source/binaries/history, native parser, original references and prompts. Restore separately and configure HETEROSPEC_PHASE1_ROOT and HETEROSPEC_RTX_STUDY_ROOT.'}
    assert sha(prior)==dependency['sha256']
    pairs=[]
    def add(p,name):
        assert p.is_file();pairs.append((p,name))
    for p in HERE.iterdir():
        if p.is_file():add(p,'experiment/'+p.name)
    for directory in ['runs','generated/analysis','generated/source']:
        for p in (HERE/directory).rglob('*'):
            if p.is_file():add(p,'experiment/'+p.relative_to(HERE).as_posix())
    for p in (HERE/'generated').iterdir():
        if p.is_file():add(p,'experiment/generated/'+p.name)
    for name in ['llama-cli.exe','llama-server.exe']:
        add(HERE/'generated/build/bin'/name,'experiment/current-binaries/'+name)
    for p in OUT.iterdir():
        if p.is_file() and p.name.startswith(('HeteroSpec_RTX_第二阶段','HeteroSpec_RTX_第二阶段统筹')) and p.suffix in ['.md','.csv','.png','.svg']:
            add(p,'outputs/'+p.name)
    assert len({n for _,n in pairs})==len(pairs)
    destination=OUT/'HeteroSpec_RTX_第二阶段_完整记录.zip';assert not destination.exists()
    seen={};index=[];logical=0;unique=0;started=time.time()
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        z.write(HERE/'rehydrate.py','rehydrate.py')
        for p,name in pairs:
            h=sha(p);size=p.stat().st_size;index.append({'path':name,'sha256':h,'bytes':size});logical+=size
            if h not in seen:z.write(p,'objects/'+h);seen[h]=p;unique+=size
        manifest={'schema':'heterospec-content-addressed-archive-v1','phase':'RTX-consistency-phase2-A',
                  'files':index,'logical_bytes':logical,'unique_bytes':unique,'unique_objects':len(seen),
                  'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip(),
                  'phase1_dependency':dependency,'excluded':'GGUF weights, released DLLs, build intermediates and unrelated files; identities supplied in source bindings and post audit.',
                  'restore':'python rehydrate.py ARCHIVE.zip NEW_DESTINATION; SHA256 checked, different existing files refused.'}
        z.writestr('INDEX.json',json.dumps(manifest,ensure_ascii=True,indent=2)+'\n')
        z.writestr('README.txt','Phase 2 scope qualification and matched cost raw evidence. Every run, negative output, zero-model build preparation failure, exact private source and CLI/server executable is retained.\nAll bytes are stored once by SHA256; INDEX.json maps file paths. Use rehydrate.py to restore into a new directory.\nRestore the existing Phase 1 archive separately; its immutable filename/hash and required environment paths are in INDEX.json. It is not embedded or modified.\nWeights and published DLLs are not copied; match their bound hashes. No model output/state diagnostic is a free online candidate input. B/C/D are planned, not executed.\n')
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        for h in seen:
            with z.open('objects/'+h) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
        assert json.loads(z.read('INDEX.json'))==manifest
    result={'status':'PASS','archive':str(destination),'sha256':sha(destination),'zip_bytes':destination.stat().st_size,
            'file_paths':len(index),'unique_objects':len(seen),'logical_bytes':logical,'unique_bytes':unique,
            'seconds':time.time()-started,'crc_and_all_object_sha256_verified':True,'source_head':manifest['source_head'],
            'phase1_dependency':dependency}
    save(OUT/'HeteroSpec_RTX_第二阶段_记录包校验.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
