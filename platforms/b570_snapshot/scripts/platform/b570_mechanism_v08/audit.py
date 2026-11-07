"""Conservative task-identity exposure audit. No inference or outcome selection."""
import gzip, hashlib, json, re, subprocess, tarfile, zipfile
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / 'benchmarks/b570_mechanism_v08'
DISCOVERY = ['HumanEval/'+str(n) for n in (89,101,104,162,3,10,68,70,19,20,28,32)]
PREFIX = 'heterospec-b570-mechanism-v08-reserved|'
TEXT = {'.json','.jsonl','.md','.txt','.log','.csv','.yaml','.yml','.ps1','.py','.sh','.ini'}
IDENTITY = re.compile(r'HumanEval[/_\-](\d+)')

def sha(data): return hashlib.sha256(data).hexdigest()
def save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def main():
    dataset = REPO/'datasets/humaneval/HumanEval.jsonl.gz'
    with gzip.open(dataset,'rt',encoding='utf-8') as f:
        tasks = {r['task_id']:r['prompt'] for r in map(json.loads,f)}
    evidence = []; scanned = []; errors = []
    roots = [REPO, Path('C:/hs'), Path('C:/work'),Path('C:/Users/DIANG/Documents/Codex'),Path('C:/Users/DIANG/Desktop')]
    tracked = set(subprocess.check_output(['git','ls-files'],cwd=REPO,text=True).splitlines())
    def inspect(label, data, scope):
        try: text = data.decode('utf-8-sig',errors='replace')
        except Exception as ex: errors.append({'path':label,'error':str(ex)});return
        strong = scope or bool(re.search(r'B570|b570|Intel\(R\) Arc\(TM\) B570',text))
        if not strong:return
        ids = {'HumanEval/'+m for m in IDENTITY.findall(label+'\n'+text)} & tasks.keys()
        # Prompt-only files can contain no task ID. Match full original dataset text.
        if not ids and ('prompt' in label.lower() or label.lower().endswith(('.stdout.txt','.txt'))):
            ids = {t for t,p in tasks.items() if p in text}
        if ids:
            evidence.append({'path':label,'sha256':sha(data),'task_ids':sorted(ids),'basis':'conservative task identity mention in B570-associated material; no outcomes used'})
    for root in roots:
        if not root.exists():errors.append({'path':str(root),'error':'missing root'});continue
        files = subprocess.check_output(['rg','--files','--hidden','--no-ignore',str(root),'-g','!.git/**','-g','!models/**','-g','!node_modules/**','-g','!__pycache__/**'],text=True,encoding='utf-8').splitlines()
        for name in files:
            p=Path(name)
            if 'b570_mechanism_v08' in p.as_posix():continue
            try: rel=p.relative_to(REPO).as_posix()
            except ValueError:rel=p.as_posix()
            low=rel.lower()
            # Exclude dataset and vendor trees: they list a task universe, not exposures.
            if low.startswith(('datasets/','models/','tools/')) or '/upstream/' in low or '/llama-b10839/' in low or '/b570-direct-id-v1-src/' in low:continue
            scope = 'b570' in low or 'windows_humaneval' in low or 'windows-humaneval' in low
            if p.suffix.lower() in TEXT:
                data=p.read_bytes()
                inspect(rel,data,scope)
                if scope or rel in tracked:scanned.append({'path':rel,'sha256':sha(data),'bytes':len(data),'tracked':rel in tracked})
            elif scope and (low.endswith('.tar.gz') or p.suffix.lower()=='.zip'):
                scanned.append({'path':rel,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size,'archive':True,'tracked':rel in tracked})
                if low.endswith('.tar.gz'):
                    with tarfile.open(p,'r:gz') as archive:
                        for m in archive:
                            if m.isfile() and Path(m.name).suffix.lower() in TEXT and '/dataset/' not in m.name:
                                inspect(rel+'!'+m.name,archive.extractfile(m).read(),True)
                else:
                    with zipfile.ZipFile(p) as archive:
                        for m in archive.infolist():
                            if not m.is_dir() and Path(m.filename).suffix.lower() in TEXT:
                                inspect(rel+'!'+m.filename,archive.read(m),True)
            elif scope:
                ids={'HumanEval/'+m for m in IDENTITY.findall(rel)} & tasks.keys()
                if ids:evidence.append({'path':rel,'sha256':sha(p.read_bytes()),'task_ids':sorted(ids),'basis':'B570 artifact filename'})
    by={t:[] for t in tasks}
    for record in evidence:
        for t in record['task_ids']:by[t].append(record['path'])
    eligible=sorted(t for t in tasks if not by[t]) if not errors else []
    selected=sorted(eligible,key=lambda t:sha((PREFIX+t).encode()))[:24]
    inventory={'schema':'heterospec.b570.mechanism.exposure.v08','audit_utc':datetime.now(timezone.utc).isoformat(),'starting_main':subprocess.check_output(['git','rev-parse','main'],cwd=REPO,text=True).strip(),
      'roots':[str(p) for p in roots],'scope':'all available repository tracked and untracked material; retained C:/hs, C:/work, Documents/Codex and Desktop; archive members included; no model inference',
      'policy':'Any B570-associated task identity mention is conservatively exposed, including planned or ambiguous exposure. No observed outcome values select eligibility. Missing/unreadable scope invalidates selection.',
      'dataset_sha256':sha(dataset.read_bytes()),'errors':errors,'files_scanned':scanned,'evidence':evidence,
      'tasks':{t:{'status':'EXPOSED_B570' if by[t] or errors else 'NO_KNOWN_B570_EXPOSURE','sources':by[t]} for t in sorted(tasks)},'exposed_count':sum(bool(by[t]) for t in tasks),'eligible_count':len(eligible)}
    save('exposure_inventory.json',inventory)
    save('RESERVED_VALIDATION_SET.json',{'schema':'heterospec.b570.mechanism.reserved.v08','dataset_sha256':inventory['dataset_sha256'],'eligible_pool':eligible,'exclusion_reasons':{t:by[t] for t in tasks if by[t]},'selection_rule':'SHA256("'+PREFIX+'" + task_id), ascending hexadecimal lexicographic sort, first 24','selection_keys':{t:sha((PREFIX+t).encode()) for t in selected},'selected_task_ids':selected,'count':len(selected),'no_inference_executed':True})
    (OUT/'EXPOSURE_INVENTORY.md').write_text('# B570 exposure inventory v0.8\n\nAudited repository tracked and retained local evidence plus archive members. Any B570-associated task mention is conservatively excluded, regardless of whether execution is certain. No output values participate in selection.\n\n'+f'Dataset tasks: {len(tasks)}. Exposed/excluded: {inventory["exposed_count"]}. Eligible: {len(eligible)}. Reserved: {len(selected)}. Audit errors: {len(errors)}.\n\n'+ 'Scope and per-file SHA-256 evidence are recorded in exposure_inventory.json. NO_KNOWN_B570_EXPOSURE means no recorded exposure in the available audited scope, not proof about unavailable or deleted records. Dataset/vendor task enumerations are excluded.\n',encoding='utf-8')
    print(json.dumps({'eligible':len(eligible),'exposed':inventory['exposed_count'],'reserved':selected,'errors':errors}))

if __name__=='__main__':main()
