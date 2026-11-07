"""Bounded native admission negatives, charged and retained before formal timing."""
from pathlib import Path
import argparse, copy, subprocess, sys
import run_m1 as m

def main():
    p=argparse.ArgumentParser()
    for key in ('work','runtime','builds'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('baseline','repo','observer-builds'):p.add_argument('--'+key,type=Path)
    a=p.parse_args();m.load_runtime(a.runtime.resolve());w=a.work.resolve();base=m.read(w/'qualification-01/jobs/Qwen-natural-W_L4_D4.json')
    need,read,save,sha=m.need,m.read,m.save,m.sha
    need(read(w/'qualification-01/NATIVE_CHECKS_COMPLETE.json')['passed'],'Run after finite qualification')
    base['inputs']=[x for x in base['inputs'] if x['name']=='cap1-clean'];need(len(base['inputs'])==1,'One cap1 negative request')
    cases=[('unknown-field','Unknown M1 native job field'),('ignored-output-capacity','Native capability differs from complete requested contract')];rows=[]
    for name,error in cases:
        job=copy.deepcopy(base)
        if name=='unknown-field':job['unimplemented_context_option']=True
        else:job['capability_request']['target_context']['outputs_max']=8
        path=w/'capability-negatives-01/jobs'/(name+'.json');out=w/'capability-negatives-01/runs'/name;save(path,job)
        try:m.host.run(w/'config.json',a.builds.resolve()/'loop4/BUILD.json',path,out,'development')
        except RuntimeError:
            need(read(out/'HOST.json')['status']=='FAILED','Negative must retain failed host status')
            need(read(out/'native/failure.json')['error']==error,'Wrong native negative failure')
            need(not (out/'native/result.json').exists(),'Negative executed requests before rejecting capability')
        else:raise RuntimeError('Ignored or unknown field reached native requests')
        rows.append(dict(name=name,expected_error=error,job_sha256=sha(path),launch_sha256=sha(out/'launch.json'),
            failure_sha256=sha(out/'native/failure.json'),host_sha256=sha(out/'HOST.json'),charged=True))
    save(w/'capability-negatives-01/CHECKED.json',dict(passed=True,tests=rows,model_forwards=0,qualification_or_formal_slots_retried=False))
    print('NATIVE_CAPABILITY_NEGATIVES_PASS',flush=True)
    # This supplemental graph witness uses the same formal numerical archives;
    # it must finish before run_panel admits any timed slot.
    configured=read(w/'ADAPTER_PATHS.private.json') if (w/'ADAPTER_PATHS.private.json').exists() else {}
    def supplied(key):
        value=getattr(a,key.replace('-','_')) or configured.get(key)
        need(value is not None,'Explicit adapter path required: '+key);return str(Path(value).resolve())
    subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('check_dispatch.py')),
        '--work',str(w),'--baseline',supplied('baseline'),'--runtime',str(a.runtime.resolve()),
        '--repo',supplied('repo'),'--builds',str(a.builds.resolve()),'--observer-builds',supplied('observer-builds')],check=True)

if __name__=='__main__':main()
