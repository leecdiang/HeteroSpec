"""Separate source epoch for complete physical counters and equal-work ownership."""
from pathlib import Path
import json,os,shutil,subprocess,time
from admission import HERE,ROOT,sha,put
from build_windows import BASE,WORK

def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)

def main():
    front=WORK/'frontend-v2';shutil.copytree(WORK/'frontend',front)
    shutil.copy2(HERE/'same_work.hpp',front/'same_work.hpp')
    p=front/'m1_capability.hpp';s=p.read_text();s=once(s,'"proposal_tape_requests"};','"proposal_tape_requests","same_work"};');p.write_text(s)
    p=front/'entry.cpp';s=p.read_text();s=once(s,'#include "m2_tapes.hpp"','#include "m2_tapes.hpp"\n#include "same_work.hpp"')
    s=once(s,'        if(job.contains("proposal_tape_requests"))','        if(job.contains("same_work")){same_work(job,result,root,pool);}\n        else if(job.contains("proposal_tape_requests"))')
    s=once(s,'            record["executions"]=ctx->plan.executions;', '            record["target_physical_width_hist"]=width_histogram(hsc::w.target_physical);\n            record["draft_physical_width_hist"]=width_histogram(hsc::w.draft_physical);\n            record["executions"]=ctx->plan.executions;');p.write_text(s)
    p=front/'worker.cpp';s=p.read_text()
    s=once(s,'    double setup=since(start);','    r["reset_and_setup_seconds"]=since(start);\n    double setup=since(start);')
    p.write_text(s)
    shutil.copytree(front,ROOT/'candidate_frontend_v2')
    source=WORK/'SOURCE-v2.json';put(source,dict(parent_source_sha256=sha(WORK/'SOURCE.json'),frontend={p.name:sha(p) for p in front.iterdir() if p.is_file()},
        numerical_core_edits=False,original_R_edits=False,threads=24,qualification='NOT_RUN',same_work='Symmetric restore outside primary timer; all eight owned full vectors inside; q4 first outputs copied before second call; actual core widths checked'))
    commands=[]
    for core in ('loop4','packed'):
        old=WORK/core;out=WORK/(core+'-v2');out.mkdir();(out/'bin').mkdir()
        for label in ('worker','link'):
            args=json.loads((old/(label+'.json')).read_bytes())['argv'];args=[x.replace(str(old),str(out)).replace(str(WORK/'frontend'),str(front)) for x in args]
            env=os.environ.copy();env.update(ZIG_GLOBAL_CACHE_DIR=str(WORK/'compiler-cache'),TEMP=str(WORK/'temp'),TMP=str(WORK/'temp'))
            start=time.monotonic()
            with (out/(label+'.log')).open('xb') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=900)
            record=dict(argv=args,code=r.returncode,wall_seconds=time.monotonic()-start);put(out/(label+'.json'),record);commands.append(record);r.check_returncode()
        for p in (old/'bin').glob('*.dll'):shutil.copy2(p,out/'bin'/p.name)
        b=json.loads((old/'BUILD.json').read_bytes());put(out/'BUILD.json',dict(b,exe=sha(out/'bin/worker.exe'),frontend_sha256=sha(source),qualified=False))
    put(ROOT/'BUILD_V2.json',dict(status='BUILT_NOT_QUALIFIED',source_binding=str(source),source_sha256=sha(source),commands=commands,new_model_requests=0,prior_epoch_retained=True))
    print('Windows epoch v2 built without model forwards',flush=True)

if __name__=='__main__':main()
