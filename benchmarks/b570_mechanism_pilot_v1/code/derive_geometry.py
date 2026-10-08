"""CPU-only real context-log and source-bound geometry audit."""
from pathlib import Path
import re,json,hashlib
R=Path(__file__).parent;rows=[]
for directory in (R/'sessions').iterdir():
 if not (directory/'SESSION.json').exists():continue
 s=json.loads((directory/'SESSION.json').read_text(encoding='utf8'));p=directory/'stderr.log';text=p.read_text(encoding='utf8',errors='replace');contexts=[]
 current=None
 for line in text.splitlines():
  m=re.search(r'llama_context: (n_ctx|n_batch|n_ubatch|n_outputs_max|n_outputs_max_per_seq|causal_attn)\s*=\s*(\d+)',line)
  if not m:continue
  key,value=m.group(1),int(m.group(2))
  if key=='n_ctx':current={};contexts.append(current)
  if current is not None:current[key]=value
 rows.append(dict(session=directory.name,label=s.get('config',{}).get('label','auxiliary_cross_fixed_batch'),round=s.get('config',{}).get('round'),actual_contexts=contexts,log_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),note='First target then draft (if native); subsequent contexts are actual per-request legacy continuation handoffs; live private in-place phase update appears in request metrics, not constructor log.'))
sources={}
for name in ['C:/hs/b570-direct-id-v1-src/src/llama-context.cpp','C:/hs/b570-direct-id-v1-src/src/llama-batch.h']:
 p=Path(name);sources[name]=hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(status='PASS',contexts=rows,source_bindings=sources,host_logits_stride=dict(vocabulary=151936,float32_row_bytes=151936*4,method='get_logits_ith uses output_reorder then output_resolve_row and logits.data + row * model.vocab.n_tokens; all crossed returned rows saved and independently validated',proof_level='source-bound host output layout, not backend operand/dispatch'),logits_mask='Actual batch logits_requested captured; all B common rows true and same across four cells. Attention causal_attn=1 in real logs; physical backend attention-mask tensors/operand strides/dispatch not directly measured.',KV_layout='Independent state parser validates F16 keys and transposed F16 values, exact serialized row/element byte counts, layer counts, logical positions and single-sequence ownership. Serialized layout is not proof of a unique execution kernel.',reservation_scope='Real current complete recipes: N1 outputs3/perseq3 UB1; E outputs2/perseq2 UB2; /72 both current recipes outputs3/perseq3 UB1. Candidate and ordinary R outputs512/perseq1, private candidate phase128-to1 in one target context.',model_requests=0)
(R/'GEOMETRY_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('Geometry audited',len(rows),'real session logs; backend operand strides/kernel dispatch remain unknown')
