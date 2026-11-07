"""CPU byte/address causal witnesses from retained D0 interventions and reversal."""
import struct
from pathlib import Path
from common import V,load,save,sha
from run import root
rows=[]
for p in sorted((root()/'attempts').glob('*/JOB.json')):
    job=load(p)
    if job['stage']!='D0':continue
    n=p.parent/'native';r=load(n/'RECORD.json');g=load(n/'GRAPH.json');addresses={x['id']:x for x in g['addresses']};row=dict(attempt=p.parent.name,arm=job['block'],lifecycle=job['lifecycle'],calls=len(r['calls']),ordinary_exact=sum(x['ordinary_exact'] for x in r['calls']),input_after=r['input_after_equal'],host_input_unchanged=r['host_input_unchanged'],overlays=[])
    if job['lifecycle']=='original_resident':
        output=(n/'ordinary_0.bin').read_bytes()
        for role,input_id,node_id in [('K','input1','node2'),('V','input2','node4')]:
            offset=addresses[node_id]['data']-addresses[input_id]['data'];after=(n/f'input_{role}_call0.bin').read_bytes();before=(n/f'input_{role}_before.bin').read_bytes();assert offset>=0 and offset+len(output)<=len(after);assert after[offset:offset+len(output)]==output and after!=before
            row['overlays'].append(dict(role=role,input_relative_offset=offset,bytes=len(output),after_region_equals_first_ordinary=True,before_region_sha256=__import__('hashlib').sha256(before[offset:offset+len(output)]).hexdigest(),after_region_sha256=__import__('hashlib').sha256(after[offset:offset+len(output)]).hexdigest()))
        v=(n/'input_V_call0.bin').read_bytes();observed=struct.unpack_from('<f',(n/'ordinary_1.bin').read_bytes())[0];half=struct.unpack_from('<e',v)[0];assert half==observed==512.;row['second_output_first']=observed;row['overwritten_V_first_FP16']=half;row['ordinary0_low16bits']=output[:2].hex()
    rows.append(row)
save(V/'D0_FINDINGS.json',dict(status='REPRODUCED_INPUT_STORAGE_REUSE_AND_INTERVENTION_REVERSAL',attempts=rows,scope='anchor only for mechanistic byte witness;full24 repeatability established separately by N1',cause='host assumes immutable resident inputs but graph allocator recycles K/V storage for AV/ordinary output after last read;external persistent input owners prevent it',proof='overlap addresses+exact overwritten bytes+FP16 reinterpretation512+reupload intervention+persistent storage+original reversal',not_claimed=['same kernel','same reduction DAG','universal backend equivalence','qualification of historical stopped r2'],historical_r2_unchanged=True))
print('D0 causal witnesses',len(rows))
