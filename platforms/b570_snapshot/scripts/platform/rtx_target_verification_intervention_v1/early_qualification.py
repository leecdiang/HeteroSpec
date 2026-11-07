"""Original native baseline qualification, with per-attempt raw retention."""
import importlib.util, json, os, subprocess, time, uuid
from pathlib import Path
from prepare import *

def main():
    spec=importlib.util.spec_from_file_location('v4_native',ROOT/'scripts/platform/rtx_trajectory_cost_v4/native.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    expected=read(DOC/'HISTORICAL_EXPECTED.json');inputs=read(OUT/'INPUTS.json')
    results=[]
    for t in G0TASKS:
        for c,oldc in [('R','TARGET_REFERENCE'),('N0','RTX_BATCHED_K2')]:
            d=OUT/'early-g0'/(t.replace('/','-')+'-'+c+'-r1')/uuid.uuid4().hex;d.mkdir(parents=True)
            cmd=m.templates(m.paths(ASSET))[oldc]
            mapping={'{prompt}':str(ROOT/inputs[t]['prompt']),'{native_log}':str(d/'native.log'),'{transcript}':str(d/'transcript.txt')}
            cmd=[mapping.get(x,x) for x in cmd]
            start={'task':t,'condition':c,'rep':1,'command':cmd,'started_utc':utc(),'formal':False,'path':'original_native','attempt':d.name}
            save(d/'START.json',start)
            print(json.dumps({'start':t,'condition':c}),flush=True)
            before=time.monotonic()
            with (d/'stdout.log').open('wb') as so,(d/'stderr.log').open('wb') as se:
                run=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=so,stderr=se,timeout=300,env={**os.environ,'LLAMA_BATCH_DEBUG':'1'})
            result={**start,'returncode':run.returncode,'elapsed_seconds':time.monotonic()-before,'ended_utc':utc()}
            try:
                assert run.returncode==0
                x=m.parse_capture(d/'native.log',oldc);result.update(x)
                e=expected[f'{t}/{c}/1']
                result['historical_equal']=x['generated_ids']==e['ids'] and x['termination']==e['endpoint']
                result['status']='VALID'
            except Exception as exc:result.update(status='INVALID',error=repr(exc),historical_equal=False)
            result['files']={p.name:sha(p) for p in d.iterdir() if p.is_file()}
            save(d/'RESULT.json',result);results.append(result)
            save(DOC/'EARLY_G0.json',{'status':'PASS_PREFIX' if result['historical_equal'] else 'BLOCKED_QUALIFICATION','runs':results,'planned_qualification_arrays':120,'actual_arrays':len(results)})
            print(json.dumps({k:result[k] for k in ['task','condition','status','historical_equal','elapsed_seconds']}),flush=True)
            if not result['historical_equal']:
                save(DOC/'STOP_REASON.json',{'status':'BLOCKED_QUALIFICATION','utc':utc(),'reason':'Original native output failed historical complete-array/endpoint qualification','task':t,'condition':c,'raw':str(d.relative_to(ROOT)).replace('\\','/'),'formal_valid':0,'formal_unexecuted':645})
                return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
