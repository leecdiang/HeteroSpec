"""CPU/disk only: original24 coordinates and exact future cost wires."""
from pathlib import Path
import shutil,datetime,struct
from common import V,RUN,load,save,pin,sha
OLD=Path('D:/hs114-bridge-v2/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v2')
RAW=Path('D:/hs114-s1a-bridge-v2')
ROOT='D:/hs116-s1b-cost-v1'
def main():
    prior=load(OLD/'PLAN.json');a=load(OLD/'closure/ANALYSIS.json');closure=load(OLD/'numerical_delivery/CLOSURE.json')
    assert a['status']=='COMPLETE_QUALIFIED_PANEL' and a['completed_qualified']==240 and closure['analyses_byte_equal']
    assert sha(OLD/'closure/ANALYSIS.json')==sha(OLD/'closure/FRESH_ANALYSIS.json')==closure['original_analysis_sha256']
    previous=load('D:/hs113-bridge/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v1/S1B_CPU_INTEGRATION.json')
    assert previous['actual_native_clean_graphs']==72
    plan=dict(schema=1,run_id=RUN,execution_root=ROOT,descriptors=prior['descriptors'],clean_slots=[],trace_slots=[],layouts=['PQ','QB','QH_C'])
    refs={};inputs={};outputs=0
    for d in prior['descriptors']:
        for l in plan['layouts']:
            entries=next(c for c in a['contexts'] if c['descriptor']==d['id'])['layouts'][l]
            assert all(e and e['module_input_graph_placement_completion_controls']=='PASS' for e in entries)
            r0=RAW/entries[0]['directory']/'native';r1=RAW/entries[1]['directory']/'native'
            def blob(name):
                b=load(r0/(name+'.BLOB.json'));c=load(r1/(name+'.BLOB.json'));assert b['sha256']==c['sha256'];p=RAW/b['cas_relative'];assert sha(p)==b['sha256'];return pin(p)
            refs[d['id'],l]=dict(ordinary_reference=blob('ordinary'),AV_reference=blob('AV'))
            outputs+=refs[d['id'],l]['ordinary_reference']['bytes']*29 #3clean x9 +1trace x2
        for row in d['input_files']:inputs[row['sha256']]=row['bytes']
    def make(d,l,kind,i,block=None):
        return dict(run_id=RUN,kind=kind,stage='TRACE' if kind=='trace' else 'CLEAN',index=i,id=f's1b/{kind}/{i:03d}/{d["id"]}/{l}',descriptor=d['id'],family=d['family'],phase=d['phase'],q=d['q'],layer=d['layer'],block=block,layout=l,root=d['root'],input_files=d['input_files'],runtime_directory=load(OLD/'F0.json')['runtime_directory'],core_sha256=load(OLD/'F0.json')['numerical_DLLs']['ggml-base.dll'],ordinary_reference=refs[d['id'],l]['ordinary_reference'],AV_reference=refs[d['id'],l]['AV_reference'],cas_root=ROOT+'/cas',native_output=ROOT+f'/{kind}/{i:03d}/native',warmups=1,measured_evaluations=1 if kind=='trace' else 8,graph_computes=2 if kind=='trace' else 9)
    for block in range(3):
        q1=[d for d in prior['descriptors'] if d['q']==1];many=[d for d in prior['descriptors'] if d['q']>1]
        q1=q1[block*2:]+q1[:block*2];many=many[block*6:]+many[:block*6]
        for ci,d in enumerate(q1+many):
            order=plan['layouts'];shift=(ci+block)%3
            for l in order[shift:]+order[:shift]:plan['clean_slots'].append(make(d,l,'clean',len(plan['clean_slots']),block))
    for d in prior['descriptors']:
        for l in plan['layouts']:plan['trace_slots'].append(make(d,l,'trace',len(plan['trace_slots'])))
    plan['census_job']=dict(run_id=RUN,kind='support',stage='CENSUS',id='s1b/support/all72',graph_computes=0,warmups=0,native_output=ROOT+'/census/native',runtime_directory=load(OLD/'F0.json')['runtime_directory'],cas_root=ROOT+'/cas')
    plan['order']='Three fixed rotated acquisition blocks;all18 q1 hosts first in each block. Context family order rotated per block;Latin layout positions balanced,not all six directed carryover orders.'
    plan['qualification']='Every first warmup and8ordinary readbacks must equal PR116 bytes. Block0 all72 clean graphs provides independent actual clean GPU correctness before later blocks can be authorized. No extra numerical or probe calls.'
    plan['trace_status']='PLANNED_NOT_ADMITTED_PROFILE_UNAVAILABLE';plan['original_caps']=dict(clean_hosts=216,trace_hosts=72,graph_calls=2088,warmups=288)
    save(V/'PLAN.json',plan)
    save(V/'EVIDENCE_BINDING.json',dict(PR116_commit='2b5ed1552263907df3adfdff9b0121d115734a6c',F0=pin(OLD/'F0.json'),analysis=pin(OLD/'closure/ANALYSIS.json'),fresh_analysis=pin(OLD/'closure/FRESH_ANALYSIS.json'),closure=pin(OLD/'numerical_delivery/CLOSURE.json'),archive=pin(OLD/'closure/RAW_BRIDGE.zip'),prior_S1B_CPU_audit=pin(Path('D:/hs113-bridge/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v1/S1B_CPU_INTEGRATION.json')),qualification='Exposed fixed24 only;not full72,natural decoder or cost evidence'))
    save(V/'STORAGE_BASIS.json',dict(unique_full_inputs_bytes=sum(inputs.values()),all_2088_ordinary_outputs_no_dedup_bytes=outputs,input_readback_traffic=sum(sum(d['metadata'][r]['bytes'] for r in ['Q','K','V','mask'])*2*3*4 for d in prior['descriptors']),maximum_input_bytes=max(sum(d['metadata'][r]['bytes'] for r in ['Q','K','V','mask']) for d in prior['descriptors'])))
    print('Prepared216clean+72trace slots;2088calls;CPU only')
if __name__=='__main__':main()
