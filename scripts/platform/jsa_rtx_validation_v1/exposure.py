"""Conservative host/PR/archive exposure audit before any F discovery forward."""
import collections,re,zipfile,tarfile
from common import *
TEXT={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.py','.toml','.cpp','.h','.tex'}
SKIP={'.git','__pycache__','node_modules','vendor','third_party','models','tools','hf-cache','datasets','env','python311','pinned-source','native-build','native-source','source','c-source','x-source','build','c-build','x-build','bin','dependencies','site-packages','llm-42'}
def main():
    assert not (PUB/'CONFIRMATION_INPUTS.json').exists()
    corpus=Path('D:/HeteroSpec-RTX-Target-V1/work/rtx-target-v1/sanitized-mbpp.json');expected='ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9';assert sha(corpus)==expected
    data=read(corpus);patterns={}
    for r in data:
        for b in [r['prompt'].encode(),json.dumps(r['prompt'],ensure_ascii=True)[1:-1].encode()]:patterns.setdefault(b,set()).add(r['task_id'])
    descriptions=re.compile(b'|'.join(re.escape(b) for b in sorted(patterns,key=len,reverse=True)));ids=re.compile(rb'\bMBPP[/_\-](\d{1,4})\b',re.I)
    seen=set();matches={};catalog=[];errors=[];archive_receipts=[];roots=[];commits={};last=time.monotonic();availability=[];archive_seen=set()
    def scan(b,label):
        nonlocal last
        h=hashlib.sha256(b).hexdigest();catalog.append({'path':label,'sha256':h,'bytes':len(b)})
        if time.monotonic()-last>20:
            save(LOCAL/'EXPOSURE_CHECKPOINT.json',{'matches':matches,'errors':errors,'catalog_records':len(catalog),'unique':len(seen),'last_path':label})
            print('AUDIT',len(catalog),'unique',len(seen),'excluded_ids',len(matches),'path',label,flush=True);last=time.monotonic()
        if h==expected or h in seen:return
        seen.add(h)
        if b'"vocab_only": true' in b and b'"forward_calls": 0' in b and not any(k in b for k in [b'original_reference_ids',b'predicted_ms',b'generated_ids']):return
        if re.search(r'part-\d+-attempt-\d+\.response\.json$',label) and re.search(rb'"encoding"\s*:\s*"base64"',b):
            availability.append({'path':label,'sha256':h,'classification':'base64 transport response; decoded archive logical objects audited independently'});return
        # Previous exposure audits list entire eligible pools; that is availability,
        # not 427 model executions. Retain their exclusions and selected cohorts.
        label_lower=label.lower()
        if 'exposure' in label_lower or b'"eligible_ranked"' in b or b'"eligible_pool"' in b:
            try:a=json.loads(b)
            except (ValueError,UnicodeDecodeError):a=None
            if isinstance(a,dict) and ('eligible_ranked' in a or 'eligible_pool' in a or ('rows' in a and 'selected' in a)):
                keep={k:v for k,v in a.items() if k in ['selected','prior_mbpp_executed','engineering','formal','exclusion_reasons']}
                keep['excluded_rows']=[r for r in a.get('rows',[]) if r.get('exclusions') or r.get('excluded') or r.get('status') in ['EXECUTED_OR_INSPECTED','UNKNOWN']]
                availability.append({'path':label,'sha256':h,'classification':'exposure population/availability ledger; only selected or excluded/unknown rows scanned'})
                b=json.dumps(keep).encode()
            elif isinstance(a,dict) and ('descriptions' in a and 'identifiers' in a or 'description_matches' in a and 'project_records' in a or all(isinstance(v,dict) and 'sha256' in v and 'bytes' in v for v in a.values())):
                # Catalogs and match maps are audit indexes. Their source objects
                # are scanned independently and their ledger exclusions above apply.
                availability.append({'path':label,'sha256':h,'classification':'audit index; underlying source objects and ledger exclusions scanned separately'});return
        try:a=json.loads(b)
        except (ValueError,UnicodeDecodeError):a=None
        if isinstance(a,list) and a==data:
            availability.append({'path':label,'sha256':h,'classification':'semantically identical official downloaded corpus; no forward record'});return
        if isinstance(a,dict) and isinstance(a.get('files'),dict) and all(isinstance(v,dict) and 'sha256' in v for v in a['files'].values()):
            availability.append({'path':label,'sha256':h,'classification':'CAS logical-file index; actual science objects scanned independently'});return
        hits=set(int(m.group(1)) for m in ids.finditer(b))
        if b'Write' in b or b'write' in b:
            for m in descriptions.finditer(b):hits.update(patterns[m.group(0)])
        new_hits=hits-set(matches)
        if len(new_hits)>50:print('BROAD_NEW_MATCH',label,len(new_hits),'keys',list(a)[:12] if isinstance(a,dict) else type(a).__name__,flush=True)
        for tid in hits:
            a=matches.setdefault(tid,{'count':0,'examples':[]});a['count']+=1
            if len(a['examples'])<8:a['examples'].append({'path':label,'sha256':h})
        if time.monotonic()-last>20:print('AUDIT',len(catalog),'unique',len(seen),'excluded_ids',len(matches),flush=True);last=time.monotonic()
    # All pull heads are read explicitly, including merged or deleted branches.
    prs=json.loads(subprocess.check_output(['gh','pr','list','--repo','leecdiang/HeteroSpec','--state','all','--limit','100','--json','number,headRefOid'],text=True))
    fetch=['git','fetch','origin']+[f'refs/pull/{p["number"]}/head:refs/audit/pr-{p["number"]}' for p in prs]
    subprocess.run(fetch,cwd=REPO,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    refs=subprocess.check_output(['git','for-each-ref','--format=%(refname) %(objectname)','refs/remotes/origin','refs/audit'],cwd=REPO,text=True).splitlines()
    blobs={}
    for line in refs:
        ref,commit=line.split();commits[ref]=commit
        if commit in commits.values() and any(v==commit for k,v in list(commits.items())[:-1]):continue
        tree=subprocess.check_output(['git','ls-tree','-rz',commit],cwd=REPO)
        for entry in tree.split(b'\0'):
            if not entry:continue
            meta,p=entry.split(b'\t',1);mode,kind,oid=meta.split();name=p.decode()
            if kind==b'blob' and Path(name).suffix.lower() in TEXT:blobs.setdefault(oid.decode(),'git:'+commit+':'+name)
    # Download small scientific blobs in one refetch instead of many network round trips.
    subprocess.run(['git','fetch','origin','--refetch','--filter=blob:limit=2m'],cwd=REPO,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    proc=subprocess.Popen(['git','cat-file','--batch'],cwd=REPO,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for oid,label in blobs.items():
        proc.stdin.write((oid+'\n').encode());proc.stdin.flush();header=proc.stdout.readline().split()
        assert header[0].decode()==oid and len(header)==3
        b=proc.stdout.read(int(header[2]));assert proc.stdout.read(1)==b'\n';scan(b,label)
    proc.stdin.close();assert proc.wait()==0
    for root in [Path('C:/Users/ASUS/Documents/Codex'),Path('D:/HeteroSpec-PC'),Path('D:/HeteroSpec-RTX-Target-V1')]:
        roots.append(str(root))
        for d,dirs,files in os.walk(root):
            dirs[:]=[n for n in dirs if n not in SKIP and not n.startswith('.venv')]
            for name in files:
                p=Path(d)/name
                try:
                    if p.suffix.lower() in TEXT:scan(p.read_bytes(),str(p))
                    elif p.suffix.lower()=='.zip':
                        archive_h=sha(p)
                        if archive_h in archive_seen:archive_receipts.append({'path':str(p),'sha256':archive_h,'classification':'byte-identical previously scanned archive'});continue
                        archive_seen.add(archive_h)
                        with zipfile.ZipFile(p) as z:
                            count=0
                            index=json.loads(z.read('INDEX.json')) if 'INDEX.json' in z.namelist() else {}
                            if isinstance(index,dict) and isinstance(index.get('files'),list):
                                for e in index['files']:
                                    logical=Path(e['path'])
                                    if logical.suffix.lower() not in TEXT or any(part in SKIP for part in logical.parts):continue
                                    b=z.read('objects/'+e['sha256']);assert hashlib.sha256(b).hexdigest()==e['sha256'];scan(b,str(p)+'!'+e['path']);count+=1
                            else:
                                for name in z.namelist():
                                    logical=Path(name)
                                    if logical.suffix.lower() in TEXT and not any(part in SKIP for part in logical.parts):scan(z.read(name),str(p)+'!'+name);count+=1
                                    elif name.startswith('objects/') and z.getinfo(name).file_size<50*1024**2:
                                        with z.open(name) as member:first=member.read(1)
                                        if first in [b'{',b'[']:scan(z.read(name),str(p)+'!'+name);count+=1
                            if count:archive_receipts.append({'path':str(p),'sha256':archive_h,'text_members':count})
                    elif p.suffixes[-2:]==['.tar','.gz']:
                        archive_h=sha(p)
                        if archive_h in archive_seen:archive_receipts.append({'path':str(p),'sha256':archive_h,'classification':'byte-identical previously scanned archive'});continue
                        # A previously failed readback is a byte-for-byte prefix of
                        # the complete archive, which is scanned; it adds no object.
                        complete=Path('D:/HeteroSpec-RTX-Target-V1/work/rtx-target-v1/archive/raw-cas-v1.tar.gz')
                        if p.name=='raw-cas-v1.tar.gz' and p!=complete and p.stat().st_size<complete.stat().st_size:
                            with complete.open('rb') as f:prefix=hashlib.sha256(f.read(p.stat().st_size)).hexdigest()
                            if prefix==archive_h:
                                archive_receipts.append({'path':str(p),'sha256':archive_h,'classification':'truncated download prefix; byte-verified complete canonical archive audited','complete_path':str(complete),'complete_sha256':sha(complete)});continue
                        archive_seen.add(archive_h)
                        with tarfile.open(p,'r:gz') as z:
                            count=0;logical_by_hash={}
                            for member in z:
                                logical=Path(member.name)
                                if not member.isfile():continue
                                if logical.name in ['MANIFEST.json','INDEX.json']:
                                    raw=z.extractfile(member).read();index=json.loads(raw);entries=index.get('files',{})
                                    if isinstance(entries,dict):
                                        for name,e in entries.items():
                                            name_path=Path(name)
                                            if name_path.suffix.lower() in TEXT and not any(part in SKIP for part in name_path.parts):logical_by_hash.setdefault(e['sha256'],[]).append(name)
                                        availability.append({'path':str(p)+'!'+member.name,'sha256':hashlib.sha256(raw).hexdigest(),'classification':'CAS index resolved to logical objects'});continue
                                if logical.name in logical_by_hash:
                                    b=z.extractfile(member).read();assert hashlib.sha256(b).hexdigest()==logical.name
                                    for name in logical_by_hash[logical.name]:scan(b,str(p)+'!'+name);count+=1
                                elif logical.suffix.lower() in TEXT and not any(part in SKIP for part in logical.parts):scan(z.extractfile(member).read(),str(p)+'!'+member.name);count+=1
                            if count:archive_receipts.append({'path':str(p),'sha256':archive_h,'text_members':count})
                except (OSError,ValueError,EOFError,zipfile.BadZipFile,tarfile.TarError) as e:errors.append({'path':str(p),'error':repr(e)})
    counts=collections.Counter(r['task_id'] for r in data);texts=collections.Counter(r['prompt'] for r in data);pool=[];rows=[];salt='JSA_RTX_VALIDATION_V1|confirmation|20261010|'
    for r in data:
        tid=r['task_id'];full='MBPP/'+str(tid);reasons=[]
        if not 11<=tid<=510:reasons.append('outside_official_test_ID_range')
        if counts[tid]!=1 or texts[r['prompt']]!=1:reasons.append('duplicate_ID_or_description')
        if tid in matches:reasons.append('prior_execution_or_ambiguous_project_ID_description_evidence')
        rank=hashlib.sha256((salt+full).encode()).hexdigest();rows.append({'id':full,'excluded':reasons,'evidence':matches.get(tid),'rank':rank})
        if not reasons:pool.append({'id':full,'description':r['prompt'],'raw_prompt':'Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n'+r['prompt'],'description_sha256':hashlib.sha256(r['prompt'].encode()).hexdigest(),'cap':128,'selection_hash':rank})
    pool.sort(key=lambda r:(r['selection_hash'],r['id']));selected=pool[:24]
    save(LOCAL/'EXPOSURE_CATALOG.json',catalog)
    report={'status':'PASS' if len(pool)>=24 and not errors else 'INPUT_POOL_BLOCKED','utc':now(),'dataset':{'revision':'e49bbfe381c9c0e564b937f1c4e163a2273c65cc','sha256':expected,'rows':len(data)},'refs_scanned':commits,'pull_heads_count':len(prs),'host_roots':roots,'archive_receipts':archive_receipts,'catalog_sha256':sha(LOCAL/'EXPOSURE_CATALOG.json'),'records':len(catalog),'unique_texts':len(seen),'errors':errors,'rows':rows,'eligible_ranked':[r['id'] for r in pool],'selected':[r['id'] for r in selected],'new_confirmation_forwards':0,'policy':'Pure downloaded corpus and explicit vocab-only output do not count as forwards; ambiguous matches excluded conservatively. Unknown remote host payloads are unavailable; public cohort IDs conservatively excluded. No global training-data claim.'}
    report['availability_only']=availability
    save(PUB/'EXPOSURE_AUDIT.json',report)
    if report['status']=='PASS':save(PUB/'CONFIRMATION_INPUTS.json',selected)
    print(json.dumps({'status':report['status'],'eligible':len(pool),'selected':report['selected'],'errors':errors}),flush=True)
if __name__=='__main__':main()
