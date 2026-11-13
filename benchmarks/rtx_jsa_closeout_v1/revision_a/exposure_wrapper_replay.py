"""Bounded-memory host audit, reusing the complete cryptographic Git catalog."""
import base64
import collections
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tarfile
import tempfile
import threading
import time
import zipfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
WORK=REPO.parent
sys.path.insert(0,str(WORK/'cpu-deps'))
import ahocorasick
import ijson
import psutil
from exposure_v2 import normalize,TEXT,SKIP

LIMIT=8*1024**2
def read(path):return json.loads(path.read_bytes())
def digest(data):return hashlib.sha256(data).hexdigest()
def file_hash(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())

def main():
    out=WORK/'amended-host-wrapper-replay';out.mkdir(exist_ok=False)
    start=time.monotonic();stop=threading.Event()
    def watch():
        while not stop.wait(2):
            rss=psutil.Process().memory_info().rss
            if rss>16*1024**3 or time.monotonic()-start>3600:
                save(out/'RESOURCE_STOP.json',{'rss_bytes':rss,'seconds':time.monotonic()-start,'model_requests':0});os._exit(2)
    threading.Thread(target=watch,daemon=True).start()
    gitroot=WORK/'amended-git-complete';git=read(gitroot/'AUDIT.json');equivalence=read(HERE/'HISTORICAL_ARCHIVE_EQUIVALENCE.json')
    damaged={item['damaged_sha256']:item['canonical_sha256'] for item in equivalence['archives']}
    prefix_equivalence=read(HERE/'TRUNCATED_ARCHIVE_EQUIVALENCE.json')
    damaged[prefix_equivalence['damaged_sha256']]=prefix_equivalence['canonical_sha256']
    covered_errors={item['damaged_blob_oid'] for item in equivalence['archives']}
    if any(error['path'].split(':')[1] not in covered_errors for error in git['errors']):raise ValueError('unresolved Git audit errors')
    seen={row['sha256'] for row in read(gitroot/'CATALOG.json')}
    archive_seen={row['sha256'] for row in git['archives']}
    prep=read(HERE/'PREP_REGISTRATION.json');old=WORK/'s0-static-census';new=Path(prep['output'])
    tasks=read(old/'NATURAL_TASKS.json')+read(new/'NATURAL_TASKS.json');descriptions={task['id']:task['description'] for task in tasks}
    patterns=collections.defaultdict(set)
    for ident,text in descriptions.items():patterns[normalize(text)].add(ident)
    auto=ahocorasick.Automaton()
    for text,ids in patterns.items():auto.add_word(text,sorted(ids))
    auto.make_automaton();max_pattern=max(map(len,patterns))
    regexp=re.compile(r'\b(?:MBPP[/_\-](\d{1,4})|GSM8K/test/(\d{1,4})|CodeContests/valid/(\d{1,4}))\b',re.I)
    token_lookup=collections.defaultdict(set)
    for family in ['Qwen','SmolLM2','Llama']:
        with (old/(family+'-target.stdout.jsonl')).open('rb') as stream:
            next(stream)
            for line in stream:
                row=json.loads(line);token_lookup[digest(json.dumps(row['prompt_ids'],separators=(',',':')).encode())].add(row['task_id'])
    for row in read(new/'NATIVE_INPUTS.json'):token_lookup[digest(json.dumps(row['prompt_ids'],separators=(',',':')).encode())].add(row['id'])
    whitelist={file_hash(path) for root in [old,new] for path in root.iterdir() if path.is_file()}
    whitelist.update(file_hash(HERE/name) for name in ['CODECONTESTS_VALID_DESCRIPTIONS.json','PREP_REGISTRATION.json','AMENDMENT.md','AUTHOR_AUTHORIZATION.json'])
    oldplan=read(REPO/'benchmarks/rtx_jsa_closeout_v1/S0_CENSUS_PLAN.json')
    whitelist.update(oldplan['files'][key]['sha256'] for key in ['mbpp','gsm8k'])
    exclusions=set(git['excluded_ids']);hits={};errors=[];counts=collections.Counter();archives=[]
    catalog=(out/'FILE_RECEIPTS.jsonl').open('xb')
    def match(text):
        found={('MBPP/'+m[1] if m[1] else 'GSM8K/test/'+m[2] if m[2] else 'CodeContests/valid/'+m[3]) for m in regexp.finditer(text)}
        for _,ids in auto.iter(normalize(text)):found.update(ids)
        return found & descriptions.keys()
    def record(found,label,h):
        for ident in found:
            exclusions.add(ident)
            if len(hits.setdefault(ident,[]))<8:hits[ident].append({'path':label,'sha256':h})
    def strings(obj):
        if isinstance(obj,str):yield obj
        elif isinstance(obj,list):
            for item in obj:yield from strings(item)
        elif isinstance(obj,dict):
            for key,value in obj.items():yield str(key);yield from strings(value)
    def inspect_object(obj,label,h):
        if isinstance(obj,dict):
            if obj.get('vocab_only') is True and obj.get('forward_calls')==0:return
            if obj.get('encoding')=='base64' and isinstance(obj.get('content'),str):
                inspect_bytes(base64.b64decode(obj['content']),label+'!base64');return
            if isinstance(obj.get('files'),dict) and all(isinstance(v,dict) and 'sha256' in v for v in obj['files'].values()):return
            if ('description_matches' in obj and 'project_records' in obj) or ('descriptions' in obj and 'identifiers' in obj):return
            if 'eligible_pool' in obj or 'eligible_ranked' in obj or ('rows' in obj and any(k in obj for k in ['selected','chosen','eligible_count','known_executed_planned'])):
                obj={k:v for k,v in obj.items() if k in ['selected','chosen','prior_mbpp_executed','known_executed_planned','engineering','formal','reservations','exclusion_reasons']}
            if obj.get('schema')=='heterospec.jsa.b570.coordination.v1':obj={k:v for k,v in obj.items() if k!='remaining_ranked_candidates'}
        if isinstance(obj,list) and len(obj)==427 and all(isinstance(v,dict) and 'task_id' in v and 'prompt' in v for v in obj):
            if all(descriptions.get('MBPP/'+str(v['task_id']))==v['prompt'] for v in obj):return
        if isinstance(obj,list) and len(obj)==1319 and all(isinstance(v,dict) and 'question' in v and 'answer' in v for v in obj):
            if all(descriptions.get('GSM8K/test/'+str(i))==v['question'] for i,v in enumerate(obj)):return
        record(match('\n'.join(strings(obj))),label,h)
        def vectors(value):
            if isinstance(value,dict):
                for key,item in value.items():
                    if key in ['prompt_ids','tokens','prompt','input_ids'] and isinstance(item,list) and item and len(item)<=1024 and all(type(v)is int for v in item):
                        record(token_lookup.get(digest(json.dumps(item,separators=(',',':')).encode()),()),label,h)
                    elif isinstance(item,(dict,list)):vectors(item)
            elif isinstance(value,list):
                for item in value:
                    if isinstance(item,(dict,list)):vectors(item)
        vectors(obj)
    def stream_json(stream,label,h):
        stack=[];arrays={};root_found=set()
        for prefix,event,value in ijson.parse(stream,multiple_values=True,use_float=True):
            if any(part in ['eligible_pool','eligible_ranked','remaining_ranked_candidates'] for part in prefix.split('.')):continue
            if event=='start_map':stack.append({'found':set(),'vocab_only':False,'forward_calls':None,'encoding':None,'encoded_content':None})
            elif event=='end_map':
                state=stack.pop();found=state['found']
                if state['encoding']=='base64' and state['encoded_content'] is not None:inspect_bytes(base64.b64decode(state['encoded_content']),label+'!deferred-base64')
                if state['vocab_only'] and state['forward_calls']==0:found=set()
                if stack:stack[-1]['found'].update(found)
                else:record(found,label,h)
            elif event in ['string','map_key']:
                if event=='string' and stack and prefix.split('.')[-1]=='encoding':stack[-1]['encoding']=value
                if event=='string' and stack and prefix.split('.')[-1]=='content':stack[-1]['encoded_content']=value
                else:
                    found=match(value)
                    if stack:stack[-1]['found'].update(found)
                    else:root_found.update(found)
            elif event in ['boolean','number'] and stack:
                if prefix.split('.')[-1]=='vocab_only':stack[-1]['vocab_only']=value is True
                if prefix.split('.')[-1]=='forward_calls':stack[-1]['forward_calls']=value
            if event=='start_array' and prefix.split('.')[-1] in ['prompt_ids','prompt','tokens','input_ids']:arrays[prefix]=[]
            if event=='number':
                for owner,items in arrays.items():
                    if prefix==owner+'.item' and len(items)<=1024:items.append(value)
            if event=='end_array' and prefix in arrays:
                items=arrays.pop(prefix)
                if items and len(items)<=1024 and all(type(v)is int for v in items):
                    found=token_lookup.get(digest(json.dumps(items,separators=(',',':')).encode()),())
                    if stack:stack[-1]['found'].update(found)
                    else:root_found.update(found)
        record(root_found,label,h)
    def inspect_stream(stream,size,label,h):
        if h in seen or h in whitelist:return
        seen.add(h);counts['new_text_objects']+=1
        stream.seek(0)
        if size<=LIMIT:
            data=stream.read()
            try:inspect_object(json.loads(data),label,h);return
            except (ValueError,UnicodeError):
                lines=data.splitlines()
                if lines and all(not line.strip() or line.lstrip().startswith(b'{') for line in lines):
                    for line in lines:
                        if line.strip():
                            try:inspect_object(json.loads(line),label,h)
                            except ValueError:record(match(line.decode('utf-8',errors='replace')),label,h)
                    return
                record(match(data.decode('utf-8',errors='replace')),label,h);return
        first=stream.read(4096).lstrip();stream.seek(0)
        if first.startswith((b'{',b'[')):
            try:stream_json(stream,label,h);return
            except (ijson.JSONError,ValueError,OverflowError):stream.seek(0)
        import codecs
        decoder=codecs.getincrementaldecoder('utf-8')(errors='replace');tail=''
        while True:
            chunk=stream.read(1024*1024)
            if not chunk:break
            text=tail+decoder.decode(chunk);record(match(text),label,h);tail=text[-max_pattern*2:]
    def inspect_bytes(data,label):
        h=digest(data)
        if h in seen or h in whitelist:return
        if data.startswith((b'PK\x03\x04',b'\x1f\x8b')):visit_archive(io.BytesIO(data),label,h,len(data))
        else:inspect_stream(io.BytesIO(data),len(data),label,h)
    def member(stream,size,label):
        with tempfile.SpooledTemporaryFile(max_size=LIMIT,dir='D:/') as temporary:
            hasher=hashlib.sha256()
            while True:
                block=stream.read(1024*1024)
                if not block:break
                hasher.update(block);temporary.write(block)
            actual_size=temporary.tell();temporary.seek(0);head=temporary.read(16);temporary.seek(0)
            if size and actual_size!=size:raise ValueError('truncated archive member')
            if head.startswith((b'PK\x03\x04',b'\x1f\x8b')):visit_archive(temporary,label,hasher.hexdigest(),actual_size)
            else:inspect_stream(temporary,actual_size,label,hasher.hexdigest())
    def visit_archive(source,label,h,size):
        if h in archive_seen:return
        if h in damaged:
            if damaged[h] not in archive_seen:raise ValueError('canonical archive was not audited')
            archives.append({'path':label,'sha256':h,'status':'EXACT_TRANSPORT_EQUIVALENCE_TO_AUDITED_CANONICAL'});return
        archive_seen.add(h)
        if zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as archive:
                for item in archive.infolist():
                    if not item.is_dir() and Path(item.filename).suffix.lower() in TEXT|{'.zip','.gz'}:
                        with archive.open(item) as stream:member(stream,item.file_size,label+'!'+item.filename)
        else:
            if isinstance(source,Path):source_handle=source.open('rb')
            else:source.seek(0);source_handle=source
            head=source_handle.read(16);source_handle.seek(0)
            if head.startswith(b'PK^C^D') and size<100:inspect_stream(source_handle,size,label+'!failed-transport-literal',h)
            elif head.startswith(b'\x1f\x8b'):
                try:
                    with tarfile.open(fileobj=source_handle,mode='r:gz') as archive:
                        for item in archive:
                            if item.isfile() and Path(item.name).suffix.lower() in TEXT|{'.zip','.gz'}:
                                with archive.extractfile(item) as stream:member(stream,item.size,label+'!'+item.name)
                except tarfile.ReadError:
                    source_handle.seek(0)
                    with gzip.GzipFile(fileobj=source_handle,mode='rb') as stream:member(stream,0,label+'!gzip-text')
            else:inspect_stream(source_handle,size,label+'!literal',h)
            if isinstance(source,Path):source_handle.close()
        archives.append({'path':label,'sha256':h,'bytes':size})
    roots=[Path('C:/Users/ASUS/Documents/Codex'),Path('D:/HeteroSpec-PC'),Path('D:/HeteroSpec-RTX-Target-V1')]
    roots += [p for p in Path('D:/').iterdir() if p.is_dir() and p.name.startswith('hs')]
    own={str(WORK.parent).casefold(),read(HERE/'STORAGE_BINDING.json')['storage_root'].replace('/','\\').casefold()}
    def paths():
        for record in read(WORK/'amended-host-resume/LARGE_TEXT_REPLAY.json'):
            yield Path('HOST_WRAPPER_REPLAY'),Path(record['path'])
    def load(path):
        try:return path.stat().st_size,file_hash(path),None
        except OSError as error:return 0,None,repr(error)
    progress=time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending=collections.deque()
        def collect(root,path,future):
            nonlocal progress
            size,h,error=future.result();counts['host_files']+=1
            catalog.write((json.dumps({'path':str(path),'bytes':size,'sha256':h,'error':error})+'\n').encode())
            if error:errors.append({'path':str(path),'error':error})
            else:
                try:
                    if path.suffix.lower() in TEXT:
                        if h not in seen and h not in whitelist:
                            with path.open('rb') as stream:inspect_stream(stream,size,str(path),h)
                    else:visit_archive(path,str(path),h,size)
                except Exception as failure:errors.append({'path':str(path),'error':repr(failure)})
            if time.monotonic()-progress>15:
                print('HOST_STREAM',counts['host_files'],'new',counts['new_text_objects'],'excluded',len(exclusions),'errors',len(errors),'RSS_MiB',round(psutil.Process().memory_info().rss/1024**2),str(root),flush=True)
                save(out/'PROGRESS.json',{'counts':dict(counts),'excluded_ids':sorted(exclusions),'errors':errors,'current_path':str(path)});progress=time.monotonic()
        for root,path in paths():
            pending.append((root,path,pool.submit(load,path)))
            if len(pending)>=4:collect(*pending.popleft())
        while pending:collect(*pending.popleft())
    catalog.close();stop.set()
    result={'status':'PASS' if not errors else 'AUDIT_INCOMPLETE','excluded_ids':sorted(exclusions),'matches':hits,'errors':errors,
            'host_counts':dict(counts),'host_roots':list(map(str,roots)),'owned_seconds':time.monotonic()-start,
            'complete_Git_audit_sha256':file_hash(gitroot/'AUDIT.json'),'canonical_archive_equivalence_sha256':file_hash(HERE/'HISTORICAL_ARCHIVE_EQUIVALENCE.json'),
            'file_receipts_sha256':file_hash(out/'FILE_RECEIPTS.jsonl'),'unresolved_text_objects':[], 'unresolved_archive_objects':[],
            'memory_ceiling_bytes':16*1024**3,'wall_safety_ceiling_seconds':3600,
            'unknown_history':'Other private hosts and unreachable force-pushed states unavailable; no pretraining-unseen claim'}
    save(out/'AUDIT.json',result);print('HOST_STREAM_COMPLETE',result['status'],dict(counts),len(exclusions),flush=True)

if __name__=='__main__':main()
