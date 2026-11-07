"""CPU only reservation/exposure refresh. Never replaces a frozen confirmation task."""
import os,re,json,hashlib,time
from pathlib import Path
from prepare import R,REPO,PLAN,load,save
chosen=load(R/'SMOL_CONFIRMATION_INPUTS.json');ours={x['id'] for x in chosen};descriptions={x['description_sha256'] for x in chosen};conflicts=[]
for filename in ['F_CONFIRMATION_INPUTS.json','QWEN_CONFIRMATION_INPUTS.json']:
 for x in load(R/'pre-confirmation'/filename):
  desc=x.get('description_sha256') or hashlib.sha256(x.get('description','').encode()).hexdigest()
  if x['id'] in ours or desc in descriptions:conflicts.append(dict(file=filename,task=x['id'],reason='task ID or description hash reserved/executed elsewhere'))
baseline=load(R/'EXPOSURE_CATALOG.json');changed=[];checked=0
roots=[REPO,Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec'),Path('C:/Users/DIANG/.codex/worktrees'),Path('C:/hs')]
skip={'.git','__pycache__','models','vendor','third_party','node_modules','datasets','build','candidate-build','tokenizer-bin','tokenizer-build','archive','capsule','remote-parts','candidate-src','candidate-common','b570-direct-id-v1-src','b570-direct-id-v1-build','llama-b10839','b570-prefill-build','b570-partition-intervention-v1-build','b570-mechanism-v08-build','source-history','jsa-b570-run-v1','jsa-b570-v1','python-deps'}
suffix={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.tex','.py'}
mechanical={'EXPOSURE_AUDIT.json','EXPOSURE_CATALOG.json','EXPOSURE_SUMMARY.json','INPUT_CANDIDATES.json','E_EXPOSURE_AUDIT.json','E_EXPOSURE_CATALOG.json','TOKENIZATION.stdout.jsonl','PR59.json','PR60.json','PR62.json','PR63.json','EXPOSURE_RECHECK.json','E_SELECTION.json'}
datasetsha=load(R/'EXPOSURE_AUDIT.json')['dataset_sha256'];seen=set()
for root in roots:
 for directory,dirs,files in os.walk(root):
  dirs[:]=[n for n in dirs if n not in skip and not n.startswith('.venv')]
  for name in files:
   p=Path(directory)/name
   if p.suffix.lower() not in suffix or p.stat().st_size>128*1024*1024 or p.is_relative_to(REPO/'benchmarks/jsa_b570_validation_v1') or p.is_relative_to(PLAN):continue
   if str(p) in seen:continue
   seen.add(str(p));b=p.read_bytes();h=hashlib.sha256(b).hexdigest();checked+=1
   if baseline.get(str(p),{}).get('sha256')==h:continue
   changed.append(dict(path=str(p),sha256=h,bytes=len(b)))
   if name in mechanical or h==datasetsha or 'jsa_b570_validation_20261010' in p.parts or (b'"forward_calls": 0' in b and b'"vocab_only": true' in b and not any(k in b for k in [b'generated_ids',b'accepted_ids'])):continue
   for x in chosen:
    exact=x['id'].encode();desc=x['description'].encode();escaped=json.dumps(x['description'],ensure_ascii=True)[1:-1].encode()
    if re.search(rb'\b'+re.escape(exact)+rb'\b',b) or desc in b or escaped in b:conflicts.append(dict(path=str(p),task=x['id'],reason='new/changed accessible ID or description ambiguity'))
save('CONFIRMATION_RESERVATION_RECHECK.json',dict(status='PASS' if not conflicts else 'CONFIRMATION_RESERVATION_CONFLICT',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),remote=load(R/'pre-confirmation/HEADS.json'),checked_files=checked,changed_files=changed,conflicts=conflicts,frozen_tasks_replaced=0,scope='Incremental accessible-host and live RTX cohort refresh; unavailable private hosts remain explicitly unknown.'))
assert not conflicts,conflicts
print('Confirmation refresh PASS',checked,'files',len(changed),'changed',flush=True)
