"""Audit accessible histories and tokenize descriptions with zero model forwards."""
import json,hashlib,re,os,subprocess,collections
from pathlib import Path
ROOT=Path(__file__).parent
WORKTREE=Path('C:/Users/DIANG/.codex/worktrees/b570-closeout-v1/HeteroSpec')
ORIGINAL=Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 p=Path(p)
 if p.exists():raise RuntimeError('Refuse to overwrite '+str(p))
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
corpus=ROOT/'dependencies/corpus/sanitized-mbpp.json'
assert sha(corpus)=='ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9'
data=read(corpus);assert len(data)==427
prior=read(ROOT/'dependencies/8dfa60a/EXPOSURE_SUMMARY.json');shared=read(ROOT/'dependencies/RTX/B_INPUTS.json')
allowed=set(prior['eligible_ranked'])-{r['id'] for r in shared}
known={'MBPP/'+str(i) for i in prior['prior_mbpp_executed']}|{r['id'] for r in shared}
patterns={}
for r in data:
 for b in [r['prompt'].encode(),json.dumps(r['prompt'],ensure_ascii=True)[1:-1].encode()]:patterns.setdefault(b,set()).add(r['task_id'])
rx=re.compile(b'|'.join(re.escape(b) for b in sorted(patterns,key=len,reverse=True)))
ids=re.compile(rb'\bMBPP[/_-](\d{1,4})\b',re.I)
suffixes={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.tex','.cpp','.h','.py'}
skip={'.git','__pycache__','models','tools','vendor','third_party','node_modules','datasets','build','capsule','remote-parts'}
catalog={};hits={};seen=set();errors=[]
roots=[ORIGINAL,WORKTREE,Path('C:/hs/b570-prefill-v1'),Path('C:/Users/DIANG/.codex/worktrees/b570-partition-intervention-v1/HeteroSpec')]
for root in roots:
 for d,dirs,files in os.walk(root):
  dirs[:]=[n for n in dirs if n not in skip and not n.startswith('.venv')]
  for name in files:
   p=Path(d)/name
   if p.suffix.lower() not in suffixes or p.stat().st_size>128*1024*1024:continue
   try:b=p.read_bytes()
   except OSError as e:errors.append({'path':str(p),'error':str(e)});continue
   h=hashlib.sha256(b).hexdigest();catalog[str(p)]={'sha256':h,'bytes':len(b)}
   if h in seen:continue
   seen.add(h)
   if h==sha(corpus):continue
   if b'"forward_calls": 0' in b and b'"vocab_only": true' in b and not any(k in b for k in [b'generated_ids',b'original_reference_ids',b'accepted_ids']):continue
   for m in ids.finditer(b):hits.setdefault('MBPP/'+m.group(1).decode(),[]).append(str(p))
   for m in rx.finditer(b):
    for tid in patterns[m.group(0)]:hits.setdefault('MBPP/'+str(tid),[]).append(str(p))
 print('audited',root,'records',len(catalog),'matched ids',len(hits),flush=True)
assert not errors,errors
counts=collections.Counter(r['task_id'] for r in data);descs=collections.Counter(r['prompt'] for r in data)
rows=[];eligible=[]
for r in data:
 task='MBPP/'+str(r['task_id']);reasons=[]
 if task not in allowed:reasons.append('not_in_inherited_conservative_eligible_pool_after_shared_exclusion')
 if task in known:reasons.append('known_project_execution')
 if task in hits:reasons.append('accessible_execution_inspection_or_ambiguous_record')
 if counts[r['task_id']]!=1 or descs[r['prompt']]!=1:reasons.append('duplicate_id_or_description')
 row={'id':task,'exclusions':reasons,'evidence':hits.get(task,[])[:10],'description_sha256':hashlib.sha256(r['prompt'].encode()).hexdigest(),'selection_hash':hashlib.sha256((task+'HeteroSpec-B570-Closeout-Unused-v1').encode()).hexdigest()}
 rows.append(row)
 if not reasons:
  raw='Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n'+r['prompt']
  formatted='<|im_start|>user\n'+raw+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
  eligible.append(dict(row,raw_prompt=raw,formatted_prompt=formatted,formatted_prompt_sha256=hashlib.sha256(formatted.encode()).hexdigest(),cohort='project_unused_within_accessible_audit'))
eligible.sort(key=lambda r:(r['selection_hash'],r['id']))
save(ROOT/'EXPOSURE_CATALOG.json',catalog)
save(ROOT/'EXPOSURE_AUDIT.json',{'status':'PASS','roots':[str(p) for p in roots],'records':len(catalog),'unique_texts':len(seen),'rows':rows,'eligible_ranked':[r['id'] for r in eligible],'known_executed':sorted(known),'inherited_prior_receipt_sha256':sha(ROOT/'dependencies/8dfa60a/EXPOSURE_SUMMARY.json'),'limitations':['RTX machine-local bulk histories unavailable on B570: inherited fixed receipt and accessible PR59/60/62 inputs examined; not independently rescanned','Unused means project execution within accessible audited history, not model training'],'new_task_forward_calls':0})
long=[r for r in read(ROOT/'dependencies/b0dfa0f/COST_INPUTS.json') if r['id'] in ['HumanEval/49','HumanEval/81','HumanEval/31']]
if len(long)!=3:
 old=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/evaluation/HISTORICAL_EXPECTED.json'))
 inputs=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json'))
 tasks=list(inputs)
 def rank(t):return hashlib.sha256((t+'HeteroSpec-B570-Closeout-Long-v1').encode()).hexdigest()
 caplimited=sorted([t for t in tasks if old[t+'/R/1']['endpoint']=='CAP128'],key=lambda t:(rank(t),t))
 rest=sorted([t for t in tasks if t not in caplimited],key=lambda t:(-len(old[t+'/R/1']['ids']),rank(t),t))
 long=[{'id':t,'formatted_prompt':Path(inputs[t]['text']).read_text(encoding='utf-8'),'prompt_ids':read(inputs[t]['ids']),'input_origin':'old B570 byte-bound prompt','cohort':'exposed_long_supplement'} for t in (caplimited+rest)[:3]]
else:
 for r in long:
  for k in list(r):
   if k not in ['id','formatted_prompt','cap']:del r[k]
  r['cohort']='exposed_long_supplement';r['input_origin']='RTX PR59 frozen COST_INPUTS descriptions and wrapper; no RTX reference retained'
token_inputs=shared+eligible+long
exe=ROOT/'tokenizer-bin/Release/b570-tokenizer.exe'
stderr=(ROOT/'TOKENIZATION.stderr.log').open('wb')
request=''.join(json.dumps({'id':r['id'],'formatted_prompt':r['formatted_prompt']})+'\n' for r in token_inputs).encode()
result=subprocess.run([str(exe),str(ORIGINAL/'models/gguf/Qwen3-8B-Q8_0.gguf')],input=request,stdout=subprocess.PIPE,stderr=stderr,check=True,timeout=120);stderr.close()
(ROOT/'TOKENIZATION.stdout.jsonl').write_bytes(result.stdout)
tokens=[json.loads(s) for s in result.stdout.decode().splitlines()];identity=tokens.pop(0);byid={r['id']:r['prompt_ids'] for r in tokens};assert all(r['forward_calls']==0 for r in tokens)
for r in token_inputs:
 if 'prompt_ids' in r:assert r['prompt_ids']==byid[r['id']],r['id']
 r['prompt_ids']=byid[r['id']];assert len(r['prompt_ids'])+512+12<=1024
 r['formatted_prompt_sha256']=hashlib.sha256(r['formatted_prompt'].encode()).hexdigest()
for r in shared:r['cohort']='cross_platform_shared_project_exposed'
save(ROOT/'TOKENIZATION_PROOF.json',dict(identity,vocab_only=True,tokenizer_sha256=sha(exe),source_sha256=sha(ROOT/'tokenizer.cpp'),stdout_sha256=sha(ROOT/'TOKENIZATION.stdout.jsonl'),models_sha256=sha(ORIGINAL/'models/gguf/Qwen3-8B-Q8_0.gguf')))
save(ROOT/'INPUT_CANDIDATES.json',{'shared':shared,'eligible_unused':eligible,'long':long})
print({'shared':len(shared),'eligible_unused':len(eligible),'long':[r['id'] for r in long],'forward_calls':0},flush=True)
