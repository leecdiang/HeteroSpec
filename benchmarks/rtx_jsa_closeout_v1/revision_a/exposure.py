"""Read-only reachable-history and accessible archive exposure audit before selection."""
import base64
import collections
import hashlib
import gzip
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time
import unicodedata
import zipfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
WORK=REPO.parent
sys.path.insert(0,str(WORK/'cpu-deps'))
import ahocorasick

TEXT={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.py','.toml','.cpp','.h','.hpp','.tex','.ps1','.bib','.sh','.wire','.stdout','.stderr','.b64','.base64','.diff','.patch'}
SKIP={'.git','__pycache__','node_modules','vendor','third_party','models','tools','hf-cache','datasets','env','python311','source','build','bin','dependencies','site-packages','cpu-deps','amended-native','source-preparation','history-preparation'}

def sha(data):return hashlib.sha256(data).hexdigest()
def normalize(text):return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())
def read(path):return json.loads(path.read_bytes())
def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')

def main():
    out=WORK/(sys.argv[1] if len(sys.argv)>1 else 'amended-exposure');out.mkdir(exist_ok=False)
    prep=read(HERE/'PREP_REGISTRATION.json')
    fresh=Path(prep['output'])
    old=WORK/'s0-static-census'
    tasks=read(old/'NATURAL_TASKS.json')+read(fresh/'NATURAL_TASKS.json')
    descriptions={t['id']:t['description'] for t in tasks}
    auto=ahocorasick.Automaton()
    patterns=collections.defaultdict(set)
    for ident,text in descriptions.items():patterns[normalize(text)].add(ident)
    for text,ids in patterns.items():auto.add_word(text,sorted(ids))
    auto.make_automaton()
    regexp=re.compile(r'\b(?:MBPP[/_\-](\d{1,4})|GSM8K/test/(\d{1,4})|CodeContests/valid/(\d{1,4}))\b',re.I)
    prior=read(WORK/'history-preparation/PR89_HISTORY_AUDIT.json')
    exclusions=set(prior['excluded_ids']);hits={};errors=[];catalog=[];availability=[];archives=[];seen=set();archive_seen=set();counts=collections.Counter()
    whitelist={sha(p.read_bytes()) for root in [old,fresh] for p in root.iterdir() if p.is_file()}
    whitelist.update(sha((HERE/name).read_bytes()) for name in ['CODECONTESTS_VALID_DESCRIPTIONS.json','PREP_REGISTRATION.json','AUTHOR_AUTHORIZATION.json','AMENDMENT.md','DATASET_CARD.md'])
    for key in ['mbpp','gsm8k']:
        plan=read(REPO/'benchmarks/rtx_jsa_closeout_v1/S0_CENSUS_PLAN.json');whitelist.add(plan['files'][key]['sha256'])
    token_lookup=collections.defaultdict(set)
    for f in ['Qwen','SmolLM2','Llama']:
        for line in (old/(f+'-target.stdout.jsonl')).read_bytes().splitlines()[1:]:
            row=json.loads(line);token_lookup[sha(json.dumps(row['prompt_ids'],separators=(',',':')).encode())].add(row['task_id'])
    for row in read(fresh/'NATIVE_INPUTS.json'):
        token_lookup[sha(json.dumps(row['prompt_ids'],separators=(',',':')).encode())].add(row['id'])
    def strings(obj):
        if isinstance(obj,str):yield obj
        elif isinstance(obj,list):
            for item in obj:yield from strings(item)
        elif isinstance(obj,dict):
            for key,value in obj.items():yield str(key);yield from strings(value)
    def vectors(obj):
        if isinstance(obj,dict):
            for key,value in obj.items():
                if key in ('prompt_ids','tokens','prompt') and isinstance(value,list) and value and all(type(v)is int for v in value):
                    yield sha(json.dumps(value,separators=(',',':')).encode())
                elif isinstance(value,(dict,list)):yield from vectors(value)
        elif isinstance(obj,list):
            for value in obj:
                if isinstance(value,(dict,list)):yield from vectors(value)
    def scan(data,label):
        h=sha(data);counts['logical_objects']+=1
        if h in seen:return
        seen.add(h);catalog.append({'path':label,'sha256':h,'bytes':len(data)})
        if h in whitelist:availability.append({'path':label,'reason':'pinned complete corpus or zero-forward inventory','sha256':h});return
        text=data.decode('utf-8',errors='replace')
        try:obj=json.loads(text)
        except ValueError:obj=None
        if isinstance(obj,dict):
            if obj.get('vocab_only') is True and obj.get('forward_calls')==0:return
            if obj.get('encoding')=='base64' and isinstance(obj.get('content'),str):
                scan(base64.b64decode(obj['content']),label+'!base64');return
            if isinstance(obj.get('files'),dict) and all(isinstance(v,dict) and 'sha256' in v for v in obj['files'].values()):return
            if ('description_matches' in obj and 'project_records' in obj) or ('descriptions' in obj and 'identifiers' in obj):return
            if 'eligible_pool' in obj or 'eligible_ranked' in obj or ('rows' in obj and any(k in obj for k in ['selected','chosen','eligible_count','known_executed_planned'])):
                obj={k:v for k,v in obj.items() if k in ['selected','chosen','prior_mbpp_executed','known_executed_planned','engineering','formal','reservations','exclusion_reasons']}
            if obj.get('schema')=='heterospec.jsa.b570.coordination.v1':obj={k:v for k,v in obj.items() if k!='remaining_ranked_candidates'}
        if re.search(r'"vocab_only"\s*:\s*true',text) and re.search(r'"forward_calls"\s*:\s*0',text) and not re.search(r'"(?:original_reference_ids|generated_ids|tokens_predicted|output)"\s*:',text):return
        if isinstance(obj,list) and len(obj)==427 and all(isinstance(v,dict) and 'task_id' in v and 'prompt' in v for v in obj):return
        if obj is not None:text='\n'.join(strings(obj))
        found=set()
        for match in regexp.finditer(text):found.add('MBPP/'+match[1] if match[1] else 'GSM8K/test/'+match[2] if match[2] else 'CodeContests/valid/'+match[3])
        for _,ids in auto.iter(normalize(text)):found.update(ids)
        if obj is not None:
            for hsh in vectors(obj):found.update(token_lookup.get(hsh,()))
        for ident in found:
            if ident not in descriptions:continue
            exclusions.add(ident)
            if len(hits.setdefault(ident,[]))<8:hits[ident].append({'path':label,'sha256':h})
    archive_oids=set()
    def archive(data,label):
        h=sha(data);archive_oids.add(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())
        if h in archive_seen:return
        archive_seen.add(h)
        if zipfile.is_zipfile(io.BytesIO(data)):
            with zipfile.ZipFile(io.BytesIO(data)) as source:
                for item in source.infolist():
                    if item.is_dir():continue
                    suffix=Path(item.filename).suffix.lower()
                    if suffix in TEXT:scan(source.read(item),label+'!'+item.filename)
                    elif suffix in {'.zip','.gz'}:archive(source.read(item),label+'!'+item.filename)
        elif data.startswith(b'\x1f\x8b'):
            try:
                with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as source:
                    for item in source:
                        if item.isfile() and Path(item.name).suffix.lower() in TEXT:scan(source.extractfile(item).read(),label+'!'+item.name)
            except tarfile.ReadError:
                scan(gzip.decompress(data),label+'!gzip-plaintext')
        else:
            text=data.decode('utf-8')
            if data.startswith(b'PK^C^D') and len(data)<100:
                scan(data,label+'!historical-failed-transport-literal')
                archives.append({'path':label,'sha256':h,'bytes':len(data),'status':'HISTORICAL_FAILED_TRANSPORT_LITERAL_NOT_ARCHIVE'})
                return
            if data.startswith(b'PK') or '\x00' in text:raise ValueError('invalid archive: '+label)
            scan(data,label+'!plain-text')
        archives.append({'path':label,'sha256':h,'bytes':len(data)})
    objects=read(WORK/'history-preparation/ALL_REACHABLE_BLOBS.json')
    env=dict(os.environ,GIT_NO_LAZY_FETCH='1')
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=REPO,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    git_archives=[]
    for i,(oid,name) in enumerate(objects['objects'].items()):
        suffix=Path(name).suffix.lower()
        if suffix not in TEXT and suffix not in {'.zip','.gz','.xz'}:continue
        process.stdin.write((oid+'\n').encode());process.stdin.flush();header=process.stdout.readline().decode().strip().split()
        if len(header)<3:
            if suffix in TEXT:errors.append({'path':'gitblob:'+oid+':'+name,'error':'missing text object'})
            else:git_archives.append({'oid':oid,'path':name,'available':False})
            continue
        size=int(header[2]);data=process.stdout.read(size);process.stdout.read(1)
        if suffix in TEXT:scan(data,'gitblob:'+oid+':'+name)
        else:
            git_archives.append({'oid':oid,'path':name,'available':True,'sha256':sha(data)})
            try:archive(data,'gitblob:'+oid+':'+name)
            except (ValueError,EOFError,zipfile.BadZipFile,tarfile.TarError) as error:errors.append({'path':'gitblob:'+oid+':'+name,'error':repr(error)})
        if i%1000==0:print('git objects',i,'excluded',len(exclusions),flush=True)
    process.stdin.close();process.wait(timeout=30)
    save(out/'GIT_ARCHIVES.json',git_archives)
    roots=[Path('C:/Users/ASUS/Documents/Codex'),Path('D:/HeteroSpec-PC'),Path('D:/HeteroSpec-RTX-Target-V1')]
    roots.extend(p for p in Path('D:/').iterdir() if p.is_dir() and p.name.startswith(('hs','HeteroSpec')) and p not in roots)
    progress=time.monotonic()
    for root in roots:
        for directory,dirs,names in os.walk(root):
            current=Path(directory)
            dirs[:]=[d for d in dirs if d not in SKIP and not d.startswith('.venv') and (current/d).resolve()!=WORK.parent]
            for name in names:
                path=current/name;suffix=path.suffix.lower()
                if suffix not in TEXT and suffix not in {'.zip','.gz'}:continue
                try:
                    data=path.read_bytes()
                    if suffix in TEXT:scan(data,str(path))
                    else:archive(data,str(path))
                except (OSError,ValueError,EOFError,zipfile.BadZipFile,tarfile.TarError) as error:errors.append({'path':str(path),'error':repr(error)})
                if time.monotonic()-progress>20:
                    print('host objects',counts['logical_objects'],'exclusions',len(exclusions),'errors',len(errors),flush=True);progress=time.monotonic()
    unresolved=[a for a in git_archives if not a['available'] and a['oid'] not in archive_oids]
    save(out/'UNRESOLVED_GIT_ARCHIVES.json',unresolved)
    save(out/'CATALOG.json',catalog)
    save(out/'AUDIT.json',{'status':'PASS' if not errors else 'AUDIT_INCOMPLETE','excluded_ids':sorted(exclusions),'matches':hits,'errors':errors,
         'git_root_trees':len(objects['root_trees']),'git_unique_blob_objects':len(objects['objects']),
         'catalog_sha256':sha((out/'CATALOG.json').read_bytes()),'counts':dict(counts),'archives':archives,'availability':availability,
         'prior_audit':'PR89 complete audit retained; this increment also scans prior contents for the new source',
         'unknown_history':'Other private hosts and unreachable force-pushed objects cannot be inspected; no pretraining-unseen claim'})

if __name__=='__main__':main()
