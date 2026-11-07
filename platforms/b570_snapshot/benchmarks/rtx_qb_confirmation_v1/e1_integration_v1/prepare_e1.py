"""Freeze the original 72-context E1 matrix from pinned model metadata/inputs."""
import struct
import shutil
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiment as e
import adapter

ROOT=Path('D:/hs104-e1-v1');E2=Path('D:/hs-qb-confirmation-v02')

def block_count(path):
    with Path(path).open('rb') as f:
        def unpack(fmt):return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))[0]
        def string():return f.read(unpack('Q')).decode()
        def value(t,keep=False):
            formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
            if t==8:return string()
            if t==9:
                kind,n=unpack('I'),unpack('Q')
                for _ in range(n):value(kind)
                return None
            return unpack(formats[t])
        e.require(f.read(4)==b'GGUF' and unpack('I') in (2,3),'unsupported GGUF metadata')
        tensors,n=unpack('Q'),unpack('Q');architecture=None
        for _ in range(n):
            key=string();t=unpack('I');v=value(t)
            if key=='general.architecture':architecture=v
            if architecture and key==architecture+'.block_count':
                e.require(type(v)is int and 2<=v<=256,'invalid layer count');return v
    raise ValueError('model block count missing')

def main():
    build=e.read(ROOT/'NATIVE_BUILD.json');e.require(build['status']=='BUILT_NOT_GPU_QUALIFIED','isolated build unavailable')
    old=e.read(E2/'PLAN.json');p0=e.read(Path(old['results'])/'P0_PLAN.json')
    contract=e.read(E2/'MODEL_CONTRACT.json');contexts=[];selected={}
    for family in e.FAMILIES:
        task=sorted(p0['P2_panel'][family],key=lambda t:(-len(t['prompt_ids']),t['id']))[0]
        layers=block_count(contract['families'][family]['models']['target']['path'])
        selected[family]=dict(task=task,target_layers=layers,rule='longest inherited P2 prompt, lexical ID tie break; before E1 forwards')
        for layer in (0,layers//2,layers-1):
            for phase in ('prefill','continuation'):
                for q in (1,2,3,4):
                    row=dict(id=f'{family}_l{layer:02d}_{phase}_q{q}',family=family,layer=layer,phase=phase,q=q,
                             min_key=128 if q in (2,4) else 0,task=task)
                    row['selectors']=adapter.selectors(row);row['condition']=adapter.condition(row);contexts.append(row)
    e.require(len(contexts)==72 and len({c['id'] for c in contexts})==72,'E1 matrix differs')
    for name in ('MODEL_CONTRACT.json','COUNTER_SEMANTICS.md','HOST.json'):
        shutil.copyfile(E2/name,ROOT/name)
    plan=dict(schema=1,contexts=contexts,selected=selected,warmups=p0['warmups'],legacy=old['legacy'],
              request_cap=216,operator_cap=432,owned_seconds_cap=21600,native_worker_cap=72,
              requests_per_context=['counts_warmup','heavy_capture','counts_capture_off'],operator_repeats=2,
              operator_arms=['MQ','PQ','QB'],order_rule='rotate MQ/PQ/QB by (context index + repeat) mod 3',
              selection_after_E1_results=False,scientific_retries=False,kernel_and_reduction_tree='UNKNOWN',
              physical_token_attribution='Complete native caller trace retained; physical row attribution UNKNOWN unless directly identifiable',
              numeric_scope='fixed same captured bytes/geometry; no universal equivalence or full-model causal trace claim')
    e.save(ROOT/'PLAN.json',plan)
    print({f:(x['target_layers'],x['task']['id'],len(x['task']['prompt_ids'])) for f,x in selected.items()})
if __name__=='__main__':main()
