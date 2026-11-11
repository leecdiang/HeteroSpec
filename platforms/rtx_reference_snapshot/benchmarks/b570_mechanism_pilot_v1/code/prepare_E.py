"""Fresh conservative accessible-history audit and predetermined balanced E panel, zero forwards."""
from pathlib import Path
import json,hashlib,re,os,collections,datetime
R=Path(__file__).parent;OLD=Path('C:/hs/b570-closeout-v1');PROJECT=Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert load(R/'D_VERIFICATION.json')['scientific_gate']=='PASS'
corpus=OLD/'dependencies/corpus/sanitized-mbpp.json';dataset_digest=sha(corpus);assert dataset_digest=='ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9';data=load(corpus)
prior=load(OLD/'dependencies/8dfa60a/EXPOSURE_SUMMARY.json');vocab=load(OLD/'INPUT_CANDIDATES.json');pool={i['id']:i for i in vocab['eligible_unused']};known={p['id'] for p in load(R/'D_INPUTS.json')}|{'MBPP/'+str(i) for i in prior['prior_mbpp_executed']}
token_proof=load(OLD/'TOKENIZATION_PROOF.json');token_stdout=OLD/'TOKENIZATION.stdout.jsonl'
assert token_proof['vocab_only'] and token_proof['stdout_sha256']==sha(token_stdout) and token_proof['models_sha256']=='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'
assert token_proof['tokenizer_sha256']==sha(OLD/'tokenizer-bin/Release/b570-tokenizer.exe') and token_proof['source_sha256']==sha(OLD/'tokenizer.cpp')
token_rows=[json.loads(l) for l in token_stdout.read_text(encoding='utf8').splitlines()][1:];token_map={i['id']:i for i in token_rows};assert all(i['forward_calls']==0 for i in token_rows)
for item in pool.values():assert item['prompt_ids']==token_map[item['id']]['prompt_ids']
known.update(p['id'] for p in load(OLD/'dependencies/RTX/B_INPUTS.json'))
patterns={}
for row in data:
 for b in [row['prompt'].encode(),json.dumps(row['prompt'],ensure_ascii=True)[1:-1].encode()]:patterns.setdefault(b,set()).add('MBPP/'+str(row['task_id']))
rx=re.compile(b'|'.join(re.escape(b) for b in sorted(patterns,key=len,reverse=True)));ids=re.compile(rb'\bMBPP[/_-](\d{1,4})\b',re.I)
roots=[PROJECT,Path('C:/Users/DIANG/.codex/worktrees/b570-closeout-v1/HeteroSpec'),Path('C:/Users/DIANG/.codex/worktrees/b570-mechanism-pilot-v1/HeteroSpec'),Path('C:/Users/DIANG/.codex/worktrees/b570-partition-intervention-v1/HeteroSpec'),Path('C:/hs')]
skip={'.git','__pycache__','models','vendor','third_party','node_modules','datasets','build','candidate-build','tokenizer-bin','archive','capsule','remote-parts','candidate-src','candidate-common','b570-direct-id-v1-src','b570-direct-id-v1-build','llama-b10839','b570-prefill-build','b570-partition-intervention-v1-build','b570-mechanism-v08-build'}
suffixes={'.json','.jsonl','.md','.txt','.csv','.log','.yaml','.yml','.tex','.cpp','.h','.py'}
catalog={};hits={};seen=set();errors=[];availability=[]
# Explicit mechanical availability files are not output inspection. Their bytes and policy are retained.
mechanical={'EXPOSURE_AUDIT.json','EXPOSURE_CATALOG.json','EXPOSURE_SUMMARY.json','INPUT_CANDIDATES.json','E_EXPOSURE_AUDIT.json','E_EXPOSURE_CATALOG.json','E_INPUTS.json','E_MANIFEST.json','E_SELECTION.json','TOKENIZATION.stdout.jsonl','PR59.json','PR60.json','PR62.json','PR63.json'}
for root in roots:
 for directory,dirs,files in os.walk(root):
  dirs[:]=[n for n in dirs if n not in skip and not n.startswith('.venv')]
  for name in files:
   p=Path(directory)/name
   if p.suffix.lower() not in suffixes or p.stat().st_size>128*1024*1024:continue
   try:b=p.read_bytes()
   except OSError as e:errors.append(dict(path=str(p),error=str(e)));continue
   h=hashlib.sha256(b).hexdigest();catalog[str(p)]=dict(sha256=h,bytes=len(b))
   if h in seen:continue
   seen.add(h)
   if h==dataset_digest or p.name in mechanical or (b'"forward_calls": 0' in b and b'"vocab_only": true' in b and not any(k in b for k in [b'generated_ids',b'original_reference_ids',b'accepted_ids'])):
    availability.append(str(p));continue
   for m in ids.finditer(b):hits.setdefault('MBPP/'+m.group(1).decode(),set()).add(str(p))
   for m in rx.finditer(b):
    for task in patterns[m.group(0)]:hits.setdefault(task,set()).add(str(p))
 print('Exposure audited',str(root),'files',len(catalog),'known hits',len(hits),flush=True)
assert not errors,errors
rows=[];eligible=[];counts=collections.Counter(i['task_id'] for i in data);desc=collections.Counter(i['prompt'] for i in data)
for row in data:
 task='MBPP/'+str(row['task_id']);reasons=[]
 if task not in pool:reasons.append('outside inherited conservative eligible pool')
 if task in known:reasons.append('known execution including PR63 all32, RTX62 and dev')
 if task in hits:reasons.append('fresh accessible output/inspection/ambiguous hit')
 if counts[row['task_id']]!=1 or desc[row['prompt']]!=1:reasons.append('duplicate ID or description')
 if task in pool and len(pool[task]['prompt_ids'])+128+2+4>1024:reasons.append('static ctx1024 safety')
 digest=hashlib.sha256((task+'HeteroSpec-B570-mechanism-v1-confirm').encode()).hexdigest()
 entry=dict(id=task,selection_hash=digest,exclusions=reasons,evidence=sorted(hits.get(task,[]))[:8],description_sha256=hashlib.sha256(row['prompt'].encode()).hexdigest());rows.append(entry)
 if not reasons:
  item=dict(pool[task]);raw='Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n'+row['prompt'];formatted='<|im_start|>user\n'+raw+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n';assert item['formatted_prompt']==formatted and item['raw_prompt']==raw
  item['cohort']='accessible_project_unused_confirmation';item['selection_hash']=digest;item['cap']=128;eligible.append(item)
eligible.sort(key=lambda x:(x['selection_hash'],x['id']))
chosen=eligible[:15]
audit=dict(status='PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),roots=[str(p) for p in roots],files=len(catalog),unique_files=len(seen),known_executed=sorted(known),rows=rows,eligible_ranked=[i['id'] for i in eligible],availability_only_files=availability,availability_policy='Exact corpus, mechanically exhaustive exposure ledgers/candidate availability tables and explicit zero-forward tokenization are availability only, not evidence of generated/output inspection. All other description or task-ID hits conservatively exclude.',limitations=['RTX machine-local bulk raw unavailable: known PR62 receipt and accessible public inputs/results examined; no claim of independent RTX bulk rescan.','Accessible project unused, not model-training unseen.'],dataset_sha256=sha(corpus),inherited_receipt_sha256=sha(OLD/'dependencies/8dfa60a/EXPOSURE_SUMMARY.json'),tokenizer_proof_sha256=sha(OLD/'TOKENIZATION_PROOF.json'),new_model_forwards=0)
def save(n,x):(R/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
save('E_EXPOSURE_CATALOG.json',catalog);save('E_EXPOSURE_AUDIT.json',audit);save('E_INPUTS.json',chosen)
save('E_TOKENIZATION_BINDINGS.json',dict(status='PASS',dataset_sha256=dataset_digest,inherited_zero_forward_tokenization_proof=token_proof,token_stdout_sha256=sha(token_stdout),reused_prompt_IDS_exact=True,prompt_wrappers_rederived_from_original_corpus=True,no_new_forward_or_tokenizer_request=True))
save('E_BUDGET_AMENDMENT.json',dict(before_any_new_confirmation_output=True,original_max=128,new_matched_target_capture_bridge=8,bridge_tasks=['HumanEval/42','HumanEval/145','HumanEval/134','MBPP/72'],bridge_rounds=['capture_on','capture_off'],confirmation_tasks=len(chosen),modes=4,rounds=2,complete_balanced_formal_requests=len(chosen)*8,total_nonwarm=8+len(chosen)*8,selection_rule='fixed hash order from current eligible list; first15 rather than16 to fund8 diagnostic requests uniformly across all modes/rounds',selected=[i['id'] for i in chosen],sixteenth_not_run=eligible[15]['id'] if len(eligible)>15 else None,no_output_based_selection=True))
print('Selected',len(chosen),'balanced confirmation tasks from',len(eligible),'eligible, no model forward')
assert len(chosen)>=8,'UNSUPPORTED_UNUSED_PANEL; zero new-output calls, audited rows preserved'
