"""Actual GGUF and full native vocabulary qualification, vocab-only, zero forwards."""
import struct,json,subprocess,shutil,hashlib
from pathlib import Path
from prepare import R,REPO,PLAN,load,save,sha
def gguf(p):
 with Path(p).open('rb') as f:
  def readfmt(fmt):return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))[0]
  def text():return f.read(readfmt('Q')).decode('utf8')
  def value(t):
   if t==8:return text()
   if t==9:
    typ=readfmt('I');n=readfmt('Q');return [value(typ) for _ in range(n)]
   return readfmt({0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}[t])
  assert f.read(4)==b'GGUF';version=readfmt('I');nt=readfmt('Q');nk=readfmt('Q');meta={}
  for _ in range(nk):key=text();meta[key]=value(readfmt('I'))
 return dict(version=version,tensors=nt,metadata=meta)
bin=R/'tokenizer-build/Release';bin.mkdir(parents=True,exist_ok=True)
for p in (R/'bin/original').glob('*.dll'):shutil.copyfile(p,bin/p.name)
models=load(R/'MODEL_CHOICE.json')['models'];native={};metas={}
for role,x in models.items():
 metas[role]=gguf(x['path']);save('GGUF_'+role.upper()+'.json',metas[role])
 out=R/(role+'_vocab.jsonl');err=R/(role+'_vocab.stderr.log')
 with out.open('wb') as f,err.open('wb') as e:subprocess.run([str(bin/'b570-tokenizer.exe'),x['path']],input=b'',stdout=f,stderr=e,check=True)
 native[role]=json.loads(out.read_text(encoding='utf8').splitlines()[0]);save('VOCAB_'+role.upper()+'.json',native[role])
print('Native full vocab read, zero forward',flush=True)
t,d=native['target'],native['draft']
for key in ['vocab_tokens','vocab_type','table','bos','eos','add_bos','add_eos','runtime_eog_ids']:assert t[key]==d[key],key
tm,dm=metas['target']['metadata'],metas['draft']['metadata']
for k in set(tm)|set(dm):
 if k.startswith('tokenizer.') and k!='tokenizer.chat_template':assert tm.get(k)==dm.get(k),k
assert t['chat_template']==tm['tokenizer.chat_template'] and t['chat_template']
from jinja2 import Environment,StrictUndefined
env=Environment(undefined=StrictUndefined);env.globals['raise_exception']=lambda msg:(_ for _ in ()).throw(RuntimeError(msg));template=env.from_string(t['chat_template'])
table=t['table'];token=lambda i:bytes.fromhex(table[i]['text_hex']).decode('utf8')
def format_prompt(raw):return template.render(messages=[dict(role='user',content=raw)],add_generation_prompt=True,bos_token=token(t['bos']),eos_token=token(t['eos']))
discovery=[]
for x in load(R/'QWEN_INPUTS.json'):
 raw=x.get('raw_prompt')
 if not raw:
  # HumanEval raw user content is reconstructed from the retained exact Qwen wrapper.
  formatted=x['formatted_prompt'];assert formatted.startswith('<|im_start|>user\n');raw=formatted.split('<|im_start|>user\n',1)[1].split('<|im_end|>',1)[0]
 discovery.append(dict(id=x['id'],raw_prompt=raw,description=x.get('description',raw),description_sha256=hashlib.sha256(x.get('description',raw).encode()).hexdigest()))
groups={'SMOL_DISCOVERY_INPUTS.json':discovery,'SMOL_CONFIRMATION_INPUTS.json':load(R/'CONFIRMATION_RAW_INPUTS.json')}
all_inputs=[]
for rows in groups.values():
 for x in rows:x['formatted_prompt']=format_prompt(x['raw_prompt']);all_inputs.append(x)
encoded=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in all_inputs).encode('utf8')
out=R/'TOKENIZATION.stdout.jsonl';err=R/'TOKENIZATION.stderr.log'
with out.open('wb') as f,err.open('wb') as e:subprocess.run([str(bin/'b570-tokenizer.exe'),models['target']['path']],input=encoded,stdout=f,stderr=e,check=True)
lines=[json.loads(x) for x in out.read_text(encoding='utf8').splitlines()];assert lines[0]==t;rows=lines[1:];assert len(rows)==len(all_inputs)
for x,tok in zip(all_inputs,rows):
 assert x['id']==tok['id'] and tok['forward_calls']==0;x['prompt_ids']=tok['prompt_ids'];assert len(x['prompt_ids'])+128+2+4<=1024
 x['raw_prompt_sha256']=hashlib.sha256(x['raw_prompt'].encode()).hexdigest();x['formatted_prompt_sha256']=hashlib.sha256(x['formatted_prompt'].encode()).hexdigest();x['prompt_ids_sha256']=hashlib.sha256(json.dumps(x['prompt_ids'],separators=(',',':')).encode()).hexdigest();x['cap']=128
for filename,rows in groups.items():save(filename,rows)
offload={}
for role,m in metas.items():arch=m['metadata']['general.architecture'];offload[role]=m['metadata'][arch+'.block_count']+1
save('TOKENIZATION_BINDINGS.json',dict(status='PASS',vocab_tokens=t['vocab_tokens'],runtime_eog_ids=t['runtime_eog_ids'],offload_layers=offload,actual_full_vocab_and_tokenizer_metadata_equal=True,actual_template_sha256=hashlib.sha256(t['chat_template'].encode()).hexdigest(),tokenizer_executable_sha256=sha(bin/'b570-tokenizer.exe'),source_sha256=sha(Path(__file__).with_name('tokenizer.cpp')),stdout_sha256=sha(out),vocab_only=True,forward_calls=0,architecture_schema={role:{k:v for k,v in m['metadata'].items() if not k.startswith('tokenizer.')} for role,m in metas.items()}))
print('Inputs frozen',len(discovery),len(groups['SMOL_CONFIRMATION_INPUTS.json']),'vocab',t['vocab_tokens'],'layers',offload,flush=True)
