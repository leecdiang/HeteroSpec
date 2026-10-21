"""Capture original controller100.Worker.request without constructing a native Worker.
A sealed admitted object is sent directly. There is no registry read in the sender path.
No CLI native execution entry point exists in this CPU-only revision.
"""
import copy,subprocess,tempfile,types
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch
from pinned_sources import *
from registry import C,label,kvkey,logkey,spec_equal,PayloadReader,validate_registry_against_plan

class Captured(BaseException):pass
def forbidden_launch(*args,**kwargs):raise AssertionError('CPU_ONLY_NATIVE_LAUNCH_FORBIDDEN')

def capture_real_request(s,reg,candidate_root):
 """Runs the exact hash-bound original method and its actual lookup, CHECK and restore100 assembly."""
 m=load('controller100');candidate_root=Path(candidate_root);lookup_reads=[];sent=[];wire=[]
 with tempfile.TemporaryDirectory() as d:
  donorfile=Path(d)/'DONORS.json';write(donorfile,reg)
  def loader(p):
   require(Path(p)==candidate_root/'DONORS.json','unexpected dry-run file lookup');lookup_reads.append(str(p));return read(donorfile)['entries']
  class Wire:
   def write(self,b):wire.append(b)
   def flush(self):pass
  fake=types.SimpleNamespace(dir=candidate_root/'raw'/s['slot'],block={'phase':s['stage'],'observation_mode':s['mode'],'own_bind_sham':False,'repeat':s['repeat']},name=s['slot'],p=types.SimpleNamespace(pid=-1,stdin=Wire()),cfg={'partition':512},arm='A',freeze='CPU_ONLY_DRY_RUN')
  def send(obj):
   m.Worker.send(fake,obj);sent.append(obj)
   if 'restore100' in obj:raise Captured()
  fake.send=send;fake.wait=lambda name,*a: {'event':'CHECK_OK'} if name=='CHECK_OK' else (_ for _ in ()).throw(AssertionError('No completion allowed'))
  case={'id':s['task'],'prompt_ids':s['prompt_ids'],'boundary_cuts':s['cuts'] if s['mode']=='heavy' else [],'schedule':[],'restore_donors':[label(s),'recipient_'+s['recipient']],'operator_capture':False}
  with patch.object(subprocess,'Popen',forbidden_launch),patch.multiple(m,ROOT=candidate_root,load=loader,charge=lambda *a:None,event=lambda **a:None,save=lambda *a:None):
   # .glob on a non-existent candidate operator directory is empty; no run directory is created.
   try:m.Worker.request(fake,s['slot'],case)
   except Captured:pass
  require(len(sent)==2 and sent[0]=={'op':'CHECK'} and 'restore100' in sent[1] and len(lookup_reads)==1,'did not capture actual CHECK/request/lookup')
 require(len(wire)==2 and loads(wire[0])==sent[0] and loads(wire[1])==sent[1],'original Worker.send serialization differs')
 return sent[1],{'wire_sha256':digest(wire[1]),'wire_bytes':len(wire[1]),'method':'hash-bound original controller100.Worker.request','source_sha256':REFS['source_modules']['controller100.py']['sha256'],'registry_reads':1,'CHECKs_captured_CPU_only':1,'completion_sent':0,'native_launches':0}

@dataclass(frozen=True)
class Admitted:
 request:dict
 slot:dict
 plan_sha256:str
 registry_sha256:str
 request_sha256:str
 runtime_expected:dict


def runtime_recipe():return {'prefill_ub':512,'continuation_ub':512,'output_capacity':1,'maximum_k':0,'logical_batch':512,'n_ctx':1024,'threads':10,'kv':'F16','flash_attention':False}
def identity_expected():
 f=read(Path(REFS['old_run'])/'F0.json');names=('b570-boundary-worker.exe','ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll','llama-b570-memory.dll');return {'driver_identity':f['driver_identity'],'model':next(p for p in f['bindings'] if p['path'].endswith('.gguf')),'modules':[p for p in f['bindings'] if Path(p['path']).name in names],'driver_modules':f['driver_module_pins'],'recipe':runtime_recipe(),'device':{'vendor_id':0x8086,'device_id':0xE20C,'device_local_heap_bytes':10563354624,'minimum_headroom_bytes':536870912},'target_all_weights_Vulkan0':True,'context_numeric_path':'Vulkan0_F16_KV_FAoff','load_forward_calls':0,'physical_residency':'UNKNOWN'}

def validate_actual_request(req,s,reg,candidate_root,reader=None):
 require(req['request_id']==__import__('hashlib').sha256(s['slot'].encode()).hexdigest()[:32] and req['prompt_ids']==s['prompt_ids'],'actual prompt/request ID differs');require(req['cap']==128 and req['observation_mode']==s['mode'] and req['capture']==(s['mode']=='heavy') and req['phase96_diagnostic']==(s['mode']=='heavy'),'mode/capture mismatch');require(req['boundary_cuts']==(s['cuts'] if s['mode']=='heavy' else []) and req['prefill_partition']==512 and req['prefill_schedule']==[] and not req['operator_capture'] and req['operator_layer']==0 and not req['own_bind_sham'],'cuts/recipe mismatch');require(req['operator_bytes_existing']==0 and Path(req['payload_dir'])==Path(candidate_root)/'payloads' and Path(req['operator_dir'])==Path(candidate_root)/'operator_payloads','payload/output paths');p=req['restore100'];require(p['donor_labels']==[label(s),'recipient_'+s['recipient']],'logical donor labels');require(spec_equal(p['KV'],s['mixture_spec']) and spec_equal(p['logits'],s['initial_logits_spec']),'actual request imports another valid cell');require(spec_equal(p['KV'],reg['entries'][kvkey(s)]['KV']) and spec_equal(p['logits'],reg['entries'][logkey(s)]['logits']),'actual request/registry disagreement')
 if reader:reader(p['KV']);reader(p['logits'])
 return True

def admit(req,s,plan,reg,candidate_root,reader=None):
 validate_actual_request(req,s,reg,candidate_root,reader);return Admitted(req,copy.deepcopy(s),digest(encoded(plan)),digest(encoded(reg)),digest(encoded(req)),identity_expected())

def send_preverified(a,sender,runtime_identity,*,allow_native=False):
 require(getattr(sender,'CPU_only',False) or allow_native,'NEW_NATIVE_REQUIRES_SEPARATE_AUTHOR_BUDGET_AND_F0_APPROVAL');require(runtime_identity==a.runtime_expected,'runtime identity changed');require(digest(encoded(a.request))==a.request_sha256,'admitted object mutated');s=a.slot;p=a.request['restore100'];require(a.request['prompt_ids']==s['prompt_ids'] and a.request['boundary_cuts']==(s['cuts'] if s['mode']=='heavy' else []) and a.request['observation_mode']==s['mode'] and spec_equal(p['KV'],s['mixture_spec']) and spec_equal(p['logits'],s['initial_logits_spec']),'pre-send import/prompt/cuts mismatch');fresh=PayloadReader();fresh(p['KV']);fresh(p['logits'])
 sender.send({'op':'CHECK'});sender.wait('CHECK_OK')
 require(digest(encoded(a.request))==a.request_sha256,'mutation after CHECK');require(sender.runtime_identity==a.runtime_expected,'identity drift before first forward');fresh=PayloadReader();fresh(p['KV']);fresh(p['logits']);sender.send(a.request) # exact same admitted object; no registry lookup here


def validate_native_result(req,s,raw,evidence,pid,mode,resolver):
 """Future independent post-import gate retained. Counts and heavy channels stay distinct."""
 require(raw['request_id']==req['request_id'],'native REQUEST/RESULT id');C.validate_endpoint(raw,s['prompt_ids'],pid,mode);C.validate_channel(evidence,raw,s['prompt_ids'],pid,mode);p=raw['restore100'];require(spec_equal(p['KV_source'],req['restore100']['KV']) and spec_equal(p['logits_source'],req['restore100']['logits']),'native import sources differ');require(p['post_restore_KV_sha256']==req['restore100']['KV']['sha256'] and p['post_restore_logits_sha256']==req['restore100']['logits']['sha256'],'native reserialization mismatch');require(C.endpoint(raw)==s['reference_endpoint'],'native endpoint/reference mismatch')
 if mode=='heavy':
  require(resolver is not None,'heavy capture resolver required')
  for t in req['boundary_cuts']:z,proof=C.logits_at(raw,t,resolver,req['restore100']['logits']);require(z is not None,'missing admitted heavy full capture')
 return True


def identity_from_native_evidence(identity,command,ready,loaded_paths,live_driver):
 """Future loaded-worker gate. Reads hashes/evidence only; never allocates or launches a model."""
 expected=identity_expected();require(identity['status']=='PASS' and identity['owned_pid']==ready['pid'] and ready['forward_calls']==0 and not identity['api_layer_loaded'],'loaded native identity/zero-forward guard');argv=command['argv'];require(Path(argv[0]).resolve()==Path(expected['modules'][0]['path']).resolve() and argv[3]=='NONE' and argv[4:7]==['512','ordinary','1'],'native worker/offload recipe');require(Path(argv[2]).resolve()==Path(expected['model']['path']).resolve(),'native model path');require(sha(argv[2])==expected['model']['sha256'] and Path(argv[2]).stat().st_size==expected['model']['bytes'],'native model bytes');require(live_driver==expected['driver_identity'],'live driver differs');actual={str(Path(p['path']).resolve()).lower():p for p in identity['modules']}
 for p in expected['modules']:
  k=str(Path(p['path']).resolve()).lower();require(k in actual and actual[k]['sha256']==p['sha256'] and sha(p['path'])==p['sha256'],'native worker/DLL identity')
 loaded={str(Path(p).resolve()).lower() for p in loaded_paths}
 for p in expected['driver_modules']:require(str(Path(p['path']).resolve()).lower() in loaded and sha(p['path'])==p['sha256'],'loaded driver module')
 require(len(identity['contexts'])==len(identity['weight_maps'])==1 and identity['weight_maps'][0]['all_weights_Vulkan0'],'weights not all on Vulkan0');ctx=identity['contexts'][0];require(ctx['numeric_path']==expected['context_numeric_path'] and ctx['load_forward_calls']==0 and ctx['ub']==512 and ctx['n_ctx']==1024 and ctx['outputs_max']==1,'native context');C.validate_memory({'violation':False,'samples':identity['memory']},identity['owned_pid']);return expected
