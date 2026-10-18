"""Explicit synthetic CPU envelopes; never new CUDA observations or times."""
import copy,json,shutil
from pathlib import Path
from common import V,load,save,sha,pin
import audit
def main():
    root=V/'cpu_tests/qpc_audit_fixture';root.mkdir(exist_ok=False);(root/'cas').mkdir();plan=load(V/'PLAN.json');slot=plan['clean_slots'][0];n=root/'clean/000/native';n.mkdir(parents=True)
    old=Path('D:/hs114-s1a-bridge-v2/numerical/002');oldr=load(old/'native/RECORD.json');pid=oldr['pid'];oldexe=oldr['modules'][0];newexe=str(V/'s1b_clean.exe')
    for name in ['CORE_ADMITTED_BEFORE_CUDA.json','PLUGIN_CORE_IMPORTS.json']:shutil.copyfile(old/'native'/name,n/name)
    for prefix in ['native','readiness']:
        for suffix in ['PROCESS.json','LIFETIME.json','JOB_EVENTS.json']:
            data=load(old/(prefix+'.'+suffix))
            if suffix=='JOB_EVENTS.json':
                for e in data['events']:
                    if e.get('image')==oldexe:e['image']=newexe
            save(n.parent/(prefix+'.'+suffix),data)
    expected=next(r for r in load(V/'CPU_EXPECTED.json') if (r['descriptor_id'],r['layout'])==(slot['descriptor'],slot['layout']));graph=copy.deepcopy(expected)
    for r in graph['nodes']:r['CUDA_support']=True;r['placement']='CPU_SYNTHETIC_CUDA_ENVELOPE_ONLY'
    graph['ownership']=[dict(id='input'+str(i),has_buffer=True,host=False,actual=1,intended=1,valid=True) for i in range(4)]+[dict(id=r['id'],has_buffer=True,host=False,actual=1,intended=1,valid=True) for r in graph['nodes'] if not r['metadata_only']]
    save(n/'GRAPH_AND_OWNERSHIP.json',graph)
    intervals=[]
    for i in range(9):
        t=1000+1000*i;intervals.append(dict(index=i,warmup=i==0,begin=t,compute_return=t+200,sync_return=t+300,readback_return=t+350,audit_return=t+400));save(n/f'GRAPH_STARTED_{i}.json',dict(index=i,warmup=i==0))
    modules=[newexe if p==oldexe else p for p in oldr['modules']];record=dict(status='COMPLETED',kind='clean',layout=slot['layout'],pid=pid,graph_computes=9,warmups=1,measured=8,QPC_frequency=10000000,intervals=intervals,cost_ticks=dict(source_read=100,CPU_materialize_full_inputs=100,H2D_and_setup_sync=100),modules=modules)
    save(n/'RECORD.json',record);inventory=load(old/'MODULE_FILES.json');inventory=[p for p in inventory if p['path']!=oldexe];inventory.append(pin(V/'s1b_clean.exe'));save(n.parent/'MODULE_FILES.json',inventory)
    meta=plan['descriptors'][0]['metadata']
    def retain_source(row,name):
        p=Path(row['path']);dest=root/'cas'/(row['sha256']+'.bin')
        if not dest.exists():shutil.copyfile(p,dest)
        save(n/(name+'.BLOB.json'),dict(artifact=name,slot=slot['id'],pid=pid,bytes=row['bytes'],sha256=row['sha256'],cas_relative='cas/'+row['sha256']+'.bin'))
    for role in ['Q','K','V','mask']:
        row=next(r for r in slot['input_files'] if Path(r['path']).name==meta[role]['file'])
        for when in ['before','after']:retain_source(row,f'input_{role}.{when}')
    for i in range(9):retain_source(slot['ordinary_reference'],f'ordinary_{i}')
    oldf=load('D:/hs114-bridge-v2/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v2/F0.json');f=dict(hosts=dict(clean=pin(V/'s1b_clean.exe')),numerical_DLLs=oldf['numerical_DLLs'],runtime_directory=oldf['runtime_directory'],console_helper=oldf['console_helper'],admission_policy=oldf['admission_policy'],QPC_frequency=10000000)
    result=audit.inspect(slot,n.parent,f,plan,expected,root);assert len(result['intervals'])==9 and round(result['mean_FG_ms']*record['QPC_frequency']/1000)==300
    negative=[]
    changes=[('timer_frequency','RECORD.json',lambda x:x.__setitem__('QPC_frequency',1)),('clock_backwards','RECORD.json',lambda x:x['intervals'][1].__setitem__('sync_return',0)),('wrong_warmup','RECORD.json',lambda x:x.__setitem__('warmups',0)),('extra_call','RECORD.json',lambda x:x.__setitem__('graph_computes',10)),('wrong_device','GRAPH_AND_OWNERSHIP.json',lambda x:x['ownership'][0].__setitem__('actual',2)),('unsupported','GRAPH_AND_OWNERSHIP.json',lambda x:x['nodes'][0].__setitem__('CUDA_support',False)),('wrong_param','GRAPH_AND_OWNERSHIP.json',lambda x:x['nodes'][0]['op_params'].__setitem__(0,255)),('missing_plugin_symbol','PLUGIN_CORE_IMPORTS.json',lambda x:x.pop()),('wrong_input','input_Q.after.BLOB.json',lambda x:x.__setitem__('sha256','0'*64)),('wrong_ordinary','ordinary_8.BLOB.json',lambda x:x.__setitem__('sha256','0'*64))]
    for label,name,mutate in changes:
        case=root/'negative'/label;shutil.copytree(n.parent,case);p=case/'native'/name;x=load(p);mutate(x);p.write_text(json.dumps(x),encoding='utf-8');error=None
        try:audit.inspect(slot,case,f,plan,expected,root)
        except Exception as exc:error=repr(exc)
        assert error,label;negative.append(dict(case=label,error=error))
    case=root/'negative/heavy_observer';shutil.copytree(n.parent,case);save(case/'native/QK.BLOB.json',dict(CPU_fake=True))
    try:audit.inspect(slot,case,f,plan,expected,root)
    except AssertionError:negative.append(dict(case='heavy_stage_observer',rejected=True))
    assert len(negative)==11
    save(V/'CPU_QPC_AUDIT_TESTS.json',dict(status='PASS',full_cpu_fixture_inspections=12,negative=negative,real_bytes_source='PR116 complete input and ordinary bytes;runtime envelopes explicitly synthetic CPU fixtures',new_GPU_queries=0,CUDA_loads=0,graph_computes=0,GPU_times_created=False))
    print('PASS full independent CPU raw inspector and11negative module/timer/device/input/output/observer cases')
if __name__=='__main__':main()
