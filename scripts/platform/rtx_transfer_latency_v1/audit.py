"""Audit available task-bearing evidence before any new inference."""
import gzip, hashlib, json, re, subprocess, tarfile, zipfile, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT/'benchmarks/rtx_transfer_latency_v1'
SALT = 'RTX_TRANSFER_AND_MATCHED_LATENCY_V1|reserved|20260930|'
TEXT = {'.json','.jsonl','.txt','.log','.md','.csv','.yaml','.yml','.py','.ps1'}
IDS = re.compile(r'HumanEval[/_\-](\d+)')
SKIP = {'eligible_pool','selection_keys','tasks','files_scanned','evidence','no_known_exposure_task_ids'}

def main():
    with gzip.open('D:/HeteroSpec-PC/datasets/humaneval/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:
        tasks = {r['task_id']:r['prompt'] for r in map(json.loads,f)}
    roots = [ROOT,Path('D:/HeteroSpec-PC'),Path('C:/Users/ASUS/Documents/Codex'),
             Path('C:/Users/ASUS/Downloads'),Path('C:/Users/ASUS/Desktop'),Path('D:/'),Path('E:/'),Path('F:/')]
    evidence=[]; errors=[]; seen=set(); catalog=[]
    def inspect(label,data):
        text=data.decode('utf-8-sig',errors='replace')
        low=label.lower()
        found=set()
        # Inventories enumerate the universe. Only recorded exclusions and selections
        # are exposure; remaining eligible IDs are input listings, not results.
        if low.endswith(('.json','.jsonl')):
            try:
                obj=json.loads(text)
                def visit(v):
                    if isinstance(v,dict):
                        if 'seen_in_historical_m4_execution' in v and not v['seen_in_historical_m4_execution'] and not v['historical_outcome_exposed']:
                            return  # explicitly unused input-only candidate
                        for k,x in v.items():
                            if k in SKIP: continue
                            if k in ('exclusion_reasons','excluded_task_ids'): found.update(IDS.findall(str(x)))
                            else: visit(x)
                    elif isinstance(v,list):
                        for x in v:visit(x)
                    elif isinstance(v,str):found.update(IDS.findall(v))
                visit(obj)
                if isinstance(obj,dict) and isinstance(obj.get('tasks'),dict):
                    for t,r in obj['tasks'].items():
                        if isinstance(r,dict) and ('EXPOSED' in r.get('status','') or r.get('sources')):
                            found.update(IDS.findall(t))
            except (ValueError,TypeError):found.update(IDS.findall(text))
        else: found.update(IDS.findall(text))
        found.update(IDS.findall(label))
        if not found and ('prompt' in low or low.endswith('.txt')):
            found.update(t.split('/')[1] for t,p in tasks.items() if p in text)
        ids=sorted({'HumanEval/'+x for x in found}&tasks.keys())
        if ids:evidence.append({'path':label,'sha256':hashlib.sha256(data).hexdigest(),'task_ids':ids,
            'basis':'conservative known or ambiguous task association; no outcome-based selection'})
    if '--reclassify-inventories' in sys.argv:
        cached=json.loads((STUDY/'exposure_inventory.json').read_text(encoding='utf-8'))
        evidence=[r for r in cached['evidence'] if 'WORKLOAD_INVENTORY.json' not in r['path']]
        catalog=cached['catalog']; errors=cached['errors']
        for r in cached['evidence']:
            if 'WORKLOAD_INVENTORY.json' not in r['path']:continue
            label=r['path']
            if '!' in label:
                path,member=label.split('!',1)
                with tarfile.open(path) as t:data=t.extractfile(member).read()
            else:data=Path(label).read_bytes()
            assert hashlib.sha256(data).hexdigest()==r['sha256']
            inspect(label,data)
        roots_to_scan=[]
    else:roots_to_scan=roots
    for root in roots_to_scan:
        if not root.exists():continue
        cmd=['rg','--files','--hidden','--no-ignore',str(root)]
        for g in ('!.git/**','!node_modules/**','!AppData/**','!$RECYCLE.BIN/**','!System Volume Information/**',
                  '!models/**','!tools/**','!.venv*/**','!python311/**','!datasets/**','!llama-source/**','!HeteroSpec-base/**'):
            cmd+=['-g',g]
        proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # Windows paths may contain personal names; record only relevant experiment
        # files. Protected system directories are outside scientific evidence scope.
        for name in proc.stdout.decode('utf-8',errors='replace').splitlines():
            p=Path(name); key=str(p).lower()
            if key in seen:continue
            seen.add(key)
            if any(x in key for x in ('rtx_transfer_latency_v1','rtx_predictive_transfer_v1','rtx_matched_latency_v1','llama-source','heterospec-base','\\.codex\\')):continue
            if p.suffix.lower() not in TEXT and not key.endswith(('.tar.gz','.zip')):continue
            relevant=any(x in key for x in ('heterospec','rtx-','b570','humaneval','experiment','benchmark','replication','divergence','capture','5070'))
            if not relevant:continue
            if any(x in key for x in ('\\models\\','\\datasets\\','\\tools\\','\\.venv','\\python311\\','\\vendor\\')):continue
            try:
                if key.endswith(('.tar.gz','.zip')):
                    if 'source' in p.name.lower():continue
                    catalog.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'archive':True})
                    if key.endswith('.zip'):
                        with zipfile.ZipFile(p) as z:
                            for m in z.infolist():
                                if Path(m.filename).suffix.lower() in TEXT:inspect(str(p)+'!'+m.filename,z.read(m))
                    else:
                        with tarfile.open(p) as t:
                            for m in t:
                                if m.isfile() and Path(m.name).suffix.lower() in TEXT:inspect(str(p)+'!'+m.name,t.extractfile(m).read())
                else:
                    data=p.read_bytes(); inspect(str(p),data)
                    catalog.append({'path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            except Exception as e:errors.append({'path':str(p),'error':str(e)})
    by={t:[] for t in tasks}
    for r in evidence:
        for t in r['task_ids']:by[t].append(r['path'])
    eligible=sorted(t for t in tasks if not by[t]) if not errors else []
    keys={t:hashlib.sha256((SALT+t).encode()).hexdigest() for t in eligible}
    selected=sorted(eligible,key=lambda t:keys[t])[:24]
    STUDY.mkdir(parents=True,exist_ok=True)
    inventory={'created_utc':datetime.now(timezone.utc).isoformat(),'roots':[str(p) for p in roots],
       'scope':'recursive available scientific material, archive members included; dataset/vendor/universe listings excluded; relevant paths identified without inference',
       'errors':errors,'catalog':catalog,'evidence':evidence,'excluded_task_ids':sorted(t for t in tasks if by[t]),
       'eligible_pool':eligible,'selection_salt':SALT,'selected_task_ids':selected,'selection_keys':{t:keys[t] for t in selected},
       'input_hashes':{t:hashlib.sha256(tasks[t].encode()).hexdigest() for t in selected},
       'exclusion_reasons':{t:by[t] for t in tasks if by[t]},'new_inference_executed':False,
       'status':'PASS' if len(selected)==24 and not errors else 'RESERVED_POOL_BLOCKED'}
    (STUDY/'exposure_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:inventory[k] for k in ('status','selected_task_ids','errors')}))
    print('excluded',len(inventory['excluded_task_ids']),'eligible',len(eligible),'files',len(catalog))

if __name__=='__main__':main()
