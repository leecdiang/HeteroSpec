"""Incremental audit of all reachable Git and accessible host/archives, ID + description."""
from run_common import *
import ahocorasick, collections, tarfile, zipfile
import closeout
from concurrent.futures import ThreadPoolExecutor
from collections import deque

TEXT={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.py','.toml','.cpp','.h','.tex'}
SKIP={'.git','__pycache__','node_modules','vendor','third_party','models','tools','hf-cache','datasets','env','python311','pinned-source','native-build','native-source','source','c-source','x-source','build','c-build','x-build','bin','dependencies','site-packages','llm-42','static-native','restored84'}
def cpu_remote_retry(operation,label):
    deadline=datetime.fromisoformat(read(PUB/'F0A.json')['utc']).timestamp()+7*86400
    attempts=0
    while True:
        try:return operation()
        except (subprocess.CalledProcessError,OSError) as e:
            attempts+=1
            if time.time()+60>=deadline:raise
            status('CPU_HISTORY_REMOTE_RETRY',operation=label,attempt=attempts,error=repr(e),formal_forwards=0)
            time.sleep(min(60,5*attempts))

def load_git_blob(oid,name):
    # Missing text blobs use the authenticated API endpoint, with durable cache
    # and CPU-only retry, rather than another per-object Git HTTPS lazy fetch.
    env=dict(os.environ,GIT_NO_LAZY_FETCH='1')
    local=subprocess.run(['git','cat-file','blob',oid],cwd=REPO,env=env,capture_output=True)
    if local.returncode==0:return local.stdout
    blob=cpu_remote_retry(lambda:api('git/blobs/'+oid),'authenticated-text-blob:'+oid)
    assert blob['encoding']=='base64' and blob['sha']==oid
    b=base64.b64decode(blob['content']);assert len(b)==blob['size']
    assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid
    stored=subprocess.check_output(['git','hash-object','-w','--stdin'],input=b,cwd=REPO).decode().strip();assert stored==oid
    p=LOCAL/'authenticated-text-blobs'/(oid+'.json')
    if not p.exists():save(p,dict(oid=oid,path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),actual_authenticated_remote_bytes=True,utc=now()))
    return b

def reachable_text_objects(known_git):
    # Enumerate all reachable snapshots without fetching unrelated binary blobs
    # from this partial clone merely to discover their object type.
    trees=set(git('log','--all','--format=%T').splitlines());objects={}
    for tree in sorted(trees):
        raw=subprocess.check_output(['git','ls-tree','-r','-z','--full-tree',tree],cwd=REPO)
        for entry in raw.split(b'\0'):
            if not entry:continue
            metadata,name=entry.split(b'\t',1);_,kind,oid=metadata.split()
            name=name.decode('utf-8');oid=oid.decode('ascii')
            if kind==b'blob' and Path(name).suffix.lower() in TEXT and oid not in known_git:objects.setdefault(oid,name)
    save(LOCAL/'REACHABLE_TEXT_TREES.json',dict(complete_reachable_snapshot_trees=sorted(trees),additional_text_objects=objects,enumeration='all reachable commit root trees; recursive ls-tree; no binary lazy-fetch'))
    return objects

def aggregate_availability_ids(obj,coord):
    if obj.get('status')!='PASS_ACCESSIBLE_ID_AUDIT' or obj.get('confirmation_selection')!='NOT_PERFORMED':return set()
    assert coord['schema']=='heterospec.jsa.b570.coordination.v1'
    remaining=set(coord['remaining_ranked_candidates'])
    reserved=set(coord['provisional_b570_reservation'])|set(coord['rtx_reserved_ids'])
    return {i for i,paths in obj['hits'].items() if paths and i in remaining and i not in reserved and all(Path(p.replace('\\','/')).name in ['TOKENIZATION.stdout.jsonl','COORDINATION_SNAPSHOT.json'] for p in paths)}

def confirmation_pool(data,exclusions):
    counts=collections.Counter(closeout.normalized_text(t['description']) for t in data);pool=[]
    for t in data:
        if t['id'] in exclusions or (t['domain']=='MBPP' and not 11<=int(t['id'].split('/')[-1])<=510) or counts[closeout.normalized_text(t['description'])]!=1:continue
        if closeout.cohort_parity(t['domain'],t['description'])!=0:continue
        key='heterospec-final-closeout-v1|'+t['domain']+'|'+closeout.normalized_text(t['description'])
        prefix='Solve the following problem and explain your reasoning.\n\n' if t['domain']=='GSM8K' else 'Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n'
        pool.append({**t,'raw_prompt':prefix+t['description'],'selection_hash':hashlib.sha256(key.encode()).hexdigest(),'cap':128})
    return sorted(pool,key=lambda t:(t['selection_hash'],t['id']))

def seal_audited_panel(audit,reuse_static=False):
    assert audit['status']=='PASS' and audit['completed'] and not audit['errors']
    d=read(DESIGN/'DESIGN.json');mb=Path('D:/HeteroSpec-RTX-Target-V1/work/rtx-target-v1/sanitized-mbpp.json');gs=PRIMARY/'work/third-family/datasets/gsm8k-test.jsonl'
    assert sha(mb)=='ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9' and sha(gs)==d['dataset_pins']['GSM8K']['sha256']
    data=[dict(id='MBPP/'+str(t['task_id']),domain='MBPP',description=t['prompt']) for t in read(mb)]
    data += [dict(id='GSM8K/test/'+str(i),domain='GSM8K',description=json.loads(line)['question']) for i,line in enumerate(gs.read_text(encoding='utf-8').splitlines())]
    pool=confirmation_pool(data,set(audit['excluded_ids']));native=__import__('native_inputs').tokenize(pool,'confirmation-pool',reuse=reuse_static)
    valid={t['id'] for t in pool if all(0<len(next(r for r in native[f] if r['id']==t['id'])['prompt_ids'])<=768 for f in d['families'])};selected=[]
    for domain in ['MBPP','GSM8K']:
        rows=[t for t in pool if t['domain']==domain and t['id'] in valid];assert len(rows)>=12;selected+=rows[:12]
    inputs=dict(tasks=selected,families={f:[next(r for r in native[f] if r['id']==t['id']) for t in selected] for f in d['families']},history_audit={**{k:audit[k] for k in ['completed','by_id_and_description','unknown_hosts_disclosed','training_unseen_claim','excluded_ids']},'evidence_sha256':sha(PUB/'HISTORY_AUDIT.json')},forwards=0)
    save(PUB/'CONFIRMATION_INPUTS.json',inputs);save(PUB/'FORMAL_PLAN.json',closeout.schedule(d,inputs,read(PUB/'SELECTED_ORDINARY.json')))
    status('NEW_PANEL_SEALED',tasks=[t['id'] for t in selected],forwards=0)

def host_objects(roots,prior_seen):
    def paths():
        for root in roots:
            for dirname,dirs,files in os.walk('\\\\?\\'+str(root.resolve())):
                dirs[:]=[n for n in dirs if n not in SKIP and not n.startswith('.venv')]
                for name in files:
                    p=Path(dirname)/name
                    if p.suffix.lower() in TEXT or p.suffix.lower()=='.zip' or p.suffixes[-2:]==['.tar','.gz']:yield p
    def load(p):
        try:
            if p.suffix.lower() in TEXT:
                b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
                return ('reused_text',h) if h in prior_seen else ('text',b)
            return 'archive',sha(p)
        except OSError as e:return 'error',repr(e)
    # Only reads/hashes run concurrently. One ordered collector owns all
    # exclusions, descriptions, inventories and archive traversal.
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending=deque()
        for p in paths():
            pending.append((p,pool.submit(load,p)))
            if len(pending)>=4:
                q,f=pending.popleft();yield q,f.result()
        while pending:
            q,f=pending.popleft();yield q,f.result()

def main():
    prior=read(OLDPUB/'EXPOSURE_AUDIT.json');assert prior['status']=='PASS' and not prior['errors']
    catpath=LOCAL/'restored84/third-family/EXPOSURE_CATALOG.json';assert sha(catpath)==prior['catalog_sha256']
    catalog=read(catpath);seen={r['sha256'] for r in catalog};known_archive={r['sha256'] for r in prior['archive_receipts']}
    historypath=LOCAL/'restored84/third-family/GIT_HISTORY_TEXT_OBJECTS.json'
    assert sha(historypath)==prior['reachable_Git_history_supplement']['object_list_sha256']
    known_git=set(read(historypath)['blobs']);exclusions={r['id'] for r in prior['rows'] if r['exclusions']}
    d=read(DESIGN/'DESIGN.json');exclusions.update(d['mandatory_excluded_ids'])
    exclusions.update(t['id'] for t in read(OLDPUB/'CONFIRMATION_INPUTS.json')['tasks'])
    mbpath=Path('D:/HeteroSpec-RTX-Target-V1/work/rtx-target-v1/sanitized-mbpp.json')
    gspath=PRIMARY/'work/third-family/datasets/gsm8k-test.jsonl'
    assert sha(mbpath)=='ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9'
    assert sha(gspath)==d['dataset_pins']['GSM8K']['sha256']
    mbdata=read(mbpath)
    data=[dict(id='MBPP/'+str(t['task_id']),domain='MBPP',description=t['prompt']) for t in mbdata]
    data += [dict(id='GSM8K/test/'+str(i),domain='GSM8K',description=json.loads(line)['question']) for i,line in enumerate(gspath.read_text(encoding='utf-8').splitlines())]
    auto=ahocorasick.Automaton();patterns={}
    for t in data:patterns.setdefault(closeout.normalized_text(t['description']),[]).append(t['id'])
    for p,ids in patterns.items():auto.add_word(p,ids)
    auto.make_automaton();regexp=re.compile(r'\b(?:MBPP[/_\-](\d{1,4})|GSM8K/test/(\d{1,4}))\b',re.I)
    new=[];errors=[];availability=[];archives=[];matches={};counter=collections.Counter()
    coord=json.loads(load_git_blob('856a06913df1f4699aca073b9a6fbc1a4bbb2f25','docs/experiments/jsa_b570_validation_20261010/COORDINATION_SNAPSHOT.json'))
    def strings(obj):
        if isinstance(obj,str):yield obj
        elif isinstance(obj,list):
            for o in obj:yield from strings(o)
        elif isinstance(obj,dict):
            for k,v in obj.items():yield str(k);yield from strings(v)
    def scan(b,label):
        h=hashlib.sha256(b).hexdigest();counter['accessible_objects']+=1
        if h in seen:counter['prior_verified_bytes_reused']+=1;return
        seen.add(h);new.append(dict(path=label,sha256=h,bytes=len(b)))
        if h in {sha_mb,sha_gs}:availability.append(dict(path=label,sha256=h,reason='complete pinned corpus availability'));return
        try:obj=json.loads(b)
        except (ValueError,UnicodeDecodeError):obj=None
        lower=label.lower()
        if isinstance(obj,dict):
            if obj.get('status')=='PASS_ACCESSIBLE_ID_AUDIT' and isinstance(obj.get('hits'),dict):
                population=aggregate_availability_ids(obj,coord)
                availability.append(dict(path=label,sha256=h,reason='aggregate tokenization/coordination hits for verified unreserved remaining population',ids=sorted(population)))
                obj=dict(excluded_ids=sorted(set(obj['excluded_ids'])-population))
            if isinstance(obj.get('files'),dict) and all(isinstance(v,dict) and 'sha256' in v for v in obj['files'].values()):return
            if ('description_matches' in obj and 'project_records' in obj) or ('descriptions' in obj and 'identifiers' in obj):return
            if 'eligible_pool' in obj or 'eligible_ranked' in obj or ('rows' in obj and any(k in obj for k in ['selected','chosen','eligible_count','known_executed_planned'])):
                obj={k:v for k,v in obj.items() if k in ['selected','chosen','prior_mbpp_executed','known_executed_planned','engineering','formal','reservations','exclusion_reasons']}
                availability.append(dict(path=label,sha256=h,reason='population availability; selected/excluded reservations scanned'))
            if obj.get('schema')=='heterospec.jsa.b570.coordination.v1':obj={k:v for k,v in obj.items() if k!='remaining_ranked_candidates'}
            if obj.get('vocab_only') is True and obj.get('forward_calls')==0:return
            if obj.get('encoding')=='base64' and isinstance(obj.get('content'),str):
                scan(base64.b64decode(obj['content']),label+'!decoded');return
        if isinstance(obj,list) and len(obj)==len(mbdata) and all(isinstance(o,dict) and 'task_id' in o and 'prompt' in o for o in obj):
            if {o['task_id']:o['prompt'] for o in obj}=={o['task_id']:o['prompt'] for o in mbdata}:return
        text=b.decode('utf-8',errors='replace') if obj is None else '\n'.join(strings(obj))
        ids={'MBPP/'+m.group(1) if m.group(1) else 'GSM8K/test/'+m.group(2) for m in regexp.finditer(text)}
        for _,found in auto.iter(closeout.normalized_text(text)):ids.update(found)
        for i in ids:
            exclusions.add(i);matches.setdefault(i,[])
            if len(matches[i])<8:matches[i].append(dict(path=label,sha256=h))
    sha_mb=sha(mbpath);sha_gs=sha(gspath)
    pulls=cpu_remote_retry(lambda:api('pulls?state=all&per_page=100'),'pull-heads');assert len(pulls)>=89 and len(pulls)<100
    assert next(p['head']['sha'] for p in pulls if p['number']==89)==DESIGN_HEAD,'design changed, stop instead of executing stale design'
    save(LOCAL/'AUDIT_PULL_HEADS.json',[dict(number=p['number'],head=p['head']['sha'],base=p['base']['sha']) for p in pulls])
    cpu_remote_retry(lambda:subprocess.run(['git','-c','gc.auto=0','-c','maintenance.auto=false','fetch','origin',*[f'refs/pull/{p["number"]}/head:refs/closeout-audit/pr-{p["number"]}' for p in pulls]],cwd=REPO,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL),'complete-pull-head-fetch')
    assert git('rev-parse','--is-shallow-repository')=='false','complete reachable history required'
    newobjects=reachable_text_objects(known_git)
    for oid,name in newobjects.items():
        scan(load_git_blob(oid,name),'gitblob:'+oid+':'+name)
    roots=[Path('C:/Users/ASUS/Documents/Codex'),Path('D:/HeteroSpec-PC'),Path('D:/HeteroSpec-RTX-Target-V1'),LOCAL]
    progress=time.monotonic();host_count=0
    for p,(kind,payload) in host_objects(roots,frozenset(seen)):
        label=str(p)[4:];host_count+=1
        if time.monotonic()-progress>=15:
            status('CPU_HISTORY_LOCAL_SCAN',host_files=host_count,logical_objects=counter['accessible_objects'],errors=len(errors),formal_forwards=0);progress=time.monotonic()
        try:
            if kind=='error':errors.append(dict(path=label,error=payload));continue
            if kind=='reused_text':counter['accessible_objects']+=1;counter['prior_verified_bytes_reused']+=1;continue
            if kind=='text':scan(payload,label)
            elif p.suffix.lower()=='.zip':
                h=payload
                if h in known_archive:archives.append(dict(path=label,sha256=h,prior_verified_logical_objects_reused=True));continue
                known_archive.add(h)
                if not zipfile.is_zipfile(p):
                    b=p.read_bytes();text=b.decode('utf-8')
                    if b.startswith(b'PK') or not text.isprintable():raise zipfile.BadZipFile('invalid binary archive')
                    scan(b,label+'!actual-plain-text');availability.append(dict(path=label,sha256=h,reason='actual printable UTF8 text with .zip suffix'));continue
                with zipfile.ZipFile(p) as z:
                    for n in z.namelist():
                        q=Path(n)
                        if q.suffix.lower() in TEXT and not any(part in SKIP for part in q.parts):scan(z.read(n),label+'!'+n)
                archives.append(dict(path=label,sha256=h))
            else:
                h=payload
                if h in known_archive:archives.append(dict(path=label,sha256=h,prior_verified_logical_objects_reused=True));continue
                with tarfile.open(p,'r:gz') as z:
                    for m in z:
                        if m.isfile() and Path(m.name).suffix.lower() in TEXT:scan(z.extractfile(m).read(),label+'!'+m.name)
                archives.append(dict(path=label,sha256=h));known_archive.add(h)
        except (OSError,ValueError,EOFError,zipfile.BadZipFile,tarfile.TarError) as e:errors.append(dict(path=label,error=repr(e)))
    save(LOCAL/'HISTORY_NEW_OBJECTS.json',new)
    pool=confirmation_pool(data,exclusions);domaincounts=collections.Counter(t['domain'] for t in pool)
    audit=dict(status='PASS' if not errors and all(domaincounts[x]>=12 for x in ['MBPP','GSM8K']) else 'INPUT_POOL_BLOCKED',utc=now(),completed=not errors,by_id_and_description=True,unknown_hosts_disclosed=True,training_unseen_claim=False,excluded_ids=sorted(exclusions),prior_audit_sha256=sha(OLDPUB/'EXPOSURE_AUDIT.json'),prior_catalog_sha256=sha(catpath),prior_reachable_history_sha256=sha(historypath),prior_verified_git_objects=len(known_git),additional_reachable_text_objects=len(newobjects),pull_heads=len(pulls),host_roots=list(map(str,roots)),counts=dict(counter),new_object_inventory_sha256=sha(LOCAL/'HISTORY_NEW_OBJECTS.json'),matches=matches,archives=archives,availability=availability,errors=errors,eligible_counts=dict(domaincounts),unknown_history='Other private hosts, unreachable force-pushed states and pretraining corpora unavailable')
    save(PUB/'HISTORY_AUDIT.json',audit);assert audit['status']=='PASS','complete host/history audit or input pool blocked'
    seal_audited_panel(audit)

if __name__=='__main__': main()
