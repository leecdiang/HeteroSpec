"""Static MBPP selection; no context or model forward is used."""
import collections, zipfile
from prepare import *

def main():
    if (DOC/'COHORT.json').exists():raise RuntimeError('cohort already selected')
    p=OUT/'sanitized-mbpp.json';data=read(p)
    upstream='e49bbfe381c9c0e564b937f1c4e163a2273c65cc'
    descriptions={r['task_id']:r['prompt'] for r in data if 11<=r['task_id']<=510}
    counts=collections.Counter(r['task_id'] for r in data);text_counts=collections.Counter(r['prompt'] for r in data)
    # Limit audit to project records, not unrelated user files or model training data.
    roots=[ASSET/x for x in ['scripts','benchmarks','reports','runs','logs','artifacts','configs','datasets','work']]
    roots += [ROOT/x for x in ['scripts','benchmarks','paper','docs']]
    audit_files={};hits={};name_hits=[];skipped=[]
    suffixes={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.py','.toml'}
    for root in roots:
        if not root.exists():continue
        for f in root.rglob('*'):
            if not f.is_file() or f.suffix.lower() not in suffixes or '__pycache__' in f.parts:continue
            if ROOT in f.parents and ('rtx_target_verification_intervention_v1' in f.parts):continue
            b=f.read_bytes();audit_files[str(f)]=hashlib.sha256(b).hexdigest()
            for tid,desc in descriptions.items():
                if desc.encode('utf-8') in b:hits.setdefault(tid,[]).append(str(f))
            if b'MBPP/' in b or b'MBPP-' in b:name_hits.append(str(f))
    archives={}
    for f in (ASSET/'archives').glob('*.zip'):
        with zipfile.ZipFile(f) as z:
            names=z.namelist();matches=[n for n in names if 'mbpp' in n.lower()]
            archives[f.name]={'member_count':len(names),'mbpp_named_members':matches,'scope':'member index checked; archive bytes not wholly decoded'}
            # Scan text inference records inside archives. Skip tools/models and nonrecords.
            for n in names:
                if Path(n).suffix.lower() not in suffixes or not any('/'+x+'/' in '/'+n for x in ['runs','logs','artifacts','benchmarks','reports']):continue
                info=z.getinfo(n)
                if info.file_size>100*1024*1024:skipped.append({'archive':f.name,'member':n,'reason':'over100MiB'});continue
                b=z.read(n)
                for tid,desc in descriptions.items():
                    if desc.encode() in b:hits.setdefault(tid,[]).append(f.name+':'+n)
    # Model training exposure is outside this audit. Any matching description is conservatively excluded.
    inputs=read(OUT/'INPUTS.json');existing={sha(ROOT/v['prompt']) for v in inputs.values()};rows=[];queries=[]
    template='Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n{description}'
    for r in data:
        tid=r['task_id'];reasons=[]
        if not 11<=tid<=510:reasons.append('outside_official_test_range')
        if counts[tid]!=1:reasons.append('nonunique_id')
        if text_counts[r['prompt']]!=1:reasons.append('duplicate_description')
        if tid in hits:reasons.append('known_or_ambiguous_project_exposure')
        text=template.format(description=r['prompt']);h=hashlib.sha256(text.encode()).hexdigest()
        if h in existing:reasons.append('duplicate_prompt')
        row={'task_id':tid,'description_sha256':hashlib.sha256(r['prompt'].encode()).hexdigest(),'prompt_sha256':h,'exposure_matches':hits.get(tid,[]),'exclusions':reasons}
        rows.append(row)
        if not reasons:queries.append({'task_id':'MBPP/'+str(tid),'formatted_prompt':formatted(text)})
    exe=OUT/'worker-bin/tokenizer.exe';payload=''.join(json.dumps(q)+'\n' for q in queries).encode()
    with (OUT/'tokenizer.stderr.log').open('wb') as se:
        run=subprocess.run([str(exe),str(RUNTIME),str(ASSET/'models/gguf/Qwen3-8B-Q8_0.gguf')],input=payload,stdout=subprocess.PIPE,stderr=se,check=True)
    tokens={int(x['task_id'].split('/')[1]):x for x in map(json.loads,run.stdout.splitlines())}
    eligible=[]
    for row in rows:
        if row['exclusions']:continue
        x=tokens[row['task_id']];assert x['forward_calls']==0 and x['vocab_only']
        row['prompt_token_count']=len(x['prompt_ids'])
        if len(x['prompt_ids'])+128>4096:row['exclusions'].append('context_capacity')
        else:
            row['selection_hash']=hashlib.sha256(('HeteroSpec|RTX_TARGET_VERIFY_INTERVENTION_V1|MBPP|20261004|'+str(row['task_id'])).encode()).hexdigest();eligible.append(row)
    eligible.sort(key=lambda r:(r['selection_hash'],r['task_id']));assert len(eligible)>=30
    eng=[r['task_id'] for r in eligible[:6]];formal=[r['task_id'] for r in eligible[6:30]]
    for tid in eng+formal:
        task='MBPP/'+str(tid);text=template.format(description=descriptions[tid]);d=OUT/'inputs'/task.replace('/','-');d.mkdir(parents=True)
        (d/'prompt.txt').write_text(text,encoding='utf-8',newline='\n');save(d/'prompt_ids.json',tokens[tid]['prompt_ids'])
        inputs[task]={'prompt':str((d/'prompt.txt').relative_to(ROOT)).replace('\\','/'),'prompt_sha256':sha(d/'prompt.txt'),'ids':str((d/'prompt_ids.json').relative_to(ROOT)).replace('\\','/'),'group':'engineering' if tid in eng else 'new_formal'}
    save(OUT/'INPUTS.json',inputs)
    save(DOC/'EXPOSURE_AUDIT.json',{'utc':utc(),'project_records':audit_files,'description_matches':hits,'mbpp_identifier_files':name_hits,'archive_indexes':archives,'skipped_members':skipped,'limitation':'no known execution exposure within inspected project records and indexed local archives; no assertion about model training or inaccessible histories','new_task_forward_calls':0})
    save(DOC/'COHORT.json',{'utc':utc(),'dataset':'official Google Research sanitized-mbpp.json JSON array','upstream_commit':upstream,'url':f'https://raw.githubusercontent.com/google-research/google-research/{upstream}/mbpp/sanitized-mbpp.json','sha256':sha(p),'template':template,'engineering':eng,'formal':formal,'old_regression':TASKS,'eligible_ranked':[r['task_id'] for r in eligible],'rows':rows,'new_task_forward_calls_before_selection':0,'tokenizer_sha256':sha(exe),'exposure_audit_sha256':sha(DOC/'EXPOSURE_AUDIT.json')})
    save(DOC/'QUEUE.json',[{'id':f'{STUDY}/v1/{t}/{c}/{rep}','task':t,'condition':c,'rep':rep} for c in ['R','H0','H1','N0','N1'] for t in TASKS+['MBPP/'+str(i) for i in formal] for rep in range(1,4)])
    print(json.dumps({'eligible':len(eligible),'engineering':eng,'formal':formal,'audit_files':len(audit_files),'new_task_forwards':0}),flush=True)

if __name__=='__main__':main()
