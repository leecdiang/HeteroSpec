"""Prospective MBPP/GSM8K audit derived from pinned PR80 auditor; no model forwards."""
import collections,re,zipfile,tarfile,ahocorasick
from common import *
TEXT={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.py','.toml','.cpp','.h','.tex'}
SKIP={'.git','__pycache__','node_modules','vendor','third_party','models','tools','hf-cache','datasets','env','python311','pinned-source','native-build','native-source','source','c-source','x-source','build','c-build','x-build','bin','dependencies','site-packages','llm-42'}
def main():
    assert not (PUB/'CONFIRMATION_INPUTS.json').exists()
    from audit_index_correction import transport_proof
    index_proof=transport_proof();metadata_hashes={index_proof['failed_index_sha256'],*index_proof['wrappers']}
    def metadata_index_only(r):
        e=r.get('evidence')
        return r.get('id') in index_proof['safe_IDs'] and isinstance(e,dict) and e.get('count')==len(e.get('examples',[])) and bool(e.get('examples')) and all(x['sha256'] in metadata_hashes for x in e['examples'])
    corpus=Path('D:/HeteroSpec-RTX-Target-V1/work/rtx-target-v1/sanitized-mbpp.json');expected='ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9';assert sha(corpus)==expected
    mbpp_data=read(corpus);gsm_path=LOCAL/'datasets/gsm8k-test.jsonl';gsm_expected='3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14';assert sha(gsm_path)==gsm_expected;gsm_data=[json.loads(b) for b in gsm_path.read_text(encoding='utf-8').splitlines()];assert len(gsm_data)==1319;data=mbpp_data+[{'task_id':100000+i,'prompt':r['question']} for i,r in enumerate(gsm_data)];patterns={}
    for r in data:
        for b in [r['prompt'].encode(),json.dumps(r['prompt'],ensure_ascii=True)[1:-1].encode()]:patterns.setdefault(b,set()).add(r['task_id'])
    descriptions=ahocorasick.Automaton();[descriptions.add_word(b.decode('latin1'),tuple(ids)) for b,ids in patterns.items()];descriptions.make_automaton();ids=re.compile(rb'\b(?:MBPP[/_\-](\d{1,4})|GSM8K/test/(\d{1,4}))\b',re.I)
    seen=set();matches={};catalog=[];errors=[];archive_receipts=[];roots=[];commits={};last=time.monotonic();availability=[];archive_seen=set();resume=os.environ.get('JSA_EXPOSURE_RESUME_LONG')=='1';retry_paths=set();publication={};unwrapped_ids=[]
    history_only=os.environ.get('JSA_HISTORY_INCREMENTAL')=='1';history_receipt=None
    if history_only:
        assert not resume
        prior=read(PUB/'EXPOSURE_AUDIT.json');assert prior['status']=='PASS' and not prior['errors']
        catalog=read(LOCAL/'EXPOSURE_CATALOG.json');assert sha(LOCAL/'EXPOSURE_CATALOG.json')==prior['catalog_sha256']
        seen={r['sha256'] for r in catalog};matches={(100000+int(r['id'].split('/')[-1]) if r['domain']=='GSM8K' else int(r['id'].split('/')[-1])):r['evidence'] for r in prior['rows'] if r['evidence']}
        availability=prior['availability_only'];archive_receipts=prior['archive_receipts'];roots=prior['host_roots']
    if resume:
        prior=read(PUB/'EXPOSURE_AUDIT.json');save(LOCAL/'EXPOSURE_SHORTPATH_ATTEMPT.json',prior);catalog=read(LOCAL/'EXPOSURE_CATALOG.json');seen={r['sha256'] for r in catalog};matches={int(r['id'].split('/')[1]):r['evidence'] for r in prior['rows'] if r['evidence']};availability=prior['availability_only'];archive_receipts=prior['archive_receipts'];archive_seen={r['sha256'] for r in archive_receipts};retry_paths={r['path'] for r in prior['errors']}
        for tid,evidence in list(matches.items()):
            if evidence['count']==len(evidence['examples']) and all('PUBLISH' in e['path'] and '!' not in e['path'] for e in evidence['examples']):
                checked=True
                for e in evidence['examples']:
                    p=Path('\\\\?\\'+e['path']);b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==e['sha256'];a=json.loads(b);checked &= isinstance(a,list) and all(isinstance(r,dict) and r.get('type')=='blob' and isinstance(r.get('path'),str) and isinstance(r.get('content'),str) for r in a);publication[e['path']]=b
                if checked:del matches[tid];unwrapped_ids.append(tid)
        seen.difference_update(hashlib.sha256(b).hexdigest() for b in publication.values())
    def scan(b,label):
        nonlocal last
        h=hashlib.sha256(b).hexdigest();catalog.append({'path':label,'sha256':h,'bytes':len(b)})
        if time.monotonic()-last>20:
            save(LOCAL/'audit-progress'/f'{len(catalog):08d}.json',{'matches':matches,'errors':errors,'catalog_records':len(catalog),'unique':len(seen),'last_path':label})
            print('AUDIT',len(catalog),'unique',len(seen),'excluded_ids',len(matches),'path',label,flush=True);last=time.monotonic()
        if h in [expected,gsm_expected] or h in seen:return
        seen.add(h)
        if str(LOCAL).lower().replace('\\','/') in label.lower().replace('\\','/') and any(k in label.lower().replace('\\','/') for k in ['/audit-progress/', '/preparation-versions/', '/exposure_checkpoint.json']):
            availability.append({'path':label,'sha256':h,'classification':'this study interrupted zero-forward preparation index; underlying sources audited independently; no selected confirmation or model output'});return
        if 'vocabulary' in label.lower() and re.search(rb'"vocab_only"\s*:\s*true',b) and re.search(rb'"forward_calls"\s*:\s*0',b) and not re.search(rb'"(?:original_reference_ids|predicted_ms|generated_ids|tokens_predicted)"\s*:',b):
            availability.append({'path':label,'sha256':h,'classification':'native vocab-only/tokenization records; zero context creations/forwards; no model output'});return
        if re.search(r'part-\d+-attempt-\d+\.response\.json$',label) and re.search(rb'"encoding"\s*:\s*"base64"',b):
            availability.append({'path':label,'sha256':h,'classification':'base64 transport response; decoded archive logical objects audited independently'});return
        # Previous exposure audits list entire eligible pools; that is availability,
        # not 427 model executions. Retain their exclusions and selected cohorts.
        label_lower=label.lower()
        if 'exposure' in label_lower or b'"eligible_ranked"' in b or b'"eligible_pool"' in b:
            try:a=json.loads(b)
            except (ValueError,UnicodeDecodeError):a=None
            if isinstance(a,dict) and ('eligible_ranked' in a or 'eligible_pool' in a or ('rows' in a and any(k in a for k in ['selected','chosen','eligible_count','known_executed_planned']))):
                keep={k:v for k,v in a.items() if k in ['selected','chosen','prior_mbpp_executed','known_executed_planned','engineering','formal','exclusion_reasons','reservations']}
                keep['excluded_rows']=[r for r in a.get('rows',[]) if not metadata_index_only(r) and (r.get('exclusions') or r.get('excluded') or r.get('reasons') or r.get('status') in ['EXECUTED_OR_INSPECTED','UNKNOWN'])]
                availability.append({'path':label,'sha256':h,'classification':'exposure population/availability ledger; only selected or excluded/unknown rows scanned'})
                b=json.dumps(keep).encode()
            elif isinstance(a,dict) and ('descriptions' in a and 'identifiers' in a or 'description_matches' in a and 'project_records' in a or all(isinstance(v,dict) and 'sha256' in v and 'bytes' in v for v in a.values())):
                # Catalogs and match maps are audit indexes. Their source objects
                # are scanned independently and their ledger exclusions above apply.
                availability.append({'path':label,'sha256':h,'classification':'audit index; underlying source objects and ledger exclusions scanned separately'});return
        try:a=json.loads(b)
        except (ValueError,UnicodeDecodeError):a=None
        tree=a.get('tree') if isinstance(a,dict) else a
        if isinstance(tree,list) and tree and all(isinstance(r,dict) and r.get('type')=='blob' and isinstance(r.get('path'),str) and isinstance(r.get('content'),str) for r in tree):
            availability.append({'path':label,'sha256':h,'classification':'GitHub publication transport wrapper; each embedded logical file decoded and audited separately'})
            for r in tree:scan(r['content'].encode(),label+'!publish:'+r['path'])
            return
        if isinstance(a,list) and a==mbpp_data:
            availability.append({'path':label,'sha256':h,'classification':'semantically identical official downloaded corpus; no forward record'});return
        if isinstance(a,list) and len(a)==len(mbpp_data) and all(isinstance(r,dict) and 'task_id' in r and 'prompt' in r and not any(k in r for k in ['response','generated_ids','proposal','logits','predicted_ms','tokens_predicted']) for r in a) and {r['task_id']:r['prompt'] for r in a}=={r['task_id']:r['prompt'] for r in mbpp_data}:
            availability.append({'path':label,'sha256':h,'classification':'complete official ID/description corpus; answer/test/metadata representation differs; no output payload'});return
        if isinstance(a,dict) and isinstance(a.get('files'),dict) and all(isinstance(v,dict) and 'sha256' in v for v in a['files'].values()):
            availability.append({'path':label,'sha256':h,'classification':'CAS logical-file index; actual science objects scanned independently'});return
        if isinstance(a,dict) and a.get('schema')=='heterospec.jsa.b570.coordination.v1' and 'remaining_ranked_candidates' in a:
            a={k:v for k,v in a.items() if k!='remaining_ranked_candidates'}
            availability.append({'path':label,'sha256':h,'classification':'B570 metadata coordination snapshot: unreserved remaining candidate availability is not forward evidence; both provisional B570 and RTX reservations retained'})
            b=json.dumps(a,ensure_ascii=False).encode()
        hits={int(m.group(1)) if m.group(1) else 100000+int(m.group(2)) for m in ids.finditer(b)}
        if True:
            for _,matched_ids in descriptions.iter(b.decode('latin1')):hits.update(matched_ids)
        new_hits=hits-set(matches)
        if len(new_hits)>50:print('BROAD_NEW_MATCH',label,len(new_hits),'keys',list(a)[:12] if isinstance(a,dict) else type(a).__name__,flush=True)
        for tid in hits:
            a=matches.setdefault(tid,{'count':0,'examples':[]});a['count']+=1
            if len(a['examples'])<8:a['examples'].append({'path':label,'sha256':h})
        if time.monotonic()-last>20:print('AUDIT',len(catalog),'unique',len(seen),'excluded_ids',len(matches),flush=True);last=time.monotonic()
    # All pull heads are read explicitly, including merged or deleted branches.
    prs=read(LOCAL/'PR_HEADS.json');assert len(prs)>=83;assert next(p['headRefOid'] for p in prs if p['number']==83)==DESIGN_SHA
    fetch=['git','fetch','origin']+[f'refs/pull/{p["number"]}/head:refs/audit/pr-{p["number"]}' for p in prs]
    subprocess.run(fetch,cwd=REPO,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    refs=subprocess.check_output(['git','for-each-ref','--format=%(refname) %(objectname)','refs/remotes/origin','refs/audit'],cwd=REPO,text=True).splitlines()
    blobs={}
    previous_git_labels={r['path'] for r in catalog if r['path'].startswith('git:')} if history_only else set();covered=set()
    for line in refs:
        ref,commit=line.split();commits[ref]=commit
        if commit in commits.values() and any(v==commit for k,v in list(commits.items())[:-1]):continue
        tree=subprocess.check_output(['git','ls-tree','-rz',commit],cwd=REPO)
        for entry in tree.split(b'\0'):
            if not entry:continue
            meta,p=entry.split(b'\t',1);mode,kind,oid=meta.split();name=p.decode()
            if kind==b'blob' and Path(name).suffix.lower() in TEXT:
                label='git:'+commit+':'+name;blobs.setdefault(oid.decode(),label)
                if label in previous_git_labels:covered.add(oid.decode())
    if history_only:
        history=read(LOCAL/'GIT_HISTORY_TEXT_OBJECTS.json');blobs={oid:'gitblob:'+oid+':'+name for oid,name in history['blobs'].items() if oid not in covered}
        history_receipt={'reachable_commits':len(history['commits']),'unique_trees':len({r.split()[1] for r in history['commits']}),'reachable_text_blobs':len(history['blobs']),'previously_read_head_blob_objects_reused':len(covered),'additional_text_blob_objects_read':len(blobs),'object_list_sha256':sha(LOCAL/'GIT_HISTORY_TEXT_OBJECTS.json'),'shallow_repository':False,'unadvertised_force_pushed_or_unreachable_states':'unavailable; other private hosts and pretraining also unavailable'}
        print('GIT HISTORY SUPPLEMENT',json.dumps(history_receipt),flush=True)
    # Download small scientific blobs in one refetch instead of many network round trips.
    # Existing Git objects are reused; the promisor fetches missing blobs on demand.
    proc=subprocess.Popen(['git','cat-file','--batch'],cwd=REPO,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for oid,label in blobs.items():
        proc.stdin.write((oid+'\n').encode());proc.stdin.flush();header=proc.stdout.readline().split()
        assert header[0].decode()==oid and len(header)==3
        b=proc.stdout.read(int(header[2]));assert proc.stdout.read(1)==b'\n';scan(b,label)
    proc.stdin.close();assert proc.wait()==0
    for label,b in publication.items():scan(b,label)
    for root in ([] if history_only else [Path('C:/Users/ASUS/Documents/Codex'),Path('D:/HeteroSpec-PC'),Path('D:/HeteroSpec-RTX-Target-V1')]):
        roots.append(str(root))
        walk_root='\\\\?\\'+str(root.resolve())
        for d,dirs,files in os.walk(walk_root):
            dirs[:]=[n for n in dirs if n not in SKIP and not n.startswith('.venv')]
            for name in files:
                p=Path(d)/name
                label=str(p)[4:] if str(p).startswith('\\\\?\\') else str(p)
                if resume and len(label)<260 and label not in retry_paths:continue
                try:
                    if p.suffix.lower() in TEXT:scan(p.read_bytes(),label)
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
    counts=collections.Counter(r['task_id'] for r in data);texts=collections.Counter(r['prompt'] for r in data);pool=[];rows=[]
    for r in data:
        tid=r['task_id'];domain='GSM8K' if tid>=100000 else 'MBPP';full='GSM8K/test/'+str(tid-100000) if tid>=100000 else 'MBPP/'+str(tid);reasons=[]
        if domain=='MBPP' and not 11<=tid<=510:reasons.append('outside_official_test_ID_range')
        if counts[tid]!=1 or texts[r['prompt']]!=1:reasons.append('duplicate_ID_or_description')
        if tid in matches:reasons.append('prior_execution_or_ambiguous_project_ID_description_evidence')
        rank=hashlib.sha256(('heterospec-jsa-third-family-20261011-v1|'+domain+'|'+full).encode()).hexdigest()
        rows.append({'id':full,'domain':domain,'exclusions':reasons,'evidence':matches.get(tid),'selection_hash':rank})
        if not reasons:
            prefix='Solve the following problem and explain your reasoning.\n\n' if domain=='GSM8K' else 'Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n'
            pool.append({'id':full,'domain':domain,'description':r['prompt'],'raw_prompt':prefix+r['prompt'],'description_sha256':hashlib.sha256(r['prompt'].encode()).hexdigest(),'cap':128,'selection_hash':rank})
    pool.sort(key=lambda r:(r['selection_hash'],r['id']))
    if history_only:
        (PUB/'EXPOSURE_AUDIT.json').rename(PUB/'EXPOSURE_HEADS_HOST.json')
        (LOCAL/'EXPOSURE_CATALOG.json').rename(LOCAL/'EXPOSURE_CATALOG_HEADS_HOST.json')
        (LOCAL/'AVAILABLE_CANDIDATES.json').rename(LOCAL/'AVAILABLE_CANDIDATES_HEADS_HOST.json')
    save(LOCAL/'EXPOSURE_CATALOG.json',catalog)
    report={'status':'PASS' if all(sum(r['domain']==d for r in pool)>=12 for d in ['MBPP','GSM8K']) and not errors else 'INPUT_POOL_BLOCKED','utc':now(),'datasets':{'MBPP':{'revision':'e49bbfe381c9c0e564b937f1c4e163a2273c65cc','sha256':expected,'rows':len(mbpp_data)},'GSM8K':{'revision':'3101c7d5072418e28b9008a6636bde82a006892c','sha256':gsm_expected,'rows':len(gsm_data)}},'refs_scanned':commits,'pull_heads_count':len(prs),'host_roots':roots,'archive_receipts':archive_receipts,'catalog_sha256':sha(LOCAL/'EXPOSURE_CATALOG.json'),'records':len(catalog),'unique_texts':len(seen),'errors':errors,'rows':rows,'eligible_ranked':[r['id'] for r in pool],'selected':[],'new_confirmation_forwards':0,'Windows_extended_paths':True,'availability_only':availability,'policy':'Conservative ID/description evidence exclusion; all accessible history, unknown remote hosts explicit; template/token-count gates follow before final selection. No pretraining claim.'}
    if history_only:report['reachable_Git_history_supplement']=history_receipt;report['prior_heads_host_audit_sha256']=sha(PUB/'EXPOSURE_HEADS_HOST.json');report['prior_static_index_correction']=prior['static_index_correction']
    save(PUB/'EXPOSURE_AUDIT.json',report)
    if report['status']=='PASS':save(LOCAL/'AVAILABLE_CANDIDATES.json',{'eligible_pool':pool,'selected':[],'model_forwards':0})
    print(json.dumps({'status':report['status'],'eligible':{d:sum(r['domain']==d for r in pool) for d in ['MBPP','GSM8K']},'errors':len(errors)}),flush=True)
if __name__=='__main__':main()
