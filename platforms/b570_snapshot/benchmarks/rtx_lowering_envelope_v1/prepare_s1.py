"""Full descriptor and immutable S1 command/wire plan; no backend or model calls."""
import copy,hashlib,json,sys
from pathlib import Path
from s0_budget import ROOT,save
from recover_s0 import sha
sys.path.insert(0,str(ROOT.parents[1]/'docs/experiments/rtx_lowering_envelope_20261015'))
import design_checks as d
def input_descriptor(ne,nb,type_):return dict(ne=ne,nb=nb,type=type_,bytes=(4 if type_==0 else 2)+sum((x-1)*y for x,y in zip(ne,nb)))
def main():
    snapshots=json.loads((ROOT/'FULL_SNAPSHOTS.json').read_bytes())['contexts'];descriptors=[]
    for c in snapshots:descriptors.append(dict(id=c['context']['id'],kind='ACTUAL_FULL_SNAPSHOT',metadata=c['metadata'],snapshot_index=c['index'],root=c['root'],registry=c['registry']))
    for family in d.FAMILIES:
        first=next(c for c in snapshots if c['context']['family']==family);meta=first['metadata'];D=meta['Q']['ne'][0];H=meta['Q']['ne'][2];G=meta['K']['ne'][2]
        for extent in (256,512,768,1024):
            for q in (1,2,3,4):
                for strides in ('inherited_permuted','compact'):
                    m=copy.deepcopy(meta);m['q_occupancy']=q;m['captured_key_extent']=extent
                    m['Q']=input_descriptor([D,q,H,1],[4,4*D*H,4*D,4*D*H*q] if strides=='inherited_permuted' else [4,4*D,4*D*q,4*D*H*q],0)
                    m['K']=input_descriptor([D,extent,G,1],[2,2*D*G,2*D,2*D*G*1024],1)
                    m['V']=input_descriptor([extent,D,G,1],[2,2048,2048*D,2048*D*G],1)
                    m['mask']=input_descriptor([extent,q,1,1],[4,4*extent,4*extent*q,4*extent*q],0)
                    descriptors.append(dict(id=f'{family}_superset_K{extent}_q{q}_{strides}',kind='SOURCE_DERIVED_SHAPE_SUPERSET_NO_PAYLOAD',metadata=m,
                        derivation='ctx1024; non-flash cache get_n_kv=max256 padding, capped cells.size; H/G/D inherited, target ub4/VERIFY k3+1; single stream; observed source strides plus legal compact Q'))
    save(ROOT/'DESCRIPTOR_PLAN.json',dict(schema=1,descriptors=descriptors,runtime_directory='D:/hs104-e1-v1/native/build/bin',
        actual_full_snapshots=72,source_shape_superset=96,padding_source_sha256=sha(ROOT/'native/source/src/llama-kv-cache.cpp'),
        support_status='NOT_QUERIED_S0',arithmetic_placement='NOT_EXECUTED_S0',new_GPU_device_queries=0))
    slots=[dict(id='S1/census',kind='support',graph_computes=0,warmups=0)]
    for c in snapshots:
        for arm in ('MQ','PQ','QB','QH_C','QH_D'):
            for repeat in (0,1):slots.append(dict(id=f'S1/numeric/{c["index"]:03d}/{arm}/{repeat}',kind='numeric',descriptor=c['context']['id'],root=c['root'],layout=arm,graph_computes=1,warmups=0,repeat=repeat))
    for family,phase,q,layer in d.profile_coordinates():
        c=next(x for x in snapshots if (x['context']['family'],x['context']['phase'],x['context']['q'],x['context']['layer'])==(family,phase,q,layer))
        for block in range(3):
            names=('PQ','QB','SELECTED_QH');rotation=(block+q)%3;names=names[rotation:]+names[:rotation]
            for arm in names:slots.append(dict(id=f'S1/timing/{c["index"]:03d}/{block}/{arm}',kind='clean',descriptor=c['context']['id'],root=c['root'],layout=arm,block=block,graph_computes=9,warmups=1))
        for arm in ('PQ','QB','SELECTED_QH'):slots.append(dict(id=f'S1/trace/{c["index"]:03d}/{arm}',kind='trace',descriptor=c['context']['id'],root=c['root'],layout=arm,graph_computes=2,warmups=1))
    assert len(slots)==1009 and sum(s['graph_computes'] for s in slots)==2808 and sum(s['warmups'] for s in slots)==288
    for s in slots:
        s['wire_json']=json.dumps(s,sort_keys=True,separators=(',',':'));s['wire_sha256']=hashlib.sha256(s['wire_json'].encode()).hexdigest()
        s['command_template']=['native/build/bin/lowering113.exe','--gpu-census' if s['kind']=='support' else '--gpu-run','ADMITTED_IMMUTABLE_JOB_JSON','NEW_SLOT_OUTPUT']
    save(ROOT/'S1_PLAN.json',dict(schema=1,slots=slots,ceilings=d.budgets(),owned_seconds=7200,derived_bytes=4*1024**3,
        selected_QH='PENDING_COMPLETE_PREOUTPUT_ACTUAL_CENSUS',source_superset='metadata only; no synthetic tensors enter numerical replay',
        authorization='NOT_GRANTED; S0 is CPU engineering only',mask=3,k=3,profiles='separate from clean; unavailable means explicit UNKNOWN; no automatic profiler replay'))
    print(json.dumps(dict(descriptors=len(descriptors),slots=len(slots),computes=2808,warmups=288)))
if __name__=='__main__':main()
