"""Fresh accessible-host task-ID and description audit before any Smol forward."""
from pathlib import Path
import os,re,json,hashlib,collections,time
from prepare import R,REPO,PLAN,load,save,sha
corpus=Path('C:/hs/b570-closeout-v1/dependencies/corpus/sanitized-mbpp.json');dataset=load(corpus);dataset_sha=sha(corpus)
snapshot=load(PLAN/'COORDINATION_SNAPSHOT.json');ranked=snapshot['remaining_ranked_candidates']
known=set(snapshot['rtx_reserved_ids'])
for filename in ['F_CONFIRMATION_INPUTS.json','QWEN_CONFIRMATION_INPUTS.json']:
 known.update(x['id'] for x in load(R/'remote'/filename))
# Explicit inherited public executed panels; downloaded exhaustive corpus alone is availability.
for p in [Path('C:/hs/b570-mechanism-pilot-v1/E_INPUTS.json'),Path('C:/hs/b570-mechanism-pilot-v1/D_INPUTS.json')]:known.update(x['id'] for x in load(p))
counts=collections.Counter(x['task_id'] for x in dataset);desc_counts=collections.Counter(x['prompt'] for x in dataset)
patterns={}
for row in dataset:
 for b in [row['prompt'].encode(),json.dumps(row['prompt'],ensure_ascii=True)[1:-1].encode()]:patterns.setdefault(b,set()).add('MBPP/'+str(row['task_id']))
rx=re.compile(b'|'.join(re.escape(b) for b in sorted(patterns,key=len,reverse=True)));ids=re.compile(rb'\bMBPP[/_-](\d{1,4})\b',re.I)
roots=[REPO,Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec'),Path('C:/Users/DIANG/.codex/worktrees'),Path('C:/hs')]
skip={'.git','__pycache__','models','vendor','third_party','node_modules','datasets','build','candidate-build','tokenizer-bin','tokenizer-build','archive','capsule','remote-parts','candidate-src','candidate-common','b570-direct-id-v1-src','b570-direct-id-v1-build','llama-b10839','b570-prefill-build','b570-partition-intervention-v1-build','b570-mechanism-v08-build','source-history','jsa-b570-run-v1','jsa-b570-v1'}
suffix={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.tex','.py'}
mechanical={'EXPOSURE_AUDIT.json','EXPOSURE_CATALOG.json','EXPOSURE_SUMMARY.json','INPUT_CANDIDATES.json','E_EXPOSURE_AUDIT.json','E_EXPOSURE_CATALOG.json','TOKENIZATION.stdout.jsonl','PR59.json','PR60.json','PR62.json','PR63.json','EXPOSURE_RECHECK.json','E_SELECTION.json'}
catalog={};hits={};seen=set();avail=[];errors=[]
for root in roots:
 for directory,dirs,files in os.walk(root):
  dirs[:]=[n for n in dirs if n not in skip and not n.startswith('.venv')]
  for name in files:
   p=Path(directory)/name
   if p.suffix.lower() not in suffix or p.stat().st_size>128*1024*1024:continue
   # This experiment's unexecuted reservation and code are availability, never reused output.
   if p.is_relative_to(REPO/'benchmarks/jsa_b570_validation_v1') or p.is_relative_to(PLAN):avail.append(str(p));continue
   try:b=p.read_bytes()
   except OSError as e:errors.append(dict(path=str(p),error=str(e)));continue
   h=hashlib.sha256(b).hexdigest();catalog[str(p)]=dict(sha256=h,bytes=len(b))
   if h in seen:continue
   seen.add(h)
   if h==dataset_sha or name in mechanical or (b'"forward_calls": 0' in b and b'"vocab_only": true' in b and not any(k in b for k in [b'generated_ids',b'accepted_ids'])):
    avail.append(str(p));continue
   # Own plan identical mirrors are availability too (tracked source hash validated separately).
   if 'jsa_b570_validation_20261010' in p.parts:avail.append(str(p));continue
   for m in ids.finditer(b):hits.setdefault('MBPP/'+m.group(1).decode(),set()).add(str(p))
   for m in rx.finditer(b):
    for task in patterns[m.group(0)]:hits.setdefault(task,set()).add(str(p))
 print('AUDITED',root,len(catalog),len(hits),flush=True)
assert not errors,errors
rows=[];eligible=[];byid={'MBPP/'+str(x['task_id']):x for x in dataset}
for task in ranked:
 x=byid[task];reasons=[]
 if task in known:reasons.append('known executed/planned/reserved confirmation')
 if task in hits:reasons.append('accessible result/inspection/ambiguous ID or exact description hit')
 if counts[x['task_id']]!=1 or desc_counts[x['prompt']]!=1:reasons.append('duplicate ID or description')
 rank=hashlib.sha256((snapshot['selection_salt']+'|'+task).encode()).hexdigest()
 row=dict(id=task,description_sha256=hashlib.sha256(x['prompt'].encode()).hexdigest(),selection_hash=rank,reasons=reasons,evidence=sorted(hits.get(task,[])))
 rows.append(row)
 if not reasons:eligible.append(dict(id=task,description=x['prompt'],description_sha256=row['description_sha256'],selection_hash=rank,raw_prompt='Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n'+x['prompt']))
assert [x['id'] for x in sorted(rows,key=lambda x:(x['selection_hash'],x['id']))]==ranked
chosen=eligible[:24]
save('EXPOSURE_CATALOG.json',catalog);save('EXPOSURE_AUDIT.json',dict(status='PASS' if len(chosen)==24 else 'INCOMPLETE_EXPOSURE_AUDIT',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),roots=list(map(str,roots)),scanned_files=len(catalog),unique_files=len(seen),dataset_sha256=dataset_sha,known_executed_planned=sorted(known),availability_only=avail,availability_policy='Exact exhaustive corpus, mechanical exposure/candidate tables and proven vocab-only streams do not count as all-task forwards. Own frozen plan is availability; all other ID/description matches exclude conservatively.',rows=rows,eligible_count=len(eligible),chosen=[x['id'] for x in chosen],limitations=['Unknown private remote host bulk not independently rescanned; accessible project evidence and relevant public cohorts excluded.','Not a global project-host or model-training unseen claim.','All result-bearing CAS logical files accessible under restored local study trees were scanned; source-history/binary/model directories excluded from text matches.'],new_smol_forwards=0))
save('CONFIRMATION_RAW_INPUTS.json',chosen)
print('Confirmation reserved',len(chosen),'from',len(eligible),'eligible',flush=True)
