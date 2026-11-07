"""Final source-bound identity/input negatives and actual census-wire CPU parsing."""
import argparse,copy,json,shutil,subprocess,sys
from pathlib import Path
from common import V,load,save,wire,pin,retain,env
import analyzer as A
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tag',default='final');args=ap.parse_args()
    plan=load(V/'PLAN.json');refs=load(V/'REFERENCE_INDEX.json');table={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_GRAPH_EXPECTED.json')}
    root=V/('analyzer_fixtures_'+args.tag);slot=next(s for s in plan['numerical_slots'] if s['descriptor']=='Qwen_l00_prefill_q2' and s['layout']=='MQ' and s['repeat']==0)
    base=root/'numerical'/('%03d'%slot['index']);helper=pin(Path('C:/Windows/System32/conhost.exe'))
    f0=dict(executable=str(V/'lowering113_formal.exe'),executable_sha256=pin(V/'lowering113_formal.exe')['sha256'],runtime_directory=plan['census_wire']['runtime_directory'],numerical_DLLs=load(V.parent/'repair_timer_v1/GPU14_F0.json')['numerical_DLLs'],console_helper=helper,admission_policy=dict(nvidia_smi='C:/Windows/system32/nvidia-smi.EXE'))
    r0=A.inspect(slot,base,f0,plan,refs,table[slot['descriptor'],'MQ'],{},root);negative=[]
    cases=[('wrong_core_module','native/CORE_ADMITTED_BEFORE_CUDA.json',lambda x:x['core'].__setitem__('path','C:/wrong/ggml-base.dll')),
        ('wrong_core_SHA','native/CORE_ADMITTED_BEFORE_CUDA.json',lambda x:x['core'].__setitem__('sha256','0'*64)),
        ('wrong_registry_SHA','native/CORE_ADMITTED_BEFORE_CUDA.json',lambda x:x['registry_import'].__setitem__('sha256','0'*64)),
        ('wrong_helper','native.JOB_EVENTS.json',lambda x:x['events'][1].__setitem__('image','C:/wrong.exe')),
        ('fake_job_counter','native.LIFETIME.json',lambda x:x.__setitem__('job_total_processes',1)),
        ('missing_input_bytes','native/input_Q.before.BLOB.json',lambda x:x.__setitem__('bytes',4))]
    for label,name,fn in cases:
        case=root/'extra'/label;shutil.copytree(base,case);p=case/name;v=load(p);fn(v);p.write_text(json.dumps(v),encoding='utf-8')
        try:A.inspect(slot,case,f0,plan,refs,table[slot['descriptor'],'MQ'],{},root)
        except Exception as e:negative.append(dict(label=label,error=repr(e)));continue
        raise AssertionError('accepted '+label)
    for label,name in [('actual_input_mutation','input_Q.before'),('actual_nonfinite_stage','QK')]:
        case=root/'extra'/label;shutil.copytree(base,case);p=case/'native'/(name+'.BLOB.json');rf=load(p);b=(root/'cas'/(rf['sha256']+'.bin')).read_bytes()
        data=(bytes([b[0]^1])+b[1:]) if label=='actual_input_mutation' else b'\x01\x00\xc0\x7f'+b[4:]
        changed=retain(root/'cas',data);rf.update(changed,cas_relative='cas/'+changed['sha256']+'.bin');p.write_text(json.dumps(rf),encoding='utf-8')
        try:A.inspect(slot,case,f0,plan,refs,table[slot['descriptor'],'MQ'],{},root)
        except Exception as e:negative.append(dict(label=label,error=repr(e)));continue
        raise AssertionError('accepted '+label)
    # Numeric PID reuse is legal only with a different kernel creation identity.
    r1slot=plan['numerical_slots'][slot['index']+1];case=root/'numerical'/('%03d'%r1slot['index']);shutil.copytree(base,case)
    for p in (case/'native').glob('*.BLOB.json'):
        rf=load(p);rf['slot']=r1slot['id'];p.write_text(json.dumps(rf),encoding='utf-8')
    for name in ('native.PROCESS.json','native.LIFETIME.json'):
        p=case/name;x=load(p);x['creation_filetime_100ns']=3;p.write_text(json.dumps(x),encoding='utf-8')
    A.inspect(r1slot,case,f0,plan,refs,table[slot['descriptor'],'MQ'],{(slot['descriptor'],'MQ',0):r0},root)
    for name in ('native.PROCESS.json','native.LIFETIME.json'):
        p=case/name;x=load(p);x['creation_filetime_100ns']=1;p.write_text(json.dumps(x),encoding='utf-8')
    try:A.inspect(r1slot,case,f0,plan,refs,table[slot['descriptor'],'MQ'],{(slot['descriptor'],'MQ',0):r0},root)
    except Exception as e:negative.append(dict(label='reused_process_generation',error=repr(e)))
    else:raise AssertionError('same process generation accepted')
    # The rejected CPU fixture remains rejected; no actual run root is involved.
    save(V/('CPU_EXTRA_TESTS_'+args.tag+'.json'),dict(status='PASS',negative_cases=negative,PID_reuse_with_new_kernel_creation_accepted=True,same_generation_rejected=True,
        full_mutant_input_and_nonfinite_bytes_retained=True,fixture_only=True,GPU_queries=0,CUDA_loads=0,graph_computes=0,model_requests=0))
    print('PASS9 extra raw-control negatives and PID-generation semantics; zero GPU work')
if __name__=='__main__':main()
