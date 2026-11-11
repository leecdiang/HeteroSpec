"""Audit project history and lock prospective MBPP inputs before any generation."""
import collections,hashlib,json,os,re,subprocess,time,zipfile
from pathlib import Path
from close_base import HERE,ASSET,OLDROOT,REPO,PHASE1,PHASE2,SEED,read,save,sha,rank,formatted,now
SUFFIXES={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.py','.toml','.cpp','.h'}
SKIP={'.git','__pycache__','node_modules','vendor','third_party','models','tools','hf-cache','datasets','env','python311','pinned-source','native-build','native-source','source','c-source','build','c-build','.venv-analysis','.venv-intel','.venv-target','.venv-npu-lab'}
TEMPLATE='Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n{description}'

def main():
    assert not (HERE/'B_INPUTS.json').exists()
    corpus=OLDROOT/'work/rtx-target-v1/sanitized-mbpp.json';expected='ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9'
    assert sha(corpus)==expected;data=read(corpus);assert len(data)==427
    prior_path=HERE.parent/'bridge/benchmarks/rtx_target_verification_intervention_v1/COHORT.json'
    prior=read(prior_path);assert prior['sha256']==expected
    prior_he_path=HERE.parent/'bridge/benchmarks/rtx_trajectory_cost_v4/EXPOSURE_AUDIT.json'
    he=read(prior_he_path);a_tasks={r['id'] for r in read(PHASE2/'INPUTS.json')}
    excluded_he=set(he['exclusion_reasons'])|a_tasks
    assert len(excluded_he)==164 and set(he['eligible_pool'])<=a_tasks
    known={int(t) for t in prior['engineering']+prior['formal']}
    descriptions={r['task_id']:r['prompt'] for r in data if 11<=r['task_id']<=510}
    patterns={};description_hits={};id_hits={};catalog={};available={};errors=[];archives={};seen=set()
    for tid,desc in descriptions.items():
        for b in [desc.encode(),json.dumps(desc,ensure_ascii=True)[1:-1].encode()]:patterns.setdefault(b,set()).add(tid)
    regex=re.compile(b'|'.join(re.escape(b) for b in sorted(patterns,key=len,reverse=True)))
    ids=re.compile(rb'\bMBPP[/\-_](\d{1,4})\b',re.I)
    started=time.monotonic();last=started
    def scan(b,label,h=None):
        nonlocal last
        h=h or hashlib.sha256(b).hexdigest();catalog[label]={'sha256':h,'bytes':len(b)}
        if h==expected:available[label]='bound downloaded corpus, no execution inference';return
        # A pure vocab-only tokenizer result is available input evidence, not a model trajectory.
        if b'"vocab_only": true' in b and b'"forward_calls": 0' in b and not any(k in b for k in [b'generated_ids',b'original_reference_ids',b'predicted_ms',b'accepted_ids']):
            available[label]='explicit zero-forward vocabulary-only record';return
        if h in seen:return
        seen.add(h)
        if b'MBPP' in b or b'mbpp' in b:
            for m in ids.finditer(b):id_hits.setdefault(int(m.group(1)),[]).append({'path':label,'sha256':h})
        if b'Write' in b or b'write' in b:
            for m in regex.finditer(b):
                for tid in patterns[m.group(0)]:description_hits.setdefault(tid,[]).append({'path':label,'sha256':h})
        if time.monotonic()-last>30:
            print(json.dumps({'audit_records':len(catalog),'unique_texts':len(seen),'matched_mbpp_ids':len(set(description_hits)|set(id_hits))}),flush=True);last=time.monotonic()
    roots=[]
    for root in [ASSET,OLDROOT]:
        roots += [root/x for x in ['analysis','artifacts','benchmarks','configs','docs','logs','paper','reports','runs','scripts','telemetry','work'] if (root/x).exists()]
    # Prior local repository copies and deliverable records belong to this same research project.
    for p in Path('C:/Users/ASUS/Documents/Codex').glob('**/.git/config'):
        if 'HeteroSpec' in p.read_text(encoding='utf-8',errors='replace'):
            repo=p.parent.parent
            roots += [repo/x for x in ['analysis','artifacts','benchmarks','configs','docs','logs','paper','reports','runs','scripts','work'] if (repo/x).exists()]
    roots += [HERE.parent/x for x in ['bridge','r','research-pr','feasibility-sources','performance-pilot','continuity-state-v1','rtx-consistency-phase2']]
    visited=set()
    for root in roots:
        for d,dirs,files in os.walk(root):
            dirs[:]=[n for n in dirs if n not in SKIP and not n.startswith('.venv')]
            for name in files:
                p=Path(d)/name
                if p.suffix.lower() not in SUFFIXES or p.resolve() in visited:continue
                visited.add(p.resolve())
                if p.name=='sanitized-mbpp.json':
                    if sha(p)!=expected:errors.append({'path':str(p),'reason':'unknown alternate MBPP corpus'} )
                    else:available[str(p)]='same bound corpus'
                    continue
                try:scan(p.read_bytes(),str(p))
                except OSError as e:errors.append({'path':str(p),'reason':str(e)})
    # Inspect the fetched scientific Git snapshot, even when files are absent in the sparse checkout.
    commit=subprocess.check_output(['git','rev-parse','FETCH_HEAD'],cwd=REPO,text=True).strip()
    tree=subprocess.check_output(['git','ls-tree','-rz',commit],cwd=REPO)
    blobs=[]
    for line in tree.split(b'\0'):
        if not line:continue
        meta,path=line.split(b'\t',1);mode,kind,oid=meta.split();name=path.decode()
        if kind==b'blob' and Path(name).suffix.lower() in SUFFIXES:blobs.append((oid.decode(),name))
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=REPO,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for oid,name in blobs:
        process.stdin.write((oid+'\n').encode());process.stdin.flush();header=process.stdout.readline().split();assert header[0].decode()==oid
        b=process.stdout.read(int(header[2]));assert process.stdout.read(1)==b'\n';scan(b,'git:'+commit+':'+name)
    process.stdin.close();process.wait();assert process.returncode==0
    # Existing native input manifests explicitly identify every previously selected MBPP task.
    old_inputs=read(OLDROOT/'work/rtx-target-v1/INPUTS.json')
    known |= {int(k.split('/')[1]) for k in old_inputs if k.startswith('MBPP/')}
    archive_roots=[ASSET/'archives',HERE.parent.parent/'outputs']
    for root in archive_roots:
        for p in root.glob('*.zip'):
            try:
                with zipfile.ZipFile(p) as z:
                    names=z.namelist();record={'sha256':sha(p),'members':len(names),'scientific_text_scanned':0}
                    if 'INDEX.json' in names:
                        index=json.loads(z.read('INDEX.json'))
                        for e in index['files']:
                            name=e['path']
                            if Path(name).suffix.lower() not in SUFFIXES or any('/'+part+'/' in '/'+name for part in SKIP):continue
                            b=z.read('objects/'+e['sha256']);assert hashlib.sha256(b).hexdigest()==e['sha256'];scan(b,str(p)+'!'+name);record['scientific_text_scanned']+=1
                    else:
                        for name in names:
                            if Path(name).suffix.lower() not in SUFFIXES or not any('/'+part+'/' in '/'+name for part in ['analysis','runs','logs','artifacts','benchmarks','reports','paper']):continue
                            if any('/'+part+'/' in '/'+name for part in SKIP):continue
                            scan(z.read(name),str(p)+'!'+name);record['scientific_text_scanned']+=1
                    archives[str(p)]=record
            except (OSError,ValueError,zipfile.BadZipFile) as e:errors.append({'path':str(p),'reason':str(e)})
    assert not errors,'Unreadable or unknown scientific exposure records; no clean task selection permitted'
    counts=collections.Counter(r['task_id'] for r in data);texts=collections.Counter(r['prompt'] for r in data)
    rows=[];eligible=[]
    for r in data:
        tid=r['task_id'];task='MBPP/'+str(tid);reasons=[]
        if not 11<=tid<=510:reasons.append('outside_bound_official_test_range')
        if counts[tid]!=1 or texts[r['prompt']]!=1:reasons.append('duplicate_id_or_description')
        if tid in known:reasons.append('previous_MBPP_engineering_or_formal')
        evidence=description_hits.get(tid,[])+id_hits.get(tid,[])
        if evidence:reasons.append('executed_inspected_or_ambiguous_project_record')
        text=TEMPLATE.format(description=r['prompt']);prompt=formatted(text)
        if len(prompt.encode())+520>4096:reasons.append('conservative_context_capacity_bound')
        row={'id':task,'status':'EXECUTED_OR_INSPECTED' if tid in known else ('UNKNOWN' if evidence else 'AVAILABLE_ONLY'),
             'exclusions':reasons,'evidence_count':len(evidence),'evidence_sample':evidence[:5],
             'description_sha256':hashlib.sha256(r['prompt'].encode()).hexdigest(),'selection_hash':rank(task)}
        rows.append(row)
        if not reasons:eligible.append({'id':task,'raw_prompt':text,'formatted_prompt':prompt,'cap':128,
                                        'description_sha256':row['description_sha256'],'formatted_prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'selection_hash':rank(task)})
    eligible.sort(key=lambda r:(r['selection_hash'],r['id']));assert len(eligible)>=24
    selected=eligible[:24]
    save(HERE/'generated/EXPOSURE_CATALOG.json',catalog)
    save(HERE/'generated/EXPOSURE_MATCHES.json',{'descriptions':description_hits,'identifiers':id_hits,'available_only':available})
    ledger={'utc':now(),'status':'PASS','main_scanned':commit,'human_eval_remaining':0,'human_eval_excluded':sorted(excluded_he),
            'prior_human_eval_audit_sha256':sha(prior_he_path),'prior_mbpp_cohort_sha256':sha(prior_path),'prior_mbpp_executed':sorted(known),
            'dataset':{'upstream_commit':prior['upstream_commit'],'sha256':expected,'rows':427,'url':prior['url']},
            'project_records':len(catalog),'unique_texts':len(seen),'catalog_sha256':sha(HERE/'generated/EXPOSURE_CATALOG.json'),
            'matches_sha256':sha(HERE/'generated/EXPOSURE_MATCHES.json'),'archives':archives,'errors':errors,'rows':rows,
            'eligible_ranked':[r['id'] for r in eligible],'selected':[r['id'] for r in selected],
            'new_task_model_forwards':0,'limitation':'No known execution or ambiguous description/ID match within the audited available project histories; not a claim about model training or inaccessible histories. Downloaded corpus and explicit zero-forward vocabulary records are availability only.'}
    save(HERE/'EXPOSURE_LEDGER.json',ledger);save(HERE/'B_INPUTS.json',selected)
    print(json.dumps({'status':'PASS','human_eval_remaining':0,'eligible_mbpp':len(eligible),'selected':[r['id'] for r in selected],
                      'project_records':len(catalog),'seconds':time.monotonic()-started,'new_task_model_forwards':0}),flush=True)

if __name__=='__main__':main()
