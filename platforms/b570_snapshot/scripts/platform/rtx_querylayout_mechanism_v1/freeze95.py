from common95 import *
def archive(path,files):
    index={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in sorted(files.items())}
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('INDEX.json',json.dumps(dict(files=index),ensure_ascii=False,indent=2)+'\n')
        for name,p in sorted(files.items()):z.write(p,name)
    with zipfile.ZipFile(path) as z:
        for name,a in index.items():
            b=z.read(name);assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
    return dict(bytes=Path(path).stat().st_size,sha256=sha(path),logical_files=len(index))
def split(path,prefix):
    path=Path(path);parts=[]
    with path.open('rb') as f:
        while b:=f.read(48*1024**2):
            p=PUB/(prefix+f'.part{len(parts)+1:03d}')
            with p.open('xb') as out:out.write(b)
            parts.append(dict(name=p.name,bytes=len(b),sha256=sha(p)))
    return parts
def source_package():
    files={'native/source/'+p.relative_to(LOCAL/'native/source').as_posix():p for p in (LOCAL/'native/source').rglob('*') if p.is_file()}
    files['native/bin/llama-server.exe']=LOCAL/'native/build/bin/llama-server.exe';files['native/bin/querylayout-replay.exe']=LOCAL/'native/build/bin/querylayout-replay.exe'
    files['parent/PR91_SOURCE_RUNTIME.zip']=LOCAL/'parent-restored/repository/benchmarks/rtx_evidence_closeout_v1/SOURCE_RUNTIME.zip'
    for p in (LOCAL/'native').glob('build-*.log'):files['native/'+p.name]=p
    path=LOCAL/'SOURCE_RUNTIME.zip';info=archive(path,files);parts=split(path,'SOURCE_RUNTIME')
    save(PUB/'SOURCE_RUNTIME_MANIFEST.json',dict(**info,parts=parts,format='ordered binary ZIP slices'))
def freeze(phase):
    assert phase in ['F0A','F0B'];assert not any(read(p)['phase']=='formal' for p in (LOCAL/'ledger').glob('*.json'))
    if phase=='F0A':
        assert not list((LOCAL/'runs').rglob('REQUEST_STARTED.json'))
        for name,h in read(PUB/'NATIVE_SOURCE_HASHES.json').items():assert sha(LOCAL/'native/source'/name)==h
        source_package()
    paths=[p for root in [PUB,Path(__file__).parent] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    payload={p.relative_to(REPO).as_posix():sha(p) for p in paths}
    value=dict(utc=now(),phase=phase,design_head=DESIGN_HEAD,audit_head=AUDIT_HEAD,parent_head=PARENT_HEAD,payload_sha256=payload,plan_sha256=digest(read(PUB/('P0_PLAN.json' if phase=='F0A' else 'FORMAL_PLAN.json'))),before_new_forward=True,budgets=read(PUB/'P0_PLAN.json'),native_build_sha256=sha(PUB/'NATIVE_BUILD.json'))
    save(PUB/(phase+'.json'),value);paths.append(PUB/(phase+'.json'))
    subprocess.run(['git','add','--sparse','-f','--',*[p.relative_to(REPO).as_posix() for p in paths]],cwd=REPO,check=True)
    subprocess.run(['git','commit','-m','Freeze RTX query-layout '+phase+' before new forwards'],cwd=REPO,check=True)
    retry(lambda:subprocess.run(['git','push','-u','origin',git('branch','--show-current')],cwd=REPO,check=True),'freeze-push-'+phase)
    head=git('rev-parse','HEAD');tree=api('git/trees/'+head+'?recursive=1');assert not tree.get('truncated');items={x['path']:x for x in tree['tree']};checked={}
    for p in paths:
        name=p.relative_to(REPO).as_posix();item=items[name];b=verified_blob(item['sha']);assert len(b)==p.stat().st_size and hashlib.sha256(b).hexdigest()==sha(p);checked[name]=dict(sha256=sha(p),bytes=len(b),git_blob=item['sha'])
    receipt=dict(utc=now(),phase=phase,commit=head,actual_authenticated_remote_bytes=True,before_new_forward=True,payload_sha256=payload,readback=checked)
    save(LOCAL/(phase+'_REMOTE_RECEIPT.json'),receipt)
    save(PUB/(phase+'_REMOTE_READBACK.json'),receipt);status(phase+'_REMOTE_BYTES_VERIFIED',commit=head,files=len(checked))
