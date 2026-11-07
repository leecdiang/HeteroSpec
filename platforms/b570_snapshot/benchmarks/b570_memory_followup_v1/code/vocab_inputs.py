"""Native vocabulary-only checks and prospective engineering/warm/boundary bytes."""
from common import *
import sys
sys.path.insert(0,'C:/hs/jsa-b570-run-v1/python-deps')
from jinja2 import Environment,StrictUndefined
exe=Path('C:/hs/jsa-b570-run-v1/tokenizer-build/Release/b570-tokenizer.exe');assets=load(R/'ASSET_CHECKS.json')['models'];vocabs={};(R/'vocab').mkdir(exist_ok=True)
for key,a in assets.items():
 assert sha(a['path'])==a['sha256'] and Path(a['path']).stat().st_size==a['bytes']
 out=R/'vocab'/(key+'.jsonl');err=out.with_suffix('.stderr.log')
 if not out.exists():
  with out.open('wb') as f,err.open('wb') as e:subprocess.run([str(exe),a['path']],input=b'',stdout=f,stderr=e,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
 vocabs[key]=json.loads(out.read_text().splitlines()[0]);assert vocabs[key]['vocab_only'] and vocabs[key]['forward_calls']==0
fields=['vocab_tokens','vocab_type','table','bos','eos','add_bos','add_eos','runtime_eog_ids']
target=vocabs['Llama_target_Q6_K'];pairs=[]
for key,v in vocabs.items():
 for field in fields:assert target[field]==v[field],key+' '+field
 pairs.append(dict(asset=key,full_native_rows_equal=len(v['table']),runtime_eog_equal=True))
assert target['chat_template']==vocabs['Llama_target_Q8_0']['chat_template']
env=Environment(undefined=StrictUndefined);env.globals['raise_exception']=lambda msg:(_ for _ in ()).throw(RuntimeError(msg));template=env.from_string(target['chat_template']);token=lambda i:bytes.fromhex(target['table'][i]['text_hex']).decode('utf8')
def format_prompt(raw):return template.render(messages=[dict(role='user',content=raw)],add_generation_prompt=True,bos_token=token(target['bos']),eos_token=token(target['eos']))
rows=load(R/'ENGINEERING_INPUTS.json')
synthetics=[dict(id='SYNTHETIC/WARM',raw_prompt='Explain in one short sentence what an integer is.',cap=128),dict(id='SYNTHETIC/BOUNDARY_A',raw_prompt='Return only the Python expression that adds two integers a and b.',cap=128),dict(id='SYNTHETIC/BOUNDARY_B',raw_prompt='Reply with the single word Done.',cap=128),dict(id='SYNTHETIC/LONGEST_768',raw_prompt='Read the following repeated words and answer with the word Done.\n'+'word '*900,cap=128)]
allrows=rows+synthetics
for x in allrows:x['formatted_prompt']=format_prompt(x['raw_prompt'])
def tokenize(xs):
 p=subprocess.run([str(exe),assets['Llama_target_Q6_K']['path']],input=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in xs).encode(),capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
 out=[json.loads(s) for s in p.stdout.splitlines()];assert out[0]==target
 return out[1:]
native=tokenize(allrows)
# Construct a real rendered synthetic prompt of exactly768 native IDs. No shortening
# of any scientific task or generated output; variable synthetic padding fixed at F0A.
long=allrows[-1]
estimate=900-(len(native[-1]['prompt_ids'])-768)
for n in [estimate]+[estimate+d for d in range(-8,9) if d]:
 candidate=dict(long,raw_prompt='Read the following repeated words and answer with the word Done.\n'+'word '*n);candidate['formatted_prompt']=format_prompt(candidate['raw_prompt']);tok=tokenize([candidate])[0]
 if len(tok['prompt_ids'])==768:long.clear();long.update(candidate);native[-1]=tok;break
else:raise RuntimeError('Synthetic longest prompt construction failed')
for x,t in zip(allrows,native):
 assert x['id']==t['id'] and t['forward_calls']==0;x['prompt_ids']=t['prompt_ids'];assert 0<len(x['prompt_ids'])<=768
 x['prompt_ids_sha256']=hashlib.sha256(json.dumps(x['prompt_ids'],separators=(',',':')).encode()).hexdigest()
 x['raw_prompt_sha256']=hashlib.sha256(x['raw_prompt'].encode()).hexdigest();x['formatted_prompt_sha256']=hashlib.sha256(x['formatted_prompt'].encode()).hexdigest()
save(R/'ENGINEERING_INPUTS.json',rows);save(R/'SYNTHETIC_INPUTS.json',synthetics)
save(R/'VOCAB_CHECKS.json',dict(status='PASS',pairs=pairs,vocab_tokens=target['vocab_tokens'],runtime_eog_ids=target['runtime_eog_ids'],tokenizer_sha256=sha(exe),target_template_sha256=hashlib.sha256(target['chat_template'].encode()).hexdigest(),forward_calls=0,original_checkpoint_provenance='NOT_CERTIFIED'))
print('Four full vocab tables and12 engineering/four synthetic inputs PASS',flush=True)
