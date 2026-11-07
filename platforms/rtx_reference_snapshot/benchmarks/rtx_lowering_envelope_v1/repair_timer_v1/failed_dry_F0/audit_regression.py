"""Independent full-byte CPU checks for the prospective engineering regression."""
import hashlib,json,struct
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import audit
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ordinary(av,meta):
    d,q,h,_=meta['native_AV']['ne'];assert len(av)==d*q*h*4
    return b''.join(av[(a*q+j)*d*4:(a*q+j+1)*d*4] for j in range(q) for a in range(h))
def finite(data):return all((w&0x7f800000)!=0x7f800000 for (w,) in struct.iter_unpack('<I',data))
def inspect(slot,directory,f0,prior):
    n=directory/'native';record=load(n/'RECORD.json');meta=load(Path(slot['root'])/'snapshot.json')
    assert record['graph_computes']==1 and record['warmups']==0 and record['kind']=='numeric'
    assert load(n/'GRAPH_CALL_RETURNED.json')['status']==0 and load(n/'SYNCHRONIZATION_RETURNED.json')['status']==0
    assert load(n/'GRAPH_STARTED_0.json')==dict(index=0,warmup=False)
    assert not (n/'GRAPH_STARTED_1.json').exists()
    audit.modules(record['modules'],f0['numerical_DLLs'],f0['runtime_directory'])
    gate=load(n/'CORE_ADMITTED_BEFORE_CUDA.json');core=gate['core']
    assert core['sha256']==f0['numerical_DLLs']['ggml-base.dll'] and core['ready'] and core['events'].count('dll_initializer_returned')==1
    assert gate['host_import']['owner_path']==core['path'] and gate['host_import']['IAT_target']==core['functions']['ggml_init']['address']
    assert gate['registry_import']['sha256']==f0['numerical_DLLs']['ggml.dll']
    plugin=load(n/'PLUGIN_CORE_IMPORTS.json');assert len(plugin)==f0['plugin_core_import_count']
    assert all(p['owner_path']==core['path'] for p in plugin)
    graph=record['nodes'];assert graph['actual_placement']=='CUDA0 direct backend; no scheduler' and graph['full_support']
    assert len(graph['nodes'])==slot['registered_support_queries']
    for t in graph['nodes']:
        assert type(t['CUDA_support'])is bool
        if not t['metadata_only']:assert t['CUDA_support'] and t['placement'] and 'CUDA' in t['placement']
    for role in ('Q','K','V','mask'):
        original=(Path(slot['root'])/meta[role]['file']).read_bytes()
        assert (n/('input_'+role+'.before.bin')).read_bytes()==original==(n/('input_'+role+'.after.bin')).read_bytes()
    stages={s:(n/(s+'.bin')).read_bytes() for s in ('QK','softmax','AV')}
    assert all(finite(x) for x in stages.values())
    assert (n/'ordinary.bin').read_bytes()==ordinary(stages['AV'],meta)
    references={s:audit.canonical(slot['root'],meta['native_'+s]) for s in stages}
    comparisons={s:audit.numeric(references[s],stages[s]) for s in stages}
    if slot['layout']=='MQ' or slot['group']=='common_q1':assert all(c['bitwise_equal'] for c in comparisons.values()),'MQ own path/q1 mandatory gate'
    if slot['layout'] in ('PQ','QB'):
        for s,data in stages.items():
            original=Path(f0['old_operator_root'])/f'{slot["old_index"]:03d}'/(slot['layout']+'-r'+str(slot['repeat']))/(s+'.bin')
            assert original.read_bytes()==data,'inherited PQ/QB gate'
    repeated=None
    if slot['repeat']==1:
        first=next(p for p in prior if p['descriptor']==slot['descriptor'] and p['layout']==slot['layout'] and p['repeat']==0)
        first_directory=Path(first['directory'])/'native'
        assert all((first_directory/(s+'.bin')).read_bytes()==data for s,data in stages.items())
        assert (first_directory/'ordinary.bin').read_bytes()==(n/'ordinary.bin').read_bytes();repeated='BITWISE_PASS'
    for other in prior:
        if other['descriptor']==slot['descriptor'] and {other['layout'],slot['layout']}=={'PQ','QB'}:
            assert all((Path(other['directory'])/'native'/(s+'.bin')).read_bytes()==data for s,data in stages.items()),'PQ/QB correspondence gate'
    # Valid finite QH q2 differences do not alter the fixed selected variant.
    return dict(slot=slot['id'],descriptor=slot['descriptor'],layout=slot['layout'],repeat=slot['repeat'],directory=str(directory),
                module_input_placement_completion_controls='PASS',repeatability=repeated,vs_original_MQ=comparisons,
                status='FINITE_EMPIRICAL_DIFFERENCE' if any(not c['bitwise_equal'] for c in comparisons.values()) else 'BITWISE_MQ_CORRESPONDENCE',
                cost_qualification='NONE: engineering observer includes IO, not a timing experiment')
