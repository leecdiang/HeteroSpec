from pathlib import Path
import json,hashlib,datetime
import experiment
p=Path(__file__).resolve().parent
def prepare():
 candidates=[json.loads(x) for x in (p/'evidence/tokenized.jsonl').read_text(encoding='utf8').splitlines()]
 candidates=[x for x in candidates if 1<=len(x['prompt_ids'])<=768]
 def viable(cuts):
  return all(sum(x['domain']==d and lo<len(x['prompt_ids'])<=hi for x in candidates)>=2 for lo,hi in zip([0]+cuts[:-1],cuts) for d in ['code','math'])
 cuts=[128,256,512,768]
 if not viable(cuts):
  cuts=[];lo=0
  for stage in range(3):
   choices=sorted({len(x['prompt_ids']) for x in candidates if len(x['prompt_ids'])>lo})
   hi=next(n for n in choices if all(sum(x['domain']==d and lo<len(x['prompt_ids'])<=n for x in candidates)>=2 and sum(x['domain']==d and len(x['prompt_ids'])>n for x in candidates)>=2*(3-stage) for d in ['code','math']))
   cuts.append(hi);lo=hi
  cuts.append(768)
 chosen=[]
 for b,(lo,hi) in enumerate(zip([0]+cuts[:-1],cuts)):
  for domain in ['code','math']:
   xs=sorted([x for x in candidates if x['domain']==domain and lo<len(x['prompt_ids'])<=hi],key=lambda x:x['root'])[:2]
   if len(xs)!=2:raise ValueError('unfillable panel')
   chosen.extend(dict(x,length_bin=b) for x in xs)
 out=p/'evidence/prepared';out.mkdir(exist_ok=False)
 (out/'panel.json').write_text(json.dumps(chosen,indent=2),encoding='utf8')
 for i,session in enumerate(experiment.schedule(chosen)):
  stem=f'{i:02d}_{session[0]["mode"]}_{session[0]["arm"]}';(out/(stem+'.json')).write_text(json.dumps(session,indent=2),encoding='utf8')
  tsv=[' '.join(map(str,[r['id'],r['mode'],len(r['prompt_ids']),128]+r['prompt_ids']+r['continuation_ids'])) for r in session]
  (out/(stem+'.tsv')).write_text('\n'.join(tsv)+'\n',encoding='utf8')
 # Independent historical R fixture retained verbatim; qualification only.
 old=json.loads(Path('D:/rtx192-review-v2/runs/Qwen-v2-matrix-R/job.json').read_bytes())['cases'][0]['forced'][0]['ids']
 diagnostics=[dict(chosen[0],kind='G'),dict(root='historical-R-q4-inside-prefix764',prompt_ids=old,continuation_ids=chosen[0]['continuation_ids'],kind='P',source='D:/rtx192-review-v2/runs/Qwen-v2-matrix-R/job.json')]
 for arm,offset in [('R',9000),('M',9100)]:
  ref=[dict(x,id=offset+i+1) for i,x in enumerate(diagnostics)];ref[0]['panel_check']=chosen
  (p/f'evidence/{arm}-reference.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in ref),encoding='utf8')
  for passname,base,reuse in [('fresh',10,False),('repeat-reset',20,True)]:
   specs=[dict(x,id=offset+base+i+1,mode='H' if x['kind']=='G' else 'Q') for i,x in enumerate(diagnostics)]
   if reuse:specs += [dict(x,id=offset+30+i+1,mode='H' if x['kind']=='G' else 'Q') for i,x in enumerate(diagnostics)]
   stem=f'{arm}-{passname}';(p/f'evidence/{stem}.json').write_text(json.dumps(specs,indent=2),encoding='utf8');(p/f'evidence/{stem}.tsv').write_text('\n'.join(' '.join(map(str,[r['id'],r['mode'],len(r['prompt_ids']),128]+r['prompt_ids']+r['continuation_ids'])) for r in specs)+'\n',encoding='utf8')
 manifest=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prescribed_bins=[128,256,512,768],actual_bin_tops=cuts,changed_before_any_inference=True,selection='native tokenizer export only;no model outputs used;predeclared deterministic feasible cuts if needed',roots=[dict(root=x['root'],domain=x['domain'],prompt_length=len(x['prompt_ids']),length_bin=x['length_bin']) for x in chosen],candidates=len(candidates),requests=220,deployments=18,qualification_short='own greedy with complete requested vectors',qualification_near='historical prompt764+fixed128;complete requested vectors;R additionally exact historical frontier')
 (p/'evidence/PANEL_FROZEN.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
 return manifest
