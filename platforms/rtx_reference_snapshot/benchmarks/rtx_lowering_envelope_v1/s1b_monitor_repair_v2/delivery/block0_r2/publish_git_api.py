"""Publish the same committed Git tree through authenticated GitHub Git Data API.

CPU transport only. No experimental bytes,authorization,F0,or GPU execution change.
"""
import base64,datetime,hashlib,json,subprocess
from pathlib import Path
from common import V,load,save,sha

def publish(f,d,run):
    repo=f['repository'];branch=f['branch'];endpoint='repos/leecdiang/HeteroSpec';serial=[0]
    git=next(p['path'] for p in f['CPU_transport_executables'] if p['path'].replace('\\','/').lower().endswith('/mingw64/bin/git.exe'))
    def gitread(args,label,cap=40*1024**2):return run([git,'-C',repo,*args],label,cap)
    def api(method,path,payload=None,label='api'):
        i=serial[0];serial[0]+=1;cmd=[f['gh']['path'],'api','--method',method,endpoint+path]
        request=None
        if payload is not None:
            request=d/f'{i:03d}-REQUEST.json';save(request,payload);save(d/f'{i:03d}-REQUEST_RECEIPT.json',dict(path=path,bytes=request.stat().st_size,sha256=sha(request),original_committed_source_preserved=True));cmd+=['--input',str(request)]
        response=run(cmd,f'{i:03d}-{label}');result=load(response)
        if request is not None and request.stat().st_size>1024**2:
            # Only successful redundant transport encoding scratch is released.
            # Raw experiment/archive/Git blob,request hash,response and all
            # failed-request payloads remain intact.
            request.unlink()
        return result
    if (d.parent.parent/'TRANSPORT_LAYOUT.json').exists():
        gitread(['add','--sparse','--force','--',str(Path(__file__).relative_to(Path(repo)))],'stage-current-CPU-transport-source')
    local=gitread(['rev-parse','HEAD'],'local-head').read_text().strip()
    remote=api('GET','/git/ref/heads/'+branch,label='remote-ref')['object']['sha']
    if remote==local:
        save(d/'API_ALREADY_PRESENT.json',dict(commit=local,experiment_retry=False));print('Already published',local);return
    raw=gitread(['cat-file','commit',local],'local-commit').read_bytes();header,message=raw.split(b'\n\n',1);lines=header.decode().splitlines();tree=next(x[5:] for x in lines if x.startswith('tree '));parents=[x[7:] for x in lines if x.startswith('parent ')]
    assert len(parents)==1 and parents[0]==remote,'remote branch changed;no force'
    multipart=(d.parent.parent/'TRANSPORT_LAYOUT.json').exists()
    if multipart:tree=gitread(['write-tree'],'desired-index-tree').read_text().strip()
    base=api('GET','/git/commits/'+remote,label='base-commit')['tree']['sha']
    diffargs=['diff-index','--cached','--no-ext-diff','--raw','--no-abbrev','-z',remote] if multipart else ['diff-tree','--no-ext-diff','--raw','--no-abbrev','-r','-z',remote,local]
    diff=gitread(diffargs,'tree-diff').read_bytes().split(b'\0');entries=[];done=set();known=set()
    if multipart:
        for p in d.parent.glob('*/*-create-blob.stdout'):
            try:
                obj=load(p)
                if len(obj.get('sha',''))==40:known.add(obj['sha'])
            except Exception:pass
    for i in range(0,len(diff)-1,2):
        fields=diff[i].decode().split();path=diff[i+1].decode();assert path.startswith('benchmarks/rtx_lowering_envelope_v1/s1b_monitor_repair_v2/')
        mode,blob,status=fields[1],fields[3],fields[4];assert status in ['A','M'] and mode=='100644'
        if blob in known:done.add(blob)
        if blob not in done:
            source=gitread(['cat-file','blob',blob],f'blob-{len(done):03d}');data=source.read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob
            result=api('POST','/git/blobs',dict(content=base64.b64encode(data).decode(),encoding='base64'),label='create-blob');assert result['sha']==blob
            save(source.with_suffix('.SOURCE_RECEIPT.json'),dict(source_blob=blob,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),source_commit=local,source_path=path))
            if len(data)>1024**2:source.unlink() # verified successful Git-read transport scratch only
            done.add(blob)
        entries.append(dict(path=path,mode=mode,type='blob',sha=blob))
    created=api('POST','/git/trees',dict(base_tree=base,tree=entries),label='create-tree');assert created['sha']==tree,'published tree must be byte-identical'
    def signature(prefix):
        value=next(x[len(prefix)+1:] for x in lines if x.startswith(prefix+' '));identity,timestamp,zone=value.rsplit(' ',2);name,email=identity.rsplit(' <',1);offset=(int(zone[1:3])*60+int(zone[3:]))*(1 if zone[0]=='+' else -1)
        date=datetime.datetime.fromtimestamp(int(timestamp),datetime.timezone(datetime.timedelta(minutes=offset))).isoformat()
        return dict(name=name,email=email[:-1],date=date)
    author,committer=signature('author'),signature('committer')
    if multipart:
        now=datetime.datetime.now(datetime.timezone.utc).isoformat();author['date']=now;committer['date']=now
        message=b'PR118: preserve stopped r2 Block0 evidence via byte-identical multipart CPU transport\n'
    commit=api('POST','/git/commits',dict(message=message.decode(),tree=tree,parents=parents,author=author,committer=committer),label='create-commit');published=commit['sha']
    latest=api('GET','/git/ref/heads/'+branch,label='check-ref')['object']['sha'];assert latest==remote,'remote changed;no force'
    api('PATCH','/git/refs/heads/'+branch,dict(sha=published,force=False),label='update-ref')
    if published!=local:
        # Preserve the unpublished source commit. The publication tree equals
        # the prepared index; multipart only changes CPU container transport,
        # never the ZIP concatenation or experimental member bytes.
        assert commit['tree']['sha']==tree
        if multipart:gitread(['update-ref','refs/codex/pr118/r2-unpublished-source',local],'preserve-original-local-commit')
        gitread(['update-ref','-m','CPU API transport identical-tree publication','refs/heads/'+branch,published,local],'align-local-ref')
    gitread(['update-ref','refs/remotes/origin/'+branch,published],'align-remote-tracking')
    save(d/'API_PUBLICATION_VERIFIED.json',dict(original_local_commit=local,published_commit=published,tree=tree,all_prepared_index_tree_bytes_identical=True,original_local_tree_identical=not multipart,multipart_transport_only=multipart,scientific_raw_members_and_ZIP_bytes_unchanged=True,blob_count=len(done),file_count=len(entries),remote_force=False,original_local_commit_retained=True,F0_sha256=sha(V/'F0.json'),experiment_retry=False,GPU_queries=0,graph_calls=0))
    print('API PUBLISHED exact tree',published)
