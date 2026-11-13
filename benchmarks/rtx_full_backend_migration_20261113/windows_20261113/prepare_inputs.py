from pathlib import Path
import gzip,json,hashlib,datetime
p=Path(__file__).resolve().parent;out=p/'inputs'
rows=[]
for line in gzip.decompress((out/'HumanEval.jsonl.gz').read_bytes()).decode('utf8').splitlines():
 d=json.loads(line);rows.append(dict(root=d['task_id'],domain='code',source='openai/human-eval;local frozen gzip SHA256',prompt=d['prompt'],continuation=d['canonical_solution']+'\n'+d['test']))
meta=json.loads((out/'MATH_META.json').read_bytes())
for i,line in enumerate((out/'test.jsonl').read_text(encoding='utf8').splitlines()):
 d=json.loads(line);rows.append(dict(root=f'MATH500/{i:04d}',domain='math',source='HuggingFaceH4/MATH-500@'+meta['sha'],prompt=d['problem'],continuation=d['solution']))
for d in rows:
 d['prompt_text']='<|im_start|>user\n'+d.pop('prompt')+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
 d['continuation_text']=d.pop('continuation')
with (out/'raw_candidates.jsonl').open('x',encoding='utf8') as f:
 for d in rows:f.write(json.dumps(d,ensure_ascii=True)+'\n')
manifest=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),raw_records=len(rows),format='explicit frozen Qwen3 user/assistant no-thinking rendering,parse_special true,add_special true;not claimed default template',continuation='first128 native tokens of dataset solution+tests(code) or solution(math);filter if shorter,never repeat/pad',selection='first2 stable IDs per domain in each prescribed bin;deterministic feasible consecutive length cuts only if those bins cannot fill,freeze before inference/timing',sources=[dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest()) for q in [out/'HumanEval.jsonl.gz',out/'test.jsonl',out/'raw_candidates.jsonl']],prior_exposure='HumanEval and math tasks may have appeared in prior project corpora;not a training-unseen claim;panel separate from prior singleton operator/A5000 roots')
(out/'RAW_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(json.dumps(dict(raw_records=len(rows),GPU=0)))
