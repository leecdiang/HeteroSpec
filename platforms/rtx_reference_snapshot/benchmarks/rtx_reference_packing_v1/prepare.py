"""Prospective native selection and fixed small parity panel; zero GPU work."""
import hashlib
import json
from pathlib import Path
import random
import struct
import fp32

ROOT=Path(__file__).parent
SOURCE=Path('D:/hs104-e1-v1')
PR104=Path('C:/Users/ASUS/Documents/Codex/2026-10-14/heterospec-pr-104-rtx-implementation-pq/work/HeteroSpec-pr104')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,sort_keys=True,indent=2);f.write('\n')
def fbits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def canonical(root,m):
    assert m['type']==0
    b=(root/m['file']).read_bytes();out=bytearray();ne,nb=m['ne'],m['nb']
    for i3 in range(ne[3]):
        for i2 in range(ne[2]):
            for i1 in range(ne[1]):
                for i0 in range(ne[0]):
                    offset=sum(a*b for a,b in zip((i0,i1,i2,i3),nb));assert offset+4<=len(b)
                    out.extend(b[offset:offset+4])
    return bytes(out)
def eligible(a):
    res=a.get('result',{});qual=res.get('numerical',{}).get('qualification',{})
    return (res.get('capture_on_off_full_equal') is True and
            res.get('source_lifetime',{}).get('same_captured_input_bytes') is True and
            all(qual.get('own_path',{}).get(s) is True for s in ('QK','softmax','AV')) and
            qual.get('repeatability',{}).get('MQ') is True)
def main():
    assert json.loads((SOURCE/'RUN_COMPLETE.json').read_bytes())['contexts']==72
    accepted=PR104/'benchmarks/rtx_qb_confirmation_v1/final_20261015/AUTHENTICATED_COMBINED_RESTORE.json'
    assert accepted.exists(),'PR104 must be sealed before new research'
    (ROOT/'inputs').mkdir(exist_ok=False)
    records=[json.loads(p.read_bytes()) for p in sorted((SOURCE/'contexts').glob('*.json'))];assert len(records)==72
    coverage=[];sources=[];workloads=[]
    for family in ('Qwen','SmolLM2','Llama'):
        for phase in ('prefill','continuation'):
            for q in (1,2,3,4):
                # Only provenance/own-path/repeatability; no PQ/QB equality or latency.
                candidates=[a for a in records if (a['context']['family'],a['context']['phase'],a['context']['q'])==(family,phase,q) and eligible(a)]
                if not candidates:coverage.append(dict(family=family,phase=phase,q=q,status='NOT_AVAILABLE'));continue
                a=min(candidates,key=lambda a:(a['context']['layer'],a['context']['task']['id'],a['index']))
                index=a['index'];ctx=a['context'];reg=json.loads((SOURCE/f'snapshot_registry/{index:03d}.json').read_bytes());root=Path(reg['root'])
                assert reg['registry']==a['result']['source_lifetime']['registry']
                for name,h in reg['registry'].items():assert sha(root/name)==h
                m=json.loads((root/'snapshot.json').read_bytes());boundary=json.loads((root/'LOGICAL_BOUNDARY.json').read_bytes())
                assert boundary['native_decode']['role']=='target' and boundary['native_decode']['scope_mask']==0
                assert m['q_occupancy']==q and m['layer']==ctx['layer'] and m['phase']==phase
                qual=a['result']['numerical']['qualification'];replays=[]
                for repeat in (0,1):
                    name=f'MQ-r{repeat}';d=SOURCE/f'operators/{index:03d}'/name;receipt=json.loads((d/'REPLAY.json').read_bytes())
                    for filename,h in qual['artifacts'][name].items():assert sha(d/filename)==h
                    for role,readback in receipt['fixed_inputs'].items():
                        assert readback['readback_bitwise_equal'] and all(readback[s]==m[role][s] for s in ('ne','nb','type'))
                    for stage in ('QK','softmax','AV'):assert canonical(root,m['native_'+stage])==(d/(stage+'.bin')).read_bytes()
                    replays.append(dict(repeat=repeat,files=qual['artifacts'][name],receipt=receipt))
                pm,vm=m['native_softmax'],m['V'];assert pm['type']==0 and vm['type']==1
                keys=min(64,pm['ne'][0]);channels=2;pb=(root/pm['file']).read_bytes();vb=(root/vm['file']).read_bytes()
                assert vm['ne'][0]==pm['ne'][0] and vm['ne'][1]>=channels
                P=[[struct.unpack_from('<I',pb,t*pm['nb'][0]+j*pm['nb'][1])[0] for t in range(keys)] for j in range(q)]
                V=[[fbits(struct.unpack_from('<e',vb,t*vm['nb'][0]+c*vm['nb'][1])[0]) for c in range(channels)] for t in range(keys)]
                for row in P+V:
                    for b in row:fp32.decode(b)
                ident=f'native_{family}_{phase}_q{q}'
                w=dict(id=ident,source='NATIVE_OPERAND_SUBVIEW_PR104',q=q,keys=keys,channels=channels,P=P,V=V,
                       owner=f'PR104_context_{index}',epoch=0,layer=ctx['layer'],family=family,phase=phase,
                       source_index=index,subview='head0, KVhead0, channels[0:2], keys[0:min(64,K)], all physical queries; P not renormalized',
                       new_native_capture=False,legacy_RTX_arithmetic_reproduced=False)
                save(ROOT/'inputs'/f'{ident}.json',w);workloads.append(ident)
                coverage.append(dict(family=family,phase=phase,q=q,status='QUALIFIED_NATIVE_SUBVIEW',source_index=index,layer=ctx['layer']))
                sources.append(dict(id=ident,source_root=str(root),registry=reg['registry'],metadata=m,logical_boundary=boundary,
                                    own_path=qual['own_path'],MQ_repeatability=qual['repeatability']['MQ'],MQ_replays=replays,
                                    caller_positions_to_physical_query_attribution='UNKNOWN',selection_uses_PQ_QB_equality_or_speed=False))
    rng=random.Random(20261015)
    for q in (1,4):
        P=[]
        for j in range(q):
            row=[]
            for t in range(32):
                pair=[0,fbits(1/32)];rng.shuffle(pair);row.extend(pair)
            P.append(row)
        V=[[fbits(rng.randint(-32,32)/16) for c in range(2)] for t in range(64)];ident=f'synthetic_q{q}_k64'
        save(ROOT/'inputs'/f'{ident}.json',dict(id=ident,source='SYNTHETIC',q=q,keys=64,channels=2,P=P,V=V,owner=ident,epoch=0,seed=20261015))
        workloads.append(ident)
    save(ROOT/'NATIVE_COVERAGE.json',dict(groups=coverage,sources=sources,source='completed PR104 E1',
         source_commit='f997262d6b0accb126a1217c9356745cc8bbf708',accepted_restore_receipt_sha256=sha(accepted),
         run_complete_sha256=sha(SOURCE/'RUN_COMPLETE.json'),selection_priority='layer0,middle,last; lexical task ID; stable context index'))
    base=dict(lanes=4,issue_rate=1,compute_latency=2,contexts=8,context_ports=4,context_write_ports=4,
              buffer_bytes=512,banks=4,bank_ports=4,broadcast_words=8,memory_ports=4,memory_latency=2,queue_depth=8,
              output_ports=4,output_latency=1,store_queue_depth=4,extra_issue_latency=0)
    resources=[dict(id='ABSTRACT_WIDE',**base),dict(id='ABSTRACT_SUPPLY_LIMITED',**(base|dict(memory_ports=1,broadcast_words=2,queue_depth=2))),
               dict(id='ABSTRACT_BANK_CONFLICT',**(base|dict(banks=1,bank_ports=2)))]
    from model import MAPPINGS
    cells=[dict(workload=w,resource=r['id'],mapping=m) for w in workloads for r in resources for m in MAPPINGS]
    save(ROOT/'PLAN.json',dict(schema=2,status='PROSPECTIVE_PARITY_PANEL',reference='DECLARED_ARCHITECTURE_REFERENCE',
        workloads=workloads,resources=resources,cells=cells,seed=20261015,
        mapping_capabilities='Five aliases of same concrete legal policy: both proposed capabilities already available to B1 and not legitimately excluded from B0',
        parity_scope='Rectangular 64-key two-channel finite panel, one stable-priority key-wave policy; not optimality or ragged schedule-set equivalence',
        buffer_accounting='64B global control plus20B per context plus12B per resident or in-flight input; no free spill',
        policy_switch_cost='zero for identical static mappings; extra issue latency explicitly tested as engineering negative',
        budget=dict(child_seconds=14400,rss_bytes=8589934592,derived_bytes=2147483648,formal_cells=1024,max_heavy_jobs=1),
        crop_rule_frozen_before_candidate_comparisons=True,new_GPU_model_operator_starts=0))
    print(json.dumps(dict(workloads=len(workloads),native=len(sources),missing_groups=sum(g['status']=='NOT_AVAILABLE' for g in coverage),cells=len(cells))))
if __name__=='__main__':main()
