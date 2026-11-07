"""Outcome-independent, conservative host/repository/archive exposure audit."""
import gzip, hashlib, json, re, subprocess, tarfile, zipfile
from pathlib import Path
from study import ROOT, LOCAL, PLAN, DATA, SALT, PREFIX, save, sha, utc, V1

TEXT={'.json','.jsonl','.md','.txt','.log','.csv','.yaml','.yml','.py','.ps1','.sh'}
ID=re.compile(r'HumanEval[/_\-](\d+)')

def main():
    assert not (PLAN/'EXPOSURE_AUDIT.json').exists(),'Exposure audit already frozen'
    with gzip.open(DATA,'rt',encoding='utf-8') as f: dataset={r['task_id']:r for r in map(json.loads,f)}
    roots=[LOCAL,Path('C:/hs'),Path('C:/work'),Path('C:/Users/DIANG/Documents/Codex'),
        Path('C:/Users/DIANG/Desktop'),Path('C:/Users/DIANG/Downloads'),Path('C:/Users/DIANG/.codex/worktrees')]
    exposed=set(V1['task_ids']);evidence=[];errors=[];scanned=[];seen=set()
    old_reserved=json.loads((ROOT/'benchmarks/b570_mechanism_v08/RESERVED_VALIDATION_SET.json').read_text(encoding='utf-8'))['selected_task_ids']
    exposed.update(old_reserved)
    evidence.append({'path':'explicit old 30 + old reserved 24','task_ids':sorted(exposed),'basis':'Mandatory exclusion independent of outcomes'})
    def inspect(label,data,strong):
        text=data.decode('utf-8-sig',errors='replace')
        if not strong and not re.search(r'B570|b570|Arc\(TM\) B570',text):return
        # Audit inventories enumerate the dataset universe. Parse recorded exposure only.
        if Path(label.split('!')[-1]).name in ('exposure_inventory.json','RESERVED_VALIDATION_SET.json'):
            obj=json.loads(text)
            ids=set(obj.get('selected_task_ids',[]))
            ids.update(t for t,v in obj.get('tasks',{}).items() if v.get('status')!='NO_KNOWN_B570_EXPOSURE')
            for row in obj.get('evidence',[]):ids.update(row.get('task_ids',[]))
        else:
            ids={'HumanEval/'+n for n in ID.findall(label+'\n'+text)}
            if not ids and ('prompt' in label.lower() or label.lower().endswith('.txt')):
                ids={t for t,r in dataset.items() if r['prompt'] in text}
        ids &= dataset.keys()
        if ids:
            exposed.update(ids);evidence.append({'path':label,'sha256':hashlib.sha256(data).hexdigest(),
                'task_ids':sorted(ids),'basis':'Recorded or ambiguous B570-associated task mention; no outcomes select tasks'})
    for root in roots:
        if not root.exists():errors.append({'path':str(root),'error':'missing audit root'});continue
        proc=subprocess.run(['rg','--files','--hidden','--no-ignore',str(root),'-g','!**/.git/**',
            '-g','!**/models/**','-g','!**/datasets/**','-g','!**/tools/**','-g','!**/node_modules/**',
            '-g','!**/upstream/**','-g','!**/__pycache__/**','-g','!**/.venv*/**'],capture_output=True,encoding='utf-8')
        if proc.returncode not in (0,1):errors.append({'path':str(root),'error':proc.stderr});continue
        for name in proc.stdout.splitlines():
            p=Path(name)
            if str(p).lower() in seen:continue
            seen.add(str(p).lower());low=p.as_posix().lower()
            if 'b570_partition_intervention_v1' in low or 'b570-partition-intervention-v1' in low:continue
            if any(x in low for x in ('/b570-direct-id-v1-src/','/llama-b10839/','/cmakefiles/','/vendor/')):continue
            scope='b570' in low or 'windows_humaneval' in low or 'windows-humaneval' in low
            try:
                if p.suffix.lower() in TEXT:
                    data=p.read_bytes();inspect(str(p),data,scope)
                    if scope:scanned.append({'path':str(p),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
                elif low.endswith(('.tar.gz','.zip')) and (scope or '/artifacts/' in low or '/archives/' in low):
                    scanned.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'archive':True})
                    if low.endswith('.tar.gz'):
                        with tarfile.open(p,'r:gz') as ar:
                            for m in ar:
                                if m.isfile() and Path(m.name).suffix.lower() in TEXT and '/datasets/' not in m.name:
                                    inspect(str(p)+'!'+m.name,ar.extractfile(m).read(),scope or 'b570' in m.name.lower())
                    else:
                        with zipfile.ZipFile(p) as ar:
                            for m in ar.infolist():
                                if not m.is_dir() and Path(m.filename).suffix.lower() in TEXT and '/datasets/' not in m.filename:
                                    inspect(str(p)+'!'+m.filename,ar.read(m),scope or 'b570' in m.filename.lower())
            except Exception as ex:errors.append({'path':str(p),'error':repr(ex)})
    eligible=sorted(set(dataset)-exposed) if not errors else []
    selected=sorted(eligible,key=lambda t:hashlib.sha256((SALT+t).encode()).hexdigest())[:24]
    inventory={'audit_utc':utc(),'roots':[str(p) for p in roots],'starting_main':subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip(),
        'policy':'B570-associated identity mention is excluded, including ambiguous/planned exposure. Missing/unreadable scope forbids formal selection. Dataset/vendor universes are excluded. Existing audit manifests are parsed by exposure classification, never by eligible-universe mention.',
        'errors':errors,'files_scanned':scanned,'evidence':evidence,'exposed_task_ids':sorted(exposed),'eligible_task_ids':eligible,
        'old30_task_ids':V1['task_ids'],'old_reserved24_task_ids':old_reserved,'dataset_sha256':sha(DATA),
        'scope_limit':'No claim about deleted/unavailable records or other hosts; all available stated roots and relevant archive members were scanned.'}
    save(PLAN/'EXPOSURE_AUDIT.json',inventory)
    reserved={'created_utc':utc(),'salt':SALT,'selection_rule':'Ascending SHA256(salt + task_id), first 24; no output-based selection',
        'eligible_task_ids':eligible,'task_ids':selected,'repetitions':3,'dataset_sha256':sha(DATA),
        'prompts':{t:{'input':PREFIX+dataset[t]['prompt'],'sha256':hashlib.sha256((PREFIX+dataset[t]['prompt']).encode()).hexdigest(),
            'selection_key':hashlib.sha256((SALT+t).encode()).hexdigest()} for t in selected},'no_new_task_inference':True}
    save(PLAN/'RESERVED_SET.json',reserved)
    print(json.dumps({'exposed':len(exposed),'eligible':len(eligible),'selected':selected,'errors':errors}),flush=True)

if __name__=='__main__':main()
