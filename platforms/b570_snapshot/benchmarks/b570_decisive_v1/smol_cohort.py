"""Pre-output natural Smol cohort using the pinned existing public pool."""
from smol import *
from design import select,schedule,ARMS,SESSIONS
import jinja2
def prepare():
 folder=SROOT/'cohort';folder.mkdir()
 pool=Path('I:/HeteroSpec/b570-prefix-reuse-20261104')
 assert sha(pool/'corpus/messages.jsonl.gz')=='2ff4aa8999c911ffec7972ddf70359f220b3da184b731f3649f68b1391e19341'
 vocab=read(SMOL/'VOCAB_TARGET.json');table=vocab['table']
 env=jinja2.Environment(undefined=jinja2.StrictUndefined);env.globals['raise_exception']=lambda x:(_ for _ in ()).throw(ValueError(x));template=env.from_string(vocab['chat_template'])
 def token(i):return bytes.fromhex(table[i]['text_hex']).decode()
 formatted=[];source=[]
 for line in (pool/'corpus/paths.jsonl').read_text(encoding='utf-8').splitlines():
  r=json.loads(line);text=template.render(messages=r['messages'],add_generation_prompt=True,bos_token=token(vocab['bos']),eos_token=token(vocab['eos']))
  formatted.append(dict(id=r['id'],formatted_prompt=text));source.append(r)
 with (folder/'rendered.jsonl').open('x',encoding='utf-8') as f:
  for x in formatted:f.write(json.dumps(x,ensure_ascii=False)+'\n')
 binary=SMOL/'tokenizer-build/Release/b570-tokenizer.exe';assert sha(binary)==read(SMOL/'TOKENIZATION_BINDINGS.json')['tokenizer_executable_sha256']
 with (folder/'rendered.jsonl').open('rb') as inp,(folder/'tokenized.jsonl').open('xb') as out,(folder/'tokenizer.stderr.log').open('xb') as err:subprocess.run([str(binary),read(SROOT/'AUTHENTICATION.json')['models'][0]['path']],stdin=inp,stdout=out,stderr=err,check=True,timeout=120)
 lines=(folder/'tokenized.jsonl').read_text(encoding='utf-8').splitlines();assert json.loads(lines[0])==vocab
 previous=read(pool/'panel.json');excluded={r['root_id'] for group in ('calibration','test') for r in previous[group]}
 eligible=[];inputs={};rejected=[]
 for x,r,text in zip(lines[1:],source,formatted,strict=True):
  t=json.loads(x);assert t['id']==r['id'] and t['forward_calls']==0;ids=t['prompt_ids'];reason=None
  if r['history_exposed']:reason='inherited project exposure'
  elif len(ids)+127+1+4>1024:reason='original C1024 frontend extent'
  if reason:rejected.append(dict(id=r['id'],root_id=r['root_id'],reason=reason,prompt_tokens=len(ids)));continue
  eligible.append(dict(id=r['id'],root_id=r['root_id'],tokens=len(ids),native_tokenized=True,admitted=True))
  inputs[r['id']]=dict(id=r['id'],root_id=r['root_id'],prompt_ids=ids,formatted_sha256=hashlib.sha256(text['formatted_prompt'].encode()).hexdigest(),source_message_ids=r['message_ids'])
 # The following authored, committed RTX append panel is additional known exposure.
 commit='610fd3a364bec6e8a3881ef666bedacd2035679a'
 paths=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','ls-tree','-r','--name-only',commit],cwd=HERE,text=True).splitlines()
 pins=[]
 for p in paths:
  if not p.startswith('benchmarks/rtx_rechunk_discrimination_v1/evidence/') or Path(p).name not in ('selected-inputs.json','exclusions.json'):continue
  raw=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show',commit+':'+p],cwd=HERE)
  try:v=json.loads(raw)
  except (ValueError,UnicodeError):continue
  def absorb(z):
   if isinstance(z,list):
    for q in z:absorb(q)
   elif isinstance(z,dict):
    if isinstance(z.get('root_id'),str):excluded.add(z['root_id'])
    if isinstance(z.get('root_ids'),list):excluded.update(z['root_ids'])
    for q in z.values():
     if isinstance(q,(dict,list)):absorb(q)
  absorb(v);pins.append(dict(commit=commit,path=p,sha256=hashlib.sha256(raw).hexdigest()))
 panel=select(eligible,excluded)
 arms=['M','H1','C1U1','C4U1','C4U2','C4U4']
 # Separate secondary lane: retain the stronger historical whole-prompt UB1.
 ARMS['b570-smol-draft']=arms;SESSIONS['b570-smol-draft']=6
 plan=schedule(panel,'b570-smol-draft')
 write(folder/'PANEL.json',panel);write(folder/'SCHEDULE.json',plan)
 write(folder/'INPUTS.json',{r['id']:inputs[r['id']] for group in ('development','test') for r in panel[group]})
 write(folder/'SELECTION_AUDIT.json',dict(corpus_sha256=sha(pool/'corpus/messages.jsonl.gz'),old_paths_sha256=sha(pool/'corpus/paths.jsonl'),template_sha256=hashlib.sha256(vocab['chat_template'].encode()).hexdigest(),tokenizer_sha256=sha(binary),exposure_sources=pins,excluded_roots=sorted(excluded),eligible_paths=len(eligible),rejected=rejected,selection_before_outputs=True,secondary_lane=True,arms=arms,prospective_reason='The existing Smol caller is whole-prompt UB1, so H1 is retained in addition to all caller/UB controls; no weak caller-only baseline or speed-based exclusion',main_measurements=432,main_warmups=432,global_request_ceiling_unchanged=6144,actual_model_forwards=0))
 print('Smol frozen inputs:',len(panel['development']),len(panel['test']),'roots;',len(plan['slots']),'main slots')
if __name__=='__main__':prepare()
