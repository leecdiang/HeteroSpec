"""Independent trace/state adapter and exact full-vector comparison.

The reviewed readers are reused with import paths remapped only. No tolerance,
candidate oracle, tensor-value omission, or top1-only numerical check is added.
"""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys, types
import numpy as np
from common import need, sha

def review_writers(stage):
 stage=Path(stage);rows=[]
 functions={'src/llama-kv-cache.cpp':['void llama_kv_cache::state_write(','void llama_kv_cache::state_write_meta(','void llama_kv_cache::state_write_data('],
            'src/llama-context.cpp':['size_t llama_context::state_seq_get_data(','size_t llama_context::state_seq_write_data(']}
 for path,names in functions.items():
  texts={role:(stage/'sources'/role/path).read_text() for role in ('reference','loop4','packed')}
  for name in names:
   bodies={}
   for role,text in texts.items():
    start=text.index(name);end=text.index('\n}\n',start)+3;bodies[role]=text[start:end]
   need(len(set(bodies.values()))==1,'Serializer changed; register an actual new state ABI before comparison')
   rows.append({'source':path,'function':name,'same_body_all_roles':True,'body_sha256':hashlib.sha256(bodies['reference'].encode()).hexdigest()})
 vocab={role:(stage/'sources'/role/'src/llama-vocab.cpp').read_text() for role in ('reference','loop4','packed')}
 need(len(set(vocab.values()))==1,'Different native vocabulary/EOG implementation')
 return {'passed':True,'reviewed_functions':rows,'native_vocab_source_equal_all_roles':True,
         'reader_contract':'seq0 magic, one dense stream, exact positions/sequence IDs, all layers in native order, F16 K/V, full tensor payload and no trailing bytes',
         'non_value_fields_ignored':False,'source_order':'state_write_data iterates layers in native layer.il order; dense pinned GGUF layer count and dimensions checked independently'}

def legacy_readers(repo):
 root=Path(repo)/'benchmarks/tpds_decisive_v1';package='_reviewed_dense_linux'
 if package not in sys.modules:
  p=types.ModuleType(package);p.__path__=[str(root)];sys.modules[package]=p
  for name in ('common','trace','active_kv','normalize'):
   path=root/(name+'.py');text=path.read_text()
   for imported in ('common','trace','active_kv'):text=text.replace('from '+imported+' import','from .'+imported+' import')
   module=types.ModuleType(package+'.'+name);module.__file__=str(path);module.__package__=package
   sys.modules[module.__name__]=module;exec(compile(text,str(path),'exec'),module.__dict__)
 return sys.modules[package+'.normalize'].trace_from_row,sys.modules[package+'.active_kv'].parse

def gguf_structure(path):
 """Read architecture metadata, never tensors or model outputs."""
 with Path(path).open('rb') as f:
  def rd(fmt):
   n=struct.calcsize('<'+fmt);b=f.read(n);need(len(b)==n,'GGUF header truncated');return struct.unpack('<'+fmt,b)[0]
  def string(keep=True):
   n=rd('Q');need(n<=64*1024*1024,'GGUF header string bound')
   if not keep:f.seek(n,1);return None
   b=f.read(n);need(len(b)==n,'GGUF metadata string');return b.decode('utf8')
  def value(t,keep):
   formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
   if t in formats:return rd(formats[t])
   if t==8:return string(keep)
   need(t==9,'Unknown GGUF metadata type');element=rd('I');count=rd('Q');need(count<=2000000,'GGUF array bound')
   if keep:return [value(element,True) for _ in range(count)]
   if element in formats:f.seek(struct.calcsize('<'+formats[element])*count,1)
   else:
    for _ in range(count):value(element,False)
   return {'array_type':element,'length':count}
  need(f.read(4)==b'GGUF' and rd('I') in (2,3),'Pinned GGUF encoding');tensors=rd('Q');count=rd('Q');need(count<10000,'GGUF key bound')
  meta={}
  for _ in range(count):
   key=string();t=rd('I');meta[key]=value(t,not key.startswith(('tokenizer.ggml.tokens','tokenizer.ggml.merges','tokenizer.ggml.scores','tokenizer.ggml.token_type')))
 arch=meta['general.architecture'];layers=meta[arch+'.block_count'];heads=meta[arch+'.attention.head_count'];kv=meta.get(arch+'.attention.head_count_kv',heads)
 need(all(type(x)is int and x>0 for x in (layers,heads,kv)),'Unsupported non-uniform layer/head metadata')
 dim=meta[arch+'.embedding_length'];key_dim=meta.get(arch+'.attention.key_length',dim//heads);value_dim=meta.get(arch+'.attention.value_length',dim//heads)
 need(dim%heads==0,'Undeclared head geometry')
 return {'architecture':arch,'layers':layers,'query_heads':heads,'kv_heads':kv,'head_k':key_dim,'head_v':value_dim,'K_elements':kv*key_dim,'V_elements':kv*value_dim,
         'vocab':meta['tokenizer.ggml.tokens']['length'],'tensor_count':tensors,
         'declared_stop_ids':{k:v for k,v in meta.items() if k.startswith('tokenizer.ggml.') and k.endswith(('.eos_token_id','.eot_token_id','.eom_token_id'))}}

def profile(model,model_sha256,writer,structure):
 need(sha(model)==model_sha256,'Independent profile model identity')
 return {'format':'dense_seq_f16_v1','writer_sha256':sha(writer),'layer_map_source_sha256':sha(writer),'target_model_sha256':model_sha256,
         'host_writer_reviewed':True,'capacity':1024,'layers':[{'id':i,'k_elements':structure['K_elements'],'v_elements':structure['V_elements']} for i in range(structure['layers'])]}

def vector_pair(actual,expected,vocab):
 actual=Path(actual);expected=Path(expected);a=actual.read_bytes();b=expected.read_bytes()
 need(len(a)==len(b)==4*vocab,'Full requested vocabulary missing')
 aa=np.frombuffer(a,dtype='<f4');bb=np.frombuffer(b,dtype='<f4');need(bool(np.isfinite(aa).all() and np.isfinite(bb).all()),'Nonfinite requested vector')
 result={'equal':a==b,'actual_sha256':hashlib.sha256(a).hexdigest(),'reference_sha256':hashlib.sha256(b).hexdigest(),'bytes':len(a)}
 if a!=b:
  i=int(np.flatnonzero(aa.view('<u4')!=bb.view('<u4'))[0]);result['first_difference']={'index':i,'actual':float(aa[i]),'reference':float(bb[i]),'actual_bits':int(aa.view('<u4')[i]),'reference_bits':int(bb.view('<u4')[i])}
 return result

def state_pair(actual,expected,positions,reader,writer_profile):
 a=Path(actual).read_bytes();b=Path(expected).read_bytes()
 av,am=reader(a,list(range(positions)),writer_profile);bv,bm=reader(b,list(range(positions)),writer_profile)
 need(am['active_layout_sha256']==bm['active_layout_sha256'],'Layer/layout identity differs')
 return {'equal':av==bv,'raw_equal':a==b,'actual_raw_sha256':hashlib.sha256(a).hexdigest(),'reference_raw_sha256':hashlib.sha256(b).hexdigest(),
         'actual_active_sha256':hashlib.sha256(av).hexdigest(),'reference_active_sha256':hashlib.sha256(bv).hexdigest(),'active_bytes':len(av),'positions':positions,'layout_sha256':am['active_layout_sha256'],'profile_sha256':am['profile_sha256']}
