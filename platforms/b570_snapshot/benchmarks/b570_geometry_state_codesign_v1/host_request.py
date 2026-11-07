"""Real serializer and immutable launch admission. Importing this module cannot start workers."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from pathlib import Path
from protocol import digest,require,recipe_request,BY_NAME
ROOT=Path(__file__).resolve().parent
@dataclass(frozen=True)
class Admitted:
 slot:str
 arm:str
 runtime_role:str
 argv:tuple[str,...]
 wire:bytes
 wire_sha256:str
 request_sha256:str
 effective_k:int
 native_arg_k:int
 binary_sha256:str
 @property
 def request(self):return json.loads(self.wire)
 def send(self,pipe):
  require(hashlib.sha256(self.wire).hexdigest()==self.wire_sha256,'mutated wire')
  pipe.write(self.wire);pipe.flush() # same exact validated bytes, no registry or recipe lookup

def serialize(x:dict)->bytes:
 # Exact inherited Worker.send JSON framing.
 return (json.dumps(x,separators=(',',':'),allow_nan=False)+'\n').encode()
def admit(slot:dict,case:dict,runtime:dict)->Admitted:
 req=slot['request'];r=BY_NAME[slot['arm']]
 require(req==recipe_request(case,r,slot['mode']) and digest(req)==slot['request_sha256'],'slot request drift')
 role=r.runtime;asset=runtime['roles'][role]
 require(asset['role']==role and asset['kind']==('ORIGINAL_PR92' if role=='old' else 'PR108_GRAPH_PORT'),'binary role mismatch')
 expected_binary=ROOT/('_host/pr97/baseline/pr92_restore/build/Release/b570-evidence-worker.exe' if role=='old' else '_host/build/Release/b570-geometry-worker.exe')
 require(Path(asset['binary']).resolve()==expected_binary.resolve(),'binary launch path is outside assigned role')
 require(any(Path(x['path']).resolve()==expected_binary.resolve() and x['sha256']==asset['sha256'] for x in asset['modules']),'binary hash is not in role module pins')
 require(Path(runtime['models']['target']['path']).name==req['target'],'target model role')
 if r.draft:require(Path(runtime['models']['draft']['path']).name==req['draft'],'draft model role')
 ub=req['producer_plan']['ubatch'];spec=r.draft
 trace=ROOT/'_host/run'/slot['slot']
 argv=[asset['binary'],'STANDARD_Q6',runtime['models']['target']['path'],runtime['models']['draft']['path'] if spec else 'NONE',str(ub),'native_greedy' if spec else 'ordinary','1',str(trace),'resident',slot['mode']]
 actual=dict(request_id=slot['slot'],prompt_ids=req['prompt_ids'],cap=128,capture=slot['mode']=='diagnostic',observation_mode=slot['mode'])
 if role=='new':
  argv += [r.continuation,str(r.capacity)]
  actual.update(normalized108=req,phase96_diagnostic=False,own_bind_sham=False,boundary_cuts=[])
 require(role!='old' or r.name=='R' and slot['mode']=='counts','original reference mapping')
 wire=serialize(actual);back=json.loads(wire)
 require(back==actual and back['prompt_ids']==req['prompt_ids'],'wire roundtrip')
 if role=='new':require(back['normalized108']==req,'normalized wire roundtrip')
 return Admitted(slot['slot'],slot['arm'],role,tuple(argv),wire,hashlib.sha256(wire).hexdigest(),digest(req),r.k,1,asset['sha256'])
def readback(a:Admitted)->dict:
 return dict(slot=a.slot,arm=a.arm,runtime_role=a.runtime_role,argv=list(a.argv),wire_utf8=a.wire.decode(),wire_sha256=a.wire_sha256,request_sha256=a.request_sha256,effective_k=a.effective_k,native_arg_k=a.native_arg_k,binary_sha256=a.binary_sha256,actual_GPU_geometry='PENDING_P1_OBSERVATION')
