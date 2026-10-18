"""Real-byte CPU semantic tests, never evidence of new CUDA execution.

Synthetic runtime envelopes are explicitly adapted from retained GPU14 records;
all tensors are real old bytes or deliberately labeled negative perturbations.
"""
import argparse,copy,json,shutil,struct,subprocess
from pathlib import Path
from common import V,load,save,sha,pin,blob,retain
import analyzer as A
from pe_review import PE
def reject(label,fn,results):
    try:fn()
    except Exception as e:results.append(dict(label=label,status='EXPECTED_REJECTION',error=repr(e)));return
    raise AssertionError('negative accepted: '+label)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tag',default='final');args=ap.parse_args()
    plan=load(V/'PLAN.json');refs=load(V/'REFERENCE_INDEX.json');runtime=Path(plan['census_wire']['runtime_directory'])
    exports=dict(core=PE(runtime/'ggml-base.dll').exports(),registry=PE(runtime/'ggml.dll').exports(),plugin_core_symbols=PE(runtime/'ggml-cuda.dll').imports()['ggml-base.dll'],core_sha256=sha(runtime/'ggml-base.dll'),registry_sha256=sha(runtime/'ggml.dll'))
    if (V/'ABI_EXPORTS.json').exists():assert load(V/'ABI_EXPORTS.json')==exports
    else:save(V/'ABI_EXPORTS.json',exports)
    rows=load(V/'CPU_WIRES.json')['records'];expected=[]
    for r in rows:
        if r['repeat']==0:expected.append({k:v for k,v in r.items() if k not in ('slot','repeat','wire_file_sha256')})
    assert len(expected)==360
    if (V/'CPU_GRAPH_EXPECTED.json').exists():assert load(V/'CPU_GRAPH_EXPECTED.json')==expected
    else:save(V/'CPU_GRAPH_EXPECTED.json',expected)
    table={(r['descriptor_id'],r['layout']):r for r in expected}
    positive=0;neg=[];pure={}
    for d in plan['descriptors']:
        meta,reference=A.reference_values(d['id'],V/'reference_cas',refs)
        for layout in A.LAYOUTS:
            hist={s:blob(V/'reference_cas',refs[d['id']]['historical'][layout+'-r0/'+s]) for s in A.STAGES[:-1]} if layout in ('PQ','QB') else None
            values=copy.deepcopy(reference)
            if hist:values.update(hist);values['ordinary']=A.restore(values['AV'],meta)
            if d['q']>1 and layout.startswith('QH'):
                old=struct.unpack('<f',values['QK'][:4])[0];values['QK']=struct.pack('<f',old+(0.125 if layout=='QH_C' else .25))+values['QK'][4:]
            for repeat in (0,1):
                s=next(s for s in plan['numerical_slots'] if (s['descriptor'],s['layout'],s['repeat'])==(d['id'],layout,repeat))
                actual_hist={s:blob(V/'reference_cas',refs[d['id']]['historical'][layout+'-r'+str(repeat)+'/'+s]) for s in A.STAGES[:-1]} if hist else None
                A.verify_numeric(s,meta,values,reference,actual_hist,values if repeat else None);positive+=1
            if d['family']=='Qwen' and d['q']==2 and d['layer']==0 and d['phase']=='prefill':pure[layout]=(s,meta,values,reference,hist)
    assert positive==720
    s,m,v,ref,h=pure['QH_C'];base=copy.deepcopy(v)
    for label,stage,value in [('NaN','QK',struct.pack('<I',0x7fc00001)+v['QK'][4:]),('truncated','AV',v['AV'][:-4]),('wrong_ordinary_order','ordinary',v['ordinary'][4:]+v['ordinary'][:4])]:
        bad=dict(v);bad[stage]=value;reject(label,lambda bad=bad:A.verify_numeric(s,m,bad,ref,None,v),neg)
    bad=dict(v);bad['QK']=struct.pack('<f',.75)+v['QK'][4:]
    reject('repeat_changed',lambda:A.verify_numeric(s,m,bad,ref,None,v),neg)
    reject('missing_independent_repeat',lambda:A.verify_numeric(s,m,v,ref,None,None),neg)
    mq=pure['MQ'];bad=dict(mq[2]);bad['QK']=struct.pack('<f',.75)+bad['QK'][4:]
    reject('MQ_ownpath',lambda:A.verify_numeric(mq[0],m,bad,ref,None,mq[2]),neg)
    pq=pure['PQ'];bad=dict(pq[2]);bad['QK']=struct.pack('<f',.75)+bad['QK'][4:]
    reject('historical_PQ',lambda:A.verify_numeric(pq[0],m,bad,ref,pq[4],pq[2]),neg)
    q1=next(s for s in plan['numerical_slots'] if s['q']==1 and s['layout']=='QH_D' and s['repeat']==0);qm,qr=A.reference_values(q1['descriptor'],V/'reference_cas',refs)
    bad=dict(qr);bad['QK']=struct.pack('<f',.75)+bad['QK'][4:];reject('q1_common_all_layouts',lambda:A.verify_numeric(q1,qm,bad,qr,None),neg)
    census=dict(records=copy.deepcopy(expected),support_queries=5418,GPU_initializations=1,graph_computes=0,allocations=0)
    for r in census['records']:
        r['full_support']=True
        for n in r['nodes']:n['CUDA_support']=True
    assert A.census_decision(census,table,plan)['numerical_admitted']
    for layout,q,blocked in [('QH_D',2,False),('QH_C',2,True),('MQ',2,True),('QH_D',1,True)]:
        c=copy.deepcopy(census);target=next(r for r in c['records'] if r['layout']==layout and r['descriptor_id'].endswith('q'+str(q)))
        next(n for n in target['nodes'] if not n['metadata_only'])['CUDA_support']=False;target['full_support']=False
        decision=A.census_decision(c,table,plan);assert decision['numerical_admitted']==(not blocked) and len(decision['denied_slots'])==2 and decision['primary_QH']=='QH_C'
    c=copy.deepcopy(census);c['records']=c['records'][:-1];reject('missing_census_graph',lambda:A.census_decision(c,table,plan),neg)
    c=copy.deepcopy(census);c['records'][0]['nodes'][0]['CUDA_support']=1;reject('non_boolean_support',lambda:A.census_decision(c,table,plan),neg)
    # Test the whole raw inspector on a CPU-only adapted retained MQ envelope.
    root=V/('analyzer_fixtures_'+args.tag);root.mkdir(exist_ok=False);(root/'cas').mkdir()
    slot=next(s for s in plan['numerical_slots'] if s['descriptor']=='Qwen_l00_prefill_q2' and s['layout']=='MQ' and s['repeat']==0)
    retained=Path('D:/hs113-timer-gpu14-v1/06');base_dir=root/'numerical'/('%03d'%slot['index']);(base_dir/'native').mkdir(parents=True)
    for name in ('RECORD.json','CORE_ADMITTED_BEFORE_CUDA.json','PLUGIN_CORE_IMPORTS.json','GRAPH_STARTED_0.json','GRAPH_CALL_RETURNED.json','SYNCHRONIZATION_RETURNED.json'):
        shutil.copyfile(retained/'native'/name,base_dir/'native'/name)
    r=load(base_dir/'native/RECORD.json');pid=r['pid'];old_exe=r['modules'][0];r['modules'][0]=str(V/'lowering113_formal.exe');(base_dir/'native/RECORD.json').write_text(json.dumps(r),encoding='utf-8')
    r['nodes']['ownership']=[dict(node=n['id'],has_buffer=True,buffer_is_host=False,actual_device=113,intended_device=113,valid=True) for n in r['nodes']['nodes'] if not n['metadata_only']]
    r['nodes']['all_ownership_checks_passed']=True;(base_dir/'native/RECORD.json').write_text(json.dumps(r),encoding='utf-8')
    helper=pin(Path('C:/Windows/System32/conhost.exe'))
    for prefix,main_pid,created,executable in [('native',pid,1,str(V/'lowering113_formal.exe')),('readiness',pid+100,2,'C:/Windows/system32/nvidia-smi.EXE')]:
        save(base_dir/(prefix+'.PROCESS.json'),dict(pid=main_pid,creation_filetime_100ns=created,creation_flags=0x08000000|4,active_process_limit=2,suspended_before_job_assignment=True))
        save(base_dir/(prefix+'.LIFETIME.json'),dict(pid=main_pid,creation_filetime_100ns=created,seconds=.5,exit_code=0,error=None,job_total_processes=2))
        save(base_dir/(prefix+'.JOB_EVENTS.json'),dict(registered_PID=main_pid,errors=[],started_unique_PIDs=[main_pid,main_pid+1],console_helper_pin=helper,
            events=[dict(message=6,pid=main_pid,image=executable),dict(message=6,pid=main_pid+1,image=helper['path'])]))
    save(base_dir/'native/STAGE_DESCRIPTORS.json',table[slot['descriptor'],'MQ']['stage_descriptors'])
    all_refs=refs[slot['descriptor']]['files']|refs[slot['descriptor']]['historical']
    for ref in all_refs.values():retain(root/'cas',blob(V/'reference_cas',ref))
    for p in (retained/'native').glob('*.bin'):
        rf=retain(root/'cas',p.read_bytes());name=p.stem
        save(base_dir/'native'/(name+'.BLOB.json'),dict(artifact=name,slot=slot['id'],pid=pid,cas_relative='cas/'+rf['sha256']+'.bin',**rf))
    inventory={A.norm(p['path']):p for p in load(V.parent/'GPU14_EXECUTION/OBSERVED_MODULE_FILES.json')['files']}
    inventory[A.norm(V/'lowering113_formal.exe')]=pin(V/'lowering113_formal.exe')
    save(base_dir/'MODULE_FILES.json',[inventory[A.norm(p)] for p in r['modules']])
    f0=dict(executable=str(V/'lowering113_formal.exe'),executable_sha256=sha(V/'lowering113_formal.exe'),runtime_directory=str(runtime),numerical_DLLs=load(V.parent/'repair_timer_v1/GPU14_F0.json')['numerical_DLLs'],console_helper=helper,admission_policy=dict(nvidia_smi='C:/Windows/system32/nvidia-smi.EXE'))
    A.inspect(slot,base_dir,f0,plan,refs,table[slot['descriptor'],'MQ'],{},root)
    mutations=[('bad_host_IAT','CORE_ADMITTED_BEFORE_CUDA.json',lambda x:x['host_import'].__setitem__('IAT_target',0)),
        ('missing_plugin_import','PLUGIN_CORE_IMPORTS.json',lambda x:x.pop()),('call_failed','GRAPH_CALL_RETURNED.json',lambda x:x.__setitem__('status',1)),
        ('sync_failed','SYNCHRONIZATION_RETURNED.json',lambda x:x.__setitem__('status',1)),('wrong_PID','GRAPH_CALL_RETURNED.json',lambda x:x.__setitem__('pid',0)),
        ('wrong_dtype','STAGE_DESCRIPTORS.json',lambda x:x['QK'].__setitem__('type',1)),
        ('CPU_placement','RECORD.json',lambda x:next(n for n in x['nodes']['nodes'] if not n['metadata_only']).__setitem__('placement','CPU')),
        ('wrong_graph_param','RECORD.json',lambda x:x['nodes']['nodes'][0]['op_params'].__setitem__(0,255)),
        ('missing_output_blob','QK.BLOB.json',lambda x:x.__setitem__('sha256','0'*64))]
    for label,name,mutate in mutations:
        case=root/'negative'/label;shutil.copytree(base_dir,case);p=case/'native'/name;data=load(p);mutate(data);p.write_text(json.dumps(data),encoding='utf-8')
        reject(label,lambda case=case:A.inspect(slot,case,f0,plan,refs,table[slot['descriptor'],'MQ'],{},root),neg)
    # Failed/unsupported coverage remains complete even without native outputs.
    denied=root/'capability_stop';denied.mkdir();save(denied/'CENSUS_DECISION.json',dict(denied_slots=[plan['numerical_slots'][0]['id']],numerical_admitted=False))
    status=A.analyze(denied,f0,plan,refs,table);assert status['slots'][0]['status']=='NOT_SUPPORTED' and status['slots'][1]['status']=='NOT_STARTED_CAPABILITY_STOP'
    failed=root/'census_failed';failed.mkdir();save(failed/'CENSUS_FAILED.json',dict(error='CPU_NEGATIVE_FIXTURE'))
    assert all(s['status']=='NOT_STARTED_PROTOCOL_STOP' for s in A.analyze(failed,f0,plan,refs,table)['slots'])
    empty=A.analyze(root/'never_executed',f0,plan,refs,table);assert len(empty['slots'])==720 and len(empty['contexts'])==72 and empty['completed_qualified']==0
    assert all(r['status']=='NOT_STARTED_NOT_AUTHORIZED' for r in empty['slots'])
    save(V/('CPU_ANALYZER_TESTS_'+args.tag+'.json'),dict(status='PASS',positive_pure_real_byte_cases=positive,finite_q_gt1_QH_differences_deliberately_accepted=True,
        complete_raw_inspector_CPU_fixture_cases=1+len(mutations),negative_cases=neg,full_missing_coordinate_enumeration=720,
        all72_contexts_and_requested_pairwise_relations_enumerated=True,support_outcome_policy_cases=4,
        source='CPU fixtures only; adapted retained GPU14 runtime envelope, real frozen reference bytes and explicit mutations. Not new GPU or formal-v2 observations.',GPU_queries=0,CUDA_plugin_loads=0,graph_computes=0,model_requests=0))
    print('PASS generic720 CPU numerical cases, finite-QH acceptance,',len(neg),'negative cases,360census policy and720missing-slot enumeration; no GPU work')
if __name__=='__main__':main()
