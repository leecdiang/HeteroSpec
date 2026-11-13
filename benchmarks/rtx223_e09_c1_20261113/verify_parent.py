"""Read-only CPU identity and raw GGUF payload checks. No numerical libraries."""
from pathlib import Path
import json,hashlib,struct,datetime,statistics,math
here=Path(__file__).resolve().parent;study=here.parent;old=study/'rtx223-e08';num=old/'numeric-v1'
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def need(c,s):
 if not c:raise RuntimeError(s)
checks=[]
for row in json.loads((num/'FINAL_IDENTITIES.json').read_bytes())['files']:
 need(sha(row['path'])==row['sha256'],'old identity drift '+row['path']);checks.append(row)
mapping={Path(x['original']):x for x in json.loads((num/'PROFILE_DATA_PRESERVED.json').read_bytes())['files']}
operands=json.loads((num/'OPERANDS_FROZEN.json').read_bytes());data=[]
for row in operands['files']:
 saved=Path(mapping[Path(row['path'])]['preserved']);need(sha(saved)==row['sha256'],'raw capture drift');data.append(dict(original=row['path'],preserved=str(saved),sha256=row['sha256'],bytes=saved.stat().st_size))
model=Path('D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf')
need(sha(model)==operands['model_sha256'],'current model differs from producer')
# GGUF parsing reads metadata and the selected raw tensor only. No model init.
with model.open('rb') as f:
 def get(fmt):return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))[0]
 def string():
  n=get('Q');need(n<64*1024**2,'string bound');return f.read(n).decode('utf8')
 sizes={0:1,1:1,2:2,3:2,4:4,5:4,6:4,7:1,10:8,11:8,12:8}
 def skip(t):
  if t in sizes:f.seek(sizes[t],1)
  elif t==8:n=get('Q');need(n<64*1024**2,'value bound');f.seek(n,1)
  elif t==9:
   element=get('I');n=get('Q');need(n<10000000,'array bound')
   if element in sizes:f.seek(n*sizes[element],1)
   else:
    for _ in range(n):skip(element)
  else:raise RuntimeError('unknown GGUF type')
 need(f.read(4)==b'GGUF' and get('I')==3,'GGUF v3 required');nt=get('Q');nm=get('Q');alignment=32
 for _ in range(nm):
  key=string();typ=get('I')
  if key=='general.alignment':need(typ==4,'alignment type');alignment=get('I')
  else:skip(typ)
 tensor=None
 for _ in range(nt):
  name=string();nd=get('I');need(0<nd<=4,'dimensions');dims=[get('Q') for _ in range(nd)];typ=get('I');offset=get('Q')
  if name=='blk.0.attn_q.weight':tensor=dict(name=name,dims=dims,type=typ,offset=offset)
 need(tensor and tensor['dims']==[4096,4096] and tensor['type']==8,'Q8 tensor identity')
 base=(f.tell()+alignment-1)//alignment*alignment;f.seek(base+tensor['offset']);payload=f.read(17825792);need(len(payload)==17825792,'weight length')
 weight=next(x for x in data if Path(x['preserved']).name=='weight.bin');need(hashlib.sha256(payload).hexdigest()==weight['sha256'],'captured weight not exact model tensor')
 tensor.update(data_base=base,absolute_file_offset=base+tensor['offset'],bytes=len(payload),sha256=weight['sha256'])
q=json.loads((num/'evidence/qualification-001/result.json').read_bytes());timing=json.loads((num/'evidence/timing-001/result.json').read_bytes())
need(q['status']=='PASS_OPERATOR_ONLY' and len(q['qualification'])==6,'old qualification incomplete')
oracle=(num/'evidence/capture-003/backend-output.f32').read_bytes();quant=(num/'evidence/capture-003/quantized/activation_q8_1.bin').read_bytes()
for arm in range(3):
 for repeat in range(2):
  need((num/f'evidence/qualification-001/arm{arm}-r{repeat}-activation.bin').read_bytes()==quant,'old activation mismatch')
  need((num/f'evidence/qualification-001/arm{arm}-r{repeat}-output.bin').read_bytes()==oracle,'old output mismatch')
paired=[]
for mode in ('kernel-only','complete-operator'):
 ratios=[]
 for block in range(6):
  values={x['arm']:x['event_ms'] for x in timing['paired_timings'] if x['mode']==mode and x['block']==block};ratios.append(values[2]/values[1])
 paired.append(dict(mode=mode,C_over_B_geomean=math.exp(statistics.mean(map(math.log,ratios))),all_C_slower=all(x>1 for x in ratios)))
ledgers=json.loads((old/'OLD_LEDGERS_RECHECK.json').read_bytes())['ledgers']
for row in ledgers:need(sha(row['path'])==row['sha256'],'legacy ledger drift')
keep=[Path(x['path']) for x in ledgers]+list(Path('D:/HeteroSpec-PC/rtx223-e08').rglob('attempt.jsonl'))+[Path('D:/HeteroSpec-PC/rtx223-e08/bootstrap-family.jsonl'),Path('D:/HeteroSpec-PC/rtx223-bootstrap-b1/attempt.jsonl'),old/'ADMIN_EVENTS.jsonl']
preservation=[dict(path=str(f),sha256=sha(f)) for f in keep]
failures=[]
for f in Path('D:/HeteroSpec-PC/rtx223-e08').rglob('attempt.jsonl'):
 tail=json.loads(f.read_bytes().splitlines()[-1])['event'];need(tail.get('owned_process_exit_confirmed') is True,'old task not closed');failures.append(dict(path=str(f),terminal=tail))
result=dict(pass_=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_head='ba019f30522352c87cac2cc527082ecc6c73ed97',old_identity_checks=checks,model=dict(path=str(model),sha256=operands['model_sha256']),selected_tensor=tensor,operands=data,old_raw_bitwise_verified=True,old_paired_ratios=paired,preservation=preservation,old_terminal_receipts=failures,CUDA_initializations=0,model_loads=0,GPU_contexts=0,explicit_kernel_calls=0)
with (here/'PARENT_REUSE_VERIFIED.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(pass_=True,tensor=tensor,old_paired=paired,raw_operand_files=len(data),legacy_ledgers=len(ledgers),CUDA_initializations=0),indent=2))
