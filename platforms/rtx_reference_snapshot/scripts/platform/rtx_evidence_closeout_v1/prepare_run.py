"""Restore actual bound author archive and independently reproduce #84, no GPU forwards."""
from run_common import *
import shutil, zipfile

def main():
    LOCAL.mkdir(exist_ok=True);PUB.mkdir(parents=True,exist_ok=True)
    docs={}
    for p in sorted(DESIGN.iterdir()):
        b=p.read_bytes();v=json.loads(b) if p.suffix=='.json' else b.decode('utf-8')
        docs[p.name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'fully_read':True,'keys':list(v) if isinstance(v,dict) else None}
    assert git('rev-parse','HEAD')==DESIGN_HEAD
    closeout.validate(read(DESIGN/'DESIGN.json'))
    bindings=[]
    for a in read(DESIGN/'SOURCE_BINDINGS.json')['files']:
        b=subprocess.check_output(['git','show',a['head']+':'+a['path']],cwd=REPO)
        assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
        remote=api('git/blobs/'+a['sha']);rb=base64.b64decode(remote['content'])
        assert rb==b
        bindings.append(dict(path=a['path'],sha256=a['sha256'],git_blob=a['sha'],actual_authenticated_remote_bytes=True))
    save(PUB/'DESIGN_READ_RECEIPT.json',dict(design_head=DESIGN_HEAD,base_head=BASE_HEAD,documents=docs,source_bindings=bindings,utc=now(),forwards=0))
    source=PRIMARY/'outputs/HeteroSpec_RTX_三家族同日实验_完整记录.zip'
    manifest=read(OLDPUB/'ARCHIVE_MANIFEST.json')['private_author_archive']
    assert source.stat().st_size==manifest['bytes'] and sha(source)==manifest['sha256']
    root=LOCAL/'restored84';root.mkdir(exist_ok=False)
    with zipfile.ZipFile(source) as z:
        idx=json.loads(z.read('INDEX.json'))
        for name,a in idx['files'].items():
            p=(root/name).resolve();assert p.is_relative_to(root.resolve())
            b=z.read(name);assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    repo=root/'repository';oldlocal=root/'third-family'
    inv=read(oldlocal/'native/SOURCE_HASHES_FINAL.json')
    for name,h in inv.items(): assert sha(oldlocal/'native/source'/name)==h
    assert sha(oldlocal/'native/build/bin/llama-server.exe')==read(OLDPUB/'NATIVE_BUILD.json')['binary_sha256']
    out=root/'RESULTS_REPRODUCED.json'
    r=subprocess.run([sys.executable,str(repo/'scripts/platform/jsa_third_family_v1/analyse.py'),str(out)],capture_output=True,timeout=240)
    (root/'CPU.stdout').write_bytes(r.stdout);(root/'CPU.stderr').write_bytes(r.stderr)
    assert r.returncode==0 and sha(out)==sha(OLDPUB/'RESULTS.json')
    save(PUB/'RESTORE84.json',dict(status='PASS',utc=now(),archive_sha256=sha(source),logical_files=len(idx['files']),source_files=len(inv),server_sha256=sha(oldlocal/'native/build/bin/llama-server.exe'),independent_cpu_exit=r.returncode,reproduced_results_sha256=sha(out),forwards=0))
    assets=read(DESIGN/'ASSETS.json');rows=[]
    for f,pair in models().items():
        for role,a in pair.items():
            p=Path(a['path']);actual=sha(p);pin=assets['families'][f]['models'][role]
            assert p.stat().st_size==a['bytes']==pin['bytes'] and actual==a['sha256']==pin['sha256']
            rows.append(dict(family=f,role=role,path=str(p),bytes=p.stat().st_size,sha256=actual))
    dll=[]
    for n,h in assets['numerical_DLL_sha256'].items():
        p=Path('D:/HeteroSpec-PC/tools/llama-b10839')/n;assert sha(p)==h
        dll.append(dict(name=n,bytes=p.stat().st_size,sha256=h))
    save(PUB/'ASSET_CHECK.json',dict(status='PASS',utc=now(),models=rows,numerical_DLLs=dll,forwards=0,conversion_lineage='Publisher bytes certified; official checkpoint ancestry unverified'))
    shutil.copytree(oldlocal/'native/source',LOCAL/'native/source')
    shutil.copyfile(oldlocal/'native/vocabulary.exe',LOCAL/'native/vocabulary.exe')
    shutil.copyfile(OLDPUB/'MODEL_CONTRACT.json',PUB/'MODEL_CONTRACT.json')
    save(LOCAL/'native/BASE_SOURCE_HASHES.json',inv)
    status('SOURCE_AND_ASSETS_RESTORED',source_files=len(inv),model_files=len(rows),forwards=0)

if __name__=='__main__': main()
