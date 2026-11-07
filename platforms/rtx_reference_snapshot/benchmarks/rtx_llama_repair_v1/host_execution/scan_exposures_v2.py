"""Conservative exposure union from reachable Git input artifacts and retained host manifests."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    ids,texts,tokens=set(),set(),set();inventory=[];errors=[];placeholders=[]
    pattern=re.compile(r'(input|panel|exposure|calibration|plan|requests|references|freeze|manifest)',re.I)
    excluded=re.compile(r'(RAW_FILE|SOURCE_FILE|ARTIFACT_MANIFEST|FILE_MANIFEST|SOURCE_MEMBERS)',re.I)
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if re.match(r'^(APPS|MATH|CodeContests|GSM8K|MBPP|HumanEval)/',k):ids.add(k)
                if k in ('id','input_id','task_id') and isinstance(v,str):ids.add(v)
                if k in ('description','question','problem','raw_prompt','prompt','formatted_prompt','text') and isinstance(v,str):texts.add(sha(v.strip().encode()))
                if k in ('text_sha256','prompt_text_sha256'):
                    if isinstance(v,str):texts.add(v)
                    elif isinstance(v,list):texts.update(n for n in v if isinstance(n,str))
                if k in ('prompt_ids_sha256','input_ids_sha256'):
                    if isinstance(v,str):tokens.add(v)
                    elif isinstance(v,list):tokens.update(n for n in v if isinstance(n,str))
                if k in ('prompt_ids','input_ids','token_ids') and isinstance(v,list) and v:
                    if all(type(n)is int for n in v):tokens.add(sha(json.dumps(v,separators=(',',':')).encode()))
                    elif k=='input_ids' and all(isinstance(n,str) for n in v):ids.update(v)
                walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    def ingest(data,label):
        item={'source':label,'bytes':len(data),'sha256':sha(data)};inventory.append(item)
        try:
            if label.lower().endswith('.jsonl'):
                for line in data.splitlines():
                    if line.strip():walk(json.loads(line))
            else:walk(json.loads(data))
        except Exception as exc:
            if data.strip() in (b'CPU_FIXTURE_NO_GPU_AUTHORITY',b'CPU_FIXTURE_NOT_GPU_AUTHORIZED',b''):
                placeholders.append(dict(item,reason='Explicit non-execution fixture or empty artifact',text=data.decode()))
            else:errors.append(dict(item,error=str(exc),prefix=data[:200].decode('utf-8',errors='replace')))
    objects={}
    listing=subprocess.check_output(['git','log','--all','--raw','--no-abbrev','--format=','--no-renames','--root','--full-history','-m','--','*.json','*.jsonl'],cwd=a.repo,text=True,encoding='utf-8',timeout=120)
    (a.out/'GIT_RAW_HISTORY.txt').write_text(listing,encoding='utf-8')
    for line in listing.splitlines():
        if not line.startswith(':'):continue
        meta,path=line.split('\t',1)
        if pattern.search(Path(path).name) and not excluded.search(Path(path).name):
            for oid in meta.split()[2:4]:
                if set(oid)!={'0'}:objects[oid]=path
    listing=subprocess.check_output(['git','rev-list','--objects','--all','--missing=print'],cwd=a.repo,text=True,encoding='utf-8',timeout=120)
    missing={line[1:] for line in listing.splitlines() if line.startswith('?')}
    selected=sorted(set(objects)&missing)
    (a.out/'MISSING_SELECTED.txt').write_text('\n'.join(selected)+'\n')
    if selected:
        command=['git','-c','http.version=HTTP/1.1','-c','fetch.negotiationAlgorithm=noop','fetch','--no-tags','--no-write-fetch-head','--filter=blob:none','origin','--stdin']
        fetched=subprocess.run(command,input='\n'.join(selected)+'\n',cwd=a.repo,text=True,capture_output=True,timeout=600)
        (a.out/'fetch.stdout.log').write_text(fetched.stdout);(a.out/'fetch.stderr.log').write_text(fetched.stderr)
        (a.out/'FETCH.json').write_text(json.dumps({'argv':command,'objects':selected,'exit_code':fetched.returncode},indent=2))
        fetched.check_returncode()
    refs=subprocess.check_output(['git','show-ref'],cwd=a.repo,text=True)
    (a.out/'GIT_REFS.txt').write_text(refs)
    (a.out/'GIT_OBJECTS.json').write_text(json.dumps(objects,indent=2))
    for i,(oid,path) in enumerate(objects.items()):
        ingest(subprocess.check_output(['git','cat-file','blob',oid],cwd=a.repo),oid+':'+path)
        if i%200==0:print('git',i,len(objects),flush=True)
    roots=[p for p in Path('D:/').iterdir() if p.is_dir() and p.name.lower().startswith(('hs','rtx'))]
    roots += [Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work'),Path('C:/Users/ASUS/Documents/Codex/2026-10-10/kan/work'),Path('E:/rtx160/research')]
    roots += [Path('D:/HeteroSpec-PC')/name for name in ('runs','benchmarks','reports','artifacts','work','spec','configs')]
    roots=[p for p in roots if p.exists()]
    files=subprocess.check_output(['rg','--files','--hidden','--no-ignore','-g','*.json','-g','*.jsonl',*[str(p) for p in roots]],text=True,encoding='utf-8',stderr=subprocess.DEVNULL).splitlines()
    seen=set()
    for name in files:
        path=Path(name)
        if not pattern.search(path.name) or excluded.search(path.name):continue
        if any(part in ('.venv','site-packages','node_modules','source','core','.git') for part in path.parts):continue
        resolved=str(path.resolve()).lower()
        if resolved in seen:continue
        seen.add(resolved);ingest(path.read_bytes(),str(path))
    exposures=[{'id':s} for s in sorted(ids)]+[{'text_sha256':s} for s in sorted(texts)]+[{'prompt_ids_sha256':s} for s in sorted(tokens)]
    (a.out/'EXPOSURES.json').write_text(json.dumps(exposures,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'coverage_review_complete':not errors,'scope':'All reachable Git input/plan/request/reference/freeze/manifest blobs, not just current branch heads; retained host input manifests and previous exposure catalogs. Tokenized candidate pools without output exposure are not treated as model executions.',
            'roots':[str(p) for p in roots],'counts':{'ids':len(ids),'text_hashes':len(texts),'token_hashes':len(tokens)},
            'inventory':inventory,'errors':errors,'reviewed_placeholders':placeholders}
    (a.out/'REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(report['counts'],'errors',len(errors),'sources',len(inventory))


if __name__=='__main__':main()
