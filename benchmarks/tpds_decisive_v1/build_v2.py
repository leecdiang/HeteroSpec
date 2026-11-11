"""Add post-service clean state and independent original scalar replay; keep v1."""
from build_host import *
import os,difflib
HERE=Path(__file__).resolve().parent
def compile_one(out,entry):
    binding=json.loads((OLD/'BUILD.json').read_bytes());(out/'bin').mkdir()
    for name,h in binding['numerical_modules'].items():
        src=ROOT/'draft/reference-observer/bin'/name;assert sha(src)==h;os.link(src,out/'bin'/name)
    commands=[]
    for rec in binding['commands']:
        if rec['label'] not in ('worker','link'):continue
        argv=[x.replace(str(OLD/'worker.cpp'),str(out/entry)).replace(str(OLD/'worker.obj'),str(out/'worker.obj')).replace(str(OLD/'bin/rtx-scope-transfer.exe'),str(out/'bin/worker.exe')) for x in rec['argv']]
        t=time.monotonic()
        with (out/(rec['label']+'.log')).open('xb') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=600)
        row=dict(argv=argv,code=r.returncode,seconds=time.monotonic()-t);commands.append(row);put(out/(rec['label']+'.json'),row);r.check_returncode()
    put(out/'BUILD.json',dict(exe=sha(out/'bin/worker.exe'),sources={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.cpp','.hpp')},core=binding['core_sha256'],modules=binding['numerical_modules'],commands=commands,status='BUILT_NOT_QUALIFIED'))
def main():
    for name in ['D1','D2','D4']:
        old=ROOT/'draft'/(name+'-observer');out=ROOT/'draft-v3'/name;out.mkdir(parents=True)
        s=(old/'worker.cpp').read_text();original=s
        s=s.replace('int pending=target->sample(-1,"initial"),','int final_frontier=-1;int pending=target->sample(-1,"initial"),')
        s=s.replace('if(capture)target->snapshot("commit-"+std::to_string(cycle),accepted);','final_frontier=accepted;if(capture)target->snapshot("commit-"+std::to_string(cycle),accepted);')
        s=s.replace('    return r;','    if(!capture){auto diagnostic=Clock::now();target->capture=true;target->snapshot("final-clean",final_frontier);target->capture=false;r["post_service_state_seconds"]=since(diagnostic);}\n    return r;')
        s=s.replace('fs::path path;int calls=0;','json caller_trace=json::array();fs::path path;int calls=0;')
        s=s.replace('capture=cap;path=dir;calls=0;','capture=cap;path=dir;calls=0;caller_trace=json::array();')
        s=s.replace('obs.phase=phase;obs.base=pos;','if(capture)caller_trace.push_back({{"phase",phase},{"position",pos},{"rows",ids.size()},{"all_outputs",all}});obs.phase=phase;obs.base=pos;')
        s=s.replace('r["target_calls"]=target->calls;', 'r["target_caller_trace"]=target->caller_trace;r["draft_caller_trace"]=draft?draft->caller_trace:json::array();r["draft_physical_width_hist"]=json::object();for(size_t z=0;z<hsc::w.draft_physical.size();z++)if(hsc::w.draft_physical[z])r["draft_physical_width_hist"][std::to_string(z)]=hsc::w.draft_physical[z];r["target_calls"]=target->calls;')
        begin=s.index('        HMODULE mods[1024]');end=s.index('        auto pool_start=',begin)
        inventory=s[begin:end].replace('HMODULE mods[1024];DWORD bytes=0;','')
        s=s.replace('        cleanup();result["status"]="COMPLETE";', '        result["modules_before"]=result["modules"];'+inventory+'        cleanup();result["status"]="COMPLETE";')
        (out/'worker.cpp').write_text(s,encoding='utf8');shutil.copy2(old/'target_capture.hpp',out/'target_capture.hpp')
        (out/'CHANGE.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True))),encoding='utf8');compile_one(out,'worker.cpp');print(name,'v2 built',flush=True)
    if (ROOT/'forced-v1/BUILD.json').exists():return
    out=ROOT/'forced-v1';out.mkdir()
    shutil.copy2(ROOT/'draft/reference-observer/worker.cpp',out/'worker.cpp');shutil.copy2(HERE/'forced_host.cpp',out/'forced_host.cpp')
    for name in ['target_capture.hpp','replay_path.hpp']:shutil.copy2(HERE/'native'/name,out/name)
    compile_one(out,'forced_host.cpp');print('forced-v1 built',flush=True)
if __name__=='__main__':main()
