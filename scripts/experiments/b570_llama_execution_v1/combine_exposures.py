"""Close local/Git, authenticated RTX159 and conservative ongoing RTX162 exclusions."""
from pathlib import Path
import argparse,hashlib,json,re,sys,collections
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha,digest,utc

def combine(root,out):
    root=Path(root);report=read(root/'exposure-scan-01/REPORT.json');need(report['coverage_review_complete'] and not report['errors'],'local/Git coverage unresolved')
    rows=read(root/'exposure-scan-01/EXPOSURES.json');keys={v for x in rows for v in x.values()};inventory=[]
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if re.match(r'^(APPS|MATH|CodeContests|GSM8K|MBPP|HumanEval)/',k):keys.add(k)
                if k in ('id','input_id','task_id','text_sha256','prompt_text_sha256','prompt_ids_sha256','input_ids_sha256'):
                    if isinstance(v,str):keys.add(v)
                    elif isinstance(v,list):keys.update(s for s in v if isinstance(s,str))
                if k in ('description','question','problem','raw_prompt','prompt','formatted_prompt','text') and isinstance(v,str):keys.add(hashlib.sha256(v.strip().encode()).hexdigest())
                if k in ('prompt_ids','input_ids','token_ids') and isinstance(v,list) and v:
                    if all(type(n)is int for n in v):keys.add(digest(v))
                    elif all(isinstance(n,str) for n in v):keys.update(v)
                walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    recovery=root/'rtx159-readonly';need(read(recovery/'EXPOSURE_READBACK.json')['status']=='VERIFIED','published RTX159 evidence readback')
    for f in read(recovery/'EXPOSURE_SELECTION.json'):
        p=recovery/'restored'/f['path'];need(sha(p)==f['sha256'],'published input metadata drift')
        data=p.read_text(encoding='utf-8');walk([json.loads(l) for l in data.splitlines() if l.strip()] if p.suffix=='.jsonl' else json.loads(data));inventory.append({'path':str(p),'sha256':sha(p)})
    p=root/'research/EXPOSURE.jsonl'
    for line in p.read_text(encoding='utf-8').splitlines():walk(json.loads(line))
    inventory.append({'path':str(p),'sha256':sha(p),'mutable_after_review':True,'scope':'All later engineering uses only the same already excluded development IDs until a newly sealed panel'})
    exclusion=root/'rtx-pool-exclusion-00/EXCLUSION.json';keys.update(read(exclusion)['keys'])
    pins=[root/'exposure-scan-01/REPORT.json',root/'exposure-scan-01/EXPOSURES.json',recovery/'EXPOSURE_READBACK.json',recovery/'FULL_RAW_ACCESS.json',exclusion,root/'rtx162-readonly/PR_EXPOSURE_SNAPSHOT.json']
    counts=collections.Counter()
    for x in read(root/'natural-pool-00/POOL.json')['inputs']:
        if not any(k in keys for k in (x['id'],x['text_sha256'],digest(x['prompt_ids']))):counts[x['domain']+'/'+x['stratum']]+=1
    need(set(counts)=={'code/short','code/long','math/short','math/long'} and min(counts.values())>=6,'insufficient untouched natural strata')
    write(out,{'complete':True,'platforms':['RTX','B570'],'unresolved_sources':[],'utc':utc(),'keys':sorted(keys),'scope':'All reachable local Git input artifacts, retained B570 host manifests, recovered cross-platform historical evidence, every selected input/exposure member in the authenticated RTX159 release, and the entire pinned APPS/test plus MATH/test superset of ongoing RTX162 pool. Conservative exclusions may include tasks that were tokenized but never executed.','source_reports':[{'path':str(p),'sha256':sha(p)} for p in pins],'supplemental_inventory':inventory,'eligible_strata_counts_no_selection':dict(counts),'panel_selected':False,'rtx_runtime_modified':False})
    print('EXPOSURE_REVIEW_COMPLETE',dict(counts),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);a=p.parse_args();combine(a.root,a.out)
