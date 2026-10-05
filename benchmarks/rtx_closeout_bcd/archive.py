"""New immutable content-addressed delivery, independently verified in full."""
import hashlib,subprocess,time,zipfile
from close_base import HERE,PHASE2,OLDROOT,read,save,sha

OUT=HERE.parent.parent/'outputs'

def main():
    assert read(HERE/'generated/POST_AUDIT.json')['status']=='PASS'
    bundle=HERE/'generated/FROZEN_HISTORY.bundle';assert not bundle.exists()
    subprocess.check_call(['git','bundle','create',str(bundle),'--all'],cwd=HERE);subprocess.check_call(['git','bundle','verify',str(bundle)],cwd=HERE)
    deps=[{'archive':'HeteroSpec_局部一致性实验_完整记录.zip','sha256':'4e2f990f79d80d2eb74c27ecb1f172d50cc4e0b432f180020dc78c091b7f06d6'},
          {'archive':'HeteroSpec_RTX_第二阶段_完整记录.zip','sha256':'cd57ec99359b35ce201cf7c1b19979a46e05af3d03740e3cc2a753d596ca2b3d'}]
    for x in deps:assert sha(OUT/x['archive'])==x['sha256']
    pairs=[]
    for p in HERE.iterdir():
        if p.is_file():pairs.append((p,'experiment/'+p.name))
    for directory in ['runs','generated/c-source']+(['generated/x-source'] if (HERE/'generated/x-source').exists() else []):
        for p in (HERE/directory).rglob('*'):
            if p.is_file():pairs.append((p,'experiment/'+p.relative_to(HERE).as_posix()))
    for p in (HERE/'generated').rglob('*'):
        if p.is_file() and all('/'+d+'/' not in p.as_posix() for d in ['c-source','c-build','x-source','x-build']) and not p.name.startswith('PUBLISH_'):
            pairs.append((p,'experiment/'+p.relative_to(HERE).as_posix()))
    for n in ['llama-cli.exe','llama-server.exe']:pairs.append((HERE/'generated/c-build/bin'/n,'experiment/current-binaries/'+n))
    if (HERE/'generated/x-build/bin/llama-server.exe').exists():
        for n in ['llama-cli','llama-server']:pairs.append((HERE/'generated/x-build/bin'/(n+'.exe'),'experiment/current-binaries/'+n+'-cross.exe'))
    corpus=OLDROOT/'work/rtx-target-v1/sanitized-mbpp.json';assert sha(corpus)==read(HERE/'EXPOSURE_LEDGER.json')['dataset']['sha256']
    pairs.append((corpus,'experiment/frozen-corpus/sanitized-mbpp.json'))
    for p in OUT.iterdir():
        if p.is_file() and p.name.startswith('HeteroSpec_RTX_闭环') and p.suffix in ['.md','.csv','.png','.svg']:pairs.append((p,'outputs/'+p.name))
    assert len({name for _,name in pairs})==len(pairs)
    destination=OUT/'HeteroSpec_RTX_闭环_完整记录.zip';assert not destination.exists();index=[];seen={};logical=0;unique=0;started=time.time()
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        z.write(PHASE2/'rehydrate.py','rehydrate.py')
        for p,name in pairs:
            h=sha(p);size=p.stat().st_size;index.append({'path':name,'sha256':h,'bytes':size});logical+=size
            if h not in seen:z.write(p,'objects/'+h);seen[h]=p;unique+=size
        manifest={'schema':'heterospec-content-addressed-archive-v1','phase':'RTX-closeout-B-C-D','files':index,'logical_bytes':logical,'unique_bytes':unique,'unique_objects':len(seen),
                  'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip(),'dependencies':deps,
                  'excluded':'Model weights, released DLLs, C build intermediates and unrelated files. Bound identities and source/build commands are retained.',
                  'restore':'python rehydrate.py ARCHIVE.zip NEW_DESTINATION; configure prior phase roots separately. Private executable identities are bound by C_BUILD_IDENTITY.json.'}
        z.writestr('INDEX.json',__import__('json').dumps(manifest,indent=2)+'\n')
        z.writestr('README.txt','RTX B/C/D finite closeout. Full raw outputs, all failed boundaries and diagnostic attempts, source snapshots, build evidence, zero-forward exposure audit and frozen Git history are retained.\nEarlier archives remain separate immutable dependencies and are SHA256-verified. No universal/cross-platform/functional-accuracy claim follows from this panel.\n')
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        for h in seen:
            with z.open('objects/'+h) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
        assert __import__('json').loads(z.read('INDEX.json'))==manifest
    result={'status':'PASS','archive':str(destination),'sha256':sha(destination),'zip_bytes':destination.stat().st_size,'file_paths':len(index),'unique_objects':len(seen),
            'logical_bytes':logical,'unique_bytes':unique,'crc_and_all_object_sha256_verified':True,'source_head':manifest['source_head'],'dependencies':deps,'seconds':time.time()-started}
    save(OUT/'HeteroSpec_RTX_闭环_记录包校验.json',result);print(result,flush=True)

if __name__=='__main__':main()
