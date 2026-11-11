"""Content freeze, exact remote blob retrieval and offline Git membership proofs."""
import base64,hashlib,json,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from prepare import ROOT,STUDY,save,sha,now,ledger
BRANCH='experiment/rtx-trajectory-and-matched-cost-v4'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def manifest(stage,paths=None):
    if (STUDY/(stage+'_MANIFEST.json')).exists():raise RuntimeError('checkpoint manifest cannot be overwritten')
    if paths is None:
        paths=[]
        for directory in ['scripts/platform/rtx_trajectory_cost_v4','benchmarks/rtx_trajectory_cost_v4','artifacts/rtx_trajectory_sufficiency_v4','artifacts/rtx_matched_qualification_cost_v3']:
            p=ROOT/directory
            if p.exists():paths.extend(q.relative_to(ROOT).as_posix() for q in p.rglob('*') if q.is_file() and q.name!='AUTHORIZATION.json' and q.suffix not in ['.exe','.dll','.pdb','.pyc'] and '__pycache__' not in q.parts and not (q.name in ['REPORT.json','REPORT.md'] and q.parent.name in ['A_trajectory','B_matched_cost']) and not any(x in q.name for x in ['REMOTE_RECEIPT','F0_MANIFEST.json','F1_MANIFEST.json','F2_MANIFEST.json','B_START_MANIFEST.json','EXECUTION_LEDGER','A_TERMINAL','PROTOCOL_REVIEW_PACKET','CLOSEOUT','JOINT_CHRONOLOGY','EXECUTION_COUNTS','INDEPENDENT_VALIDATION']))
    files={n:{'sha256':sha(ROOT/n),'bytes':(ROOT/n).stat().st_size} for n in sorted(set(paths))}
    save(STUDY/(stage+'_MANIFEST.json'),{'checkpoint':stage,'created_utc':now(),'files':files,'identity_scope':'exact protected content; receipt child commits refer to this parent content commit; no manifest self-hash cycle'})
def receipt(stage):
    head=git('rev-parse','HEAD').decode().strip();subprocess.run(['git','push','--set-upstream','origin',BRANCH],cwd=ROOT,check=True)
    remote=git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
    if remote!=head:raise RuntimeError('remote full SHA differs')
    response=subprocess.check_output(['gh','api','-i',f'repos/leecdiang/HeteroSpec/git/commits/{head}']).decode('utf-8')
    header,body=response.split('\r\n\r\n' if '\r\n\r\n' in response else '\n\n',1);obj=json.loads(body)
    tree=json.loads(subprocess.check_output(['gh','api',f'repos/leecdiang/HeteroSpec/git/trees/{obj["tree"]["sha"]}?recursive=1']))
    if tree.get('truncated'):raise RuntimeError('remote tree truncated')
    blobs={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'}
    m=json.loads((STUDY/(stage+'_MANIFEST.json')).read_text());files=dict(m['files'])
    mn=(STUDY/(stage+'_MANIFEST.json')).relative_to(ROOT).as_posix();files[mn]={'sha256':sha(ROOT/mn),'bytes':(ROOT/mn).stat().st_size}
    snapshot=ROOT/'work/frozen-checkpoints'/stage;snapshot.mkdir(parents=True,exist_ok=False)
    def fetch(item):
        name,v=item;blob=git('rev-parse',head+':'+name).decode().strip()
        if blobs.get(name)!=blob:raise RuntimeError('remote tree/file mismatch '+name)
        b=subprocess.check_output(['gh','api',f'repos/leecdiang/HeteroSpec/git/blobs/{blob}']);o=json.loads(b)
        if o['sha']!=blob or o.get('encoding')!='base64':raise RuntimeError('remote blob transport mismatch')
        payload=base64.b64decode(o['content'])
        h=hashlib.sha256(payload).hexdigest()
        if h!=v['sha256'] or len(payload)!=v['bytes']:raise RuntimeError('remote retrieved bytes differ '+name)
        q=snapshot/'files'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(payload)
        return name,{**v,'git_blob':blob,'retrieved_utc':now()}
    with ThreadPoolExecutor(max_workers=4) as pool:retrieved=dict(pool.map(fetch,files.items()))
    archives=[]
    for name in retrieved:
        if not name.endswith('.parts.json') or not name.startswith('artifacts/'):continue
        index=json.loads((snapshot/'files'/name).read_text());h=hashlib.sha256();total=0
        for part in index['parts']:
            payload=(snapshot/'files'/part['path']).read_bytes()
            if sha(snapshot/'files'/part['path'])!=part['sha256'] or len(payload)!=part['bytes']:raise RuntimeError('remote archive part changed')
            h.update(payload);total+=len(payload)
        if h.hexdigest()!=index['sha256'] or total!=index['bytes']:raise RuntimeError('remote complete archive differs')
        archives.append({'index':name,'sha256':h.hexdigest(),'bytes':total,'fully_reconstructed_from_remote_parts':True})
    if git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]!=head:raise RuntimeError('remote changed during receipt')
    proof={'commit':head,'root_tree':obj['tree']['sha'],'trees':{}}
    (snapshot/'commit.object').write_bytes(git('cat-file','commit',head));dirs={''}
    for n in files:
        parent=Path(n).parent
        while str(parent)!='.':dirs.add(parent.as_posix());parent=parent.parent
    for d in sorted(dirs):
        h=obj['tree']['sha'] if not d else git('rev-parse',head+':'+d).decode().strip();q=snapshot/'trees'/(h+'.object');q.parent.mkdir(exist_ok=True);q.write_bytes(git('cat-file','tree',h));proof['trees'][d]=h
    save(snapshot/'GIT_MEMBERSHIP.json',proof)
    save(STUDY/(stage+'_GIT_PROOF.json'),{'commit':head,'root_tree':obj['tree']['sha'],'commit_base64':base64.b64encode((snapshot/'commit.object').read_bytes()).decode(),'trees':{d:{'sha':h,'base64':base64.b64encode((snapshot/'trees'/(h+'.object')).read_bytes()).decode()} for d,h in proof['trees'].items()},'scope':'Portable SHA1 Git object membership proof; original retrieved file bytes are the parent commit files and content-addressed packages; not proof of independent clock trust'})
    headers={}
    for line in header.splitlines():
        if ':' in line:
            k,v=line.split(':',1)
            if k.lower() in ['date','etag','x-github-request-id']:headers[k.lower()]=v.strip()
    r={'checkpoint':stage,'commit':head,'remote_ref':remote,'tree_sha':obj['tree']['sha'],'remote_ack_utc':now(),'server_headers':headers,'files':retrieved,'retrieved_files':retrieved,'full_retrieval_verified':True,'manifest_sha256':sha(STUDY/(stage+'_MANIFEST.json')),'git_membership_proof':'frozen-checkpoints/'+stage,'chronology_limit':'Git authenticates content/ancestry; server Date is response time with finite resolution. Host process/order times are retained, not a trusted timestamp service.'}
    r['remote_complete_archives']=archives
    save(STUDY/(stage+'_REMOTE_RECEIPT.json'),r)
    import verify_receipts
    verify_receipts.checkpoint(ROOT,STUDY,stage)
    ledger({'event':'remote_freeze_acknowledged','phase':stage,'content_commit':head,'retrieved_file_count':len(retrieved),'status':'VALID'});return r
